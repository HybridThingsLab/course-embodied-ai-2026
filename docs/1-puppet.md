# Puppet

Module 1: move the robot directly. Sliders, oscillators and noise become a character
that breathes, nods and looks around.

Next: [Animate](2-animate.md).

## A first character: 01_puppet.toe

Open [`touchdesigner/01_puppet.toe`](../touchdesigner/01_puppet.toe), click
`reachy_hub`, press **Start** on its Station page and wait for `ready`. The robot
breathes, nods, looks around and sways its antennas. `reachy_model` shows it right away,
also without the simulator.

| Operator | What it does |
| --- | --- |
| `base` (Constant) | all nine robot channels at 0, so every channel is always there |
| `breath`, `nod`, `ant_left`, `ant_right` (LFO) | one channel each: the head rising 3 mm, a 1.5° nod, the antennas swaying |
| `look` (Noise) | the head drifting a few degrees, never quite still |
| `sum` (Math: Combine CHOPs *Add*) | adds the layers channel by channel |
| `energy` (Math) | one Multiply for the whole character: 0 = still, 2 = restless |
| `smooth` (Lag) | takes the edges off |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back |
| `reachy_model` | the robot as a picture, from what goes into `reachy_hub` ([below](#without-a-robot-the-reachy_model-component)) |

Each layer makes **one channel, named like the robot control it moves**
([the robot's channels](robot-channels.md)). To add a movement, add a CHOP with such a
channel and wire it into `sum`. Start by changing the Amplitude and Frequency of the
layers.

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

- **Input:** the same channels as `reachy_hub`. Wire what goes into the hub into it as
  well (as the projects in `touchdesigner` do), or instead.
- **Output 1** is the picture (a TOP), **output 2** the pose it shows, named like the
  hub's output.
- It shows what the robot would do: values kept inside their ranges and speed limits.
  With **Robot Limits** off it shows the channels as they arrive.
- **Status** says how many channels arrive, and names one it does not know (a typing
  mistake, or a leading `/`).
- **Camera Turn**, **Camera Height** and **Camera Distance** move the view. With
  **Floor** off the background is transparent, to lay the robot over another picture.

To watch what the simulator or the robot does, wire the hub's output into a second
`reachy_model` with **Robot Limits** off.
