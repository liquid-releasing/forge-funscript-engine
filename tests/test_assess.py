"""Assess-adapter tests:  python -m unittest tests.test_assess -v

The host's phrases.json metrics overlay onto a motion-derived base Feel:
bpm -> Pace, span -> Depth (sections 3 / 10). Synthetic metrics only — the real
.forge sample bundles are gitignored, not part of the repo.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from forge_funscript_engine import Feel, feel_from_phrase     # noqa: E402
from forge_funscript_engine.assess import BPM_REF             # noqa: E402

BASE = Feel(intensity=0.4, pace=0.1, wildness=0.2, sharpness=0.3, depth=0.9, focus=0.7)


class TestAssessAdapter(unittest.TestCase):
    def test_bpm_overrides_pace(self):
        f = feel_from_phrase({"bpm": BPM_REF}, BASE)   # saturating bpm
        self.assertAlmostEqual(f.pace, 1.0, places=6)

    def test_span_overrides_depth(self):
        f = feel_from_phrase({"span": 80}, BASE)        # 0-100 range
        self.assertAlmostEqual(f.depth, 0.8, places=6)

    def test_other_dials_from_base(self):
        f = feel_from_phrase({"bpm": 60, "span": 50}, BASE)
        self.assertEqual(f.intensity, BASE.intensity)
        self.assertEqual(f.wildness, BASE.wildness)
        self.assertEqual(f.sharpness, BASE.sharpness)
        self.assertEqual(f.focus, BASE.focus)

    def test_missing_metrics_keep_base(self):
        f = feel_from_phrase({}, BASE)
        self.assertEqual((f.pace, f.depth), (BASE.pace, BASE.depth))

    def test_clamps_to_unit_range(self):
        f = feel_from_phrase({"bpm": BPM_REF * 5, "span": 250}, BASE)
        self.assertEqual((f.pace, f.depth), (1.0, 1.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
