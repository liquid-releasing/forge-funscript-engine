/*
 * FunscriptForge · Unified Forge
 * Views + App — Voicing / Moments / Polish, one shared state
 *
 * Block B. Voicing (Feel dials + Passages add/empty-state editor), Moments
 * (capture begin/end from playhead, Chain + Snap to beat), Polish (per-device
 * Hammer & tongs + multi-channel bench). App holds the single source of truth
 * (feel, passages, moments, playhead) and routes the active tab.
 * Canonical artifact is "Unified Forge.html" — these files mirror the two
 * inline <script type="text/babel"> blocks it embeds, split for reading.
 */

const { useState, useMemo, useRef, useEffect, useCallback } = React;
const CARD={ background:"var(--surface)",border:"1px solid var(--border)",borderRadius:12 };

/* ───────────── Voicing view ───────────── */
function VoicingView({ feel, setFeel, passages, setPassages, moments, playhead, onScrub }){
  const [lensId,setLensId]=useState("intent");
  const lens=lensById(lensId);
  const set=(k,v)=>setFeel(f=>({...f,[k]:v}));
  const SHAPES=[["build","Build"],["fall","Release"],["swell","Swell"],["hold","Steady"]];
  const chOf=t=>Math.min(21,Math.max(1,Math.floor(t*21)+1));
  const addPassage=()=>{ const id="p"+Date.now().toString(36); setPassages(ps=>[...ps,{id,shape:"build",from:0.3,to:0.6,lo:0.4,hi:0.85,label:`Ch${chOf(0.3)} → Ch${chOf(0.6)}`}]); };
  const rmPassage=(id)=>setPassages(ps=>ps.filter(p=>p.id!==id));
  const setShape=(id,sh)=>setPassages(ps=>ps.map(p=>p.id===id?{...p,shape:sh}:p));
  const word=useMemo(()=>{ const p=[]; p.push(feel.intensity>0.66?"Intense":feel.intensity<0.33?"Gentle":"Balanced");
    if(feel.wildness>0.55)p.push("Wild"); else if(feel.wildness<0.2)p.push("Steady");
    if(feel.pace>0.6)p.push("Fast"); else if(feel.pace<0.25)p.push("Slow");
    if(feel.sharpness>0.6)p.push("Sharp"); return p.join(" · "); },[feel]);
  const stats=useMemo(()=>{ const {arr}=buildSamples(feel,passages,lens,moments,400);
    const rms=Math.round(Math.sqrt(arr.reduce((s,v)=>s+v*v,0)/arr.length)*100);
    let pk=0; for(let i=1;i<arr.length;i++)pk=Math.max(pk,Math.abs(arr[i]-arr[i-1])); return {rms,peak:Math.round(pk*100)}; },[feel,passages,lens,moments]);

  return (
    <>
      <div style={{display:"flex",alignItems:"baseline",gap:14,marginBottom:6}}>
        <h1 style={{margin:0,fontSize:26,fontWeight:800,letterSpacing:"-0.02em"}}>Voicing</h1>
        <span style={{fontSize:13,color:"var(--text-muted)",maxWidth:620}}>One device-agnostic source. You shape <em style={{color:"var(--text)",fontStyle:"normal",fontWeight:600}}>how it feels</em> — every device speaks the same intent. Polish forges the files.</span>
      </div>
      <div style={{display:"flex",gap:14,marginTop:12}}>
        <div style={{flex:1,minWidth:0,...CARD,padding:14}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12,flexWrap:"wrap"}}>
            <span className="eyebrow">Preview lens</span>
            <div style={{display:"inline-flex",gap:0,background:"var(--surface-2)",border:"1px solid var(--border)",borderRadius:8,padding:3}}>
              {LENSES.map(l=>{ const active=l.id===lensId; return (
                <button key={l.id} onClick={()=>setLensId(l.id)} style={{display:"inline-flex",alignItems:"center",gap:7,padding:"6px 12px",borderRadius:6,border:"none",
                  background:active?"var(--surface)":"transparent",cursor:"pointer",color:active?"#fafafa":"var(--text-muted)",fontSize:12,fontWeight:active?700:500,
                  outline:active?`1px solid ${l.hex}66`:"none"}}>
                  <span style={{width:8,height:8,borderRadius:2,background:l.hex,opacity:active?1:0.55}}/>{l.label}
                </button>); })}
            </div>
            <span className="mono" style={{fontSize:10.5,color:"var(--text-dim)"}}>{lens.sub}</span>
          </div>
          <UnifiedBand feel={feel} passages={passages} lens={lens} moments={moments} momentsMode="faint" playhead={playhead} onScrub={onScrub}/>
          <div style={{display:"flex",alignItems:"center",gap:16,marginTop:10,flexWrap:"wrap"}}>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:18,height:3,background:lens.hex,borderRadius:2}}/> energy → device</span>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:18,borderTop:"1px dashed #9ba3c4"}}/> position spine</span>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:14,height:10,background:lens.hex+"22",borderRadius:2}}/> wildness</span>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-dim)"}}>faint blocks = Moments (edit in Moments tab)</span>
            <span style={{flex:1}}/>
            {[["rms",stats.rms],["peak Δ",stats.peak+"%"]].map(([k,v])=>(<span key={k} className="mono" style={{fontSize:10.5,color:"var(--text-dim)"}}>{k} <span style={{color:"var(--text)"}}>{v}</span></span>))}
          </div>
          <div style={{marginTop:10,padding:"9px 12px",borderRadius:8,background:lens.hex+"10",border:`1px solid ${lens.hex}33`,fontSize:11.5,color:"var(--text-muted)",lineHeight:1.5}}>
            <strong style={{color:lens.hex}}>{lens.label}.</strong> {lens.note}
          </div>
        </div>
        <MediaViewer playhead={playhead} blurb={<span>You watch the scene while you author the <strong style={{color:"var(--text)"}}>feel</strong>. The band is the intent — Polish turns it into each device's file.</span>}/>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1.25fr 1fr",gap:14,marginTop:14}}>
        <div style={{...CARD,padding:"16px 18px"}}>
          <div style={{display:"flex",alignItems:"baseline",gap:10,marginBottom:16}}>
            <h3 style={{margin:0,fontSize:16,fontWeight:700}}>Feel</h3>
            <span style={{fontSize:11.5,color:"var(--text-muted)"}}>the character of the energy — shared by every device</span>
            <span style={{flex:1}}/><span className="mono" style={{fontSize:11,color:"#ff7a3a",fontWeight:600}}>{word}</span>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"20px 28px"}}>
            <Dial label="Intensity" value={feel.intensity} onChange={v=>set("intensity",v)} lo="soft" hi="strong" fill="#ff4b4b"/>
            <Dial label="Pace"      value={feel.pace}      onChange={v=>set("pace",v)}      lo="slow" hi="fast"  fill="#ff8c42"/>
            <Dial label="Wildness"  value={feel.wildness}  onChange={v=>set("wildness",v)}  lo="steady" hi="wild" fill="#c075ff"/>
            <Dial label="Sharpness" value={feel.sharpness} onChange={v=>set("sharpness",v)} lo="smooth" hi="sharp" fill="#4dabf7"/>
            <Dial label="Depth"     value={feel.depth}     onChange={v=>set("depth",v)}     lo="shallow" hi="deep" fill="#3ed598"/>
            <Dial label="Focus"     value={feel.focus}     onChange={v=>set("focus",v)}     lo="loose" hi="tight" fill="#39d4d4"/>
          </div>
          <div style={{marginTop:16,paddingTop:14,borderTop:"1px dashed var(--border)",display:"flex",gap:10,alignItems:"flex-start"}}>
            <span style={{width:24,height:24,borderRadius:6,border:"1px dashed var(--border-strong)",color:"var(--text-dim)",display:"grid",placeItems:"center",fontSize:14,flexShrink:0}}>?</span>
            <div style={{fontSize:11.5,color:"var(--text-dim)",lineHeight:1.5}}>Six qualities, all device-agnostic. Twist / vibrate / pulse are <em style={{fontStyle:"normal",color:"var(--text-muted)"}}>not</em> here — they fall out of these + the device. Dig through it; if a seventh is missing, it'll show itself.</div>
          </div>
        </div>
        <div style={{...CARD,padding:"16px 18px"}}>
          <div style={{display:"flex",alignItems:"baseline",gap:10,marginBottom:14}}>
            <h3 style={{margin:0,fontSize:16,fontWeight:700}}>Dynamics</h3>
            <span style={{fontSize:11.5,color:"var(--text-muted)",maxWidth:300}}>Slow intensity arcs over scene-scale spans — the change a single chapter is too short to carry.</span>
            <span style={{flex:1}}/>
            <button onClick={addPassage} style={{display:"inline-flex",alignItems:"center",gap:6,padding:"6px 11px",borderRadius:7,background:"var(--surface-2)",border:"1px solid var(--border-strong)",color:"#ff8c42",fontSize:12,fontWeight:700,cursor:"pointer",fontFamily:"inherit"}}>+ Add passage</button>
          </div>
          <MacroPreview passages={passages}/>
          {passages.length===0 ? (
            <div style={{marginTop:14,border:"1px dashed var(--border-strong)",borderRadius:10,padding:"26px 18px",textAlign:"center"}}>
              <div style={{fontSize:12.5,color:"var(--text-muted)"}}>No passages yet.</div>
              <div style={{fontSize:11.5,color:"var(--text-dim)",marginTop:6,maxWidth:440,marginInline:"auto",lineHeight:1.5}}>Add one to lay a <strong style={{color:"var(--text-muted)"}}>Build</strong>, <strong style={{color:"var(--text-muted)"}}>Release</strong>, or <strong style={{color:"var(--text-muted)"}}>Swell</strong> across a run of chapters — the default <strong style={{color:"var(--text-muted)"}}>Steady</strong> is a flat no-op.</div>
            </div>
          ) : (
          <div style={{display:"flex",flexDirection:"column",gap:10,marginTop:14}}>
            {passages.map(p=>(
              <div key={p.id} style={{background:"var(--surface-2)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 12px"}}>
                <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:9}}>
                  <div style={{display:"inline-flex",gap:0,background:"var(--bg)",border:"1px solid var(--border)",borderRadius:6,padding:2}}>
                    {SHAPES.map(([v,l])=>{ const on=p.shape===v; return (
                      <button key={v} onClick={()=>setShape(p.id,v)} style={{padding:"3px 8px",borderRadius:4,border:"none",background:on?"#ff8c42":"transparent",color:on?"#0e1117":"var(--text-muted)",fontSize:11,fontWeight:on?700:500,cursor:"pointer",fontFamily:"inherit"}}>{l}</button>
                    );})}
                  </div>
                  <span className="mono" style={{fontSize:10.5,color:"var(--text-dim)"}}>{p.label}</span>
                  <span style={{flex:1}}/>
                  <span className="mono" style={{fontSize:11,color:"var(--text-muted)"}}>{Math.round(p.lo*100)}% → {Math.round(p.hi*100)}%</span>
                  <button onClick={()=>rmPassage(p.id)} title="Remove passage" style={{width:22,height:22,borderRadius:5,background:"transparent",border:"1px solid var(--border)",color:"var(--text-dim)",cursor:"pointer",fontSize:11,lineHeight:1,padding:0}}>✕</button>
                </div>
                <input className="dial" type="range" min={0.2} max={1} step={0.01} value={p.hi}
                  onChange={e=>{ const v=Number(e.target.value); setPassages(ps=>ps.map(x=>x.id===p.id?{...x,hi:v}:x)); }}
                  style={{"--fill":"#ff8c42","--pct":`${((p.hi-0.2)/0.8)*100}%`}}/>
                <div style={{fontSize:10.5,color:"var(--text-dim)",marginTop:5}}>{p.shape==="build"?"Rises from floor to ceiling across the span.":p.shape==="fall"?"Falls from ceiling to floor across the span.":p.shape==="swell"?"Swells up then back down across the span.":"Holds flat at the ceiling — a steady no-op."}</div>
              </div>
            ))}
          </div>
          )}
        </div>
      </div>
    </>
  );
}

/* ───────────── Moments view ───────────── */
let MID=100;
function MomentsView({ feel, passages, moments, setMoments, playhead, onScrub, armed, setArmed, selId, setSelId }){
  const lens=INTENT;
  const armedInf=infById(armed);
  const drop=useCallback((typeId,at)=>{ const inf=infById(typeId); const id=++MID;
    setMoments(ms=>[...ms,{id,typeId,at:Math.min(0.97,at),dur:inf.dur,amount:inf.amount}]); setSelId(id); },[setMoments,setSelId]);
  useEffect(()=>{ const onKey=e=>{ const inf=INFLUENCES.find(i=>i.key===e.key); if(inf){ e.preventDefault(); drop(inf.id,playhead); } };
    window.addEventListener("keydown",onKey); return ()=>window.removeEventListener("keydown",onKey); },[drop,playhead]);
  const sel=moments.find(m=>m.id===selId), selInf=sel?infById(sel.typeId):null;
  const updSel=patch=>setMoments(ms=>ms.map(m=>m.id===selId?{...m,...patch}:m));
  const ordered=[...moments].sort((a,b)=>a.at-b.at);
  const [snap,setSnap]=useState(true);
  const [chain,setChain]=useState(true);
  const [anchor,setAnchor]=useState(null);
  const snapT=(t)=>{ if(!snap) return t; const g=1/(21*8); return Math.round(t/g)*g; };
  const capBegin=()=>{ if(!sel) return; const end=sel.at+sel.dur; let b=(chain&&anchor!=null)?anchor:snapT(playhead); b=Math.max(0,Math.min(b,end-0.003)); updSel({at:b,dur:end-b}); };
  const capEnd=()=>{ if(!sel) return; let e=snapT(playhead); e=Math.max(sel.at+0.003,Math.min(0.999,e)); updSel({dur:e-sel.at}); if(chain) setAnchor(e); };
  const resetWin=()=>{ if(!sel) return; const inf=infById(sel.typeId); updSel({dur:inf.dur}); setAnchor(null); };
  const capBtn={display:"inline-flex",alignItems:"center",gap:6,padding:"7px 12px",borderRadius:7,background:"var(--surface-2)",border:"1px solid var(--border-strong)",color:"var(--text)",fontSize:12,fontWeight:600,cursor:sel?"pointer":"not-allowed",fontFamily:"inherit"};
  const timeBox={minWidth:94,textAlign:"center",padding:"7px 10px",borderRadius:7,background:"var(--surface-2)",border:"1px solid var(--border)",fontSize:13,fontWeight:600,color:sel?"var(--text)":"var(--text-dim)"};
  const chk={display:"inline-flex",alignItems:"center",gap:7,fontSize:12,fontWeight:600,color:"var(--text-muted)",cursor:"pointer"};

  return (
    <>
      <div style={{display:"flex",alignItems:"baseline",gap:14,marginBottom:12}}>
        <h1 style={{margin:0,fontSize:26,fontWeight:800,letterSpacing:"-0.02em"}}>Moments</h1>
        <span style={{fontSize:13,color:"var(--text-muted)",maxWidth:640}}>Punctual influences you drop <em style={{color:"var(--text)",fontStyle:"normal",fontWeight:600}}>while watching</em>. Each has a begin & end and <em style={{color:"var(--text)",fontStyle:"normal",fontWeight:600}}>adds on top</em> of the Voicing bed — same vocabulary, so it forges to every device too.</span>
      </div>
      <div style={{display:"flex",gap:14}}>
        <div style={{flex:1,minWidth:0,...CARD,padding:14}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12,flexWrap:"wrap"}}>
            <span className="eyebrow">Armed</span>
            <div style={{display:"inline-flex",gap:6}}>
              {INFLUENCES.map(inf=>{ const on=inf.id===armed; return (
                <button key={inf.id} onClick={()=>setArmed(inf.id)} style={{display:"inline-flex",alignItems:"center",gap:7,padding:"6px 11px",borderRadius:7,
                  background:on?inf.color+"1c":"var(--surface-2)",border:`1px solid ${on?inf.color:"var(--border)"}`,cursor:"pointer",color:on?"#fafafa":"var(--text-muted)",fontSize:12,fontWeight:on?700:500}}>
                  <span className="mono" style={{fontSize:9.5,color:inf.color,border:`1px solid ${inf.color}66`,borderRadius:3,padding:"0 4px"}}>{inf.key}</span>
                  <span style={{width:7,height:7,borderRadius:2,background:inf.color}}/>{inf.name}
                </button>); })}
            </div>
            <span style={{flex:1}}/>
            <button onClick={()=>drop(armed,playhead)} style={{display:"inline-flex",alignItems:"center",gap:8,padding:"8px 14px",borderRadius:8,background:armedInf.color,border:"none",color:"#0e1117",fontWeight:700,fontSize:12.5,cursor:"pointer"}}>⌖ Capture here</button>
          </div>
          <UnifiedBand feel={feel} passages={passages} lens={lens} moments={moments} momentsMode="edit" selId={selId} onPick={setSelId} playhead={playhead} onScrub={onScrub}/>
          <div style={{display:"flex",alignItems:"center",gap:16,marginTop:10,flexWrap:"wrap"}}>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:18,height:3,background:"#ff7a3a",borderRadius:2}}/> bed + moments</span>
            <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:18,borderTop:"1px dashed #9ba3c4"}}/> position spine</span>
            <span style={{flex:1}}/>
            <span className="mono" style={{fontSize:10.5,color:"var(--text-dim)"}}>click a window to edit · click empty to scrub · keys 1–5 to stamp</span>
          </div>
        </div>
        <MediaViewer playhead={playhead} armedColor={armedInf.color} blurb={<span>Watch, and <strong style={{color:"var(--text)"}}>tap a number</strong> to stamp the armed influence at the playhead.</span>}/>
      </div>
      {/* precise begin/end capture from playhead */}
      <div style={{marginTop:14,...CARD,padding:"11px 16px",display:"flex",alignItems:"center",gap:16,flexWrap:"wrap",opacity:sel?1:0.6}}>
        <span style={{width:26,height:26,borderRadius:"50%",background:sel?selInf.color:"var(--surface-3)",color:sel?"#0e1117":"var(--text-dim)",display:"grid",placeItems:"center",fontWeight:800,fontSize:12,flexShrink:0}}>{sel?ordered.findIndex(m=>m.id===selId)+1:"–"}</span>
        <span style={{fontSize:11,fontWeight:700,letterSpacing:".1em",textTransform:"uppercase",color:"var(--text-muted)"}}>Mark begin / end from playhead</span>
        <span style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:11.5,color:"var(--text-dim)"}}>Begin</span>
          <button onClick={capBegin} disabled={!sel} style={capBtn}>◎ Capture</button>
          <span className="mono" style={timeBox}>{sel?fmtMs(sel.at*TOTAL_MS):"--:--.---"}</span>
        </span>
        <span style={{color:"var(--text-dim)"}}>→</span>
        <span style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:11.5,color:"var(--text-dim)"}}>End</span>
          <button onClick={capEnd} disabled={!sel} style={capBtn}>◎ Capture</button>
          <span className="mono" style={timeBox}>{sel?fmtMs((sel.at+sel.dur)*TOTAL_MS):"--:--.---"}</span>
        </span>
        <span style={{display:"flex",flexDirection:"column",gap:2,marginLeft:4}}>
          <span className="eyebrow">Duration · derived</span>
          <span className="mono" style={{fontSize:13,fontWeight:600,color:sel?selInf.color:"var(--text-dim)"}}>{sel?fmtMs(sel.dur*TOTAL_MS):"--:--.---"}</span>
        </span>
        <span style={{flex:1}}/>
        <label style={chk}><input type="checkbox" checked={chain} onChange={e=>setChain(e.target.checked)} style={{accentColor:selInf?selInf.color:"#ff7a3a"}}/> Chain</label>
        <label style={chk}><input type="checkbox" checked={snap} onChange={e=>setSnap(e.target.checked)} style={{accentColor:selInf?selInf.color:"#ff7a3a"}}/> Snap to beat</label>
        <button onClick={resetWin} disabled={!sel} style={{...capBtn,opacity:sel?0.85:0.4}}>↺ Reset</button>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"320px 1fr",gap:14,marginTop:14}}>
        <div style={{...CARD,padding:14,alignSelf:"flex-start"}}>
          <div style={{display:"flex",alignItems:"baseline",gap:8,marginBottom:12}}>
            <h3 style={{margin:0,fontSize:15,fontWeight:700}}>Captured</h3><span className="mono" style={{fontSize:10.5,color:"var(--text-dim)"}}>{moments.length}</span>
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:7}}>
            {ordered.map(m=>{ const inf=infById(m.typeId),on=m.id===selId; return (
              <button key={m.id} onClick={()=>setSelId(m.id)} style={{display:"flex",alignItems:"center",gap:10,padding:"9px 11px",borderRadius:8,textAlign:"left",
                background:on?inf.color+"14":"var(--surface-2)",border:`1px solid ${on?inf.color+"88":"var(--border)"}`,borderLeft:`3px solid ${inf.color}`,cursor:"pointer",color:"inherit"}}>
                <span style={{width:8,height:8,borderRadius:2,background:inf.color,flexShrink:0}}/>
                <span style={{fontSize:13,fontWeight:600,flex:1}}>{inf.name}</span>
                <span className="mono" style={{fontSize:10.5,color:"var(--text-dim)"}}>{fmt(m.at*TOTAL_MS)}</span>
                <span style={{fontSize:9,fontWeight:700,letterSpacing:".06em",textTransform:"uppercase",color:inf.combine==="replace"?"#c075ff":"#3ed598"}}>{inf.combine==="replace"?"replace":"adds"}</span>
              </button>); })}
          </div>
        </div>
        <div style={{...CARD,padding:0,overflow:"hidden",alignSelf:"flex-start"}}>
          {sel?(
            <>
              <div style={{display:"flex",alignItems:"center",gap:12,padding:"14px 18px",borderBottom:"1px solid var(--border)"}}>
                <span style={{width:30,height:30,borderRadius:8,background:selInf.color+"22",border:`1px solid ${selInf.color}`,color:selInf.color,display:"grid",placeItems:"center",fontWeight:800,fontSize:13}}>{ordered.findIndex(m=>m.id===selId)+1}</span>
                <h2 style={{margin:0,fontSize:20,fontWeight:800}}>{selInf.name}</h2>
                <span style={{flex:1}}/>
                <span style={{fontSize:9.5,fontWeight:800,letterSpacing:".08em",textTransform:"uppercase",color:selInf.combine==="replace"?"#c075ff":"#3ed598",background:(selInf.combine==="replace"?"#c075ff":"#3ed598")+"1a",border:`1px solid ${(selInf.combine==="replace"?"#c075ff":"#3ed598")}55`,borderRadius:4,padding:"4px 9px"}}>{selInf.combine==="replace"?"Replaces":"Adds on top"}</span>
                <button onClick={()=>{ setMoments(ms=>ms.filter(m=>m.id!==selId)); setSelId(null); }} style={{width:28,height:28,borderRadius:6,background:"transparent",border:"1px solid var(--border)",color:"var(--text-dim)",cursor:"pointer"}}>✕</button>
              </div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:0}}>
                <div style={{padding:"16px 18px",borderRight:"1px solid var(--border)"}}>
                  <div className="eyebrow" style={{marginBottom:12}}>What this produces</div>
                  <div style={{display:"flex",flexDirection:"column",gap:11}}>
                    {selInf.produces.map((p,i)=>(<div key={i} style={{display:"flex",gap:10,alignItems:"flex-start"}}><span className="mono" style={{fontSize:11,color:selInf.color,fontWeight:600,flexShrink:0}}>{i+1}</span><span style={{fontSize:12.5,lineHeight:1.45}}>{p}</span></div>))}
                  </div>
                  <div style={{marginTop:14,paddingTop:12,borderTop:"1px dashed var(--border)",fontSize:11,color:"var(--text-dim)",lineHeight:1.5}}>Device-agnostic feel-ops. Polish renders them as pulse-rate / volume / stroke per target — same as the bed.</div>
                </div>
                <div style={{padding:"16px 18px"}}>
                  <div className="eyebrow" style={{marginBottom:14}}>Tune</div>
                  <div style={{display:"flex",flexDirection:"column",gap:16}}>
                    <Param label="Strength" v={sel.amount} lo="subtle" hi="strong" fill={selInf.color} onChange={v=>updSel({amount:v})} disp={Math.round(sel.amount*100)}/>
                    <Param label="Width" v={(sel.dur-0.005)/0.06} lo="instant" hi="long" fill="#ff8c42" onChange={v=>updSel({dur:0.005+v*0.06})} disp={fmtDur(sel.dur)}/>
                  </div>
                  <div style={{marginTop:18,paddingTop:14,borderTop:"1px solid var(--border)",fontSize:11,color:"var(--text-dim)",lineHeight:1.5}}>
                    Window <span className="mono" style={{color:"var(--text-muted)"}}>{fmtMs(sel.at*TOTAL_MS)} → {fmtMs((sel.at+sel.dur)*TOTAL_MS)}</span>. Set it precisely with <strong style={{color:"var(--text-muted)",fontWeight:600}}>Mark begin / end from playhead</strong> above.
                  </div>
                </div>
              </div>
            </>
          ):(
            <div style={{padding:"48px 24px",textAlign:"center",color:"var(--text-dim)"}}>
              <div style={{fontSize:13}}>No moment selected.</div>
              <div style={{fontSize:11.5,marginTop:6}}>Arm an influence above and tap a number while watching, or click a window on the band.</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* ───────────── Polish view ───────────── */
function PolishView({ feel, passages, moments, benchId, setBenchId, knobMap, setKnobMap, stamped, setStamped }){
  const dev=devById(benchId), knobs=knobMap[benchId];
  const setKnob=(k,v)=>setKnobMap(m=>({...m,[benchId]:{...m[benchId],[k]:v}}));
  const {out}=useMemo(()=>buildDevice(dev,knobs,feel,passages,moments),[dev,knobs,feel,passages,moments]);
  const st=statsOf(out);
  const norm=normKnobs(dev.id,knobs);
  const chan=CHANNELS[dev.id];
  const nStamped=Object.values(stamped).filter(Boolean).length;

  return (
    <>
      <div style={{display:"flex",alignItems:"baseline",gap:14,marginBottom:14}}>
        <h1 style={{margin:0,fontSize:26,fontWeight:800,letterSpacing:"-0.02em"}}>Polish</h1>
        <span style={{fontSize:13,color:"var(--text-muted)"}}>One pipeline. Each station forges a device-ready file from your <strong style={{color:"#ff7a3a"}}>Voicing + Moments</strong> output.</span>
        <span style={{flex:1}}/><span className="mono" style={{fontSize:12,color:"var(--text-dim)"}}>{nStamped}/{DEVICES.length} stamped</span>
      </div>
      <div style={{...CARD,padding:16,marginBottom:16}}>
        <div style={{display:"flex",alignItems:"stretch",gap:10}}>
          <div style={{flex:"0 0 120px",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:8,background:"var(--surface-2)",border:"1px solid var(--border)",borderRadius:10,padding:12}}>
            <div style={{width:40,height:40,borderRadius:"50%",border:"1.5px solid #ff7a3a",display:"grid",placeItems:"center"}}><svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="#ff7a3a" strokeWidth={1.8}><path d="M 2 12 Q 6 4 10 12 T 18 12 T 22 12"/></svg></div>
            <div style={{textAlign:"center"}}><div style={{fontSize:11,fontWeight:700,color:"#ff7a3a"}}>VOICING</div><div style={{fontSize:11,fontWeight:700,color:"#ff7a3a"}}>+ MOMENTS</div><div style={{fontSize:9.5,color:"var(--text-dim)",marginTop:2}}>source</div></div>
          </div>
          <div style={{display:"flex",alignItems:"center",color:"var(--text-dim)"}}>→</div>
          <div style={{flex:1,display:"grid",gridTemplateColumns:`repeat(${DEVICES.length},1fr)`,gap:10}}>
            {DEVICES.map((d,i)=>{ const on=d.id===benchId,done=stamped[d.id]; return (
              <button key={d.id} onClick={()=>setBenchId(d.id)} style={{textAlign:"left",background:on?d.hex+"12":"var(--surface-2)",border:`1px solid ${on?d.hex:"var(--border)"}`,borderRadius:10,padding:12,cursor:"pointer",color:"inherit"}}>
                <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:8}}>
                  <span style={{width:24,height:24,borderRadius:6,background:d.hex+"22",border:`1px solid ${d.hex}66`,display:"grid",placeItems:"center"}}><span style={{width:8,height:8,borderRadius:2,background:d.hex}}/></span>
                  <div style={{minWidth:0}}><div style={{fontSize:12.5,fontWeight:700,whiteSpace:"nowrap"}}>{d.name}</div><div style={{fontSize:9.5,color:"var(--text-dim)"}}>{d.sub}</div></div>
                </div>
                <MiniEnv dev={d} knobs={knobMap[d.id]} feel={feel} passages={passages} moments={moments} active={on}/>
                <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginTop:8}}>
                  <span className="mono" style={{fontSize:10,color:"var(--text-dim)"}}>{String(i+1).padStart(2,"0")}</span>
                  {done?(<span style={{fontSize:9,fontWeight:700,letterSpacing:".06em",color:"#3ed598",textTransform:"uppercase"}}>✓ stamped</span>)
                    :on?(<span style={{fontSize:9,fontWeight:700,letterSpacing:".04em",color:d.hex,textTransform:"uppercase",whiteSpace:"nowrap",border:`1px solid ${d.hex}`,borderRadius:3,padding:"1px 6px"}}>● in forge</span>)
                    :(<span style={{fontSize:9,fontWeight:700,letterSpacing:".06em",color:"var(--text-dim)",textTransform:"uppercase"}}>pending</span>)}
                </div>
              </button>); })}
          </div>
        </div>
        <div className="mono" style={{fontSize:10,color:"var(--text-dim)",marginTop:10}}>↑ click a station to bring it to the bench · cards show the whole track · Stamp forges the file</div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 360px",gap:14}}>
        <div style={{...CARD,padding:18}}>
          <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:14}}>
            <span style={{width:34,height:34,borderRadius:8,background:dev.hex+"22",border:`1px solid ${dev.hex}`,display:"grid",placeItems:"center"}}><span style={{width:10,height:10,borderRadius:3,background:dev.hex}}/></span>
            <div><div className="eyebrow" style={{color:dev.hex}}>On the bench</div><h2 style={{margin:0,fontSize:20,fontWeight:800}}>{dev.name}</h2></div>
            <span style={{flex:1}}/>
            <div style={{textAlign:"right"}}>
              <div className="eyebrow">Output</div>
              {chan
                ? <div className="mono" style={{fontSize:11,color:dev.hex,fontWeight:600,lineHeight:1.45}}>{dev.id==="estim"?"estim/":"axes/"} · {chan.length} channels<div style={{color:"var(--text-dim)",fontWeight:400,fontSize:10}}>{CHANNEL_FILES[dev.id].map(f=>f.replace("ipzz-125.","")).join(" · ")}</div></div>
                : <div className="mono" style={{fontSize:12,color:dev.hex,fontWeight:600}}>{dev.file}</div>}
            </div>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:16,marginBottom:8,flexWrap:"wrap"}}>
            <span className="eyebrow">{chan?"Channels · what the device gets":"Channel preview · what the device gets"}</span><span style={{flex:1}}/>
            {chan
              ? deriveChannels(dev,[0],feel,1).map(c=>(
                  <span key={c.label} style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:16,height:3,background:c.color,borderRadius:2}}/> {c.label}</span>))
              : <>
                <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:16,borderTop:"1px dashed #9ba3c4"}}/> input</span>
                <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:14,height:9,background:"#ff8c4233",borderRadius:2}}/> knob effect</span>
                <span style={{display:"flex",alignItems:"center",gap:6,fontSize:10.5,color:"var(--text-muted)"}}><span style={{width:16,height:3,background:dev.hex,borderRadius:2}}/> to device</span>
              </>}
          </div>
          <Bench dev={dev} knobs={knobs} feel={feel} passages={passages} moments={moments}/>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginTop:14}}>
            {[["rms",st.rms],["peak Δ",st.peak+"%"],["lead",norm.lead+" ms"]].map(([k,v])=>(
              <div key={k} style={{background:"var(--surface-2)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 12px"}}><div className="eyebrow">{k}</div><div className="mono" style={{fontSize:18,fontWeight:700,color:dev.hex,marginTop:3}}>{v}</div></div>))}
          </div>
        </div>
        <div style={{...CARD,padding:18,display:"flex",flexDirection:"column"}}>
          <div className="eyebrow" style={{color:dev.hex,marginBottom:2}}>Hammer &amp; tongs</div>
          <div style={{fontSize:11.5,color:"var(--text-muted)",marginBottom:16}}>{KNOBS[dev.id].sub}</div>
          {KNOBS[dev.id].specs.map(s=>(
            <Knob key={s.key} label={s.label} value={knobs[s.key]} onChange={v=>setKnob(s.key,v)} min={s.min} max={s.max} step={s.step} fill={dev.hex} fmt={s.fmt} hint={s.hint}/>
          ))}
          <span style={{flex:1}}/>
          <button onClick={()=>setStamped(s=>({...s,[benchId]:!s[benchId]}))} style={{marginTop:12,padding:"12px",borderRadius:10,border:"none",cursor:"pointer",
            background:stamped[benchId]?"var(--surface-2)":dev.hex,color:stamped[benchId]?dev.hex:"#0e1117",fontWeight:700,fontSize:13.5,
            boxShadow:stamped[benchId]?"none":`0 0 24px ${dev.hex}44`,border:stamped[benchId]?`1px solid ${dev.hex}55`:"none"}}>
            {stamped[benchId]?"✓ Stamped — re-forge":"Stamp this pass"}
          </button>
        </div>
      </div>
      <div style={{marginTop:14,fontSize:11.5,color:"var(--text-dim)",lineHeight:1.6,maxWidth:920}}>The dashed <em style={{fontStyle:"normal",color:"var(--text-muted)"}}>input</em> is the one device-agnostic signal from Voicing + Moments. Each station conditions it for its hardware — nothing is re-authored. <strong style={{color:"var(--text-muted)"}}>Stamp</strong> writes that device's funscript.</div>
    </>
  );
}

/* ───────────── App · single source of truth ───────────── */
function App(){
  const [tab,setTab]=useState("Voicing");
  // shared signal model
  const [feel,setFeel]=useState({ intensity:0.62, pace:0.34, wildness:0.22, sharpness:0.4, depth:0.55, focus:0.45 });
  const [passages,setPassages]=useState([
    { id:"p1", shape:"build", from:0,    to:1,    lo:0.40, hi:1.00, label:"Ch1 → Ch21" },
    { id:"p2", shape:"build", from:0.76, to:0.81, lo:0.55, hi:1.00, label:"Ch17 → Ch17" },
  ]);
  const [moments,setMoments]=useState([
    {id:1,typeId:"swell",at:0.16,dur:0.045,amount:0.32},
    {id:2,typeId:"hold", at:0.45,dur:0.022,amount:0.30},
    {id:3,typeId:"hit",  at:0.71,dur:0.010,amount:0.55},
  ]);
  const [playhead,setPlayhead]=useState(0.30);
  // moments-tab ui state (kept in app so it persists across tab switches)
  const [armed,setArmed]=useState("hold");
  const [selId,setSelId]=useState(2);
  // polish-tab ui state
  const [benchId,setBenchId]=useState("estim");
  const [stamped,setStamped]=useState({});
  const [knobMap,setKnobMap]=useState(()=>{ const m={}; DEVICES.forEach(d=>{ const o={}; KNOBS[d.id].specs.forEach(s=>o[s.key]=s.def); m[d.id]=o; }); return m; });

  // shared playhead animation
  useEffect(()=>{ let raf,last=performance.now();
    const loop=now=>{ const dt=(now-last)/1000; last=now; setPlayhead(p=>(p+dt*0.018)%1); raf=requestAnimationFrame(loop); };
    raf=requestAnimationFrame(loop); return ()=>cancelAnimationFrame(raf); },[]);

  const word=useMemo(()=>{ const p=[]; p.push(feel.intensity>0.66?"Intense":feel.intensity<0.33?"Gentle":"Balanced");
    if(feel.wildness>0.55)p.push("Wild"); else if(feel.wildness<0.2)p.push("Steady"); return p.join(" · "); },[feel]);
  const nStamped=Object.values(stamped).filter(Boolean).length;

  return (
    <div style={{height:"100vh",display:"flex",flexDirection:"column",background:"var(--bg)"}}>
      <TopBar tab={tab}/><TabStrip tab={tab} onNav={setTab}/>
      <div style={{flex:1,overflow:"auto",padding:"18px 24px",minHeight:0}}>
        {tab==="Voicing" && <VoicingView feel={feel} setFeel={setFeel} passages={passages} setPassages={setPassages} moments={moments} playhead={playhead} onScrub={setPlayhead}/>}
        {tab==="Moments" && <MomentsView feel={feel} passages={passages} moments={moments} setMoments={setMoments} playhead={playhead} onScrub={setPlayhead} armed={armed} setArmed={setArmed} selId={selId} setSelId={setSelId}/>}
        {tab==="Polish"  && <PolishView feel={feel} passages={passages} moments={moments} benchId={benchId} setBenchId={setBenchId} knobMap={knobMap} setKnobMap={setKnobMap} stamped={stamped} setStamped={setStamped}/>}
      </div>
      {/* status bar */}
      <div className="mono" style={{height:28,background:"var(--bg)",borderTop:"1px solid var(--border)",display:"flex",alignItems:"center",padding:"0 16px",gap:14,fontSize:10.5,color:"var(--text-dim)",flexShrink:0}}>
        <span style={{color:"#3ed598"}}>● ready</span><span>·</span>
        <span>one source</span><span>·</span><span>{moments.length} moments</span><span>·</span>
        <span style={{color:"var(--text-muted)"}}>feel: <span style={{color:"#ff7a3a"}}>{word}</span></span>
        <span style={{flex:1}}/>
        <span>{nStamped}/{DEVICES.length} forged</span><span>·</span>
        <span style={{color:"var(--text-muted)"}}>{tab==="Polish"?"Voicing + Moments → device":tab==="Moments"?"layered on the bed":"→ Moments → Polish"}</span>
      </div>
    </div>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
