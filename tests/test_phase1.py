"""Phase-1 acceptance suite (tests/README.md sets A-D).

Run from the repo root:  python -m unittest tests.test_phase1 -v

A. Production analyze() reproduces goldens.json base signals within tolerance.
B. Relational invariants hold (Pace(fast)>Pace(slow), etc.).
C. Every generated alpha/beta/volume funscript is valid + in range + safe.
D. Disc-path sanity: radius grows with speed (fast-smooth > slow-smooth).
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from forge_funscript_engine import load_funscript, analyze, generate_estim  # noqa: E402
from forge_funscript_engine.safety import CH_MAX, MAX_VOLUME, RATE_CAP       # noqa: E402

FIX = os.path.join(HERE, "fixtures")
with open(os.path.join(HERE, "goldens.json"), encoding="utf-8") as _f:
    GOLDENS = json.load(_f)
FIXTURE_NAMES = list(GOLDENS["fixtures"].keys())


def _actions(name):
    return load_funscript(os.path.join(FIX, name + ".funscript")).actions


def _sig(name):
    return analyze(_actions(name))


def _decode(pos):
    return pos / 100.0


class TestA_AnalyzerSignals(unittest.TestCase):
    """Production analyzer reproduces the reference signals (tests/README set A)."""

    BEHAVIORAL = ["slow-smooth", "fast-smooth", "shallow-fast",
                  "sharp-snap", "irregular", "build-ramp"]

    def test_signals_match_goldens(self):
        for name in self.BEHAVIORAL:
            g = GOLDENS["fixtures"][name]["signals"]
            s = _sig(name)
            with self.subTest(fixture=name):
                self._close(s.f_hz, g["f_hz"], rel=0.05, msg=f"{name} f_hz")
                self.assertLessEqual(abs(s.depth - g["depth"]), 0.02, f"{name} depth")
                self._close(s.crest, g["crest"], rel=0.05, msg=f"{name} crest")
                self._close(s.v_rms, g["v_rms"], rel=0.05, msg=f"{name} v_rms")
                self.assertLessEqual(abs(s.cv_d - g["cv_d"]), 0.05, f"{name} cv_d")
                self.assertLessEqual(abs(s.cv_a - g["cv_a"]), 0.05, f"{name} cv_a")
                self.assertLessEqual(abs(s.autocorr - g["autocorr"]), 0.05,
                                     f"{name} autocorr")

    def _close(self, got, exp, rel, msg):
        tol = abs(exp) * rel + 1e-9
        self.assertLessEqual(abs(got - exp), tol,
                             f"{msg}: got {got}, expected {exp} (+/-{rel:.0%})")


class TestB_Invariants(unittest.TestCase):
    """Relational invariants -- true for any sane calibration (tests/README set B)."""

    def test_invariants(self):
        s = {n: _sig(n) for n in
             ["slow-smooth", "fast-smooth", "shallow-fast", "sharp-snap", "irregular"]}
        self.assertGreater(s["fast-smooth"].f_hz, s["slow-smooth"].f_hz, "Pace")
        self.assertGreater(s["fast-smooth"].depth, s["shallow-fast"].depth, "Depth")
        self.assertGreater(s["sharp-snap"].crest, s["slow-smooth"].crest, "Sharpness")
        self.assertGreater(s["irregular"].cv_a, s["slow-smooth"].cv_a, "Wildness/amp")
        self.assertGreater(s["irregular"].cv_d, s["slow-smooth"].cv_d, "Wildness/dur")
        self.assertGreater(s["slow-smooth"].autocorr, s["irregular"].autocorr, "Focus")
        self.assertGreater(s["fast-smooth"].v_rms, s["slow-smooth"].v_rms, "Intensity")


class TestC_OutputValidity(unittest.TestCase):
    """Every channel of every fixture is valid, in range, NaN-free, safe (set C)."""

    def test_all_fixtures(self):
        for name in FIXTURE_NAMES:
            channels = generate_estim(_actions(name), name=name)
            for ch, fs in channels.items():
                with self.subTest(fixture=name, channel=ch):
                    self._valid_channel(name, ch, fs)

    def _valid_channel(self, name, ch, fs):
        ceiling = MAX_VOLUME if ch == "volume" else CH_MAX
        last_at = -1
        prev_dec = None
        for act in fs.actions:
            at, pos = act["at"], act["pos"]
            # JSON/integer/order
            self.assertIsInstance(at, int, f"{name}.{ch} at must be int")
            self.assertIsInstance(pos, int, f"{name}.{ch} pos must be int")
            self.assertGreaterEqual(at, 0, f"{name}.{ch} at >= 0")
            self.assertGreater(at, last_at, f"{name}.{ch} at strictly increasing")
            last_at = at
            # range
            self.assertGreaterEqual(pos, 0)
            self.assertLessEqual(pos, 100)
            dec = _decode(pos)
            self.assertLessEqual(dec, ceiling + 1e-9,
                                 f"{name}.{ch} decoded {dec} <= {ceiling}")
            self.assertGreaterEqual(dec, 0.0)
            # no NaN/Inf is implicit: ints decode finite. Rate cap on volume:
            if ch == "volume" and prev_dec is not None:
                self.assertLessEqual(abs(dec - prev_dec), RATE_CAP + 1e-9,
                                     f"{name}.volume per-step delta <= {RATE_CAP}")
            prev_dec = dec

    def test_json_serializable(self):
        # round-trips through JSON without error (valid JSON guarantee)
        for name in FIXTURE_NAMES:
            channels = generate_estim(_actions(name), name=name)
            for ch, fs in channels.items():
                json.dumps({"actions": fs.actions})


class TestD_DiscPathSanity(unittest.TestCase):
    """alpha/beta trace a sane disc path: radius grows with speed (set D)."""

    def _mean_radius(self, name):
        ch = generate_estim(_actions(name), name=name)
        a = [abs(_decode(x["pos"]) - 0.5) for x in ch["alpha"].actions]
        b = [abs(_decode(x["pos"]) - 0.5) for x in ch["beta"].actions]
        vals = a + b
        return sum(vals) / len(vals)

    def test_fast_radius_exceeds_slow(self):
        self.assertGreater(self._mean_radius("fast-smooth"),
                           self._mean_radius("slow-smooth"),
                           "faster motion -> larger disc radius (spec section 7.2)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
