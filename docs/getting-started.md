# Getting started

From nothing installed to a **Reachy Mini moving in a 3D simulation** — no robot
required. Works on **macOS** and **Windows**; assumes basic command-line familiarity.

> **Reading the commands:** type them exactly as shown, one at a time. Everything —
> including `.[sim]` — is literal.

> No physical robot needed. To use real hardware later, see
> [working-with-the-robot.md](working-with-the-robot.md) — same files, only the way
> you start things changes.

## How it works

- **The daemon** owns the robot (or the simulator) and runs in the background.
- **The bridge** passes messages between TouchDesigner and the daemon.
- **The station** starts both with one command (Step 4).

```
  TouchDesigner ──OSC──▶ bridge ──▶ daemon ──▶ simulated (or real) robot
```

## 1. Get the code

```bash
git clone https://github.com/HybridThingsLab/sense-think-move.git
```

```bash
cd sense-think-move
```

No git? [GitHub Desktop](https://desktop.github.com/) or the repository's
**Code → Download ZIP** also work.

## 2. Run the setup

In the project folder, double-click:

- **macOS:** `setup.command`
- **Windows:** `setup.bat`

It installs [`uv`](https://docs.astral.sh/uv/) (the tool that manages Python) if
needed, creates the project's own Python 3.12 environment, installs the robot
software and the simulator (a few hundred MB), and finally starts everything once as
a check. That first start can take a few minutes. It ends with **Setup complete** —
then continue with [step 5](#5-move-it-from-touchdesigner). Running it again is safe.

If the system blocks the file because it was downloaded:

- **macOS** ("cannot be opened" / "Apple could not verify"): open **System Settings →
  Privacy & Security** and click **Open Anyway** next to the message, or run
  `bash setup.command` in a terminal in the project folder.
- **Windows** ("Windows protected your PC"): click **More info → Run anyway**.

Prefer to see every step? Steps 3 and 4 below do the same by hand.

## 3. Or by hand: install `uv`

[`uv`](https://docs.astral.sh/uv/) manages the Python environment and installs the
required Python 3.12 for you.

- **macOS:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Open a new terminal afterward, then check with `uv --version`.

### Set up the project

Run these three commands **one at a time, in this order**, from the project folder.
Wait for each to finish before typing the next.

**a. Create an isolated Python 3.12 environment** (a `.venv` folder):

```bash
uv venv --python 3.12 --managed-python
```

`--managed-python` makes `uv` use its own copy of Python 3.12, whatever else is
installed on the computer, so every computer runs the same Python.

**b. Activate it** — the prompt then starts with the folder name in parentheses:

- macOS: `source .venv/bin/activate`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`

**c. Install the project** — the robot software, the bridge and the MuJoCo
simulator (a few hundred MB, the first time):

```bash
uv pip install -e ".[sim]"
```

Steps a and c are needed only once. Step b is needed **in every new terminal**:
if a command says `No module named td_reachy`, activate first.

## 4. Start the simulator and the bridge

```bash
python -m td_reachy.station
```

After 10–20 seconds a window opens with the robot, it wakes up, and the terminal
ends with the line below. The very first start after installing can take a few
minutes.

```
[station] ready: TouchDesigner: OSC Out CHOP → 127.0.0.1:7000, OSC In CHOP ← port 7001
```

Leave it running while you work; **Ctrl+C** stops everything. On a slow machine,
`python -m td_reachy.station --headless` runs the simulator without the window.

Prefer a graphical app? Pollen's
[Reachy Mini desktop app](https://github.com/pollen-robotics/reachy-mini-desktop-app/releases)
can run the simulator too. Start it in **simulation mode** first; the station then
uses it and only adds the bridge.

## 5. Move it from TouchDesigner

Install TouchDesigner ([touchdesigner.md](touchdesigner.md), step 1), then open the
first project, `touchdesigner/puppet_start.toe`: [1-puppet.md](1-puppet.md). To send
values by hand instead, see step 3 there.

## Troubleshooting

- **`command not found: uv`** — open a new terminal (macOS: or run
  `export PATH="$HOME/.local/bin:$PATH"`).
- **`No module named td_reachy`** or **`missing Python packages`** — activate the
  environment in this terminal (step 3b).
- **Windows: `Activate.ps1 … running scripts is disabled`** — run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use
  `.venv\Scripts\activate.bat`.
- **The station stops with an error** — its last `[station] error:` line says what
  to do. More in [touchdesigner.md](touchdesigner.md#troubleshooting) and
  [simulation.md](simulation.md).

## More

[touchdesigner.md](touchdesigner.md) · the modules: [1-puppet.md](1-puppet.md),
[2-animate.md](2-animate.md), [3-sense.md](3-sense.md), [4-think.md](4-think.md) ·
[robot-channels.md](robot-channels.md) · [simulation.md](simulation.md) ·
[working-with-the-robot.md](working-with-the-robot.md)
