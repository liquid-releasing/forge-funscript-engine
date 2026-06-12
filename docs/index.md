# Forge Funscript Engine

Turn a **1-D stroke funscript** into **e-stim device channels** (restim `alpha` / `beta` /
`volume`) through one device-agnostic *intent* model — a clean-room, dependency-free
alternative to the channel-generation step in edger's funscript-tools. Implements the
Unified Forge build spec.

!!! note "Status — Phase 1"
    e-stim `alpha`/`beta`/`volume` from motion, with the safety envelope. The full e-stim
    channel set, single-axis strokers (Handy/Vacuglide), and the adjustment UI are Phase 2–3.
    See the [build spec](unified-forge.spec.md).

## The idea

Author (or reuse) **one** stroke motion file. The engine derives a small set of
device-agnostic **Feel** dials from the motion, then *forges* that single signal into the
channel set each device actually needs. Hardware-specificity lives in exactly one place;
everything above it is one honest signal.

```text
VOICING  ->  the continuous bed     -- Feel + Dynamics, derived from motion
MOMENTS  ->  punctual influences     -- local touch-ups layered on top
POLISH   ->  the per-device forge     -- conditions the one signal into N device files
```

## Install

```bash
pip install forge-funscript-engine    # once published
pip install -e .                       # runtime is pure stdlib, no dependencies
pip install -e ".[docs]"               # to build this site
```

## CLI

```bash
forge-funscript-engine input.funscript -o out/ --name myclip
# -> out/estim/myclip.{alpha,beta,volume}.funscript
```

## Library

```python
from forge_funscript_engine import generate_estim, analyze, derive_feel

channels = generate_estim(actions)   # {"alpha": Funscript, "beta": …, "volume": …}
feel     = derive_feel(analyze(actions))
```

Pass `out_dir=...` to also write the channel files; omit it to keep everything in memory for
embedding in your own app. Every channel is safety-clamped to the restim range as the final
stage ([spec §9](unified-forge.spec.md)).

## Where to go next

- **[Build spec](unified-forge.spec.md)** — the document of record: the intent model (§2),
  Feel-from-motion derivation (§3), e-stim channels (§7), safety (§9), phases (§11).
- **Background** — the rationale docs the spec consolidates.
