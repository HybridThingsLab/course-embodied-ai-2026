# Compose

Module 5: all of it as one behaviour. What it does when nobody is there, how it reacts to
a face and a voice, and how it answers - each a layer, and a mixer that decides how much
of each there is.

Before: [Think](4-think.md).

## One character: compose_start.toe

Open [`touchdesigner/compose_start.toe`](../touchdesigner/compose_start.toe). It needs the
camera and the `MediaPipe` component, as in
[Sense](3-sense.md#camera-tracking-with-mediapipe), and a model for `brain`, as in
[Think](4-think.md#a-decision-the-brain_signal-component); with **Answered By** set to
*Keywords only* it works without one. Click `MediaPipe` and choose your camera as
**Webcam**. `reachy_twin` shows the robot right away; for the simulator or the robot,
press **Start** on `reachy_hub`.

While nobody is there it sleeps. A face or a voice wakes it, and it looks at whoever is
there; while someone speaks it leans in. Type a sentence into **Text** on `brain`: while
it thinks, its head tilts, then it answers with a gesture, a look around or a happy
little dance. And it always breathes.

| Layer (mixer input) | Mode | Weight | What it is |
| --- | --- | --- | --- |
| `asleep` (2) | Take Over | 1 − awake | a pose: the head down, the antennas drooping |
| `gaze` (3) | Take Over | `face/present` | `look` → `degrees` → `as_head` → `steady` → `follow`: it looks at the face |
| `listen` (4) | Add | `voice/active` | `lean_in`: the head forward, the antennas in |
| `think` (5) | Add | `brain/thinking` | `tilt`: the head to one side |
| `gestures` (6) | Add | 1 | the clips yes, no and maybe, when `brain` picks them |
| `act` (7) | Take Over | 1 while it plays | the clips look_around and cheerful1 (for `happy`) |
| `idle` (8) | Add | 1 | `breath`, `drift`, `sway_left`, `sway_right` |

The weights come from the signals and meet in `weights`, a channel named like each
layer: `someone` (a face or a voice) → `wake` (up at once, down over a few seconds) →
`sleepy` (1 − wake) is `asleep`; `face/present`, `voice/active`, `brain/thinking` and
whether an act plays are renamed to `gaze`, `listen`, `think` and `act`. `leading` shows
the weights as the mixer uses them.

Change first: the **Weight** of `idle` on the mixer's Mixer page (0 = still, 2 =
restless), the Lag of `wake` (how soon it falls asleep), and the **Mode** of `act`: as
Add, a look around goes on top of where it looks.

- **It never falls asleep:** `face` says `1 face` although nobody is there. MediaPipe
  sends a face stored in its file until the camera's first picture arrives.
- **`mixer` says `no layer named ...`:** a channel in `weights` is named like no layer -
  a typing mistake, or a layer without its Name yet.

## Mixing layers: the mixer component

[`mixer.tox`](../touchdesigner/components/mixer.tox) mixes layers of channels by their
names. It works with any channels, not only the robot's.

- **Inputs 2 to 9:** the layers, from the bottom (2) to the top (9).
- **Input 1** (optional): the weights. A channel named like a layer is its weight.
- **Output 1:** every channel of every layer wired in, mixed.
- **Output 2:** the weight of each layer as it is now, named like the layer.
- **Mixer page:** for each input a **Name**, a **Mode** and a **Weight**; **Fade**, the
  seconds a change of weight or mode takes; **Status**: how many layers and channels,
  and the layer on top.

| Mode | What the layer does |
| ---- | ------------------- |
| **Add** | it is added to the same channels below it, times its weight |
| **Take Over** | it replaces the same channels below it, as far as its weight says; the channels it does not have stay as they are |

A layer's weight is its **Weight** times its channel in input 1, if there is one.
**Weight** 0 mutes a layer. Take Over goes no further than 1; Add may (2 = twice as
much).

**Try:** a layer of your own. Wire a CHOP with robot channels into input 9, give it a
**Name** and a **Mode**, and its weight a channel of that name in `weights`.
