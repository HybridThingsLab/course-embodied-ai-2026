#!/bin/bash
# One-time setup on macOS: double-click this file in Finder (or run `bash setup.command`).
# Installs uv if needed, creates the project's Python environment (.venv), installs
# the robot software and the simulator, then starts everything once as a check.
# Safe to run again: steps that are already done are skipped or quick.

cd "$(dirname "$0")" || exit 1

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
fail() {
    printf '\n\033[31mSetup stopped: %s\033[0m\n' "$1"
    echo "Details are above. The troubleshooting list in docs/getting-started.md covers the usual causes."
    exit 1
}

step "1/4  uv (manages Python)"
export PATH="$HOME/.local/bin:$PATH"
if command -v uv >/dev/null 2>&1; then
    echo "uv is installed: $(uv --version)"
else
    echo "Installing uv from astral.sh ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || fail "uv could not be installed"
    command -v uv >/dev/null 2>&1 || fail "uv was installed but can't be found"
fi

step "2/4  Python environment (.venv)"
if [ -x .venv/bin/python ]; then
    echo "Already there - keeping it. (To start fresh, delete the .venv folder and run this again.)"
else
    uv venv --python 3.12 --managed-python || fail "the environment could not be created"
fi

step "3/4  Robot software, bridge and simulator (a few hundred MB the first time)"
uv pip install --python .venv/bin/python -e ".[sim]" || fail "the installation failed"

step "4/4  Check: start the simulator and the bridge once, then stop"
echo "The very first start can take a few minutes."
.venv/bin/python -m td_reachy.station --headless --check || fail "the check did not pass"

printf '\n\033[32mSetup complete.\033[0m\n'
echo "Next: install TouchDesigner and follow docs/touchdesigner.md."
echo "From now on the robot software starts from TouchDesigner (reachy_hub's Station page),"
echo "or in a terminal: .venv/bin/python -m td_reachy.station"
