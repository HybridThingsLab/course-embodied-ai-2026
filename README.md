# Sense · Think · Move

Give a thing a behaviour, in [TouchDesigner](https://derivative.ca/): what it does
when nothing happens, how it reacts when it sees a face or hears a voice, and how it
answers what is said to it. Something is sensed, something is decided, something
moves, and the network that connects the three is yours to design.

The body to begin with is the
[Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) (Pollen Robotics / Hugging
Face): a head that turns, tilts and shifts in every direction, two antennas and a
turning base. The components that sense and decide know nothing about this robot, so
that another body can take its place.

This repository holds the TouchDesigner files, the programs behind them and the
guides. It is the material of the TouchDesigner workshop in the course *Physical
Interfaces: Embodied Interaction with AI* at the Technical University of Applied
Sciences Augsburg ([Hybrid Things Lab](https://github.com/HybridThingsLab)).

**No robot needed.** Everything runs against a 3D simulation on macOS or Windows, and
the same TouchDesigner files drive the real robot unchanged.

## The modules

**Puppet → Animate → Sense → Think → Compose → Extend.** Six modules that build on
each other. They take the chain from its far end: first what moves (Puppet, Animate),
then what is sensed (Sense), then what is decided (Think), then all of it as one
behaviour (Compose) and on another body (Extend). The first four come with a project
to open (a `.toe`) or components to drag into your own (`.tox`), all in
[`touchdesigner/`](touchdesigner/).

| | Module | What it is about | Start with |
| - | ------ | ---------------- | ---------- |
| 1 | **Puppet** | Move the robot directly. Sliders, oscillators and noise become a character that breathes, nods and looks around. | `puppet_start.toe` ([guide](docs/1-puppet.md#a-first-character-puppet_starttoe)) |
| 2 | **Animate** | Movements over time. Play clips such as yes, no and maybe, and make your own: pose by pose, as a take, or by posing the real robot by hand. | `animate_start.toe` ([guide](docs/2-animate.md#clips-animate_starttoe)) |
| 3 | **Sense** | What happens in front of the robot, as numbers a network can react to: a face, a hand, a voice, a spoken sentence. | the `_signal` components ([guide](docs/3-sense.md)) |
| 4 | **Think** | A sentence, typed or spoken, goes in and a decision comes out: a model chooses one of your options, and the robot plays that option's clip. | `think_start.toe` ([guide](docs/4-think.md#a-sentence-in-a-clip-out-think_starttoe)) |
| 5 | **Compose** | Idle, gaze, clips and reactions layered into one behaviour. | not in the repository yet |
| 6 | **Extend** | The same behaviour on another body: a light, a servo, a projection. | not in the repository yet |

One idea runs through all six. A **signal** says what happens, as channels such as
`face/x`, `voice/level` or `brain/yes`: it never moves anything. The robot takes
channels named like its controls, such as `reachy/head/yaw`, through the `reachy_hub`
component. What lies between the two is the **behaviour**: a network of ordinary
TouchDesigner operators that you build, and that stays open to change.

## Start here

1. **Get the code and run the setup**: double-click `setup.command` (macOS) or
   `setup.bat` (Windows). It installs everything and checks that it starts. Step by
   step: [docs/getting-started.md](docs/getting-started.md).
2. **Install TouchDesigner**, the free non-commercial edition:
   [docs/touchdesigner.md](docs/touchdesigner.md#1-install-touchdesigner).
3. **Open `touchdesigner/puppet_start.toe`**, click `reachy_hub`, press **Start** on
   its Station page and wait for `ready`. The simulated robot starts to move.

For a first look without any setup, drag `touchdesigner/reachy_twin.tox` into a new
TouchDesigner project: it is the robot as a picture and needs nothing else.

## The components

Each is a `.tox` file in [`touchdesigner/`](touchdesigner/): drag it into a network.
The names link to their section in the module's guide.

| Component | What it does | Module |
| --------- | ------------ | ------ |
| [`reachy_hub`](docs/1-puppet.md#the-reachy_hub-component) | The robot as one component: channels in, its measured pose out, and Start / Stop for the robot software. | Puppet |
| [`reachy_twin`](docs/1-puppet.md#without-a-robot-the-reachy_twin-component) | The robot as a picture inside TouchDesigner. Needs no robot and no setup. | Puppet |
| [`clip_player`](docs/2-animate.md#playing-a-clip-the-clip_player-component) | Plays a clip: one from the library in [`clips/`](touchdesigner/clips/README.md), or one of your own. | Animate |
| [`recorder`](docs/2-animate.md#making-a-clip-the-recorder-component) | Makes a clip from whatever arrives on its input, pose by pose or as a take. | Animate |
| [`face_signal`](docs/3-sense.md#a-face-as-channels-the-face_signal-component) | A face in front of the camera: where it is, how it is turned, whether it smiles. | Sense |
| [`hand_signal`](docs/3-sense.md#a-hand-as-channels-the-hand_signal-component) | A hand in front of the camera: where it is, how it is held, what its fingers do. | Sense |
| [`voice_signal`](docs/3-sense.md#a-voice-as-channels-the-voice_signal-component) | What a microphone hears: how loud it is, whether someone is speaking, a clap. | Sense |
| [`speech_signal`](docs/3-sense.md#what-was-said-the-speech_signal-component) | What was said, as a sentence: written down by Whisper on this computer, or by Chrome. | Sense, Think |
| [`brain_signal`](docs/4-think.md#a-decision-as-channels-the-brain_signal-component) | A sentence in, a decision model's choice among your options out. The model runs on this computer or in the cloud. | Think |

`face_signal` and `hand_signal` read the
[MediaPipe](docs/3-sense.md#camera-tracking-with-mediapipe) component, a separate
download. Also in the folder: `basic_control.toe`, the smallest example there is
(sliders straight to the robot).

## How it reaches the robot

```
  TouchDesigner ──OSC──▶ bridge ──▶ daemon ──▶ robot (simulated or real)
        ▲                  │
        └── live pose ─────┘
```

- **The daemon** is Pollen's program that owns the robot, or the simulator.
- **The bridge** passes messages between TouchDesigner and the daemon, and sends the
  robot's live pose back. TouchDesigner cannot load the robot's Python software
  itself, so this small program sits in between.
- **The station** starts both: from inside TouchDesigner with **Start** on
  `reachy_hub`'s Station page, or in a terminal with `python -m td_reachy.station`.

## Guides

- **[getting-started.md](docs/getting-started.md)**: install everything and see the
  simulated robot move.
- **[touchdesigner.md](docs/touchdesigner.md)**: install TouchDesigner, start the robot
  software, send and read values by hand, troubleshooting.
- **One guide per module**: [1-puppet.md](docs/1-puppet.md),
  [2-animate.md](docs/2-animate.md), [3-sense.md](docs/3-sense.md),
  [4-think.md](docs/4-think.md). Each has its project to open and its components.
- **[robot-channels.md](docs/robot-channels.md)**: every channel the robot takes, with
  its safe range and the speed limits.
- **[simulation.md](docs/simulation.md)**: simulator options, and how simulation
  differs from the real robot.
- **[working-with-the-robot.md](docs/working-with-the-robot.md)**: running on the
  physical robot.

## Also here

- **[`src/td_reachy/`](src/td_reachy/)**: the Python side: the station, the bridge,
  the listener behind `speech_signal`, and a safer daemon launcher for the real robot.
