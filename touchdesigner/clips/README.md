# Clips

Movements for the `clip_player` component (see [docs/2-animate.md](../../docs/2-animate.md)):
choose one on its Clip page and press Play. Your own recordings from the `recorder`
component are saved here too.

A clip is a table of numbers: one column per robot channel, named like its OSC address,
and one row per 1/60 s. The values are offsets from the robot's neutral pose, as
recorded: `reachy_hub` keeps every pose inside the robot's safe ranges on the way out,
whatever a clip says.

| Clip | Seconds | From | What it says |
| ---- | ------- | ---- | ------------ |
| `yes` | 1.8 | gesture `nod(times=2, amplitude=15)` | A nod, twice. |
| `no` | 1.5 | gesture `shake(times=2, amplitude=20)` | A shake of the head, twice. |
| `maybe` | 1.8 | gesture `curious(roll=20, hold=0.6)` | The head tilts to one side, the antennas lean, it holds, and comes back. |
| `look_around` | 3.5 | gesture `look_around(duration=0.7)` | A look to the left, to the right, up and down. |
| `cheerful1` | 2.8 | Pollen Robotics | It is like whistling. Use it when someone makes you a proposal that makes you happy. |

## Where they come from

- **Gestures**: the gesture vocabulary of this repository (`src/td_reachy/gestures.py`).
- **Pollen Robotics**: recorded emotions from the
  [Reachy Mini emotions library](https://huggingface.co/datasets/pollen-robotics/reachy-mini-emotions-library)
  (commit `873ae49f0b89`), © Pollen Robotics, licensed under the Apache License 2.0
  ([LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt)). Changed for this repository: the
  movement only, without the sound; resampled from about 50 to 60 poses per second; the
  head's pose written as position (metres) and roll, pitch, yaw (degrees), the base in
  degrees. The descriptions in the table are Pollen's.
