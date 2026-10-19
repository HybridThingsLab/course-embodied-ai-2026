#!/bin/bash
# Listening, for the speech_signal component, on macOS: double-click this file in
# Finder (or run `bash setup-listen.command`). Run setup.command first.
# Installs Whisper's packages into the project's environment and fetches its model
# (about 0.5 GB), so that switching Listen on in TouchDesigner works at once.
# Safe to run again: what is already there is skipped.

cd "$(dirname "$0")" || exit 1

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
fail() {
    printf '\n\033[31mSetup stopped: %s\033[0m\n' "$1"
    echo "Details are above. docs/3-sense.md says more."
    exit 1
}

step "1/3  The project's environment"
[ -x .venv/bin/python ] || fail "there is no .venv folder yet: run setup.command first"
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null 2>&1 || fail "uv was not found: run setup.command first"
echo "Found."

step "2/3  Whisper's packages"
uv pip install --python .venv/bin/python -e ".[listen]" || fail "the installation failed"

step "3/3  Whisper's model, and the microphones"
.venv/bin/python -m td_reachy.listener --prepare || fail "Whisper could not be made ready"

printf '\n\033[32mListening is ready.\033[0m\n'
echo "In TouchDesigner: click speech_signal, Speech page, switch Listen on."
echo "The first time, the system may ask whether TouchDesigner may use the microphone."
