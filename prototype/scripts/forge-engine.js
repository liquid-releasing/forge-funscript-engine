/*
 * FunscriptForge · Unified Forge
 * Engine — constants + signal synth (device-agnostic)
 *
 * Block A, part 1. Pure JS (no JSX). The unified value model: feel dials,
 * passages (dynamics), moment influences, device lenses, per-device knob schema
 * (KNOBS) + normalizer (normKnobs), multi-channel maps (CHANNELS/deriveChannels
 * for e-stim alpha/beta/volume + SR6 L0/R0/R1), the synth (sampleIntent /
 * applyMoments) and per-device conditioning (buildDevice).
 * Canonical artifact is "Unified Forge.html" — these files mirror the two
 * inline <script type="text/babel"> blocks it embeds, split for reading.
 */

const { useState, useMemo, useRef, useEffect, useCallback } = React;

/* ───────────────────────── constants ───────────────────────── */
const TOTAL_MS = 2*3600*1000 + 8*60*1000;            // ~2:08:00
const CH_PALETTE = ["#4dabf7","#3ed598","#ff8c42","#c075ff","#ff4b4b","#3ed598","#4dabf7"];
const CHAPTERS = Array.from({length:21},(_,i)=>({
  id:`ch${i+1}`, label:`ch${i+1}`, color:CH_PALETTE[i%CH_PALETTE.length], from:i/21, to:(i+1)/21,
}));

const INTENT = { id:"intent", label:"Intent", sub:"device-agnostic source", hex:"#ff7a3a",
  freqMul:1, smooth:0, tracks:1, fuzz:1.0, file:null, baseSmooth:0,
  note:"What you author. Energy + feel over time, before any device." };

const DEVICES = [
  { id:"estim", label:"E-Stim", name:"E-Stim", sub:"3-phase · export", hex:"#c075ff",
    freqMul:2.6, smooth:0.05, tracks:1, fuzz:0.85, file:"ipzz-125.estim3.funscript", baseSmooth:0.30,
    note:"Carrier rides the feel; volume follows the macro arc. Forged as a .funscript here." },
  { id:"handy", label:"The Handy", name:"The Handy", sub:"1-axis stroker", hex:"#ff8c42",
    freqMul:0.85, smooth:0.55, tracks:1, fuzz:0.25, file:"ipzz-125.handy.funscript", baseSmooth:0.55,
    note:"One axis can't hold all the texture, so wildness is smoothed into stroke aggressiveness." },
  { id:"sr6", label:"OSR2 / SR6", name:"OSR2 / SR6", sub:"TCode multi-axis", hex:"#ffb547",
    freqMul:1.1, smooth:0.2, tracks:3, fuzz:0.7, file:"ipzz-125.sr6.funscript", baseSmooth:0.25,
    note:"More axes = somewhere to put the energy. Wildness spreads onto twist & roll." },
  { id:"lov", label:"Lovense", name:"Lovense", sub:"BT · vibration", hex:"#ff5470",
    freqMul:1.4, smooth:0.4, tracks:1, fuzz:0.45, file:"ipzz-125.lovense.funscript", baseSmooth:0.40,
    note:"A vibrator only has intensity — pace & wildness collapse into one buzz envelope." },
  { id:"vacu", label:"Vacuglide", name:"Vacuglide 2", sub:"Autoblow · 1-axis", hex:"#39d4d4",
    freqMul:1.0, smooth:0.45, tracks:1, fuzz:0.4, file:"ipzz-125.vacuglide.funscript", baseSmooth:0.45,
    note:"Sleeve stroker — moderate range, heavier smoothing keeps the motor honest." },
];
const LENSES = [INTENT, ...DEVICES];
const lensById = id => LENSES.find(l=>l.id===id) || INTENT;
const devById  = id => DEVICES.find(d=>d.id===id) || DEVICES[0];

/* per-device conditioning schema — the bespoke "Hammer & tongs" each station shows */
const KNOBS = {
  estim: { sub:"carrier · phase balance · volume floor", specs:[
    { key:"carrier",  label:"Carrier",       min:0.5, max:1.6, step:0.05, def:1.0,  fmt:v=>v.toFixed(2)+"×", hint:"Speed of the 3-phase carrier riding the feel." },
    { key:"phase",    label:"Phase balance", min:0,   max:1,   step:0.01, def:0.5,  fmt:v=>(v<0.45?"α ":v>0.55?"β ":"·")+Math.round((v-0.5)*200)+"%", hint:"Bias the sensation forward (alpha) ↔ back (beta)." },
    { key:"volume",   label:"Volume floor",  min:0,   max:0.3, step:0.01, def:0.08, fmt:v=>v.toFixed(2), hint:"Minimum so the sensation never fully drops out." },
    { key:"smoothing",label:"Smoothing",     min:0,   max:1,   step:0.01, def:0.30, fmt:v=>v.toFixed(2), hint:"Low-pass on the volume envelope." },
  ]},
  handy: { sub:"BPM ceiling · carriage acceleration", specs:[
    { key:"maxBpm",   label:"Max BPM",       min:60,  max:240, step:5,    def:120,  fmt:v=>v+" bpm", hint:"Softens cycling faster than the carriage can travel." },
    { key:"smoothing",label:"Smoothing",     min:0,   max:1,   step:0.01, def:0.45, fmt:v=>v.toFixed(2), hint:"Low-pass on the position curve. Tames jitter the motor can't track." },
    { key:"lead",     label:"Lead-time",     min:0,   max:120, step:5,    def:60,   fmt:v=>"+"+v+" ms", hint:"Send the command this many ms early to land on the beat." },
    { key:"step",     label:"Position step", min:0.01,max:0.1, step:0.005,def:0.01, fmt:v=>Math.round(v*100)+"%", hint:"Smallest move the carriage bothers with — skips micro-jitter." },
  ]},
  sr6: { sub:"axis spread · range mapping", specs:[
    { key:"spread",   label:"Axis spread",   min:0,   max:1,   step:0.01, def:0.5,  fmt:v=>Math.round(v*100)+"%", hint:"How much energy fans onto twist & roll vs. staying on stroke." },
    { key:"range",    label:"Stroke range",  min:0.3, max:1,   step:0.01, def:0.9,  fmt:v=>Math.round(v*100)+"%", hint:"Depth the main axis uses end-to-end." },
    { key:"smoothing",label:"Smoothing",     min:0,   max:1,   step:0.01, def:0.25, fmt:v=>v.toFixed(2), hint:"Low-pass on every axis." },
    { key:"lead",     label:"Lead-time",     min:0,   max:120, step:5,    def:30,   fmt:v=>"+"+v+" ms", hint:"TCode lead to beat the servo lag." },
  ]},
  lov: { sub:"intensity floor · buzz response", specs:[
    { key:"floor",    label:"Intensity floor",min:0,  max:0.3, step:0.01, def:0.10, fmt:v=>v.toFixed(2), hint:"Vibrators stall below a threshold — keeps the motor spun up." },
    { key:"response", label:"Response",      min:0,   max:1,   step:0.01, def:0.55, fmt:v=>v.toFixed(2), hint:"How fast the buzz tracks the envelope. Slow = creamy, fast = twitchy." },
    { key:"curve",    label:"Buzz curve",    min:0,   max:1,   step:0.01, def:0.5,  fmt:v=>v.toFixed(2), hint:"Maps the signal onto the 0–20 power steps — low-end emphasis ↔ linear." },
    { key:"latency",  label:"BT latency",    min:40,  max:240, step:10,   def:120,  fmt:v=>"+"+v+" ms", hint:"Bluetooth round-trip the command leads by." },
  ]},
  vacu: { sub:"stroke window · motor smoothing", specs:[
    { key:"window",   label:"Stroke window", min:0.3, max:1,   step:0.01, def:0.8,  fmt:v=>Math.round(v*100)+"%", hint:"How much of the sleeve's travel to use." },
    { key:"smoothing",label:"Smoothing",     min:0,   max:1,   step:0.01, def:0.50, fmt:v=>v.toFixed(2), hint:"Heaviest low-pass — the sleeve motor is the slowest of the bunch." },
    { key:"maxBpm",   label:"Max BPM",       min:60,  max:200, step:5,    def:110,  fmt:v=>v+" bpm", hint:"Cap on cycles the sleeve can keep up with." },
    { key:"lead",     label:"Lead-time",     min:0,   max:120, step:5,    def:50,   fmt:v=>"+"+v+" ms", hint:"Command lead for the drive belt." },
  ]},
};
// normalize device-specific knobs → the synth's conditioning {smoothing, quiet, rate, lead}
function normKnobs(devId, k){
  let smoothing = k.smoothing;
  if(smoothing==null && k.response!=null) smoothing = 1 - k.response; // lovense: fast response = less low-pass
  if(smoothing==null) smoothing = 0.3;
  const quiet = (k.volume!=null ? k.volume : (k.floor!=null ? k.floor : 0));
  let rate = 0.06;
  if(k.maxBpm!=null) rate = 0.02 + (k.maxBpm/240)*0.09;
  const lead = (k.lead!=null ? k.lead : (k.latency!=null ? k.latency : 20));
  return { smoothing, quiet, rate, lead };
}
// multi-channel devices reveal their axes in Polish (e-stim → alpha/beta/volume, sr6 → L0/R0/R1)
const CHANNELS = {
  estim: ["alpha","beta","volume"],
  sr6:   ["L0","R0","R1"],
};
const CHANNEL_FILES = {
  estim: ["ipzz-125.alpha.funscript","ipzz-125.beta.funscript","ipzz-125.volume.funscript"],
  sr6:   ["ipzz-125.L0.funscript","ipzz-125.R0.funscript","ipzz-125.R1.funscript"],
};
function deriveChannels(dev, out, feel, n){
  const freq=(6+90*feel.pace)*dev.freqMul;
  if(dev.id==="estim"){
    const alpha=[],beta=[],volume=[];
    for(let i=0;i<n;i++){ const t=i/(n-1);
      volume.push(out[i]);
      alpha.push(Math.max(0,Math.min(1, out[i]*(0.5+0.5*Math.sin(t*freq*2*Math.PI)) )));
      beta.push( Math.max(0,Math.min(1, out[i]*(0.5+0.5*Math.sin(t*freq*2*Math.PI + Math.PI/2)) )));
    }
    return [ {label:"alpha",color:"#c075ff",data:alpha}, {label:"beta",color:"#9b5bff",data:beta}, {label:"volume",color:"#e0a3ff",data:volume} ];
  }
  if(dev.id==="sr6"){
    const L0=out.slice(), R0=[], R1=[];
    for(let i=0;i<n;i++){ R0.push(Math.max(0,0.5+(fbm(i*0.5+3)-0.5)*feel.wildness*1.6)); R1.push(0.5+0.42*Math.sin(i/n*Math.PI*2*(2+8*feel.pace))); }
    return [ {label:"L0 · stroke",color:"#4dabf7",data:L0}, {label:"R0 · twist",color:"#ffb547",data:R0}, {label:"R1 · roll",color:"#ff8c42",data:R1} ];
  }
  return null;
}

/* moment influence types — each decompiles to unified feel-ops */
const INFLUENCES = [
  { id:"hold",   key:"1", name:"Hold",   color:"#4dabf7", combine:"add",     shape:"hold",
    amount:0.30, dur:0.020,
    produces:["Freeze pace → near 0 over the window","Hold intensity at the bed's level, +volume","Add a fine buzz so it doesn't read as dead"] },
  { id:"hit",    key:"2", name:"Hit",    color:"#ff4b4b", combine:"add",     shape:"hit",
    amount:0.55, dur:0.010,
    produces:["Intensity spike, fast attack","Sharpness → max for the hit","Decays back to the bed in ~200 ms"] },
  { id:"swell",  key:"3", name:"Swell",  color:"#ff8c42", combine:"add",     shape:"swell",
    amount:0.32, dur:0.040,
    produces:["Intensity rises then falls (sine hump)","Pace eases up slightly through the rise","Lands back on the bed at the end"] },
  { id:"tease",  key:"4", name:"Tease",  color:"#c075ff", combine:"replace", shape:"dip",
    amount:0.45, dur:0.030,
    produces:["Gate intensity down toward the floor","Pace stutters (withdraw)","Releases back to the bed — the edge"] },
  { id:"flutter",key:"5", name:"Flutter",color:"#39d4d4", combine:"add",     shape:"flutter",
    amount:0.28, dur:0.022,
    produces:["Rapid wildness burst","Pace doubles briefly","Tapers out over the window"] },
];
const infById = id => INFLUENCES.find(i=>i.id===id);

/* ───────────────────────── synth ───────────────────────── */
function hash(n){ const s=Math.sin(n*127.1)*43758.5453; return s-Math.floor(s); }
function vnoise(x){ const i=Math.floor(x),f=x-i,a=hash(i),b=hash(i+1),u=f*f*(3-2*f); return a*(1-u)+b*u; }
function fbm(x){ return vnoise(x)*0.55 + vnoise(x*2.3+11.7)*0.3 + vnoise(x*4.9+5.1)*0.15; }

function macroAt(t, passages){
  let v=0.35;
  passages.forEach(p=>{
    if(t<p.from||t>p.to) return;
    const k=p.to>p.from?(t-p.from)/(p.to-p.from):1;
    let shape;
    if(p.shape==="build") shape=k;
    else if(p.shape==="fall") shape=1-k;
    else if(p.shape==="swell") shape=Math.sin(k*Math.PI);
    else shape=1;
    v=Math.max(v, p.lo+(p.hi-p.lo)*shape);
  });
  return Math.min(1,v);
}
// rich device-agnostic feel sample (before moments), rendered through a lens
function sampleIntent(t, feel, passages, lens){
  const macro=macroAt(t,passages);
  const base=macro*(0.25+0.75*feel.intensity);
  const freq=(6+90*feel.pace)*lens.freqMul;
  const sine=Math.sin(t*freq*2*Math.PI);
  const square=Math.sign(sine)*Math.pow(Math.abs(sine),1-0.85*feel.sharpness);
  const wave=sine*(1-feel.sharpness)+square*feel.sharpness;
  const oscAmp=base*(0.10+0.32*feel.pace);
  let v=base+wave*oscAmp;
  const wild=feel.wildness*lens.fuzz;
  v+=(fbm(t*60+3.3)-0.5)*wild*0.9 + (fbm(t*7+21.0)-0.5)*wild*0.5;
  const focus=feel.focus??0.45; v=base+(v-base)*(1-focus*0.72);
  const depth=feel.depth??0.55;  v=0.5+(v-0.5)*(0.5+depth*1.0);
  if(lens.smooth>0){ const m=macro*(0.3+0.7*feel.intensity); v=v*(1-lens.smooth)+m*lens.smooth; }
  return Math.max(0,Math.min(1,v));
}
function spineAt(t, feel, passages){ return macroAt(t,passages)*(0.25+0.75*feel.intensity); }

function envAt(lt, shape){
  switch(shape){
    case "hold":    return Math.max(0,Math.min(1, Math.min(lt/0.18,1)*Math.min((1-lt)/0.18,1)));
    case "hit":     return Math.exp(-Math.pow((lt-0.10)/0.10,2));
    case "swell":   return Math.sin(lt*Math.PI);
    case "dip":     return Math.sin(lt*Math.PI);
    case "flutter": return Math.sin(lt*Math.PI)*(0.55+0.45*Math.sin(lt*44));
    default:        return Math.sin(lt*Math.PI);
  }
}
// apply moments on top of a base value at t (bedVal = same-lens value w/o moments, for replace target)
function applyMoments(v, t, moments, bedVal){
  for(const m of moments){
    const inf=infById(m.typeId); if(!inf) continue;
    if(t<m.at||t>m.at+m.dur) continue;
    const e=envAt((t-m.at)/m.dur, inf.shape), amt=m.amount;
    if(inf.combine==="replace"){ const target=bedVal*(1-amt); v=v*(1-e)+target*e; }
    else v=v+e*amt;
  }
  return Math.max(0,Math.min(1,v));
}
// the full unified value at t through a lens, with moments layered on
function unifiedAt(t, feel, passages, lens, moments){
  const bed=sampleIntent(t,feel,passages,lens);
  return applyMoments(bed,t,moments,bed);
}
// device-agnostic source (intent lens) — what Polish conditions
function sourceAt(t, feel, passages, moments){ return unifiedAt(t,feel,passages,INTENT,moments); }

function buildSamples(feel, passages, lens, moments, n=900){
  const arr=new Array(n), bed=new Array(n), raw=new Array(n);
  for(let i=0;i<n;i++){ const t=i/(n-1);
    bed[i]=sampleIntent(t,feel,passages,lens);
    arr[i]=applyMoments(bed[i],t,moments,bed[i]);
    raw[i]=spineAt(t,feel,passages);
  }
  return {arr,bed,raw,n};
}

/* ── Polish device conditioning ── */
function smoothArr(arr,amt){ if(amt<=0)return arr.slice(); const w=Math.max(1,Math.round(amt*22)); const out=new Array(arr.length);
  for(let i=0;i<arr.length;i++){ let s=0,n=0; for(let j=-w;j<=w;j++){ const k=i+j; if(k>=0&&k<arr.length){s+=arr[k];n++;} } out[i]=s/n; } return out; }
function buildDevice(dev, rawKnobs, feel, passages, moments, n=720){
  const knobs=normKnobs(dev.id, rawKnobs);
  const inp=new Array(n);
  for(let i=0;i<n;i++){ const t=i/(n-1);
    const carrier=0.5+0.5*Math.sin(t*(6+90*feel.pace)*dev.freqMul*2*Math.PI);
    inp[i]=Math.max(0,Math.min(1, sourceAt(t,feel,passages,moments)*(0.6+0.4*carrier)));
  }
  let out=smoothArr(inp,knobs.smoothing);
  out=out.map(v=>Math.max(knobs.quiet,v));
  const cap=knobs.rate, res=[out[0]];
  for(let i=1;i<out.length;i++){ let d=out[i]-res[i-1]; d=Math.max(-cap,Math.min(cap,d)); res.push(res[i-1]+d); }
  return {inp,out:res};
}
function statsOf(a){ const rms=Math.round(Math.sqrt(a.reduce((s,v)=>s+v*v,0)/a.length)*100);
  let pk=0; for(let i=1;i<a.length;i++) pk=Math.max(pk,Math.abs(a[i]-a[i-1])); return {rms,peak:Math.round(pk*100)}; }

function fmt(ms){ const s=Math.floor(ms/1000),h=Math.floor(s/3600),m=Math.floor((s%3600)/60),ss=s%60;
  return `${h}:${String(m).padStart(2,"0")}:${String(ss).padStart(2,"0")}`; }
function fmtDur(d){ const ms=Math.round(d*TOTAL_MS); return ms>=1000?(ms/1000).toFixed(1)+"s":ms+"ms"; }
function fmtMs(ms){ const mm=Math.floor(ms/60000), ss=Math.floor((ms%60000)/1000), mmm=Math.floor(ms%1000); return `${mm}:${String(ss).padStart(2,"0")}.${String(mmm).padStart(3,"0")}`; }
