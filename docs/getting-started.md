# Getting started

From nothing installed to a simulated Reachy Mini moving in TouchDesigner. Works on
macOS and Windows. No robot needed.

## 1. Install TouchDesigner

Download the free **Non-Commercial** edition from
[derivative.ca/download](https://derivative.ca/download) and install it. It needs a
reasonably capable graphics card.

## 2. Get the code

```bash
git clone https://github.com/HybridThingsLab/course-embodied-ai-2026.git sense-think-move
```

No git? [GitHub Desktop](https://desktop.github.com/) or **Code → Download ZIP** on the
repository's page work too.

## 3. Run the setup

In the project folder, double-click `setup.command` (macOS) or `setup.bat` (Windows).
It installs the robot software and the simulator (a few hundred MB) and starts them
once as a check, which can take a few minutes the first time. It ends with **Setup
complete**. Running it again is safe.

If the system blocks the file:

- **macOS** ("cannot be opened"): System Settings → Privacy & Security → **Open
  Anyway**, or run `bash setup.command` in a terminal in the project folder.
- **Windows** ("Windows protected your PC"): **More info → Run anyway**.

If it still does not run, or you would rather type each step yourself:
[manual-install.md](manual-install.md).

## 4. Open the first project

Open `touchdesigner/01_puppet.toe`, click `reachy_hub`, press **Start** on its
Station page and wait until **Status** says `ready`. `reachy_model` shows the simulated
robot: the simulator has no window of its own. Drag the value of `head_yaw` and it
turns. Continue with [Puppet](1-puppet.md).

## 5. Later: listening, a model, speaking

Some parts need one more setup each, also in the project folder:

- **`setup-listen`**, for [Sense](3-sense.md#what-was-said-the-speech_signal-component):
  Whisper, which writes down what is said (0.5 GB).
- **`setup-think`**, for [Think](4-think.md#tev1-step-by-step): install Ollama from
  [its site](https://ollama.com/download) and open it first; the setup then downloads
  the models Tev1 (4.4 GB) and Gemma 3 (3.3 GB).
- **`setup-speak`**, for [Think](4-think.md#a-voice-the-speaker-component): Kokoro, the
  robot's voice (350 MB). At the end it says a sentence.

## If Start does not work: the terminal

**Start** on `reachy_hub` runs the **station**: the simulator (or the connection to the
real robot) and a bridge that passes TouchDesigner's messages on. Its Status says what
went wrong, and its full output is in `station.log` in the project folder. To see it
directly, start the station in a terminal, in the project folder.

macOS:

```bash
source .venv/bin/activate
python -m td_reachy.station
```

Windows (PowerShell): `.venv\Scripts\Activate.ps1`, then the same `python` line.

Wait for `[station] ready` and leave it running; **Ctrl+C** stops it. Add `--headless`
for no simulator window, or `--robot` for the real robot.

- **`No module named td_reachy`**: the first line was left out, or the setup has not
  run.
- **Windows: `running scripts is disabled`**: run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use
  `.venv\Scripts\activate.bat`.
- **`UDP port 7000 is taken`** or **`port 8000 is taken`**: an earlier station is still
  running. Quit it, or on macOS `lsof -ti udp:7000 | xargs kill` (for 8000:
  `tcp:8000`); on Windows `netstat -ano | findstr 7000`, then
  `taskkill /PID <the number> /F`.

More in [simulator-and-robot.md](simulator-and-robot.md#when-something-goes-wrong).
