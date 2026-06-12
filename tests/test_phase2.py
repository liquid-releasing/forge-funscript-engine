"""Phase-2 acceptance suite:  python -m unittest tests.test_phase2 -v

Covers spec section 11 Phase 2:
  - full e-stim channel set + variants, all in range (sections 7.1/7.3/7.4)
  - lift styles: Wildness widens the angular sweep (section 7.2)
  - chapter seam stitching: per-seam delta within the safety envelope (section 7.5)
  - single-axis profiles (Handy/Vacuglide): conditioned position track (section 8)
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from forge_funscript_engine import (                       # noqa: E402
    load_funscript, generate_estim, generate_single_axis)
from forge_funscript_engine.estim import FULL, MINIMAL, RISE_TIME  # noqa: E402
from forge_funscript_engine.safety import (                # noqa: E402
    channel_ceiling, SEAM_MAX_DELTA)
from forge_funscript_engine.chapters import (              # noqa: E402
    stitch, within_seam_envelope)
from forge_funscript_engine.singleaxis import norm_knobs   # noqa: E402

FIX = os.path.join(HERE, "fixtures")
ALL_FIXTURES = ["slow-smooth", "fast-smooth", "shallow-fast", "sharp-snap",
                "irregular", "build-ramp", "empty", "single-point", "flat",
                "huge-gap", "monotonic", "max-speed"]


def _actions(name):
    return load_funscript(os.path.join(FIX, name + ".funscript")).actions


def _dec(pos):
    return pos / 100.0


class TestFullChannelSet(unittest.TestCase):
    def test_full_set_present(self):
        ch = generate_estim(_actions("fast-smooth"))
        self.assertEqual(set(ch.keys()), set(FULL))     # 9 channels, no rise_time

    def test_minimal_set(self):
        ch = generate_estim(_actions("fast-smooth"), full=False)
        self.assertEqual(set(ch.keys()), set(MINIMAL))  # alpha/beta/volume only

    def test_rise_time_opt_in(self):
        off = generate_estim(_actions("fast-smooth"))
        on = generate_estim(_actions("fast-smooth"), enable_rise_time=True)
        self.assertNotIn(RISE_TIME, off)
        self.assertIn(RISE_TIME, on)

    def test_every_channel_in_range_all_fixtures(self):
        for name in ALL_FIXTURES:
            ch = generate_estim(_actions(name), enable_rise_time=True)
            for cname, fs in ch.items():
                ceiling = channel_ceiling(cname)
                last_at = -1
                for act in fs.actions:
                    self.assertIsInstance(act["at"], int)
                    self.assertIsInstance(act["pos"], int)
                    self.assertGreater(act["at"], last_at,
                                       f"{name}.{cname} at increasing")
                    last_at = act["at"]
                    self.assertGreaterEqual(act["pos"], 0)
                    self.assertLessEqual(act["pos"], 100)
                    self.assertLessEqual(_dec(act["pos"]), ceiling + 1e-9,
                                         f"{name}.{cname} <= {ceiling}")

    def test_volume_variants_under_ceiling(self):
        ch = generate_estim(_actions("fast-smooth"))
        for cname in ("volume", "volume-prostate", "volume-stereostim"):
            for act in ch[cname].actions:
                self.assertLessEqual(_dec(act["pos"]), 0.7 + 1e-9)


class TestLiftStyles(unittest.TestCase):
    """Section 7.2: Wildness widens theta's span past the semicircle, so beta dips
    below the 0.5 axis (sin < 0) — which never happens for the low-Wildness baseline."""

    def _beta_min(self, name):
        ch = generate_estim(_actions(name), full=False)
        return min(_dec(a["pos"]) for a in ch["beta"].actions)

    def test_wildness_widens_sweep(self):
        # slow-smooth: Wildness 0 -> theta in [0,pi] -> beta >= 0.5 (pos >= 50)
        self.assertGreaterEqual(self._beta_min("slow-smooth"), 0.5 - 1e-9)
        # irregular: high Wildness -> theta exceeds pi -> beta dips below 0.5
        self.assertLess(self._beta_min("irregular"), 0.5)


class TestSeamStitching(unittest.TestCase):
    def test_stitch_bounds_seam_delta(self):
        series = [0.0] * 20 + [1.0] * 20          # hard jump at index 20
        boundaries = [20]
        self.assertFalse(within_seam_envelope(series, boundaries))
        stitched = stitch(series, boundaries)
        self.assertTrue(within_seam_envelope(stitched, boundaries),
                        "stitched seam delta must be within the safety envelope")
        self.assertLessEqual(abs(stitched[20] - stitched[19]), SEAM_MAX_DELTA + 1e-9)

    def test_chaptered_generation_valid(self):
        ch = generate_estim(_actions("build-ramp"), chapters=3)
        self.assertEqual(set(ch.keys()), set(FULL))
        self.assertGreater(len(ch["alpha"].actions), 1)
        for fs in ch.values():
            for act in fs.actions:
                self.assertTrue(0 <= act["pos"] <= 100)


class TestSingleAxis(unittest.TestCase):
    def test_handy_position_valid(self):
        ch = generate_single_axis(_actions("fast-smooth"), device="handy")
        self.assertEqual(list(ch.keys()), ["position"])
        acts = ch["position"].actions
        self.assertGreater(len(acts), 1)
        for a in acts:
            self.assertTrue(0 <= a["pos"] <= 100)

    def test_rate_clamp_respected(self):
        ch = generate_single_axis(_actions("max-speed"), device="handy")
        prim = norm_knobs("handy", None)
        cap_pos = prim["rate"] * 100 + 1.5      # +rounding slack
        acts = ch["position"].actions
        for i in range(1, len(acts)):
            self.assertLessEqual(abs(acts[i]["pos"] - acts[i - 1]["pos"]), cap_pos)

    def test_vacuglide_runs(self):
        ch = generate_single_axis(_actions("slow-smooth"), device="vacuglide")
        self.assertGreater(len(ch["position"].actions), 1)

    def test_empty_safe(self):
        ch = generate_single_axis(_actions("empty"), device="handy")
        self.assertEqual(len(ch["position"].actions), 1)

    def test_writes_device_folder(self):
        with tempfile.TemporaryDirectory() as out:
            generate_single_axis(_actions("fast-smooth"), device="handy",
                                 name="clip", out_dir=out)
            path = os.path.join(out, "handy", "clip.funscript")
            self.assertTrue(os.path.isfile(path))
            json.loads(open(path, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
