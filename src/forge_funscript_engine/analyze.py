"""Section 3 motion analysis: a funscript's actions -> the constant-free base signals.

These are the production reimplementation of the reference oracle in
tests/make_fixtures.py. The test suite asserts this reproduces goldens.json
within tolerance (set A) and that the relational invariants hold (set B).

Everything here is NaN-safe (spec section 3.4): pathological inputs (empty,
single point, flat, huge gap, monotonic, max-speed) yield finite signals.
"""
import math
from dataclasses import dataclass, field

DT_MS = 20.0           # resample step, 50 Hz (spec section 3.1)
DT_S = DT_MS / 1000.0
P_MIN = 0.05           # reversal prominence floor, rejects jitter (spec section 3.1)


@dataclass
class Signals:
    n_samples: int
    T_s: float          # window duration, seconds
    f_hz: float         # stroke frequency
    depth: float        # median stroke amplitude (travel fraction)
    cv_d: float         # coefficient of variation of stroke durations
    cv_a: float         # coefficient of variation of stroke amplitudes
    crest: float        # velocity crest factor (waveform sharpness)
    v_rms: float        # rms velocity (motion energy)
    autocorr: float     # autocorrelation at the dominant lag (coherence)
    xs: list = field(default_factory=list, repr=False)  # resampled position, 0..1
    v: list = field(default_factory=list, repr=False)   # velocity per sample


def _resample(actions):
    """Linear interpolation onto a uniform DT_MS grid. Returns (xs, T_s)."""
    if len(actions) < 2:
        return [], 0.0
    t0, t1 = actions[0]["at"], actions[-1]["at"]
    if t1 <= t0:
        return [actions[0]["pos"] / 100.0], 0.0
    n = int((t1 - t0) / DT_MS) + 1
    xs, j = [], 0
    for i in range(n):
        t = t0 + i * DT_MS
        while j < len(actions) - 2 and actions[j + 1]["at"] < t:
            j += 1
        a, b = actions[j], actions[j + 1]
        span = b["at"] - a["at"]
        frac = 0.0 if span <= 0 else max(0.0, min(1.0, (t - a["at"]) / span))
        xs.append((a["pos"] + (b["pos"] - a["pos"]) * frac) / 100.0)
    return xs, (t1 - t0) / 1000.0


def _diff(arr):
    return [(arr[i] - arr[i - 1]) / DT_S for i in range(1, len(arr))]


def _reversals(actions):
    """Turning points from the sparse action list, prominence-filtered.

    Dwell plateaus (runs of equal pos) are collapsed first so a hold-then-snap
    still registers its reversals (drives the sharp-snap crest signal).
    """
    raw = [(a["at"], a["pos"] / 100.0) for a in actions]
    pts = [raw[0]] if raw else []
    for p in raw[1:]:
        if p[1] != pts[-1][1]:
            pts.append(p)
    if len(pts) < 3:
        return []
    ext = [pts[0]]
    for i in range(1, len(pts) - 1):
        prev, cur, nxt = pts[i - 1][1], pts[i][1], pts[i + 1][1]
        if (cur - prev) * (nxt - cur) < 0:          # slope sign change
            if abs(cur - ext[-1][1]) >= P_MIN:
                ext.append(pts[i])
    if abs(pts[-1][1] - ext[-1][1]) >= P_MIN:
        ext.append(pts[-1])
    return ext


def _mean(a):
    return sum(a) / len(a) if a else 0.0


def _std(a):
    if len(a) < 2:
        return 0.0
    m = _mean(a)
    return math.sqrt(sum((x - m) ** 2 for x in a) / len(a))


def _rms(a):
    return math.sqrt(sum(x * x for x in a) / len(a)) if a else 0.0


def _pctl(a, q):
    if not a:
        return 0.0
    s = sorted(a)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] if lo == hi else s[lo] * (hi - k) + s[hi] * (k - lo)


def _autocorr_at(xs, lag):
    if lag <= 0 or lag >= len(xs):
        return 0.0
    m = _mean(xs)
    denom = sum((x - m) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    num = sum((xs[i] - m) * (xs[i + lag] - m) for i in range(len(xs) - lag))
    return num / denom


def analyze(actions) -> Signals:
    """Compute the section 3.1 base signals for a list of {at, pos} actions."""
    xs, T = _resample(actions)
    if len(xs) < 2:
        return Signals(len(xs), round(T, 3), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       xs=xs, v=[])
    v = _diff(xs)
    a = _diff(v)  # noqa: F841 -- acceleration available for future dials (section 3.2)
    ext = _reversals(actions)
    amps = [abs(ext[i + 1][1] - ext[i][1]) for i in range(len(ext) - 1)]
    durs = [(ext[i + 1][0] - ext[i][0]) / 1000.0 for i in range(len(ext) - 1)]
    K = len(ext)
    f = (K - 1) / (2 * T) if (T > 0 and K >= 2) else 0.0
    v_rms = _rms(v)
    crest = (_pctl([abs(x) for x in v], 0.95) / v_rms) if v_rms > 0 else 0.0
    med_amp = sorted(amps)[len(amps) // 2] if amps else (max(xs) - min(xs))
    lag = round((1.0 / f) / DT_S) if f > 0 else 0
    return Signals(
        n_samples=len(xs),
        T_s=round(T, 3),
        f_hz=round(f, 4),
        depth=round(med_amp, 4),
        cv_d=round(_std(durs) / _mean(durs), 4) if _mean(durs) > 0 else 0.0,
        cv_a=round(_std(amps) / _mean(amps), 4) if _mean(amps) > 0 else 0.0,
        crest=round(crest, 4),
        v_rms=round(v_rms, 4),
        autocorr=round(_autocorr_at(xs, lag), 4) if lag > 0 else 0.0,
        xs=xs,
        v=v,
    )
