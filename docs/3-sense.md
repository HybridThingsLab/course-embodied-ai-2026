# Sense

Module 3: what happens in front of the robot, as numbers a network can react to. Each
component here is a **signal**: it says what happens, as channels, and never moves
anything itself. What the robot does with it is up to your network.

Before: [Animate](2-animate.md). Next: [Think](4-think.md).

## Three reflexes: sense_start.toe

[`touchdesigner/sense_start.toe`](../touchdesigner/sense_start.toe) has a face, a hand
and a voice move the robot: it looks at you, it nods at a thumbs up, and its antennas
lean in when you speak.

It needs a webcam and the `MediaPipe` component, a download of its own
([see below](#camera-tracking-with-mediapipe)). Open the project, click `MediaPipe` and
choose your camera as **Webcam**. Allow TouchDesigner the camera and the microphone if
the system asks. `reachy_twin` shows the robot right away; for the simulator or the
robot, press **Start** on `reachy_hub`.

| Operator | What it does |
| --- | --- |
| `MediaPipe` | the camera, and what MediaPipe finds in its picture |
| `face`, `hand`, `voice` | the three signals; `face_out`, `hand_out` and `voice_out` show their channels |
| `look` → `degrees` → `as_head` → `steady` → `follow` | it looks at you: where the face is becomes a turn of the head |
| `thumbs_up` → `nod` (a `clip_player`) | thumbs up, and it plays the clip `yes` |
| `level` → `perk` → `lean_left`, `lean_right` → `as_left`, `as_right` | speak, and the antennas lean in: louder is further |
| `base` and `motion` (Math: Combine CHOPs *Add*) | the three reactions added up |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back |

The three are three kinds of reaction: a position that is followed, an event that
starts something, and a strength that becomes an amount. Change their numbers first:
the Multiply of `degrees`, the Lag of `follow`, the **Clip** of `nod`, the gesture
named in `thumbs_up`. Then add your own chains, ending in `motion`.

- **`face` says `no data`:** press **Connect to MediaPipe** on `face` and on `hand`.
- **`face` says `1 face` although the camera is off:** MediaPipe sends a stored face
  until the camera's first picture arrives. Cover the camera: Status should say
  `no face`.
- **The head turns away from you:** **Picture is Flipped** on `face` has to be on
  while MediaPipe's **Horizontal Flip** is on.
- **The antennas never rest:** the room is loud. Raise **Quiet** on `voice`.

## Camera tracking with MediaPipe

`face_signal` and `hand_signal` read the results of
[MediaPipe for TouchDesigner](https://github.com/torinmb/mediapipe-touchdesigner)
(Torin Blankensmith / Google Creative Lab). Its main component is too large for this
repository: download `release.zip` from its
[releases](https://github.com/torinmb/mediapipe-touchdesigner/releases) and put its
`toxes/MediaPipe.tox` at `touchdesigner/mediapipe/toxes/MediaPipe.tox`.

For a project of your own with a camera, start from a copy of `sense_start.toe` saved
next to it.

## A face: the face_signal component

[`face_signal.tox`](../touchdesigner/components/face_signal.tox): where a face is and
what it does. Drag it next to `MediaPipe` and press **Connect to MediaPipe** on its Face
page. **Status** says `1 face` when it sees you.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `face/present` | 0 or 1 | 1 while there is a face |
| `face/count` | 0, 1, 2, … | how many faces |
| `face/x` | −1 … 1 | where the face is, sideways: + = towards the robot's left |
| `face/y` | −1 … 1 | and in height: + = lower in the picture |
| `face/size` | 0 … 1 | bigger = closer |
| `face/yaw`, `face/pitch`, `face/roll` | degrees | the person's head turned, nodding, tilted, as a mirror image |
| `face/jaw`, `face/smile`, `face/brow`, `face/blink` | 0 … 1 | mouth open, smiling, brows raised, eyes closed |

They describe the largest face, and are 0 while there is none. **Each Face** adds
`face1/…` to `face3/…` for up to three faces.

**Try:** the head copies the person's head, as in a mirror: **Select**
(`face/yaw face/pitch face/roll`) → **Rename** (to
`reachy/head/yaw reachy/head/pitch reachy/head/roll`) → **Lag** (0.2) → into `motion`.

## A hand: the hand_signal component

[`hand_signal.tox`](../touchdesigner/components/hand_signal.tox): where a hand is, how
it is held and what its fingers do. Drag it next to `MediaPipe` and press **Connect to
MediaPipe** on its Hand page. **Status** says `1 hand` when it sees one.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `hand/present` | 0 or 1 | 1 while there is a hand |
| `hand/count` | 0, 1, 2, … | how many hands |
| `hand/x` | −1 … 1 | where the palm is, sideways: + = towards the robot's left |
| `hand/y` | −1 … 1 | and in height: + = higher in the picture |
| `hand/size` | 0 … 1 | bigger = closer |
| `hand/yaw`, `hand/pitch`, `hand/roll` | degrees | how the hand is held, as a mirror image, as if it were a head |
| `hand/open` | 0 … 1 | 0 = a fist, 1 = an open hand |
| `hand/pinch` | 0 … 1 | 1 = thumb and index fingertip together |
| `hand/thumb`, `hand/index`, `hand/middle`, `hand/ring`, `hand/pinky` | 0 … 1 | each finger: 0 = curled, 1 = stretched |
| `hand/fist`, `hand/palm`, `hand/point`, `hand/thumbs_up`, `hand/thumbs_down`, `hand/victory`, `hand/i_love_you` | 0 or 1 | 1 while MediaPipe recognises the gesture |

They describe the largest hand, and are 0 while there is none. Turned too far, an angle
goes back to 0 instead of jumping. **Both Hands** adds `left_hand/…`, `right_hand/…`,
and `hands/apart` and `hands/tilt` for the pair (set MediaPipe's **Max Number of Hands**
to 2).

**Try:** the hand is the head: **Select** (`hand/yaw hand/pitch hand/roll`) → **Rename**
(to `reachy/head/yaw reachy/head/pitch reachy/head/roll`) → **Filter** (One Euro) →
**Lag** (0.1) → into `motion`. Or a finger is an antenna: **Select** (`hand/index`) →
**Math** (Range: From 0 … 1, To 1.5 … 0) → **Rename** (to `reachy/antenna/left`).

## A voice: the voice_signal component

[`voice_signal.tox`](../touchdesigner/components/voice_signal.tox): how loud it is and
whether someone speaks. Drag it into your network: it listens to the default
microphone. Only the loudness is measured; nothing is recorded or sent.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `voice/level` | 0 … 1 | the loudness, between **Quiet** (0) and **Loud** (1) |
| `voice/active` | 0 or 1 | 1 while there is a voice |
| `voice/silence` | seconds | how long it has been quiet |
| `voice/clap` | 0 or 1 | 1 for a moment at a sudden loud sound |
| `voice/rms` | 0 … 1 | the loudness as measured |

Any sound that loud counts as a voice: music, a door, the robot itself.

- **Quiet** and **Loud** fit it to the room: set **Quiet** to `voice/rms` while nobody
  speaks, and **Loud** to what it reaches when you speak.
- **Microphone** chooses the device. The robot's own is "Reachy Mini Audio".
- **Status** says whether sound arrives. If not, allow TouchDesigner the microphone:
  macOS System Settings → Privacy & Security → Microphone; Windows Settings → Privacy &
  security → Microphone.

**Try:** a clap plays a clip: **Select** (`voice/clap`) into the second input of a
`clip_player`. Or a nod in a pause: **Select** (`voice/silence`) → **Logic** (*Off When
Outside Bounds*, Bounds 0.5 to 6) into a `clip_player`'s second input.

## What was said: the speech_signal component

[`speech_signal.tox`](../touchdesigner/components/speech_signal.tox) gives what someone
says as a sentence. On its Speech page, **Heard By** chooses who listens, **Listen**
switches it on and off, and **Language** is Deutsch or English.

| Heard By | Where the speech is recognised | What to expect |
| -------- | ------------------------------ | -------------- |
| **Whisper, on this computer** | on this computer | the sentence after a short pause, with punctuation |
| **Chrome, on this computer where it can** | in Chrome, on this computer | the words while you speak, without punctuation |
| **Chrome's speech service** | at Google: the audio leaves the computer | as above; needs the internet |

- **Output 1** has the channels below. **Output 2** is the last sentence, as a table:
  wire it into the second input of a
  [`brain_signal`](4-think.md#a-decision-the-brain_signal-component).
- **Whisper** needs a setup of its own once: `setup-speech` in the project folder.
- **Chrome** opens a page: keep that tab open and allow the microphone. The first time,
  the page may show a button to download Chrome's speech model.
- It hears everything the microphone picks up: everyone in the room, a film, the next
  table.
- **If Whisper does not start**, Status says why. It can also run in a terminal, with
  Listen off (macOS: `source .venv/bin/activate` first, see
  [the terminal](getting-started.md#if-start-does-not-work-the-terminal)):
  `python -m td_reachy.listener --post http://127.0.0.1:9982`

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `speech/listening` | 0 or 1 | 1 while a listener is there and listens |
| `speech/hearing` | 0 or 1 | 1 while someone is speaking |
| `speech/writing` | 0 or 1 | 1 while Whisper writes down what it heard |
| `speech/said` | 0 or 1 | 1 for a moment when a sentence is complete |
| `speech/age` | seconds | how long ago the last sentence was |

**Try:** the head tilts while someone speaks: **Select** (`speech/hearing`) → **Math**
(Multiply 8) → **Rename** (to `reachy/head/roll`) → **Lag** (0.3 up, 0.6 down) → into
`motion`.
