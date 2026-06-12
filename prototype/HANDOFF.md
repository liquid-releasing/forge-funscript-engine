# Unified Forge — Developer Handoff

**FunscriptForge · cross-device authoring**
Status: design prototype for review · single-file artifact: `Unified Forge.html`

---

## 1. What this is

A reframe of how FunscriptForge authors cross-device output. The old model split authoring **per device** (a tab for e-stim "character", a tab for mechanical "motion", etc.). This prototype collapses that into **one device-agnostic intent signal** that every device derives from, and pushes all device-specificity to the last step (Polish).

The whole thing is three tabs over **one shared state**:

```
VOICING  →  the continuous bed      — feel + dynamics, authored once
MOMENTS  →  punctual influences      — dropped in the moment, layered on top
POLISH   →  the per-device forge     — conditions the one signal into N device files
```

Voicing + Moments produce a single signal. Polish is the **only** place hardware shape enters.

---

## 2. The unified value model

This is the deliverable the original request asked for — "a new unified set of values used when we create the scripts during polish or export." It is small and device-agnostic.

### Feel — the character of the energy (6 dials, all 0..1)
| Dial | Meaning |
|---|---|
| **Intensity** | how strong |
| **Pace** | how fast (vibrate/buzz is just pace cranked up) |
| **Wildness** | how unpredictable / textured |
| **Sharpness** | attack — smooth swell vs. hard edge |
| **Depth** | how much of the full travel the signal uses |
| **Focus** | tight tracking of the source spine ↔ loose embellishment |

> **Open question for the team:** a *seventh* dial may be missing. The prototype intentionally leaves room — the belief is it surfaces once you author against the six. Candidate axes discussed: "Regularity/Groove" (lock to beat grid) and "Bias/Direction" (where in the stroke the energy concentrates). Not yet committed.

**Twist, vibrate, pulse, stroke are NOT dials.** They are *consequences* of feel + the target device. A multi-axis device spreads wildness onto twist; a vibrator collapses pace+wildness into one buzz envelope. The user authors "wild and building" — Polish decides where that energy goes.

### Dynamics (Passages) — the slow envelope
Intensity arcs over the scene (minutes-scale): `build / fall / swell / hold` spans with `lo`/`hi` and a time range. This is the macro shape the feel rides on. The Voicing editor lets you **add / remove** passages and switch each one's shape via a segmented control labelled **Build / Release / Swell / Steady** (= `build / fall / swell / hold`; Steady is a flat no-op). Clear them all and it falls to an empty state.

### Moments — punctual influences
Named, begin/end windowed influences dropped while watching. Each **decompiles transparently** into feel-ops and declares a combine mode:
- `add` (ADDS ON TOP — superimposes onto the bed): Hold, Hit, Swell, Flutter
- `replace` (gates the bed down then releases): Tease

A moment is `{ typeId, at, dur, amount }`. The influence catalog (`INFLUENCES` in `forge-engine.js`) defines each type's `shape`, `combine`, and the human-readable `produces[]` list shown in the editor. The selected moment's window is set precisely with the **Mark begin / end from playhead** bar — *Begin*/*End* capture the live playhead (`fmtMs` shows m:ss.mmm), **Snap to beat** quantizes to an 8-per-chapter grid, **Chain** anchors the next Begin to the last captured End, and **Reset** restores the default duration.

### The same model at four time-scales
Passage (scene) → Character/feel (chapter) → Pattern (phrase) → Moment (beat). All are *influences on one signal*; they compose into a single per-time intensity+feel track. That track is what Polish renders.

---

## 3. Signal pipeline (what the synth does)

In `forge-engine.js`:

```
macroAt(t, passages)                 → slow envelope from Dynamics
sampleIntent(t, feel, passages, lens)→ rich feel sample, rendered through a lens
applyMoments(v, t, moments, bed)     → layer punctual influences (add | replace)
unifiedAt / sourceAt                 → the device-agnostic signal (INTENT lens)
buildDevice(dev, knobs, …)           → carrier + conditioning → the device track
```

**Lenses** (`LENSES`) are how the same intent is previewed as each device would speak it (freqMul, smoothing, fuzz, track count). `INTENT` is the device-agnostic source; the rest are device previews. In Voicing the lens is a *preview*; in Polish the device is the *target*.

### Polish conditioning ("Hammer & tongs") — bespoke per device, this is where hardware lives
Each station defines its **own** knob set in `KNOBS[deviceId]` (`forge-engine.js`), with a header subtitle. `normKnobs(deviceId, knobs)` maps whatever knobs a device exposes down to the synth's four conditioning primitives (`smoothing`, `quiet`, `rate`, `lead`), so the UI stays device-shaped while the synth stays uniform.

| Device | Header | Knobs |
|---|---|---|
| **The Handy** | BPM ceiling · carriage acceleration | Max BPM · Smoothing · Lead-time · Position step |
| **OSR2 / SR6** | axis spread · range mapping | Axis spread · Stroke range · Smoothing · Lead-time |
| **Lovense** | intensity floor · buzz response | Intensity floor · Response · Buzz curve · BT latency |
| **Vacuglide** | stroke window · motor smoothing | Stroke window · Smoothing · Max BPM · Lead-time |
| **E-Stim** | carrier · phase balance · volume floor | Carrier · Phase balance · Volume floor · Smoothing |

**Multi-channel devices** reveal their axes on the bench instead of a single track (`CHANNELS` + `deriveChannels` in `forge-engine.js`):
- **E-Stim → alpha / beta / volume.** E-stim is *not* one funscript — alpha+beta encode the 3-phase position, volume the intensity. Output is the `estim/` channel set (`*.alpha.funscript`, `*.beta.funscript`, `*.volume.funscript`). Polish is the device-render step where these appear.
- **SR6 → L0 / R0 / R1** (stroke / twist / roll).

Single-axis devices (Handy, Lovense, Vacuglide) show the dashed **input** vs. bold **to-device** band and one output file. **Stamp** = forge that device's file(s). E-stim is **export-only** — generated funscript-style tracks handed to an external player, not driven live (that library constraint is what motivated treating everything as one signal type: a normalized value-over-time on a named axis).

---

## 4. The single visual grammar

One honesty principle: **the picture is computed from the real signal, but reads perceptually.** `UnifiedBand` (in `forge-components.jsx`) draws:
- fill height = intensity, slope = build, stripe/osc = pace, **turbulence/fuzz = wildness**
- a faint dashed **position spine** = the literal derived curve (the honest funscript line)
- moment **windows** with labels overlaid (`momentsMode`: `off` | `faint` | `edit`)

Polish reuses the same grammar one layer down (`Bench`): dashed **input** (the one intent signal) vs. bold **to-device** output, with the knob-effect band between them. Intent vs. render, same language. The user never has to read raw funscript JSON to know what they did.

---

## 5. State & integration contract

`App` (in `forge-views.jsx`) owns the single source of truth:
```js
feel      // {intensity, pace, wildness, sharpness, depth, focus}  — 0..1
passages  // [{id, shape, from, to, lo, hi, label}]
moments   // [{id, typeId, at, dur, amount}]
playhead  // 0..1, shared animation
// per-tab UI: lensId (Voicing), armed/selId (Moments), benchId/knobMap/stamped (Polish)
```
Views are pure props-in; editing a Feel dial in Voicing re-derives Moments and re-forges every Polish station live, because there is exactly one model.

**To wire to the real engine:** replace the synth functions in `forge-engine.js` with calls into the production analyzer/derivation, keeping the same signatures (`sampleIntent`, `applyMoments`, `buildDevice` returning `0..1` arrays). The UI depends only on those shapes. The `.feel.yml` authored values map directly to `feel` + `passages` + `moments`.

---

## 6. Naming decisions made in this pass
- **Channels → Voicing** (the tab is "how we derive every output", not the spatial layer only).
- **Events → Moments** (punctual things dropped *in the moment* while watching).
- **Polish** keeps device-specificity; it was always going to re-introduce it, so Channels was freed to be device-agnostic.

## 7. Caveats
- Prototype math is illustrative, not production DSP (see `scripts/README.md`).
- **Stamp** toggles state; it does not write files.
- Loads React/Babel from CDN — needs network on first open. For a fully offline copy, bundle to a self-contained file.
- The non-active tabs in the strip (Library, Project, Analysis, …) are chrome only; Voicing / Moments / Polish are live.
