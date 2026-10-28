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
| `to_mapping` (Merge) → `reachy_mapping`, and its table `mapping` | the robot's channels pass through; any other channel wired into `to_mapping` moves the robot as a row of `mapping` says ([below](#the-reachy_mapping-component)) |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back |
| `reachy_model` | the robot as a picture: the pose the simulator or the robot reports ([below](#without-a-robot-the-reachy_model-component)) |

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
picture. It needs no robot, no simulator and no setup: drag it into any project.

- **Input:** the same channels as `reachy_hub`. The projects in `touchdesigner` wire
  `robot_pose` into it, with **Robot Limits** off: it shows what the simulator or the
  robot does. Wire what goes into the hub into it instead, and it shows what the robot
  would do, with no simulator running.
- **Output 1** is the picture (a TOP), **output 2** the pose it shows, named like the
  hub's output.
- It shows what the robot would do: values kept inside their ranges and speed limits.
  With **Robot Limits** off it shows the channels as they arrive.
- **Status** says how many channels arrive, and names one it does not know (a typing
  mistake, or a leading `/`).
- **Camera Turn**, **Camera Height** and **Camera Distance** move the view. With
  **Floor** off the background is transparent, to lay the robot over another picture.

## The reachy_mapping component

[`reachy_mapping.tox`](../touchdesigner/components/reachy_mapping.tox) turns any
channel into the robot's, by a table. Every starter,
`01_puppet.toe` to `05_compose.toe`, has it right before `to_robot`, with its table
next to it: `mapping`.

- **Input 1:** any channels. Those named `reachy/...` pass through unchanged. Any other
  becomes a robot channel where a row of the table names it; the rest stays behind.
- **Input 2:** the table, a Table DAT. Without one, the component uses its own rows,
  the ones below. Keep yours in your project: the rows inside the component are read
  again from its file whenever the project opens.
- **Output:** the robot's channels, with what the rows make added.
- **Status** says what is wrong with a row, and which rows are in use.

A row says: take this channel, which runs from in_min to in_max, and make it this robot
channel, from out_min to out_max. The rows it comes with:

| channel | reachy | in_min | in_max | out_min | out_max |
| --- | --- | --- | --- | --- | --- |
| `face/x` | `head/yaw` | -1 | 1 | -35 | 35 |
| `face/y` | `head/pitch` | -1 | 1 | -20 | 20 |
| `hand/x` | `head/yaw` | -1 | 1 | -35 | 35 |
| `hand/y` | `head/pitch` | -1 | 1 | 20 | -20 |
| `voice/level` | `antenna/left` | 0 | 1 | 0 | 0.5 |
| `voice/level` | `antenna/right` | 0 | 1 | 0 | -0.5 |
| `brain/thinking` | `head/roll` | 0 | 1 | 0 | 8 |
| `speaker/level` | `antenna/left` | 0 | 1 | 0 | 0.4 |
| `speaker/level` | `antenna/right` | 0 | 1 | 0 | -0.4 |

Wire `face_signal` into `to_mapping`, and the robot looks at the face; `hand_signal`,
at the hand. `voice_signal` and `speaker` move the antennas, and `brain_signal` tilts
the head while it thinks.

- **reachy** is one of the nine [robot channels](robot-channels.md), with or without
  `reachy/`.
- A value beyond in_min or in_max counts as that end. out_min above out_max turns it
  the other way: a hand higher up makes the head look up.
- Rows that move the same robot channel are added up, and added to that channel where
  it passes through: the face turning the head 20° one way and the hand 10° the other
  turn it 10°.
- How far the robot goes in the end is `reachy_hub`'s to say: it keeps every channel
  inside the robot's limits.

**Try:** a slider of your own. A Constant with a channel `my/slider` (0 to 1), wired
into `to_mapping`, and a row `my/slider`, `body_yaw`, 0, 1, -90, 90: the slider turns
the base. A signal from the camera jitters: smooth it before it goes in, with a Filter
(One Euro) or a Lag (0.2).
