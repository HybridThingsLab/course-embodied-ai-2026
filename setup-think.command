#!/bin/bash
# The models on this computer for the brain_signal and answer components, on macOS:
# double-click this file in Finder (or run `bash setup-think.command`). Run
# setup.command first, and install Ollama from https://ollama.com/download - that one
# step is yours, because its installer asks for this computer's password.
# Then this checks Ollama, downloads the models Tev1 (about 4.4 GB), which decides, and
# Gemma 3 (about 3.3 GB), which answers, and asks each one sentence. Safe to run again:
# what is already there is skipped.

cd "$(dirname "$0")" || exit 1

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
fail() {
    printf '\n\033[31mSetup stopped: %s\033[0m\n' "$1"
    echo "Details are above. docs/4-think.md says more."
    exit 1
}

step "The project's environment"
[ -x .venv/bin/python ] || fail "there is no .venv folder yet: run setup.command first"
echo "Found."

.venv/bin/python -m td_reachy.think_setup "$@" || fail "the models are not ready yet"

printf '\n\033[32mThe models are ready.\033[0m\n'
