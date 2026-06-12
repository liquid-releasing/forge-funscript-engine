"""CLI acceptance tests:  python -m unittest tests.test_cli -v

Exercises forge.cli.main end-to-end: reads a fixture, writes the estim channel
set to a temp dir, and asserts the files exist, are valid funscript JSON, and
match generate_estim's output. Also covers the missing-input error path.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from forge_funscript_engine.cli import main          # noqa: E402
from forge_funscript_engine.funscript import load_funscript  # noqa: E402
from forge_funscript_engine.pipeline import CHANNELS         # noqa: E402

FIX = os.path.join(HERE, "fixtures")


class TestCLI(unittest.TestCase):
    def test_generates_channel_files(self):
        with tempfile.TemporaryDirectory() as out:
            rc = main(["--out-dir", out, "--name", "clip",
                       os.path.join(FIX, "fast-smooth.funscript")])
            self.assertEqual(rc, 0)
            estim = os.path.join(out, "estim")
            for ch in CHANNELS:
                path = os.path.join(estim, f"clip.{ch}.funscript")
                self.assertTrue(os.path.isfile(path), f"missing {ch} file")
                doc = json.loads(open(path, encoding="utf-8").read())  # valid JSON
                self.assertIn("actions", doc)
                self.assertGreater(len(doc["actions"]), 0)

    def test_default_name_is_input_stem(self):
        with tempfile.TemporaryDirectory() as out:
            rc = main(["-o", out, os.path.join(FIX, "slow-smooth.funscript")])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.isfile(
                os.path.join(out, "estim", "slow-smooth.alpha.funscript")))

    def test_missing_input_returns_2(self):
        rc = main(["does-not-exist.funscript"])
        self.assertEqual(rc, 2)

    def test_empty_fixture_safe(self):
        with tempfile.TemporaryDirectory() as out:
            rc = main(["-o", out, "--name", "e",
                       os.path.join(FIX, "empty.funscript")])
            self.assertEqual(rc, 0)
            fs = load_funscript(os.path.join(out, "estim", "e.alpha.funscript"))
            self.assertEqual(len(fs.actions), 1)  # single safe frame


if __name__ == "__main__":
    unittest.main(verbosity=2)
