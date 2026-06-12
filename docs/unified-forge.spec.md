# Unified Forge — Multi-Device Generation Build Spec

**Status:** Draft v0.1 (buildable consolidation)
**Supersedes:** [funscript.spec.md](background/funscript.spec.md) (e-stim generator), [funscriptforge.spec.md](background/funscriptforge.spec.md) (host), and the deferred direction in [unified-haptics-direction.md](background/unified-haptics-direction.md). Those three remain as **background/rationale**; this is the document we build against.
**Prototype of record:** [`prototype/`](../prototype/) (`Unified Forge.html`, `scripts/forge-engine.js`) — the UI artifact that resolved the unified model. This spec wires that model to motion-derived generation and the real safety envelope.

> **Clean-room / licensing.** **restim (diglet48/restim) is MIT** — we may read *and reuse* its code with attribution; it is the interoperability reference for the e-stim channel contract and the 1D→2D encoding. **edger477's repos are unlicensed** (= all rights reserved): read for *facts* only (channel roles, parameter ranges, safety limits), never copy code; their generated *output* is usable as a calibration reference. **OpenFunscripter's license is unconfirmed** — facts-only until verified; a deeper OFS integration is a deferred roadmap item. Your **liquid-releasing CLI** contribution is yours to reuse. See [funscript.spec.md §2](background/funscript.spec.md).

---

## 1. What this spec defines

One engine that turns a **single input funscript** (1-D stroke motion) into device output for **many device families**, via **one device-agnostic intent signal**. Device-specificity is quarantined to a final **Polish** step.

The whole system is three layers over **one shared model**:

```
VOICING  →  the continuous bed     — Feel + Dynamics, derived from motion, user-adjustable
MOMENTS  →  punctual influences     — local touch-ups layered on top
POLISH   →  the per-device forge     — conditions the one signal into N device files
```

Voicing + Moments produce **one signal**. Polish is the **only** place hardware shape enters.

**First build covers, concretely:**
- **E-stim 3-phase** (restim) — the full channel set (§7), with the safety envelope (§9).
- **Single-axis strokers** — Handy and Vacuglide (§8).

**Deferred to future profiles** (architecture supports them; not built first): OSR2/SR6 multi-axis, Lovense, bHaptics, shaker. They slot in as profiles (§6) with no engine changes.

---

## 2. The unified intent model

This is the deliverable the original request asked for: *"a new unified set of values used when we create the scripts during polish or export."* Small, device-agnostic, the same at every time-scale.

### 2.1 Feel — the character of the energy (6 dials, all 0..1)

| Dial | Meaning | Realized as (examples) |
|---|---|---|
| **Intensity** | how strong | e-stim volume; stroker stroke energy; vibe amplitude |
| **Pace** | how fast (buzz = pace cranked up) | e-stim pulse_frequency / carrier; stroke speed; vibration rate |
| **Wildness** | how unpredictable / textured | lift-style randomness + fuzz; stroke variation; pattern jitter |
| **Sharpness** | attack — smooth swell vs. hard edge | pulse attack; stroke aggressiveness |
| **Depth** | how much of the full travel is used | alpha/beta radius range; stroke window |
| **Focus** | tight tracking of the source spine ↔ loose embellishment | smoothing / tracking tightness |

> **Open: a possible 7th dial.** Candidates discussed: *Regularity/Groove* (lock to a beat grid) and *Bias/Direction* (where in the stroke the energy concentrates). Not committed — the model leaves room (§11). Build against the six; add only if authoring against them surfaces a real gap.

**Twist, vibrate, pulse, stroke are NOT dials.** They are *consequences* of Feel + the target device, decided in Polish. The user authors "wild and building"; Polish decides where that energy goes.

### 2.2 The same model at four time-scales

All four are *influences on one signal*; they compose into a single per-time intensity+feel track. That track is what Polish renders. **Each maps to an existing FunscriptForge concept**, now unified:

| Time-scale | Unified name | = existing concept | Authoring |
|---|---|---|---|
| Scene (minutes) | **Passage / Dynamics** | cross-chapter ramp ([funscriptforge.spec.md §3A.2](background/funscriptforge.spec.md)) | `build / fall / swell / hold` spans with lo/hi over a time range |
| Chapter (3–5 min) | **Feel** | tone + e-stim character ([funscriptforge.spec.md §3](background/funscriptforge.spec.md)) | the 6 dials, **per chapter** |
| Phrase | **Pattern** | phrase/pattern/stanza transforms ([funscriptforge.spec.md §2](background/funscriptforge.spec.md)) | per-phrase Feel adjustments |
| Beat | **Moment** | events ([funscriptforge.spec.md §3A.3](background/funscriptforge.spec.md)) | punctual, windowed influences |

**Chapter is the generation unit** (3–5 min). Phrases/patterns/stanzas are *editing lenses*; chapters are where Feel and device generation are anchored. This preserves [funscript.spec.md §6](background/funscript.spec.md)'s per-chapter generation + seam stitching.

### 2.3 Moments — punctual influences

A Moment is `{ typeId, at, dur, amount }`. Each type decompiles transparently into Feel-ops and declares a **combine mode**:

| Type | Combine | Shape | Effect |
|---|---|---|---|
| Hold | `add` | hold | freeze pace, hold intensity, fine buzz so it doesn't read dead |
| Hit | `add` | hit | fast-attack intensity spike, sharpness → max, ~200 ms decay |
| Swell | `add` | swell | intensity rises then falls (sine hump), pace eases |
| Flutter | `add` | flutter | rapid wildness burst, pace doubles briefly, tapers |
| Tease | `replace` | dip | gate intensity toward the floor, pace stutters, release (the edge) |

- `add` superimposes onto the bed.
- `replace` gates the bed down (toward `bed × (1 − amount)`) then releases.

Authoring a Moment's window: capture begin/end from the live playhead, **Snap to beat** (quantize to the chapter's beat grid), **Chain** (anchor next begin to last end). This is the `events` model finalized: **chapter-scoped, composes additively or as a gate**, resolving [funscriptforge.spec.md §8.6](background/funscriptforge.spec.md).

---

## 3. Feel from motion — the derivation (the new bridge)

**The decision:** Feel is **derived from the input funscript's motion**; the dials are the **adjustment surface** on top. This satisfies the easy-button promise (zero tuning → a sensible result from any input file) and keeps motion-first authoring ([funscript.spec.md §7](background/funscript.spec.md)).

The host's `assess` stage already computes phrases with BPM, pattern, amplitude, and behavioral tags. Feel reads off those. For a chapter (or phrase), over its motion window:

| Dial | Derived from | Notes |
|---|---|---|
| **Intensity** | motion energy (RMS of `pos` × speed) **+ the Passage/ramp slice** for this chapter | ramp is the scene-scale floor; motion energy rides on top |
| **Pace** | stroke frequency / BPM, normalized against a configurable max BPM | the dominant cycle rate in the window |
| **Wildness** | variability — variance of inter-stroke timing and amplitude; deviation from a regular pattern | high for irregular/textured motion |
| **Sharpness** | attack — normalized jerk (abruptness of `pos` change) at stroke turnarounds | hard edges → high |
| **Depth** | fraction of the 0–100 travel the motion actually uses (range within window) | |
| **Focus** | pattern coherence — how repetitive/locked the phrase is (inverse of embellishment) | distinct from wildness: focus = tracking the spine, wildness = texture |

> Constants below are marked **[calibrate]** — the formulas fix the *signals*; the constants are tuned against real scripts (§12). The reference test suite (`engine-tests/`) asserts mostly **relational invariants** (e.g. `Pace(fast) > Pace(slow)`) precisely so calibration doesn't break the goldens.

### 3.1 Base signals

Input actions `A = [(tᵢ, pᵢ)]`, `pᵢ ∈ [0,100]`. Over a motion window `[t₀, t₁]` of `T` seconds:

1. **Normalize & resample.** `xᵢ = pᵢ/100 ∈ [0,1]`; linearly interpolate onto a uniform grid `x[n]` at `Δ = 20 ms` (50 Hz), `n = 0…N−1`.
2. **Velocity** `v[n] = (x[n] − x[n−1]) / Δ_s`, `Δ_s = 0.02 s` (units: travel·s⁻¹).
3. **Acceleration** `a[n] = (v[n] − v[n−1]) / Δ_s`.
4. **Reversals → strokes.** Local extrema of `x` with prominence `≥ p_min` (default **0.05** [calibrate], rejects jitter) give ordered turning points `τ₁…τ_K`. Each adjacent pair is a **stroke** with amplitude `Aⱼ = |x(τⱼ₊₁) − x(τⱼ)|` and duration `Dⱼ = τⱼ₊₁ − τⱼ`.
5. **Stroke frequency** `f = (K−1) / (2T)` Hz (a full cycle = 2 strokes).
6. **Ramp slice** `R ∈ [0,1]` — the Passage envelope (§2.2) sampled at the chapter's center. Phase-1 single-chapter fallback: `R = clamp(ramp_per_hour/100 · elapsed_hours, 0, 1)` (default `ramp_per_hour = 15`).

### 3.2 Per-dial formulas (each → `[0,1]`)

Let `vᵣₘₛ = √(mean(v[n]²))`, `aᵣₘₛ = √(mean(a[n]²))`.

| Dial | Formula | Constant (default) |
|---|---|---|
| **Intensity** | `clamp( a_R·R + (1−a_R)·min(vᵣₘₛ / V_ref, 1), 0, 1)` | `a_R = 0.5`, `V_ref = 4.0` [calibrate] |
| **Pace** | `clamp( f / F_ref, 0, 1)` | `F_ref = 2.5 Hz` [calibrate] |
| **Wildness** | `clamp( 0.5·min(CV_D/CV_ref,1) + 0.5·min(CV_A/CV_ref,1), 0, 1)` where `CV_D = std(Dⱼ)/mean(Dⱼ)`, `CV_A = std(Aⱼ)/mean(Aⱼ)` | `CV_ref = 0.8` [calibrate] |
| **Sharpness** | `clamp( (CF − CF₀) / (CF_max − CF₀), 0, 1)` where `CF = pctl₉₅(\|v\|) / vᵣₘₛ` (velocity crest factor) | `CF₀ = 1.41` (sine), `CF_max = 3.0` [calibrate] |
| **Depth** | `clamp( median(Aⱼ) / D_ref, 0, 1)` | `D_ref = 1.0` (no free constant) |
| **Focus** | `clamp( ρ(L*), 0, 1)` — autocorrelation of `(x−x̄)` at the dominant lag `L* = round((1/f)/Δ)` | none |

**Why these and not the obvious ones:**
- **Sharpness uses the velocity crest factor**, which is **scale- and rate-invariant** (waveform *shape* only) — so a fast or deep stroke isn't mistaken for a sharp one. A triangle (constant speed) → `CF ≈ 1` → 0; dwell-then-snap → high `CF` → high. This deliberately decouples Sharpness from Pace and Depth.
- **Wildness** (irregularity of timing/amplitude) and **Focus** (spectral/autocorrelation coherence) are computed from different statistics so they're genuinely distinct, not two readouts of one number.

### 3.3 Dials as adjustments

Each dial persists a **signed offset** `o ∈ [−1, 1]` (default **0**). Effective Feel = `clamp(derived + o, 0, 1)`. The UI shows the **effective** value with a ghost mark at `derived`; dragging sets `o = effective − derived`. Persisting the *offset* (not the absolute value) means re-deriving after a motion edit preserves the user's intent relative to the new baseline. Offsets apply per chapter (Feel) or per phrase (Pattern). Default everywhere = easy button.

### 3.4 Edge cases (all must be NaN-safe — drives the fuzz fixtures, §11/tests)

| Condition | Behavior |
|---|---|
| empty / `N < 2` | Intensity = `R`; all motion dials = 0 |
| no reversals (`K < 2`): flat or monotonic | Pace = Wildness = 0; Depth = `clamp(x_max − x_min, 0, 1)`; Focus = `clamp(ρ(L*),0,1)` (monotonic → low f → clamp); Sharpness = 0 if `vᵣₘₛ = 0` |
| `vᵣₘₛ = 0` (flat) | Sharpness = 0; Intensity from `R` only |
| any denominator 0 (`mean(Dⱼ)`, `vᵣₘₛ`, `Σ(x−x̄)²`) | that term → 0 |
| huge gaps / single huge stroke | interpolation fills; `median` over strokes resists single-outlier domination |

> **Build note:** these derivation functions replace the prototype's `sampleIntent`/`deriveChannels` synth ([forge-engine.js](../prototype/scripts/forge-engine.js)), keeping the same *output* shape (`0..1` arrays over time) so the UI is unaffected. The prototype authored Feel from scratch; production derives it, then lets the same dials adjust. See [HANDOFF.md §5](../prototype/HANDOFF.md).

---

## 4. Signal pipeline (what the synth produces)

The device-agnostic signal, evaluated at time `t`:

```
passageAt(t)                         → slow envelope (scene dynamics / ramp slice)
feelAt(t)        = derive(motion@t) ⊕ adjustments      → the 6-dial Feel sample
intentAt(t)      = combine(passageAt, feelAt)          → device-agnostic bed
applyMoments(intentAt, t, moments)   → layer punctual influences (add | replace)
   ⇒ sourceAt(t) : the single signal Polish renders
```

`sourceAt` is the **one signal**. It is device-agnostic: no carrier, no axes, no channels — just energy + feel over time. Everything below this line is per-device.

**Internal representation is free.** Funscript is a **render target, not the working format** ([funscript.spec.md §3](background/funscript.spec.md)). The internal model can be continuous signals / per-chapter parameter curves / an in-memory model. Constraints only: (a) renderable for preview/playback, (b) renderable as the funscript channel set at export.

---

## 5. Polish — the per-device forge

Polish conditions `sourceAt` into device output. Two stages per device:

### 5.1 Conditioning — device-shaped knobs → uniform primitives

Each device exposes its **own** knob set (the bespoke "Hammer & tongs"), normalized down to four synth primitives so the UI stays device-shaped while the synth stays uniform ([forge-engine.js](../prototype/scripts/forge-engine.js) `normKnobs`):

```
device knobs  ──normKnobs──►  { smoothing, quiet, rate, lead }
```

| Primitive | Meaning |
|---|---|
| `smoothing` | low-pass on the envelope (tames jitter the hardware can't track) |
| `quiet` | floor — minimum so the sensation never fully drops out / motor never stalls |
| `rate` | max per-step change (BPM ceiling → carriage/motor reachability) |
| `lead` | command lead-time (ms) to beat transport/BT/servo latency |

### 5.2 Channel derivation — single signal → device tracks

- **Single-axis devices** (Handy, Vacuglide): one output track — conditioned position. Bench shows dashed **input** vs. bold **to-device** band.
- **Multi-channel devices** (e-stim): reveal their axes on the bench (`CHANNELS` / `deriveChannels`), one file per channel.

**Profile contract** — every profile declares:
1. The channels/tracks it emits, each channel's **valid range + clamp**.
2. Its knob schema and `normKnobs` mapping.
3. The Feel → channel mapping (where each dial's energy goes).
4. **Device-specific safety limits** (§9).

**Design rule:** no device specifics above the profile layer. Adding a device = adding a profile, not touching the engine.

---

## 6. Profiles built first

| Profile | Class | Tracks | Status |
|---|---|---|---|
| **E-stim 3-phase** (restim) | e-stim | alpha, beta, volume, pulse_*, frequency (+ variants) | **build** — §7 |
| **The Handy** | single-axis stroker | position | **build** — §8 |
| **Vacuglide** | single-axis stroker (sleeve) | position | **build** — §8 |
| OSR2 / SR6 | multi-axis stroker | L0/R0/R1 … (1→many lift) | future |
| Lovense | vibe | vibration intensity | future |
| bHaptics | vest | per-actuator intensity | future |
| shaker | transducer | low-freq amplitude | future |

---

## 7. E-stim profile (full channel set)

E-stim is **not one funscript**: alpha+beta encode 3-phase position, volume the intensity, pulse/frequency the texture. **Export-only** — generated funscript-style tracks handed to restim (or driven in-memory by ForgePlayer), not a live-driven single track.

### 7.1 Channels (the ten files)

For input `name.funscript`, emit into `estim/`:

| # | File | Derivation |
|---|---|---|
| 1 | `name.alpha.funscript` | 1-D→2-D lift, alpha axis (§7.2) |
| 2 | `name.alpha-prostate.funscript` | `alpha` inverted (`pos → 100 − pos`) |
| 3 | `name.beta.funscript` | 1-D→2-D lift, beta axis |
| 4 | `name.frequency.funscript` | weighted blend of ramp + speed → carrier window |
| 5 | `name.pulse_frequency.funscript` | mapped from alpha motion (Pace-driven) |
| 6 | `name.pulse_rise_time.funscript` | composite timing (omit if unset — restim default-empty) |
| 7 | `name.pulse_width.funscript` | alpha-derived, clamped to window |
| 8 | `name.volume.funscript` | normalized blend of ramp + speed (Intensity envelope) |
| 9 | `name.volume-prostate.funscript` | `volume` with raised floor / steeper mapping |
| 10 | `name.volume-stereostim.funscript` | `volume` remapped to the stereostim window |

Minimal playable set = **alpha + beta + volume**. **Emit-superset, consume-subset**: emit the full set; restim plays what it's configured for, ignores the rest ([funscript.spec.md §5](background/funscript.spec.md)).

### 7.2 The 1-D → 2-D lift (real geometry — replaces prototype's illustrative sine)

```
radius(t) = min_distance + (1 − min_distance) · clamp(speed(t) / speed_at_edge, 0, 1)
alpha(t)  = 0.5 + 0.5 · radius(t) · cos(θ(t))      # then scaled to [0, 0.998]
beta(t)   = 0.5 + 0.5 · radius(t) · sin(θ(t))
```

- `min_distance` (0.1–0.9): minimum radius for slow motion. ← **Depth** sets the radius range; slow motion → center (diffuse), fast → edge (localized).
- `θ(t)` chosen by a **lift style**, selected from **Feel** (not hand-picked per chapter unless overridden):

> **restim parity (verified against [diglet48/restim](https://github.com/diglet48/restim) `funscript_1d_to_2d.py`, MIT).** Our **encoding is byte-compatible** with restim — `pos` int 0–100 ⇄ decoded 0–1, `at` in ms, `actions` array, one file per axis — so our `alpha`/`beta` load in restim unchanged. Our **geometry intentionally differs**: restim's converter is *amplitude-driven* (`r = (start−end)/2`, alpha follows the raw position, semicircle per stroke) and is basic + **no longer maintained**; ours is *speed-driven* per edger's documented philosophy and Feel-shaped. We keep ours — it's the richer creator restim lacks — while staying load-compatible.

| Lift style | θ range | Feel that selects it |
|---|---|---|
| Circular | 0°–180° (semicircular sweep) | low Wildness, default |
| Top-Left-Right / Top-Right-Left | 0°–270° / 0°–90° (biased arc) | moderate Wildness + Bias |
| 0–360 full | full rotation, optional random flips | high Wildness |

Feel → lift mapping (replaces the old per-chapter "character" table, now derived): **Wildness** drives style randomness/flips, **Pace** the angular rate, **Depth** the radius envelope, **Focus** the smoothing of θ. The five edger-style characters (Gentle/Reactive/Scene Builder/Unpredictable/Balanced) become **named Feel presets**, not a separate axis.

### 7.3 Other e-stim channels

- `volume = normalize(w_r · ramp + w_s · speed)`. **Intensity** scales it; ramp is the Passage slice.
- `volume-prostate` = raised floor / steeper map. `volume-stereostim` = linear remap to the stereostim window.
- `frequency` = weighted blend (ramp:speed) into the carrier window (500–1500 Hz). **Pace** biases toward speed.
- `pulse_frequency` = map(alpha motion) → 1–150 Hz. **Pace**-driven.
- `pulse_width` = alpha-derived, clamped 3–15. **Sharpness** narrows it.
- `pulse_rise_time` = composite, clamped 1–5; omit file unless enabled.

### 7.4 restim contract (interoperability facts)

Ranges below are **edger's verified `normalization`** (from `config.event_definitions.yml`,
edger477/funscript-tools) where present — they supersede earlier assumptions. **The engine
emits *normalized* funscript values (pos 0–100 ⇄ decoded 0–1); these physical ranges are how
restim maps that normalized value.** So our files are restim-compatible regardless; this table
is the device-side mapping, not our on-disk encoding.

| Channel | Range (Min–Max) | Meaning |
|---|---|---|
| `alpha`, `beta` | 0 – 0.998 | spatial position (unit-disc point); restim derives the 3-phase electrode signals from this 2-D point |
| `volume` | 0 – 1.0 (edger); **we cap at ≤ 0.7** | intensity / amplitude. edger sets no ceiling; §9 keeps ours more conservative ("meet or beat") |
| `frequency` (carrier) | 0 – 1200 Hz | carrier tone (was assumed 500–1500) |
| `pulse_frequency` | 0 – 120 Hz | pulse rate (was assumed 1–150) |
| `pulse_width` | 0 – 100 % | pulse width, as a percentage (was assumed 3–15 absolute) |
| `pulse_rise_time` | 1 – 5 | envelope rise (default-empty; not in edger's normalization — assumption, unconfirmed) |

### 7.5 Per-chapter generation + seam stitching

Synthesize channels **per chapter** (using that chapter's Feel + its Passage/ramp slice), then **stitch across seams** — blend channel values at chapter boundaries to avoid audible/physical discontinuities (assert a max per-seam delta). This is what differentiates us from edger's single global pass and makes the result vary scene-to-scene ([funscript.spec.md §6](background/funscript.spec.md)).

### 7.6 Chapter input contract (how boundaries reach the engine)

**The engine consumes chapter boundaries; it does not create them.** Chapter *creation* (audio/video analysis → 3–5 min chunks) is the host's `[chapterize]` stage (§10); the host owns steps that produce `[{start, end}, …]`, and this engine owns generation. So boundaries are **supplied**, via any of four forms (precedence high → low):

| Form | How | Use |
|---|---|---|
| **Sidecar JSON** | `--chapters-file <file>` / `load_chapters_file(path)` → `[(start_ms, end_ms), …]` | real scenes from the host / a tool |
| **Explicit tuples** | `generate_estim(actions, chapters=[(start_ms, end_ms), …])` | programmatic embedding (a first-class library option) |
| **Equal split** | `--chapters N` / `chapters=N` | a **testing convenience** — naive equal-duration windows, not real scenes |
| **None** | default | single chapter spanning the whole clip (Phase-1 fallback) |

**Sidecar schema (tolerant, so different tools' files fit).** The document is a top-level array **or** an object with a `chapters` array. Each entry needs a **start**; the **end** is taken from `end`/`duration`, else the next chapter's start, else the clip end. Times are a number/numeric-string (= **milliseconds**, the funscript `at` convention) or a colon string (`HH:MM:SS.mmm` / `MM:SS`). Accepted key aliases — start: `start`/`startTime`/`start_ms`/`from`/`begin`/`at`/`time`; end: `end`/`endTime`/`end_ms`/`to`/`finish`/`stop`; duration: `duration`/`dur`/`length`; name (optional): `name`/`title`/`label`. Entries without a start are skipped. If a real file doesn't parse, the parser is widened rather than the file reshaped.

> This keeps the **host-owns-chaptering** boundary from [funscript.spec.md §11](background/funscript.spec.md) intact while making the engine usable standalone by anyone with a chapter sidecar.

---

## 8. Single-axis profiles (Handy, Vacuglide)

Output is one conditioned **position** track. The source signal is mapped to stroke position; Feel shapes how:

| Feel dial | Single-axis effect |
|---|---|
| Intensity | stroke energy / aggressiveness |
| Pace | cycle rate (capped by Max BPM) |
| Wildness | smoothed into stroke variation (one axis can't hold full texture) |
| Sharpness | turnaround aggressiveness |
| Depth | stroke window / range used |
| Focus | smoothing of the position curve |

**Knob schemas** (→ `normKnobs`):

| Device | Knobs | Notes |
|---|---|---|
| **The Handy** | Max BPM · Smoothing · Lead-time · Position step | `step` skips micro-jitter the carriage won't bother with |
| **Vacuglide** | Stroke window · Smoothing · Max BPM · Lead-time | heaviest smoothing — slowest motor of the set |

Conditioning order (per [forge-engine.js](../prototype/scripts/forge-engine.js) `buildDevice`): smooth → apply floor (`quiet`) → clamp per-step delta (`rate`) → apply `lead`. Output is one `position` funscript.

---

## 9. Safety (non-negotiable)

E-stim drives current through the body; intensity and waveform bounds are a **safety boundary**, not a feel knob. **Form is ours; the safety envelope is earned knowledge** — treat edger's documented ranges/ramp rates/ceilings as a **validated baseline to meet or beat**, and justify+test any deviation that could affect safety.

- **Hard-clamp every output** to its device range *after* all math — never emit `pos` outside 0–100; never let volume variants exceed the configured hardware max.
- Global `max_volume` ceiling (default ≤ 0.7) honored by `volume`, `volume-prostate`, `volume-stereostim`.
- Prefer **smooth ramps** over step jumps; cap per-step volume delta (the `rate` primitive).
- Ramp rate within the safe envelope (default 15 %/hour, range 0–40).
- **Carrier-frequency floor (frequencies to avoid).** A carrier that is too *low* is unsafe — per restim's *e-stim-safety* wiki (IEC 60601-2-10 + charge-per-phase): low Hz permits far less current (`50 mA < 400 Hz`, `80 mA < 1500 Hz`), and the minimum safe carrier runs **≈ 446 Hz** (15 cm² glans loop) to **≈ 755 Hz** (9 cm² shaft). The engine **floors the carrier to a safe minimum** (default `MIN_CARRIER_HZ = 500`, raise for small electrodes) so it can never drop toward 0. **Net pulsetrain charge** must stay under the reversible storage limit (~40–50 µC/cm²) — no DC bias — to avoid electrode corrosion. Because restim *also* lets the user select the carrier (with its own electrode-aware safety calc), the automated `frequency` channel is **optional** (`emit_carrier=False` → restim owns the static carrier). This resolves §12 Q#4.
- **Do not** invent waveform parameters outside documented restim ranges.
- Each profile owns its device-specific safety limits.

The prototype has **no** safety layer — this section is mandatory net-new work, applied as the final stage of every render and export.

---

## 10. Pipeline & integration

```
input.funscript
   │
   ▼
[chapterize]  → audio analysis → 3–5 min editing chunks (video detection planned)
   │
   ▼
[assess]      → phrases within each chapter (BPM, pattern, tags)
   │
   ▼
[derive Feel] → per-chapter 6-dial Feel from motion (§3); Passage/ramp across chapters
   │
   ▼
[adjust]      → user nudges Feel (chapter), Patterns (phrase), drops Moments (beat)
   │            ← live single-output render here, to VISUALIZE choices
   ▼
[POLISH]      → device selected HERE (last step); condition sourceAt → device tracks
   ├─ e-stim       → alpha/beta/volume/pulse_*/frequency (+ variants)  §7
   ├─ Handy        → position  §8
   └─ Vacuglide    → position  §8
   │
   ▼
[safety]      → clamp every channel to range + ceilings  §9
   │
   ▼
render → ForgePlayer (native, in-memory) OR funscript export folder (+ _forge_log)
```

**Two playback paths** ([funscriptforge.spec.md §5B](background/funscriptforge.spec.md)):
- **External players** → emit funscript superset → ship to a recognized folder (restim's channel names) → player consumes its subset.
- **ForgePlayer (native)** → read `.forge` metadata → select per device → play in-memory. No funscript surfaced.

**Handoff contract (decision to confirm):** **(B) structured intermediate as the contract** (a normalized `intent + Feel + passages + moments` model each profile consumes) **+ (A) in-process library call for the e-stim implementation**. B keeps profiles independent; A keeps the e-stim path fast and file-free for ForgePlayer. Resolves [funscriptforge.spec.md §8.3](background/funscriptforge.spec.md).

**State contract** (single source of truth, from [HANDOFF.md §5](../prototype/HANDOFF.md)):
```
feel       // {intensity, pace, wildness, sharpness, depth, focus} — derived ⊕ adjustment
passages   // [{id, shape, from, to, lo, hi}]   — scene dynamics / ramp
moments    // [{id, typeId, at, dur, amount}]    — beat influences
// per chapter; per-tab UI: lensId, benchId, knobMap
```

---

## 11. Implementation phases

**Phase 1 — Motion → intent → playable e-stim core.**
- Parse input funscript; integrate chapterization (or single-chapter fallback).
- Compute speed + ramp; **derive the 6 Feel dials from motion** (§3).
- Synthesize `alpha`, `beta`, `volume` via the real lift (§7.2).
- Write valid funscript JSON; apply safety clamps (§9).
- **Verify:** restim loads alpha/beta/volume and plays clean; alpha/beta trace a sane disc path on slow vs. fast input; golden-file tests on a short sample.

**Phase 2 — Full e-stim channels + variants + single-axis profiles.**
- Add `frequency`, `pulse_*` with clamping; `alpha-prostate`, `volume-prostate`, `volume-stereostim`.
- Chapter-local lift styles + seam stitching (§7.5).
- Handy + Vacuglide profiles (§8).
- **Verify:** every channel within range; no discontinuities at seams (max per-seam delta); single-axis output plays on the real device.

**Phase 3 — Adjustment surface, Moments, config, safety hardening.**
- Feel/Pattern adjustment UI; Moments authoring (snap-to-beat, chain).
- Passage editor (scene dynamics / ramp).
- Config + presets (easy button = derived Feel, zero adjustment).
- **Verify:** fuzz pathological inputs (empty, single point, huge gaps, max-speed) → no NaN, no out-of-range `pos`, no unsafe volume.

---

## 12. Open questions

1. **7th Feel dial** — Regularity/Groove or Bias/Direction? Decide after authoring against the six (§2.1).
2. **Feel derivation tuning** — the exact motion→dial formulas (§3) need calibration against real scripts; the table fixes the *signals*, not the constants.
3. **stereostim remap window** — exact min/max for `volume-stereostim` (placeholder = linear remap of full range).
4. **carrier `frequency`** — automate it, or leave static in restim and emit only `pulse_frequency`?
5. **pulse_rise_time** — emit or omit by default (assumption: omit unless enabled).
6. **Output folder convention** — exact per-device export layout the player auto-discovers.
7. **License/ownership audit** — pin the exact commits/files of your CLI contribution; record restim's LICENSE before reusing any of its *code* (concepts/ranges are interoperability facts and already safe).
8. **Handoff A/B/C** — confirm the §10 recommendation in design review before fixing profile input shapes.

---

### Sources consulted (facts only)
- [diglet48/restim](https://github.com/diglet48/restim) — realtime multi-electrode e-stim from funscript/audio; parameter ranges.
- [edger477/funscript-tools](https://github.com/edger477/funscript-tools) — channel list and roles (read-only; unlicensed).
- [edger477/Restim-Controller](https://github.com/edger477/Restim-Controller) — parameter value ranges.
- [liquid-releasing/funscriptforge](https://github.com/liquid-releasing/funscriptforge) — host pipeline, phrases, tones, device list, CLI.
