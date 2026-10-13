"""Where a hand has put the head.

In teach mode the motors are soft and a hand moves the head. Every pose it is in then
has been reached: it is known to be possible. The bridge's limits do not know that.
Their rule for tilt and position sharing one room (``bridge.limit_shift``) is a careful
guess, and a movement taught by hand came back weaker than it was shown: the head had
been tilted and shifted further at once than the guess allows.

This module keeps what was reached, and the bridge lets a target go as far:

    for each tilt of the head (roll and pitch, in steps of TILT_STEP degrees),
    each turn of the head against the body (TURN_STEP degrees)
    and each direction of shift, seen from the body (DIRECTIONS steps per axis),
    the farthest the head has been shifted, in metres.

A target may be shifted that far in that direction at that tilt and turn - and less far
too, since a smaller shift at the same tilt is further from everything. Right next to
what was reached it still counts in full (up to one step away), then fades out over
half a step, so that nothing jumps when a target leaves the room.

Only the shared rule gives way. Each channel's own range, the tilt ellipse, the turn
limit and the speed limits stay as they are, whatever a hand has shown.

A pose where the head was resting on the body, or pressed against it, counts like any
other: played back, the motors hold it there. ``forget()`` empties the room.

The room is kept in a file, so a movement taught yesterday plays today. It belongs to
the robot it was taught on.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

TILT_STEP = 3.0     # degrees of roll, and of pitch, per step
TURN_STEP = 15.0    # degrees of head turn against the body per step
DIRECTIONS = 4      # steps per unit of the shift's direction: a step is about 14 degrees
MIN_SHIFT = 0.001   # metres: a smaller shift is not worth keeping (and has no direction)
SLACK = 0.0002      # metres: what a pose loses and gains on its way through a clip file

NEAR = (-1, 0, 1)


def _place(x, y, z, roll, pitch, yaw, body_yaw):
    """A pose as the room sees it: tilt and turn in steps, the shift's direction in
    steps (all not yet rounded), and the shift's length. The shift is turned into the
    body's frame: what matters is where the head is against the body, not in the room."""
    b = math.radians(body_yaw)
    bx, by = x * math.cos(b) + y * math.sin(b), -x * math.sin(b) + y * math.cos(b)
    length = math.sqrt(bx * bx + by * by + z * z)
    if length < MIN_SHIFT:
        return None, None, length
    tilt = (roll / TILT_STEP, pitch / TILT_STEP, (yaw - body_yaw) / TURN_STEP)
    direction = tuple(v / length * DIRECTIONS for v in (bx, by, z))
    return tilt, direction, length


def _near(value):
    """The steps near a value, each with how much it counts there: in full up to one
    step away, fading to nothing at one and a half."""
    centre = round(value)
    found = []
    for step in NEAR:
        weight = min(1.0, 3.0 - 2.0 * abs(value - (centre + step)))
        if weight > 0.0:
            found.append((centre + step, weight))
    return found


class TaughtRoom:
    """What a hand has reached, and how far a target may go because of it."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.cells: dict[tuple[int, int, int], dict[tuple[int, int, int], float]] = {}
        self.changed = False
        self.note = ""  # what happened to the file, for the bridge to print
        self.load()

    def __len__(self) -> int:
        return sum(len(directions) for directions in self.cells.values())

    def visit(self, x, y, z, roll, pitch, yaw, body_yaw) -> None:
        """The head is here, put there by a hand."""
        tilt, direction, length = _place(x, y, z, roll, pitch, yaw, body_yaw)
        if tilt is None:
            return
        directions = self.cells.setdefault(tuple(round(v) for v in tilt), {})
        key = tuple(round(v) for v in direction)
        if length > directions.get(key, 0.0):
            directions[key] = length
            self.changed = True

    def reach(self, x, y, z, roll, pitch, yaw, body_yaw) -> float:
        """How far a head tilted and turned like this may be shifted in this
        direction, in metres, going by what was reached. 0 where nothing was."""
        if not self.cells:
            return 0.0
        tilt, direction, _length = _place(x, y, z, roll, pitch, yaw, body_yaw)
        if tilt is None:
            return 0.0
        dx, dy, dz = (_near(v) for v in direction)
        best = 0.0
        for r, wr in _near(tilt[0]):
            for p, wp in _near(tilt[1]):
                for t, wt in _near(tilt[2]):
                    directions = self.cells.get((r, p, t))
                    if not directions:
                        continue
                    here = wr * wp * wt
                    for i, wi in dx:
                        for j, wj in dy:
                            for k, wk in dz:
                                reached = directions.get((i, j, k))
                                if reached:
                                    best = max(best, (reached + SLACK) * here * wi * wj * wk)
        return best

    def forget(self) -> None:
        """Empty the room, and take its file away."""
        self.cells, self.changed = {}, False
        if self.path is not None:
            self.path.unlink(missing_ok=True)

    # --- the file ---------------------------------------------------------------

    def load(self) -> None:
        if self.path is None or not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            steps = (data["tilt_step"], data["turn_step"], data["directions"])
            if steps != (TILT_STEP, TURN_STEP, DIRECTIONS):
                self.note = f"{self.path.name} was made with other steps: starting empty"
                return
            cells: dict = {}
            for r, p, t, i, j, k, millimetres in data["cells"]:
                cells.setdefault((int(r), int(p), int(t)), {})[(int(i), int(j), int(k))] = (
                    float(millimetres) / 1000.0)
            self.cells = cells
        except (OSError, ValueError, KeyError, TypeError):
            self.note = f"{self.path.name} cannot be read: starting empty"

    def save(self) -> None:
        """Write the room to its file, if there is one and something was added."""
        if self.path is None or not self.changed:
            return
        rows = [[*tilt, *direction, round(reached * 1000.0, 2)]
                for tilt, directions in sorted(self.cells.items())
                for direction, reached in sorted(directions.items())]
        text = json.dumps({"what": "where a hand has put the robot's head (td_reachy.taught_room)",
                           "tilt_step": TILT_STEP, "turn_step": TURN_STEP,
                           "directions": DIRECTIONS, "cells": rows})
        part = self.path.with_name(self.path.name + ".part")
        part.write_text(text, encoding="utf-8")
        part.replace(self.path)
        self.changed = False
