"""Section 9 safety envelope. Applied as the FINAL stage of every channel.

E-stim drives current through the body; these bounds are a safety boundary,
not a feel knob. Every output is hard-clamped to its device range AFTER all
math. Treat restim's documented ranges as a validated baseline (spec section 9).
"""
import math

CH_MAX = 0.998        # restim alpha/beta/volume decoded ceiling (spec section 7.4)
MAX_VOLUME = 0.7      # global volume ceiling, default <= 0.7 (spec section 9)
RATE_CAP = 0.05       # max per-step volume delta (smooth-ramp requirement) [calibrate]


def _finite(x):
    """NaN/Inf -> 0.0 (section 3.4 / 9: never emit a non-finite channel value)."""
    return x if math.isfinite(x) else 0.0


def clamp(x, lo, hi):
    x = _finite(x)
    return lo if x < lo else hi if x > hi else x


def rate_limit(values, cap=RATE_CAP):
    """Clamp successive deltas to +/- cap (volume smooth-ramp, section 9)."""
    if not values:
        return values
    out = [clamp(values[0], 0.0, MAX_VOLUME)]
    for x in values[1:]:
        x = _finite(x)
        prev = out[-1]
        d = max(-cap, min(cap, x - prev))
        out.append(prev + d)
    return out


def encode_pos(value, ceiling=CH_MAX):
    """Decoded channel value in [0, ceiling] -> integer funscript pos in [0, 100].

    Guarantees pos/100 <= ceiling so the decoded value never exceeds the device
    range (e.g. ceiling 0.998 -> pos <= 99; volume ceiling 0.7 -> pos <= 70).
    """
    value = clamp(value, 0.0, ceiling)
    pos_max = int(math.floor(ceiling * 100))
    pos = int(math.floor(value * 100 + 0.5))
    return max(0, min(pos_max, pos))
