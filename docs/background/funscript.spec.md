# Multi-Channel Funscript Generation Spec

**Status:** Draft v0.1
**Purpose:** Define an application that takes a single input `.funscript` (a 1‑D stroke/position track) and generates the set of channel funscripts required to drive **restim** e‑stim hardware over audio connectors — producing output comparable to edger477's `funscript-tools`, but using our own (funscriptforge) generation approach.

> This document is a *clean‑room interface + design spec*. It documents the playback contract (the funscript format and restim's parameter ranges, which are interoperability facts) and specifies **our own algorithms**. It does **not** reproduce proprietary source code. See [§2 Licensing](#2-licensing--clean-room-stance) before reusing any third‑party code.

---

## 1. Goals & non‑goals

**Goal:** From one input funscript, generate up to ten channel funscripts that restim can load and play, with intensity/positioning/pulse characteristics that feel haptically coherent with the source motion.

**Build target (decided):** **restim three-phase** (alpha/beta positioning across a 3-electrode setup) as the output model, and the **full channel set** (all ten, §5) as the first build — not a minimal subset. Spec **scope** (self-contained generator vs. FunscriptForge-host-coupled) is **pending** a separate discussion; the consolidated clean-room *build* spec will be assembled once that's settled.

**Non‑goals (for now):**
- We are not required to generate all ten channels — a working subset is acceptable (see [§9 phasing](#9-implementation-plan-3-phases)).
- We are not reverse‑engineering or copying edger477's implementation. We match the *outputs' role*, not his code — and our format need not match his (§10), **but the safety envelope must**.
- Real‑time generation is out of scope; this is an offline batch converter.

---

## 2. Licensing & clean‑room stance

Your concern about reuse is correct and material. The driving fact: **edger477's information is public, but his repo carries no open‑source license.** "No license" does **not** mean public domain — under default copyright it means **all rights reserved**. We may *read* it; we may **not** copy or closely derive from its code. This is why we **rewrite the whole thing deeply as our own spec** and implementation, depending only on *facts* (the format and the documented parameter ranges), never on his code.

Ground rules:

| Source | What we may use | What we may **not** do |
|---|---|---|
| **Funscript format** | The JSON schema — open de‑facto standard. | — |
| **restim / edger477 parameter names & ranges** | Documented value ranges and channel meanings — an *interoperability contract* (like an API), required for compatibility. | — |
| **READMEs / wikis** | Learn *facts*: which channels exist, valid ranges, **safety limits**. | Copy substantial copyrighted prose verbatim. |
| **Unlicensed repo code** (edger477's, "all rights reserved") | Nothing — read for understanding only. | Copy or paraphrase code into our product. |
| **Licensed third‑party code** (e.g. restim, prior‑work repos) | Only if its **LICENSE explicitly permits**, with required attribution. | Reuse *before* reading its LICENSE. "Based on prior work" repos may carry inherited obligations — treat as suspect until verified. |

**Our own contribution.** You authored and contributed the **entire CLI** to edger477's funscript-tools, under the name **liquid-releasing** — there was **no CLI before your contribution**; your intent was to make his code usable as a **pipeline**. The maintainer may have added to it since. You **retain copyright in the code you wrote** — merging it into his repo does not transfer your copyright (and with no CLA, he holds at most an implied license to use it *in that project*; it does not become his). Therefore **your CLI is safely reusable by us** as a starting point; the rest of his repo is clean‑room (read‑only). Pin down exactly which commits/files are yours in [§11](#11-open-questions--assumptions) so the boundary is unambiguous.

**Action item:** before lifting any algorithm *code* (not concepts), open the repo's `LICENSE` and contribution terms and record them in §11. Concepts and published parameter ranges are safe; verbatim third‑party code is not.

---

## 3. The funscript file format

A funscript is a JSON file describing a single time‑series channel.

```json
{
  "version": "1.0",
  "inverted": false,
  "range": 100,
  "actions": [
    { "at": 0,    "pos": 0   },
    { "at": 250,  "pos": 80  },
    { "at": 600,  "pos": 20  }
  ]
}
```

- `at` — timestamp in **milliseconds** (integer, monotonically increasing).
- `pos` — position **0–100** (integer). For position channels this is stroke depth; for parameter channels (volume, frequency, …) it is a normalized 0–100 value that restim maps onto the channel's real range (see §4).
- `actions` — sparse keyframes; players **linearly interpolate** between them.

All generated channel files use this same format. The semantic meaning of `pos` differs per channel; the *encoding* never does.

**Funscript is a render target, not the working format.** The generator's **internal representation can be whatever serves it** (continuous signals, per-chapter parameter curves, an in-memory model) — funscript is produced only when **rendering out** at polish/export, or fed live to a player. The constraints are just: (a) the model can be **rendered for preview/playback**, and (b) the final result can be **rendered as the funscript channel set** above. This latitude comes from FunscriptForge developing device output at the **Polish** step rather than building funscript buckets eagerly (see [funscriptforge.spec.md §4](funscriptforge.spec.md)). Practically: design the internal model for fidelity and safety first; treat funscript emission as a final serialization.

---

## 4. restim playback model (the target contract)

restim is a realtime multi‑electrode e‑stim signal generator. It loads a set of funscripts — one per parameter — and synthesizes an **audio** signal that is fed via audio connectors (a stereo/multi‑channel audio interface) into e‑stim hardware. Each parameter funscript automates one axis of the synthesized waveform over time.

restim maps each channel's `pos` 0–100 onto the channel's configured `[ValueMin, ValueMax]` range:

| Channel | Range (Min–Max) | Physical meaning |
|---|---|---|
| `alpha` | 0 – 0.998 | Spatial position, axis 1 — *where* the sensation sits between electrodes |
| `beta`  | 0 – 0.998 | Spatial position, axis 2 — combined with alpha gives a 2‑D location |
| `volume` | 0 – 0.998 | Intensity / amplitude of the stim |
| `frequency` (carrier) | 500 – 1500 Hz | Carrier tone frequency |
| `pulse_frequency` | 1 – 150 Hz | How often pulses fire |
| `pulse_width` | 3 – 15 | Width/duration of each pulse |
| `pulse_rise_time` | 1 – 5 | Pulse envelope rise time (empty/unset by default in restim) |

**Spatial model (alpha/beta → "three‑phase" position).** A single 1‑D input funscript has only depth. restim's spatial illusion needs a 2‑D coordinate (alpha, beta), interpreted as a point in a unit disc. Moving that point around the disc moves the felt sensation across the electrode array. So the converter's central job is **1‑D → 2‑D lifting**: turning stroke position+speed into an (alpha, beta) path.

**Audio channel mapping.** restim renders the (alpha, beta, volume, pulse…) state into a multi‑channel audio stream. The `*-stereostim` variant targets a stereostim‑style two‑channel mapping where the volume range is re‑scaled for that hardware's safe/effective window.

---

## 5. Output channels (the ten files)

For an input `name.funscript`, the converter emits into an output directory:

| # | File | Derivation (our impl, see §7) |
|---|---|---|
| 1 | `alpha.funscript` | 1‑D→2‑D lift of input (alpha axis) |
| 2 | `alpha-prostate.funscript` | `alpha` inverted (`pos → 100 - pos`) for prostate placement |
| 3 | `beta.funscript` | 1‑D→2‑D lift of input (beta axis) |
| 4 | `frequency.funscript` | Weighted blend of a **ramp** signal and a **speed** signal |
| 5 | `pulse_frequency.funscript` | Mapped from alpha motion |
| 6 | `pulse_rise_time.funscript` | Composite timing signal from pulse params |
| 7 | `pulse_width.funscript` | Alpha‑derived, clamped to the pulse‑width window |
| 8 | `volume.funscript` | Normalized blend of ramp + speed (intensity envelope) |
| 9 | `volume-prostate.funscript` | `volume` with an enhanced/raised intensity mapping |
| 10 | `volume-stereostim.funscript` | `volume` re‑mapped to the stereostim range |

A minimal but *playable* set is **`alpha` + `beta` + `volume`** (position + intensity). Everything else refines feel.

**Emit-superset, consume-subset.** We **emit the full channel set; restim plays what it's configured for** and ignores the rest — the same approach edger477 uses (he prints a dozen+ funscripts for 4-phase and restim selects). The generator doesn't gate on the target config; it produces the complete set. See [funscriptforge.spec.md §4](funscriptforge.spec.md).

---

## 5A. Output device profiles (multi‑use)

restim e‑stim is **one target, not the only one.** The converter's core (chapters → base curves → channel synthesis) is device‑agnostic; a final **profile** stage maps the internal signal onto a specific device family. This keeps one engine serving many devices.

```
internal signal (position, speed, ramp, intensity, 2‑D path)
        │
        ├── Profile: restim e‑stim   → alpha, beta, volume, pulse_*, frequency  (ranges per §4)
        ├── Profile: haptic / vibe   → single-axis intensity track(s) (e.g. Buttplug/Intiface, vibration 0–100)
        ├── Profile: stroker         → Handy (1‑D position); OSR2/SR6 multi‑axis (1→many axes)
        └── Profile: <other device>  → device‑specific channels + ranges
```

Profile responsibilities:
- Declare which channels it emits and each channel's valid range + clamp.
- Map the internal intensity/position/2‑D signal onto those channels.
- Own device‑specific safety limits (§10).

Design rule: **no device specifics above the profile layer.** Adding a device = adding a profile, not touching the engine. The `-prostate` / `-stereostim` variants are *sub‑profiles* of the restim profile (placement/hardware remaps), not special cases in the core.

---

## 6. Generation architecture — host-driven, per-segment

This e-stim generator is **one device profile under FunscriptForge** — see the companion doc **[funscriptforge.spec.md](funscriptforge.spec.md)** for the host pipeline (chapters → phrases → tones → device profiles).

We deliberately diverge from edger477: his tool runs one **global** pipeline over the whole script. Instead, **this generator synthesizes the e-stim channels _per chapter_**, then stitches across chapter seams. Each chapter selects its own **character** (a named parameter set — edger's term; he varies sections by different params) which drives the lift style and channel mapping (§7.2). Generating per chapter is what (a) differentiates us from edger's single global pass and (b) makes the result more interesting — the feel changes chapter to chapter.

**Granularity: chapter, not phrase.** The chapter (3–5 min) is the right unit for e-stim generation; **phrases/phases are too small** to vary character over. Phrases/patterns/stanzas are the *editing* lenses for the motion (see [funscriptforge.spec.md §2](funscriptforge.spec.md)); chapters are the *generation* unit here.

**Input is a single funscript.** After all motion transforms are applied, the result is **still one funscript** (one motion track). This generator expands that single motion into the multi-channel e-stim set, chapter by chapter — the multi-channel split happens *at generation*, not by cutting the motion into pieces.

```
input.funscript
   │
   ▼
[1] Segment into chapters ──────────────► chapter list: [{start, end, profile}, …]
   │        (funscriptforge's segmentation: scene/intensity boundaries)
   ▼
[2] Per chapter: derive base signals
        ├─ position curve   (resampled, smoothed)
        ├─ speed curve      (|d pos / d t|)
        └─ ramp curve       (slow intensity build, %/hour)
   │
   ▼
[3] Per chapter: synthesize channels
        ├─ alpha/beta  ← 1‑D→2‑D lift (chapter‑local style)
        ├─ volume      ← blend(ramp, speed)  → normalize
        └─ pulse_*     ← map(alpha, speed)
   │
   ▼
[4] Stitch chapters → continuous channel tracks (smooth boundaries)
   │
   ▼
[5] Emit derived variants (prostate inversions, stereostim remap)
   │
   ▼
output/*.funscript
```

**Why chapters matter here:** chapter boundaries let us vary the 1‑D→2‑D *style* and intensity envelope by scene (e.g. a slow chapter uses a smaller radius and gentler ramp than a fast one) without manual global ratio tuning. The stitch step (4) must blend channel values across chapter seams to avoid audible/physical discontinuities.

> **Assumption — confirm:** funscriptforge already produces chapter boundaries (and possibly the resampled position/speed/ramp curves). The cleanest integration is: funscriptforge owns steps **[1]–[2]**, this converter owns **[3]–[5]**. If funscriptforge's chapter API differs, adjust the boundary in [§11](#11-open-questions--assumptions).

---

## 7. Core algorithms

### 7.1 Speed and ramp (base signals)

- **Speed** `s(t)` = magnitude of position change rate, `|Δpos / Δt|`, smoothed, then normalized to 0–1 against a configurable `speed_at_edge` threshold (default **1–5 Hz** → 1.0).
- **Ramp** `r(t)` = a slow intensity envelope, configurable **0–40 %/hour** (default **15 %/hour**), giving long‑arc tension that motion alone doesn't. **Ramp is assigned _across chapters_ by the host** (FunscriptForge), not built locally per segment — each chapter inherits its slice of the cross-chapter envelope, and per-segment intensity sits on top. See [funscriptforge.spec.md §3A](funscriptforge.spec.md). **Events** (host-supplied extra influences) may further modulate `r(t)` or volume at specific points.

### 7.2 1‑D → 2‑D lift (alpha/beta)

Map stroke position to an angle θ on a disc and modulate radius by speed:

```
radius(t) = min_distance + (1 - min_distance) * clamp(speed(t) / speed_at_edge, 0, 1)
alpha(t)  = 0.5 + 0.5 * radius(t) * cos(θ(t))      # then scaled to [0, 0.998]
beta(t)   = 0.5 + 0.5 * radius(t) * sin(θ(t))
```

- `min_distance` — minimum radius for slow motion, **0.1–0.9**.
- θ(t) is chosen by a **style** (selectable per chapter):
  - **Circular (0°–180°)** — semicircular sweep.
  - **Top‑Left‑Right (0°–270°)** / **Top‑Right‑Left (0°–90°)** — arc oscillations biased to one side.
  - **0–360 full** — stroke‑relative full rotation (restim‑style), optional random direction flips.

Slow movement → near center (broad, diffuse). Fast movement → toward the edge (sharp, localized).

### 7.3 volume

`volume = normalize( w_r · ramp + w_s · speed )`, weights `w_r, w_s` configurable. Then:
- `volume-prostate` = same curve with a raised floor / steeper mapping (enhanced intensity).
- `volume-stereostim` = linear remap of the 0–100 range into the stereostim window.

### 7.4 pulse channels

- `pulse_frequency` = map(alpha motion) → 1–150 Hz window.
- `pulse_width` = alpha‑derived, **clamped to 3–15**.
- `pulse_rise_time` = composite of the above timing, **clamped to 1–5** (omit the file if left unset, matching restim's default‑empty behavior).

### 7.5 inversions & variants

- `alpha-prostate` = `pos → 100 - pos` of `alpha`.
- All variant files reuse a base channel's timestamps; only `pos` is transformed. Keep transforms pure and side‑effect‑free for testability.

---

## 8. Parameter reference (defaults)

| Param | Range | Default | Used by |
|---|---|---|---|
| `min_distance` | 0.1 – 0.9 | 0.3 | alpha/beta radius floor |
| `speed_at_edge` (Hz) | 1 – 5 | 3 | speed normalization |
| `ramp_per_hour` (%) | 0 – 40 | 15 | volume/frequency ramp |
| `lift_style` | enum | Circular | alpha/beta θ |
| `volume weights` `w_r:w_s` | ratio | 50:50 | volume blend |
| `frequency weights` ramp:speed | ratio | 66:33 | frequency blend |
| carrier `frequency` (Hz) | 500 – 1500 | 800 | frequency channel target range |

All persisted to a project config (e.g. `funscriptforge.config.json`), with save/load/reset.

**Easy-button preset (required).** The generator must ship a **reasonable-defaults preset** that produces a safe, playable full channel set with **zero tuning** — the values above are chosen to be exactly that. This backs FunscriptForge's one-click "easy button" ([funscriptforge.spec.md §1](funscriptforge.spec.md)): all per-chapter character/param controls are *opt-in* refinements over this default.

---

## 9. Implementation plan (3 phases)

**Phase 1 — Minimum playable converter.**
- Parse input funscript; integrate funscriptforge chapter segmentation (or a single‑chapter fallback).
- Compute speed + ramp.
- Generate `alpha`, `beta`, `volume`.
- Write valid funscript JSON.
- **Verify:** restim loads all three and plays without errors; alpha/beta trace a sane disc path on slow vs fast input. Golden‑file tests on a short sample.

**Phase 2 — Full channel set + variants.**
- Add `frequency`, `pulse_frequency`, `pulse_width`, `pulse_rise_time` with correct clamping.
- Add `alpha-prostate`, `volume-prostate`, `volume-stereostim`.
- Chapter‑local lift styles + boundary stitching.
- **Verify:** every channel stays within its restim range; no discontinuities at chapter seams (assert max per‑seam delta).

**Phase 3 — Tuning, config & safety.**
- Config UI/file with the §8 parameters; presets.
- Volume normalization + **safety clamps** (§10).
- **Verify:** fuzz with pathological inputs (empty, single point, huge gaps, max‑speed) → no NaN, no out‑of‑range `pos`, no clipped/unsafe volume.

---

## 10. Safety

E‑stim drives current through the body; intensity and waveform bounds are a **safety boundary**, not just a feel knob.

**Format freedom, not safety freedom.** Our output **need not match edger477's** channel set, naming, or structure — we are free to design our own. **But it must be _safely produced_.** edger's parameter ranges, ramp behavior, and limits reflect **years of baked-in expertise** about what is safe; that expertise is the one thing we cannot casually discard while diverging on form. So: diverge in shape if it serves us, but treat his documented safe envelope (ranges, ramp rates, ceilings) as a **validated baseline to meet or beat**, and justify/test any deviation that could affect safety. Form is ours; the safety envelope is earned knowledge.

- **Hard‑clamp every output** to its restim range *after* all math — never emit `pos` outside 0–100, and never let volume‑variant remaps exceed the configured hardware max.
- Provide a global `max_volume` ceiling (e.g. ≤ 0.7) honored by `volume`, `volume-prostate`, `volume-stereostim`.
- Prefer **smooth ramps** over step jumps in volume; cap per‑step volume delta.
- Treat any safety guidance found in third‑party docs as *facts to honor*, and record the source in §11.
- **Do not** invent waveform parameters outside the documented restim ranges.

---

## 11. Open questions & assumptions

1. **funscriptforge chapter API** — what does it expose (boundaries only, or also resampled position/speed/ramp curves)? This sets the [§6] integration seam. *(assumption: it owns segmentation + base curves)*
2. **License & ownership audit** — (a) edger477's repo has **no license = all rights reserved**: read‑only, no code reuse. (b) Identify the exact commits/files of **your merged CLI contribution** — that's yours to reuse. (c) Record the LICENSE of `diglet48/restim` and any "prior‑work" repos before reusing their *code*. Concepts/ranges already used here are interoperability facts.
3. **stereostim remap window** — exact min/max for `volume-stereostim`? Placeholder = linear remap of full range.
4. **carrier `frequency` channel** — confirm whether we automate carrier frequency at all, or leave it static in restim and only emit `pulse_frequency`. *(edger477 emits a combined ramp/speed `frequency`; confirm target range.)*
5. **pulse_rise_time** — emit the file, or omit (restim default‑empty)? *(assumption: omit unless explicitly enabled)*
6. **Output naming/layout** — *direction set:* on **ship**, the generated funscripts are written to a **folder the user (and the player) recognizes** — i.e. a known export location with the filenames the player auto-discovers (restim's expected channel names; multi-axis naming for SR6). Open detail: exact folder convention per device and how the player picks it up. See [funscriptforge.spec.md §5/export](funscriptforge.spec.md).
7. **Device profiles (§5A)** — which non‑restim targets are in scope first (haptic via Buttplug/Intiface? stroker passthrough?), and their channel sets + safe ranges.

---

### Sources consulted (facts only)
- [diglet48/restim](https://github.com/diglet48/restim) — restim overview (realtime multi‑electrode e‑stim from funscript/audio).
- [edger477/funscript-tools](https://github.com/edger477/funscript-tools) — channel list and roles.
- [edger477/Restim-Controller](https://github.com/edger477/Restim-Controller) — parameter value ranges.
