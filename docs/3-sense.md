# Sense

Module 3 of [Sense · Think · Move](../README.md#the-modules): what happens in front of
the robot, as numbers a network can react to. Each component here is a **signal**: it
says what happens, as channels, and never moves anything itself. What the robot does
with it is the network's business, and each section ends with a few ways to wire it.

- [`sense_start.toe`](#three-reflexes-sense_starttoe): the project to open
- [MediaPipe](#camera-tracking-with-mediapipe): the camera tracking the next two read
- [`face_signal`](#a-face-as-channels-the-face_signal-component): a face in front of
  the camera
- [`hand_signal`](#a-hand-as-channels-the-hand_signal-component): a hand in front of
  the camera
- [`voice_signal`](#a-voice-as-channels-the-voice_signal-component): how loud it is,
  whether someone speaks
- [`speech_signal`](#what-was-said-the-speech_signal-component): what was said, as a
  sentence

Before: [Animate](2-animate.md). Next: [Think](4-think.md).

## Three reflexes: sense_start.toe

[`touchdesigner/sense_start.toe`](../touchdesigner/sense_start.toe) has a face, a hand
and a voice move the robot, each in one way: it looks at you, it nods at a thumbs up,
and its antennas lean in when you speak. Three signals, and after each a short chain
of operators that turns what it says into a movement.

It needs a webcam and the `MediaPipe` component, a download of its own:
[see below](#camera-tracking-with-mediapipe). Then open the project, click `MediaPipe`
and choose your camera as **Webcam**. The system may ask whether TouchDesigner may use
the camera and the microphone. `reachy_twin` shows the robot as a picture right away;
for the simulator or the robot, click `reachy_hub`, press **Start** on its Station page
and wait for `ready`.

| Operator | What it does |
| --- | --- |
| `MediaPipe` | the camera, and what MediaPipe finds in its picture; only face landmarks and hands are switched on |
| `face` (a `face_signal`), `hand` (a `hand_signal`), `voice` (a `voice_signal`) | what happens, as channels; `face_out`, `hand_out` and `voice_out` (Null) show them |
| `look` (Select, `face/x face/y`) → `degrees` (Math: Multiply 35) → `as_head` (Rename to `reachy/head/yaw reachy/head/pitch`) → `steady` (Filter: One Euro) → `follow` (Lag) | it looks at you: where the face is in the picture becomes a turn of the head |
| `thumbs_up` (Select, `hand/thumbs_up`) → `nod` (a `clip_player` with the clip `yes`) → `nod_out` (Null) | thumbs up, and it nods: a gesture starts a clip |
| `level` (Select, `voice/level`) → `perk` (Lag: 0.03 up, 0.5 down) → `lean_left`, `lean_right` (Math: Multiply 0.5 and −0.5) → `as_left`, `as_right` (Rename to `reachy/antenna/left`, `reachy/antenna/right`) | speak, and the antennas lean in: how loud it is becomes how far |
| `base` (Constant) and `motion` (Math: Combine CHOPs *Add*, Match by *Channel Name*) | the nine robot channels at 0, with the three added channel by channel |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back; `reachy_twin` shows the same as a picture |

The three are examples of three kinds of reaction: a position that is followed, an
event that starts something, and a strength that becomes an amount. Change their
numbers first: the Multiply of `degrees`, the Lag of `follow`, the **Clip** of `nod`,
the gesture named in `thumbs_up`. Then wire in your own: the sections below list what
each signal says and end with more ways to use it. A new chain ends in `motion`.

- **`face` says `no data`**: press **Connect to MediaPipe** on its Face page, and the
  same on `hand`. That can happen when the project was opened before `MediaPipe.tox`
  was in its folder.
- **`face` says `1 face` before the camera is on**: `MediaPipe.tox` has one face stored
  in it, and sends that until the camera's first picture is there. The head looks a
  little down and to the side meanwhile. To see whether the camera is seen: cover it
  with your hand, and Status says `no face`.
- **The head turns away from you**: **Picture is Flipped** on `face` has to be on while
  MediaPipe's **Horizontal Flip** is on. The directions also assume a camera that looks
  where the robot looks.
- **The antennas never rest**: the room is loud. Click `voice` and raise **Quiet**.

The `readme` in the project has the steps.

## Camera tracking with MediaPipe

[`touchdesigner/mediapipe/`](../touchdesigner/mediapipe/) holds
`Reachy_Mediapipe.toe` and helper components for face, hand and pose tracking,
from [MediaPipe for TouchDesigner](https://github.com/torinmb/mediapipe-touchdesigner)
(Torin Blankensmith / Google Creative Lab). It needs a webcam and a reasonably
capable graphics card.

The main component, `MediaPipe.tox` (~172 MB), is too large for this repository.
Download `release.zip` from the project's
[releases](https://github.com/torinmb/mediapipe-touchdesigner/releases) and put its
`toxes/MediaPipe.tox` at `touchdesigner/mediapipe/toxes/MediaPipe.tox`.
`sense_start.toe` loads it from there every time it opens, so the project file itself
stays small. A copy of `sense_start.toe`, saved next to it, is the simplest start for a
project of your own with a camera.

### A face as channels: the face_signal component

[`touchdesigner/components/face_signal.tox`](../touchdesigner/components/face_signal.tox) turns MediaPipe's
face results into a handful of channels that say where a face is and what it does.

1. Have the `MediaPipe` component in your network (`sense_start.toe` has it) and
   switch on **Detect facial landmarks** on its MediaPipe page.
2. Drag `face_signal.tox` in next to it and press **Connect to MediaPipe** on its Face
   page. By hand, it is the MediaPipe output named `face_landmarks` that goes into it.
3. **Status** says `1 face` when it sees you.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `face/count` | 0, 1, 2, … | how many faces |
| `face/present` | 0 or 1 | 1 while there is a face |
| `face/x` | −1 … 1 | where the face is in the picture, sideways: + = towards the robot's left |
| `face/y` | −1 … 1 | and in height: + = lower in the picture |
| `face/size` | 0 … 1 | face width / picture width: bigger = closer |
| `face/yaw`, `face/pitch`, `face/roll` | degrees | the person's head — turned, nodding, tilted — as a mirror image |
| `face/jaw`, `face/smile`, `face/brow`, `face/blink` | 0 … 1 | mouth open, smiling, inner brows raised, eyes closed |

They describe the largest face. The channels are always there, and 0 while there is no
face. The directions assume a camera that looks where the robot looks.

- **A mirror image** means: copied to a head that faces the person (`reachy/head/yaw`,
  …), it turns, nods and tilts like their reflection. For a head that copies them as
  seen from behind, multiply yaw and roll by −1.
- **Picture is Flipped** has to be on when MediaPipe's **Horizontal Flip** is on, because
  MediaPipe then looks at a mirrored picture. *Connect to MediaPipe* sets it. The test:
  move towards the robot's left, and `face/x` rises.
- **Each Face** adds `face1/…`, `face2/…`, `face3/…` for up to three faces, the largest
  first. Set MediaPipe's **Max Number of Faces** (Facial Landmarks page) to 3.
- The head angles need MediaPipe's **Output Transformation Matricies**, and jaw, smile,
  brow and blink its **Output Blend Shapes** (Facial Landmarks page; both are on
  unless switched off).

A signal never moves anything by itself: what a face means for the robot is the network
after it. A gaze reflex, for example: **Select**
(`face/x face/y`) → **Math** (Multiply 35: position to degrees) → **Rename** (to
`reachy/head/yaw reachy/head/pitch`) → **Filter** (One Euro, against tracking jitter) →
**Lag** (0.25 up, 0.4 down) → into `sum`. Because +x is the robot's left and +y is
down, one Multiply turns the head towards the face on both axes.

### A hand as channels: the hand_signal component

[`touchdesigner/components/hand_signal.tox`](../touchdesigner/components/hand_signal.tox) turns MediaPipe's
hand results into channels that say where a hand is, how it is held and what its
fingers do: enough to play the robot like a puppet.

1. Have the `MediaPipe` component in your network with **Detect hands** on (MediaPipe
   page; it is on unless switched off).
2. Drag `hand_signal.tox` in next to it and press **Connect to MediaPipe** on its Hand
   page. By hand, it is the MediaPipe output named `hands` that goes into it.
3. **Status** says `1 hand` when it sees one.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `hand/count` | 0, 1, 2, … | how many hands |
| `hand/present` | 0 or 1 | 1 while there is a hand |
| `hand/x` | −1 … 1 | where the palm is in the picture, sideways: + = towards the robot's left |
| `hand/y` | −1 … 1 | and in height: + = higher in the picture |
| `hand/size` | 0 … 1 | the palm's length / picture width: bigger = closer |
| `hand/yaw`, `hand/pitch`, `hand/roll` | degrees | how the hand is held — turned, tipped, tilted — as a mirror image |
| `hand/open` | 0 … 1 | 0 = a fist, 1 = an open hand |
| `hand/pinch` | 0 … 1 | 1 = thumb and index fingertip together |
| `hand/thumb`, `hand/index`, `hand/middle`, `hand/ring`, `hand/pinky` | 0 … 1 | each finger: 0 = curled in, 1 = stretched out |
| `hand/fist`, `hand/palm`, `hand/point`, `hand/thumbs_up`, `hand/thumbs_down`, `hand/victory`, `hand/i_love_you` | 0 or 1 | 1 while MediaPipe recognises the gesture |

They describe the largest hand. The channels are always there, and 0 while there is no
hand. The names are `face_signal`'s wherever a face has them too, and so are the
directions, with one exception: `hand/y` counts upwards (a raised hand is +), `face/y`
downwards.

- **The hand is read like a head.** Its flat side that faces the camera — palm or back —
  is the face, the fingertips are the top. A flat hand, fingers up, facing the camera
  is 0, 0, 0. `hand/roll` is where the fingertips point in the picture, `hand/pitch`
  is + when they tip towards the camera (a head looking down), and `hand/yaw` is the
  hand turned about its own length, its flat side to the left or right. A mirror
  image, as for the face: copied to a head that faces the person, the head moves like
  the hand.
- **Turned too far, an angle goes back to 0** and never jumps to the other end.
  `hand/yaw` grows up to 60° and is 0 again when the hand is edge-on to the camera:
  from there on the camera sees its other side. `hand/roll` grows up to 120° and is 0
  with the fingertips straight down. `hand/pitch` stops at 90°, the fingertips at the
  camera; on the way there, from about 55°, yaw and roll go to 0.
- **`hand/size`** is measured on the palm, so closing the hand or tipping it does not
  change it.
- **The gestures** are MediaPipe's own: a fist, an open palm, the index finger
  pointing up, thumbs up, thumbs down, a victory sign and the sign for "I love you"
  (thumb, index and little finger out, the two fingers in between folded).
- **Picture is Flipped** has to be on when MediaPipe's **Horizontal Flip** is on.
  *Connect to MediaPipe* sets it. It also decides which hand is the left one.
- **Both Hands** adds the same channels for the person's own left and right hand as
  `left_hand/…` and `right_hand/…`, and two for the pair: `hands/apart`, the distance
  between the palms in picture widths, and `hands/tilt`, the line from one hand to
  the other against the horizon in degrees, like a steering wheel. MediaPipe's **Max
  Number of Hands** (Hands page) has to be 2.

A signal never moves anything by itself. Some ways to play the robot with a hand:

- **The hand is the head:** **Select** (`hand/yaw hand/pitch hand/roll`) → **Rename**
  (to `reachy/head/yaw reachy/head/pitch reachy/head/roll`) → **Filter** (One Euro,
  against tracking jitter) → **Lag** (0.1) → into `sum`. The angles are degrees and
  mirrored already. When the hand leaves the picture its channels go to 0, and the
  head returns to its idle.
- **Two fingers are the antennas:** **Select** (`hand/index`) → **Math** (Range: From
  0 … 1, To 1.5 … 0) → **Rename** (to `reachy/antenna/left`) → **Lag** (0.1): a curled
  finger folds its antenna away. For the right antenna the same with `hand/middle` and
  To −1.5 … 0, so both fold the same way.
- **A gesture plays a clip:** **Select** (`hand/thumbs_up`) into the second input of a
  `clip_player`.
- **It looks at the hand:** the gaze reflex above with `hand/x` for the yaw. For the
  pitch, multiply `hand/y` by −35 instead of 35: a raised hand is +, and the head
  looks down for a positive pitch.
- **Up means up:** **Select** (`hand/y`) → **Math** (Range: From −1 … 1, To −0.03 …
  0.02) → **Rename** (to `reachy/head/z`) → **Lag** (0.3): the head rises with the hand.
- **Closer means closer:** **Select** (`hand/size`) → **Math** (Range: From 0.1 … 0.3,
  To −0.015 … 0.02) → **Rename** (to `reachy/head/x`) → **Lag** (0.3): the head leans
  in when the hand comes near.
- **Two hands:** with **Both Hands**, one hand is the head (`left_hand/yaw`, …) and the
  other's fingers are the antennas (`right_hand/index`, `right_hand/middle`). Or steer:
  `hands/tilt` → **Rename** (to `reachy/head/roll`), and `hands/apart` → **Math**
  (Range: From 0.2 … 0.8, To −0.03 … 0.02) → **Rename** (to `reachy/head/z`).

## A voice as channels: the voice_signal component

[`touchdesigner/components/voice_signal.tox`](../touchdesigner/components/voice_signal.tox) listens to a
microphone and says how loud it is and whether someone is speaking. Drag it into your
network: it starts with the computer's default microphone. The first time, the system
may ask whether TouchDesigner may use the microphone. Only the loudness is measured;
nothing is recorded or sent.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `voice/rms` | 0 … 1 | the loudness as measured (RMS) |
| `voice/level` | 0 … 1 | the loudness between **Quiet** (0) and **Loud** (1) |
| `voice/active` | 0 or 1 | 1 while there is a voice |
| `voice/silence` | seconds | how long it has been quiet; 0 while there is sound |
| `voice/clap` | 0 or 1 | 1 for a moment at a sudden loud sound |

The channels are always there. It measures loudness and does not recognise speech: any
sound that loud counts as a voice — music, a door, the robot's own sound.

- **Quiet** and **Loud** fit it to the room and the microphone. Watch `voice/rms`
  while nobody speaks and set **Quiet** to that value; speak as you would to the robot
  and set **Loud** to what you reach. They start at 0.004 and 0.08.
- **`voice/active`** turns on when `voice/level` rises above 0.4. It turns off once the
  level has been below 0.3 for **Hold** seconds (0.15), so the short gaps between words
  do not end it. Raise **Hold** if it flickers while someone speaks.
- **`voice/silence`** counts from the moment the level drops below 0.3, and before the
  first voice from when listening began. A pause of half a second, the moment for a nod,
  is `voice/silence` above 0.5.
- **`voice/clap`** is 1 for a tenth of a second when `voice/rms` rises above **Clap**
  (0.3): a clap, a bang, a shout close to the microphone. The next one can come once
  the loudness has fallen below two thirds of **Clap**. A clap is loud, so
  `voice/active` comes on for a moment as well.
- **Microphone** chooses the device. The robot's own microphone is the USB audio device
  "Reachy Mini Audio".
- **The input** is optional: a CHOP wired in stands in for the microphone, which is
  then switched off. An **Audio File In CHOP** plays a recording; a **Constant CHOP** or
  a slider works without any sound, its value taken as the loudness (0.08 is a loud
  voice with the starting values).
- **Status** says where the sound comes from and whether any arrives.

A signal never moves anything by itself. Two reflexes, and a way to take turns:

- **The antennas lean in with the voice:** **Select** (`voice/level`) → **Lag** (0.03
  up, 0.5 down: it perks up at once and calms down gently) → **Math** (Multiply 0.5) →
  **Rename** (to `reachy/antenna/left`) → into `sum`. For the right antenna the same
  with Multiply −0.5, so both lean in together.
- **A clap startles it:** **Select** (`voice/clap`) → **Lag** (0.03 up, 0.4 down) →
  **Math** (Multiply −12) → **Rename** (to `reachy/head/pitch`): the head jerks up
  about 12° and settles. Or **Select** (`voice/clap`) into the second input of a `clip_player`:
  a clap plays the clip.
- **A nod in a pause:** **Select** (`voice/silence`) → **Logic** (Convert Input *Off
  When Outside Bounds*, Bounds 0.5 to 6) gives 1 from half a second of silence on — the
  trigger for a `clip_player` with a small nod — and 0 again after six seconds, when it
  is time to look away.

## What was said: the speech_signal component

[`touchdesigner/components/speech_signal.tox`](../touchdesigner/components/speech_signal.tox) gives what
someone says as a sentence, and says as channels what the listener is doing. It does
not listen itself. On its Speech page, **Heard By** chooses who does, and **Listen**
switches that listener on and off.

| Heard By | Where the speech is recognised | What to expect |
| -------- | ------------------------------ | -------------- |
| **Whisper, on this computer** | on this computer: nothing leaves it | The sentence arrives once you have stopped speaking: after a pause of 0.7 s, plus the time to write it down. With full stops and question marks. |
| **Chrome, on this computer where it can** | in Chrome, on this computer | The words appear while you speak. No punctuation, so a question does not look like one. |
| **Chrome's speech service** | at Google: the audio leaves this computer | As Chrome on this computer. Needs the internet, and is only used when it is chosen here. |

- **Output 1** has the channels below. **Output 2** is the last sentence and its
  number, as a table with one row. Wired into the second input of a
  [`brain_signal`](4-think.md#a-decision-as-channels-the-brain_signal-component), every sentence
  is asked. The number counts up, so the same sentence said twice is two.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `speech/listening` | 0 or 1 | 1 while a listener is there and listens (0 while it still loads) |
| `speech/hearing` | 0 or 1 | 1 while someone is speaking |
| `speech/writing` | 0 or 1 | 1 while Whisper writes down what it heard (Chrome writes while it hears) |
| `speech/said` | 0 or 1 | 1 for a fifth of a second when a sentence is complete: a trigger |
| `speech/age` | seconds | how long ago the last sentence was (before the first: since the start) |

- **Listen** starts and stops the listener. A project that was saved while it listened
  opens with Listen off: opening a file never switches a microphone on.
- **Language** is the language that is spoken, Deutsch or English.
- **Status** says what the listener is doing, or why it is not listening. **Heard**
  shows the sentence, with Chrome also while it is still being spoken.
- **Whisper** is a program of this project that the component starts. It needs its
  packages and its model (0.5 GB), once: double-click `setup-speech.command` (macOS) or
  `setup-speech.bat` (Windows) in the project folder. It installs the packages, fetches
  the model and lists the microphones it finds. By hand, the packages are

  ```bash
  uv pip install -e ".[speech]"
  ```

  and the model is then downloaded the first time Listen is switched on. The first
  time it listens, the system may ask whether TouchDesigner may use the microphone. Writing a sentence down took about
  half a second on the MacBook Pro it was measured on; a slower computer takes longer.
  On the Listener page, **Model** `large-v3-turbo` (1.6 GB) hears more exactly and
  took 2.4 s there.
- **Chrome** listens in a page that the component opens. Keep that tab open (it may
  be behind other windows) and allow the microphone when Chrome asks. To recognise
  speech on this computer, Chrome downloads a speech model the first time: the page
  shows a button for it. Where Chrome cannot do it at all, Status says so; choose
  Whisper then, or Chrome's speech service.
- **What it hears** is everything the microphone picks up: everyone in the room, a
  film, the group at the next table. Whisper sometimes writes a sentence for a sound
  that is no speech; steady sounds such as a hum are kept from it, music is not.
- **Port** (Listener page) is where the listener reports, on this computer only. Two
  `speech_signal` components at the same time need two ports.
- **If Whisper does not start from TouchDesigner**, Status says why, and the listener's
  own words are in `listener.log` in the project folder. It can also be started by
  hand, with Listen off, in a terminal with the environment active (`--language en`
  for English):

  ```bash
  python -m td_reachy.listener --post http://127.0.0.1:9982
  ```

`speech_signal` has been tried on macOS so far, not on Windows.

A signal never moves anything by itself. Two things to do with it:

- **It shows that it listens:** **Select** (`speech/hearing`) → **Math** (Multiply 8) →
  **Rename** (to `reachy/head/roll`) → **Lag** (0.3 up, 0.6 down) → into `sum`: the
  head tilts while someone speaks. The same with `speech/writing` fills the moment in
  which Whisper writes.
- **Every sentence starts something:** **Select** (`speech/said`) into the second input
  of a `clip_player`.
