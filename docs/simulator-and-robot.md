# The simulator and the robot

The same TouchDesigner files work with both. Only the **Mode** on `reachy_hub`'s
Station page changes.

| | Simulator | Real robot |
| --- | --- | --- |
| Mode | Simulator | Robot |
| In a terminal | `python -m td_reachy.station` (`--headless`: no window) | `python -m td_reachy.station --robot` |
| Motors off, teach mode | have no effect | work |

The simulator runs without a window of its own: it moves the robot and reports its
pose, and `reachy_model` shows that pose inside TouchDesigner. Its own window opens
only when the station is started in
[a terminal](getting-started.md#if-start-does-not-work-the-terminal) without
`--headless`.

## Switching the robot on

1. Connect the robot to the computer with its **USB cable**: directly, not through a
   hub or dock.
2. Connect its **power supply** and switch it on. USB alone does not power the motors.
3. Choose Mode **Robot**, press **Start** and wait for `ready`. If the robot was not on
   yet, the station keeps looking for it.

**Stop** (or quitting TouchDesigner) brings the robot back to neutral and lets it rest.
Then switch it off.

## Teach mode

`reachy/teach` 1 (**Teach** on `recorder`'s Teach page, in `02_animate.toe`) makes
the motors soft: move the head and antennas by hand, gently, holding the head shell.
`reachy/teach` 0 stiffens them where they are. Never move the robot by hand while the
motors are stiff. Stop playing anything into the robot before that, or it
jumps there.

The robot remembers how far a hand has moved the head, and lets a clip go as far later.
If you pressed the head against the body, press **Forget Taught Poses** on the hub's
Hub page.

## When something goes wrong

- **Status keeps saying "no motors":** the power supply is not connected, or the robot
  is not switched on.
- **`No Reachy Mini serial port found`:** the computer does not see the robot. Use the
  robot's own cable (many USB-C cables only charge) and plug it in directly.
- **It connects but does not move:** after `reachy/enable` 0 or `reachy/teach` 1, send
  1 or 0 again.
- **The base turns wildly:** press **Stop**.
- **"a simulator daemon is already running …, but the robot was requested"** (or the
  other way round): another station is still running. Stop it first.
- **TouchDesigner runs on another computer than the robot:** set the hub's **Bridge
  Address** to the robot computer's IP address, and start the station there in a
  terminal with `--out-ip <the TouchDesigner computer's IP address>`.

For starting the station in a terminal, see
[getting-started.md](getting-started.md#if-start-does-not-work-the-terminal).
