#!/usr/bin/env python3
"""
Unified Forge — Phase-1 golden fixture generator + reference analyzer.

Generates the input .funscript fixtures in fixtures/ and computes goldens.json:
the constant-free base signals (f, depth, CV_D, CV_A, CF, autocorr) per the
spec §3 formulas, plus the relational invariants the test suite asserts.

This is TEST TOOLING — it implements §3 to (a) produce deterministic fixtures
and (b) pin reference signals. The production engine reimplements §3; the suite
checks production against these goldens. Run:  python make_fixtures.py
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
os.makedirs(FIX, exist_ok=True)

# ───────────────────────── fixture builders ─────────────────────────
def triangle(period_ms, lo, hi, dur_ms, t0=0):
    """Extremes-only points → linear interp = triangle wave (smooth stroke)."""
    acts, t, up = [], t0, True
    half = period_ms / 2
    while t <= t0 + dur_ms:
        acts.append({"at": int(t), "pos": int(hi if up else lo)})
        up = not up
        t += half
    return acts

def dwell_snap(hold_ms, snap_ms, lo, hi, dur_ms):
    """Hold at an extreme then snap to the other → high velocity crest factor."""
    acts, t, up = [], 0, True
    while t <= dur_ms:
        cur = hi if up else lo
        acts.append({"at": int(t), "pos": int(cur)})       # arrive
        acts.append({"at": int(t + hold_ms), "pos": int(cur)})  # dwell
        t += hold_ms + snap_ms
        up = not up
    return acts

def growing(period_ms, center, half0, half1, dur_ms):
    """Triangle whose amplitude grows linearly center±half0 → center±half1."""
    acts, t, up = [], 0, True
    half = period_ms / 2
    n = max(1, int(dur_ms / half))
    for i in range(n + 1):
        frac = i / n
        h = half0 + (half1 - half0) * frac
        acts.append({"at": int(i * half), "pos": int(round(center + (h if up else -h)))})
        up = not up
    return acts

# hand-authored irregular stroke (varied intervals AND amplitudes)
IRREGULAR = [(0,10),(230,85),(470,40),(540,95),(900,20),(1010,70),(1400,5),
             (1480,100),(1950,55),(2060,15),(2500,90),(2700,35),(3120,75),
             (3200,12),(3680,88),(3900,30)]

def max_speed():
    acts = []
    for i in range(0, 60):
        acts.append({"at": i, "pos": 0 if i % 2 == 0 else 100})
    return acts

FIXTURES = {
    # ── behavioral fixtures (relational goldens) ──
    "slow-smooth":  triangle(2000, 0, 100, 12000),     # 0.5 Hz, full depth, triangle
    "fast-smooth":  triangle(334, 0, 100, 6000),       # ~3 Hz, full depth, triangle
    "shallow-fast": triangle(334, 40, 60, 6000),       # ~3 Hz, depth 0.2
    "sharp-snap":   dwell_snap(400, 40, 0, 100, 7000), # dwell + 40ms snaps
    "irregular":    [{"at": t, "pos": p} for t, p in IRREGULAR],
    "build-ramp":   growing(500, 50, 5, 50, 8000),     # amplitude grows over window
    # ── edge / fuzz fixtures (robustness goldens) ──
    "empty":        [],
    "single-point": [{"at": 0, "pos": 50}],
    "flat":         [{"at": 0, "pos": 50}, {"at": 5000, "pos": 50}],
    "huge-gap":     [{"at": 0, "pos": 0}, {"at": 3600000, "pos": 100}],
    "monotonic":    [{"at": i*1000, "pos": i*20} for i in range(6)],
    "max-speed":    max_speed(),
}

def write_funscript(name, actions):
    doc = {"version": "1.0", "inverted": False, "range": 100, "actions": actions}
    with open(os.path.join(FIX, name + ".funscript"), "w") as f:
        json.dump(doc, f, indent=2)

# ───────────────────────── reference analyzer (§3) ─────────────────────────
DT_MS = 20.0
DT_S = DT_MS / 1000.0
P_MIN = 0.05

def resample(actions):
    if len(actions) < 2:
        return [], 0.0
    t0, t1 = actions[0]["at"], actions[-1]["at"]
    if t1 <= t0:
        return [actions[0]["pos"]/100.0], 0.0
    n = int((t1 - t0) / DT_MS) + 1
    xs, j = [], 0
    for i in range(n):
        t = t0 + i * DT_MS
        while j < len(actions) - 2 and actions[j+1]["at"] < t:
            j += 1
        a, b = actions[j], actions[j+1]
        span = b["at"] - a["at"]
        f = 0.0 if span <= 0 else max(0.0, min(1.0, (t - a["at"]) / span))
        xs.append((a["pos"] + (b["pos"] - a["pos"]) * f) / 100.0)
    return xs, (t1 - t0) / 1000.0

def diff(arr):
    return [(arr[i] - arr[i-1]) / DT_S for i in range(1, len(arr))]

def reversals(actions):
    """Turning points from the sparse action list, prominence-filtered.
    Collapses dwell plateaus (runs of equal pos) so a hold-then-snap still
    registers its reversals."""
    raw = [(a["at"], a["pos"]/100.0) for a in actions]
    pts = [raw[0]] if raw else []          # collapse equal-consecutive values
    for p in raw[1:]:
        if p[1] != pts[-1][1]:
            pts.append(p)
    if len(pts) < 3:
        return []
    ext = [pts[0]]
    for i in range(1, len(pts)-1):
        prev, cur, nxt = pts[i-1][1], pts[i][1], pts[i+1][1]
        if (cur - prev) * (nxt - cur) < 0:  # sign change of slope
            if abs(cur - ext[-1][1]) >= P_MIN:
                ext.append(pts[i])
    if abs(pts[-1][1] - ext[-1][1]) >= P_MIN:
        ext.append(pts[-1])
    return ext

def mean(a): return sum(a)/len(a) if a else 0.0
def std(a):
    if len(a) < 2: return 0.0
    m = mean(a); return math.sqrt(sum((x-m)**2 for x in a)/len(a))
def rms(a): return math.sqrt(sum(x*x for x in a)/len(a)) if a else 0.0
def pctl(a, q):
    if not a: return 0.0
    s = sorted(a); k = (len(s)-1)*q
    lo = int(math.floor(k)); hi = int(math.ceil(k))
    return s[lo] if lo == hi else s[lo]*(hi-k)+s[hi]*(k-lo)

def autocorr_at(xs, lag):
    if lag <= 0 or lag >= len(xs): return 0.0
    m = mean(xs); denom = sum((x-m)**2 for x in xs)
    if denom == 0: return 0.0
    num = sum((xs[i]-m)*(xs[i+lag]-m) for i in range(len(xs)-lag))
    return num/denom

def analyze(actions):
    xs, T = resample(actions)
    out = {"n_samples": len(xs), "T_s": round(T, 3)}
    if len(xs) < 2:
        out.update(f_hz=0.0, depth=0.0, cv_d=0.0, cv_a=0.0, crest=0.0,
                   v_rms=0.0, autocorr=0.0)
        return out
    v = diff(xs); a = diff(v)
    ext = reversals(actions)
    amps = [abs(ext[i+1][1]-ext[i][1]) for i in range(len(ext)-1)]
    durs = [(ext[i+1][0]-ext[i][0])/1000.0 for i in range(len(ext)-1)]
    K = len(ext)
    f = (K-1)/(2*T) if (T > 0 and K >= 2) else 0.0
    v_rms = rms(v)
    crest = (pctl([abs(x) for x in v], 0.95)/v_rms) if v_rms > 0 else 0.0
    med_amp = sorted(amps)[len(amps)//2] if amps else max(xs)-min(xs)
    lag = round((1.0/f)/DT_S) if f > 0 else 0
    out.update(
        f_hz=round(f, 4),
        depth=round(med_amp, 4),
        cv_d=round(std(durs)/mean(durs), 4) if mean(durs) > 0 else 0.0,
        cv_a=round(std(amps)/mean(amps), 4) if mean(amps) > 0 else 0.0,
        crest=round(crest, 4),
        v_rms=round(v_rms, 4),
        autocorr=round(autocorr_at(xs, lag), 4) if lag > 0 else 0.0,
    )
    return out

# ───────────────────────── emit ─────────────────────────
goldens = {}
for name, acts in FIXTURES.items():
    write_funscript(name, acts)
    goldens[name] = {"n_actions": len(acts), "signals": analyze(acts)}

# relational invariants — robust to constant calibration (assert these in the suite)
INVARIANTS = [
    "f_hz(fast-smooth)        >  f_hz(slow-smooth)        # Pace",
    "depth(fast-smooth)       >  depth(shallow-fast)      # Depth",
    "crest(sharp-snap)        >  crest(slow-smooth)       # Sharpness",
    "cv_a(irregular)          >  cv_a(slow-smooth)        # Wildness (amplitude)",
    "cv_d(irregular)          >  cv_d(slow-smooth)        # Wildness (timing)",
    "autocorr(slow-smooth)    >  autocorr(irregular)      # Focus",
    "v_rms(fast-smooth)       >  v_rms(slow-smooth)       # Intensity (motion energy)",
]
INVARIANT_CHECKS = [
    goldens["fast-smooth"]["signals"]["f_hz"]   > goldens["slow-smooth"]["signals"]["f_hz"],
    goldens["fast-smooth"]["signals"]["depth"]  > goldens["shallow-fast"]["signals"]["depth"],
    goldens["sharp-snap"]["signals"]["crest"]   > goldens["slow-smooth"]["signals"]["crest"],
    goldens["irregular"]["signals"]["cv_a"]     > goldens["slow-smooth"]["signals"]["cv_a"],
    goldens["irregular"]["signals"]["cv_d"]     > goldens["slow-smooth"]["signals"]["cv_d"],
    goldens["slow-smooth"]["signals"]["autocorr"] > goldens["irregular"]["signals"]["autocorr"],
    goldens["fast-smooth"]["signals"]["v_rms"]  > goldens["slow-smooth"]["signals"]["v_rms"],
]

manifest = {
    "_comment": "Constant-free reference signals per spec §3. Dial VALUES depend on "
                "calibration constants; assert the relational invariants, not absolutes.",
    "dt_ms": DT_MS, "p_min": P_MIN,
    "fixtures": goldens,
    "invariants": INVARIANTS,
    "invariants_hold_in_reference": INVARIANT_CHECKS,
}
with open(os.path.join(HERE, "goldens.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Wrote {len(FIXTURES)} fixtures to {FIX}")
print(f"Invariants hold in reference: {all(INVARIANT_CHECKS)} {INVARIANT_CHECKS}")
for nm in ("slow-smooth","fast-smooth","shallow-fast","sharp-snap","irregular"):
    print(f"  {nm:13s} {goldens[nm]['signals']}")
