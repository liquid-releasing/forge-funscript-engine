"""Unified Forge engine.

Phase 1: parse a 1-D stroke funscript -> derive the 6-dial Feel from motion
(spec section 3) -> synthesize the e-stim alpha/beta/volume channels via the
real 1-D->2-D lift (section 7.2) -> safety-clamp (section 9) -> valid funscript.

See docs/unified-forge.spec.md (section 11, Phase 1).
"""
from .funscript import load_funscript, dump_funscript, Funscript
from .analyze import analyze, Signals
from .feel import derive_feel, Feel
from .pipeline import generate_estim

__all__ = [
    "load_funscript", "dump_funscript", "Funscript",
    "analyze", "Signals",
    "derive_feel", "Feel",
    "generate_estim",
]
