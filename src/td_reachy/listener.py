"""The listener: a microphone in, sentences out - on this computer.

    python -m td_reachy.listener                     # listens and prints what it hears
    python -m td_reachy.listener --language en
    python -m td_reachy.listener --post http://127.0.0.1:9982    # tells a speech_signal
    python -m td_reachy.listener --prepare           # fetch the model, list the microphones

It cuts what the microphone hears into utterances by loudness (an utterance ends after
a pause), writes each one down with Whisper (the faster-whisper library) and hands the
sentence on. Nothing leaves the computer. In TouchDesigner the speech_signal component
starts it (Heard By: Whisper) with --post and --managed, and stops it again.

It needs the optional packages: double-click setup-listen in the project folder, or
uv pip install -e ".[listen]" (setup-listen also fetches the model).
The model is downloaded the first time (small: 0.5 GB). Whisper works on a window of
30 seconds whatever the length of the utterance, so a sentence takes as long as the
model needs for that: with small about half a second on a laptop's processor, with
--model large-v3-turbo (1.6 GB) a few seconds - that one hears more exactly.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import queue
import sys
import threading
import time
import urllib.request
import wave

import numpy as np

RATE = 16000          # samples per second, what Whisper takes
BLOCK = 480           # samples the loudness is looked at over: 30 ms
MODEL = "small"
SIZES = {"small": "0.5 GB", "base": "0.15 GB", "large-v3-turbo": "1.6 GB"}  # the download
LEAST = 0.004         # the loudness (RMS) below which nothing counts as speech
ABOVE_NOISE = 4.0     # ... and so many times the room's noise, where that is more
ONSET = 2             # blocks of speech in a row before an utterance begins
PAUSE = 0.7           # seconds of quiet that end an utterance
BEFORE = 0.3          # seconds kept from before its first loud block
SHORTEST = 0.25       # seconds of speech an utterance needs to count
LONGEST = 15.0        # seconds after which an utterance is cut
AGAIN = 1.0           # seconds between two words to a speech_signal, so it knows we are there
STEADY = 0.1          # a sound whose loudness varies less than this is no speech: see varies()


class Segmenter:
    """Cuts a stream of sound into utterances by loudness. feed() takes samples (floats
    from -1 to 1, RATE per second) and returns what happened: ("start",) when someone
    begins to speak, ("end", samples) with the whole utterance once they pause."""

    def __init__(self, pause=PAUSE, least=LEAST):
        self.pause, self.least = pause, least
        self.rest = np.zeros(0, dtype=np.float32)   # samples that do not fill a block yet
        self.noise = None                           # how loud the room is when nobody speaks
        self.recent = []                            # the last blocks, for BEFORE
        self.heard = None                           # the blocks of the open utterance
        self.loud = self.quiet = self.spoken = 0    # blocks in a row; blocks of speech in it

    def feed(self, samples):
        events = []
        data = np.concatenate([self.rest, np.asarray(samples, dtype=np.float32).ravel()])
        whole = len(data) // BLOCK * BLOCK
        self.rest = data[whole:]
        for start in range(0, whole, BLOCK):
            events.extend(self._block(data[start:start + BLOCK]))
        return events

    def _block(self, block):
        rms = float(np.sqrt(np.mean(block * block)))
        if self.noise is None:  # listening may begin in the middle of a word
            self.noise = min(rms, self.least)
        # The room's noise: followed down at once and up only slowly, so that speech
        # does not count as noise but a room that has become louder does, in time.
        self.noise += (0.3 if rms < self.noise else 0.0005) * (rms - self.noise)
        speech = rms > max(self.least, self.noise * ABOVE_NOISE)
        if self.heard is None:  # nobody speaks: wait for an onset
            self.recent = (self.recent + [block])[-round(BEFORE * RATE / BLOCK):]
            self.loud = self.loud + 1 if speech else 0
            if self.loud < ONSET:
                return []
            self.heard, self.quiet, self.spoken = list(self.recent), 0, self.loud
            return [("start",)]
        self.heard.append(block)
        self.quiet = 0 if speech else self.quiet + 1
        self.spoken += speech
        over = self.quiet * BLOCK / RATE >= self.pause
        if not over and len(self.heard) * BLOCK / RATE < LONGEST:
            return []
        heard, spoken = self.heard, self.spoken
        self.heard, self.recent, self.loud = None, [], 0
        if spoken * BLOCK / RATE < SHORTEST:  # a click, a cough
            return [("end", None)]
        keep = len(heard) - max(0, self.quiet - round(0.2 * RATE / BLOCK)) if over else len(heard)
        return [("end", np.concatenate(heard[:keep]))]


def varies(samples):
    """How much the loudness of an utterance varies over its loud blocks: the width of
    their middle half over their median, so that the blocks where it begins and ends
    do not count. Speech rises and falls with every syllable (0.22 and more for the
    course's test sentences); a hum, a fan, a motor running evenly stays where it is
    (0.02 and less). Whisper writes a sentence down for some of those - a steady tone at
    the pitch of a voice becomes "Vielen Dank." - so what does not vary is not given to it."""
    whole = len(samples) // BLOCK * BLOCK
    if not whole:
        return 0.0
    rms = np.sqrt(np.mean(np.asarray(samples[:whole], dtype=np.float32).reshape(-1, BLOCK) ** 2,
                          axis=1))
    loud = rms[rms > 0.25 * rms.max()]
    if not len(loud):  # silence
        return 0.0
    low, middle, high = np.percentile(loud, [25, 50, 75])
    return float((high - low) / middle)


def resample(samples, rate):
    """Samples at another rate, as RATE per second (straight lines between them)."""
    if rate == RATE or not len(samples):
        return np.asarray(samples, dtype=np.float32)
    there = np.arange(0, len(samples), rate / RATE)
    return np.interp(there, np.arange(len(samples)), samples).astype(np.float32)


def read_wav(path):
    """A .wav file as floats from -1 to 1 at RATE, its first channel."""
    with wave.open(str(path)) as w:
        if w.getsampwidth() != 2:
            raise SystemExit(f"{path}: 16-bit .wav files only")
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        samples = data.reshape(-1, w.getnchannels())[:, 0].astype(np.float32) / 32768
        return resample(samples, w.getframerate())


class Whisper:
    """Writes an utterance down. The model is loaded once, on this computer."""

    def __init__(self, model=MODEL, language="de"):
        # The model is public: no login is needed, and none that happens to be stored on
        # this computer is sent along (an expired one makes the download fail).
        os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
        try:
            import ctranslate2
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise SystemExit(f"{e}. Install the listener's packages first: double-click "
                             'setup-listen in the project folder (or: uv pip install -e '
                             '".[listen]")') from None
        self.language = None if language in ("", "auto") else language
        if ctranslate2.get_cuda_device_count():
            where = {"device": "cuda", "compute_type": "float16"}
        else:  # on Apple's processors floats are the faster way, elsewhere 8-bit numbers
            apple = sys.platform == "darwin" and platform.machine() == "arm64"
            where = {"device": "cpu", "compute_type": "float32" if apple else "int8",
                     "cpu_threads": min(8, os.cpu_count() or 4)}
        self.model = WhisperModel(model, **where)

    def write(self, samples):
        segments, _info = self.model.transcribe(
            samples, language=self.language, beam_size=1, vad_filter=True,
            condition_on_previous_text=False, without_timestamps=True)
        return " ".join(segment.text.strip() for segment in segments).strip()


class Teller:
    """Hands on what is heard: to a speech_signal (--post), and to the terminal."""

    def __init__(self, address=None, out=print):
        self.address, self.out, self.deaf = (address or "").rstrip("/"), out, False
        self.last = None               # the state told last, for again()
        self.turn = threading.Lock()   # one word at a time: they arrive in their order

    def _post(self, path, body):
        if not self.address:
            return
        data = json.dumps(dict(body, by="whisper")).encode("ascii")
        req = urllib.request.Request(self.address + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=1.0).close()
            self.deaf = False
        except OSError as e:
            if not self.deaf:  # said once, not with every sentence
                self.out(f"[listener] nobody takes it at {self.address}: {e}")
            self.deaf = True

    def state(self, state, text=""):
        with self.turn:
            self.last = (state, text)
            self._post("/state", {"state": state, "text": text})

    def again(self):
        """The state once more: a speech_signal counts a listener it has not heard from
        for three seconds as gone, and one that missed a word hears it now."""
        with self.turn:
            if self.last and self.last[0] not in ("stopped", "error"):
                self._post("/state", {"state": self.last[0], "text": self.last[1]})

    def heard(self, text, seconds, took):
        self.out(f"[listener] heard ({seconds:.1f} s spoken, {took:.1f} s to write): {text}")
        with self.turn:
            self.last = ("listening", "")  # written down: it listens again
            self._post("/heard", {"text": text, "final": True})


def microphone(device, blocks):
    """An open microphone that puts what it hears into `blocks` as (samples, rate)."""
    try:
        import sounddevice
    except ImportError as e:
        raise SystemExit(f"{e}. Install the listener's packages first: double-click "
                         'setup-listen in the project folder (or: uv pip install -e '
                         '".[listen]")') from None

    def heard(indata, frames, when, status):
        blocks.put(indata[:, 0].copy())

    for rate in (RATE, None):  # at Whisper's rate where the device takes it, else its own
        try:  # in pieces of 30 ms at that rate: left to itself it may hand over 1 ms at a time
            stream = sounddevice.InputStream(samplerate=rate, channels=1, dtype="float32",
                                             blocksize=BLOCK if rate else 0,
                                             device=device, callback=heard)
            stream.start()
            return stream, int(stream.samplerate)
        except sounddevice.PortAudioError as e:
            error = e
    raise SystemExit(f"no microphone: {error}. On macOS, allow the program that started "
                     "this (System Settings, Privacy & Security, Microphone).")


def _again(tell, over):
    """Once a second, also while the model loads or a sentence is written down - both
    can take longer than a speech_signal waits for a word from its listener."""
    while not over.wait(AGAIN):
        tell.again()


def listen(args, stop):
    tell, over, stream = Teller(args.post), threading.Event(), None
    threading.Thread(target=_again, args=(tell, over), daemon=True).start()
    try:
        tell.state("loading", f"loading Whisper {args.model} (the first time it is downloaded)")
        print(f"[listener] loading Whisper {args.model} ...", flush=True)
        whisper = Whisper(args.model, args.language)
        cut = Segmenter(pause=args.pause)
        blocks = queue.Queue()
        if args.file:
            rate = RATE
            for path in args.file:  # each file, and a pause after it
                quiet = np.zeros(int(RATE * (args.pause + 0.5)), dtype=np.float32)
                blocks.put(np.concatenate([read_wav(path), quiet]))
        else:
            stream, rate = microphone(args.device, blocks)
        print(f"[listener] listening ({args.language}). Ctrl+C stops it.", flush=True)
        tell.state("listening")
        while not stop.is_set():
            try:
                samples = blocks.get(timeout=0.2)
                while not blocks.empty() and not args.file:  # what has piled up meanwhile
                    samples = np.concatenate([samples, blocks.get()])
            except queue.Empty:
                if args.file:
                    break
                samples = None
            for event in cut.feed(resample(samples, rate)) if samples is not None else ():
                if event[0] == "start":
                    tell.state("hearing")
                    continue
                if event[1] is not None and varies(event[1]) < STEADY:
                    print(f"[listener] a steady sound of {len(event[1]) / RATE:.1f} s, no speech: "
                          "not written down", flush=True)
                elif event[1] is not None:
                    tell.state("writing")
                    began = time.perf_counter()
                    text = whisper.write(event[1])
                    if text:
                        tell.heard(text, len(event[1]) / RATE, time.perf_counter() - began)
                tell.state("listening")
    finally:
        over.set()
        if stream is not None:
            stream.stop()
            stream.close()
        tell.state("stopped")
        print("[listener] stopped", flush=True)


def prepare(model, language, out=print):
    """Before the first use (setup-listen): load the model, which downloads it the
    first time, and say which microphones there are. Listens to nothing."""
    size = SIZES.get(model)
    out(f"[listener] getting Whisper {model} ready"
        f"{f' (about {size} to download the first time)' if size else ''} ...")
    try:
        Whisper(model, language)
    except SystemExit:
        raise
    except Exception as e:  # no connection, a full disk: said plainly
        raise SystemExit(f"Whisper {model} could not be loaded: {type(e).__name__}: {e}") from None
    out(f"[listener] Whisper {model} is ready.")
    try:
        import sounddevice
        names = [d["name"] for d in sounddevice.query_devices() if d["max_input_channels"] > 0]
    except Exception as e:
        names = []
        out(f"[listener] the microphones could not be listed: {e}")
    out("[listener] microphones: " + (", ".join(names) or "none found"))


def _watch_stdin(stop):
    """--managed: stop when the parent closes the pipe, or says stop."""
    try:
        for line in sys.stdin:
            if line.strip() == "stop":
                break
    except (OSError, ValueError):
        pass
    stop.set()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--language", default="de", help="de, en, ... or auto (default: de)")
    parser.add_argument("--model", default=MODEL,
                        help=f"the Whisper model (default: {MODEL}; slower, more exact: turbo)")
    parser.add_argument("--post", metavar="ADDRESS",
                        help="a speech_signal's address, e.g. http://127.0.0.1:9982")
    parser.add_argument("--device", help="the microphone, by name or number (see --list)")
    parser.add_argument("--list", action="store_true", help="list the microphones and stop")
    parser.add_argument("--pause", type=float, default=PAUSE,
                        help=f"seconds of quiet that end an utterance (default: {PAUSE})")
    parser.add_argument("--file", nargs="+", metavar="WAV",
                        help="hear these .wav files instead of the microphone, then stop")
    parser.add_argument("--prepare", action="store_true",
                        help="fetch the model, list the microphones and stop")
    parser.add_argument("--managed", action="store_true",
                        help="for a parent program: stop when stdin closes or reads 'stop'")
    args = parser.parse_args(argv)
    if args.list:
        import sounddevice
        for i, d in enumerate(sounddevice.query_devices()):
            if d["max_input_channels"] > 0:
                print(f"{i}: {d['name']}")
        return
    if args.prepare:
        prepare(args.model, args.language)
        return
    if args.device and args.device.isdigit():
        args.device = int(args.device)
    stop = threading.Event()
    if args.managed:
        threading.Thread(target=_watch_stdin, args=(stop,), daemon=True).start()
    try:
        listen(args, stop)
    except KeyboardInterrupt:
        pass
    except SystemExit as e:  # something the user can fix: also told to the speech_signal
        if args.post and e.code not in (None, 0):
            Teller(args.post, out=lambda _line: None).state("error", str(e.code))
        raise


if __name__ == "__main__":
    main()
