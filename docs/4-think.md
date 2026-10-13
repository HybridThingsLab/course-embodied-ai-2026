# Think

Module 4 of [Sense · Think · Move](../README.md#the-modules): a sentence, typed or
spoken, goes in and a decision comes out. A model chooses one of your options, and the
robot plays that option's clip.

- [`think_start.toe`](#a-sentence-in-a-clip-out-think_starttoe): the project to open
- [`brain_signal`](#a-decision-as-channels-the-brain_signal-component): asks the model
- [`speech_signal`](3-sense.md#what-was-said-the-speech_signal-component), from Sense:
  the sentence, spoken instead of typed

Before: [Sense](3-sense.md).

## A sentence in, a clip out: think_start.toe

[`touchdesigner/think_start.toe`](../touchdesigner/think_start.toe) lets the robot
answer what is said to it: you type a sentence or say it, a decision model chooses one
of your options, and the robot plays the clip of that option. Open it. `reachy_twin`
shows the robot as a picture right away; for the simulator or the robot, click
`reachy_hub`, press **Start** on its Station page and wait for `ready`. Then click
`brain`, type a sentence into **Text** on its Brain page and press Enter.

Someone has to answer. `brain` starts with the model Tev1, which needs
[Ollama](#a-decision-as-channels-the-brain_signal-component); with **Answered By** set
to *Keywords only* on its Model page it works without anything installed.

| Operator | What it does |
| --- | --- |
| `options` (Table) | one row per option: its name, a description (when does it fit? this line is what the model reads) and keywords |
| `speech` (a `speech_signal`) | what it hears goes into `brain` as a sentence; `speech_out` (Null) shows its channels |
| `brain` (a `brain_signal`) | asks the model which option fits the sentence; `brain_out` (Null) shows its channels |
| `pick_yes` … (Select, `brain/pick/yes`) → `play_yes` … (a `clip_player` each) → `yes_out` … (Null) | the trigger of an option starts the player that holds the clip of that name |
| `waiting` (Select, `brain/thinking`) → `tilt` (Math: Multiply 8) → `as_roll` (Rename to `reachy/head/roll`) → `ease` (Lag) | what the robot does while it waits for the answer: the head tilts |
| `base` (Constant) and `motion` (Math: Combine CHOPs *Add*, Match by *Channel Name*) | the nine robot channels at 0, with the tilt and the players added channel by channel |
| `to_robot` (Null) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back; `reachy_twin` shows the same as a picture |

The options are yours. Change a description and ask again: the description is all the
model knows about an option. For a new option add a row to `options`; to let it move
the robot, copy a `pick_` and `play_` pair, name the option in the Select, choose a
**Clip** in the player and wire its `_out` into `motion`. The option `nothing` has no
player: the robot stays as it is.

To say the sentence instead of typing it, click `speech` and switch **Listen** on
([`speech_signal`](3-sense.md#what-was-said-the-speech_signal-component)). The `readme` in the project has
the steps.

## A decision as channels: the brain_signal component

[`touchdesigner/brain_signal.tox`](../touchdesigner/brain_signal.tox) takes a sentence
and a list of options and asks a **decision model** which option fits. A decision
model is not a chat model: it gets a text and the options, each with a line that says
when it fits, and returns how likely each option is. Nothing else comes back, no text.

Type a sentence into **Text** on the Brain page and press Enter; **Ask** asks the same
sentence again. **Status** shows what was chosen and how sure the model is, for
example `tev1: yes (0.83)`.

- **Input 1, the options** (optional): a table with a row per option, under a first
  row that names the columns: `name`, `description`, `keywords`. The description is
  what the model reads. Without a table the component uses its own: yes, no, maybe,
  look_around, nothing. A name becomes part of a channel name: small letters, digits
  and `_`. The models here take 2 to 26 options.
- **Input 2, a sentence** (optional): a DAT, such as a `speech_signal`'s second output
  or a Text DAT. When its text changes, it is asked like a typed sentence.

| Channel | Values | Meaning |
| ------- | ------ | ------- |
| `brain/<option>` | 0 … 1 | how likely the model finds this option; stays until the next answer |
| `brain/pick/<option>` | 0 or 1 | 1 for a fifth of a second on the chosen option when an answer arrives: a trigger |
| `brain/confidence` | 0 … 1 | how sure the model is of its choice. It says how much one option stands out, not whether the choice is right. |
| `brain/thinking` | 0 or 1 | 1 while a question is out and no answer is back |
| `brain/age` | seconds | how long ago the last answer came (before the first: since the start) |
| `brain/fallback` | 0 or 1 | 1 when the last answer came from the keywords, because no model answered |

**Answered By**, on the Model page, chooses who is asked:

| Answered By | Where the sentence goes | What it needs |
| ----------- | ----------------------- | ------------- |
| **Tev1, on this computer** | nowhere: the model runs on this computer | [Ollama](https://ollama.com/) 0.35 or later, and once in a terminal: `ollama pull tev1` |
| **Nimble, on this computer** | nowhere | Ollama, and `ollama pull nimble`. A larger model that needs much more memory. |
| **Jev, in the cloud** | to a service on the internet (OpenRouter), with the options | a key, see below |
| **Keywords only** | nowhere | nothing. It understands nothing, see below. |
| **Another model or address** | to **Address**: Ollama on another computer, a relay | **Model** and **Address** |

- **The first answer** of a model on this computer takes a few seconds, because the
  model is loaded then. After that an answer took well under a second on the MacBook
  Pro it was measured on (Tev1 0.7 s, Jev 0.3 s). Ollama keeps the model loaded for ten
  minutes after an answer. Loaded, Tev1 took about 6.5 GB of memory there and Nimble
  about twice that: on a laptop with 16 GB, choose Tev1.
- **How well they choose** was tried with 32 sentences in German and English (the
  expected choices are one person's): Jev and Tev1 chose the expected option every
  time, Nimble 29 times, the keywords 21 times.
- **The key for Jev** is never typed into a parameter, because it would be saved with
  the project. It is the first line of a text file `brain_key.txt` in the project
  folder (or the file named in **Key File**). Git leaves that file out, and the key is
  only ever sent to an address that begins with `https`.
- **The keywords** answer when no model does: Ollama is not running, the model is not
  pulled, there is no key, or no answer came within **Timeout** (30 s). An option gets
  a point for each of its keywords found in the sentence, and an option with `*` as
  its keyword is the answer when none is found. Status then begins with `keyword
  match:` and says why, and `brain/fallback` is 1. It is crude on purpose: it keeps
  the robot reacting, and it understands nothing.
- **Question**, on the Brain page, is what the model is asked about the sentence. It
  starts as *Which reaction fits what was said to the robot?*

A signal never moves anything by itself. What `think_start.toe` does with it:

- **The choice plays a clip:** **Select** (`brain/pick/yes`) into the second input of
  a `clip_player` that holds the clip.
- **It shows that it thinks:** **Select** (`brain/thinking`) → **Math** (Multiply 8) →
  **Rename** (to `reachy/head/roll`) → **Lag** (0.3 up, 0.6 down): the head tilts
  until the answer is there.

And one more: **Select** (`brain/confidence`) → **Logic** (Convert Input *Off When
Outside Bounds*, Bounds 0 to 0.45) gives 1 while the last answer was an unsure one
(and before the first answer): a reason to hesitate instead of answering.
