# A Microduck, without a duck

The same behaviour, another body. Pollen's
[Microduck](https://pollen-robotics.com/microduck) is a small duck that walks and does a
forward roll. `duck_hub` turns your channels into what a duck is asked, and `duck_model` is a
3D model of the duck doing it. They need no duck, no simulator and no setup.

Before: [Compose](5-compose.md).

## Try it

1. Open any of the projects in `touchdesigner/`.
2. Drag `duck_hub.tox` and `duck_model.tox` from `touchdesigner/components/` into the
   network.
3. Wire `to_robot` into `duck_hub`, and `duck_hub` into `duck_model`.
4. Move the robot as you always do: the duck moves its head with it, degree for degree.

`duck_hub`'s **Status** says `demo, no duck: Look (Auto)`: this `duck_hub` is a demo, and
sends nothing anywhere.

Under a tenth of the range (about 14°) a duck's head does not move at all, so small turns
do nothing here. A real duck does the same.

## Make it walk

A channel named as one of `duck_hub`'s outputs, such as `duck/walk`, goes straight
through: -1 to 1 is the duck's whole range.

1. Add a Constant CHOP with a channel named `duck/walk`. Add a Merge CHOP, wire `to_robot`
   and the Constant into it, and wire the Merge into `duck_hub`, in place of the wire from
   `to_robot`.
2. Drag `duck/walk` to 0.7: the duck walks, and the camera follows it. Drag it back down to
   0.3: it goes on, slower. **Home** on `duck_model` brings it back.

At 0.5 it stays where it is: a standing duck needs about 0.55
([below](#the-duck_model-component)).

## Another channel onto the duck

Any other channel needs a row that says what it moves. Wire it into the Merge as well, add
a Table DAT with these rows, and wire the table into `duck_hub`'s second input:

| channel | duck | in_min | in_max | out_min | out_max |
| --- | --- | --- | --- | --- | --- |
| `reachy/head/yaw` | head_yaw | -143 | 143 | -1 | 1 |
| `reachy/head/pitch` | head_pitch | -143 | 143 | -1 | 1 |
| `reachy/head/roll` | head_roll | -143 | 143 | 1 | -1 |
| `hand/y` | walk | -1 | 1 | -1 | 1 |

A channel's value from in_min to in_max becomes out_min to out_max, where -1 to 1 is the
duck's whole range. A wired table replaces the one inside `duck_hub`, whose rows are the
first three here: they turn the duck's head as far as the Reachy's, and the roll is turned
round, because the duck's head tilts the other way. A row decides over a `duck/*` channel
for what it moves.

Change first: put your own signal in place of `hand/y`, and narrow out_min and out_max
until it walks as slowly as you want.

## Make it roll

The duck also does things by name, as it did in Pollen's simulator. Each time one of these
channels goes above 0.5 it does that once, however long the channel stays there:

| channel | the duck |
| --- | --- |
| `duck/roll` | does a forward roll |
| `duck/kick_left`, `duck/kick_right` | kicks with that leg |
| `duck/pick` | picks at the ground |
| `duck/sit` | sits down; the next time, stands up |
| `duck/fall` | falls over and lies there; it gets up when the channel goes back under 0.5 |

1. Add a channel `duck/roll` to the Constant, and drag it to 1: the duck rolls.
2. Drag it back to 0 before the next one.

It does one at a time, as a real duck does: what comes while another plays is lost. A seated
duck takes only `duck/sit`, though its head still turns. Walking stops for a gesture.

Nobody can ask a real duck to fall over: it falls when it falls, then gets up the same way.

Change first: a row, so that your own signal plays it. With the table from above and
`hand_signal` wired in: `hand/thumbs_up`, roll, 0, 1, 0, 1.

## The duck_hub component

| duck | moves | + is |
| --- | --- | --- |
| `walk`, `strafe`, `turn` | the duck walking | forward, to the left, to the left |
| `head_yaw`, `head_pitch`, `head_roll` | the head | left, down, tilted left |
| `neck_pitch` | the neck | back and up |
| `height`, `lean` | the body, standing | up (hardly at all), to the right |
| `sit`, `pick`, `roll`, `kick_left`, `kick_right`, `fall` | [a gesture](#make-it-roll), whatever the Mode | above 0.5: do it |

A duck's sticks carry only some of these at a time. **Mode** chooses which, as on its
gamepad, and **Auto** chooses from the channels that come in, whatever their value. **Status**
names what the mode leaves out:

| Mode | moves |
| --- | --- |
| Look | the head, the neck; the duck stands still |
| Walk | walk, strafe, turn |
| Walk and Look | walk, turn, the head's yaw and pitch |
| Body and Look | height, lean, the head's yaw and pitch |

Its output says what the duck would be asked: `duck/walk` ... `duck/lean`, -1 to 1,
`duck/sit` ... `duck/fall`, 0 to 1, and `duck/idle`, 1 in the Mode that leaves the head free
(Walk). Wire it into `duck_model` to see it.

A version that drives a real duck over the WiFi follows once it has driven one. It takes the
same channels and the same table, so it can take this one's place.

## The duck_model component

It moves as Pollen's simulator moved the duck on the walking network a real duck ships with,
recorded from it: as fast, with the same steps. Its head turns as far as it is asked; a real
duck's network may turn it less. Height and lean are the simulator's; the beak does not move
(Pollen's model has no joint for it).

A standing duck takes more asking than a walking one, and the model does the same:

| | to start from standing | to keep going |
| --- | --- | --- |
| `walk` forward | 0.55 | 0.25 |
| `walk` back | 0.85 | 0.5 |
| `strafe` right | 1 | 0.5 |
| `strafe` left | not alone | 0.4 |
| `turn` left | 0.6 | 0.2 |
| `turn` right | 0.5 | 0.2 |

Asked together they help each other: `walk` 0.45 with `turn` -0.3 starts. Under 0.1 nothing
moves at all. **Status** says when it was asked too little to start. In Pollen's simulator the
duck is less exact near these numbers: right at a threshold it may start, or not.

| On its Model page | |
| --- | --- |
| **Walk Over the Floor** | off: it walks on the spot |
| **Look Around** | off: left alone, it looks straight on |
| **Home** | back to where it began, standing, facing the camera |
| **Camera Turn**, **Height**, **Distance** | the camera follows the duck |
| **Floor** | off: the duck alone, to put over another image |

In `duck_hub`'s Mode Walk, which leaves the duck its head, it looks around when left alone for
two seconds, as Pollen's duck does, also when it sits. Anything it is asked ends that.

Its first output is the rendered duck (a TOP). Its second is the pose it shows: `place/x`,
`place/y` and `place/heading` (where it is on the floor), `trunk/z` and `trunk/rx` ...
`trunk/rz`, every joint in degrees, and `gesture`, what it is doing: 0 nothing, 1 roll,
2 kick_left, 3 kick_right, 4 pick, 5 sit, 6 stand, 7 fall, 8 get_up, 9 sitting, 10 lying.

The duck's shapes are Pollen Robotics' ([microduck_rl](https://github.com/pollen-robotics/microduck_rl)),
under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), and so is
`duck_model.tox`, which carries them: for non-commercial use, with credit to Pollen
Robotics, and what you make from it under the same licence. The
[notice](../touchdesigner/components/duck_model_LICENSE.md) says what was changed.
