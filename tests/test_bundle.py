"""Bundle loader tests:  python -m unittest tests.test_bundle -v

Builds a synthetic .forge bundle (manifest.ffmeta + motion + chapters) in a temp
dir and checks the loader resolves it and drives generation. Synthetic only — the
real .forge sample bundles are gitignored.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from forge_funscript_engine import load_bundle, generate_from_bundle      # noqa: E402
from forge_funscript_engine.bundle import find_artifacts, MANIFEST_NAME   # noqa: E402
from forge_funscript_engine.estim import FULL                             # noqa: E402


def _triangle(period_ms, dur_ms):
    acts, t, up = [], 0, True
    while t <= dur_ms:
        acts.append({"at": t, "pos": 100 if up else 0})
        up = not up
        t += period_ms // 2
    return acts


def _make_bundle(d, with_chapters=True):
    """Write a minimal FunscriptForge-style bundle into dir `d`. Returns manifest path."""
    motion = {"version": "1.0", "actions": _triangle(400, 6000)}
    with open(os.path.join(d, "motion.funscript"), "w") as f:
        json.dump(motion, f)
    artifacts = [{"path": "motion.funscript", "kind": "funscript",
                  "role": "stroke", "axis": "L0"}]
    if with_chapters:
        with open(os.path.join(d, "chapters.json"), "w") as f:
            json.dump({"chapters": [{"at_ms": 0, "end_ms": 3000},
                                    {"at_ms": 3000, "end_ms": 6000}]}, f)
        artifacts.append({"path": "chapters.json", "kind": "sidecar",
                          "analysis": "chapters"})
    manifest = {"version": 1, "schema": "ffmeta/v1", "stem": "myclip",
                "created_with": "FunscriptForge", "duration_ms": 6000,
                "artifacts": artifacts, "stations": {}}
    mpath = os.path.join(d, MANIFEST_NAME)
    with open(mpath, "w") as f:
        json.dump(manifest, f)
    return mpath


class TestBundle(unittest.TestCase):
    def test_load_resolves_motion_and_chapters(self):
        with tempfile.TemporaryDirectory() as d:
            mpath = _make_bundle(d)
            b = load_bundle(mpath)
            self.assertEqual(b.stem, "myclip")
            self.assertEqual(b.duration_ms, 6000)
            self.assertGreater(len(b.motion_actions), 2)
            self.assertEqual(b.chapters, [(0, 3000), (3000, 6000)])

    def test_load_from_directory(self):
        with tempfile.TemporaryDirectory() as d:
            _make_bundle(d)
            b = load_bundle(d)            # point at the dir, not the manifest file
            self.assertEqual(b.stem, "myclip")

    def test_missing_chapters_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            mpath = _make_bundle(d, with_chapters=False)
            b = load_bundle(mpath)
            self.assertIsNone(b.chapters)

    def test_find_artifacts_filter(self):
        with tempfile.TemporaryDirectory() as d:
            mpath = _make_bundle(d)
            b = load_bundle(mpath)
            strokes = find_artifacts(b.manifest, kind="funscript", role="stroke")
            self.assertEqual(len(strokes), 1)

    def test_generate_from_bundle_writes_named_by_stem(self):
        with tempfile.TemporaryDirectory() as d:
            mpath = _make_bundle(d)
            out = os.path.join(d, "render")
            ch = generate_from_bundle(mpath, out_dir=out)
            self.assertEqual(set(ch.keys()), set(FULL))
            self.assertTrue(os.path.isfile(
                os.path.join(out, "estim", "myclip.alpha.funscript")))

    def test_no_funscript_raises(self):
        with tempfile.TemporaryDirectory() as d:
            mpath = os.path.join(d, MANIFEST_NAME)
            with open(mpath, "w") as f:
                json.dump({"schema": "ffmeta/v1", "artifacts": []}, f)
            with self.assertRaises(ValueError):
                load_bundle(mpath)


if __name__ == "__main__":
    unittest.main(verbosity=2)
