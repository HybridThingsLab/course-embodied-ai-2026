"""Start the daemon and the TouchDesigner OSC bridge together, with one command.

    python -m td_reachy.station             # simulator (MuJoCo window)
    python -m td_reachy.station --headless  # simulator, no window
    python -m td_reachy.station --robot     # real robot, through safe_daemon
    python -m td_reachy.station --no-bridge # daemon only, for a program that talks to it itself
    python -m td_reachy.station --headless --check  # start, wait for ready, stop: tests the install

What it does, in order:
  1. Reuses a daemon that already answers on localhost:8000 (if it is in the
     requested mode), otherwise starts one: `mjpython` for the simulator on
     macOS, plain Python elsewhere, `td_reachy.safe_daemon` for a robot.
  2. Waits until `/api/daemon/status` says "running". A real robot that was not
     powered on reports "No motors detected" and the daemon caches that error —
     so the station keeps asking the daemon to re-scan until the motors appear.
  3. Starts the bridge (`td_reachy.bridge`: OSC in on 7000, live pose out on 7001)
     and waits until it is listening.
  4. On Ctrl+C / SIGTERM, or in `--managed` mode when stdin closes: stops the
     bridge first (it brings the robot back to neutral), then the daemon (it puts the
     robot to sleep) — but only a daemon it started itself; when the daemon stays, the
     bridge puts the robot to sleep.

Output for a front end (TouchDesigner's Station page reads the log): every line
of the station's own is `[station] <phase>: <message>`, with phase one of
starting, waiting, ready, stopping, stopped, error. Daemon and bridge output
follows with a `[daemon]` / `[bridge]` prefix.

`--managed` is for a parent program: the station stops when its stdin reaches
end-of-file or reads a line "stop". The parent keeps the pipe open while it
runs, so a crashed parent can't leave a daemon behind, and stopping works the
same on Windows, where there is no SIGINT to send to another process.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import sysconfig
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DAEMON_PORT = 8000
DAEMON_URL = f"http://localhost:{DAEMON_PORT}"
REPO = Path(__file__).resolve().parents[2]
# The bridge prints this once it is connected to the daemon and bound to its port.
BRIDGE_READY = "Listening for TD"

RESTART_EVERY = 8.0  # seconds between re-scans while the robot reports no motors
# The first start after installing can take minutes: the OS checks the freshly
# installed libraries on first load and GStreamer builds its plugin cache.
SLOW_START_NOTE_AFTER = 30.0
NO_USB_HINT = (
    "the computer doesn't see the robot on USB. Use the robot's own cable (many USB-C "
    "cables only charge), plug it into the computer directly rather than a monitor or "
    "hub, and check both ends; the station re-scans every few seconds"
)
NO_MOTORS_HINT = (
    "the daemon sees the robot but no motors. Switch the robot on (USB alone powers "
    "only the logic board); the station re-scans every few seconds"
)

_print_lock = threading.Lock()


def say(phase: str, message: str) -> None:
    with _print_lock:
        print(f"[station] {phase}: {message}", flush=True)


# --- daemon status ------------------------------------------------------------


def daemon_status(timeout: float = 1.0) -> dict | None:
    """The daemon's `/api/daemon/status` reply, or None when nothing answers."""
    try:
        with urllib.request.urlopen(f"{DAEMON_URL}/api/daemon/status", timeout=timeout) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError):
        return None


def request_rescan() -> None:
    """Ask the daemon to restart its backend (re-scans the motors). Busy → ignored."""
    req = urllib.request.Request(f"{DAEMON_URL}/api/daemon/restart", method="POST")
    try:
        urllib.request.urlopen(req, timeout=2.0).close()
    except (urllib.error.URLError, OSError):
        pass


def is_sim(status: dict) -> bool:
    return bool(status.get("simulation_enabled") or status.get("mockup_sim_enabled"))


def mode_mismatch(status: dict, want_sim: bool) -> str | None:
    """Why a running daemon can't be reused for the requested mode, or None."""
    if is_sim(status) == want_sim:
        return None
    if is_sim(status):
        return (
            f"a simulator daemon is already running on port {DAEMON_PORT}, but the robot was "
            "requested. Stop that daemon first, or start the station without --robot"
        )
    return (
        f"a robot daemon is already running on port {DAEMON_PORT}, but the simulator was "
        "requested. Stop that daemon first, or start the station with --robot"
    )


def read_status(status: dict | None) -> tuple[str, str]:
    """(kind, message) for one status reply: offline, starting, running, no_usb, no_motors
    or error. no_usb and no_motors are fixed by hand (plug in, switch on), so they're waited out."""
    if status is None:
        return "offline", "no daemon answering yet"
    state = status.get("state")
    error = status.get("error") or (status.get("backend_status") or {}).get("error")
    if state == "running":
        return "running", "daemon running"
    if state == "error":
        text = str(error or "").lower()
        if "serial port" in text:
            return "no_usb", NO_USB_HINT
        if "motor" in text:
            return "no_motors", NO_MOTORS_HINT
        return "error", f"the daemon reports an error: {error}"
    return "starting", f"daemon {state}"


# --- commands -----------------------------------------------------------------


def daemon_command(robot: bool, headless: bool, python: str, platform: str) -> list[str]:
    """How to start the daemon for this mode and platform."""
    if robot:
        return [python, "-m", "td_reachy.safe_daemon"]
    cmd = ["-m", "reachy_mini.daemon.app.main", "--sim"]
    if headless:
        return [python, *cmd, "--headless"]
    if platform == "darwin":
        # macOS: MuJoCo's viewer needs the main thread, which only mjpython gives it.
        return [str(Path(python).with_name("mjpython")), *cmd]
    return [python, *cmd]


def bridge_command(python: str, args: argparse.Namespace, park: str) -> list[str]:
    """park: how the bridge leaves the robot when it stops — see park_mode()."""
    return [
        python, "-m", "td_reachy.bridge",
        "--ip", args.ip, "--port", str(args.port),
        "--out-ip", args.out_ip, "--out-port", str(args.out_port),
        "--park", park,
    ]


def park_mode(station_stops_daemon: bool) -> str:
    """A daemon that stops puts the robot to sleep itself, lifting it to neutral first.
    So before that the bridge only returns to neutral and holds ("hold"); releasing the
    motors there would drop the head, and sleeping first would make it stand up again.
    A daemon that keeps running does neither, so the bridge sleeps the robot ("sleep")."""
    return "hold" if station_stops_daemon else "sleep"


def udp_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


def tcp_port_listening(port: int) -> bool:
    """Something accepts connections on localhost:port. (Connecting, not binding: a daemon
    that has just exited leaves its port in TIME_WAIT, which a bind test mistakes for busy.)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(("127.0.0.1", port)) == 0


# --- child processes ----------------------------------------------------------


def child_env(environ: dict[str, str], prefix: str, purelib: str) -> dict[str, str]:
    """The environment for a child Python, minus what the GStreamer wheel bundle injected.

    The bundle's .pth runs in every interpreter of this venv and *prepends* its folders to
    GST_*, GI_*, PYTHONPATH, PATH, … — single-path variables included. A child that inherits
    them gets them doubled (GST_PLUGIN_SCANNER_1_0="scanner:scanner"), GStreamer can't run its
    plugin scanner, and the daemon segfaults loading plugins. Dropping every entry that points
    into this venv's site-packages (or the bundle's registry cache) lets the child's own copy of
    the .pth set them once, correctly.
    """
    bundle = (
        os.path.join(purelib, ""),
        os.path.join(prefix, ".cache", "gstreamer-1.0"),
        os.path.join(prefix, "Temp", "gstreamer-1.0"),
    )
    env = {}
    for key, value in environ.items():
        parts = value.split(os.pathsep)
        kept = [p for p in parts if p != purelib and not p.startswith(bundle)]
        if kept == parts:
            env[key] = value
        elif kept:
            env[key] = os.pathsep.join(kept)
    return env


@dataclass
class Child:
    """A daemon or bridge process whose output is copied here with a prefix."""

    name: str
    proc: subprocess.Popen
    marker: str | None = None

    def __post_init__(self):
        self.ready = threading.Event()
        threading.Thread(target=self._pump, daemon=True).start()

    @classmethod
    def start(cls, name: str, cmd: list[str], marker: str | None = None) -> Child:
        env = child_env(os.environ, sys.prefix, sysconfig.get_paths()["purelib"])
        env.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        if sys.platform == "win32":
            group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            # Own session: a Ctrl+C in the terminal reaches only the station, which
            # then stops the children in the right order (bridge before daemon).
            group = {"start_new_session": True}
        proc = subprocess.Popen(
            cmd, cwd=REPO, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1, **group,
        )
        return cls(name, proc, marker)

    def _pump(self) -> None:
        for line in self.proc.stdout:
            with _print_lock:
                print(f"[{self.name}] {line.rstrip()}", flush=True)
            if self.marker and self.marker in line:
                self.ready.set()

    def exited(self) -> bool:
        return self.proc.poll() is not None

    def stop(self, grace: float) -> None:
        """Interrupt (so it can clean up), then terminate, then kill — the whole process tree."""
        if self.exited():
            return
        if sys.platform == "win32":
            self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                self.proc.wait(grace)
            except subprocess.TimeoutExpired:
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(self.proc.pid)], capture_output=True
                )
                self.proc.wait(5)
            return
        for sig, wait in ((signal.SIGINT, grace), (signal.SIGTERM, 3.0), (signal.SIGKILL, 3.0)):
            try:
                os.killpg(self.proc.pid, sig)
            except ProcessLookupError:
                return
            try:
                self.proc.wait(wait)
                return
            except subprocess.TimeoutExpired:
                continue


# --- the station --------------------------------------------------------------


def wait_for_daemon(daemon: Child | None, timeout: float, stop: threading.Event) -> bool:
    """Block until the daemon runs. Waiting for the robot (USB, power) doesn't count towards
    the timeout — someone has to walk over and plug it in or switch it on."""
    started = time.monotonic()
    deadline = started + timeout
    last_msg, last_rescan, noted_slow = None, 0.0, False
    while not stop.is_set():
        if daemon is not None and daemon.exited():
            say("error", f"the daemon exited (code {daemon.proc.returncode}); see [daemon] above")
            return False
        kind, msg = read_status(daemon_status())
        if kind == "running":
            return True
        if kind == "error":
            say("error", msg)
            return False
        if msg != last_msg:
            say("waiting", msg)
            last_msg = msg
        now = time.monotonic()
        if daemon is not None and not noted_slow and now - started > SLOW_START_NOTE_AFTER:
            say("waiting", "still starting; the first start after installing can take a few "
                           "minutes")
            noted_slow = True
        if kind in ("no_usb", "no_motors"):
            deadline = now + timeout
            if now - last_rescan > RESTART_EVERY:
                request_rescan()
                last_rescan = now
        elif now > deadline:
            say("error", f"the daemon was not running after {timeout:.0f} s")
            return False
        stop.wait(0.5)
    return False


def preflight(args: argparse.Namespace) -> str | None:
    """Everything that can be checked before starting anything; an error message or None."""
    missing = [m for m in ("reachy_mini", "pythonosc") if importlib.util.find_spec(m) is None]
    if missing:
        return (
            f"missing Python packages: {', '.join(missing)}. Run the station with the project's "
            f'.venv Python, and install the project once: uv pip install -e ".[sim]"'
        )
    if not args.robot and not args.headless and sys.platform == "darwin":
        mj = Path(sys.executable).with_name("mjpython")
        if not mj.exists():
            return f'{mj} not found. Install the simulator extra: uv pip install -e ".[sim]"'
    if not args.no_bridge and not udp_port_free(args.ip, args.port):
        return (
            f"UDP port {args.port} is taken, probably by another bridge. Stop it (Ctrl+C in its "
            "terminal), or start the station with another --port"
        )
    return None


def run(args: argparse.Namespace) -> int:
    stop = threading.Event()
    for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), lambda *_: stop.set())
    if args.managed:
        threading.Thread(target=_watch_stdin, args=(stop,), daemon=True).start()

    mode = "robot" if args.robot else "simulator" + (" (headless)" if args.headless else "")
    say("starting", f"{mode}; project {REPO}")
    problem = preflight(args)
    if problem:
        say("error", problem)
        return 1

    daemon: Child | None = None
    bridge: Child | None = None
    status: dict | None = None
    try:
        status = daemon_status()
        if status is not None:
            problem = mode_mismatch(status, want_sim=not args.robot)
            if problem:
                say("error", problem)
                return 1
            say("starting", f"reusing the daemon already running on port {DAEMON_PORT}")
        elif tcp_port_listening(DAEMON_PORT):
            say("error", f"port {DAEMON_PORT} is taken but no daemon answers there (an old "
                         "daemon that hung, or another program). Close it and try again")
            return 1
        else:
            cmd = daemon_command(args.robot, args.headless, sys.executable, sys.platform)
            say("starting", "daemon: " + " ".join([Path(cmd[0]).name, *cmd[1:]]))
            daemon = Child.start("daemon", cmd)

        if not wait_for_daemon(daemon, args.timeout, stop):
            return 0 if stop.is_set() else 1

        if args.no_bridge:
            say("ready", f"daemon running on localhost:{DAEMON_PORT}, no bridge")
            if args.check:
                say("check", "passed: the daemon started")
                return 0
            while not stop.wait(0.5):
                if daemon is not None and daemon.exited():
                    say("error", f"the daemon stopped (code {daemon.proc.returncode}); "
                                 "see [daemon] above")
                    return 1
            return 0

        say("starting", f"bridge: OSC in on {args.port}, pose out to {args.out_ip}:{args.out_port}")
        park = park_mode(station_stops_daemon=daemon is not None)
        bridge = Child.start("bridge", bridge_command(sys.executable, args, park),
                             marker=BRIDGE_READY)
        while not bridge.ready.wait(0.2):
            if stop.is_set():
                return 0
            if bridge.exited():
                say("error", f"the bridge exited (code {bridge.proc.returncode}); "
                             "see [bridge] above")
                return 1

        say("ready", f"TouchDesigner: OSC Out CHOP → 127.0.0.1:{args.port}, "
                     f"OSC In CHOP ← port {args.out_port}")
        if args.check:
            say("check", "passed: the daemon and the bridge started")
            return 0
        while not stop.wait(0.5):
            for child in (bridge, daemon):
                if child is not None and child.exited():
                    say("error", f"the {child.name} stopped (code {child.proc.returncode}); "
                                 f"see [{child.name}] above")
                    return 1
        return 0
    finally:
        # bridge first: it brings the robot back to neutral through the daemon (and, when
        # the daemon stays, down to sleep: up to 2.5 s + 5 s), then the daemon sleeps it
        if bridge is not None:
            say("stopping", "bridge")
            bridge.stop(grace=8.0 if daemon is not None else 14.0)
        if daemon is not None:
            say("stopping", "daemon")
            daemon.stop(grace=15.0)
        elif bridge is not None:
            say("stopping", "leaving the daemon running: the station did not start it")
        say("stopped", "all done")


def _watch_stdin(stop: threading.Event) -> None:
    try:
        for line in sys.stdin:
            if line.strip().lower() == "stop":
                break
    except (OSError, ValueError):
        pass
    stop.set()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start the Reachy Mini daemon and the TouchDesigner OSC bridge together."
    )
    parser.add_argument("--robot", action="store_true",
                        help="drive the real robot (through safe_daemon) instead of the simulator")
    parser.add_argument("--headless", action="store_true",
                        help="simulator without its window (no camera frames either)")
    parser.add_argument("--no-bridge", action="store_true",
                        help="start only the daemon (for programs that talk to it directly)")
    parser.add_argument("--check", action="store_true",
                        help="stop again as soon as everything is ready (tests the installation)")
    parser.add_argument("--managed", action="store_true",
                        help="for a parent program: stop when stdin closes or reads 'stop'")
    parser.add_argument("--timeout", type=float, default=300.0,
                        help="seconds to wait for the daemon (default 300)")
    parser.add_argument("--ip", default="0.0.0.0",
                        help="bridge listen address (default: all interfaces)")
    parser.add_argument("--port", type=int, default=7000,
                        help="bridge OSC in port, from TouchDesigner (default 7000)")
    parser.add_argument("--out-ip", default="127.0.0.1",
                        help="where TouchDesigner's OSC In CHOP listens (default 127.0.0.1)")
    parser.add_argument("--out-port", type=int, default=7001,
                        help="bridge pose out port, to TouchDesigner (default 7001)")
    args = parser.parse_args()
    if args.robot and args.headless:
        parser.error("--headless only applies to the simulator")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.exit(run(args))


if __name__ == "__main__":
    main()
