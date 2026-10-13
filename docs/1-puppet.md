# Puppet

Module 1 of [Sense · Think · Move](../README.md#the-modules): move the robot directly.
Sliders, oscillators and noise become a character that breathes, nods and looks around.

It needs TouchDesigner, and for the simulator or the robot the project set up
([getting-started.md](getting-started.md), then [touchdesigner.md](touchdesigner.md)).
`reachy_twin` works without that setup.

- [`puppet_start.toe`](#a-first-character-puppet_starttoe): the project to open
- [`reachy_hub`](#the-reachy_hub-component): the robot as one component
- [`reachy_twin`](#without-a-robot-the-reachy_twin-component): the robot as a picture

Next: [Animate](2-animate.md).

## A first character: puppet_start.toe

[`touchdesigner/puppet_start.toe`](../touchdesigner/puppet_start.toe) is a complete,
small example built on the hub: an idle character. Open it, click `reachy_hub`, press
**Start** on its Station page and wait for `ready`. The robot breathes, nods slightly,
looks around and sways its antennas.

How it is made:

| Operator | What it does |
| --- | --- |
| `base` (Constant) | all nine robot channels at 0, so every channel is always there |
| `breath`, `nod`, `ant_left`, `ant_right` (LFO) | one channel each: the head rising 3 mm, a 1.5° nod, the antennas swaying |
| `look` (Noise, Time Slice on) | the head drifting a few degrees, never quite still |
| `sum` (Math: Combine CHOPs *Add*, Match by *Channel Name*) | adds the layers channel by channel |
| `energy` (Math) | one Multiply for the whole character: 0 = still, 2 = restless |
| `smooth` (Lag) | takes the edges off |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back |

Each layer makes **one channel, named like the robot control it moves**. That is the
whole pattern: to add a movement, add a CHOP whose channel has a robot channel's name
and wire it into `sum`. Start by changing the Amplitude and Frequency of the layers.

## The reachy_hub component

[`touchdesigner/components/reachy_hub.tox`](../touchdesigner/components/reachy_hub.tox) packs the robot
connection into one component. Drag it from Finder / Explorer into your network.

- **Input:** wire in CHOP channels named after the robot's controls
  (`reachy/head/yaw`, … — the [address map](robot-channels.md#osc-address-map)). Send only the
  ones you use. Each is clamped to its safe range and sent to the bridge.
- **Output:** the robot's measured pose, same channel names — where it actually is.
- **Hub page:** where the bridge listens (**Bridge Address** `127.0.0.1`, **Bridge
  Port** `7000`) and where the pose comes back (**Pose Port** `7001`); **Enable
  Motors** and **Disable Motors** (real robot only — the simulator's motors are
  always on), **Neutral Pose**, and **Forget Taught Poses** (see
  [what a hand has shown](robot-channels.md#what-a-hand-has-shown)).
- **Station page:** starts the robot software on this computer, instead of the
  terminal. Pick the **Mode** (Simulator, Simulator without window, Robot), press
  **Start**, and wait until **Status** says `ready`. **Stop** ends it; quitting
  TouchDesigner ends it too. The station's full output is in the `log` DAT inside
  the component and in `station.log` in the project folder.

The Station page finds the project by itself when your `.toe` is saved inside the
project folder. Otherwise set **Project Folder** to that folder, the one with
`setup.command` in it.

The hub listens for the pose on port 7001, so don't add a second OSC In CHOP on that
port — use the hub's output.

## Without a robot: the reachy_twin component

[`touchdesigner/components/reachy_twin.tox`](../touchdesigner/components/reachy_twin.tox) is the robot as a
picture inside TouchDesigner. It needs no robot, no simulator and none of the project's
software: drag it into a network and it works, also on a computer where the project is
not set up.

- **Input:** the same channels as `reachy_hub` (`reachy/head/yaw`, … — the
  [address map](robot-channels.md#osc-address-map)). Wire what goes into the hub into the twin as
  well, or instead. Channels that are missing count as 0.
- **Output 1: the picture**, a TOP.
- **Output 2: the pose the picture shows**, with the hub's channel names: a network
  that reads the hub's measured pose reads the twin's just the same.
- **Robot Limits** (on unless switched off): the picture shows what the robot would do
  with the channels, not what was sent. Every value is kept inside its
  [safe range](robot-channels.md#osc-address-map), a change is followed no faster than the
  [speed limits](robot-channels.md#speed-limits), and the body turns along once the head is turned more
  than 65° away from it, as the robot's software does by itself. Switched off, the
  channels are shown as they arrive.
- **Status** says how many of the nine channels arrive and what the limits did to
  them: `limited: head/pitch` (beyond its range), `too fast: head/yaw` (still on its
  way there), `the body follows the head`. It also names a channel that is not one of
  the nine: a typing mistake, or a leading `/`. With **Robot Limits** off it says
  `beyond the legs' reach` for a pose the robot cannot take: the rods under the head
  then point at it without reaching it.
- **Camera Turn**, **Camera Height** and **Camera Distance** move the camera around the
  robot (Turn 0 is straight in front of it); **Resolution** is the size of the picture.
- **Floor** (on unless switched off): the robot stands on a floor that catches its
  shadow. Switched off, there is nothing behind the robot — the picture is transparent
  there — so it can be laid over another picture with an **Over TOP**.

Two ways to use it:

- **Before the robot:** shape the motion on the twin, then wire the same channels into
  `reachy_hub`.
- **Next to the robot:** wire the hub's output, the measured pose, into a twin with
  **Robot Limits** off. It then shows what the robot or the simulator is doing.

The twin shows where the robot's software would send the robot. It does not know what
only the robot can tell: a head touching the body where no limit covers it yet, a motor
that lags behind a fast move, the antennas swinging on their springs. The
[simulator](simulation.md) and the robot remain the test.

Inside, the robot is made of Geometry COMPs that hang on each other as its parts do:
`base`, `body`, `head`, the two antennas, and under the head the six legs that carry
it — for each a motor's arm on the body (`arm1` … `arm6`) and a rod from the arm up to
the head (`rod1` … `rod6`). The base, the body, the head and the antennas are moved by
expressions that read the pose: the place to see how a channel moves the robot. The
legs read `legs`, which works out for every pose how far each of the six motors has to
turn — the angles the robot's software sends them. The shapes are those of the
[simulator](simulation.md)'s model of the robot.
