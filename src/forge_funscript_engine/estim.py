"""Section 7.1 / 7.3: derive the full e-stim channel set from one chapter's
signal + Feel. Each channel is a per-sample decoded float series (pre-safety).

Minimal set = alpha + beta + volume (the playable subset, section 7.1). The full
superset adds the variants and texture channels; restim consumes the subset it is
configured for and ignores the rest ("emit-superset, consume-subset").

Channel value spaces (encoded to funscript pos 0..100 downstream):
  alpha / beta / alpha-prostate ............ [0, 1]   (capped to 0.998, section 7.4)
  volume / -prostate / -stereostim ......... [0, MAX_VOLUME]  (decoded, section 9)
  frequency / pulse_frequency / pulse_width  [0, 1]   (restim maps to its Hz/width range)
"""
from .lift import alpha_beta, speed_per_sample, SPEED_AT_EDGE
from .safety import MAX_VOLUME

# channel order, section 7.1
MINIMAL = ("alpha", "beta", "volume")
FULL = ("alpha", "alpha-prostate", "beta", "frequency", "pulse_frequency",
        "pulse_width", "volume", "volume-prostate", "volume-stereostim")
RISE_TIME = "pulse_rise_time"   # emitted only when enabled (section 7.3)

# [calibrate] -- section 7.3 blend / mapping constants
W_RAMP = 0.4          # volume blend: Passage ramp weight
W_SPEED = 0.6         # volume blend: instantaneous speed weight
PROSTATE_FLOOR = 0.35  # raised floor for the -prostate volume variant
STEREO_LO, STEREO_HI = 0.0, MAX_VOLUME   # stereostim remap window (placeholder, Q#3)
F_RAMP = 0.5          # carrier frequency blend: ramp weight (speed weight = 1 - this)


def _clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _alpha_speed_norm(alpha):
    """Per-sample |d(alpha)| normalized -- drives the pulse channels (section 7.3)."""
    n = len(alpha)
    if n < 2:
        return [0.0] * n
    # alpha already in [0,1]; scale its per-step delta so typical motion ~ 1.
    out = [0.0]
    for i in range(1, n):
        out.append(_clamp01(abs(alpha[i] - alpha[i - 1]) * 8.0))  # [calibrate]
    return out


def derive_channels(sig, feel, ramp, full=True, enable_rise_time=False):
    """Section 7.1/7.3 channels for one chapter. Returns {channel: [float, ...]}."""
    n = len(sig.xs)
    alpha, beta = alpha_beta(sig, feel)
    speed = speed_per_sample(sig.v, n)
    s_norm = [_clamp01(s / SPEED_AT_EDGE) for s in speed]

    # volume envelope in unit space, then scaled to the decoded MAX_VOLUME range.
    vol_unit = [_clamp01((W_RAMP * ramp + W_SPEED * sn) * feel.intensity) for sn in s_norm]
    volume = [v * MAX_VOLUME for v in vol_unit]

    ch = {"alpha": alpha, "beta": beta, "volume": volume}
    if not full:
        return ch

    a_speed = _alpha_speed_norm(alpha)
    speed_w = 1.0 - F_RAMP
    ch["alpha-prostate"] = [_clamp01(1.0 - a) for a in alpha]
    ch["volume-prostate"] = [
        (PROSTATE_FLOOR + (1.0 - PROSTATE_FLOOR) * v) * MAX_VOLUME for v in vol_unit
    ]
    ch["volume-stereostim"] = [STEREO_LO + (STEREO_HI - STEREO_LO) * v for v in vol_unit]
    # carrier: ramp+speed blend, Pace biases toward speed (section 7.3)
    ch["frequency"] = [
        _clamp01(F_RAMP * ramp + speed_w * (0.4 + 0.6 * feel.pace) * sn) for sn in s_norm
    ]
    # pulse rate: alpha-motion + Pace driven
    ch["pulse_frequency"] = [_clamp01(0.3 * feel.pace + 0.7 * a) for a in a_speed]
    # pulse width: Sharpness narrows it (lower value = narrower)
    ch["pulse_width"] = [
        _clamp01((1.0 - 0.6 * feel.sharpness) * (0.5 + 0.5 * a)) for a in a_speed
    ]
    if enable_rise_time:
        ch[RISE_TIME] = [_clamp01(0.3 + 0.4 * feel.sharpness)] * n
    return ch
