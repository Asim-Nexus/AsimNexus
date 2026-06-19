/**
 * AsimOrbMaster.jsx - Production Floating Orb & Chat
 * Features: Mobile gestures, Themes (Dark/Light/Nepal/Dharma), Keyboard shortcuts, WebSocket, Position memory
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, Activity, Radio, Eye, X, Maximize2, Minimize2, Moon, Sun, HelpCircle, Zap, Menu } from 'lucide-react';
import ComplexVisualizationOrb from './ComplexVisualizationOrb';
import UnifiedChat from './UnifiedChat';
import voiceAnalysisService from '../../services/VoiceAnalysisService';

const THEMES = {
  dark: { name:'Dark', bg:'rgba(12,12,28,0.98)', border:'1px solid rgba(102,126,234,0.35)', text:'#fff', muted:'rgba(255,255,255,0.5)', primary:'#667eea', glow:'rgba(102,126,234,0.25)', controls:'rgba(0,0,0,0.25)', input:'rgba(255,255,255,0.06)', shadow:'0 30px 60px rgba(0,0,0,0.6),0 0 120px rgba(102,126,234,0.15)' },
  light: { name:'Light', bg:'rgba(248,249,250,0.98)', border:'1px solid rgba(0,0,0,0.1)', text:'#212529', muted:'rgba(0,0,0,0.5)', primary:'#667eea', glow:'rgba(102,126,234,0.15)', controls:'rgba(0,0,0,0.04)', input:'rgba(0,0,0,0.04)', shadow:'0 20px 50px rgba(0,0,0,0.15),0 0 60px rgba(102,126,234,0.08)' },
  nepal: { name:'Nepal', bg:'rgba(20,10,15,0.98)', border:'1px solid rgba(220,20,60,0.4)', text:'#fff5f0', muted:'rgba(255,245,240,0.5)', primary:'#dc143c', glow:'rgba(220,20,60,0.25)', controls:'rgba(0,0,0,0.25)', input:'rgba(255,255,255,0.06)', shadow:'0 30px 60px rgba(0,0,0,0.6),0 0 120px rgba(220,20,60,0.15)' },
  dharma: { name:'Dharma', bg:'rgba(10,8,20,0.98)', border:'1px solid rgba(255,165,0,0.4)', text:'#ffecd1', muted:'rgba(255,236,209,0.5)', primary:'#ff8c00', glow:'rgba(255,140,0,0.25)', controls:'rgba(0,0,0,0.25)', input:'rgba(255,255,255,0.06)', shadow:'0 30px 60px rgba(0,0,0,0.6),0 0 120px rgba(255,140,0,0.15)' },
};

const ORB_SIZE = 58, SNAP = 70, MIN_W = 280, MIN_H = 340, MAX_W = 850, MAX_H = 750;
const lerp = (a,b,t) => a+(b-a)*t;
const clamp = (v,m,M) => Math.max(m,Math.min(M,v));
const zones = (w,h) => [{x:8,y:8},{x:w/2-ORB_SIZE/2,y:8},{x:w-ORB_SIZE-8,y:8},{x:8,y:h/2-ORB_SIZE/2},{x:w-ORB_SIZE-8,y:h/2-ORB_SIZE/2},{x:8,y:h-ORB_SIZE-8},{x:w/2-ORB_SIZE/2,y:h-ORB_SIZE-8},{x:w-ORB_SIZE-8,y:h-ORB_SIZE-8}];

export default function AsimOrbMaster({user,onCommand,systemMetrics={}}) {
  const [themeKey,setThemeKey] = useState(()=>{try{return localStorage.getItem('asimTheme')||'dark'}catch{return'dark'}});
  const theme = THEMES[themeKey]||THEMES.dark;
  const nextTheme = () => { const k=Object.keys(THEMES); const nk=k[(k.indexOf(themeKey)+1)%k.length]; setThemeKey(nk); localStorage.setItem('asimTheme',nk); };

  const [isOpen,setIsOpen] = useState(false);
  const [visMode,setVisMode] = useState('fractal');
  const [isRecording,setIsRecording] = useState(false);
  const [voiceData,setVoiceData] = useState(null);
  const [pulsePhase,setPulsePhase] = useState(0);
  const [showHelp,setShowHelp] = useState(false);
  const [showQuick,setShowQuick] = useState(false);

  const [orbPos,setOrbPos] = useState(()=>{try{const s=localStorage.getItem('asimOrbPos');return s?JSON.parse(s):{x:window.innerWidth-ORB_SIZE-16,y:window.innerHeight-ORB_SIZE-16}}catch{return{x:window.innerWidth-ORB_SIZE-16,y:window.innerHeight-ORB_SIZE-16}}});
  const [orbVis,setOrbVis] = useState(orbPos);
  const [isOrbDrag,setIsOrbDrag] = useState(false);
  const [orbOff,setOrbOff] = useState({x:0,y:0});
  const [isOrbHover,setIsOrbHover] = useState(false);

  const [popupSize,setPopupSize] = useState(()=>{try{const s=localStorage.getItem('asimPopupSize');return s?JSON.parse(s):{width:340,height:480}}catch{return{width:340,height:480}}});
  const [popupPos,setPopupPos] = useState(()=>{try{const s=localStorage.getItem('asimPopupPos');return s?JSON.parse(s):{x:window.innerWidth-380,y:window.innerHeight-520}}catch{return{x:window.innerWidth-380,y:window.innerHeight-520}}});
  const [popupVis,setPopupVis] = useState(popupPos);
  const [isPopupDrag,setIsPopupDrag] = useState(false);
  const [popupOff,setPopupOff] = useState({x:0,y:0});
  const [isResize,setIsResize] = useState(false);
  const [rs,setRs] = useState({x:0,y:0,w:0,h:0,px:0,py:0});
  const [rc,setRc] = useState('');

  const rafRef=useRef(); const touchStartY=useRef(0);

  useEffect(()=>{let t=0;const loop=()=>{t+=0.05;setPulsePhase(t);rafRef.current=requestAnimationFrame(loop)};rafRef.current=requestAnimationFrame(loop);return()=>cancelAnimationFrame(rafRef.current)},[]);
  useEffect(()=>{let a;const loop=()=>{setOrbVis(p=>({x:lerp(p.x,orbPos.x,0.18),y:lerp(p.y,orbPos.y,0.18)}));setPopupVis(p=>({x:lerp(p.x,popupPos.x,0.14),y:lerp(p.y,popupPos.y,0.14)}));a=requestAnimationFrame(loop)};a=requestAnimationFrame(loop);return()=>cancelAnimationFrame(a)},[orbPos,popupPos]);
  useEffect(()=>{if(!isOrbDrag)localStorage.setItem('asimOrbPos',JSON.stringify(orbPos))},[orbPos,isOrbDrag]);
  useEffect(()=>{if(!isPopupDrag&&!isResize){localStorage.setItem('asimPopupPos',JSON.stringify(popupPos));localStorage.setItem('asimPopupSize',JSON.stringify(popupSize))}},[popupPos,popupSize,isPopupDrag,isResize]);

  useEffect(()=>{if(isOpen)voiceAnalysisService.init()},[isOpen]);
  const toggleVoice=async()=>{if(!isRecording){if(await voiceAnalysisService.init()){setIsRecording(true);setVisMode('spectrum');voiceAnalysisService.startAnalysis(a=>setVoiceData(a))}}else{setIsRecording(false);voiceAnalysisService.stopAnalysis()}};

  const snapOrb=useCallback((x,y)=>{const z=zones(window.innerWidth,window.innerHeight);let b={x,y},bd=Infinity;z.forEach(p=>{const d=Math.hypot(p.x-x,p.y-y);if(d<SNAP&&d<bd){bd=d;b=p}});return b},[]);

  useEffect(()=>{
    if(!isOrbDrag&&!isPopupDrag&&!isResize)return;
    const onMove=e=>{
      let cx,cy;
      if(e.touches){cx=e.touches[0].clientX;cy=e.touches[0].clientY}
      else{cx=e.clientX;cy=e.clientY}
      if(isOrbDrag)setOrbPos({x:clamp(cx-orbOff.x,0,window.innerWidth-ORB_SIZE),y:clamp(cy-orbOff.y,0,window.innerHeight-ORB_SIZE)});
      if(isPopupDrag)setPopupPos({x:clamp(cx-popupOff.x,-60,window.innerWidth-popupSize.width+60),y:clamp(cy-popupOff.y,-30,window.innerHeight-popupSize.height+30)});
      if(isResize){
        const dx=cx-rs.x, dy=cy-rs.y;
        let nw=rs.w, nh=rs.h, nx=rs.px, ny=rs.py;
        if(rc.includes('e')) nw=clamp(rs.w+dx,MIN_W,MAX_W);
        if(rc.includes('s')) nh=clamp(rs.h+dy,MIN_H,MAX_H);
        if(rc.includes('w')){ nw=clamp(rs.w-dx,MIN_W,MAX_W); nx=rs.px+(rs.w-nw) }
        if(rc.includes('n')){ nh=clamp(rs.h-dy,MIN_H,MAX_H); ny=rs.py+(rs.h-nh) }
        setPopupSize({width:nw,height:nh});
        if(nx!==rs.px||ny!==rs.py) setPopupPos({x:nx,y:ny});
      }
    };
    const onUp=()=>{
      if(isOrbDrag){setIsOrbDrag(false);const s=snapOrb(orbPos.x,orbPos.y);setOrbPos(s)}
      if(isPopupDrag)setIsPopupDrag(false);
      if(isResize)setIsResize(false);
    };
    window.addEventListener('mousemove',onMove);
    window.addEventListener('mouseup',onUp);
    window.addEventListener('touchmove',onMove,{passive:false});
    window.addEventListener('touchend',onUp);
    return()=>{
      window.removeEventListener('mousemove',onMove);
      window.removeEventListener('mouseup',onUp);
      window.removeEventListener('touchmove',onMove);
      window.removeEventListener('touchend',onUp);
    };
  },[isOrbDrag,isPopupDrag,isResize,orbOff,popupOff,orbPos,popupPos,popupSize,rs,rc,snapOrb]);

  useEffect(()=>{const onKey=e=>{if(e.key==='Escape'){setIsOpen(false);setShowHelp(false);setShowQuick(false);setIsRecording(false)}if(e.altKey&&e.key==='Enter'){e.preventDefault();setIsOpen(o=>!o)}if(e.altKey&&e.key==='v'){e.preventDefault();toggleVoice()}if(e.altKey&&e.key==='1')setVisMode('fractal');if(e.altKey&&e.key==='2')setVisMode('wave');if(e.altKey&&e.key==='3')setVisMode('spectrum');if(e.altKey&&(e.key==='+'||e.key==='=')){e.preventDefault();setPopupSize(p=>({width:clamp(p.width+40,MIN_W,MAX_W),height:clamp(p.height+40,MIN_H,MAX_H)}))}if(e.altKey&&e.key==='-'){e.preventDefault();setPopupSize(p=>({width:clamp(p.width-40,MIN_W,MAX_W),height:clamp(p.height-40,MIN_H,MAX_H)}))}if(e.altKey&&e.key==='m'){e.preventDefault();nextTheme()}if(e.altKey&&e.key==='h'){e.preventDefault();setShowHelp(h=>!h)}};window.addEventListener('keydown',onKey);return()=>window.removeEventListener('keydown',onKey)},[isRecording,themeKey]);

  const glow=0.4+Math.sin(pulsePhase)*0.3;
  const orbScale=isOrbHover&&!isOrbDrag?1.12:1;
  const health=systemMetrics.health||0.7;
  const color=health>0.8?'#22c55e':health>0.5?theme.primary:'#f59e0b';
  const handleQuick=a=>{if(a==='voice')toggleVoice();if(a==='help')setShowHelp(true);if(a==='fractal')setVisMode('fractal');if(a==='wave')setVisMode('wave');if(a==='spectrum')setVisMode('spectrum');if(a==='close'){setIsOpen(false);setIsRecording(false)}};

  const handlePopupTouchStart=e=>{touchStartY.current=e.touches[0].clientY;};
  const handlePopupTouchMove=e=>{if(!isPopupDrag&&!isResize&&e.touches.length===1){const diff=touchStartY.current-e.touches[0].clientY;if(diff<-120){setIsOpen(false);setIsRecording(false);}}};

  return (
    <>
      {isOrbDrag && <div style={{position:'fixed',inset:0,zIndex:9998,pointerEvents:'none'}}>{zones(window.innerWidth,window.innerHeight).map((z,i)=><div key={i} style={{position:'absolute',left:z.x-6,top:z.y-6,width:ORB_SIZE+12,height:ORB_SIZE+12,borderRadius:'50%',border:'2px dashed rgba(102,126,234,0.35)',opacity:0.5}}/>)}</div>}

      {!isOpen && (
        <div onMouseDown={e=>{setIsOrbDrag(true);setOrbOff({x:e.clientX-orbPos.x,y:e.clientY-orbPos.y})}} onTouchStart={e=>{const t=e.touches[0];setIsOrbDrag(true);setOrbOff({x:t.clientX-orbPos.x,y:t.clientY-orbPos.y})}} onMouseEnter={()=>setIsOrbHover(true)} onMouseLeave={()=>setIsOrbHover(false)} onClick={()=>{if(!isOrbDrag){setIsOpen(true);setIsOrbHover(false)}}} style={{position:'fixed',left:orbVis.x,top:orbVis.y,width:ORB_SIZE,height:ORB_SIZE,borderRadius:'50%',background:`radial-gradient(circle at 30% 30%,${color}dd,${color}99)`,boxShadow:`0 0 ${20+glow*25}px ${color}88,0 0 ${50+glow*50}px ${color}44`,cursor:isOrbDrag?'grabbing':'grab',zIndex:10000,transform:`scale(${orbScale})`,transition:isOrbDrag?'none':'transform 0.35s cubic-bezier(0.34,1.56,0.64,1.275)',userSelect:'none',WebkitUserSelect:'none'}}>
          {isRecording && <div style={{position:'absolute',inset:-4,borderRadius:'50%',border:'2px solid rgba(239,68,68,0.7)',animation:'recPulse 1s ease-out infinite'}}/>}
          <img src="/asim-logo.png" alt="Asim Nexus" draggable={false} style={{width:'100%',height:'100%',borderRadius:'50%',objectFit:'cover',padding:3}} onError={e=>{e.target.src='/ui/AsiM logo.png'}} />
          {systemMetrics.mesh_health>0.85 && <div style={{position:'absolute',bottom:2,right:2,width:10,height:10,borderRadius:'50%',background:'#22c55e',boxShadow:'0 0 8px #22c55e',border:'2px solid rgba(10,10,26,0.9)'}}/>}
          {isOrbHover&&!isOrbDrag && <div style={{position:'absolute',bottom:70,left:'50%',transform:'translateX(-50%)',background:'rgba(10,10,26,0.95)',padding:'6px 14px',borderRadius:10,fontSize:11,color:'#fff',whiteSpace:'nowrap',border:'1px solid rgba(255,255,255,0.15)',backdropFilter:'blur(12px)',zIndex:10001,pointerEvents:'none'}}>Asim Nexus - Click to open</div>}
        </div>
      )}

      {isOpen && (
        <div onTouchStart={handlePopupTouchStart} onTouchMove={handlePopupTouchMove} style={{position:'fixed',left:popupVis.x,top:popupVis.y,width:popupSize.width,height:popupSize.height,background:theme.bg,borderRadius:18,border:theme.border,boxShadow:theme.shadow,zIndex:10000,display:'flex',flexDirection:'column',overflow:'hidden',transition:isPopupDrag||isResize?'none':'width 0.25s ease,height 0.25s ease',cursor:isPopupDrag?'grabbing':'default'}}>
          <div onMouseDown={e=>{setIsPopupDrag(true);setPopupOff({x:e.clientX-popupPos.x,y:e.clientY-popupPos.y})}} onTouchStart={e=>{const t=e.touches[0];setIsPopupDrag(true);setPopupOff({x:t.clientX-popupPos.x,y:t.clientY-popupPos.y})}} style={{position:'absolute',top:0,left:50,right:90,height:28,cursor:'grab',zIndex:10002,display:'flex',alignItems:'center',justifyContent:'center'}}><div style={{width:40,height:4,background:'rgba(255,255,255,0.2)',borderRadius:2}}/></div>
          <button onClick={()=>setShowQuick(true)} style={{position:'absolute',top:6,left:8,zIndex:10003,background:'none',border:'none',color:theme.muted,cursor:'pointer',padding:4}}><Menu size={16}/></button>
          <button onClick={nextTheme} style={{position:'absolute',top:6,right:68,zIndex:10003,background:'none',border:'none',color:theme.primary,cursor:'pointer',padding:4}}>{themeKey==='light'?<Sun size={16}/>:themeKey==='nepal'?<Zap size={16}/>:themeKey==='dharma'?<Eye size={16}/>:<Moon size={16}/>}</button>
          <button onClick={()=>setShowHelp(true)} style={{position:'absolute',top:6,right:44,zIndex:10003,background:'none',border:'none',color:theme.muted,cursor:'pointer',padding:4}}><HelpCircle size={16}/></button>
          <ComplexVisualizationOrb mode={visMode} systemMetrics={systemMetrics} voiceData={voiceData} isRecording={isRecording}/>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'6px 10px',background:theme.controls,borderBottom:theme.border,flexShrink:0}}>
            <div style={{display:'flex',gap:3}}>
              {[{id:'fractal',icon:Eye},{id:'wave',icon:Radio},{id:'spectrum',icon:Activity}].map(m=>{const Icon=m.icon;const active=visMode===m.id;return <button key={m.id} onClick={()=>setVisMode(m.id)} style={{display:'flex',alignItems:'center',gap:3,padding:'4px 8px',borderRadius:6,border:'none',background:active?`${theme.primary}55`:'rgba(255,255,255,0.08)',color:active?'#fff':theme.muted,fontSize:11,cursor:'pointer',transition:'all 0.2s'}}><Icon size={13}/></button>})}
            </div>
            <div style={{display:'flex',alignItems:'center',gap:4}}>
              <button onClick={toggleVoice} style={{padding:'4px 8px',borderRadius:6,border:'none',background:isRecording?'rgba(239,68,68,0.35)':'rgba(255,255,255,0.08)',color:isRecording?'#ef4444':theme.muted,fontSize:11,cursor:'pointer',animation:isRecording?'recPulse 1.2s infinite':'none',display:'flex',alignItems:'center',gap:3}}><Mic size={13}/></button>
              <button onClick={()=>{const w=window.innerWidth-40;const h=window.innerHeight-100;const x=20;const y=20;setPopupSize({width:Math.min(w,MAX_W),height:Math.min(h,MAX_H)});setPopupPos({x,y});}} style={{padding:4,borderRadius:6,border:'none',background:'rgba(255,255,255,0.08)',color:theme.text,cursor:'pointer'}}><Maximize2 size={13}/></button>
              <button onClick={()=>{setIsOpen(false);setIsRecording(false)}} style={{padding:4,borderRadius:6,border:'none',background:'rgba(239,68,68,0.2)',color:'#ef4444',cursor:'pointer'}}><X size={13}/></button>
            </div>
          </div>
          <div style={{flex:1,overflow:'hidden',minHeight:0}}><UnifiedChat user={user} onCommand={onCommand} compact={popupSize.width<500} theme={theme} onClose={()=>{setIsOpen(false);setIsRecording(false)}} popupSize={popupSize} /></div>
          {['nw','ne','sw','se'].map(corner=>{const isL=corner.includes('w');const isT=corner.includes('n');const c=isT?(isL?'nw-resize':'ne-resize'):(isL?'sw-resize':'se-resize');return <div key={corner} onMouseDown={e=>{e.preventDefault();e.stopPropagation();setIsResize(true);setRc(corner);setRs({x:e.clientX,y:e.clientY,w:popupSize.width,h:popupSize.height,px:popupPos.x,py:popupPos.y})}} style={{position:'absolute',[isT?'top':'bottom']:0,[isL?'left':'right']:0,width:16,height:16,cursor:c,zIndex:10003}} title="Drag to resize"/>})}
        </div>
      )}

      {showHelp && (
        <div onClick={()=>setShowHelp(false)} style={{position:'fixed',inset:0,zIndex:10100,display:'flex',alignItems:'center',justifyContent:'center',background:'rgba(0,0,0,0.6)',backdropFilter:'blur(6px)'}}>
          <div onClick={e=>e.stopPropagation()} style={{width:380,maxWidth:'92vw',background:theme.bg,borderRadius:18,border:theme.border,boxShadow:theme.shadow,padding:24,color:theme.text,maxHeight:'85vh',overflow:'auto'}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}}><h3 style={{margin:0,fontSize:18}}>⌨️ Shortcuts</h3><button onClick={()=>setShowHelp(false)} style={{background:'none',border:'none',color:theme.muted,cursor:'pointer'}}><X size={18}/></button></div>
            {[
              ['Alt+Enter','Toggle Orb'],['Alt+V','Voice Record'],['Alt+1','Fractal'],['Alt+2','Wave'],['Alt+3','Spectrum'],
              ['Alt+Plus','Bigger Popup'],['Alt+Minus','Smaller Popup'],['Alt+M','Toggle Theme'],['Alt+H','This Help'],['Esc','Close/Stop']
            ].map(([k,d],i)=><div key={i} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 12px',borderRadius:8,background:i%2?theme.controls:'transparent',marginBottom:4}}><code style={{background:theme.glow,color:theme.primary,padding:'3px 8px',borderRadius:6,fontSize:12,fontWeight:600}}>{k}</code><span style={{fontSize:13,color:theme.muted}}>{d}</span></div>)}
            <div style={{marginTop:16,paddingTop:12,borderTop:theme.border}}><h4 style={{margin:'0 0 8px',fontSize:14}}>🖱️ Touch</h4>
              {['Tap Orb → Open Chat','Drag Orb → Move (auto-snap)','Drag top bar → Move popup','Drag corner → Resize','Swipe down → Close popup'].map((t,i)=><div key={i} style={{fontSize:12,color:theme.muted,padding:'3px 0',display:'flex',gap:8}}><span>•</span><span>{t}</span></div>)}
            </div>
            <div style={{marginTop:16,textAlign:'center'}}><button onClick={()=>setShowHelp(false)} style={{background:theme.primary,color:'#fff',border:'none',borderRadius:8,padding:'8px 24px',fontSize:13,cursor:'pointer'}}>Got it!</button></div>
          </div>
        </div>
      )}

      {showQuick && (
        <div onClick={()=>setShowQuick(false)} style={{position:'fixed',inset:0,zIndex:10099,display:'flex',alignItems:'flex-end',justifyContent:'center',background:'rgba(0,0,0,0.4)',padding:'0 20px 40px'}}>
          <div onClick={e=>e.stopPropagation()} style={{width:'100%',maxWidth:320,background:theme.bg,borderRadius:18,border:theme.border,boxShadow:theme.shadow,padding:'12px 0'}}>
            {[{icon:Mic,label:'Voice Input',a:'voice'},{icon:HelpCircle,label:'Shortcuts',a:'help'},{icon:Eye,label:'Fractal',a:'fractal'},{icon:Radio,label:'Wave',a:'wave'},{icon:Activity,label:'Spectrum',a:'spectrum'},{icon:X,label:'Close',a:'close'}].map((item,i)=><button key={i} onClick={()=>{handleQuick(item.a);setShowQuick(false)}} style={{display:'flex',alignItems:'center',gap:14,width:'100%',padding:'12px 20px',border:'none',background:'none',color:theme.text,cursor:'pointer',fontSize:15,textAlign:'left',borderBottom:i<5?`1px solid ${theme.muted}22`:'none'}}><item.icon size={20} color={theme.primary}/>{item.label}</button>)}
          </div>
        </div>
      )}

      <style>{`@keyframes recPulse {0%{transform:scale(1);opacity:1}100%{transform:scale(1.6);opacity:0}}`}</style>
    </>
  );
}
