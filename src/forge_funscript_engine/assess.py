"""Sections 3 / 10: consume the host's assess-stage output (phrases.json) as Feel.

The host (funscriptforge / videoflow) already computes per-phrase metrics — bpm,
span, velocities, ramp, pattern tags — in its `[assess]` stage. The spec's primary
Feel path is to *read off those* (motion derivation is the fallback when no assess
bundle is present).

Phase-1 scope: override the two dials the host computes authoritatively and whose
units are unambiguous — **bpm → Pace** and **span → Depth**. Adopting host `span`
also resolves the Depth median-vs-range tension in the host's favor (span is the
range the motion uses). Intensity / Sharpness / Wildness / Focus stay on the
motion-derived base until the host's velocity units are calibrated (spec §12).

Cross-checked against the real `.forge` bundles (big_buck_bunny, ipzz125, voaks):
our motion `f_hz×60` tracks host `bpm` within ~10%.
"""
import json

from .feel import Feel, F_REF, _clamp01

BPM_REF = F_REF * 60.0   # bpm that saturates Pace (F_REF Hz × 60 = 150 bpm) [calibrate]


def load_phrases(path):
    """Load a host phrases.json sidecar -> list of phrase slice dicts (with metrics)."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    if isinstance(doc, dict):
        return doc.get("slices") or doc.get("phrases") or []
    return doc if isinstance(doc, list) else []


def feel_from_phrase(metrics, base):
    """Overlay host phrase `metrics` onto a motion-derived `base` Feel.

    Overrides Pace (from `bpm`) and Depth (from `span`, a 0-100 range) where present;
    every other dial is taken from `base`.
    """
    bpm = metrics.get("bpm")
    pace = _clamp01(bpm / BPM_REF) if bpm is not None else base.pace
    span = metrics.get("span")
    depth = _clamp01(span / 100.0) if span is not None else base.depth
    return Feel(base.intensity, pace, base.wildness, base.sharpness, depth, base.focus)
