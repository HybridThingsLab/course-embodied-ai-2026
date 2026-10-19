#!/bin/bash
# Speaking, for the speaker component, on macOS: double-click this file in Finder (or
# run `bash setup-speak.command`). Run setup.command first.
# Installs the speaker's packages into the project's environment, fetches Kokoro's
# model (about 350 MB) and says a sentence, so that the speaker in TouchDesigner speaks
# at once. The other engines - Supertonic, Piper - fetch theirs the first time they
# speak; Edge's voices need none. Safe to run again: what is already there is skipped.

cd "$(dirname "$0")" || exit 1

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
fail() {
    printf '\n\033[31mSetup stopped: %s\033[0m\n' "$1"
    echo "Details are above. docs/4-think.md says more."
    exit 1
}

step "1/3  The project's environment"
[ -x .venv/bin/python ] || fail "there is no .venv folder yet: run setup.command first"
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null 2>&1 || fail "uv was not found: run setup.command first"
echo "Found."

step "2/3  The speaker's packages"
uv pip install --python .venv/bin/python -e ".[speak]" || fail "the installation failed"

step "3/3  Kokoro's model, and a sentence to hear"
.venv/bin/python -m td_reachy.speaker --prepare || fail "Kokoro could not be made ready"

printf '\n\033[32mSpeaking is ready.\033[0m\n'
echo "In TouchDesigner: click speaker, Speaker page, type a sentence into Text, Enter."
