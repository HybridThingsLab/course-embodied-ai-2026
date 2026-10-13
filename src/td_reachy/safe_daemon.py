"""Start the Reachy Mini daemon with a speed limit on the base rotation motor.

Why: the daemon's automatic-body-yaw IK re-derives head yaw from the commanded
pose *matrix* (wrapped to ±π) and drags the base joint to within ±65° of it.
Any discontinuity in that value — the ±180° yaw wrap, a tracking jump
forwarded by a client, a large goto — becomes an instantaneous base joint
step which the servo chases at full speed (~275° whip measured; nearly tipped
the robot). Client-side rate limiting cannot help because the step is generated
inside the daemon, after IK.

This launcher patches the real-robot backend so every base goal written to the
motor is slew-limited (speed- and acceleration-capped), no matter which code
path produced it. The head keeps its commanded orientation relative to the
base, so a runaway target turns into a slow, harmless sweep.

Usage — exactly like `reachy-mini-daemon`, same arguments:

    python -m td_reachy.safe_daemon     (the station does this with --robot)

Tuning (env vars, radians): REACHY_MAX_BODY_YAW_SPEED (default 5.0 rad/s ≈
286°/s), REACHY_MAX_BODY_YAW_ACCEL (default 6.0 rad/s² ≈ 344°/s²). The
acceleration is the anti-tip parameter — raise the speed first. This is a
*backstop*, not a way to make the base faster.

Only the real-robot backend is patched; `--sim` / `--mockup-sim` run unchanged
(on macOS the MuJoCo sim still needs `mjpython`, see docs/simulation.md).
"""

import logging
import math
import os
import time

# What tips the robot is angular acceleration (reaction torque against a small
# footprint), not top speed — so the speed cap is generous enough to stay out
# of the way of normal motion, and the acceleration cap does the safety work.
# They sit above what deliberate base motion needs, so this only binds on jumps
# nobody commanded.
MAX_BODY_YAW_SPEED = float(os.environ.get("REACHY_MAX_BODY_YAW_SPEED", "5.0"))
MAX_BODY_YAW_ACCEL = float(os.environ.get("REACHY_MAX_BODY_YAW_ACCEL", "6.0"))

# A silent gap in base writes means torque was off / mode changed and the base
# may have been moved by hand — re-seed from the measured position so the next
# goal can't yank it from a stale one.
RESEED_AFTER = 0.5  # seconds

logger = logging.getLogger("td_reachy.safe_daemon")


class BodyYawSlewProxy:
    """Wraps the Rust motor-control loop; slew-limits `set_body_rotation`.

    Everything else is delegated untouched. The daemon's control loop calls
    `set_body_rotation` at 50 Hz in position mode, so stepping the goal here
    converges on the requested target at the capped speed.
    """

    def __init__(self, inner):
        self._inner = inner
        self._pos = None  # last goal actually written (rad)
        self._vel = 0.0
        self._t = None

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def _seed(self, fallback):
        try:
            return self._inner.get_last_position().body_yaw
        except Exception:
            return fallback

    def set_body_rotation(self, position):
        now = time.monotonic()
        if self._pos is None or (self._t is not None and now - self._t > RESEED_AFTER):
            self._pos = self._seed(position)
            self._vel = 0.0
        dt = 0.02 if self._t is None else min(max(now - self._t, 0.0), 0.1)
        self._t = now

        gap = position - self._pos
        dv_limit = MAX_BODY_YAW_ACCEL * dt
        v0 = self._vel  # velocity at the start of the tick — the cap is
        # measured against this, so a tick can never change it by more than
        # dv_limit no matter which branch below runs.

        if gap != 0.0:
            # Ease in and out. The continuous √(2·a·d) profile arrives with
            # residual velocity when integrated in discrete ticks (velocity
            # can only change a·dt per tick, so it lags the curve and the
            # last tick has to stop abruptly). This is its discrete-safe
            # form — the largest speed from which a·dt-limited braking still
            # halts within `gap` — so the base coasts to a stop instead.
            approach = -dv_limit / 2 + math.sqrt(
                (dv_limit / 2) ** 2 + 2 * MAX_BODY_YAW_ACCEL * abs(gap)
            )
            want = math.copysign(min(MAX_BODY_YAW_SPEED, approach), gap)
        else:
            want = 0.0

        # Never travel further than the remaining gap: landing exactly on the
        # target beats overshooting and coming back.
        if dt > 0 and abs(want * dt) >= abs(gap):
            want = gap / dt
        vel = v0 + min(max(want - v0, -dv_limit), dv_limit)
        step = vel * dt
        if abs(step) >= abs(gap):
            self._pos = position
        else:
            self._pos += step
        self._vel = vel
        self._inner.set_body_rotation(self._pos)


def _patch_robot_backend():
    from reachy_mini.daemon.backend.robot import backend as robot_backend

    original_init = robot_backend.RobotBackend.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if self.c is not None:
            self.c = BodyYawSlewProxy(self.c)
            self.logger.info(
                "safe_daemon: body yaw slew limiter active "
                f"(max {MAX_BODY_YAW_SPEED:.2f} rad/s, {MAX_BODY_YAW_ACCEL:.2f} rad/s²)"
            )

    robot_backend.RobotBackend.__init__ = patched_init


def main() -> None:
    _patch_robot_backend()
    logger.info("safe_daemon: RobotBackend patched, starting daemon")
    from reachy_mini.daemon.app.main import main as daemon_main

    daemon_main()


if __name__ == "__main__":
    main()
