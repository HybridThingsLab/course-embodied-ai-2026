"""The speaker: sentences in, a voice out - on this computer's speaker, or the robot's.

    python -m td_reachy.speaker "Hello, I am Reachy."             # says it (Kokoro)
    python -m td_reachy.speaker --engine edge "Hello there!"
    python -m td_reachy.speaker --engine piper --language de "Hallo, ich bin Reachy."
    python -m td_reachy.speaker --device "Reachy Mini Audio" "Hello from my head."
    python -m td_reachy.speaker --list                            # engines, voices, outputs
    python -m td_reachy.speaker --prepare                         # fetch Kokoro, say a sentence
    python -m td_reachy.speaker --prepare --engine piper          # ... or another engine
    python -m td_reachy.speaker --managed --post http://127.0.0.1:9984   # for a speaker

Four engines make the voice, three of them on this computer:
  kokoro      the default: natural English voices (US and British), no German.
              Its model (about 350 MB) is downloaded the first time.
  edge        the voices of Microsoft Edge's "read aloud", English and German: the text
              goes to Microsoft, no key is needed. It needs the internet, has no licence
              for what it says, and has stopped working for days now and then.
  supertonic  English and German, ten voices (M1-M5, F1-F5); 385 MB the first time.
  piper       English and German, the fastest; each voice about 60 MB the first time.

The program plays the sound itself and tells a speaker component in TouchDesigner
(--post) when it begins, how long it lasts and how loud it is, a value per 1/30 s: the
component makes speaker/* channels of that, to move the robot with its voice. In
TouchDesigner the speaker component starts it with --managed and sends it sentences on
its stdin, one JSON object a line.

It needs the optional packages: double-click setup-speak in the project folder, or
uv pip install -e ".[speak]" (setup-speak also fetches Kokoro and says a sentence).
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import logging
import os
import queue
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

ENGINES = ("kokoro", "edge", "supertonic", "piper")
ENGINE = "kokoro"
LANGUAGE = "en"
VOICES = {  # the voice each engine starts with, per language
    ("kokoro", "en"): "bm_george",
    ("edge", "en"): "en-US-AvaMultilingualNeural",
    ("edge", "de"): "de-DE-SeraphinaMultilingualNeural",
    ("supertonic", "en"): "F1",
    ("supertonic", "de"): "F1",
    ("piper", "en"): "en_US-lessac-medium",
    ("piper", "de"): "de_DE-thorsten-medium",
}
PER_SECOND = 30       # loudness values per second, for speaker/level
AGAIN = 1.0           # seconds between two words to a speaker component, so it knows we are there
EDGE_WAIT = 15.0      # seconds edge-tts may take for a sentence (it has hung for minutes)
ESPEAK_LIMIT = 150    # espeak-ng (in Piper and Kokoro) fails at a data path of 160 characters
CACHE = Path(os.environ.get("SPEAKER_CACHE") or Path.home() / ".cache" / "sense-think-move")
KOKORO_FILES = {  # file -> where it comes from, its size
    "kokoro-v1.0.onnx": ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
                         "model-files-v1.0/kokoro-v1.0.onnx", "325 MB"),
    "voices-v1.0.bin": ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
                        "model-files-v1.0/voices-v1.0.bin", "28 MB"),
}
INSTALL = ("Install the speaker's packages first: double-click setup-speak in the project "
           'folder (or: uv pip install -e ".[speak]")')


class SpeakerError(Exception):
    """Something the user can fix; the message says what."""


def _need(module):
    try:
        return __import__(module)
    except ImportError as e:
        raise SpeakerError(f"{e}. {INSTALL}") from None


def short_espeak(data, name, cache=CACHE):
    """espeak-ng's data folder, at a path it can read. Built into Piper's and Kokoro's
    packages, espeak-ng cannot open its data from a path of 160 characters or more (it
    falls back to the folder it was built in, which is not there): a project in a deep
    folder gets a copy in the cache."""
    data = Path(data)
    if len(str(data)) < ESPEAK_LIMIT:
        return data
    copy = Path(cache) / "espeak-ng-data" / name
    if not copy.is_dir():
        shutil.copytree(data, copy)
    if len(str(copy)) >= ESPEAK_LIMIT:
        raise SpeakerError(f"the path to espeak-ng's data is too long ({copy}): "
                           "set SPEAKER_CACHE to a short folder")
    return copy


def download(url, path, size, out=print):
    """A file from the internet, once: written beside as .part and renamed when complete."""
    path = Path(path)
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    out(f"[speaker] downloading {path.name} ({size}, once) ...")
    part = path.with_name(path.name + ".part")
    try:
        with urllib.request.urlopen(url, timeout=30) as answer, open(part, "wb") as f:
            shutil.copyfileobj(answer, f, 1 << 20)
    except OSError as e:
        raise SpeakerError(f"{path.name} could not be downloaded ({e}): no internet?") from None
    part.replace(path)
    return path


# --- the engines: each turns a sentence into samples (floats, -1 to 1) and their rate -----

class Kokoro:
    """Kokoro-82M (Apache-2.0), through kokoro-onnx: English only, 24 kHz."""

    languages = ("en",)

    def __init__(self, cache=CACHE, out=print):
        kokoro_onnx = _need("kokoro_onnx")
        espeakng_loader = _need("espeakng_loader")
        files = {name: download(url, Path(cache) / "kokoro" / name, size, out)
                 for name, (url, size) in KOKORO_FILES.items()}
        data = short_espeak(espeakng_loader.get_data_path(), "kokoro", cache)
        os.environ["ESPEAK_DATA_PATH"] = str(data)  # what it reads; its own setting is not
        self.model = kokoro_onnx.Kokoro(str(files["kokoro-v1.0.onnx"]),
                                        str(files["voices-v1.0.bin"]))
        self.voices = sorted(v for v in self.model.get_voices() if v[:1] in ("a", "b"))

    def speak(self, text, voice, language, speed):
        if language != "en":
            raise SpeakerError("Kokoro speaks no German: choose edge, supertonic or piper")
        if voice not in self.voices:
            raise SpeakerError(f'Kokoro has no voice "{voice}" (it has: {", ".join(self.voices)})')
        samples, rate = self.model.create(text, voice=voice, speed=speed,
                                          lang="en-gb" if voice.startswith("b") else "en-us")
        return np.asarray(samples, dtype=np.float32), rate


class Edge:
    """Microsoft Edge's read-aloud voices, through edge-tts: in the cloud, MP3 at 24 kHz."""

    languages = ("en", "de")

    def __init__(self, cache=CACHE, out=print):
        self.edge_tts = _need("edge_tts")
        self.soundfile = _need("soundfile")

    async def _fetch(self, text, voice, rate):
        mp3 = bytearray()
        async for chunk in self.edge_tts.Communicate(text, voice, rate=rate).stream():
            if chunk["type"] == "audio":
                mp3 += chunk["data"]
        return bytes(mp3)

    def speak(self, text, voice, language, speed):
        if not voice.lower().startswith(language + "-"):
            raise SpeakerError(f'the edge voice "{voice}" does not speak {language}')
        rate = f"{round((speed - 1) * 100):+d}%"
        try:
            mp3 = asyncio.run(asyncio.wait_for(self._fetch(text, voice, rate), EDGE_WAIT))
        except TimeoutError:
            raise SpeakerError(f"edge: no voice from Microsoft's service in {EDGE_WAIT:.0f} s "
                               "(it hangs now and then: try again, or another engine)") from None
        except Exception as e:  # no internet, the service refused, a voice it does not know
            raise SpeakerError(f"edge: {type(e).__name__}: {e} (no internet? or the service "
                               "changed: uv pip install -U edge-tts)") from None
        if not mp3:
            raise SpeakerError(f'edge: no audio for the voice "{voice}"')
        samples, rate = self.soundfile.read(io.BytesIO(mp3), dtype="float32")
        return samples, rate


class Supertonic:
    """Supertonic 3 (MIT code, OpenRAIL-M weights): 31 languages, ten voices, 44.1 kHz."""

    languages = ("en", "de")
    voices = tuple(f"{kind}{n}" for kind in "MF" for n in range(1, 6))

    def __init__(self, cache=CACHE, out=print):
        # The model is public: no login is needed, and none that happens to be stored on
        # this computer is sent along (an expired one makes the download fail with 401).
        os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
        supertonic = _need("supertonic")
        if not (Path.home() / ".cache" / "supertonic3").is_dir():
            out("[speaker] downloading Supertonic 3 (385 MB, once) ...")
        try:
            self.tts = supertonic.TTS()
        except Exception as e:
            raise SpeakerError(f"Supertonic could not be loaded: {type(e).__name__}: {e}") from None
        self.styles = {}

    def speak(self, text, voice, language, speed):
        if voice not in self.voices:
            raise SpeakerError(f'Supertonic has no voice "{voice}" '
                               f'(it has: {", ".join(self.voices)})')
        if voice not in self.styles:
            self.styles[voice] = self.tts.get_voice_style(voice)
        samples, _duration = self.tts.synthesize(text, voice_style=self.styles[voice],
                                                 lang=language, speed=1.05 * speed)
        return np.asarray(samples, dtype=np.float32).ravel(), self.tts.sample_rate


class Piper:
    """Piper (GPL-3.0), voices from rhasspy/piper-voices: 16 or 22 kHz. A voice may name
    one of its speakers after a colon: de_DE-thorsten_emotional-medium:sleepy."""

    languages = ("en", "de")

    def __init__(self, cache=CACHE, out=print):
        self.piper = _need("piper")
        from piper import download_voices
        logging.getLogger("piper.phoneme_ids").setLevel(logging.ERROR)  # German c+cedilla: harmless
        self.download_voices, self.out = download_voices, out
        self.folder = Path(cache) / "piper"
        self.espeak = short_espeak(Path(self.piper.__file__).parent / "espeak-ng-data", "piper",
                                   cache)
        self.loaded = {}

    def voice(self, name):
        if name not in self.loaded:
            path = self.folder / f"{name}.onnx"
            if not path.is_file():
                self.out(f"[speaker] downloading the Piper voice {name} (about 60 MB, once) ...")
                self.folder.mkdir(parents=True, exist_ok=True)
                try:
                    self.download_voices.download_voice(name, self.folder)
                except ValueError as e:
                    raise SpeakerError(f"Piper: {e}") from None
                except urllib.error.HTTPError as e:
                    raise SpeakerError(f'there is no Piper voice "{name}" ({e.code}): see '
                                       "https://huggingface.co/rhasspy/piper-voices") from None
                except OSError as e:
                    raise SpeakerError(f"the Piper voice {name} could not be downloaded ({e}): "
                                       "no internet?") from None
            self.loaded[name] = self.piper.PiperVoice.load(path, espeak_data_dir=self.espeak)
        return self.loaded[name]

    def speak(self, text, voice, language, speed):
        name, _, speaker = voice.partition(":")
        if not name.startswith(language + "_"):
            raise SpeakerError(f'the Piper voice "{name}" does not speak {language}')
        model = self.voice(name)
        speakers = model.config.speaker_id_map or {}
        if speaker and speaker not in speakers:
            raise SpeakerError(f'{name} has no speaker "{speaker}" (it has: {", ".join(speakers)})')
        config = self.piper.SynthesisConfig(speaker_id=speakers.get(speaker),
                                            length_scale=1.0 / speed)
        audio = b"".join(chunk.audio_int16_bytes for chunk in model.synthesize(text, config))
        return np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768, \
            model.config.sample_rate


MAKERS = {"kokoro": Kokoro, "edge": Edge, "supertonic": Supertonic, "piper": Piper}


class Voices:
    """The engines, each loaded once, when it is first needed."""

    def __init__(self, cache=CACHE, out=print, makers=None):
        self.cache, self.out, self.makers, self.engines = cache, out, makers or MAKERS, {}

    def engine(self, name):
        if name not in self.makers:
            raise SpeakerError(f'there is no engine "{name}" (there are: {", ".join(self.makers)})')
        if name not in self.engines:
            self.engines[name] = self.makers[name](self.cache, self.out)
        return self.engines[name]

    def speak(self, text, engine=ENGINE, voice="", language=LANGUAGE, speed=1.0):
        """(samples, rate) of the sentence."""
        voice = voice or VOICES.get((engine, language), "")
        made = self.engine(engine)
        if language not in made.languages:
            raise SpeakerError(f"{engine} speaks {' and '.join(made.languages)}, not {language}")
        samples, rate = made.speak(text, voice, language, max(0.5, min(2.0, float(speed))))
        return np.asarray(samples, dtype=np.float32).ravel(), int(rate)


def levels(samples, rate, per_second=PER_SECOND):
    """How loud the sound is, a value per 1/per_second s from 0 to 1: the loudness (RMS)
    of each piece, over that of the sentence's loud pieces (its 95th percentile) - so a
    sentence moves the same whichever engine said it and however loud that one is."""
    step = max(1, round(rate / per_second))
    whole = len(samples) // step * step
    if not whole:
        return []
    rms = np.sqrt(np.mean(np.asarray(samples[:whole], dtype=np.float32).reshape(-1, step) ** 2,
                          axis=1))
    top = float(np.percentile(rms, 95))
    if top <= 1e-6:
        return [0.0] * len(rms)
    return [round(float(v), 3) for v in np.minimum(1.0, rms / top)]


# --- where the sound goes ---------------------------------------------------------------

def outputs():
    """The names of the devices sound can be played on."""
    sounddevice = _need("sounddevice")
    return [d["name"] for d in sounddevice.query_devices() if d["max_output_channels"] > 0]


def find_output(wanted, names):
    """The device whose name contains `wanted` (ignoring case), as (index in names, name);
    (None, "") for the computer's default."""
    wanted = (wanted or "").strip().lower()
    if not wanted:
        return None, ""
    for i, name in enumerate(names):
        if wanted in name.lower():
            return i, name
    return None, ""


def resample(samples, rate, to):
    if rate == to or not len(samples):
        return samples
    there = np.arange(0, len(samples), rate / to)
    return np.interp(there, np.arange(len(samples)), samples).astype(np.float32)


class Player:
    """Plays one sound at a time; a new one ends the one before."""

    def __init__(self):
        self.sounddevice = _need("sounddevice")
        self.until = 0.0  # when the sound playing now ends (time.monotonic())

    def device(self, wanted):
        """(the device to play on, as sounddevice wants it, its name or a note)."""
        devices = self.sounddevice.query_devices()
        names = [d["name"] if d["max_output_channels"] > 0 else "" for d in devices]
        index, name = find_output(wanted, names)
        if index is not None:
            return index, name
        if (wanted or "").strip():
            return None, f'no output named like "{wanted}": the default output'
        return None, "the default output"

    def play(self, samples, rate, wanted=""):
        """Start playing; returns the name of where it plays. Does not wait."""
        device, where = self.device(wanted)
        self.stop()
        try:
            self.sounddevice.play(samples, rate, device=device)
        except self.sounddevice.PortAudioError:  # a device that takes only its own rate
            info = self.sounddevice.query_devices(device, "output")
            own = int(info["default_samplerate"])
            self.sounddevice.play(resample(samples, rate, own), own, device=device)
        self.until = time.monotonic() + len(samples) / rate
        return where

    def stop(self):
        self.sounddevice.stop()
        self.until = 0.0

    @property
    def playing(self):
        return time.monotonic() < self.until

    def wait(self):
        self.sounddevice.wait()


# --- talking to a speaker component ----------------------------------------------------

class Teller:
    """Tells a speaker component (--post) what happens, and the terminal."""

    def __init__(self, address=None, out=print):
        self.address, self.out, self.deaf = (address or "").rstrip("/"), out, False
        self.turn = threading.Lock()  # one word at a time: they arrive in their order

    def tell(self, state, text="", **more):
        if not self.address:
            return
        body = dict(more, state=state, text=text, by="speaker")
        req = urllib.request.Request(self.address + "/state", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with self.turn:
            try:
                urllib.request.urlopen(req, timeout=1.0).close()
                self.deaf = False
            except OSError as e:
                if not self.deaf:  # said once, not with every sentence
                    self.out(f"[speaker] nobody takes it at {self.address}: {e}")
                self.deaf = True


def _again(tell, over):
    """Once a second, also while a model loads: a speaker component counts a program it
    has not heard from for three seconds as gone."""
    while not over.wait(AGAIN):
        tell.tell("alive")


def _read_commands(commands):
    """--managed: the commands on stdin, one JSON object a line; "stop" or the end of
    stdin ends the program."""
    try:
        for line in sys.stdin:
            line = line.strip()
            if line == "stop":
                break
            if line:
                try:
                    commands.put(json.loads(line))
                except ValueError:
                    commands.put({"bad": line})
    except (OSError, ValueError):
        pass
    commands.put(None)


def _latest(commands, first):
    """The command to do now: a sentence that a newer one (or a hush) has overtaken while
    it waited is not said. The others keep their order."""
    pending = [first]
    while True:
        try:
            pending.append(commands.get_nowait())
        except queue.Empty:
            break
    kept = []
    for c in pending:
        if c is not None and ("say" in c or c.get("hush")):
            kept = [k for k in kept if k is None or "say" not in k]
        kept.append(c)
    for c in kept[1:]:
        commands.put(c)
    return kept[0]


def serve(voices, player, tell, commands, out=print):
    """Say what arrives until told to stop. Every command may name engine, voice,
    language, speed and device; "say" is the sentence, "prepare" loads an engine (and
    downloads it the first time) so that its first sentence comes quickly, "hush" stops
    the sound."""
    speaking = None  # (id, text) while a sound plays
    while True:
        try:
            command = commands.get(timeout=0.1)
        except queue.Empty:
            if speaking and not player.playing:
                tell.tell("ready", "", id=speaking[0])
                speaking = None
            continue
        command = _latest(commands, command)
        if command is None:
            return
        if "bad" in command:
            out(f"[speaker] not a command: {command['bad']}")
            continue
        engine = command.get("engine") or ENGINE
        language = command.get("language") or LANGUAGE
        voice = command.get("voice") or VOICES.get((engine, language), "")
        try:
            if command.get("hush"):
                player.stop()
                tell.tell("ready", "hushed")
                speaking = None
            elif command.get("prepare"):
                if engine not in voices.engines:
                    tell.tell("loading", f"loading {engine} (the first time it is downloaded)")
                # A first sentence, not played: an engine's first takes a second longer.
                voices.speak("Hello.", engine, voice, language)
                tell.tell("ready", f"{engine} {voice} is ready")
            elif "say" in command:
                text, ident = str(command["say"]).strip(), command.get("id", 0)
                if not text:
                    continue
                if engine not in voices.engines:
                    tell.tell("loading", f"loading {engine} (the first time it is downloaded)")
                tell.tell("rendering", text, id=ident)
                began = time.perf_counter()
                samples, rate = voices.speak(text, engine, voice, language,
                                             command.get("speed", 1.0))
                took = time.perf_counter() - began
                where = player.play(samples, rate, command.get("device", ""))
                seconds = len(samples) / rate
                tell.tell("speaking", text, id=ident, seconds=round(seconds, 3),
                          levels=levels(samples, rate), rate=PER_SECOND, took=round(took, 3),
                          engine=engine, voice=voice, output=where)
                out(f"[speaker] {engine} {voice}: {seconds:.1f} s of sound after {took:.2f} s, "
                    f"on {where}: {text}")
                speaking = (ident, text)
        except SpeakerError as e:
            out(f"[speaker] {e}")
            tell.tell("error", str(e), id=command.get("id", 0))
        except Exception as e:  # an engine failing in its own way: said, not fatal
            out(f"[speaker] {engine} failed: {type(e).__name__}: {e}")
            tell.tell("error", f"{engine} failed: {type(e).__name__}: {e}",
                      id=command.get("id", 0))


def managed(args):
    tell, over, commands = Teller(args.post), threading.Event(), queue.Queue()
    threading.Thread(target=_again, args=(tell, over), daemon=True).start()
    threading.Thread(target=_read_commands, args=(commands,), daemon=True).start()
    try:
        player = Player()
        tell.tell("ready", "ready to speak")
        print("[speaker] ready: waiting for sentences on stdin", flush=True)
        serve(Voices(), player, tell, commands)
    except SpeakerError as e:
        tell.tell("error", str(e))
        raise SystemExit(str(e)) from None
    finally:
        over.set()
        tell.tell("stopped")
        print("[speaker] stopped", flush=True)


def say_once(args):
    voices, player = Voices(), Player()
    began = time.perf_counter()
    samples, rate = voices.speak(args.text, args.engine, args.voice or "", args.language,
                                 args.speed)
    took = time.perf_counter() - began
    print(f"[speaker] {args.engine}: {len(samples) / rate:.1f} s of sound after {took:.2f} s",
          flush=True)
    if args.save:
        _need("soundfile").write(args.save, samples, rate, subtype="PCM_16")
        print(f"[speaker] saved {args.save}")
        return
    print(f"[speaker] playing on {player.play(samples, rate, args.device or '')}", flush=True)
    player.wait()


def show_list():
    print("engines and their voices (the first is where each starts):")
    for engine in ENGINES:
        for language in ("en", "de"):
            if (engine, language) in VOICES:
                print(f"  {engine:<11} {language}  {VOICES[engine, language]}")
    print("  kokoro: af_* and am_* (US), bf_* and bm_* (British), e.g. af_heart, am_michael, "
          "bf_emma, bm_george")
    print("  edge: python -m edge_tts --list-voices    supertonic: M1-M5, F1-F5")
    print("  piper: https://huggingface.co/rhasspy/piper-voices (en_US-..., de_DE-...)")
    try:
        print("outputs: " + ", ".join(outputs()))
    except SpeakerError as e:
        print(f"outputs: {e}")


TRY = {"en": "Hello! I am ready to speak.", "de": "Hallo! Ich kann jetzt sprechen."}


def prepare(engine=ENGINE, voice="", language=LANGUAGE, device="", out=print):
    """Before the first use (setup-speak): fetch the engine's model - Kokoro unless told
    otherwise - say which outputs there are, and say a sentence on one of them."""
    voices, player = Voices(out=out), Player()
    out(f"[speaker] getting {engine} ready (the first time its model is downloaded) ...")
    began = time.perf_counter()
    sentence = TRY.get(language, TRY["en"])
    samples, rate = voices.speak(sentence, engine, voice or "", language)
    out(f"[speaker] {engine} is ready ({time.perf_counter() - began:.1f} s).")
    out("[speaker] outputs: " + ", ".join(outputs()))
    out(f'[speaker] saying "{sentence}" on {player.play(samples, rate, device)}')
    player.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("text", nargs="?", help="the sentence to say")
    parser.add_argument("--engine", default=ENGINE, choices=ENGINES,
                        help=f"who makes the voice (default: {ENGINE})")
    parser.add_argument("--voice", help="the engine's voice (default: see --list)")
    parser.add_argument("--language", default=LANGUAGE, help="en or de (default: en)")
    parser.add_argument("--speed", type=float, default=1.0, help="0.5 to 2 (default: 1)")
    parser.add_argument("--device", help='where to play it, part of a name: "Reachy Mini Audio"')
    parser.add_argument("--save", metavar="WAV", help="write the sound to this file instead")
    parser.add_argument("--list", action="store_true", help="list engines, voices and outputs")
    parser.add_argument("--prepare", action="store_true",
                        help="fetch the engine's model (Kokoro unless --engine), say a "
                             "sentence, then stop")
    parser.add_argument("--post", metavar="ADDRESS",
                        help="a speaker component's address, e.g. http://127.0.0.1:9984")
    parser.add_argument("--managed", action="store_true",
                        help="for a parent program: sentences on stdin, stop when it closes")
    args = parser.parse_args(argv)
    try:
        if args.list:
            show_list()
        elif args.prepare:
            prepare(args.engine, args.voice or "", args.language, args.device or "")
        elif args.managed:
            managed(args)
        elif args.text:
            say_once(args)
        else:
            parser.print_help()
    except SpeakerError as e:
        raise SystemExit(f"[speaker] {e}") from None
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
