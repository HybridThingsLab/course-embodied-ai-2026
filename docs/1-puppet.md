# Puppet

Module 1: move the robot directly. Sliders, oscillators and noise become a character
that breathes, nods and looks around.

Next: [Animate](2-animate.md).

## A first character: 01_puppet.toe

Open [`touchdesigner/01_puppet.toe`](../touchdesigner/01_puppet.toe), click
`reachy_hub`, press **Start** on its Station page and wait for `ready`. `reachy_model`
shows the simulated robot (the simulator has no window of its own). It stands still
until you move it: drag the value of `head_yaw`, and it turns.

| Operator | What it does |
| --- | --- |
| `head_x` … `body_yaw` (Constant) | one robot channel each, at 0: drag a value and the robot follows |
| `base` (Merge) | the nine channels together, so every channel is always there |
| `breath`, `nod`, `ant_left`, `ant_right` (LFO) | below the constants, not wired yet: the head rising 3 mm, a 1.5° nod, the antennas swaying |
| `look` (Noise) | not wired yet either: the head drifting a few degrees, never quite still |
| `sum` (Math: Combine CHOPs *Add*) | adds what is wired into it to `base`, channel by channel |
| `energy` (Math) | one Multiply for everything: 0 = still, 2 = twice as much |
| `smooth` (Lag) | takes the edges off |
| `to_robot` (Null) → `reachy_mapping` → `reachy_hub` → `robot_pose` (Null) | out to the robot through `reachy_mapping` ([below](#the-reachy_mapping-component)), and its measured pose back |
| `reachy_model` | the robot as a 3D model: the pose the simulator or the robot reports ([below](#without-a-robot-the-reachy_model-component)) |

Each constant and each layer makes **one channel, named like the robot control it
moves** ([the robot's channels](robot-channels.md)). Wire `breath` into `sum` and the
robot breathes; then the others, and change their Amplitude and Frequency. To add a
movement of your own, add a CHOP with such a channel and wire it into `sum`.

## The reachy_hub component

[`reachy_hub.tox`](../touchdesigner/components/reachy_hub.tox) is the robot in one
component.

- **Input:** channels named after the robot's controls (`reachy/head/yaw`, …: see
  [the robot's channels](robot-channels.md)). Send only the ones you use. Each is kept
  inside its safe range.
- **Output:** the robot's measured pose, with the same names.
- **Station page:** choose the **Mode** (Simulator or Robot),
  press **Start** and wait until **Status** says `ready`. **Stop** ends it, and so does
  quitting TouchDesigner. If your `.toe` is saved outside the project folder, set
  **Project Folder** to the folder with `setup.command` in it.
- **Hub page:** **Neutral Pose**, and **Enable Motors** / **Disable Motors** for the
  real robot.

## Without a robot: the reachy_model component

[`reachy_model.tox`](../touchdesigner/components/reachy_model.tox) is the robot as a
3D model. It needs no robot, no simulator and no setup: drag it into any project.

- **Input:** the same channels as `reachy_hub`. The projects in `touchdesigner` wire
  `robot_pose` into it, with **Robot Limits** off: it shows what the simulator or the
  robot does. Wire what goes into the hub into it instead, and it shows what the robot
  would do, with no simulator running.
- **Output 1** is the rendered robot (a TOP), **output 2** the pose it shows, named like the
  hub's output.
- It shows what the robot would do: values kept inside their ranges and speed limits.
  With **Robot Limits** off it shows the channels as they arrive.
- **Status** says how many channels arrive, and names one it does not know (a typing
  mistake, or a leading `/`).
- **Camera Turn**, **Camera Height** and **Camera Distance** move the view. With
  **Floor** off the background is transparent, to lay the robot over another image.

## The reachy_mapping component

[`reachy_mapping.tox`](../touchdesigner/components/reachy_mapping.tox) sits between
`to_robot` and `reachy_hub` in `01_puppet.toe`, `03_sense.toe`, `04_think.toe` and
`05_compose.toe`: everything the robot gets goes through it. For each part of the robot
it has an **in** (where the channel runs as it comes in) and an **out** (where it goes
to the robot). Both start at the robot's whole range, so everything passes as it is
until you change one.

- **Input:** channels named like the robot's ([the robot's channels](robot-channels.md)).
- **Output:** each of them from its in into its out, into `reachy_hub`.
- **Mapping page:** for each part of the robot an **in** and an **out**, two numbers
  each. What you type there is saved with your project.
- **Status** says what is wrong, which robot channels are in use, and which channels
  came in that are none of the robot's (a typing mistake, for one).

What the Mapping page starts with, in and out alike:

| | in and out |
| --- | --- |
| `head/x` | -0.015, 0.022 |
| `head/y` | -0.04, 0.04 |
| `head/z` | -0.035, 0.022 |
| `head/roll` | -30, 30 |
| `head/pitch` | -27, 27 |
| `head/yaw` | -175, 175 |
| `antenna/left` | -3.1, 3.1 |
| `antenna/right` | -3.1, 3.1 |
| `body_yaw` | -160, 160 |

- **out** narrower makes a part move less: **head/yaw out** -87.5 and 87.5, and every
  turn of the head is half as big. Its first number above the second turns it the
  other way.
- **in** is where a channel runs: 0 and 1 for a signal from 0 to 1, -1 and 1 for an
  LFO - then that range is spread over out.
- In and out act on the whole channel, everything added up on its way to `to_robot`.
- A value beyond in counts as its end. Right-click a field, *Reset to Default*, to go
  back to what it started with.
- How far the robot goes in the end is `reachy_hub`'s to say: it keeps every channel
  inside the robot's limits.

**Try:** an LFO (it runs from -1 to 1), a Rename CHOP behind it (`chan1` to
`reachy/head/yaw`), wired into `sum`. On `reachy_mapping`'s Mapping page set **head/yaw
in** to -1 and 1 and **head/yaw out** to -30 and 30: the head sways 30° to each side
(`head_yaw` now counts from -1 to 1 as well). A signal from the camera jitters: smooth
it before it goes in, with a Filter (One Euro) or a Lag (0.2).
