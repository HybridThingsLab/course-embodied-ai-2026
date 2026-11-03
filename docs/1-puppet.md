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
| `reachy_mapping` | beneath the network, not wired to it: a value from 0 to 1, named like a robot channel, into how far that part goes ([below](#the-reachy_mapping-component)) |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back |
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

[`reachy_mapping.tox`](../touchdesigner/components/reachy_mapping.tox) is how a value of
your own reaches the robot. The rule:

1. **Bring it to 0 to 1:** a Math CHOP, its Range page: **From Range** where your value
   runs (-1 and 1 for an LFO), **To Range** 0 and 1. Ease it (Lag) before, if it jitters.
2. **Name it like a robot channel:** a Rename CHOP, `chan1` to `reachy/head/yaw` …
   ([the robot's channels](robot-channels.md)).
3. **Wire it into `reachy_mapping`.** On its Mapping page, **out** says where that part
   goes at 0 and at 1.

Its Mapping page also has an **in** for each part: where your value runs, 0 and 1 to
start. Leave it there when you bring your value to 0 to 1; set it to your value's range
instead (-1 and 1 for an LFO) and you can leave the Math out.

- **Input:** values from 0 to 1, named like the robot's channels. For several, merge
  them first (`to_mapping` in `03_sense.toe` and `04_think.toe`).
- **Output:** each of them in degrees, metres or radians: into the mix, as the robot's
  other layers.
- **Mapping page:** an **in** and an **out** for each part of the robot, two numbers
  each. What you type there is saved with your project. Right-click a field, *Reset to
  Default*, to go back.
- **Status** says what is wrong, which robot channels are in use, which come in beyond
  their in, and which channels came in that are none of the robot's (not renamed yet, or
  a typing mistake).

What the Mapping page starts with - every in at 0 and 1, every out the robot's whole
range:

| | in | out |
| --- | --- | --- |
| `head/x` | 0, 1 | -0.015, 0.022 |
| `head/y` | 0, 1 | -0.04, 0.04 |
| `head/z` | 0, 1 | -0.035, 0.022 |
| `head/roll` | 0, 1 | -30, 30 |
| `head/pitch` | 0, 1 | -27, 27 |
| `head/yaw` | 0, 1 | -175, 175 |
| `antenna/left` | 0, 1 | -3.1, 3.1 |
| `antenna/right` | 0, 1 | -3.1, 3.1 |
| `body_yaw` | 0, 1 | -160, 160 |

`reachy/head/yaw` at 0 turns the head as far right as it goes, at 1 as far left, at 0.5
straight ahead. Head x and z are the exception: their 0.5 is a few millimetres off the
rest position, because they reach further one way than the other.

- A narrower **out** makes a gentler move: -35 and 35 for `03_sense.toe`'s face. 0 and 8
  moves one way only (`04_think.toe`'s tilt). The first number above the second turns
  it the other way.
- A value beyond in (below 0 or above 1, to start) counts as in's end, and Status
  names it.
- Clips, recordings, poses and the sliders of `01_puppet.toe` are in degrees and metres
  already: they go into the mix as they are, not through `reachy_mapping`.
- How far the robot goes in the end is `reachy_hub`'s to say: it keeps every channel
  inside the robot's limits.

**Try:** in `01_puppet.toe` it sits beneath the network, not wired to it. An LFO (it
runs from -1 to 1), a Math CHOP behind it (From Range -1 and 1, To Range 0 and 1), a
Rename CHOP (`chan1` to `reachy/head/yaw`), into `reachy_mapping`, and its output into
`sum`. Set **head/yaw out** to -30 and 30: the head sways 30° to each side. Or leave
the Math out and set **head/yaw in** to -1 and 1.
