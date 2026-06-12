"""Forge Funscript Engine.

Parse a 1-D stroke funscript -> derive the 6-dial Feel from motion (spec section 3)
-> condition into device channels -> safety-clamp (section 9) -> valid funscript.

  - e-stim (`generate_estim`): alpha/beta/volume + the full superset, chapter-aware
    with seam stitching (sections 7.1-7.5).
  - single-axis strokers (`generate_single_axis`): one position track for Handy /
    Vacuglide (section 8).

See docs/unified-forge.spec.md.
"""
from .funscript import load_funscript, dump_funscript, Funscript
from .analyze import analyze, Signals
from .feel import derive_feel, Feel
from .pipeline import generate_estim, generate_single_axis
from .chapters import load_chapters_file, parse_chapters
from .assess import load_phrases, feel_from_phrase
from .bundle import load_bundle, generate_from_bundle, Bundle

__all__ = [
    "load_funscript", "dump_funscript", "Funscript",
    "analyze", "Signals",
    "derive_feel", "Feel",
    "generate_estim", "generate_single_axis",
    "load_chapters_file", "parse_chapters",
    "load_phrases", "feel_from_phrase",
    "load_bundle", "generate_from_bundle", "Bundle",
]
