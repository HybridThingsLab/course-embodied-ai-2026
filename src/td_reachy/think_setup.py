"""Get a decision model ready on this computer, for brain_signal: check Ollama, fetch
the model, ask it one sentence.

    python -m td_reachy.think_setup             # Tev1
    python -m td_reachy.think_setup --model nimble

setup-think.command / setup-think.bat run this. It does not install Ollama: its
installer asks for the computer's password and differs from system to system, so that
step stays with whoever sits at the computer (https://ollama.com/download). Everything
after it is done here, and each step says what is wrong when it cannot go on.

The question it asks at the end is the one a brain_signal asks - a sentence, and
options with a line each - at the address a brain_signal uses, so an answer here means
the component will get one too.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOST = "http://localhost:11434"   # where Ollama answers on this computer
NEEDED = (0, 35)                  # the first Ollama that serves decision models
MODEL = "tev1"
SIZES = {"tev1": "4.4 GB", "nimble": "9.3 GB"}   # what `ollama pull` downloads
SENTENCE = "Hello, is anyone there?"
QUESTION = "Which reaction fits what was said to the robot?"
OPTIONS = {
    "yes": "A nod. The robot agrees, says yes, or likes what it hears.",
    "no": "A shake of the head. The robot disagrees, says no, or does not want this.",
    "look_around": "A look around. Someone greets the robot, calls it, or asks who is there.",
    "nothing": "No reaction. What was said is not meant for the robot or needs no answer.",
}
DOWNLOAD = "https://ollama.com/download"


class Stop(Exception):
    """A step cannot go on; the message says what to do."""


def version(text):
    """'0.40.3', or 'ollama version is 0.40.3' -> (0, 40, 3). () when there is none."""
    for word in str(text).split():
        parts = word.strip("v").split(".")
        if len(parts) >= 2 and all(p.split("-")[0].isdigit() for p in parts[:2]):
            return tuple(int(p.split("-")[0]) for p in parts if p.split("-")[0].isdigit())
    return ()


def find_ollama(which=shutil.which, exists=os.path.exists, platform=sys.platform, env=None):
    """The ollama program: on the PATH, or where its app keeps it."""
    env = os.environ if env is None else env
    found = which("ollama")
    if found:
        return found
    if platform == "darwin":
        places = ["/Applications/Ollama.app/Contents/Resources/ollama"]
    elif platform == "win32":
        places = [str(Path(env.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe")]
    else:
        places = ["/usr/local/bin/ollama", "/usr/bin/ollama"]
    return next((place for place in places if exists(place)), None)


def get(path, timeout=5.0):
    with urllib.request.urlopen(HOST + path, timeout=timeout) as answer:
        return json.loads(answer.read().decode("utf-8"))


def post(path, body, timeout=180.0):
    request = urllib.request.Request(HOST + path, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return json.loads(answer.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # Ollama says why in the body
        try:
            said = json.loads(e.read().decode("utf-8")).get("error", "")
        except ValueError:
            said = ""
        raise Stop(f"Ollama answered {e.code}: {said or e.reason}") from None


def check_ollama(get=get, find=find_ollama):
    """Ollama is installed, running and new enough: its version as text."""
    if find() is None:
        raise Stop(f"Ollama is not installed. Install it from {DOWNLOAD} (it asks for this "
                   "computer's password), start it, then run this again.")
    try:
        said = get("/api/version").get("version", "")
    except (OSError, ValueError):
        raise Stop("Ollama is installed but does not answer. Start the Ollama app (or "
                   "`ollama serve` in a terminal), then run this again.") from None
    if version(said) < NEEDED:
        need = ".".join(str(n) for n in NEEDED)
        raise Stop(f"Ollama {said} is too old for decision models: {need} or later is "
                   f"needed. Update it from {DOWNLOAD}, then run this again.")
    return said


def have(model, get=get):
    """Whether the model is on this computer already."""
    names = [m.get("name", "") for m in get("/api/tags").get("models", [])]
    return any(name == model or name.split(":")[0] == model for name in names)


def fetch(model, run=subprocess.run, find=find_ollama):
    """`ollama pull`, with its own progress on the screen."""
    try:
        done = run([find(), "pull", model])
    except OSError as e:
        raise Stop(f"ollama pull could not be started: {e}") from None
    if done.returncode != 0:
        raise Stop(f"ollama pull {model} did not finish (exit {done.returncode}). Its own "
                   "words are above; with no connection, try again later.")


def ask(model, post=post, clock=time.perf_counter):
    """One sentence, as a brain_signal asks it: (the choice, how sure, seconds)."""
    began = clock()
    said = post("/v1/systemone", {
        "model": model, "state": SENTENCE, "keep_alive": "10m",
        "questions": {"reaction": {"type": "choice", "instructions": QUESTION,
                                   "criteria": OPTIONS}}})
    answer = (said.get("answers") or {}).get("reaction") or {}
    choice = answer.get("choice")
    if choice not in OPTIONS:
        raise Stop(f"{model} answered, but not with one of the options: {str(said)[:200]}")
    return choice, float(answer.get("confidence") or 0.0), clock() - began


def setup(model=MODEL, out=print, **how):
    """All steps. `how` replaces what talks to the outside, for the tests."""
    get_, post_ = how.get("get", get), how.get("post", post)
    find, run = how.get("find", find_ollama), how.get("run", subprocess.run)
    out("\n== 1/3  Ollama")
    out(f"Ollama {check_ollama(get_, find)} is running.")
    out(f"\n== 2/3  The model {model}")
    if have(model, get_):
        out("It is on this computer already.")
    else:
        size = SIZES.get(model)
        out(f"Downloading it{f' (about {size})' if size else ''} ...")
        fetch(model, run, find)
    out("\n== 3/3  Check: one sentence, as TouchDesigner will ask it")
    out("The first answer takes a few seconds: the model is loaded then.")
    choice, sure, seconds = ask(model, post_)
    out(f'"{SENTENCE}" -> {model} chose {choice} ({sure:.2f}) after {seconds:.1f} s')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", default=MODEL, help=f"the model to get ready (default: {MODEL})")
    args = parser.parse_args(argv)
    try:
        setup(args.model)
    except Stop as e:
        print(f"\nSetup stopped: {e}")
        return 1
    print(f"\nReady. In TouchDesigner: click brain, Model page, Answered By: {args.model.title()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
