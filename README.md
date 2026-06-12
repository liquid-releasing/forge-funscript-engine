# Forge Funscript Engine

Turn a **1-D stroke funscript** into **e-stim device channels** (restim `alpha` / `beta` /
`volume`) through one device-agnostic *intent* model — a clean-room, dependency-free
alternative to the channel-generation step in edger's funscript-tools. Implements the
Unified Forge build spec ([docs/unified-forge.spec.md](docs/unified-forge.spec.md)).

You author (or already have) a single stroke motion file. The engine derives a small set of
device-agnostic **Feel** dials from the motion, then *forges* that one signal into the
channel set a device actually needs. Device-specificity lives in one place; everything above
it is one honest signal.

> **Status:** Phase 1 — e-stim `alpha`/`beta`/`volume` from motion, with the safety envelope.
> Full e-stim channel set, single-axis strokers (Handy/Vacuglide), and the adjustment UI are
> Phase 2–3. See [docs/unified-forge.spec.md](docs/unified-forge.spec.md).

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
forge-funscript-engine input.funscript -o out/ --name myclip
# -> out/estim/myclip.alpha.funscript
#    out/estim/myclip.beta.funscript
#    out/estim/myclip.volume.funscript
```

| Flag | Meaning |
|---|---|
| `input` | input `.funscript` (1-D stroke motion) |
| `-o, --out-dir` | output dir; channels written to `<out-dir>/estim/` (default `.`) |
| `--name` | output basename (default: input filename stem) |
| `--ramp` | Passage ramp slice `R` in `[0,1]` (default: derived from clip length) |

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
channels = generate_estim(actions)          # {"alpha": Funscript, "beta": …, "volume": …}
alpha = channels["alpha"].actions           # [{"at": ms, "pos": 0..100}, …]
```

Every output is hard-clamped to the restim range (`alpha/beta/volume` decode to `[0, 0.998]`,
`volume` under the `≤ 0.7` ceiling) and the volume envelope is rate-limited — the safety
envelope is applied as the final stage, always (see [spec §9](docs/unified-forge.spec.md)).

### Public API

| Symbol | Purpose |
|---|---|
| `generate_estim(actions, ramp=None, name="out", out_dir=None)` | motion → `{channel: Funscript}`; writes `<out_dir>/estim/` if `out_dir` given |
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
