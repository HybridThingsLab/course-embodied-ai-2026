"""The OSC bridge between TouchDesigner and Reachy Mini — both directions.

    python -m td_reachy.bridge        (or let `python -m td_reachy.station` start it)

TouchDesigner can't load the Reachy SDK (it ships its own Python), so this small
program relays OSC from TouchDesigner to the robot, and streams the robot's live
pose back:

    TD ──/reachy/... targets :7000──▶ bridge ──set_target──▶ robot   (drive / replay)
    robot ──present pose──▶ bridge ──OSC/UDP :7001──▶ TD's OSC In CHOP  (read / record)
    TD ──/reachy/teach 1──▶ bridge ──disable_motors──▶ robot goes limp (pose it by hand)

It deliberately does only what TouchDesigner can't: drive the robot, put it in
**teach mode** (compliant, back-drivable), and **stream its pose out**. Recording,
saving and playing motion back are TouchDesigner nodes (see docs/2-animate.md).
The OUT addresses are the IN addresses, so a recording plays straight back.

Two UDP ports:
  * IN  (default 7000): targets + commands from TD.
  * OUT (default 7001): the robot's live pose, one message per channel.

Address map, IN and OUT (angles in DEGREES, translation in METRES, antennas in
RADIANS):

    /reachy/head/x /y /z          head translation, metres  (x -0.015..+0.022, y +/-0.040,
                                  z -0.035..+0.022; less the more the head tilts)
    /reachy/head/roll /pitch /yaw head orientation, degrees (+/-30, +/-27, +/-175;
                                  roll and pitch together stay inside an ellipse)
    /reachy/antenna/left /right   antenna angle, radians    (+/-3.1)
    /reachy/body_yaw              base yaw, degrees          (+/-160)

Every target is kept inside these ranges and followed no faster than the speed limits
(SPEED_MAX: head angles 300 deg/s, head position 0.35 m/s, antennas 12 rad/s; the base
183 deg/s with gentle acceleration) - see SpeedLimiter.

One of the rules gives way to what a hand has shown: "less shift the more the head
tilts". In teach mode the bridge remembers where the head was put (taught_room.py,
kept in taught_room.json), and lets a target be shifted as far at that tilt. So a
movement taught by hand plays back as it was shown. Each channel's own range, the tilt
ellipse, the turn limit and the speed limits hold all the same.

Grouped forms (IN only): /reachy/head/rpy <roll pitch yaw>,
/reachy/head/pose <x y z roll pitch yaw>, /reachy/antennas <left right>.

Commands (IN only):
    /reachy/neutral         back to the neutral pose
    /reachy/enable  <0|1>   motors on / off
    /reachy/teach   <0|1>   1 = go compliant for hand-posing; 0 = stiffen & hold
    /reachy/taught/forget   forget where a hand has put the head (empties taught_room.json)

Values outside the ranges are clamped. Yaw stops at +/-175, not 180: at the
+/-180 wrap the daemon's automatic body yaw would whip the base around.

Prereq: a daemon running (the station starts one), and the project installed.
"""

from __future__ import annotations

import argparse
import math
import threading
import time
from dataclasses import dataclass, replace

# Head joints from get_current_joint_positions() are [body_yaw, stewart_1..6]
# (see reachy_mini.kinematics.analytical_kinematics). Antennas come separately.


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# Head tilt limits, degrees. Not the SDK's ±40: on the real robot the head bumps into
# the body beyond about ±30 roll and ±27 pitch (tested 2026-09-30).
ROLL_MAX = 30.0
PITCH_MAX = 27.0


def limit_tilt(roll: float, pitch: float) -> tuple[float, float]:
    """Keep roll and pitch together inside an ellipse with semi-axes ROLL_MAX, PITCH_MAX.

    Each axis alone gets its full range, but tilting both ways at once bumps into the
    body sooner, so a combination outside the ellipse is scaled back towards level,
    keeping its direction: 30° + 27° becomes about 21° + 19°.
    """
    r = math.hypot(roll / ROLL_MAX, pitch / PITCH_MAX)
    if r <= 1.0:
        return roll, pitch
    return roll / r, pitch / r


# The antennas, radians: just short of half a turn either way, which is all the joint
# has (the robot's model: +/-pi). It was +/-2 until 2026-10-07, for no recorded reason;
# Pollen's recorded emotions reach 2.8.
ANTENNA_MAX = 3.1

# Head shift limits, metres: (towards -, towards +). The platform's travel is small, and
# not the same in every direction. Backward (-x) the real head hits the body at 20 mm
# (tried on the robot, 2026-10-06), so it stops at 15. Forward (+x) and down (-z) it
# meets the body too, and up (+z) the motors run out of reach at 24 mm: those come from
# the SDK's collision model; z was then widened after a pass on
# the robot showed room to spare.
SHIFT_MAX = {"x": (0.015, 0.022), "y": (0.040, 0.040), "z": (0.035, 0.022)}


def limit_shift(
    x: float, y: float, z: float, roll: float, pitch: float, reach=None
) -> tuple[float, float, float]:
    """Keep the head's shift inside what its tilt leaves over.

    Tilt and shift share one budget: tilt uses hypot(roll/ROLL_MAX, pitch/PITCH_MAX) of
    it, the shift |x|/max + |y|/max + |z|/max (each with the limit of its direction),
    and together they stay at or below 1. A level head gets the full shift ranges; at
    the tilt limit it cannot shift at all. The tilt has priority (where the head looks
    matters more), so a shift that doesn't fit is scaled back towards the centre.
    Pass roll and pitch already limited (limit_tilt).

    reach: a function giving how far, in metres, a hand has shifted the head in this
    direction at this tilt (TaughtRoom.reach). The shift may go that far even where
    the budget says less. It is only asked where the budget is not enough.
    """
    room = max(0.0, 1.0 - math.hypot(roll / ROLL_MAX, pitch / PITCH_MAX))
    shift = sum(abs(v) / SHIFT_MAX[k][v > 0] for k, v in (("x", x), ("y", y), ("z", z)))
    if shift <= room:
        return x, y, z
    f = room / shift
    if reach is not None:
        f = max(f, min(1.0, reach() / math.sqrt(x * x + y * y + z * z)))
    return x * f, y * f, z * f


@dataclass(frozen=True)
class Target:
    """A pose, in the same units the OSC map uses. Degrees / metres / radians."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    ant_left: float = 0.0
    ant_right: float = 0.0
    body_yaw: float = 0.0

    def ranged(self) -> Target:
        """Each channel inside its own range, roll and pitch inside their ellipse: all
        the limits but the one that tilt and shift share (clamped does that last)."""
        roll, pitch = limit_tilt(
            _clamp(self.roll, -ROLL_MAX, ROLL_MAX), _clamp(self.pitch, -PITCH_MAX, PITCH_MAX)
        )
        x, y, z = (_clamp(v, -SHIFT_MAX[k][0], SHIFT_MAX[k][1])
                   for k, v in (("x", self.x), ("y", self.y), ("z", self.z)))
        return replace(
            self,
            x=x,
            y=y,
            z=z,
            roll=roll,
            pitch=pitch,
            # Strictly below 180°: at/past ±180° the pose matrix wraps to the
            # opposite sign and the daemon's automatic-body-yaw IK whips the
            # base ~275° to follow it (nearly tips the robot).
            yaw=_clamp(self.yaw, -175.0, 175.0),
            ant_left=_clamp(self.ant_left, -ANTENNA_MAX, ANTENNA_MAX),
            ant_right=_clamp(self.ant_right, -ANTENNA_MAX, ANTENNA_MAX),
            body_yaw=_clamp(self.body_yaw, -160.0, 160.0),
        )

    def clamped(self, taught=None) -> Target:
        """This pose inside the limits. Each channel into its own range first, then the
        ones that share room (the hub limits in the same order, so the two agree).
        taught: a TaughtRoom - where a hand has put the head, the shift may go as far
        as it did there (see limit_shift)."""
        t = self.ranged()
        def reach() -> float:
            return taught.reach(t.x, t.y, t.z, t.roll, t.pitch, t.yaw, t.body_yaw)

        x, y, z = limit_shift(t.x, t.y, t.z, t.roll, t.pitch, reach if taught is not None else None)
        return replace(t, x=x, y=y, z=z)


# Speed limits: how fast a target may travel on its way to the robot. Whatever
# arrives - a typed-in jump, a glitch, a clip that starts somewhere else - the robot
# follows it no faster than this. They are caps, not a style: ordinary gestures stay
# well below them, so shape the motion in TouchDesigner (Lag, Filter) as before.
SPEED_MAX = {
    "x": 0.35, "y": 0.35, "z": 0.35,                 # metres per second
    "roll": 300.0, "pitch": 300.0, "yaw": 300.0,     # degrees per second
    "ant_left": 12.0, "ant_right": 12.0,             # radians per second
}
# The base carries the whole robot: it also speeds up and brakes gently.
BODY_SPEED_MAX = 183.0   # degrees per second (3.2 rad/s)
BODY_ACCEL_MAX = 229.0   # degrees per second squared (4 rad/s^2)


class SpeedLimiter:
    """Follows the incoming targets, no faster than the robot should move.

    Call ``step(target, dt)`` once per control tick and send what it returns. Call
    ``reset(pose)`` with the robot's present pose whenever the stream starts again
    (at the beginning, after teach mode, after the motors were off), so the first
    target is approached at the limited speed instead of jumped to.
    """

    def __init__(self, at: Target | None = None, taught=None) -> None:
        self.taught = taught  # a TaughtRoom: see Target.clamped
        self.reset(at or Target())

    def reset(self, at: Target) -> None:
        self.last = at
        self.body_speed = 0.0

    def step(self, want: Target, dt: float) -> Target:
        if dt <= 0:
            return self.last
        want, last = want.clamped(self.taught), self.last
        out = {}
        for key in ("x", "y", "z", "yaw", "ant_left", "ant_right"):
            reach = SPEED_MAX[key] * dt
            was = getattr(last, key)
            out[key] = was + _clamp(getattr(want, key) - was, -reach, reach)

        # Roll and pitch slow down together, so the head tilts along a straight line:
        # between two poses inside the tilt ellipse it never leaves it.
        moves = {"roll": want.roll - last.roll, "pitch": want.pitch - last.pitch}
        k = min([1.0, *(SPEED_MAX[key] * dt / abs(d) for key, d in moves.items() if d)])
        out["roll"] = last.roll + moves["roll"] * k
        out["pitch"] = last.pitch + moves["pitch"] * k

        # The base: head for the fastest speed from which it can still stop in time,
        # and change speed by at most BODY_ACCEL_MAX.
        err = want.body_yaw - last.body_yaw
        dist, dv_max = abs(err), BODY_ACCEL_MAX * dt
        v_stop = -dv_max / 2 + math.sqrt(dv_max * dv_max / 4 + 2 * BODY_ACCEL_MAX * dist)
        v_want = math.copysign(min(BODY_SPEED_MAX, v_stop, dist / dt), err)
        self.body_speed += _clamp(v_want - self.body_speed, -dv_max, dv_max)
        body = last.body_yaw + self.body_speed * dt
        if dist < 0.01 and abs(self.body_speed) <= dv_max:   # arrived
            body, self.body_speed = want.body_yaw, 0.0

        # The ranges once more: the shift gives way if the tilt got ahead of it.
        self.last = Target(**out, body_yaw=body).clamped(self.taught)
        return self.last


class SharedTarget:
    """Thread-safe box the OSC thread writes and the control loop reads.

    ``teach`` and ``torque`` are plain booleans (atomic assignment): the OSC
    thread flips them, the control loop acts on the
    change. All *robot* calls stay on the control loop's thread.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._t = Target()
        self.torque = True
        self.teach = False
        self.forget = False   # asked to forget where a hand has put the head

    def update(self, **fields: float) -> None:
        with self._lock:
            self._t = replace(self._t, **fields)

    def set(self, t: Target) -> None:
        with self._lock:
            self._t = t

    def reset(self) -> None:
        with self._lock:
            self._t = Target()

    def get(self) -> Target:
        with self._lock:
            return self._t


def build_dispatcher(shared: SharedTarget):
    """Map incoming OSC onto SharedTarget."""
    from pythonosc.dispatcher import Dispatcher

    disp = Dispatcher()

    # Per-channel scalars (TD's OSC Out CHOP sends channel `a/b` as `/a/b <f>`).
    scalar = {
        "/reachy/head/x": "x",
        "/reachy/head/y": "y",
        "/reachy/head/z": "z",
        "/reachy/head/roll": "roll",
        "/reachy/head/pitch": "pitch",
        "/reachy/head/yaw": "yaw",
        "/reachy/antenna/left": "ant_left",
        "/reachy/antenna/right": "ant_right",
        "/reachy/body_yaw": "body_yaw",
    }
    for addr, field in scalar.items():
        disp.map(addr, lambda _a, *args, f=field: shared.update(**{f: float(args[0])}))

    # Bundled multi-arg convenience messages.
    disp.map(
        "/reachy/head/rpy",
        lambda _a, *a: shared.update(roll=float(a[0]), pitch=float(a[1]), yaw=float(a[2])),
    )
    disp.map(
        "/reachy/head/pose",
        lambda _a, *a: shared.update(
            x=float(a[0]), y=float(a[1]), z=float(a[2]),
            roll=float(a[3]), pitch=float(a[4]), yaw=float(a[5]),
        ),
    )
    disp.map(
        "/reachy/antennas",
        lambda _a, *a: shared.update(ant_left=float(a[0]), ant_right=float(a[1])),
    )

    # Commands.
    disp.map("/reachy/neutral", lambda _a, *_: shared.reset())

    def _enable(_a, *args):
        shared.torque = bool(args and float(args[0]) >= 0.5)

    def _teach(_a, *args):
        shared.teach = bool(args and float(args[0]) >= 0.5)

    def _forget(_a, *_args):
        shared.forget = True

    disp.map("/reachy/enable", _enable)
    disp.map("/reachy/teach", _teach)
    disp.map("/reachy/taught/forget", _forget)
    return disp


def read_present(mini):
    """Read the robot's *present* pose (works with torque off) as a Target.

    ``get_current_head_pose`` is the inverse of ``create_head_pose``: decompose
    the 4x4 back into x/y/z + roll/pitch/yaw (XYZ-Euler, degrees). Antennas and
    base yaw come from the joint encoders.

    As measured, not limited: a head held outside the safe ranges by hand (teach
    mode) reports where it is, so a recording is what was shown. What the robot is
    *sent* is limited on its way out (``Target.clamped``, ``SpeedLimiter``); where a
    measured pose becomes a target, the control loop limits it there.
    """
    from scipy.spatial.transform import Rotation

    pose = mini.get_current_head_pose()
    x, y, z = (float(v) for v in pose[:3, 3])
    roll, pitch, yaw = Rotation.from_matrix(pose[:3, :3]).as_euler("xyz", degrees=True)

    head_joints, antennas = mini.get_current_joint_positions()
    ant_left, ant_right = float(antennas[0]), float(antennas[1])
    body_yaw = math.degrees(float(head_joints[0]))  # head_joints[0] is body_yaw (radians)

    return Target(
        x=x, y=y, z=z,
        roll=float(roll), pitch=float(pitch), yaw=float(yaw),
        ant_left=ant_left, ant_right=ant_right,
        body_yaw=body_yaw,
    )


def send_present(client, t: Target) -> None:
    """Emit the present pose to TD as one message per channel (matches the IN map)."""
    client.send_message("/reachy/head/x", t.x)
    client.send_message("/reachy/head/y", t.y)
    client.send_message("/reachy/head/z", t.z)
    client.send_message("/reachy/head/roll", t.roll)
    client.send_message("/reachy/head/pitch", t.pitch)
    client.send_message("/reachy/head/yaw", t.yaw)
    client.send_message("/reachy/antenna/left", t.ant_left)
    client.send_message("/reachy/antenna/right", t.ant_right)
    client.send_message("/reachy/body_yaw", t.body_yaw)


def move_duration(t: Target) -> float:
    """Seconds for a move between `t` and neutral: slow enough for a big turn."""
    return min(2.5, max(0.6, max(abs(t.yaw), abs(t.body_yaw)) / 90.0))


def away_from_neutral(t: Target) -> bool:
    return (max(abs(t.roll), abs(t.pitch), abs(t.yaw), abs(t.body_yaw)) > 3.0
            or max(abs(t.x), abs(t.y), abs(t.z)) > 0.005)


def to_neutral(mini) -> None:
    """Ease the whole robot to neutral, from wherever it is, with the motors on."""
    from td_reachy import gestures

    # Torque on first: it pins every target to the measured pose, so nothing snaps
    # (the motors may be off: teach mode, /reachy/enable 0, a robot left asleep).
    mini.enable_motors()
    present = read_present(mini)
    mini.goto_target(gestures.NEUTRAL, antennas=[0.0, 0.0], body_yaw=0.0,
                     duration=move_duration(present))


def park(mini, mode: str) -> None:
    """End a session without the head dropping.

    Cutting the torque at neutral lets the head fall onto its rest, so the motors are
    never released up there. Both modes first ease to neutral, then:
      hold   stay there, motors on. For when the daemon stops right afterwards (the
             station does this): the daemon lowers the robot to sleep itself, and a
             robot already asleep would be stood up again first.
      sleep  lower the robot into its sleep pose, then release the motors. For when
             the daemon keeps running.
    """
    to_neutral(mini)
    if mode == "hold":
        return
    mini.goto_sleep()
    mini.disable_motors()


def control_loop(mini, shared, out_client, rate, stop, taught=None) -> None:
    """One loop: drive playback when stiff, stay out of the way when teaching,
    and always stream the present pose out to TD.

    taught: a TaughtRoom. While the motors are off - teach mode, /reachy/enable 0 -
    whatever pose the head is in was put there by a hand, and is remembered; targets
    may then go as far (Target.clamped). None: the limits as they are, nothing learnt.
    """
    from reachy_mini.utils import create_head_pose

    dt = 1.0 / rate
    teaching = False
    torqued = True
    limiter = SpeedLimiter(read_present(mini).clamped(taught), taught)

    def keep() -> None:
        if taught is not None and taught.changed:
            taught.save()
            print(f"taught: {len(taught)} places known where a hand has put the head.")

    while not stop.is_set():
        tick = time.perf_counter()

        if shared.forget:
            shared.forget = False
            if taught is not None:
                taught.forget()
                print("taught: forgotten. The limits are as careful as before.")

        # --- teach-mode transitions (all robot calls happen here, one thread) ---
        if shared.teach and not teaching:
            # Enter teach: go fully compliant so it's back-drivable by hand.
            mini.disable_motors()
            teaching, torqued = True, False
            print("teach mode ON — motors compliant, move the robot by hand.")
        elif not shared.teach and teaching:
            # Leave teach: pin the target to where the robot *is* so enabling
            # doesn't jerk it away, then stiffen and hold.
            present = read_present(mini).clamped(taught)
            shared.set(present)
            limiter.reset(present)
            mini.enable_motors()
            teaching, torqued = False, True
            print("teach mode OFF — holding current pose, ready to replay.")
            keep()

        if not teaching:
            # /reachy/enable torque toggle.
            if shared.torque and not torqued:
                # start from where the robot is, and travel to the target at the
                # limited speed instead of jumping there
                limiter.reset(read_present(mini).clamped(taught))
                mini.enable_motors()
                torqued = True
                keep()
            elif not shared.torque and torqued:
                mini.disable_motors()
                torqued = False

            if torqued:
                # Replay: stream the latest incoming target to the robot, inside its
                # ranges and no faster than its speed limits.
                t = limiter.step(shared.get(), dt)
                head = create_head_pose(x=t.x, y=t.y, z=t.z, roll=t.roll, pitch=t.pitch, yaw=t.yaw)
                mini.set_target(
                    head=head, antennas=[t.ant_left, t.ant_right], body_yaw=math.radians(t.body_yaw)
                )

        # --- always stream the present pose out to TD (this is the "read every
        #     joint in TouchDesigner" the recorder relies on) ---
        present = read_present(mini)
        if out_client is not None:
            send_present(out_client, present)
        if taught is not None and not torqued:
            # Motors off: a hand holds the head, or it rests. Either way it is here.
            # Kept as a target of it would arrive at the shared rule: inside each
            # channel's own range, which no hand can widen.
            at = present.ranged()
            taught.visit(at.x, at.y, at.z, at.roll, at.pitch, at.yaw, at.body_yaw)

        slack = dt - (time.perf_counter() - tick)
        if slack > 0:
            time.sleep(slack)


def serve(args) -> None:
    try:
        from reachy_mini import ReachyMini
    except ImportError:
        print("reachy-mini SDK not installed — running in dry mode.")
        print(f"[dry run] would receive OSC on {args.ip}:{args.port}, stream pose "
              f"to {args.out_ip}:{args.out_port}, and teach/replay via the daemon.")
        return
    try:
        from pythonosc.osc_server import ThreadingOSCUDPServer
        from pythonosc.udp_client import SimpleUDPClient
    except ImportError:
        print("python-osc not installed. Install the project into this environment:")
        print('  uv pip install -e ".[sim]"')
        return

    try:
        mini_cm = ReachyMini()
    except Exception as err:  # noqa: BLE001 — friendly hint, then bail
        print("Could not reach the Reachy Mini daemon.")
        print("Start daemon + bridge together:  python -m td_reachy.station  (--robot: real robot)")
        print(f"\nOriginal error: {err}")
        return

    taught = None
    if not args.no_taught_room:
        from td_reachy.taught_room import TaughtRoom
        taught = TaughtRoom(args.taught_room)
        known = f"{len(taught)} places known where a hand has put the head"
        print(f"taught: {taught.note or known} ({taught.path})")

    shared = SharedTarget()
    server = ThreadingOSCUDPServer((args.ip, args.port), build_dispatcher(shared))
    out_client = SimpleUDPClient(args.out_ip, args.out_port)
    stop = threading.Event()

    with mini_cm as mini:
        print("Connected — enabling motors (head + antennas + base).")
        mini.enable_motors()
        if away_from_neutral(read_present(mini)):
            # e.g. asleep after the last session: come up gently instead of snapping
            # to the first target
            print("easing to neutral")
            to_neutral(mini)

        srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
        srv_thread.start()
        print(f"Listening for TD on {args.ip}:{args.port}")
        print(f"Streaming pose to TD on {args.out_ip}:{args.out_port} at {args.rate:.0f} Hz")
        print("Send /reachy/teach 1 to hand-pose, /reachy/teach 0 to stiffen & replay.")
        print("Ctrl+C to stop.")

        try:
            control_loop(mini, shared, out_client, args.rate, stop, taught)
        except KeyboardInterrupt:
            print("\nStopping.")
        except ConnectionError as err:
            print(f"\nLost connection to the daemon ({err}) — stopping.")
        finally:
            stop.set()
            server.shutdown()
            if taught is not None:
                taught.save()
            try:
                if args.park == "hold":
                    print("parking: back to neutral (the daemon puts the robot to sleep)")
                else:
                    print("parking: back to neutral, down to sleep, motors off")
                park(mini, args.park)
            except ConnectionError:
                print("(connection already gone — nothing to park)")


def main() -> None:
    parser = argparse.ArgumentParser(description="TouchDesigner teach-record / replay bridge")
    parser.add_argument(
        "--ip", default="0.0.0.0", help="listen address for TD (default: all interfaces)"
    )
    parser.add_argument(
        "--port", type=int, default=7000, help="OSC IN port from TD (default 7000; avoid 8000)"
    )
    parser.add_argument(
        "--out-ip", default="127.0.0.1", help="where TD's OSC In CHOP listens (default 127.0.0.1)"
    )
    parser.add_argument(
        "--out-port", type=int, default=7001, help="OSC OUT port to TD (default 7001)"
    )
    parser.add_argument(
        "--rate", type=float, default=100.0, help="loop Hz for replay + pose stream (default 100)"
    )
    parser.add_argument(
        "--park", choices=("sleep", "hold"), default="sleep",
        help="on stopping: 'sleep' lowers the robot to its sleep pose and releases the motors "
             "(default); 'hold' leaves it at neutral with the motors on, for when the daemon "
             "stops next and puts it to sleep itself (the station passes this)",
    )
    parser.add_argument(
        "--taught-room", default="taught_room.json", metavar="FILE",
        help="where the poses a hand has put the head in are kept, so that a movement "
             "taught by hand plays back as it was shown (default: taught_room.json in the "
             "folder the bridge is started from; it belongs to the robot it was taught on)",
    )
    parser.add_argument(
        "--no-taught-room", action="store_true",
        help="the limits as they are: learn nothing in teach mode, and let nothing "
             "through because a hand once showed it",
    )
    serve(parser.parse_args())


if __name__ == "__main__":
    main()
