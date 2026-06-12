"""Section 7.5: per-chapter generation + seam stitching.

Chapters are the generation unit (3-5 min, spec section 2.2). Each chapter derives
its own Feel and channels; concatenating them can leave a discontinuity at the seam.
`stitch` crossfades a short window across each boundary so the per-seam delta stays
within the safe envelope (section 9) -- this is what differentiates us from edger's
single global pass.

Real chapterization is audio/video analysis (section 10, [chapterize]); here the
engine is chapter-aware and accepts explicit boundaries, defaulting to one chapter.
"""
from .safety import SEAM_MAX_DELTA

SEAM_WINDOW = 12   # samples crossfaded on each side of a seam (~240 ms at 20 ms) [calibrate]


def slice_actions(actions, start_ms, end_ms):
    """Actions whose timestamp falls in [start_ms, end_ms]."""
    return [a for a in actions if start_ms <= a["at"] <= end_ms]


def equal_chapters(actions, count):
    """Split the action timeline into `count` equal-duration chapter windows."""
    if count <= 1 or len(actions) < 2:
        return [actions]
    t0, t1 = actions[0]["at"], actions[-1]["at"]
    step = (t1 - t0) / count
    out = []
    for i in range(count):
        s = t0 + i * step
        e = t1 if i == count - 1 else t0 + (i + 1) * step
        out.append(slice_actions(actions, s, e))
    return out


def stitch(series, boundaries, window=SEAM_WINDOW):
    """Linear crossfade across each seam index so the boundary delta is bounded by
    |endpoints| / (2*window). Returns a new list; non-seam regions are untouched."""
    s = list(series)
    n = len(s)
    for b in boundaries:
        lo = max(0, b - window)
        hi = min(n - 1, b + window - 1)
        if hi <= lo:
            continue
        a, c = s[lo], s[hi]
        steps = hi - lo
        for k in range(lo, hi + 1):
            s[k] = a + (c - a) * (k - lo) / steps
    return s


def seam_deltas(series, boundaries):
    """The per-step delta at each seam boundary index (for the section 7.5 assertion)."""
    return [abs(series[b] - series[b - 1])
            for b in boundaries if 0 < b < len(series)]


def within_seam_envelope(series, boundaries, max_delta=SEAM_MAX_DELTA):
    return all(d <= max_delta + 1e-9 for d in seam_deltas(series, boundaries))
