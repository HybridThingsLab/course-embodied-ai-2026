# Think

Module 4: a sentence, typed or spoken, goes in. A model chooses one of your options and
the robot plays that option's clip; another model writes what the robot says back.

Before: [Sense](3-sense.md). Next: [Compose](5-compose.md).

## Step by step: 04_think.toe

[`touchdesigner/04_think.toe`](../touchdesigner/04_think.toe) has a base for each part
of Think: `speech_to_text`, `text_to_choice`, `text_to_speech` and `text_to_answer`. Each
base holds what the robot does with its part, but not the part itself: you add that.
Go into a base (double-click it) and read its `instructions`. Drag the component's
`.tox` file from `touchdesigner/components` into the base, wire it there, and press
**u** to go back up. The bases are already wired to each other.

Press **Start** on `reachy_hub` first: `reachy_model` shows the simulated robot, or the
real one.

| Step | Into the base | Drag in | Wire | Then |
| --- | --- | --- | --- | --- |
| 1 · Speech to text | `speech_to_text` | `speech_signal.tox` | first output → `speech_in`, second output → `said` | Language *English*, **Listen** on. What you say appears in `heard`; while you speak, the head tilts. |
| 2 · A decision | `text_to_choice` | `brain_signal.tox` | `options` → first input, `sentence` → second input, first output → `brain_in` | A model chooses an option and its clip plays (`pick_yes` → `play_yes` …). While it thinks, the head looks up. |
| 3 · Text to speech | `text_to_speech` | `speaker.tox` | `reply` → its input, first output → `voice_in` | Type into **Text** on its Speaker page: the robot says it, and the antennas move with the voice. |
| 4 · An answer | `text_to_answer` | `answer.tox` | `sentence` → its input, second output → `reply` | The robot answers what you say. **Character** is who it is. |

Each step needs its setup once: `setup-listen` (1), Ollama and `setup-think` (2 and 4),
`setup-speak` (3).

- **The options are yours.** `options`, in `text_to_choice`, is all the model knows
  about an option. For a new option add a row, copy `pick_yes`, `play_yes` and `yes_out`
  together, wire `brain_in` into the new Select and the new Null into `played`, write
  `brain/pick/` and the option's name in the Select, and choose a **Clip** in the
  player.
- **How far:** the head's tilt (head/roll), its look up (head/pitch) and the antennas
  are on the Mapping page of `reachy_mapping`, next to the robot.
- **The microphone hears the robot too.** `listen_gate`, in `speech_to_text`, passes
  nothing on to `heard` while the robot speaks or in the 2 s after, so it does not
  answer itself. With other robots nearby, use headphones.
- **German:** choose *Deutsch* on `speech_signal`, the speaker and `answer`, and a
  speaker **Engine** other than Kokoro, which speaks English only.

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
3. Double-click `setup-think` in the project folder. It downloads Tev1 (4.4 GB) and
   Gemma 3 for `answer` (3.3 GB), asks each one sentence and ends with **The models
   are ready**.
4. In TouchDesigner, `brain` asks Tev1 (the first choice of **Answered By**) and
   `answer` asks Gemma 3 whenever Ollama runs. When `brain`'s Status begins with
   `keyword match:`, no model answered: open Ollama again.

**Try:** hesitate when unsure: **Select** (`brain/confidence`) → **Logic** (*Off When
Outside Bounds*, Bounds 0 to 0.45) gives 1 after an unsure answer.

## An answer: the answer component

`answer.tox` (in `touchdesigner/components`) takes a sentence and asks a **language
model** for a short spoken answer: one or two sentences, no emojis, no lists. Type a
sentence into **Text** on the Answer page and press Enter, wire a sentence into its
input, or call `op('answer').Ask('Hello!')` from Python. Its second output is the
answer as text: wire it into a `speaker`.

- **Character:** who the robot is, in a few sentences: the first thing the model reads.
  Change it and talk to it again.
- **Language:** `en` or `de`, the language of its speaker. **Words:** at most so many.
- **Memory:** how many exchanges go along with each sentence, so that it can follow a
  conversation. **Forget** starts a new one; after two minutes without an answer it
  starts a new one by itself.
- **Input 1** (optional): a sentence, for example `speech_signal`'s second output.
- **Output 2:** the answer and its number, as a table: for `speaker`'s input.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `answer/thinking` | 0 or 1 | 1 while it waits for the model |
| `answer/done` | 0 or 1 | 1 for a moment when an answer is out |
| `answer/age` | seconds | how long ago the last answer came |
| `answer/failed` | 0 or 1 | 1 when the last sentence got no answer: then nothing is said |

**Answered By**, on the Model page:

| Answered By | Where the sentence goes | What it needs |
| ----------- | ----------------------- | ------------- |
| **Gemma 3, on this computer** | nowhere | Ollama and the model: `setup-think` downloads it with Tev1 |
| **Claude Haiku, in the cloud** | to OpenRouter, on the internet | the key in `brain_key.txt`, as for Jev |

The menu also has any other model or address that takes OpenAI's chat completions:
Ollama on another computer, LM Studio, another service.

When no model answers it says nothing, and **Status** says why, for example
`no answer - model "gemma3:4b" not found` (run `setup-think`). The first answer takes a
few seconds, while the model is loaded; later ones under a second.

**Try:** another character. **Character**: *You are Reachy, a shy little robot. You
answer briefly and quietly, and sometimes you only say hm.* Or give it a name, a mood,
a favourite subject.

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
On the Program page, **Output** lists this computer's sound outputs: choose
`Reachy Mini Audio` for the robot's own speaker, `default` (or nothing) for this
computer's. You can also type part of a name.

- **Input 1** (optional): a sentence, for example `speech_signal`'s second output. It is
  said when it changes.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `speaker/speaking` | 0 or 1 | 1 while it speaks |
| `speaker/level` | 0 … 1 | how loud it is now |
| `speaker/done` | 0 or 1 | 1 for a moment when a sentence has been said |
| `speaker/silence` | seconds | how long ago it last stopped speaking |
| `speaker/age` | seconds | how long ago the last sentence began |

**Try:** another voice: choose another **Voice**, or set **Speed** to 0.8.
