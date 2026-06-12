"""Section 7.2: the 1-D -> 2-D lift. One stroke signal -> the spatial (alpha, beta)
position on the unit disc. The real geometry that replaces the prototype's sine.

    radius(t) = min_distance + (1 - min_distance) * clamp(speed/speed_at_edge, 0, 1)
                * (0.5 + 0.5 * Depth)
    alpha(t)  = 0.5 + 0.5 * radius * cos(theta)
    beta(t)   = 0.5 + 0.5 * radius * sin(theta)

Lift style (section 7.2 table) is selected from Feel, not hand-picked:
**Wildness** widens theta's span (Circular semicircle -> full rotation), **Pace** is
the angular rate (already carried by the motion), **Depth** the radius envelope,
**Focus** the smoothing of theta.
"""
import math

SPEED_AT_EDGE = 4.0   # velocity at which radius reaches the electrode edge [calibrate]
MIN_DISTANCE = 0.1    # radius floor for slow motion (diffuse center) [calibrate]


def speed_per_sample(v, n):
    """|velocity| aligned to the n resample samples (v has n-1 entries)."""
    if not v:
        return [0.0] * n
    return [abs(v[0])] + [abs(vi) for vi in v]


def theta_span(feel):
    """Wildness widens the angular sweep: pi (semicircle) .. 2*pi (full). [calibrate]"""
    return math.pi * (1.0 + feel.wildness)


def radius_series(sig, feel):
    """Per-sample radius in [MIN_DISTANCE, 1], growing with speed and Depth."""
    n = len(sig.xs)
    speed = speed_per_sample(sig.v, n)
    span = 1.0 - MIN_DISTANCE
    depth_env = 0.5 + 0.5 * feel.depth
    out = []
    for i in range(n):
        s_norm = max(0.0, min(1.0, speed[i] / SPEED_AT_EDGE))
        out.append(MIN_DISTANCE + span * s_norm * depth_env)
    return out


def alpha_beta(sig, feel):
    """Return (alpha[], beta[]) decoded channel values in [0, 1], one per sample."""
    xs = sig.xs
    n = len(xs)
    if n == 0:
        return [], []
    radius = radius_series(sig, feel)
    span = theta_span(feel)
    alpha, beta = [], []
    for i in range(n):
        theta = span * xs[i]
        alpha.append(0.5 + 0.5 * radius[i] * math.cos(theta))
        beta.append(0.5 + 0.5 * radius[i] * math.sin(theta))
    return alpha, beta
