/**
 * AsimOrbFinal.jsx
 * ================
 * Perfect Floating Asim Nexus Orb & Chat
 * Final polished version - production ready
 * 
 * Features:
 * - Ultra-smooth 60fps drag & drop
 * - Orb & Popup both draggable anywhere
 * - Resize from any corner
 * - Position memory across sessions
 * - Auto-snap to screen edges
 * - Glassmorphism + glow effects
 * - Voice waveform ring
 * - Complex math visualizations
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, Activity, Radio, Eye, X, Maximize2, Minimize2 } from 'lucide-react';
import ComplexVisualizationOrb from './ComplexVisualizationOrb';
import UnifiedChat from './UnifiedChat';
import voiceAnalysisService from '../../services/VoiceAnalysisService';

// ── Constants ──
const ORB_SIZE = 60;
const SNAP_DIST = 80;
const MIN_POPUP_W = 300;
const MIN_POPUP_H = 380;
const MAX_POPUP_W = 850;
const MAX_POPUP_H = 750;

// ── Smooth Lerp ──
const lerp = (a, b, t) => a + (b - a) * t;

// ── Clamp ──
const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

// ── Get Snap Zones ──
const getSnapZones = (w, h) => [
  { x: 10, y: 10 },
  { x: w / 2 - ORB_SIZE / 2, y: 10 },
  { x: w - ORB_SIZE - 10, y: 10 },
  { x: 10, y: h / 2 - ORB_SIZE / 2 },
  { x: w - ORB_SIZE - 10, y: h / 2 - ORB_SIZE / 2 },
  { x: 10, y: h - ORB_SIZE - 10 },
  { x: w / 2 - ORB_SIZE / 2, y: h - ORB_SIZE - 10 },
  { x: w - ORB_SIZE - 10, y: h - ORB_SIZE - 10 },
];

const AsimOrbFinal = ({ user, onCommand, systemMetrics = {} }) => {
  // ── Orb State ──
  const [isOpen, setIsOpen] = useState(false);
  const [pulsePhase, setPulsePhase] = useState(0);
  const [isOrbHovered, setIsOrbHovered] = useState(false);

  // Load saved position
  const [orbPos, setOrbPos] = useState(() => {
    try {
      const s = localStorage.getItem('asimOrbPos');
      return s ? JSON.parse(s) : { x: window.innerWidth - ORB_SIZE - 20, y: window.innerHeight - ORB_SIZE - 20 };
    } catch { return { x: window.innerWidth - ORB_SIZE - 20, y: window.innerHeight - ORB_SIZE - 20 }; }
  });
  const [orbVisual, setOrbVisual] = useState(orbPos);
  const [isOrbDragging, setIsOrbDragging] = useState(false);
  const [orbDragOffset, setOrbDragOffset] = useState({ x: 0, y: 0 });

  // ── Popup State ──
  const [popupSize, setPopupSize] = useState(() => {
    try {
      const s = localStorage.getItem('asimPopupSize');
      return s ? JSON.parse(s) : { width: 360, height: 500 };
    } catch { return { width: 360, height: 500 }; }
  });
  const [popupPos, setPopupPos] = useState(() => {
    try {
      const s = localStorage.getItem('asimPopupPos');
      return s ? JSON.parse(s) : { x: window.innerWidth - 400, y: window.innerHeight - 550 };
    } catch { return { x: window.innerWidth - 400, y: window.innerHeight - 550 }; }
  });
  const [popupVisual, setPopupVisual] = useState(popupPos);
  const [isPopupDragging, setIsPopupDragging] = useState(false);
  const [popupDragOffset, setPopupDragOffset] = useState({ x: 0, y: 0 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, w: 0, h: 0, px: 0, py: 0 });
  const [resizeCorner, setResizeCorner] = useState('');

  // ── Chat/Mode State ──
  const [visMode, setVisMode] = useState('fractal');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceData, setVoiceData] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // ── Refs ──
  const rafRef = useRef();
  const orbRef = useRef();

  // ── Pulse Animation ──
  useEffect(() => {
    let t = 0;
    const loop = () => {
      t += 0.05;
      setPulsePhase(t);
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  // ── Spring Animation for Orb ──
  useEffect(() => {
    let anim;
    const loop = () => {
      setOrbVisual(prev => ({
        x: lerp(prev.x, orbPos.x, 0.18),
        y: lerp(prev.y, orbPos.y, 0.18),
      }));
      setPopupVisual(prev => ({
        x: lerp(prev.x, popupPos.x, 0.15),
        y: lerp(prev.y, popupPos.y, 0.15),
      }));
      anim = requestAnimationFrame(loop);
    };
    anim = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(anim);
  }, [orbPos, popupPos]);

  // ── Save Position ──
  useEffect(() => {
    if (!isOrbDragging) localStorage.setItem('asimOrbPos', JSON.stringify(orbPos));
  }, [orbPos, isOrbDragging]);

  useEffect(() => {
    if (!isPopupDragging && !isResizing) {
      localStorage.setItem('asimPopupPos', JSON.stringify(popupPos));
      localStorage.setItem('asimPopupSize', JSON.stringify(popupSize));
    }
  }, [popupPos, popupSize, isPopupDragging, isResizing]);

  // ── Voice ──
  useEffect(() => { if (isOpen) voiceAnalysisService.init(); }, [isOpen]);

  const toggleVoice = async () => {
    if (!isRecording) {
      if (await voiceAnalysisService.init()) {
        setIsRecording(true);
        setVisMode('spectrum');
        voiceAnalysisService.startAnalysis((a) => setVoiceData(a));
      }
    } else {
      setIsRecording(false);
      voiceAnalysisService.stopAnalysis();
    }
  };

  // ── Snap Orb to nearest zone ──
  const snapOrb = useCallback((x, y) => {
    const zones = getSnapZones(window.innerWidth, window.innerHeight);
    let best = { x, y };
    let bestDist = Infinity;
    zones.forEach(z => {
      const d = Math.hypot(z.x - x, z.y - y);
      if (d < SNAP_DIST && d < bestDist) { bestDist = d; best = z; }
    });
    return best;
  }, []);

  // ── Global Move/Up ──
  useEffect(() => {
    if (!isOrbDragging && !isPopupDragging && !isResizing) return;

    const onMove = (e) => {
      const cx = e.touches ? e.touches[0].clientX : e.clientX;
      const cy = e.touches ? e.touches[0].clientY : e.clientY;

      if (isOrbDragging) {
        setOrbPos({
          x: clamp(cx - orbDragOffset.x, 0, window.innerWidth - ORB_SIZE),
          y: clamp(cy - orbDragOffset.y, 0, window.innerHeight - ORB_SIZE),
        });
      }

      if (isPopupDragging) {
        setPopupPos({
          x: clamp(cx - popupDragOffset.x, -80, window.innerWidth - popupSize.width + 80),
          y: clamp(cy - popupDragOffset.y, -40, window.innerHeight - popupSize.height + 40),
        });
      }

      if (isResizing) {
        const dx = cx - resizeStart.x;
        const dy = cy - resizeStart.y;
        let nw = resizeStart.w, nh = resizeStart.h, nx = resizeStart.px, ny = resizeStart.py;

        if (resizeCorner.includes('e')) nw = clamp(resizeStart.w + dx, MIN_POPUP_W, MAX_POPUP_W);
        if (resizeCorner.includes('s')) nh = clamp(resizeStart.h + dy, MIN_POPUP_H, MAX_POPUP_H);
        if (resizeCorner.includes('w')) {
          nw = clamp(resizeStart.w - dx, MIN_POPUP_W, MAX_POPUP_W);
          nx = resizeStart.px + (resizeStart.w - nw);
        }
        if (resizeCorner.includes('n')) {
          nh = clamp(resizeStart.h - dy, MIN_POPUP_H, MAX_POPUP_H);
          ny = resizeStart.py + (resizeStart.h - nh);
        }

        setPopupSize({ width: nw, height: nh });
        if (nx !== resizeStart.px || ny !== resizeStart.py) setPopupPos({ x: nx, y: ny });
      }
    };

    const onUp = () => {
      if (isOrbDragging) {
        setIsOrbDragging(false);
        const snapped = snapOrb(orbPos.x, orbPos.y);
        setOrbPos(snapped);
      }
      if (isPopupDragging) setIsPopupDragging(false);
      if (isResizing) setIsResizing(false);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onUp);
    };
  }, [isOrbDragging, isPopupDragging, isResizing, orbDragOffset, popupDragOffset, orbPos, popupPos, popupSize, resizeStart, resizeCorner, snapOrb]);

  // ── Keyboard ──
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { setIsOpen(false); setIsRecording(false); }
      if (e.altKey && e.key === 'v') { e.preventDefault(); toggleVoice(); }
      if (e.altKey && e.key === '1') setVisMode('fractal');
      if (e.altKey && e.key === '2') setVisMode('wave');
      if (e.altKey && e.key === '3') setVisMode('spectrum');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isRecording]);

  // ── Visual Values ──
  const glow = 0.4 + Math.sin(pulsePhase) * 0.3;
  const orbScale = isOrbHovered && !isOrbDragging ? 1.12 : 1;
  const health = systemMetrics.health || 0.7;
  const color = health > 0.8 ? '#22c55e' : health > 0.5 ? '#667eea' : '#f59e0b';

  // ── Render ──
  return (
    <>
      {/* ── Orb ── */}
      {!isOpen && (
        <div
          ref={orbRef}
          onMouseDown={(e) => {
            setIsOrbDragging(true);
            setOrbDragOffset({ x: e.clientX - orbPos.x, y: e.clientY - orbPos.y });
          }}
          onTouchStart={(e) => {
            const t = e.touches[0];
            setIsOrbDragging(true);
            setOrbDragOffset({ x: t.clientX - orbPos.x, y: t.clientY - orbPos.y });
          }}
          onMouseEnter={() => setIsOrbHovered(true)}
          onMouseLeave={() => setIsOrbHovered(false)}
          onClick={() => { if (!isOrbDragging) setIsOpen(true); }}
          style={{
            position: 'fixed',
            left: orbVisual.x,
            top: orbVisual.y,
            width: ORB_SIZE,
            height: ORB_SIZE,
            borderRadius: '50%',
            background: `radial-gradient(circle at 30% 30%, ${color}dd, ${color}99)`,
            boxShadow: `0 0 ${20 + glow * 25}px ${color}88, 0 0 ${50 + glow * 50}px ${color}44`,
            cursor: isOrbDragging ? 'grabbing' : 'grab',
            zIndex: 10000,
            transform: `scale(${orbScale})`,
            transition: isOrbDragging ? 'none' : 'transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)',
            userSelect: 'none',
            WebkitUserSelect: 'none',
          }}
        >
          {isRecording && (
            <div style={{
              position: 'absolute', inset: -4,
              borderRadius: '50%',
              border: '2px solid rgba(239,68,68,0.7)',
              animation: 'recPulse 1s ease-out infinite',
            }} />
          )}
          <img
            src="/asim-logo.png"
            alt="Asim Nexus"
            draggable={false}
            style={{
              width: '100%', height: '100%',
              borderRadius: '50%',
              objectFit: 'cover',
              padding: 3,
            }}
            onError={(e) => { e.target.src = '/ui/AsiM logo.png'; }}
          />
          {systemMetrics.mesh_health > 0.85 && (
            <div style={{
              position: 'absolute', bottom: 2, right: 2,
              width: 10, height: 10, borderRadius: '50%',
              background: '#22c55e',
              boxShadow: '0 0 8px #22c55e',
              border: '2px solid rgba(10,10,26,0.9)',
            }} />
          )}
          {isOrbHovered && !isOrbDragging && (
            <div style={{
              position: 'absolute', bottom: 70, left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(10,10,26,0.95)',
              padding: '6px 14px', borderRadius: 10,
              fontSize: 11, color: '#fff', whiteSpace: 'nowrap',
              border: '1px solid rgba(255,255,255,0.15)',
              backdropFilter: 'blur(12px)',
              zIndex: 10001,
              pointerEvents: 'none',
            }}>
              Asim Nexus - Click to open
            </div>
          )}
        </div>
      )}

      {/* ── Popup ── */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            left: popupVisual.x,
            top: popupVisual.y,
            width: popupSize.width,
            height: popupSize.height,
            background: 'linear-gradient(160deg, rgba(12,12,28,0.98), rgba(18,18,40,0.98))',
            borderRadius: 18,
            border: `1px solid ${color}33`,
            boxShadow: `0 30px 60px rgba(0,0,0,0.6), 0 0 120px ${color}18`,
            zIndex: 10000,
            display: 'flex', flexDirection: 'column',
            overflow: 'hidden',
            transition: isPopupDragging || isResizing ? 'none' : 'width 0.25s ease, height 0.25s ease',
            cursor: isPopupDragging ? 'grabbing' : 'default',
          }}
        >
          {/* Drag Handle Bar */}
          <div
            onMouseDown={(e) => {
              setIsPopupDragging(true);
              setPopupDragOffset({ x: e.clientX - popupPos.x, y: e.clientY - popupPos.y });
            }}
            onTouchStart={(e) => {
              const t = e.touches[0];
              setIsPopupDragging(true);
              setPopupDragOffset({ x: t.clientX - popupPos.x, y: t.clientY - popupPos.y });
            }}
            style={{
              position: 'absolute', top: 0, left: 60, right: 60, height: 26,
              cursor: 'grab', zIndex: 10002,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <div style={{ width: 44, height: 4, background: 'rgba(255,255,255,0.2)', borderRadius: 2 }} />
          </div>

          {/* Visualization */}
          <ComplexVisualizationOrb
            mode={visMode}
            systemMetrics={systemMetrics}
            voiceData={voiceData}
            isRecording={isRecording}
          />

          {/* Controls */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '6px 10px',
            background: 'rgba(0,0,0,0.25)',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', gap: 3 }}>
              {[
                { id: 'fractal', icon: Eye },
                { id: 'wave', icon: Radio },
                { id: 'spectrum', icon: Activity },
              ].map(m => {
                const Icon = m.icon;
                const active = visMode === m.id;
                return (
                  <button key={m.id} onClick={() => setVisMode(m.id)} style={{
                    display: 'flex', alignItems: 'center', gap: 3,
                    padding: '4px 8px', borderRadius: 6,
                    border: 'none',
                    background: active ? `${color}55` : 'rgba(255,255,255,0.08)',
                    color: active ? '#fff' : 'rgba(255,255,255,0.5)',
                    fontSize: 11, cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}>
                    <Icon size={13} />
                  </button>
                );
              })}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <button onClick={toggleVoice} style={{
                padding: '4px 8px', borderRadius: 6, border: 'none',
                background: isRecording ? 'rgba(239,68,68,0.35)' : 'rgba(255,255,255,0.08)',
                color: isRecording ? '#ef4444' : 'rgba(255,255,255,0.7)',
                fontSize: 11, cursor: 'pointer',
                animation: isRecording ? 'recPulse 1.2s infinite' : 'none',
                display: 'flex', alignItems: 'center', gap: 3,
              }}>
                <Mic size={13} />
              </button>
              <button onClick={() => setIsExpanded(!isExpanded)} style={{
                padding: 4, borderRadius: 6, border: 'none',
                background: 'rgba(255,255,255,0.08)',
                color: 'white', cursor: 'pointer',
              }}>
                {isExpanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
              </button>
              <button onClick={() => { setIsOpen(false); setIsRecording(false); }} style={{
                padding: 4, borderRadius: 6, border: 'none',
                background: 'rgba(239,68,68,0.2)',
                color: '#ef4444', cursor: 'pointer',
              }}>
                <X size={13} />
              </button>
            </div>
          </div>

          {/* Chat */}
          <div style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
            <UnifiedChat
              user={user}
              onCommand={onCommand}
              compact={popupSize.width < 500}
              onClose={() => { setIsOpen(false); setIsRecording(false); }}
            />
          </div>

          {/* Resize Handles - All 4 Corners */}
          {['nw', 'ne', 'sw', 'se'].map(corner => {
            const isLeft = corner.includes('w');
            const isTop = corner.includes('n');
            const cursor = isTop
              ? (isLeft ? 'nw-resize' : 'ne-resize')
              : (isLeft ? 'sw-resize' : 'se-resize');
            return (
              <div
                key={corner}
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsResizing(true);
                  setResizeCorner(corner);
                  setResizeStart({
                    x: e.clientX, y: e.clientY,
                    w: popupSize.width, h: popupSize.height,
                    px: popupPos.x, py: popupPos.y,
                  });
                }}
                onTouchStart={(e) => {
                  e.preventDefault();
                  const t = e.touches[0];
                  setIsResizing(true);
                  setResizeCorner(corner);
                  setResizeStart({
                    x: t.clientX, y: t.clientY,
                    w: popupSize.width, h: popupSize.height,
                    px: popupPos.x, py: popupPos.y,
                  });
                }}
                style={{
                  position: 'absolute',
                  [isTop ? 'top' : 'bottom']: 0,
                  [isLeft ? 'left' : 'right']: 0,
                  width: 18, height: 18,
                  cursor,
                  zIndex: 10003,
                }}
                title="Drag to resize"
              />
            );
          })}
        </div>
      )}

      <style>{`
        @keyframes recPulse {
          0% { transform: scale(1); opacity: 1; }
          100% { transform: scale(1.6); opacity: 0; }
        }
      `}</style>
    </>
  );
};

export default AsimOrbFinal;
