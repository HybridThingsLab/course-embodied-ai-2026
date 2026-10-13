# Working with the physical robot

Everything built against the [simulator](simulation.md) runs on the physical robot
with **no changes** — only the start command differs, plus the physical-setup steps
below. The project must already be set up (see
[getting-started.md](getting-started.md)); the robot connects to the computer over
USB.

## 1. Power on — in the right order

1. Connect the robot to the computer with the **USB cable**.
2. Connect the robot's **power supply** and switch the robot on.

> **Both are required.** USB alone powers only the robot's electronics — the motors
> need the separate power supply. Without it the daemon starts but finds no motors.

## 2. Start the station with `--robot`

In a terminal with the environment activated:

```bash
python -m td_reachy.station --robot
```

Wait for the `[station] ready` line. If the robot wasn't switched on yet, the
station says so and re-scans every few seconds — switch it on and it continues.

`--robot` starts the daemon through `td_reachy.safe_daemon`, which limits how fast
the base can turn: a sudden large base turn can tip the robot over.

## 3. Use TouchDesigner — exactly as in simulation

Same patches, same ports ([touchdesigner.md](touchdesigner.md)). What the simulator
can't do: **teach mode**, posing the robot by hand and recording the motion
([2-animate.md](2-animate.md#teach-mode-pose-it-by-hand-record-replay)).

## 4. Shutting down

- **Ctrl+C** in the station's terminal: the robot returns to neutral and relaxes,
  then the daemon stops.
- Switch off and disconnect the robot.

## Common issues

- **"doesn't see the robot on USB"** (the daemon says `No Reachy Mini serial port
  found`) — the computer doesn't detect the robot at all. Use the robot's own cable
  (many USB-C cables only charge), plug it into the computer directly rather than into
  a monitor, dock or hub, and check both ends. The station re-scans every few seconds,
  so it continues once the robot shows up. On macOS, `ls /dev/cu.usb*` lists the
  connected USB serial devices.
- **The station keeps saying "no motors"** — the power supply isn't connected or the
  robot isn't switched on. Fix the power; the station picks it up by itself.
- **The robot connects but doesn't move** — its motors start relaxed; the bridge
  switches them on when it connects. If you sent `/reachy/enable 0` or
  `/reachy/teach 1`, send `/reachy/enable 1` or `/reachy/teach 0`.
- **`403` / "connection failed"** — the daemon isn't ready yet; this is *not* a
  network problem. Its real state is at <http://localhost:8000/api/daemon/status>.
- **The base turns wildly** — stop with Ctrl+C. Check that head yaw values stay
  within ±175° (the bridge clamps them), and that the station was started with
  `--robot` (not a daemon started by hand).
