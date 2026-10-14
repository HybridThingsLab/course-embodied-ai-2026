# Animate

Module 2: movements over time. Play clips such as yes, no and maybe, and make your own.

Before: [Puppet](1-puppet.md). Next: [Sense](3-sense.md).

## Clips: animate_start.toe

A **clip** is a movement over time: one channel per robot control, many samples. Open
[`touchdesigner/animate_start.toe`](../touchdesigner/animate_start.toe) and start
`reachy_hub` as in Puppet. Then click `library`, choose a **Clip** on its Clip page and
press **Play**.

| Operator | What it does |
| --- | --- |
| `library` (a `clip_player`) | plays a clip from [`touchdesigner/clips`](../touchdesigner/clips/README.md): yes, no, maybe, and recorded emotions |
| `recorder` | makes a clip from the pose the robot reports |
| `take` (a second `clip_player`) | plays what `recorder` holds |
| `clips` (Math: Combine CHOPs *Add*) | what both players give, added up |
| `pose` (Constant) | a pose typed in, for the simulator |
| `drive` (Switch) | what the robot follows: Index 0 = `pose`, 1 = `clips` |
| `teach` (Constant) | 1 = the real robot's motors go soft, to pose it by hand |
| `to_robot` (Merge) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back, into `recorder` |

**Make a clip of your own, pose by pose:**

- **On the robot:** set `teach` to 1: the motors go soft. Move the head and antennas by
  hand, gently, holding the head shell, and press **Add Key** on `recorder`. Next pose,
  Add Key again. Set `teach` back to 0 when you are done.
- **In the simulator:** set the Index of `drive` to 0, type a pose into `pose` and press
  **Add Key**. Next pose, Add Key again. Set the Index back to 1 when you are done.

Then press **Play** on `take`. To keep the clip, give it a **Name** on `recorder` and
press **Save**. The `readme` in the project has the steps.

While you teach, hold the head up a little: with the motors soft it sinks, and the clip
plays back no lower than the robot's range.

## Playing a clip: the clip_player component

[`clip_player.tox`](../touchdesigner/components/clip_player.tox) plays a clip from its
start to its end.

- **Clip** lists the files in [`touchdesigner/clips`](../touchdesigner/clips/README.md).
  If your `.toe` is saved outside the project folder, set **Clips Folder**.
- **Play**, **Stop**, **Loop**, **Speed** (2 = twice as fast), and **Fade**: the
  seconds over which a clip fades in and out, so it never jumps.
- **Input 1** (optional): a clip as a CHOP, such as `recorder`'s output. It plays
  instead of the file.
- **Input 2** (optional): a trigger. The clip plays when it goes from 0 to 1: a button,
  a gesture, a sound.
- **Output 1:** the clip's channels, 0 while nothing plays. Wire it into `sum` and the
  clip plays on top of the idle.
- **Output 2:** `running`, `done` and `timer_fraction` (0 to 1 while it plays), for
  example to start something when a clip ends.

For several clips, use one player per clip. It works with any channels, not only the
robot's.

## Making a clip: the recorder component

[`recorder.tox`](../touchdesigner/components/recorder.tox) makes a clip from what
arrives on its input: the robot's pose, a slider, a face. Its output is the clip so
far: wire it into a `clip_player` to play it.

- **Add Key** adds the input as it is now as the next pose. **Remove Last Key** and
  **Clear** undo. **Seconds per Key** is the time from one pose to the next.
- **Record** on, move, **Record** off: a take, one pose per frame. It replaces the keys.
- **Easing** (*Smooth* or *Linear*) is how it moves between keys. **Stretch** makes the
  clip longer (2) or shorter (0.5).
- **Save** writes the clip as **Name** into the clips folder. It is then in the Clip
  menu of every `clip_player`.
