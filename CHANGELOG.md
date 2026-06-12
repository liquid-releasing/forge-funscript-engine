# Changelog

All notable changes to the Forge Funscript Engine. Pure standard library, zero runtime
dependencies.

## [0.2.0] — 2026-06-11 — Read/render core

Point at a loose funscript **or** a full `.forge` bundle and get safe, restim-compatible
device output.

### Added
- **Phase 1** — motion → 6-dial Feel (§3) → e-stim `alpha`/`beta`/`volume` via the real
  1D→2D lift (§7.2), safety-clamped (§9). Constant-free golden test suite.
- **Phase 2** — full e-stim channel superset (`alpha-prostate`, `frequency`,
  `pulse_frequency`, `pulse_width`, `volume-prostate`, `volume-stereostim`;
  `pulse_rise_time` opt-in), Wildness-driven lift styles, chapter-aware generation with
  seam stitching, single-axis stroker profiles (Handy, Vacuglide).
- **Chapter sidecar input** — tolerant parser (`load_chapters_file` / `parse_chapters`),
  verified against the real `.forge` `at_ms`/`end_ms` schema.
- **Assess adapter** — consume the host's `phrases.json` (`bpm`→Pace, `span`→Depth).
- **Manifest bundle loader** — read `manifest.ffmeta` (ffmeta/v1), resolve artifacts,
  `load_bundle` / `generate_from_bundle`; CLI `--bundle <manifest|dir>`.
- **CLI** — `--device`, `--channels`, `--chapters`/`--chapters-file`, `--bundle`,
  `--no-carrier`.
- **Docs** — build spec, container & player architecture, mkdocs site with Mermaid.

### Safety
- Carrier-frequency floor (`MIN_CARRIER_HZ`, default 500) — never emit an unsafe low
  carrier (restim e-stim-safety: IEC 60601-2-10 + charge-per-phase, ~446–755 Hz minimum).
- `max_volume` ≤ 0.7 ceiling, per-step rate cap, NaN/Inf-safe throughout.

### Interoperability
- restim 1D→2D parity verified — byte-compatible funscript encoding (MIT, reusable).
- §7.4 channel ranges reconciled to edger's verified `normalization`.
- Licensing recorded: restim MIT (read + reuse w/ attribution), edger unlicensed
  (facts only), OpenFunscripter unconfirmed (facts only).

### Notes
- 44 tests (`python -m unittest discover -s tests -p "test_*.py" -b`).
- Math is pure stdlib (`math` + hand-rolled RMS/std/percentile/autocorrelation) — no numpy.

## [0.1.0] — Phase 1 scaffold

Initial engine: motion → e-stim alpha/beta/volume with the golden test suite.
