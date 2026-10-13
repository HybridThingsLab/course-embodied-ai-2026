# Using TouchDesigner with Reachy Mini

[TouchDesigner](https://derivative.ca/) (TD) is a visual, node-based tool for
building real-time interactive graphics and signals. Here it **generates motion**
that drives Reachy Mini's head, antennas and base, live, and it can **read the
robot's pose** back, for example to record motion you pose by hand.

Set up the project first ([getting-started.md](getting-started.md)) — TouchDesigner
talks to the robot *through* it. To try a motion before that, or without a robot, there
is [`reachy_twin`](1-puppet.md#without-a-robot-the-reachy_twin-component): the robot as a picture
inside TouchDesigner.

## How TouchDesigner reaches the robot

TouchDesigner can't load the robot's Python software (it ships its own Python), so a
small **bridge** relays messages between the two over **OSC**, a standard way for
creative tools to send named values:

```
  TouchDesigner ──OSC :7000──▶ bridge ──▶ daemon ──▶ robot (simulated or real)
  TouchDesigner ◀──OSC :7001── bridge ◀── the robot's live pose
```

Nothing needs installing on the TouchDesigner side.

## 1. Install TouchDesigner

Download the **free non-commercial** edition from
[derivative.ca/download](https://derivative.ca/download) (macOS and Windows). It's a
large download and needs a reasonably capable graphics card — camera tracking
(MediaPipe, in [Sense](3-sense.md#camera-tracking-with-mediapipe)) is the most demanding part.

## 2. Start the robot + the bridge

A TouchDesigner session needs the **daemon** (simulated or real) and the **bridge**
running. One command starts both, in a terminal with the environment activated:

```bash
python -m td_reachy.station             # simulator, with its 3D window
python -m td_reachy.station --headless  # simulator, no window
python -m td_reachy.station --robot     # a real robot, switched on
```

It picks the right way to start the daemon on your system (including `mjpython` on
macOS), waits until it runs, then starts the bridge. Wait for:

```
[station] ready: TouchDesigner: OSC Out CHOP → 127.0.0.1:7000, OSC In CHOP ← port 7001
```

Leave it running while you work. **Ctrl+C** stops everything: the bridge first (it
brings the robot back to neutral), then the daemon (it lowers the robot to sleep). A
daemon that was already running when the station started (for example from Pollen's
desktop app) is used as it is and left running; the bridge then lowers the robot to
sleep itself.
With `--robot`, if the robot isn't switched on yet, the station waits and re-scans
every few seconds — switch it on and it continues.

**Or from inside TouchDesigner:** the [`reachy_hub`](1-puppet.md#the-reachy_hub-component)
component has a
**Station** page with the same choices and Start / Stop buttons.

**Or by hand, in two terminals:** start the daemon (see [simulation.md](simulation.md)
or [working-with-the-robot.md](working-with-the-robot.md)), then the bridge with
`python -m td_reachy.bridge`.

## 3. Send OSC from TouchDesigner

In TouchDesigner, add an **OSC Out CHOP** (right-click the network → *Add Operator*
→ CHOP → *OSC Out*) and set:

| Parameter        | Value                                   |
| ---------------- | --------------------------------------- |
| Protocol         | Messaging (UDP)                         |
| Network Address  | `127.0.0.1` (same computer as the bridge) |
| Network Port     | `7000`                                  |
| Numeric Format   | Float (32 bit)                          |

The OSC Out CHOP sends **one message per input channel**, named `/` + the channel
name. So name the channels you feed into it after the robot's controls — a channel
called `reachy/head/yaw` becomes the message `/reachy/head/yaw`.

**Quick test:** wire a **Constant CHOP** with a channel `reachy/head/pitch` into the
OSC Out CHOP, then drag its value. The robot's head should nod. A ready-made version
with sliders is [`touchdesigner/basic_control.toe`](../touchdesigner/basic_control.toe).

Shape the motion in TouchDesigner (Lag, Filter, LFO, Noise CHOPs): the bridge sends
the latest value of every channel to the robot, 100 times a second. It changes two
things on the way, both for the robot's safety: it keeps every value inside its
[range](robot-channels.md#osc-address-map), and it follows a change no faster than the
[speed limits](robot-channels.md#speed-limits) — a typed-in jump becomes a quick move, not a snap.

## 4. Read the robot's pose

With `reachy_hub`, its output already is the pose. Without it, add an **OSC In
CHOP** with **Network Port `7001`**. Either way you get one channel per address of
the [address map](robot-channels.md#osc-address-map), with the robot's *measured* pose — where it actually is, not where it was
told to go. Wire it into a **Trail CHOP** to see both side by side.

## The modules, one guide each

| | Module | Guide | What is in it |
| - | ------ | ----- | ------------- |
| 1 | Puppet | [1-puppet.md](1-puppet.md) | `puppet_start.toe`, `reachy_hub`, `reachy_twin` |
| 2 | Animate | [2-animate.md](2-animate.md) | `animate_start.toe`, `clip_player`, `recorder`, teach mode |
| 3 | Sense | [3-sense.md](3-sense.md) | MediaPipe, `face_signal`, `hand_signal`, `voice_signal`, `speech_signal` |
| 4 | Think | [4-think.md](4-think.md) | `think_start.toe`, `brain_signal` |

For reference: [robot-channels.md](robot-channels.md) has every channel the robot
takes, with its safe range and the speed limits.

## OSC address map

The addresses, their ranges and the speed limits are in
[robot-channels.md](robot-channels.md#osc-address-map).

## Troubleshooting

- **Nothing moves, no errors.** Check the terminal printed `[station] ready`, and
  that TD's OSC Out CHOP shows Address `127.0.0.1` and Port `7000`. Channel names
  have no leading `/`.
- **The OSC In CHOP stays empty.** Its port must be `7001`. If TouchDesigner runs on
  another computer, see the last point.
- **`No module named td_reachy` or `missing Python packages`.** The environment isn't
  activated in that terminal — see getting-started, step 3.
- **`voice_signal` says `no sound from the microphone`.** Choose the microphone on its
  Voice page, and check that TouchDesigner may use it. macOS: System Settings → Privacy
  & Security → Microphone. Windows: Settings → Privacy & security → Microphone → *Let
  desktop apps access your microphone*.
- **`brain_signal` says `keyword match: …`.** No model answered, and the rest of the
  line says why. For Tev1 and Nimble: start Ollama, and get the model once (run
  `setup-think`, or `ollama pull tev1`). For Jev: the key file is missing or was not
  accepted.
- **`speech_signal` says `Whisper stopped: No module named …`.** Its packages are not
  installed: run `setup-speech` in the project folder (or
  `uv pip install -e ".[speech]"` there).
- **`speech_signal` says `no microphone …`, or hears nothing.** TouchDesigner may not
  use the microphone: the same system setting as for `voice_signal` above. Or start
  the listener by hand ([speech_signal](3-sense.md#what-was-said-the-speech_signal-component)).
- **`UDP port 7000 is taken`.** A previous bridge is still running. macOS:
  `lsof -ti udp:7000 | xargs kill`. Windows: `netstat -ano | findstr 7000` then
  `taskkill /PID <pid> /F`.
- **`port 8000 is taken but no daemon answers there`.** An old daemon hung, or
  another program uses the port. macOS: `lsof -ti tcp:8000 | xargs kill`. Windows:
  `netstat -ano | findstr 8000` then `taskkill /PID <pid> /F`.
- **`a simulator daemon is already running …, but the robot was requested`** (or
  the other way round). Stop the running daemon first, or start the station in its
  mode.
- **TouchDesigner is on a different computer than the robot.** Set the OSC Out CHOP's
  Network Address to the *robot computer's* IP address (the bridge listens on all
  interfaces), and start the station with `--out-ip <TouchDesigner computer's IP>`
  so the pose comes back to the right place. UDP ports 7000 and 7001 must be open.
