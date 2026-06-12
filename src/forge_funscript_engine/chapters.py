"""Section 7.5: per-chapter generation + seam stitching.

Chapters are the generation unit (3-5 min, spec section 2.2). Each chapter derives
its own Feel and channels; concatenating them can leave a discontinuity at the seam.
`stitch` crossfades a short window across each boundary so the per-seam delta stays
within the safe envelope (section 9) -- this is what differentiates us from edger's
single global pass.

Real chapterization is audio/video analysis (section 10, [chapterize]); the host
(funscriptforge) owns it. This engine *consumes* boundaries, which may arrive as:
  - None                      -> one chapter (whole clip)
  - an int N                  -> N equal splits (testing convenience)
  - [(start_ms, end_ms), ...] -> explicit tuples (a first-class library option)
  - a standalone sidecar JSON -> parsed by `load_chapters_file` (-> tuples)
"""
import json

from .safety import SEAM_MAX_DELTA

SEAM_WINDOW = 12   # samples crossfaded on each side of a seam (~240 ms at 20 ms) [calibrate]

# key aliases tolerated in a sidecar chapter entry (so we fit common schemas)
_START_KEYS = ("at_ms", "start_ms", "start", "startTime", "start_time", "startTimeMs",
               "from", "begin", "at", "time")
_END_KEYS = ("end", "endTime", "end_ms", "end_time", "to", "finish", "stop")
_DUR_KEYS = ("duration", "dur", "length")
_NAME_KEYS = ("name", "title", "label", "chapter")


def slice_actions(actions, start_ms, end_ms):
    """Actions whose timestamp falls in [start_ms, end_ms]."""
    return [a for a in actions if start_ms <= a["at"] <= end_ms]


def to_ms(value):
    """Coerce a sidecar time to integer milliseconds. A bare number -- or a bare
    numeric string -- is taken as milliseconds (the funscript `at` convention).
    A colon-separated string is parsed as a clock time: 'HH:MM:SS.mmm' / 'MM:SS.mmm'."""
    if isinstance(value, bool):
        raise ValueError("chapter time cannot be a boolean")
    if isinstance(value, (int, float)):
        return int(round(value))
    if isinstance(value, str):
        s = value.strip()
        if ":" in s:
            parts = s.split(":")
            sec = float(parts[-1])
            mins = int(parts[-2]) if len(parts) >= 2 else 0
            hrs = int(parts[-3]) if len(parts) >= 3 else 0
            return (hrs * 3600 + mins * 60) * 1000 + int(round(sec * 1000))
        return int(round(float(s)))
    raise ValueError(f"unrecognized chapter time: {value!r}")


def _pick(entry, keys):
    for k in keys:
        if k in entry and entry[k] is not None:
            return entry[k]
    return None


def parse_chapters(doc, clip_end_ms=None):
    """A loaded sidecar doc -> [(start_ms, end_ms), ...], sorted by start.

    Accepts a top-level list or an object with a 'chapters' (or 'Chapters') array.
    Entries need a start; an end is taken from end/duration, else the next chapter's
    start, else clip_end_ms. Entries without a start are skipped.
    """
    if isinstance(doc, dict):
        entries = doc.get("chapters") or doc.get("Chapters") or []
    elif isinstance(doc, list):
        entries = doc
    else:
        raise ValueError("chapter sidecar must be a list or have a 'chapters' array")

    parsed = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        raw_start = _pick(e, _START_KEYS)
        if raw_start is None:
            continue
        start = to_ms(raw_start)
        raw_end = _pick(e, _END_KEYS)
        if raw_end is not None:
            end = to_ms(raw_end)
        else:
            dur = _pick(e, _DUR_KEYS)
            end = start + to_ms(dur) if dur is not None else None
        parsed.append([start, end])

    parsed.sort(key=lambda p: p[0])
    out = []
    for i, (start, end) in enumerate(parsed):
        if end is None:
            end = parsed[i + 1][0] if i + 1 < len(parsed) else clip_end_ms
        if end is None or end <= start:
            continue
        out.append((start, end))
    return out


def load_chapters_file(path, clip_end_ms=None):
    """Load and parse a standalone chapter sidecar JSON -> [(start_ms, end_ms), ...]."""
    with open(path, "r", encoding="utf-8") as f:
        return parse_chapters(json.load(f), clip_end_ms)


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
