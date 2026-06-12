/*
 * FunscriptForge · Unified Forge
 * Shared components — the single visual grammar
 *
 * Block A, part 2. Dial/Param/Knob, UnifiedBand (lens-rendered bed + moment
 * windows), Bench (single input-vs-output OR stacked multi-channel lanes),
 * shell chrome. Ends with Object.assign(window, …) so Block B can read these.
 * Canonical artifact is "Unified Forge.html" — these files mirror the two
 * inline <script type="text/babel"> blocks it embeds, split for reading.
 */

/* ───────────────────────── shared UI ───────────────────────── */
function Dial({ label, value, onChange, lo, hi, fill="#ff7a3a" }){
  return (
    <div style={{display:"flex",flexDirection:"column",gap:7}}>
      <div style={{display:"flex",alignItems:"baseline",justifyContent:"space-between"}}>
        <span style={{fontSize:14,fontWeight:700}}>{label}</span>
        <span className="mono" style={{fontSize:14,fontWeight:600,color:fill}}>{Math.round(value*100)}</span>
      </div>
      <input className="dial" type="range" min={0} max={1} step={0.01} value={value}
        onChange={e=>onChange(Number(e.target.value))} style={{"--fill":fill,"--pct":`${value*100}%`}}/>
      <div style={{display:"flex",justifyContent:"space-between"}}>
        <span style={{fontSize:10.5,color:"var(--text-dim)"}}>{lo}</span>
        <span style={{fontSize:10.5,color:"var(--text-dim)"}}>{hi}</span>
      </div>
    </div>
  );
}
function Param({ label, v, onChange, lo, hi, fill, disp }){
  const cv=Math.max(0,Math.min(1,v));
  return (
    <div style={{display:"flex",flexDirection:"column",gap:7}}>
      <div style={{display:"flex",alignItems:"baseline",justifyContent:"space-between"}}>
        <span style={{fontSize:13.5,fontWeight:700}}>{label}</span>
        <span className="mono" style={{fontSize:13,fontWeight:600,color:fill}}>{disp}</span>
      </div>
      <input className="dial" type="range" min={0} max={1} step={0.01} value={cv}
        onChange={e=>onChange(Number(e.target.value))} style={{"--fill":fill,"--pct":`${cv*100}%`}}/>
      <div style={{display:"flex",justifyContent:"space-between"}}>
        <span style={{fontSize:10.5,color:"var(--text-dim)"}}>{lo}</span>
        <span style={{fontSize:10.5,color:"var(--text-dim)"}}>{hi}</span>
      </div>
    </div>
  );
}
function Knob({ label, value, onChange, min, max, step, fmt:fmtFn, fill, hint }){
  const pct=((value-min)/(max-min))*100;
  return (
    <div style={{marginBottom:16}}>
      <div style={{display:"flex",alignItems:"baseline",justifyContent:"space-between",marginBottom:6}}>
        <span style={{fontSize:13.5,fontWeight:600,whiteSpace:"nowrap"}}>{label}</span>
        <span className="mono" style={{fontSize:12.5,fontWeight:600,color:fill}}>{fmtFn(value)}</span>
      </div>
      <input className="dial" type="range" min={min} max={max} step={step} value={value}
        onChange={e=>onChange(Number(e.target.value))} style={{"--fill":fill,"--pct":`${pct}%`}}/>
      <div style={{fontSize:10.5,color:"var(--text-dim)",marginTop:5,lineHeight:1.4}}>{hint}</div>
    </div>
  );
}

/* the hero band — bed (lens-rendered) + moments overlay; momentsMode: off|faint|edit */
function UnifiedBand({ feel, passages, lens, moments, momentsMode="faint", selId, onPick, onScrub, playhead, height=248 }){
  const wrapRef=useRef(null), cvRef=useRef(null); const [w,setW]=useState(900); const H=height;
  useEffect(()=>{ const ro=new ResizeObserver(es=>{for(const e of es)setW(e.contentRect.width);}); if(wrapRef.current)ro.observe(wrapRef.current); return ()=>ro.disconnect(); },[]);
  const data=useMemo(()=>buildSamples(feel,passages,lens,moments),[feel,passages,lens,moments]);

  useEffect(()=>{
    const cv=cvRef.current; if(!cv)return; const dpr=Math.min(2,window.devicePixelRatio||1);
    cv.width=w*dpr; cv.height=H*dpr; cv.style.width=w+"px"; cv.style.height=H+"px";
    const g=cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0); g.clearRect(0,0,w,H);
    const padT=24,padB=24,gh=H-padT-padB, X=i=>i/(data.n-1)*w, Y=v=>padT+gh*(1-v);
    // chapters
    CHAPTERS.forEach((c,idx)=>{ const x0=c.from*w,x1=c.to*w;
      g.fillStyle=idx%2?"rgba(255,255,255,0.012)":"rgba(255,255,255,0.028)"; g.fillRect(x0,padT,x1-x0,gh);
      g.strokeStyle="rgba(45,49,72,0.7)"; g.lineWidth=1; g.beginPath(); g.moveTo(x0,padT); g.lineTo(x0,padT+gh); g.stroke();
      if(idx%2===0){ g.fillStyle="rgba(107,115,144,0.55)"; g.font="9px 'JetBrains Mono'"; g.fillText(c.label,x0+4,padT+gh+14); }
      g.fillStyle=c.color+"cc"; g.fillRect(x0,padT-4,Math.max(2,(x1-x0)-2),2);
    });
    g.strokeStyle="rgba(45,49,72,0.45)"; [0.25,0.5,0.75].forEach(gv=>{ g.beginPath(); g.moveTo(0,Y(gv)); g.lineTo(w,Y(gv)); g.stroke(); });
    const hex=lens.hex;
    // moment windows (under the curve)
    if(momentsMode!=="off"){
      moments.forEach(m=>{ const inf=infById(m.typeId); if(!inf)return; const x0=m.at*w,x1=(m.at+m.dur)*w,sel=m.id===selId;
        const op = momentsMode==="edit" ? (sel?"24":"15") : "10";
        g.fillStyle=inf.color+op; g.fillRect(x0,padT,Math.max(3,x1-x0),gh);
        g.strokeStyle=inf.color+(sel?"":"88"); g.lineWidth=sel?2:1; g.beginPath(); g.moveTo(x0,padT); g.lineTo(x0,padT+gh); g.stroke();
      });
    }
    if(lens.tracks===3){
      // multi-axis lanes
      const axisDefs=[
        {label:"L0 · stroke", c:"#4dabf7", src:data.arr},
        {label:"R0 · twist",  c:"#ffb547", src:data.arr.map((v,i)=>Math.max(0,0.5+(fbm(i*0.5+3)-0.5)*feel.wildness*1.6))},
        {label:"R1 · roll",   c:"#ff8c42", src:data.arr.map((v,i)=>0.5+0.42*Math.sin(i/data.n*Math.PI*2*(2+8*feel.pace)))},
      ];
      const laneH=gh/3;
      axisDefs.forEach((ax,li)=>{ const top=padT+li*laneH;
        g.fillStyle="rgba(255,255,255,0.015)"; g.fillRect(0,top,w,laneH-3);
        g.beginPath(); g.moveTo(0,top+laneH-4); ax.src.forEach((v,i)=>g.lineTo(X(i),top+laneH-4-(laneH-8)*Math.max(0,Math.min(1,v)))); g.lineTo(w,top+laneH-4); g.closePath(); g.fillStyle=ax.c+"22"; g.fill();
        g.beginPath(); ax.src.forEach((v,i)=>{ const x=X(i),y=top+laneH-4-(laneH-8)*Math.max(0,Math.min(1,v)); i?g.lineTo(x,y):g.moveTo(x,y);}); g.strokeStyle=ax.c; g.lineWidth=1.4; g.stroke();
        g.fillStyle=ax.c; g.font="600 9px 'JetBrains Mono'"; g.fillText(ax.label,6,top+11);
      });
    } else {
      // wildness fuzz envelope
      const fuzzAmt=feel.wildness*lens.fuzz*0.5;
      if(fuzzAmt>0.02){
        g.beginPath();
        for(let i=0;i<data.n;i++){ const up=Math.min(1,data.arr[i]+fuzzAmt*(0.4+fbm(i*0.7))); g.lineTo(X(i),Y(up)); if(i===0)g.moveTo(X(0),Y(up)); }
        for(let i=data.n-1;i>=0;i--){ const dn=Math.max(0,data.arr[i]-fuzzAmt*(0.4+fbm(i*0.9+9))); g.lineTo(X(i),Y(dn)); }
        g.closePath(); g.fillStyle=hex+"1e"; g.fill();
      }
      // fill + line
      const grad=g.createLinearGradient(0,padT,0,padT+gh); grad.addColorStop(0,hex+"66"); grad.addColorStop(1,hex+"08");
      g.beginPath(); g.moveTo(0,padT+gh); for(let i=0;i<data.n;i++) g.lineTo(X(i),Y(data.arr[i])); g.lineTo(w,padT+gh); g.closePath(); g.fillStyle=grad; g.fill();
      g.beginPath(); for(let i=0;i<data.n;i++){ const x=X(i),y=Y(data.arr[i]); i?g.lineTo(x,y):g.moveTo(x,y);} g.strokeStyle=hex; g.lineWidth=1.7; g.stroke();
      // honest spine
      g.beginPath(); for(let i=0;i<data.n;i++){ const x=X(i),y=Y(data.raw[i]); i?g.lineTo(x,y):g.moveTo(x,y);} g.strokeStyle="rgba(155,163,196,0.5)"; g.lineWidth=1; g.setLineDash([3,3]); g.stroke(); g.setLineDash([]);
    }
    // moment labels (on top)
    if(momentsMode!=="off"){
      moments.forEach(m=>{ const inf=infById(m.typeId); if(!inf)return; const cx=(m.at+m.dur/2)*w; const sel=m.id===selId;
        g.font="700 10px Inter"; const tw=g.measureText(inf.name).width, bw=tw+16;
        g.fillStyle=sel?inf.color:inf.color+"cc"; g.beginPath(); g.roundRect(cx-bw/2,4,bw,16,4); g.fill();
        g.fillStyle="#0e1117"; g.fillText(inf.name,cx-tw/2,15.5);
      });
    }
  },[data,w,feel,lens,moments,momentsMode,selId,H]);

  const click=e=>{ const r=cvRef.current.getBoundingClientRect(); const f=(e.clientX-r.left)/r.width;
    if(momentsMode==="edit"){ const hit=moments.find(m=>f>=m.at&&f<=m.at+m.dur); if(hit){onPick&&onPick(hit.id);return;} }
    onScrub&&onScrub(Math.max(0,Math.min(1,f)));
  };
  return (
    <div ref={wrapRef} style={{position:"relative",width:"100%"}}>
      <canvas ref={cvRef} onClick={click} style={{display:"block",borderRadius:8,cursor:onScrub?"pointer":"default"}}/>
      <div style={{position:"absolute",top:20,bottom:20,left:`${playhead*100}%`,width:0,borderLeft:"1.5px solid #fafafa",pointerEvents:"none"}}>
        <div style={{position:"absolute",left:-4,top:-3,width:8,height:8,borderRadius:4,background:"#fafafa",boxShadow:"0 0 6px rgba(255,255,255,.6)"}}/>
      </div>
    </div>
  );
}

/* Polish bench — single: input (dashed) vs to-device (bold); multi-channel: stacked lanes */
function Bench({ dev, knobs, feel, passages, moments }){
  const ref=useRef(null), wrapRef=useRef(null); const [w,setW]=useState(700); const H=200;
  useEffect(()=>{ const ro=new ResizeObserver(es=>{for(const e of es)setW(e.contentRect.width);}); if(wrapRef.current)ro.observe(wrapRef.current); return ()=>ro.disconnect(); },[]);
  const {inp,out}=useMemo(()=>buildDevice(dev,knobs,feel,passages,moments),[dev,knobs,feel,passages,moments]);
  const lanes=useMemo(()=>deriveChannels(dev,out,feel,out.length),[dev,out,feel]);
  useEffect(()=>{
    const cv=ref.current; if(!cv)return; const dpr=Math.min(2,window.devicePixelRatio||1);
    cv.width=w*dpr; cv.height=H*dpr; cv.style.width=w+"px"; cv.style.height=H+"px";
    const g=cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0); g.clearRect(0,0,w,H);
    const padT=14,padB=14,gh=H-padT-padB, X=i=>i/(out.length-1)*w;
    if(lanes){
      const laneH=gh/lanes.length;
      lanes.forEach((ax,li)=>{ const top=padT+li*laneH;
        g.fillStyle="rgba(255,255,255,0.015)"; g.fillRect(0,top,w,laneH-3);
        g.strokeStyle="rgba(45,49,72,0.4)"; g.beginPath(); g.moveTo(0,top+laneH-3.5); g.lineTo(w,top+laneH-3.5); g.stroke();
        const gr=g.createLinearGradient(0,top,0,top+laneH); gr.addColorStop(0,ax.color+"40"); gr.addColorStop(1,ax.color+"06");
        g.beginPath(); g.moveTo(0,top+laneH-4); ax.data.forEach((v,i)=>g.lineTo(X(i),top+laneH-4-(laneH-8)*Math.max(0,Math.min(1,v)))); g.lineTo(w,top+laneH-4); g.closePath(); g.fillStyle=gr; g.fill();
        g.beginPath(); ax.data.forEach((v,i)=>{ const x=X(i),y=top+laneH-4-(laneH-8)*Math.max(0,Math.min(1,v)); i?g.lineTo(x,y):g.moveTo(x,y);}); g.strokeStyle=ax.color; g.lineWidth=1.5; g.stroke();
        g.fillStyle=ax.color; g.font="600 9px 'JetBrains Mono'"; g.fillText(ax.label,6,top+11);
      });
    } else {
      const Y=v=>padT+gh*(1-v);
      g.strokeStyle="rgba(45,49,72,0.45)"; [0.25,0.5,0.75].forEach(gv=>{ g.beginPath(); g.moveTo(0,Y(gv)); g.lineTo(w,Y(gv)); g.stroke(); });
      g.beginPath(); g.moveTo(0,Y(inp[0])); inp.forEach((v,i)=>g.lineTo(X(i),Y(v))); for(let i=out.length-1;i>=0;i--)g.lineTo(X(i),Y(out[i])); g.closePath(); g.fillStyle="#ff8c4218"; g.fill();
      g.beginPath(); inp.forEach((v,i)=>{ const x=X(i),y=Y(v); i?g.lineTo(x,y):g.moveTo(x,y);}); g.strokeStyle="rgba(155,163,196,0.55)"; g.lineWidth=1; g.setLineDash([3,3]); g.stroke(); g.setLineDash([]);
      const gr=g.createLinearGradient(0,padT,0,padT+gh); gr.addColorStop(0,dev.hex+"44"); gr.addColorStop(1,dev.hex+"06");
      g.beginPath(); g.moveTo(0,padT+gh); out.forEach((v,i)=>g.lineTo(X(i),Y(v))); g.lineTo(w,padT+gh); g.closePath(); g.fillStyle=gr; g.fill();
      g.beginPath(); out.forEach((v,i)=>{ const x=X(i),y=Y(v); i?g.lineTo(x,y):g.moveTo(x,y);}); g.strokeStyle=dev.hex; g.lineWidth=1.8; g.stroke();
    }
  },[inp,out,lanes,w,dev]);
  return <div ref={wrapRef} style={{width:"100%"}}><canvas ref={ref} style={{display:"block",borderRadius:8}}/></div>;
}
function MiniEnv({ dev, knobs, feel, passages, moments, active }){
  const ref=useRef(null);
  useEffect(()=>{ const cv=ref.current; if(!cv)return; const w=cv.clientWidth||200,h=52,dpr=Math.min(2,window.devicePixelRatio||1);
    cv.width=w*dpr; cv.height=h*dpr; cv.style.height=h+"px"; const g=cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0); g.clearRect(0,0,w,h);
    const {out}=buildDevice(dev,knobs,feel,passages,moments,200);
    g.beginPath(); g.moveTo(0,h); out.forEach((v,i)=>g.lineTo(i/(out.length-1)*w,h-(h-6)*v)); g.lineTo(w,h); g.closePath();
    const gr=g.createLinearGradient(0,0,0,h); gr.addColorStop(0,dev.hex+(active?"55":"33")); gr.addColorStop(1,dev.hex+"08"); g.fillStyle=gr; g.fill();
    g.beginPath(); out.forEach((v,i)=>{ const x=i/(out.length-1)*w,y=h-(h-6)*v; i?g.lineTo(x,y):g.moveTo(x,y);}); g.strokeStyle=dev.hex; g.lineWidth=1.4; g.globalAlpha=active?1:0.7; g.stroke();
  },[dev,knobs,feel,passages,moments,active]);
  return <canvas ref={ref} style={{display:"block",width:"100%"}}/>;
}
function MacroPreview({ passages }){
  const ref=useRef(null);
  useEffect(()=>{ const cv=ref.current; if(!cv)return; const w=cv.clientWidth||520,h=88,dpr=Math.min(2,window.devicePixelRatio||1);
    cv.width=w*dpr; cv.height=h*dpr; cv.style.height=h+"px"; const g=cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0); g.clearRect(0,0,w,h);
    for(let i=0;i<21;i++){ const x=i/21*w; g.strokeStyle="rgba(45,49,72,0.5)"; g.beginPath(); g.moveTo(x,0); g.lineTo(x,h); g.stroke(); }
    const N=300; g.beginPath(); g.moveTo(0,h); for(let i=0;i<N;i++){ const t=i/(N-1); g.lineTo(t*w,h-(h-8)*macroAt(t,passages)); } g.lineTo(w,h); g.closePath();
    const gr=g.createLinearGradient(0,0,0,h); gr.addColorStop(0,"#ff8c4255"); gr.addColorStop(1,"#ff8c4208"); g.fillStyle=gr; g.fill();
    g.beginPath(); for(let i=0;i<N;i++){ const t=i/(N-1); const y=h-(h-8)*macroAt(t,passages); i?g.lineTo(t*w,y):g.moveTo(t*w,y);} g.strokeStyle="#ff8c42"; g.lineWidth=1.6; g.stroke();
  },[passages]);
  return <canvas ref={ref} style={{display:"block",width:"100%",borderRadius:6,background:"var(--surface-2)",border:"1px solid var(--border)"}}/>;
}

/* shell chrome */
const TABS=["Library","Project","Analysis","Chapters","Phrases","Stanzas","Voicing","Moments","Polish","Export","Catalog"];
const REAL_TABS={Voicing:1,Moments:1,Polish:1};
function TopBar({ tab }){
  return (
    <div style={{height:44,background:"var(--bg)",borderBottom:"1px solid var(--border)",display:"flex",alignItems:"center",padding:"0 16px",gap:14,flexShrink:0}}>
      <div style={{display:"flex",alignItems:"center",gap:8}}>
        <svg width={20} height={20} viewBox="0 0 24 24" fill="none"><path d="M 4 16 L 12 4 L 20 16 M 6 16 L 18 16" stroke="#ff7a3a" strokeWidth={1.8} strokeLinejoin="round"/><circle cx={12} cy={10} r={2} fill="#ff7a3a"/></svg>
        <span style={{fontWeight:700,fontSize:14,letterSpacing:"-0.01em"}}>FunscriptForge</span>
        <span className="mono" style={{fontSize:10,color:"var(--text-dim)",marginLeft:4}}>v2.5 · {tab.toLowerCase()}</span>
      </div>
      <span style={{flex:1}}/>
      <div style={{display:"flex",alignItems:"center",gap:14,fontSize:11,color:"var(--text-muted)"}}>
        <span style={{display:"flex",alignItems:"center",gap:6}}><span style={{width:6,height:6,borderRadius:"50%",background:"#3ed598",boxShadow:"0 0 4px #3ed598"}}/>live preview</span>
        <span style={{color:"var(--text-dim)"}}>·</span><span className="mono">ipzz-125.feel.yml</span>
      </div>
    </div>
  );
}
function TabStrip({ tab, onNav }){
  return (
    <div style={{height:42,display:"flex",alignItems:"stretch",background:"var(--surface-2)",borderBottom:"1px solid var(--border)",padding:"0 16px",flexShrink:0}}>
      {TABS.map(t=>{ const active=t===tab, real=REAL_TABS[t];
        return (
          <div key={t} onClick={()=>real&&onNav(t)} style={{display:"flex",alignItems:"center",gap:6,padding:"0 13px",
            borderBottom:active?"2px solid #ff7a3a":"2px solid transparent",
            color:active?"#fafafa":(real?"#cfd4e6":"var(--text-muted)"),fontSize:12.5,fontWeight:active?700:500,
            cursor:real?"pointer":"default",opacity:real||active?1:0.7}}>
            {t}
            {real&&!active&&<span style={{width:5,height:5,borderRadius:"50%",background:"#ff7a3a",opacity:0.55}}/>}
          </div>
        );
      })}
    </div>
  );
}
function MediaViewer({ playhead, blurb, armedColor }){
  return (
    <div style={{flex:"0 0 248px",display:"flex",flexDirection:"column",background:"var(--surface-2)",border:"1px solid var(--border)",borderRadius:10,overflow:"hidden",alignSelf:"flex-start"}}>
      <div style={{height:140,background:"linear-gradient(135deg,#1a1d27,#0e1117)",borderBottom:"1px solid var(--border)",position:"relative"}}>
        <svg viewBox="0 0 248 140" style={{position:"absolute",inset:0,width:"100%",height:"100%"}}>
          <defs><radialGradient id="lt" cx="62%" cy="40%" r="55%"><stop offset="0%" stopColor="#ff7a3a" stopOpacity={0.30}/><stop offset="100%" stopColor="#ff7a3a" stopOpacity={0}/></radialGradient></defs>
          <rect width="248" height="140" fill="url(#lt)"/><line x1="0" y1="86" x2="248" y2="88" stroke="#3a3f5c" strokeWidth="0.5" opacity="0.5"/>
          <ellipse cx="138" cy="58" rx="14" ry="20" fill="#1a1d27" stroke="#3a3f5c"/><path d="M 114 84 Q 114 72 138 72 Q 162 72 162 84 L 162 122 L 114 122 Z" fill="#1a1d27" stroke="#3a3f5c"/>
        </svg>
        <div className="mono" style={{position:"absolute",top:8,right:8,padding:"3px 7px",borderRadius:4,background:"rgba(0,0,0,.6)",backdropFilter:"blur(8px)",fontSize:10.5,fontWeight:600}}>{fmt(playhead*TOTAL_MS)} / {fmt(TOTAL_MS)}</div>
        {armedColor&&<div style={{position:"absolute",bottom:8,left:8,width:12,height:12,borderRadius:"50%",background:armedColor,animation:"pulseRing 1.6s infinite"}}/>}
      </div>
      <div style={{padding:"10px 12px",display:"flex",alignItems:"center",gap:8}}>
        {["⏮","▶","⏭"].map((s,i)=>(<button key={i} style={{width:i===1?30:26,height:i===1?30:26,borderRadius:6,background:"var(--surface)",border:"1px solid var(--border)",color:"var(--text-muted)",cursor:"pointer",fontSize:i===1?13:11,display:"grid",placeItems:"center",padding:0}}>{s}</button>))}
        <span style={{flex:1}}/><span className="mono" style={{fontSize:10.5,color:"var(--text-muted)"}}>ipzz-125</span>
      </div>
      <div style={{padding:"10px 12px",borderTop:"1px solid var(--border)",fontSize:11,color:"var(--text-muted)",lineHeight:1.5}}>{blurb}</div>
    </div>
  );
}

Object.assign(window, {
  TOTAL_MS, CHAPTERS, INTENT, DEVICES, LENSES, lensById, devById, INFLUENCES, infById, KNOBS, normKnobs, CHANNELS, CHANNEL_FILES,
  macroAt, sampleIntent, spineAt, envAt, applyMoments, unifiedAt, sourceAt, buildSamples,
  buildDevice, statsOf, fmt, fmtDur, fmtMs, fbm,
  Dial, Param, Knob, UnifiedBand, Bench, MiniEnv, MacroPreview,
  TABS, REAL_TABS, TopBar, TabStrip, MediaViewer,
});
