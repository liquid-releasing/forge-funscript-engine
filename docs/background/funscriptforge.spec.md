# FunscriptForge — Next-Version Multi-Device Architecture

**Status:** Draft v0.1
**Scope:** How FunscriptForge (our own post-processor) drives multiple device families in the next version, and how it hands motion off to device generators — including the clean-room e-stim generator specified in [funscript.spec.md](funscript.spec.md).

> Companion doc: **[funscript.spec.md](funscript.spec.md)** specifies the *e-stim channel generator* (the clean-room replacement for edger477's funscript-tools). **This** doc specifies the *host*: structure analysis, tones, and device profiles that sit above any single device.

---

## 1. What FunscriptForge is (today)

A **local, private post-processor**: it analyzes a funscript's motion and produces device-optimized output. Pipeline (real, current):

1. **Assess** — structural analysis: phases → cycles → patterns → **phrases** → BPM transitions. Emits JSON.
2. **Transform** — BPM-threshold baseline using named transforms.
3. **Customize** — window-based fine-tuning via behavioral tags.

CLI (current): `assess`, `transform`, `customize`, `pipeline`, `phrase-transform`, `export-plan`, `meta`.
Projects persist as `.forge`; `export-plan` writes device-specific subdirectories with an embedded `_forge_log` for reproducibility. No account, no cloud, no telemetry.

Devices supported **today:** Handy (stroker), OSR2 (stroker), E-Stim FOC, E-Stim Stereo, Generic/Intiface.
E-stim output today is produced by integrating with **edger477/funscript-tools** (alpha/beta/pulse_frequency). The next version replaces that dependency with our own clean-room generator (see companion doc) — see [§6](#6-handoff-to-device-generators-greenfield).

### Design stance: everything in v1, behind an easy button

**Why v1 is feature-heavy.** We are deliberately **putting the full feature set into v1** — chapters, lenses, transforms, ramp, events, multi-device, native playback. The motivation is practical: the **existing UIs (edger's tool + restim) are too hard to wire up and make playable.** Replacing that friction means doing a lot at once rather than shipping a thin slice.

**The easy button (the mitigation).** We're aware this **risks going overboard.** The counterbalance is a **one-click "reasonable defaults"** path: the user can ignore every control and get a sensible result. Depth is **opt-in** — power users dig into chapters/characters/transforms; everyone else presses the easy button. This is a load-bearing design requirement, not a nicety: it's what keeps the feature-heavy v1 approachable.

---

## 2. Chapters and phrases (two distinct layers)

FunscriptForge segments motion at **two granularities**:

- **Chapter** — the **editing unit**: a way to slice a large funscript so a user can edit long plays in **3–5 minute chunks** instead of wrestling a one-hour script. Editing is done *to a chapter* (the smaller, navigable piece). **Tone is assigned per chapter** (see §3).
  - **Boundary detection (a FunscriptForge invention):** chapter boundaries are chosen by **audio analysis** — detecting pauses or changes in the accompanying audio (song transitions, scene/track changes, silences). The cut points follow the *audio's* structure, which is what makes the 3–5 min chunks feel natural. **Planned:** add **video detection** as a second boundary signal (scene cuts, motion changes).
- **Patterns, phrases, stanzas — three _different lenses_ on the same script** (a FunscriptForge invention). They are **not a strict nesting**; each is an independent way to select and operate on motion *above the stroke level*:
  - **Pattern** — a way to build **collections** of similar motion. Patterns are the grouping primitive: recurring motion gathered into a collection you can edit as one thing.
  - **Phrase** — a motion segment determined by **our proprietary detection algorithm** (the one developed with Claude's help). Not a simple "same pattern + same BPM" rule — it's the algorithm's notion of a coherent phrase.
  - **Stanza** — a **metrical lens**: fixed-length windows of **32 or 16 beats**, aligned to musical meter independent of motion content. Because stanzas are beat-aligned, they let a transform target a **specific beat position** — e.g. emphasize the **downbeat** or the **upbeat** across the window.

  **The overlap is intentional.** These lenses deliberately cover the same material in different ways — giving the user multiple independent handles to apply transforms (group by motion similarity *or* by detected phrase *or* by beat window). The **chapter** is the editing chunk; *within* it, the user freely switches lenses depending on what kind of edit they want.

**Core philosophy — edit patterns, not strokes.** The whole premise of FunscriptForge is to **edit patterns and groups of similar patterns**, never individual strokes. The lenses exist so the user operates on recurring structure at a meaningful scale.

**The lenses are the scopes for _transforms_.** A selected pattern / phrase / stanza is the handle to **apply a transform** (another FunscriptForge invention): change the **beats** (timing/BPM), the **amplitude** (intensity/depth), or other properties — once, to the whole selection, instead of stroke-by-stroke. Select a pattern collection → retime it; select a stanza → raise its amplitude; etc. This is the `transform` / `phrase-transform` layer of the pipeline (§1, §5).

**Behavioral tags (10), per phrase:** stingy, giggle, plateau, drift, half-stroke, drone, lazy, frantic, ramp, ambient. These drive `customize` fine-tuning.

---

## 3. Tones

**Tones** are global moods applied **per phrase**, ordered by intensity:

```
Tender → Build → Tease → Edge → Climax → Dominant
```

Each tone exposes 2–4 contextual sliders and offers dual suggestions ("Best match" / "Most variety"), with live preview on `phrase-transform`.

**Tones as a device-command subset.** In the next version, a tone maps to a **subset of the commands a device supports** — i.e. the tone is the device-agnostic intent, and each device profile (§4) realizes that intent using whatever subset of its command vocabulary it has. The same "Edge" tone becomes different concrete commands on a Lovense vibe vs. an e-stim rig vs. a shaker.

**E-stim characters (eTransforms, 5).** A **character is a named parameter set** (edger477's term — he varies sections by different params). FunscriptForge **assigns a character _per chapter_**, which is the unit at which the e-stim channels are generated — phrases/phases are too small to vary character over (see [funscript.spec.md §6](funscript.spec.md)). Each character maps onto the e-stim generator's alpha/beta "lift style" (companion doc §7.2):

| Character | Sensation | Maps to (e-stim generator) |
|---|---|---|
| Gentle | soft, slow-building | low radius, gentle ramp |
| Reactive | sharp, tracks action closely | speed-driven radius, tight tracking |
| Scene Builder | gradual build over time | ramp-dominant intensity |
| Unpredictable | random direction changes | 0–360 lift with random flips |
| Balanced | middle-ground default | default lift style |

---

## 3A. What a chapter carries: tone, cross-chapter ramp, events

A chapter is not just an editing window — it's where influences are attached. Three layers stack onto the motion:

**1. Tone** (per chapter) — the mood, realized across the chapter's phrases (§3).

**2. Ramp — assigned _across_ chapters (feature in progress).** Ramp is a **long-arc intensity envelope that spans multiple chapters**, not a build local to one. The user lays a ramp over a sequence of chapters, and **each chapter inherits its slice** of that global envelope. Per-segment intensity (from motion/speed) then sits *on top of* the chapter's ramp level. This is what gives a long multi-chapter play a coherent overall arc instead of independent, equally-intense chunks.

A worked shape we're building: **the ramp grows from the start to the middle, then ramps down from the middle to the end** (a rise-to-peak-then-fall arc across all chapters) — **more control than edger provides** (his ramp is whole-funscript, not a shaped multi-chapter arc).

**3. Events — localized character touch-ups (tentative concept, naming may change).** An event lets the user **influence a small section** (sub-chapter) — a **touch-up of the overall character**, not a separate signal or channel. Events **only influence the main funscript**: they locally nudge the character the base pipeline would otherwise produce (e.g. accent, hold/pause, surge over a short span).

**Scope difference vs edger477:**
- **Ours** — an event touches up the character **of the chapter** (chapter-scoped, matching our per-chapter generation, §3 / [funscript.spec.md §6](funscript.spec.md)).
- **Edger's** — an event touches up the **entire funscript** (global).

> **Status:** the *events* model is provisional — may be restructured or renamed. Open items: event types, point vs ranged span, and how a touch-up composes with the chapter's character/ramp (additive nudge vs scaling). Tracked in §8.

**Multi-phase output is organized per chapter.** The multi-phase e-stim channels (alpha/beta/pulse/…) are synthesized **per chapter** (using that chapter's tone/character and its ramp slice), then stitched across chapter seams — see [funscript.spec.md §6](funscript.spec.md). So "multi-phase funscript assigned to chapters" is the organizing principle on the e-stim side.

---

## 4. Device profiles (multi-device)

One engine, many devices. A **profile** maps the phrase/tone/motion intent onto a concrete device's channels, command subset, and safe ranges. **No device specifics live above the profile layer** — adding a device = adding a profile.

### Device selection happens at the end (the Polish tab)

**The user builds a device-agnostic project, then shapes for the device last.** Device selection lives on the **Polish tab** — the final step. The user spends the session choosing *details* (chapters, characters, transforms, ramp, events) that define an **overall, device-agnostic result**; only at the very end does **one polish pass shape it for the selected device**, taking **all the sidecars into account** (sidecars = the accompanying influence data: ramp, events, tone/character, transforms).

Why this matters:
- **The user never hand-builds device-specific funscripts to satisfy a feature.** They express intent once; the device shaping is automatic at the end.
- **We don't pre-build a bucket of funscripts like edger does.** Edger emits a dozen+ files up front; **we develop the device-shaped output at polish time** from the model + sidecars. The emit-superset set (below) is *produced at polish/export*, not maintained as files throughout.
- **One render now, for visualization.** During editing we render a **single** representative output so the user can *see what their choices mean*. It's a live preview of intent, not the final device bundle.

**Consequence — format wiggle room.** Because the real device output is generated only at polish, the **internal representation can be whatever we want, as long as (a) we can render it for preview/playback and (b) the final result renders as funscripts** for export. Funscript is a **render target**, not the working format. This gives the e-stim generator latitude in its internal model — see [funscript.spec.md §3/§6](funscript.spec.md).

**Emit-superset, consume-subset (still the rule at export).** When we do render out, a profile **emits the full set of tracks for its device class; the player/device uses whatever it can** and ignores the rest. This mirrors edger477's e-stim approach — he emits a dozen+ funscripts for 4-phase and **restim figures out which ones to play**. Same for mechanical: **SR6 has 6 axes, so we print all 6**; a lesser device (e.g. an OSR2 with fewer axes) simply consumes the subset it supports. The generator never needs to know exactly what's downstream — it produces the complete set, and selection happens at the device/player.

**The shared "1 → many" pattern.** Two of the profiles take a single 1‑D input funscript and **lift it into multiple coordinated tracks**:
- **E‑stim** — via the funscript‑tools‑style multi‑channel generator (alpha/beta/volume/pulse_*/frequency). This is the "deeper multi‑funscript player" path; see [funscript.spec.md](funscript.spec.md).
- **OSR2 / SR6 multi‑axis strokers** — a **multi‑axis funscript set** (one track per physical axis), a generation approach **invented by Claude + the user**. Same lift concept as e‑stim, but a **different target**: the tracks drive real mechanical axes, not stim channels.

The two are analogous in structure (1 input → many synchronized funscripts) but unrelated in axis meaning — alpha/beta is electrode position; OSR/SR6 axes are physical motion.

**Today:** Handy, OSR2, E-Stim FOC, E-Stim Stereo, Generic/Intiface.
**Planned (next version):** **bHaptics**, **shaker**, **Lovense** — and likely others.

| Profile | Class | Channels / tracks | Notes |
|---|---|---|---|
| Handy | single-axis stroker | position (1-D, the source domain) | refine/passthrough |
| **OSR2 / SR6** | **multi-axis stroker** | stroke + surge/sway/twist/roll/pitch (multi-axis funscript set) | our + Claude's invention; 1→many lift, different target than e-stim |
| E-Stim FOC / Stereo | e-stim | alpha, beta, volume, pulse_*, frequency | via companion-doc generator (funscript-tools-style) |
| Generic / Intiface | haptic hub | Buttplug protocol commands | broad device coverage |
| Lovense | vibe | vibration intensity (subset) | *planned* |
| bHaptics | vest/wearable | per-actuator intensity (subset) | *planned* |
| shaker | transducer | low-freq amplitude (subset) | *planned* |

Each profile declares: the channels/tracks it emits, each channel's valid range + clamp, the tone→command-subset mapping, and **device-specific safety limits**.

---

## 4A. Toward unified feature sets (design direction — evolving)

> **Active thinking:** this direction is being worked out in [unified-haptics-direction.md](unified-haptics-direction.md) — the final spec is deferred until the unified naming + influence model is settled.

The north star: **unify e-stim, mechanical (OSR/SR6), and haptics under one user-facing idea.** Instead of thinking per-device, the user defines a **named set of complementary features** and **applies it to the selected devices** as a single concept — expressed once, realized per device by each profile (§4).

How it relates to what exists today:
- **edger477's "characters"** (Gentle, Reactive, Scene Builder, Unpredictable, Balanced) are the **e-stim-specific** version of this idea — a named feel applied to the stim channels.
- **Tones** (§3) are already device-agnostic moods.
- The unified concept **generalizes both**: one named feature set that spans *all* device classes, with each profile mapping it onto its own channels/axes/commands. The profile layer (§4) is already the mechanism that makes this possible — this section is about the **user-facing abstraction** above it.

**Status / open:**
- **E-stim was the first use case**; the abstraction is being **worked out gradually** and is not finalized.
- **Naming is undecided.** edger used "**characters**" for e-stim; the newest FunscriptForge version has **not yet landed on a name** for the unified, cross-device concept (TBD).
- Open: how this relates to / absorbs **tones** — are tones a kind of unified feature set, or a separate axis that composes with it?

---

## 5. Pipeline (next version)

```
input.funscript
   │
   ▼
[chapterize] → audio analysis → 3–5 min editing chunks (user-navigable; video detection planned)
   │
   ▼
[assess]   → phrases within each chapter (BPM, pattern, tags)
   │
   ▼
[tone]     → assign a tone per chapter (Tender…Dominant), realized across its phrases
   │
   ▼
[transform/customize] → device-agnostic motion intent + sidecars (ramp, events, character)
   │
   │   ← live single-output render here, for the user to VISUALIZE choices
   ▼
[POLISH tab] → device selected HERE (last step); develop the device-shaped output
   │            now, from the model + ALL sidecars (no pre-built bucket)
   ├─ stroker   → position track
   ├─ e-stim    → alpha/beta/volume/pulse_*  (companion doc)
   ├─ Intiface  → Buttplug commands
   └─ Lovense / bHaptics / shaker (planned)
   │
   ▼
render → ForgePlayer (native) OR funscript export folder (+ _forge_log)
```

**Ship target.** On **ship**, the full track set (per emit-superset, §4) is written to a **folder the user — and the player — recognizes**: a known export location using the filenames the player auto-discovers (restim's channel names; multi-axis names for SR6). The player then consumes the subset it supports. *(Open detail: exact folder convention per device.)*

---

## 5B. ForgePlayer — native playback from metadata

FunscriptForge has its own player, **ForgePlayer**, which plays **directly from the project metadata** — the `.forge` model (chapters, tones, transforms, the structural lenses, cross-chapter ramp, events, per-device intent). At play time it **takes all that metadata, selects what it needs for the target device(s), and plays that**. It does **not** read exported funscript files.

**The user might never see a funscript.** Funscripts are an **export/interop format** for *third-party* players (restim, MultiFunPlayer, …) — produced only when shipping to an external tool. The native path is **metadata-driven**, with no funscript round-trip.

Two playback paths:
- **External players** → emit the funscript superset → ship to a recognized folder (§4, §5) → player consumes its subset.
- **ForgePlayer (native)** → read metadata → select per device → play. No funscript surfaced.

This makes the in-process handoff (§6 option A) the natural choice for ForgePlayer: e-stim/mechanical/haptic generation runs **in-memory at play time** rather than writing files.

**Why keep both paths.** They serve different goals:
- **Funscript export = freedom / no lock-in.** It lets users drive their devices with **existing third-party tools, independent of FunscriptForge.** This is the open-interop escape hatch — we never trap a user's work inside our format.
- **Native player(s) = better UX.** The existing tools are, in practice, **hard to use** — which is the reason we built **our own player(s)** (ForgePlayer, and related controllers). The native path trades third-party portability for a smoother, metadata-driven experience.

Neither path is "the" path: export serves portability, ForgePlayer serves ease of use.

---

## 6. Handoff to device generators (greenfield)

**Current state:** e-stim output is produced by handing off to funscript-tools. **The exact handoff is undefined for the next version and we are free to design it however we want.** It is not constrained by the current integration.

Options to decide later (no commitment yet):
- **(A) In-process library call** — the e-stim generator becomes a module FunscriptForge calls directly with phrase/tone/motion data. Cleanest; no file round-trip.
- **(B) Structured intermediate** — FunscriptForge writes a normalized "motion + tone + phrase" JSON; each device generator consumes it. Decouples host from generators; matches the existing `assess`→JSON style.
- **(C) Per-device subprocess/CLI** — `export-plan` shells out to a generator CLI per device. Mirrors today's funscript-tools integration; easiest migration.

Recommendation to evaluate: **(B) as the contract, (A) as the e-stim implementation** — a stable intermediate keeps profiles independent while letting the e-stim path stay in-process. Decide in design review.

---

## 7. Ownership & licensing (cross-ref)

- **FunscriptForge** is ours ([liquid-releasing/funscriptforge](https://github.com/liquid-releasing/funscriptforge)).
- The **CLI in edger477/funscript-tools** is **your contribution**, authored under **liquid-releasing** — it was the *entire* CLI (none existed before); intent was to make his code usable as a pipeline. The maintainer may have added more since. You retain copyright in what you wrote → reusable by us. Everything else in that repo is **all rights reserved** (no license) → read-only. Full stance in [funscript.spec.md §2](funscript.spec.md).

---

## 8. Open questions

1. **Structural units** — *resolved:* chapter = coarse 3–5 min editing chunk carrying a tone, boundaries from **audio analysis** (pauses/song changes; video detection planned). Within a chapter, **patterns / phrases / stanzas are three overlapping lenses** (not a nesting): pattern = similar-motion collections; phrase = proprietary-algorithm segment; stanza = 32/16-beat metrical window (enables downbeat/upbeat emphasis). Overlap between lenses is **intentional** (multiple handles for transforms), not a conflict to resolve.
2. **Tone→command-subset tables** — define the concrete mapping per planned device (Lovense, bHaptics, shaker).
3. **Handoff contract (§6)** — pick A/B/C before building the e-stim generator, so its input shape is fixed.
4. **Device priority** — which of bHaptics / shaker / Lovense ships first in the next version?
5. **Per-device safety ranges** — gather safe intensity/range limits for each planned device.
6. **Events model (provisional)** — finalize the concept: event types, point vs ranged, and how they compose with tone/ramp (add / override / multiply). Name may change.
7. **Cross-chapter ramp** — how the user lays/edits the multi-chapter ramp envelope, and how a chapter's slice is computed (linear span, keyframed, per-chapter targets).

---

### Sources consulted (facts only)
- [liquid-releasing/funscriptforge](https://github.com/liquid-releasing/funscriptforge) — pipeline, phrases, tones, behavioral tags, e-stim characters, device list, CLI.
