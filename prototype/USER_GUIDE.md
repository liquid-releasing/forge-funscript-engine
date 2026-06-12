# Unified Forge — User Guide

Open **`Unified Forge.html`** in a browser. You'll land on **Voicing**. Three tabs do the work — **Voicing**, **Moments**, **Polish** — and they all share one signal, so a change in one shows up everywhere.

The big idea: **you describe how it should *feel*, once. The app speaks that same intent to every device.** You don't author "twist" or "vibrate" or an e-stim track separately — those fall out of your feel plus whatever device you're sending to.

---

## The picture (every tab uses it)

The band across the top is your signal, drawn so you can *read* it at a glance:

- **Taller fill** = more intense
- **Tighter ripples** = faster pace
- **Rough, fuzzy edge** = more wildness; smooth band = steady
- **Rising slope** = building over the scene
- **Faint dashed line** = the literal script underneath (the honest version)
- The chapter tints and `ch1…ch21` ticks show where you are; the white line is the playhead.

---

## 1 · Voicing — the bed

This is the continuous feel of the whole scene. Set it once.

**Six dials (Feel):** Intensity, Pace, Wildness, Sharpness, Depth, Focus. Drag any one and the band reshapes instantly. The label on the right (e.g. "Intense · Wild") is a plain-language read of where you are.

**Dynamics:** the slow arcs — how intensity rises and falls across the scene. Hit **+ Add passage** to lay a new arc, pick its shape with the **Build / Release / Swell / Steady** toggle, drag its ceiling to set how high it climbs, and remove it with ✕. (Steady is a flat no-op.) Clear them all and you get a clean empty state.

**Preview lens:** the row of chips (Intent · E-Stim · The Handy · OSR2/SR6 · Lovense · Vacuglide). Click one to see *the same intent* as that device would play it — e-stim rides a fast carrier, a stroker smooths the texture into stroke aggressiveness, multi-axis spreads the energy. You're not authoring per device — just previewing. **Intent** is the pure, device-agnostic version.

> Tip: faint colored blocks on the band are your Moments. You edit those in the next tab.

---

## 2 · Moments — the things you drop in the moment

Some beats deserve a deliberate touch — a hold, a hit, a tease. You add these *while watching*.

1. **Arm** an influence: click one of the chips (Hold, Hit, Swell, Tease, Flutter) — or press its number key **1–5**.
2. **Watch** the playhead move.
3. **Stamp** it: press the armed number key (or click **⌖ Capture here**) at the moment you want it. A labeled window drops onto the band.

Click any window to **select** it; click empty space to **scrub**. The selected moment opens an editor showing:
- **What this produces** — the plain-language breakdown of what it does to the signal (it's honest about being a recipe of feel-ops, not a black box).
- **Adds on top** vs **Replaces** — whether it layers over the bed or gates it down.
- **Strength** and **Width** — tune how strong and how long.

**Set the exact window — Mark begin / end from playhead.** The bar under the band works on the selected moment: park the playhead and hit **Capture** under *Begin* or *End* to pin that edge to the current time; the derived duration updates live. **Snap to beat** locks captures to the beat grid, **Chain** starts the next moment where the last one ended, and **Reset** restores the default length.

Everything you drop here is in the same vocabulary as the bed, so it forges to every device too.

---

## 3 · Polish — forge the device files

This is where the one signal becomes real, device-ready files. Nothing is re-authored here — you're *conditioning* the same intent for each piece of hardware.

- The **pipeline** at the top shows your `Voicing + Moments` source feeding each **station** (E-Stim, The Handy, OSR2/SR6, Lovense, Vacuglide). Each card previews that device's whole track.
- Click a station to bring it **to the bench**. For single-axis devices (Handy, Lovense, Vacuglide) the chart shows the dashed **input** (your intent) vs. the bold **to-device** line, with the difference shaded. For **multi-channel** devices it shows the actual channels as lanes — **E-Stim → alpha / beta / volume**, **OSR2/SR6 → L0 / R0 / R1** — and the output is the channel set (e.g. `estim/ · 3 channels`).
- **Hammer & tongs** (right) — each device has its **own** knobs, tuned to its hardware. For example The Handy shows *Max BPM · Smoothing · Lead-time · Position step*; E-Stim shows *Carrier · Phase balance · Volume floor · Smoothing*; Lovense shows *Intensity floor · Response · Buzz curve · BT latency*. Each carries a one-line plain explanation.
- **Stamp this pass** marks that device forged. Work through the stations; the counter shows how many are stamped.

---

## Why it's built this way

You author **intent**, not device files. Stroke, twist, vibration, pulse, e-stim — those are just the same value-over-time signal landing on different numbers of axes. Describe the feel once; let each device speak it. Polish is the only place you think about specific hardware.

---

### Notes
- This is a **design prototype**: the shapes are illustrative, and **Stamp** doesn't actually write files yet.
- It needs an internet connection the first time you open it (it loads its UI libraries online).
- Your place in the scene and your edits live in the page while it's open.
