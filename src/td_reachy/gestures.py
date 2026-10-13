"""Reusable head + antenna gestures for Reachy Mini.

The head is a 6-DOF Stewart platform commanded with 4x4 world-frame poses. We
build those with the SDK helper ``create_head_pose(x, y, z, roll, pitch, yaw)``
(angles in degrees by default; translation in metres unless ``mm=True``).

Orientation convention (from the head's neutral, looking straight ahead):
    - yaw   (about Z) → turn left / right   → "no" shake
    - pitch (about Y) → nod up / down       → "yes" nod
    - roll  (about X) → tilt sideways       → "curious"

Safety: the SDK clamps head pitch/roll to +/-40 deg (the bridge limits them further,
to +/-30 roll and +/-27 pitch: beyond that the real head hits the body), yaw to +/-180 deg, and
body_yaw to +/-160 deg, so the small amplitudes here stay well inside limits.

Prerequisite: call ``mini.enable_motors()`` once after connecting — motors are
compliant (torque off) by default and nothing moves until then.

Every ``goto_target`` call blocks until the movement finishes, so these
functions are naturally sequential.
"""

from __future__ import annotations

import math
import time

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from reachy_mini.utils.interpolation import InterpolationTechnique

# Neutral head pose (identity 4x4 = looking straight ahead).
NEUTRAL = create_head_pose()

Method = InterpolationTechnique


def look(
    mini: ReachyMini,
    *,
    roll: float = 0.0,
    pitch: float = 0.0,
    yaw: float = 0.0,
    duration: float = 0.6,
    method: Method = Method.MIN_JERK,
) -> None:
    """Move the head to an orientation given in degrees (roll/pitch/yaw)."""
    mini.goto_target(
        create_head_pose(roll=roll, pitch=pitch, yaw=yaw),
        duration=duration,
        method=method,
    )


def neutral(mini: ReachyMini, duration: float = 0.6) -> None:
    """Return the head to the straight-ahead neutral pose."""
    mini.goto_target(NEUTRAL, duration=duration, method=Method.MIN_JERK)


def settle(mini: ReachyMini, duration: float = 0.5) -> None:
    """Park cleanly at the end of a run: ease to neutral, then release torque.

    Motors left enabled hold their last target under tension, and the Stewart
    platform can hunt around that setpoint (jitter). Call this from a ``finally``
    so every run — success, exception, or Ctrl+C — ends relaxed and quiet. To
    move again afterwards, re-enable with ``mini.enable_motors()``.
    """
    neutral(mini, duration=duration)
    mini.disable_motors()


def nod(mini: ReachyMini, times: int = 2, amplitude: float = 15.0, duration: float = 0.35) -> None:
    """"Yes" — pitch the head down and back up a few times."""
    for _ in range(times):
        look(mini, pitch=amplitude, duration=duration, method=Method.EASE_IN_OUT)
        look(mini, pitch=-amplitude / 2, duration=duration, method=Method.EASE_IN_OUT)
    neutral(mini, duration=duration)


def shake(mini: ReachyMini, times: int = 2, amplitude: float = 20.0, duration: float = 0.3) -> None:
    """"No" — yaw the head left and right a few times."""
    for _ in range(times):
        look(mini, yaw=amplitude, duration=duration, method=Method.EASE_IN_OUT)
        look(mini, yaw=-amplitude, duration=duration, method=Method.EASE_IN_OUT)
    neutral(mini, duration=duration)


def curious(mini: ReachyMini, roll: float = 20.0, hold: float = 0.6, duration: float = 0.6) -> None:
    """Tilt the head to one side (with a perky antenna accent) and hold briefly."""
    mini.goto_target(
        create_head_pose(roll=roll),
        antennas=[0.6, -0.6],
        duration=duration,
        method=Method.CARTOON,
    )
    time.sleep(hold)
    mini.goto_target(NEUTRAL, antennas=[0.0, 0.0], duration=duration, method=Method.MIN_JERK)


def circle(
    mini: ReachyMini,
    revolutions: float = 2.0,
    amplitude: float = 15.0,
    period: float = 1.8,
    fps: float = 100.0,
) -> None:
    """Roll the head around so the gaze traces a circle (the nose sweeps a cone).

    Unlike the blocking ``goto_target`` gestures, this streams closely-spaced
    poses with ``set_target`` at ``fps`` frames/sec — the motor control loop
    interpolates between them, giving one continuous circular sweep instead of
    a sequence of discrete moves. ``period`` is the seconds per revolution.

    ``fps`` deliberately oversamples the daemon's ~50 Hz control loop (100 Hz,
    matching the SDK's own ``play_move``); streaming *at* 50 fps beats against
    the loop and shows up as buzz during the sweep.
    """
    # Ease into the top of the circle first so the stream doesn't start with a jump.
    look(mini, pitch=amplitude, yaw=0.0, duration=0.5)

    steps_per_rev = max(8, int(round(period * fps)))
    dt = period / steps_per_rev
    try:
        for i in range(int(steps_per_rev * revolutions) + 1):
            theta = 2.0 * math.pi * i / steps_per_rev
            mini.set_target(
                create_head_pose(pitch=amplitude * math.cos(theta), yaw=amplitude * math.sin(theta))
            )
            time.sleep(dt)
    finally:
        # Even on Ctrl+C, ease back to neutral rather than freezing on the last
        # streamed target (a held pose lets the platform hunt around it → jitter).
        neutral(mini)


def look_around(mini: ReachyMini, duration: float = 0.7) -> None:
    """Sweep the gaze around, then settle back to neutral."""
    for yaw, pitch in [(30, 0), (-30, 0), (0, 12), (0, -12), (0, 0)]:
        look(mini, yaw=yaw, pitch=pitch, duration=duration)
