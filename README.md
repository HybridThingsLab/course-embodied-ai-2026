winter term 2026/2027<br>
Technical University of Applied Sciences Augsburg, Prof. Andreas Muxel & Mathias Hradecsni<br>
[Hybrid Things Lab](https://github.com/HybridThingsLab), Faculty of Design

# Physical Interfaces / Embodied Interaction with AI

## Sense · Think · Move

Give a thing a behaviour in [TouchDesigner](https://derivative.ca/): what it does when
nothing happens, how it reacts to a face or a voice, and how it answers what is said to
it. The body to begin with is the
[Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) robot: a head that turns,
tilts and shifts, two antennas and a turning base.

**No robot needed:** everything runs with a simulated robot on macOS and Windows, and
the same files drive the real one.

## Start here

1. Install TouchDesigner, get this repository and run its setup:
   [docs/getting-started.md](docs/getting-started.md).
2. Open `touchdesigner/01_puppet.toe`, click `reachy_hub`, press **Start** on its
   Station page and wait for `ready`: `reachy_model` shows the simulated robot. Drag
   the value of `head_yaw`, and the robot turns.

## The modules

Each module has a project to open, in [`touchdesigner/`](touchdesigner/), and a guide.

| | Module | What it is about | Open |
| - | ------ | ---------------- | ---- |
| 1 | [Puppet](docs/1-puppet.md) | Move the robot directly: sliders, oscillators and noise become a character. | `01_puppet.toe` |
| 2 | [Animate](docs/2-animate.md) | Movements over time: play clips such as yes and no, and make your own. | `02_animate.toe` |
| 3 | [Sense](docs/3-sense.md) | A face, a hand, a voice and a spoken sentence, as numbers to react to. | `03_sense.toe` |
| 4 | [Think](docs/4-think.md) | A sentence goes in, a model chooses one of your options, the robot plays its clip and answers out loud. | `04_think.toe` |
| 5 | [Compose](docs/5-compose.md) | All of it as one behaviour: it sleeps, wakes, looks, listens and answers, each a layer in a mixer. | `05_compose.toe` |

The idea behind all of them: a **signal** such as `face/x`, `voice/level` or `brain/yes`
says what happens and never moves anything. The robot takes channels named after its
controls, such as `reachy/head/yaw`, through `reachy_hub`. In between is the
**behaviour**: a network of ordinary TouchDesigner operators that you build.

## The components

Drag a `.tox` from [`touchdesigner/components/`](touchdesigner/components/) into your
network.

| Component | What it does |
| --------- | ------------ |
| [`reachy_hub`](docs/1-puppet.md#the-reachy_hub-component) | The robot: channels in, its pose out, and Start / Stop for the robot software. |
| [`reachy_model`](docs/1-puppet.md#without-a-robot-the-reachy_model-component) | The robot as a picture. Needs no robot and no setup. |
| [`reachy_mapping`](docs/1-puppet.md#the-reachy_mapping-component) | Turns any channel into the robot's, by a table: which channel moves which part, and how far. In every starter, right before `to_robot`. |
| [`clip_player`](docs/2-animate.md#playing-a-clip-the-clip_player-component) | Plays a clip. |
| [`recorder`](docs/2-animate.md#making-a-clip-the-recorder-component) | Makes a clip. |
| [`face_signal`](docs/3-sense.md#a-face-the-face_signal-component) | A face in front of the camera. |
| [`hand_signal`](docs/3-sense.md#a-hand-the-hand_signal-component) | A hand in front of the camera. |
| [`voice_signal`](docs/3-sense.md#a-voice-the-voice_signal-component) | How loud it is, and whether someone speaks. |
| [`speech_signal`](docs/3-sense.md#what-was-said-the-speech_signal-component) | What was said, as a sentence. |
| [`brain_signal`](docs/4-think.md#a-decision-the-brain_signal-component) | A sentence in, a model's choice among your options out. |
| [`answer`](docs/4-think.md#an-answer-the-answer-component) | A sentence in, a language model's short spoken answer out, for a speaker to say. |
| [`speaker`](docs/4-think.md#a-voice-the-speaker-component) | A voice: a sentence in, spoken by Kokoro, Edge's voices, Supertonic or Piper, and how loud it is. |
| [`mixer`](docs/5-compose.md#mixing-layers-the-mixer-component) | Mixes layers of channels by name: each adds to or takes over what is below it, by its weight. |

## Also in the guides

- [robot-channels.md](docs/robot-channels.md): every channel the robot takes and its
  range, and how to send them without `reachy_hub`.
- [simulator-and-robot.md](docs/simulator-and-robot.md): the real robot, teach mode,
  and what to do when something goes wrong.
