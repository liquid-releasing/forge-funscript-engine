# Unified Forge — Phase-1 golden test suite

Test fixtures + reference goldens for the Phase-1 engine ([unified-forge.spec.md §11](../docs/unified-forge.spec.md)):
**parse → derive Feel from motion (§3) → alpha/beta/volume via the real lift (§7.2) → safety clamp (§9) → valid funscript.**

```
engine-tests/
  make_fixtures.py   # generates fixtures/ + goldens.json; also the reference §3 analyzer
  fixtures/          # 12 input .funscript files (6 behavioral, 6 edge/fuzz)
  goldens.json       # constant-free reference signals + relational invariants
  README.md          # this file
```

Regenerate: `python make_fixtures.py` (deterministic — no RNG, no clock).

## Why goldens are *relational*, not absolute

Dial **values** depend on the §3.2 calibration constants (`V_ref`, `F_ref`, `CV_ref`, `CF_max`…), which will be tuned (spec §12). Snapshotting dial values would make every calibration tweak a test failure. So the suite asserts:

- **Constant-free reference signals** as exact goldens (`f_hz`, `depth`, `cv_d`, `cv_a`, `crest`, `v_rms`, `autocorr`) — these depend only on the formulas, not the constants. `goldens.json` is the source of truth; the production analyzer must reproduce them within tolerance.
- **Relational invariants** between fixtures (e.g. `Pace(fast) > Pace(slow)`) — true for *any* sane constants. These are the dial-level acceptance tests.
- **Output validity** on every fixture — hard range/format/safety guarantees.

## Fixture catalog

### Behavioral (relational goldens)

| Fixture | Shape | Primarily tests | Key reference signal |
|---|---|---|---|
| `slow-smooth` | 0.5 Hz full-depth triangle | low Pace, smooth, focused baseline | `f=0.50, crest=1.00, autocorr=0.83` |
| `fast-smooth` | ~3 Hz full-depth triangle | high Pace, high energy | `f=2.99, v_rms=5.75` |
| `shallow-fast` | ~3 Hz, amplitude 40–60 | high Pace + **low Depth** (depth decoupled from pace) | `depth=0.20` |
| `sharp-snap` | dwell 400 ms + 40 ms snaps | **high Sharpness** (crest), decoupled from pace/depth | `crest=3.42, depth=1.00` |
| `irregular` | varied intervals & amplitudes | **high Wildness**, low Focus | `cv_d=0.58, cv_a=0.23, autocorr=−0.10` |
| `build-ramp` | triangle, amplitude grows over window | Intensity rising across the window; Passage/ramp | `cv_a=0.47` (amplitude trend) |

### Edge / fuzz (robustness goldens — must not crash, NaN, or go out of range)

| Fixture | Condition | Expected |
|---|---|---|
| `empty` | `actions: []` | all signals 0; engine emits empty-or-single-safe-frame output |
| `single-point` | one action | all motion signals 0; defaults |
| `flat` | constant pos | `f=0, depth=0, v_rms=0`; volume at floor only |
| `huge-gap` | two actions 1 h apart | interpolates; `f=0`, no divide-by-zero |
| `monotonic` | strictly increasing, no reversals | `f≈0`, no negative frequency, no NaN |
| `max-speed` | 0↔100 every 1 ms | clamps hold; no out-of-range pos (note: 20 ms resample aliases sub-frame detail — robustness fixture, not a signal-accuracy fixture) |

## Assertions the suite runs against the production engine

**A. Analyzer signals (§3.1).** For each behavioral fixture, production `analyze()` reproduces `goldens.json` signals within tolerance: `f_hz` ±5 %, `depth` ±0.02, `crest`/`v_rms` ±5 %, `cv_*`/`autocorr` ±0.05.

**B. Relational invariants (§3.2)** — verified true in the reference (`invariants_hold_in_reference: true`):
```
f_hz(fast-smooth)     > f_hz(slow-smooth)        # Pace
depth(fast-smooth)    > depth(shallow-fast)      # Depth (decoupled from Pace)
crest(sharp-snap)     > crest(slow-smooth)       # Sharpness (decoupled)
cv_a(irregular)       > cv_a(slow-smooth)        # Wildness (amplitude)
cv_d(irregular)       > cv_d(slow-smooth)        # Wildness (timing)
autocorr(slow-smooth) > autocorr(irregular)      # Focus
v_rms(fast-smooth)    > v_rms(slow-smooth)       # Intensity (motion energy)
```

**C. Output validity** — for **every** fixture, the generated `alpha/beta/volume` funscripts must satisfy:
- valid JSON; `actions` `at` strictly increasing integers ≥ 0; `pos` integer ∈ `[0, 100]`.
- decoded channel values within restim range: `alpha, beta, volume ∈ [0, 0.998]` (§7.4).
- `volume` (and variants, Phase 2) ≤ the `max_volume` ceiling (default 0.7, §9).
- per-step `volume` delta ≤ the configured `rate` cap (§9 smooth-ramp requirement).
- **no NaN / Inf** anywhere; edge fixtures produce valid output, never an exception.

**D. Disc-path sanity (the spec §11 Phase-1 verify item).** alpha/beta trace a sane disc path — radius grows with speed:
```
mean(|alpha−0.5|, |beta−0.5|)  for fast-smooth  >  for slow-smooth
```
(faster motion → larger radius → toward the electrode edge, per §7.2).

## Status

The reference analyzer + fixtures + goldens are **runnable now**. Assertion sets **A, B** run against the reference (`make_fixtures.py` prints the invariant check); **C, D** assert against the production `alpha/beta/volume` output. The production `analyze()` ([src/forge_funscript_engine/analyze.py](../src/forge_funscript_engine/analyze.py)) reproduces `goldens.json` within tolerance.

## Full suite (v0.2.0 — 44 tests)

Run everything (pure stdlib, no install needed):

```bash
python -m unittest discover -s tests -p "test_*.py" -b
```

| File | Covers |
|---|---|
| `test_phase1.py` | sets A–D — analyzer signals vs goldens, relational invariants, output validity, disc-path sanity |
| `test_phase2.py` | full e-stim channel set, lift styles, seam stitching, single-axis profiles, chapter sidecar parsing, **carrier-frequency safety floor** |
| `test_assess.py` | host `phrases.json` → Feel overlay (bpm→Pace, span→Depth) |
| `test_bundle.py` | `manifest.ffmeta` `.forge` bundle loader → motion + chapters → generation |
| `test_cli.py` | CLI end-to-end (channel files, default naming, error paths) |

Tests are `unittest.TestCase`, so `pytest` collects them too if you prefer it.
