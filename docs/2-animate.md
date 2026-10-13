# Animate

Module 2 of [Sense · Think · Move](../README.md#the-modules): movements over time. Play
clips such as yes, no and maybe, and make your own: pose by pose, as a take, or by
posing the real robot by hand.

- [`animate_start.toe`](#clips-animate_starttoe): the project to open
- [`clip_player`](#playing-a-clip-the-clip_player-component): plays a clip
- [`recorder`](#making-a-clip-the-recorder-component): makes a clip
- [Teach mode](#teach-mode-pose-it-by-hand-record-replay): what happens underneath when
  the robot is posed by hand

Before: [Puppet](1-puppet.md). Next: [Sense](3-sense.md).

## Clips: animate_start.toe

A **clip** is a movement over time: one channel per control, named like the robot
channel it moves, and many samples. [`touchdesigner/animate_start.toe`](../touchdesigner/animate_start.toe)
plays clips and makes new ones. Open it, click `reachy_hub`, press **Start** on its
Station page and wait for `ready`. Then click `library`, choose a **Clip** on its Clip
page and press **Play**.

| Operator | What it does |
| --- | --- |
| `library` (a `clip_player`) | plays a clip from [`touchdesigner/clips`](../touchdesigner/clips/README.md): yes, no, maybe, and recorded emotions |
| `recorder` | makes a clip from the pose the robot reports: pose by pose, or as a take |
| `take` (a second `clip_player`) | plays what `recorder` holds |
| `library_out`, `take_out` (Null) → `clips` (Math: Combine CHOPs *Add*, Match by *Channel Name*) | what each player gives, added to `base`, the nine robot channels at 0 |
| `pose` (Constant) → `pose_lag` (Lag) | for the simulator, where there is no head to take hold of: a pose typed in |
| `drive` (Switch) | what the robot follows: Index 0 = `pose`, 1 = `clips` |
| `teach` (Constant, channel `reachy/teach`) | 1 = the real robot's motors go soft, to pose it by hand |
| `to_robot` (Merge) → `reachy_hub` → `robot_pose` (Null) | out to the robot, and its measured pose back, into `recorder` |

To make a clip of your own, pose by pose:

- **On the robot:** set `teach` to 1, move the head and antennas by hand — firmly but
  gently, from the head shell — and press **Add Key** on `recorder`. Next pose, Add Key
  again. Set `teach` back to 0 when you are done: the robot holds where it is, then
  follows `clips` again.
- **In the simulator:** set the Index of `drive` to 0, type a pose into `pose`, press
  **Add Key**. Next pose, Add Key again. Set the Index back to 1 when you are done.

Then press **Play** on `take`. The two components are described below; the `readme`
in the project has the steps.

The recorder gets the head's pose as it was, and a movement taught by hand on the
robot plays back as it was shown ([what a hand has shown](robot-channels.md#what-a-hand-has-shown)) -
inside each address's own range: with the motors soft the head hangs low, and what was
below −0.035 m comes back at −0.035. Hold the head up while you teach, and nothing is
lost. In the simulator, and for a pose that was only typed in, the more careful rule
applies: the more the head tilts, the less it shifts.

## Playing a clip: the clip_player component

[`touchdesigner/clip_player.tox`](../touchdesigner/clip_player.tox) plays a clip from
its first sample to its last. Drag it into your network.

- **Clip** lists the clip files in the clips folder. In this project that is
  [`touchdesigner/clips`](../touchdesigner/clips/README.md), found by itself when your
  `.toe` is saved inside the project folder; otherwise set **Clips Folder**. A clip
  file is a table of numbers (`.csv`): the first row names the channels, every further
  row is 1/60 s. Save such a file into the clips folder and it is in the menu.
  **Reload** looks at the
  folder and reads the chosen file again; **Status** says what would play.
- **Input 1 (optional): a clip as a CHOP** with many samples — the output of the
  `recorder` below, the take of a Record CHOP, an Animation COMP whose channels are
  named like the addresses. Wired in, it plays instead of the file.
- **Input 2: a trigger** (optional). The clip plays when the trigger's first channel
  goes from 0 to 1: a Button COMP, a key, a sensor crossing a threshold.
- **Output 1: the motion** — the clip's channels at the playhead, and 0 while nothing
  plays. That makes it a layer like the ones in `puppet_start.toe`: wire it into `sum`
  and the clip plays on top of the idle.
- **Output 2: the state** — `timer_fraction` (0 to 1 while the clip plays), `running`
  and `done`, for example to start something else when a clip ends.
- **Play** (while a clip plays: start over) and **Stop**; **Loop** (again and again,
  until Stop); **Speed** (1 = as recorded, 2 = twice as fast); **Fade**, in seconds.
- **Scrub** holds the clip at **Position** (0 = its start, 1 = its end) instead of
  playing it: to look at one pose on the robot, or to step through a movement by
  dragging Position.
- **Clip Length**, read-only: the clip's samples divided by its sample rate.

When a clip ends, or on Stop, the player keeps the last pose and fades it to 0 over
**Fade** seconds; at the start it fades in. A clip that does not begin or end at 0
therefore never jumps.

Clips play as they were recorded. `reachy_hub` and the bridge keep every pose inside the
robot's safe ranges on the way out ([address map](robot-channels.md#osc-address-map)), so a clip that
reaches further is cut off there.

For several clips, use one player per clip, each with its own trigger, all wired into
`sum`. The player works with any channels, not only the robot's: what comes out is
named like what went in.

Inside, it is a short chain: a **Timer CHOP** runs from 0 to 1 over
the clip's length, and a **Lookup CHOP** reads the clip at that point.

## Making a clip: the recorder component

[`touchdesigner/recorder.tox`](../touchdesigner/recorder.tox) makes a clip from what
arrives on its input: the pose a robot reports (`reachy_hub`'s output), but just as
well a slider or a face. Its output is the clip so far — wire it into a `clip_player`
to play, loop or scrub it.

- **Pose by pose.** Bring the input to a pose and press **Add Key**: the values as
  they are now become the next pose of the clip, **Seconds per Key** after the last
  one. **Remove Last Key** takes one back, **Clear** starts again.
- **A take.** Switch **Record** on, move, switch it off: a pose for every frame. A
  take replaces the keys, and ends by itself after a minute.
- **Easing** is how the clip moves from one key to the next: *Smooth* starts and ends
  gently, *Linear* moves at an even speed. **Stretch** makes the whole clip longer
  (2) or shorter (0.5).
- **The keys** are in the table `keys` inside the component: one row per pose, its
  time in seconds first, then one value per channel. Change a time or a value there
  and the clip follows.
- **Save** writes the clip as a file named **Name** into the clips folder (**Clips
  Folder**, found like the player's). It is then in the Clip menu of every
  `clip_player`.

The recorder works with any channels: the clip's channels are named like what went in.

## Teach mode: pose it by hand, record, replay

[`animate_start.toe`](#clips-animate_starttoe) has this wired up, with the `recorder`
component in place of the Record CHOP. By hand, it is four steps:

1. **Teach.** Send `/reachy/teach 1` (for example a Constant CHOP channel
   `reachy/teach`, driven by a button, into the OSC Out CHOP). The motors go limp:
   move the head and antennas by hand — firmly but gently, from the head shell.
2. **Record** the OSC In CHOP's channels: a **Record CHOP** (armed while you pose),
   a **Trail CHOP** to watch, or an **Animation COMP** to edit keyframes afterwards.
3. **Stop.** Send `/reachy/teach 0`. The robot stiffens and holds where it is.
4. **Replay.** Play the recording into the OSC Out CHOP. The channel names already
   match, so no mapping is needed.

Teach mode only makes sense on the real robot — there is nothing to grab in the
simulator. Stop playing anything into the OSC Out CHOP before `/reachy/teach 0`,
or the robot jumps to that pose.
