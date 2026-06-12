"""Section 3.2: base signals -> the 6 device-agnostic Feel dials, each in [0, 1].

Constants marked [calibrate] fix the mapping shape, not the final value; they
are tuned against real scripts (spec section 12). The test suite asserts the
relational invariants (set B), which hold for any sane constants.
"""
from dataclasses import dataclass

# [calibrate] -- section 3.2 default constants
V_REF = 4.0      # velocity that saturates Intensity's motion term
F_REF = 2.5      # Hz that saturates Pace
CV_REF = 0.8     # coefficient-of-variation that saturates Wildness
CF0 = 1.41       # crest factor of a pure sine -> Sharpness 0
CF_MAX = 3.0     # crest factor -> Sharpness 1
D_REF = 1.0      # travel fraction -> Depth 1 (no free constant)
A_R = 0.5        # ramp vs motion-energy weight in Intensity

RAMP_PER_HOUR = 15.0  # section 3.1 single-chapter ramp fallback (%/hour)


def _clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


@dataclass
class Feel:
    intensity: float
    pace: float
    wildness: float
    sharpness: float
    depth: float
    focus: float


def ramp_slice(T_s: float, ramp_per_hour: float = RAMP_PER_HOUR) -> float:
    """Phase-1 single-chapter Passage fallback (spec section 3.1, signal 6)."""
    return _clamp01(ramp_per_hour / 100.0 * (T_s / 3600.0))


def derive_feel(sig, ramp: float = None) -> Feel:
    """Map section 3 base signals -> Feel. `ramp` (R in [0,1]) defaults to the
    single-chapter fallback derived from the window length."""
    R = ramp_slice(sig.T_s) if ramp is None else _clamp01(ramp)
    intensity = _clamp01(A_R * R + (1 - A_R) * min(sig.v_rms / V_REF, 1.0))
    pace = _clamp01(sig.f_hz / F_REF)
    wildness = _clamp01(
        0.5 * min(sig.cv_d / CV_REF, 1.0) + 0.5 * min(sig.cv_a / CV_REF, 1.0)
    )
    sharpness = _clamp01((sig.crest - CF0) / (CF_MAX - CF0)) if sig.crest > 0 else 0.0
    depth = _clamp01(sig.depth / D_REF)
    focus = _clamp01(sig.autocorr)
    return Feel(intensity, pace, wildness, sharpness, depth, focus)
