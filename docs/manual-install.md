# Installing by hand

What `setup.command` (macOS) and `setup.bat` (Windows) do, one command at a time: for
when a setup file does not run, or to see each step. Type the commands in a terminal,
in the project folder (the one with `setup.command` in it). On Windows, use
PowerShell.

## 1. uv

[uv](https://docs.astral.sh/uv/) installs Python and the packages.

macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then open a new terminal in the project folder, so that it finds uv. `uv --version`
prints its version.

## 2. The Python environment

```bash
uv venv --python 3.12 --managed-python
```

It makes the folder `.venv` with a Python of its own. If there is a `.venv` already,
skip this step, or add `--clear` to start fresh.

## 3. The robot software and the simulator

```bash
uv pip install -e ".[sim]"
```

A few hundred MB the first time. uv installs into the `.venv` of the folder it runs in.

## 4. The check

macOS:

```bash
.venv/bin/python -m td_reachy.station --headless --check
```

Windows:

```powershell
.venv\Scripts\python.exe -m td_reachy.station --headless --check
```

It starts the simulator and the bridge once and stops them again. The very first start
can take a few minutes. It ends with `[station] check: passed`. Continue with
[getting-started.md, step 4](getting-started.md#4-open-the-first-project).

## Later: listening, a model, speaking

The other setups, by hand. On Windows, write `.venv\Scripts\python.exe` where these say
`.venv/bin/python`.

- **Listening** (`setup-listen`): `uv pip install -e ".[listen]"`, then
  `.venv/bin/python -m td_reachy.listener --prepare`. It downloads Whisper's model and
  lists the microphones.
- **A model** (`setup-think`): install and open Ollama
  ([Think](4-think.md#tev1-step-by-step)), then
  `.venv/bin/python -m td_reachy.think_setup`. It downloads Tev1 and asks it a
  sentence.
- **Speaking** (`setup-speak`): `uv pip install -e ".[speak]"`, then
  `.venv/bin/python -m td_reachy.speaker --prepare`. It downloads Kokoro and says a
  sentence.
