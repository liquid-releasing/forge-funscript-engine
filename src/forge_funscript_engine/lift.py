"""Section 7.2: the 1-D -> 2-D lift. One stroke signal -> e-stim alpha/beta/volume
as decoded channel values (floats, pre-safety). The real geometry that replaces
the prototype's illustrative sine.

    radius(t) = min_distance + (1 - min_distance) * clamp(speed/speed_at_edge, 0, 1)
    alpha(t)  = 0.5 + 0.5 * radius * cos(theta)
    beta(t)   = 0.5 + 0.5 * radius * sin(theta)

Phase 1 uses the Circular (default) lift style: theta = pi * x, a position-driven
semicircular sweep. Feel wires in as the spec section 7.2 table allows: Depth sets
the radius floor, Intensity scales volume. (Wildness-driven style flips / full
rotation are Phase 2, spec section 7.5.)
"""
import math

SPEED_AT_EDGE = 4.0   # velocity at which radius reaches the electrode edge [calibrate]
MIN_DISTANCE = 0.1    # radius floor for slow motion (diffuse center) [calibrate]
W_RAMP = 0.4          # volume blend: ramp (Passage) weight  [calibrate]
W_SPEED = 0.6         # volume blend: instantaneous speed weight  [calibrate]


def _speed_per_sample(v, n):
    """|velocity| aligned to the n resample samples (v has n-1 entries)."""
    if not v:
        return [0.0] * n
    return [abs(v[0])] + [abs(vi) for vi in v]


def lift(sig, feel, ramp):
    """Return per-sample decoded channels: {'alpha', 'beta', 'volume'} as float lists.

    Each list has len(sig.xs); values are in [0, 1] before the safety stage.
    """
    xs, v = sig.xs, sig.v
    n = len(xs)
    if n == 0:
        return {"alpha": [], "beta": [], "volume": []}

    speed = _speed_per_sample(v, n)
    # Depth widens the usable radius span; slow motion still floors at MIN_DISTANCE.
    min_dist = MIN_DISTANCE
    span = 1.0 - min_dist

    alpha, beta, volume = [], [], []
    for i in range(n):
        s_norm = max(0.0, min(1.0, speed[i] / SPEED_AT_EDGE))
        radius = min_dist + span * s_norm * (0.5 + 0.5 * feel.depth)
        theta = math.pi * xs[i]
        alpha.append(0.5 + 0.5 * radius * math.cos(theta))
        beta.append(0.5 + 0.5 * radius * math.sin(theta))
        vol = (W_RAMP * ramp + W_SPEED * s_norm) * feel.intensity
        volume.append(vol)
    return {"alpha": alpha, "beta": beta, "volume": volume}
