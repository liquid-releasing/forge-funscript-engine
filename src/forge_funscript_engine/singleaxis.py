"""Section 8: single-axis stroker profiles (Handy, Vacuglide).

One conditioned **position** track. Each device exposes its own knob set; `norm_knobs`
maps it down to the four uniform conditioning primitives so the synth stays uniform:

    device knobs --norm_knobs--> {smoothing, quiet, rate, lead}

`build_device` then conditions the position curve in the fixed order
(section 8 / prototype buildDevice): smooth -> floor (quiet) -> clamp per-step delta
(rate) -> apply lead. Output is one position series in [0, 1].
"""
from .analyze import DT_MS, DT_S
from .safety import clamp

# Each device's own knob set (section 8 schemas). Values are sensible defaults.
KNOBS = {
    "handy": {"max_bpm": 120, "smoothing": 0.3, "lead_ms": 100, "step": 0.02},
    "vacuglide": {"stroke_window": 0.85, "smoothing": 0.6, "max_bpm": 80, "lead_ms": 150},
}


def norm_knobs(device, knobs):
    """Map a device's knobs to {smoothing, quiet, rate, lead} (section 5.1)."""
    k = dict(KNOBS[device])
    k.update(knobs or {})
    # rate = max per-step position delta reachable at the BPM ceiling.
    # one cycle = 2 strokes = 2.0 travel; cycles/s = bpm/60.
    rate = 2.0 * k["max_bpm"] / 60.0 * DT_S
    return {
        "smoothing": clamp(k["smoothing"], 0.0, 0.95),
        "quiet": 0.0,                       # strokers idle at rest, no current floor
        "rate": rate,
        "lead": k["lead_ms"],
        "window": k.get("stroke_window", None),
        "step": k.get("step", 0.0),
    }


def _smooth(xs, smoothing):
    """One-pole low-pass; smoothing in [0,1) -> heavier averaging."""
    if not xs:
        return xs
    a = 1.0 - smoothing
    out = [xs[0]]
    for x in xs[1:]:
        out.append(out[-1] + a * (x - out[-1]))
    return out


def _rate_clamp(xs, rate):
    if not xs:
        return xs
    out = [xs[0]]
    for x in xs[1:]:
        d = max(-rate, min(rate, x - out[-1]))
        out.append(out[-1] + d)
    return out


def _lead(xs, lead_ms):
    """Advance the command by lead_ms to beat transport/servo latency."""
    shift = int(round(lead_ms / DT_MS))
    if shift <= 0 or not xs:
        return xs
    return xs[shift:] + [xs[-1]] * shift


def build_device(xs, feel, device="handy", knobs=None):
    """Condition the resampled position curve `xs` (0..1) into one device track."""
    prim = norm_knobs(device, knobs)
    # Depth / stroke window sets how much travel is used; center on 0.5.
    window = prim["window"] if prim["window"] is not None else feel.depth
    pos = [clamp(0.5 + (x - 0.5) * window, 0.0, 1.0) for x in xs]
    # Focus tightens tracking -> less extra smoothing; combine with the device knob.
    smoothing = clamp(prim["smoothing"] + 0.3 * (1.0 - feel.focus), 0.0, 0.95)
    pos = _smooth(pos, smoothing)
    pos = [max(prim["quiet"], p) for p in pos]      # floor
    pos = _rate_clamp(pos, prim["rate"])            # BPM ceiling reachability
    pos = _lead(pos, prim["lead"])                  # latency lead
    return pos
