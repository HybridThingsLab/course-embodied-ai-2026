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
| `circle` | 2.9 | gesture `circle(revolutions=1, amplitude=15)` | The head rolls around once. |
| `cheerful1` | 2.8 | Pollen Robotics | It is like whistling. Use it when someone makes you a proposal that makes you happy. |
| `surprised1` | 2.5 | Pollen Robotics | A reaction of surprise or amazement to something unexpected. |
| `amazed1` | 3.4 | Pollen Robotics | When you discover something extraordinary. It could be a new robot, or someone tells you you've been programmed with new abilities. It can also be when you admire what someone has done. |
| `laughing2` | 2.9 | Pollen Robotics | A lighter version of the laugh in laughing1. |
| `yes1` | 3.4 | Pollen Robotics | A long affirmative response. You nod to confirm what your interlocutor said. |
| `no1` | 2.7 | Pollen Robotics | A firm, categorical no. Like that’s final. |
| `loving1` | 5.6 | Pollen Robotics | A gesture used when someone compliments you, or you want to show you really like what’s being offered. Also usable when someone says goodbye or it was nice talking to you. |
| `success1` | 2.3 | Pollen Robotics | Use this gesture when you’ve successfully completed a task. |
| `curious1` | 11.8 | Pollen Robotics | You look around. Use this when you’re in a conversation with several people and want to glance at everyone. |
| `sad1` | 9.0 | Pollen Robotics | You’re very sad and start whining. |
| `boredom1` | 15.7 | Pollen Robotics | You’re about to fall asleep because the conversation is boring. Use it when no one talks to you for 2 minutes. You can follow with boredom2 if there is still no interaction. |
| `tired1` | 7.4 | Pollen Robotics | You yawn because you’re tired. Could be between tasks, especially after working hard. |

## Where they come from

- **Gestures**: the gesture vocabulary of this repository (`src/td_reachy/gestures.py`).
- **Pollen Robotics**: recorded emotions from the
  [Reachy Mini emotions library](https://huggingface.co/datasets/pollen-robotics/reachy-mini-emotions-library)
  (commit `873ae49f0b89`), © Pollen Robotics, licensed under the Apache License 2.0
  ([LICENSE-Apache-2.0.txt](LICENSE-Apache-2.0.txt)). Changed for this repository: the
  movement only, without the sound; resampled from about 50 to 60 poses per second; the
  head's pose written as position (metres) and roll, pitch, yaw (degrees), the base in
  degrees. The descriptions in the table are Pollen's.
