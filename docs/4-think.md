# Think

Module 4: a sentence, typed or spoken, goes in and a decision comes out. A model
chooses one of your options, and the robot plays that option's clip.

Before: [Sense](3-sense.md). Next: [Compose](5-compose.md).

## A sentence in, a clip out: 04_think.toe

Open [`touchdesigner/04_think.toe`](../touchdesigner/04_think.toe). `reachy_model`
shows the robot right away; for the simulator or the robot, press **Start** on
`reachy_hub`. Then click `brain`, type a sentence into **Text** on its Brain page and
press Enter.

It starts with the model Tev1, which needs `setup-think`
([below](#a-decision-the-brain_signal-component)). With **Answered By** set to
*Keywords only* on the Model page it works without anything installed.

| Operator | What it does |
| --- | --- |
| `options` (Table) | one row per option: its name, a description of when it fits (what the model reads), and keywords |
| `speech` (a `speech_signal`) | what it hears goes into `brain` as a sentence |
| `brain` (a `brain_signal`) | asks the model which option fits; `brain_out` shows its channels |
| `pick_yes` → `play_yes` (a `clip_player`), and the same for each option | the chosen option starts the player that holds its clip |
| `waiting` → `tilt` → `as_roll` → `ease` | while it waits for the answer, the head tilts |
| `base` and `motion` (Math: Combine CHOPs *Add*) | everything added up |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back |
| `lines` (Table) → `say_line` → `speaker` (a `speaker`) | the robot says the line of the option chosen; `talk_*` move the antennas with its voice |
| `listen_gate` → `heard` | what `speech` hears goes to `brain`, unless the robot was speaking just then |

The options are yours. Change a description and ask again: the description is all the
model knows about an option. For a new option, add a row to `options`, copy a `pick_`
and `play_` pair, name the option in the Select, choose a **Clip** in the player and
wire it into `motion`.

To say the sentence instead of typing it, click `speech` and switch **Listen** on
([`speech_signal`](3-sense.md#what-was-said-the-speech_signal-component)).

The robot answers out loud: `speaker` says the line in `lines` for the option chosen
([below](#a-voice-the-speaker-component)), from the column of its **Language**: `en` or
`de`. For German, choose *Deutsch* on `speaker` and on `speech`, and an **Engine** other
than Kokoro, which speaks English only. The microphone hears the robot too, so
`listen_gate` passes on nothing heard while it speaks or in the 2 s after: wait a
moment before you answer.

## A decision: the brain_signal component

[`brain_signal.tox`](../touchdesigner/components/brain_signal.tox) takes a sentence and
a list of options and asks a **decision model** which option fits. It is not a chat
model: it returns how likely each option is, and no text.

Type a sentence into **Text** on the Brain page and press Enter; **Ask** asks it again.
**Status** shows the choice and how sure the model is, for example `tev1: yes (0.83)`.

- **Input 1** (optional): the options, a table with the columns `name`, `description`
  and `keywords`. Without it the component uses its own: yes, no, maybe, look_around,
  nothing. Names: small letters, digits and `_`.
- **Input 2** (optional): a sentence, for example `speech_signal`'s second output.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `brain/<option>` | 0 … 1 | how likely this option is |
| `brain/pick/<option>` | 0 or 1 | 1 for a moment on the chosen option: a trigger |
| `brain/confidence` | 0 … 1 | how much the choice stands out (not whether it is right) |
| `brain/thinking` | 0 or 1 | 1 while it waits for an answer |
| `brain/age` | seconds | how long ago the last answer came |
| `brain/fallback` | 0 or 1 | 1 when the keywords answered, because no model did |

**Answered By**, on the Model page:

| Answered By | Where the sentence goes | What it needs |
| ----------- | ----------------------- | ------------- |
| **Tev1, on this computer** | nowhere | Ollama and the model: see below |
| **Jev, in the cloud** | to OpenRouter, on the internet | a key: see below |
| **Keywords only** | nowhere | nothing, and it understands nothing |

- **Tev1:** needs Ollama and the model, [step by step below](#tev1-step-by-step). The
  first answer takes a few seconds, later ones under a second.
- **Jev:** put the key in the first line of a text file `brain_key.txt` in the project
  folder. Never type it into a parameter: it would be saved with the project.
- **The keywords** answer when no model does. Status then begins with
  `keyword match:` and says why: Ollama not running, no model, no key.

The menu also has Nimble, a larger model for Ollama, and any other model or address.

### Tev1, step by step

1. Download Ollama from its site, [ollama.com/download](https://ollama.com/download),
   and install it: on macOS open the downloaded file and move Ollama into
   Applications, on Windows run the installer.
2. Open Ollama and leave it running: its icon is in the menu bar (macOS) or next to
   the clock (Windows).
3. Double-click `setup-think` in the project folder. It downloads Tev1 (4.4 GB), asks
   it one sentence and ends with **The model is ready**.
4. In TouchDesigner, `brain` asks Tev1 (the first choice of **Answered By**) whenever
   Ollama runs. When its Status begins with `keyword match:`, no model answered: open
   Ollama again.

**Try:** hesitate when unsure: **Select** (`brain/confidence`) → **Logic** (*Off When
Outside Bounds*, Bounds 0 to 0.45) gives 1 after an unsure answer.

## A voice: the speaker component

`speaker.tox` (in `touchdesigner/components`) says a sentence. Type it into **Text** on
the Speaker page and press Enter, or call `op('speaker').Say('Hello!')` from Python.
It needs a setup of its own once: double-click `setup-speak` in the project folder. It
installs the packages, downloads Kokoro and says a sentence.

| Engine | Where | Languages | The first time |
| ------ | ----- | --------- | -------------- |
| **Kokoro** (the default) | on this computer | English | downloads 350 MB |
| **Edge's voices** | Microsoft's cloud: the sentence leaves this computer | English, German | nothing; needs the internet |
| **Supertonic** | on this computer | English, German | downloads 385 MB |
| **Piper** | on this computer, the fastest | English, German | downloads each voice (60 MB) |

**Voice** lists the engine's voices in that **Language**; **Speed** goes from 0.5 to 2.
On the Program page, **Output** is where the sound goes: `Reachy Mini Audio` for the
robot's own speaker, empty for this computer's.

- **Input 1** (optional): a sentence, for example `speech_signal`'s second output. It is
  said when it changes.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `speaker/speaking` | 0 or 1 | 1 while it speaks |
| `speaker/level` | 0 … 1 | how loud it is now |
| `speaker/done` | 0 or 1 | 1 for a moment when a sentence has been said |
| `speaker/silence` | seconds | how long ago it last stopped speaking |
| `speaker/age` | seconds | how long ago the last sentence began |

**Try:** `speaker/level` as a nod: **Select** → **Math** (multiply by 4) → **Rename**
to `reachy/head/pitch` → into `motion`.
