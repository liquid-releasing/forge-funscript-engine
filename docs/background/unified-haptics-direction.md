# Unified Multi-Device Haptics — Direction Notes

**Status:** Thinking doc (not a spec). Exploratory. Final build spec is **deliberately deferred** — not being finalized tonight.
**Companions:** [funscriptforge.spec.md](funscriptforge.spec.md) (host), [funscript.spec.md](funscript.spec.md) (e-stim generator).

> Purpose: hold the open question — *what can multi-device haptics actually be?* — and the realizations that point past edger477's model, so the eventual spec is built on a unified idea rather than a port of his approach.

---

## The core realization

edger477's tool was our **starting point**, not our destination. Two decisions tonight loosen us from his model:

1. **Develop device output at the end (Polish tab), from the model + sidecars** — not by pre-building a bucket of funscripts up front. (See [funscriptforge.spec.md §4](funscriptforge.spec.md).)
2. **Funscript is a render target, not the working format** — the internal representation can be whatever we can render. (See [funscript.spec.md §3](funscript.spec.md).)

Together these mean: **we don't have to do what edger does.** Because nothing device-specific is committed until polish, we're free to define our *own* unified model of intent and let each device realize it — rather than emitting edger-shaped channel buckets and hoping the player sorts it out.

---

## The open question to think through

**What is multi-device haptics, unified?**

The goal (from [funscriptforge.spec.md §4A](funscriptforge.spec.md)): one user-facing abstraction spanning **e-stim + mechanical + haptics**, where the user defines a **named set of complementary features** and applies it to selected devices — realized per-device at polish.

What needs working out:
- **A unified naming/vocabulary.** e-stim has edger's "characters" (Gentle, Reactive, Scene Builder, Unpredictable, Balanced) and our "tones." Haptics/mechanical have no shared vocabulary yet. What is the *one* set of names that means something on a vibe, a stim rig, a 6-axis stroker, a shaker, a vest?
- **A unified influence model.** Today's influences — tone (per chapter), character (per chapter), cross-chapter ramp, events (local touch-ups) — were shaped around e-stim. **Do they generalize?** The bet: define influences on e-stim *and* haptics "in a similar way" so the same controls drive both. Which influences are truly device-agnostic, and which are e-stim-only?
- **What each device can actually express.** A unified intent only works if every profile can map it to *something* sensible (or gracefully ignore it). Need the expressive vocabulary of each target: vibe (intensity/patterns), e-stim (position/intensity/pulse), stroker (axes), shaker (low-freq amplitude), bHaptics (per-actuator).

**The payoff:** if the unified intent + influence model is right, e-stim and haptics share one authoring experience, and adding a device is "teach a profile how to realize the named features" — no per-device authoring, no edger-style buckets.

---

## The shape of the abstraction (working)

The reframe: **don't reproduce edger's e-stim channels — name the multi-axis _ideas_ underneath them, abstracted across devices.** Each idea is a *dimension of intent*; every device realizes the ones it can and ignores the rest. We **define what we want to accomplish**, then **produce outputs tailored to the device, constrained at the end** (polish + safety).

**Starter set of cross-device intent dimensions** (to refine):

| Intent dimension | What it means | e-stim | mechanical (OSR/SR6) | haptics (vibe/vest/shaker) |
|---|---|---|---|---|
| **Intensity arc** | "loud, building across a long movie" — long-range rise/fall | volume + cross-chapter ramp | stroke energy / depth | amplitude build |
| **Spatial movement** | move the sensation around / rotate | alpha / beta position | **twist** (and roll/pitch) | actuator location / channel pan |
| **Pace / beat** | how fast, on-beat emphasis | pulse_frequency | stroke speed | pulse/vibration rate |
| **Accent / touch-up** | local emphasis (events) | local volume/pulse nudge | a sharper stroke | a buzz hit |
| **Texture / character** | the "feel" preset | character (lift style) | stroke shape | vibration pattern |

The key insights the user named:
- **Intensity build is universal** — the long-arc "building across a movie" idea is the *same* on haptics and e-stim; only the realization differs.
- **Twist ≈ alpha/beta** — a mechanical axis (SR6 twist) and an e-stim positioning pair are two realizations of one **spatial-movement** dimension.

If the dimensions are right, authoring is: pick intent dimensions + their shape → at polish, each device profile maps the dimensions it supports → constrain to device limits. No per-device authoring; no edger-style channel buckets.

> Watch for: dimensions that *don't* generalize (pure e-stim physics) — keep those as device-specific extras, not forced onto every device.

---

## What we are NOT deciding tonight

- The unified naming (edger's "characters" vs our "tones" vs a new term) — TBD.
- Whether tones are absorbed into, or compose with, unified feature sets.
- The events composition rule, the ramp-slicing math, the handoff contract.
- The e-stim build spec scope (self-contained vs host-coupled) — pending a separate decision.

---

## Prompts for the next thinking session

1. List the influences we have (tone, character, ramp, events) and mark each: **device-agnostic** or **e-stim-specific**? The agnostic ones are the seed of the unified model.
2. For each device class (vibe, e-stim, stroker, shaker, vest), write one line: *what can it express?* Find the common denominator and the per-device extras.
3. Pick a working name for the unified "named feature set" concept — even a placeholder unblocks design.
4. Sketch one example: a single named feature set ("Tease") and what it becomes on a Lovense vibe vs. e-stim vs. SR6. If that mapping feels natural, the abstraction is probably right.
