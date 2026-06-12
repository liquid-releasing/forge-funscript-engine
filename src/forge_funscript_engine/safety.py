"""Section 9 safety envelope. Applied as the FINAL stage of every channel.

E-stim drives current through the body; these bounds are a safety boundary,
not a feel knob. Every output is hard-clamped to its device range AFTER all
math. Treat restim's documented ranges as a validated baseline (spec section 9).
"""
import math

CH_MAX = 0.998        # restim alpha/beta/volume decoded ceiling (spec section 7.4)
MAX_VOLUME = 0.7      # global volume ceiling, default <= 0.7 (spec section 9)
RATE_CAP = 0.05       # max per-step volume delta (smooth-ramp requirement) [calibrate]
SEAM_MAX_DELTA = 0.05  # max per-step delta allowed across a chapter seam (section 7.5)
POS_MAX = 1.0         # single-axis position uses the full 0..100 funscript range

# Carrier-frequency safety (restim e-stim-safety wiki: IEC 60601-2-10 + charge-per-phase).
# A carrier BELOW the safe minimum delivers unsafe charge per phase (thermal/tissue) and
# draws far less safe current at low Hz. restim's worked examples: >= 446 Hz (15 cm^2 glans
# loop) .. >= 755 Hz (9 cm^2 shaft). We floor the carrier so it can never drop below this.
FREQ_MAX_HZ = 1200.0     # carrier normalization max (edger, spec section 7.4)
MIN_CARRIER_HZ = 500.0   # safe carrier floor; RAISE to ~755 for small electrodes [safety-config]


def channel_ceiling(name):
    """Decoded ceiling for a channel: volume family is current-bearing -> MAX_VOLUME;
    everything else is capped to the restim CH_MAX (section 7.4 / 9)."""
    return MAX_VOLUME if name.startswith("volume") else CH_MAX


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


def carrier_floor_norm():
    """The MIN_CARRIER_HZ floor expressed as a normalized [0,1] funscript value."""
    return MIN_CARRIER_HZ / FREQ_MAX_HZ


def apply_carrier_floor(values):
    """Clamp normalized carrier-frequency values UP to the safe minimum so the decoded
    carrier never drops below MIN_CARRIER_HZ (restim e-stim-safety). NaN/Inf -> floor."""
    floor = carrier_floor_norm()
    return [max(floor, min(1.0, _finite(v))) for v in values]


def encode_pos(value, ceiling=CH_MAX):
    """Decoded channel value in [0, ceiling] -> integer funscript pos in [0, 100].

    Guarantees pos/100 <= ceiling so the decoded value never exceeds the device
    range (e.g. ceiling 0.998 -> pos <= 99; volume ceiling 0.7 -> pos <= 70).
    """
    value = clamp(value, 0.0, ceiling)
    pos_max = int(math.floor(ceiling * 100))
    pos = int(math.floor(value * 100 + 0.5))
    return max(0, min(pos_max, pos))
