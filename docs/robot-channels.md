# The robot's channels

What the Reachy Mini can be told. `reachy_hub` takes CHOP channels with these names.
Without the hub, an OSC Out CHOP sends them as addresses with a leading `/`
([below](#without-the-hub-osc-by-hand)).

## OSC address map

Angles in **degrees**, head position in **metres**, antennas in **radians**. Directions
are the robot's own: its left is your right when you face it.

| Channel | Range | Meaning |
| ------- | ----- | ------- |
| `reachy/head/roll` | ±30° | tilt sideways; + to its right |
| `reachy/head/pitch` | ±27° | nod; + looks down |
| `reachy/head/yaw` | ±175° | turn; + to its left |
| `reachy/head/x` | −0.015 … +0.022 m | forward (+) / back |
| `reachy/head/y` | ±0.040 m | to its left (+) / right |
| `reachy/head/z` | −0.035 … +0.022 m | up (+) / down |
| `reachy/antenna/left` | ±3.1 rad | left antenna: 0 = upright |
| `reachy/antenna/right` | ±3.1 rad | right antenna |
| `reachy/body_yaw` | ±160° | the base; + to its left |

Every value is kept inside its range, so anything is safe to send. Beyond the ranges,
the head would hit the body. Two more limits:

- **Tilt and position share the room.** Roll and pitch together reach less than each
  alone, and the more the head tilts, the less it can shift.
- **Speed.** The robot follows a change no faster than 300°/s for the head's angles,
  0.35 m/s for its position, 12 rad/s for the antennas and 183°/s for the base. A jump
  becomes a quick move. For a soft one, smooth it in TouchDesigner: a Lag CHOP of 0.2 to
  0.5 s.

**Commands:**

| Channel | Value | Effect |
| ------- | ----- | ------ |
| `reachy/neutral` | (any) | back to looking straight ahead, once |
| `reachy/enable` | 0 / 1 | motors off / on (real robot only) |
| `reachy/teach` | 0 / 1 | teach mode off / on ([teach mode](simulator-and-robot.md#teach-mode)) |

## Without the hub: OSC by hand

Add an **OSC Out CHOP** and set **Network Address** `127.0.0.1`, **Network Port**
`7000`. It sends every channel wired into it as a message: the channel
`reachy/head/pitch` becomes `/reachy/head/pitch`. Quick test: a **Constant CHOP** with
a channel `reachy/head/pitch` into it, then drag its value: the head nods.
[`touchdesigner/basic_control.toe`](../touchdesigner/basic_control.toe) is the same with
sliders.

The robot's measured pose comes back on port `7001`: an **OSC In CHOP** with **Network
Port** `7001` (not in the same project as `reachy_hub`, which listens there itself).

The station has to run for this: start it with `reachy_hub`, or
[in a terminal](getting-started.md#if-start-does-not-work-the-terminal).
