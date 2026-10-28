"""Get the models of Module 4 ready on this computer: check Ollama, fetch a decision
model for brain_signal and a chat model for answer, ask each one sentence.

    python -m td_reachy.think_setup             # Tev1, and Gemma 3 for answers
    python -m td_reachy.think_setup --model nimble
    python -m td_reachy.think_setup --answer none   # the decision model only

setup-think.command / setup-think.bat run this. It does not install Ollama: its
installer asks for the computer's password and differs from system to system, so that
step stays with whoever sits at the computer (https://ollama.com/download). Everything
after it is done here, and each step says what is wrong when it cannot go on.

The questions it asks at the end are the ones the components ask - for brain_signal a
sentence and options with a line each, for answer the same sentence as a conversation -
at the addresses they use, so an answer here means the components will get one too.
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
ANSWER = "gemma3:4b"              # the chat model an answer component asks
# What `ollama pull` downloads.
SIZES = {"tev1": "4.4 GB", "nimble": "9.3 GB", "gemma3:4b": "3.3 GB"}
SENTENCE = "Hello, is anyone there?"
QUESTION = "Which reaction fits what was said to the robot?"
OPTIONS = {
    "yes": "A nod. The robot agrees with what was said, says yes, or likes it.",
    "no": "A shake of the head. The robot disagrees, says no, does not want this, or is "
          "told to stop or leave something be.",
    "look_around": "A look around. Someone greets the robot, calls it, or asks who is there.",
    "nothing": "No reaction. What was said is not meant for the robot or needs no answer.",
}
# What an answer component tells its model first (answer_chat.py's, shorter).
CHAT = ("You are a small robot on a table. You are curious, friendly and a little cheeky. "
        "People talk to you, and you answer out loud. Answer with one or two short sentences, "
        "at most 25 words. Answer in English.")
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


def reply(model, post=post, clock=time.perf_counter):
    """One sentence, as an answer component asks it: (what the model said, seconds)."""
    began = clock()
    said = post("/v1/chat/completions", {
        "model": model, "max_tokens": 75, "stream": False, "keep_alive": "10m",
        "reasoning_effort": "none",
        "messages": [{"role": "system", "content": CHAT}, {"role": "user", "content": SENTENCE}]})
    first = (said.get("choices") or [{}])[0]
    text = ((first if isinstance(first, dict) else {}).get("message") or {}).get("content")
    if not isinstance(text, str) or not text.strip():
        raise Stop(f"{model} answered, but with no words: {str(said)[:200]}")
    return " ".join(text.split()), clock() - began


def setup(model=MODEL, answer=ANSWER, out=print, **how):
    """All steps. answer: the chat model as well, or None. `how` replaces what talks to
    the outside, for the tests."""
    get_, post_ = how.get("get", get), how.get("post", post)
    find, run = how.get("find", find_ollama), how.get("run", subprocess.run)
    models = [(model, "decides: brain_signal")] + ([(answer, "answers: answer")] if answer else [])
    total = len(models) + 2
    out(f"\n== 1/{total}  Ollama")
    out(f"Ollama {check_ollama(get_, find)} is running.")
    for step, (name, what) in enumerate(models, start=2):
        out(f"\n== {step}/{total}  The model {name}, which {what}")
        if have(name, get_):
            out("It is on this computer already.")
        else:
            size = SIZES.get(name)
            out(f"Downloading it{f' (about {size})' if size else ''} ...")
            fetch(name, run, find)
    out(f"\n== {total}/{total}  Check: one sentence, as TouchDesigner will ask it")
    out("The first answer takes a few seconds: the model is loaded then.")
    choice, sure, seconds = ask(model, post_)
    out(f'"{SENTENCE}" -> {model} chose {choice} ({sure:.2f}) after {seconds:.1f} s')
    if answer:
        said, seconds = reply(answer, post_)
        out(f'"{SENTENCE}" -> {answer} said "{said}" after {seconds:.1f} s')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", default=MODEL,
                        help=f"the decision model to get ready (default: {MODEL})")
    parser.add_argument("--answer", default=ANSWER,
                        help=f"the chat model that answers (default: {ANSWER}; none: skip it)")
    args = parser.parse_args(argv)
    answer = None if args.answer.strip().lower() in ("", "none") else args.answer.strip()
    try:
        setup(args.model, answer)
    except Stop as e:
        print(f"\nSetup stopped: {e}")
        return 1
    print(f"\nReady. In TouchDesigner: click brain, Model page, Answered By: {args.model.title()}.")
    if answer:
        print(f"answer asks {answer} whenever Ollama runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
