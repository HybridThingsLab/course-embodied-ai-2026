# The robot's channels

What the Reachy Mini can be told, and how far and how fast it goes: the names of its
channels, the safe range of each, and the speed limits. `reachy_hub` takes CHOP
channels with these names (without the leading `/`); an OSC Out CHOP sends them as
these addresses ([touchdesigner.md](touchdesigner.md#3-send-osc-from-touchdesigner)).

## OSC address map

Angles in **degrees**, head translation in **metres**, antennas in **radians**.
Directions are the robot's own: "its left" is your right when you face it. The
bridge clamps every value to the safe range, so out-of-range values are safe to
send.

| Address | Safe range | Meaning |
| ------- | ---------- | ------- |
| `/reachy/head/roll` | ±30° | tilt sideways; + to its right (further, the head hits the body) |
| `/reachy/head/pitch` | ±27° | nod; + looks down (further, the head hits the body) |
| `/reachy/head/yaw` | ±175° | turn; + to its left |
| `/reachy/head/x` | −0.015 … +0.022 m | forward (+) / back (backward, the head hits the body at 0.02) |
| `/reachy/head/y` | ±0.040 m | to its left (+) / right |
| `/reachy/head/z` | −0.035 … +0.022 m | up (+) / down |
| `/reachy/antenna/left` | ±3.1 rad | left antenna: 0 = upright, just short of half a turn either way |
| `/reachy/antenna/right` | ±3.1 rad | right antenna |
| `/reachy/body_yaw` | ±160° | base turntable; + to its left |

**Roll and pitch together** have a smaller range than each alone: tilting and nodding
at the same time brings the head into the body sooner. The bridge keeps the pair inside
an ellipse — the full ±30° / ±27° when only one of them moves, about 70 % of each at
the diagonal (30° and 27° together become about 21° and 19°).

**The head's position (x, y, z) is in metres, and its range is small**: the head sits
on six short arms and moves a few centimetres at most. **Tilt and position share the
room**: the more the head tilts, the less it can shift, and shifts in two directions at
once each get less. A level head gets the full ranges above; a head tilted halfway to
its limit gets half of them; at the tilt limit it cannot shift at all. The tilt has
priority: when both don't fit, the position gives way.

#### What a hand has shown

That last rule is a careful guess, and it gives way to what the robot itself has
shown. In [teach mode](2-animate.md#teach-mode-pose-it-by-hand-record-replay) the bridge remembers
where a hand puts the head: for each tilt, how far it was shifted in each direction.
From then on a target may be shifted as far at that tilt - so a movement taught by hand
plays back as it was shown, also where the head was tilted and pushed aside or down at
once. It holds for the poses that were shown and their close surroundings (a few
degrees, a few millimetres); between two poses a hand never connected, the rule is
back.

Everything else stays as it is, whatever a hand has shown: each address's own range in
the table above (a head pushed lower than −0.035 m plays back at −0.035), roll and pitch
inside their ellipse, the turn limit, the speed limits.

The bridge keeps this in the file `taught_room.json` in the project folder, so it is
still there the next day. It belongs to the robot it was taught on. **Forget Taught
Poses** on the hub's Hub page (or the message `/reachy/taught/forget`) empties it - do
that after a head was pressed against the body by hand, because such a pose counts like
any other and would be played back with the motors pressing. Starting the bridge with
`--no-taught-room` switches all of this off.

### Speed limits

However fast a value changes, the robot follows no faster than this:

| Channels | At most |
| -------- | ------- |
| head roll, pitch, yaw | 300° per second |
| head x, y, z | 0.35 m per second |
| antennas | 12 rad per second |
| base (`body_yaw`) | 183° per second, speeding up and braking at 229° per second² |

These are caps for safety, not a style: ordinary gestures stay well below them and
pass through untouched. A jump of 90° takes about a third of a second (0.3 s). For motion
that *looks* right, smooth it in TouchDesigner (a Lag CHOP of 0.2–0.5 s on what you
type or switch).

The same addresses come back on port 7001, so a recording plays straight back.

**Grouped** (one message, several values — handy from a Script or Text DAT):

| Address | Values |
| ------- | ------ |
| `/reachy/head/rpy` | `roll pitch yaw` |
| `/reachy/head/pose` | `x y z roll pitch yaw` |
| `/reachy/antennas` | `left right` |

**Commands:**

| Address | Value | Effect |
| ------- | ----- | ------ |
| `/reachy/neutral` | (any) | back to looking straight ahead — once: anything still streaming values overrides it on the next frame |
| `/reachy/enable` | `0` / `1` | motors off / on (real robot only) |
| `/reachy/teach` | `0` / `1` | teach mode off / on ([teach mode](2-animate.md#teach-mode-pose-it-by-hand-record-replay)) |
| `/reachy/taught/forget` | (any) | forget [what a hand has shown](#what-a-hand-has-shown) |

Head yaw stops at ±175°, not 180°: at ±180° the robot's software flips the direction
it thinks the head faces, and the base would whip around to follow.
