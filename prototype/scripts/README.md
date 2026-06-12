# scripts/

These three files are the **readable source** of `Unified Forge.html`, split by concern. The HTML embeds the same code as two inline `<script type="text/babel">` blocks — it is the single canonical artifact you run and share. These files exist so a developer can read and modify the logic without scrolling through markup.

| File | What it is | Maps to |
|---|---|---|
| `forge-engine.js` | Constants + the signal synth. Pure JS, no JSX. The **unified value model** lives here. | Block A, part 1 |
| `forge-components.jsx` | Shared React components — the single visual grammar (`UnifiedBand`, `Bench`) plus dials, knobs, shell chrome. Ends with `Object.assign(window, …)`. | Block A, part 2 |
| `forge-views.jsx` | `VoicingView` / `MomentsView` / `PolishView` and the `App` that owns shared state and routes tabs. | Block B |

## Load order (if you ever wire them as external files)
React → ReactDOM → Babel, then:
```html
<script type="text/babel" src="scripts/forge-engine.js"></script>
<script type="text/babel" src="scripts/forge-components.jsx"></script>
<script type="text/babel" src="scripts/forge-views.jsx"></script>
```
Engine + components must run before views — views read components off `window`. If you split into separate `<script>` blocks, wrap each in an IIFE (or alias the React hooks once) so the top-level `const { useState … } = React` does not collide across blocks. This is exactly what the single-file HTML does.

## Important
This is a **design prototype**. The synth in `forge-engine.js` (`sampleIntent`, `applyMoments`, `buildDevice`) produces *plausible, illustrative* shapes — it is not the production DSP. Treat it as the spec for *behavior and surface*, not as the shipping signal pipeline. See `../HANDOFF.md` for the real integration contract.
