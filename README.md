# Forge Funscript Engine

Turn a **1-D stroke funscript** into **e-stim device channels** (restim `alpha` / `beta` /
`volume`) through one device-agnostic *intent* model — a clean-room, dependency-free
alternative to the channel-generation step in edger's funscript-tools. Implements the
Unified Forge build spec ([docs/unified-forge.spec.md](docs/unified-forge.spec.md)).

You author (or already have) a single stroke motion file. The engine derives a small set of
device-agnostic **Feel** dials from the motion, then *forges* that one signal into the
channel set a device actually needs. Device-specificity lives in one place; everything above
it is one honest signal.

> **Status:** Phase 2 — the full e-stim channel set (alpha/beta/volume + variants,
> frequency, pulse_*), Wildness-driven lift styles, chapter-aware generation with seam
> stitching, and the single-axis strokers (Handy/Vacuglide), all under the safety envelope.
> The adjustment UI and Moments authoring are Phase 3. See
> [docs/unified-forge.spec.md](docs/unified-forge.spec.md).

## Install

```bash
pip install forge-funscript-engine     # once published
pip install -e .                        # from a checkout
# optional extras:
pip install -e ".[dev]"                 # pytest
pip install -e ".[docs]"                # mkdocs-material
```

Pure standard library at runtime — **no dependencies**. The distribution and CLI are
`forge-funscript-engine`; the Python import package is `forge_funscript_engine` (underscores,
since import names can't contain hyphens).

## Use it as a CLI

```bash
# e-stim: full channel superset (default) into out/estim/
forge-funscript-engine input.funscript -o out/ --name myclip
#   myclip.{alpha,alpha-prostate,beta,frequency,pulse_frequency,
#           pulse_width,volume,volume-prostate,volume-stereostim}.funscript

# single-axis strokers (one conditioned position track)
forge-funscript-engine input.funscript -o out/ --device handy      # -> out/handy/myclip.funscript
forge-funscript-engine input.funscript -o out/ --device vacuglide  # -> out/vacuglide/myclip.funscript

# chapter-aware generation with seam stitching (real boundaries from a sidecar),
# or N equal splits, or just the minimal a/b/v set
forge-funscript-engine input.funscript -o out/ --chapters-file input.chapters.json
forge-funscript-engine input.funscript -o out/ --chapters 4
forge-funscript-engine input.funscript -o out/ --channels minimal
```

| Flag | Meaning |
|---|---|
| `input` | input `.funscript` (1-D stroke motion) |
| `-o, --out-dir` | output dir (default `.`); channels go in `<out-dir>/<device>/` |
| `--name` | output basename (default: input filename stem) |
| `--device` | `estim` (default), `handy`, or `vacuglide` |
| `--channels` | e-stim set: `full` (default superset) or `minimal` (alpha/beta/volume) |
| `--chapters-file` | chapter sidecar JSON (real boundaries); overrides `--chapters` |
| `--chapters` | split into N equal chapters with seam stitching (testing convenience) |
| `--ramp` | Passage ramp slice `R` in `[0,1]` (default: derived from clip length) |

### Chapters

Chapters are the **generation unit** (per-chapter Feel, stitched at the seams). The
engine *consumes* boundaries — creating them (audio/video analysis) is the host's job
(spec §10). Four ways to supply them, in order of precedence:

1. **Sidecar JSON** — `--chapters-file my.chapters.json`, or `load_chapters_file(path)`.
   Tolerant of common schemas (top-level array or `{"chapters":[…]}`; times as ms
   numbers or `HH:MM:SS.mmm`; aliased start/end/duration keys). See
   [examples/README.md](examples/README.md).
2. **Explicit tuples** (library) — `generate_estim(actions, chapters=[(start_ms, end_ms), …])`.
3. **Equal split** — `--chapters N` / `chapters=N` (a testing convenience, not real scenes).
4. **None** (default) — one chapter spanning the whole clip.

Equivalent: `python -m forge_funscript_engine input.funscript -o out/`.

## Use it as a library

Embed it in your own app — `generate_estim` returns in-memory `Funscript` objects when you
omit `out_dir`, so nothing touches disk unless you want it to:

```python
from forge_funscript_engine import generate_estim, analyze, derive_feel, load_funscript

actions = load_funscript("input.funscript").actions

# 1) Inspect the derived intent (the 6 device-agnostic Feel dials)
sig  = analyze(actions)
feel = derive_feel(sig)
print(feel)   # Feel(intensity=…, pace=…, wildness=…, sharpness=…, depth=…, focus=…)

# 2) Forge the e-stim channels (in-memory; pass out_dir=... to also write files)
channels = generate_estim(actions)              # full superset, {"alpha": Funscript, …}
channels = generate_estim(actions, full=False)  # minimal {"alpha","beta","volume"}
channels = generate_estim(actions, chapters=4)  # per-chapter Feel + seam stitching
alpha = channels["alpha"].actions               # [{"at": ms, "pos": 0..100}, …]

# 3) Or condition for a single-axis stroker (one position track)
from forge_funscript_engine import generate_single_axis
handy = generate_single_axis(actions, device="handy")["position"]
```

Every output is hard-clamped to the restim range (`alpha/beta/volume` decode to `[0, 0.998]`,
`volume` under the `≤ 0.7` ceiling) and the volume envelope is rate-limited — the safety
envelope is applied as the final stage, always (see [spec §9](docs/unified-forge.spec.md)).

### Public API

| Symbol | Purpose |
|---|---|
| `generate_estim(actions, ramp=None, name="out", out_dir=None, chapters=None, full=True, enable_rise_time=False)` | motion → e-stim `{channel: Funscript}`; writes `<out_dir>/estim/` if `out_dir` given |
| `generate_single_axis(actions, device="handy", knobs=None, name="out", out_dir=None)` | motion → `{"position": Funscript}` for a stroker; writes `<out_dir>/<device>/` |
| `load_chapters_file(path, clip_end_ms=None)` / `parse_chapters(doc, …)` | chapter sidecar → `[(start_ms, end_ms), …]` for `generate_estim(chapters=…)` |
| `load_phrases(path)` / `feel_from_phrase(metrics, base)` | consume the host's `phrases.json` assess output → Feel (bpm→Pace, span→Depth) |
| `analyze(actions) -> Signals` | §3 motion analysis — the constant-free base signals |
| `derive_feel(signals, ramp=None) -> Feel` | §3.2 — the 6 Feel dials in `[0,1]` |
| `load_funscript(path)` / `dump_funscript(fs, path)` | funscript JSON I/O |
| `Funscript`, `Signals`, `Feel` | dataclasses |

## Testing

Zero-install, runs today (tests are `unittest.TestCase`, so `pytest` collects them too):

```bash
python -m unittest discover -s tests -p "test_*.py" -b
# or, if you installed the dev extra:
pytest
```

The suite asserts the production analyzer against `tests/goldens.json` (reference signals +
relational invariants) and validates every generated channel for range/format/safety. See
[tests/README.md](tests/README.md).

## Docs

The spec set lives in [docs/](docs/). Build the site locally:

```bash
mkdocs serve     # needs the [docs] extra
```

## Clean-room & license

edger477's repos are unlicensed (all rights reserved) and were read for **facts only**
(channel roles, parameter ranges, safety limits) — never code. restim's value ranges are an
interoperability contract. See [spec §1 / Sources](docs/unified-forge.spec.md).
