# Simulation

Simulation runs a virtual Reachy Mini locally — no hardware needed. TouchDesigner
files work *identically* with the simulator and the real robot; only the way the
daemon starts differs.

Set up the project first ([getting-started.md](getting-started.md)); this page is the
reference for the simulator's options.

## Starting the simulator

The station starts the simulator and the bridge together, the right way for your
system:

```bash
python -m td_reachy.station             # MuJoCo, with its 3D window
python -m td_reachy.station --headless  # MuJoCo without the window
```

Use `--headless` on older or slower machines, or over a remote connection. The
robot still moves and TouchDesigner still receives its pose; there is just nothing to
watch (and no simulated camera image).

Alternatively, Pollen's
[Reachy Mini desktop app](https://github.com/pollen-robotics/reachy-mini-desktop-app/releases)
runs the simulator from a graphical interface. Start it in simulation mode, then run
the station: it uses the running daemon and only adds the bridge. Don't run two
daemons — both would want port 8000.

## Starting the daemon by hand

The station runs these commands for you. To run the daemon alone (environment
activated):

- **macOS** — the MuJoCo 3D window has to run on the main thread, so it must be
  launched with `mjpython`, a launcher that ships with MuJoCo:
  ```bash
  mjpython -m reachy_mini.daemon.app.main --sim
  ```
- **Windows / Linux:**
  ```bash
  reachy-mini-daemon --sim
  ```
- **Without the window**, on any system: `reachy-mini-daemon --sim --headless`.

Then start the bridge in a second terminal: `python -m td_reachy.bridge`.

Other daemon options: `--scene <name>` loads a MuJoCo scene (default: `empty`);
`--mockup-sim` replaces MuJoCo with a lightweight stand-in without graphics or
physics, useful only to check that something *runs*.

## Troubleshooting

- **macOS: `launch_passive requires … mjpython`** — the daemon was started with
  `reachy-mini-daemon --sim`. Use the station, the `mjpython` form above, or add
  `--headless`.
- **`port 8000 is taken`** — a daemon is already running, often the desktop app or
  an old one that hung. To clear a stray one: macOS `lsof -ti tcp:8000 | xargs kill`;
  Windows `netstat -ano | findstr 8000` then `taskkill /PID <pid> /F`.
- **Black window / nothing moves** — give it a few seconds; if it stays black, use
  `--headless` (some graphics setups can't open the viewer, but the simulation still
  runs).

## Simulation vs. the real robot — what's different

| | Simulation | Real robot |
| --- | --- | --- |
| Hardware needed | None | Reachy Mini, with USB and power |
| Start command | `python -m td_reachy.station` | `python -m td_reachy.station --robot` |
| Your TouchDesigner files | **Same** | **Same** |
| Motors off (`/reachy/enable 0`) | Ignored — always on | Works |
| Teach mode (posing by hand) | Nothing to grab | Works |
| Power-on / "no motors" issues | Don't apply | Apply — see [working-with-the-robot.md](working-with-the-robot.md) |
| Physical presence | None | The point of it all |

Because TouchDesigner talks to the same bridge on the same ports in both cases, a
patch built and tested in simulation runs on the physical robot with no changes.
