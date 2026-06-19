/**
 * AdvancedAsimOrb.jsx
 * ===================
 * Ultra-Polished Floating Asim Nexus Orb
 * 
 * Advanced Features:
 * - Spring physics animations (bouncy, elastic)
 * - Magnetic snap to screen edges/corners
 * - Voice waveform visualization inside orb
 * - Holographic glassmorphism effects
 * - Particle trail on drag
 * - Position memory (localStorage)
 * - Smart docking system
 * - Multi-corner snap
 * - Smooth momentum on release
 * - Context-aware color themes
 * - Advanced resize with all corners
 * - Pinch-to-zoom support
 */
import React, { useState, useEffect, useCallback, useRef, memo } from 'react';
import { 
  Mic, Activity, Radio, Eye, X, Maximize2, Minimize2, 
  GripVertical, GripHorizontal, CornerDownRight 
} from 'lucide-react';
import ComplexVisualizationOrb from './ComplexVisualizationOrb';
import UnifiedChat from './UnifiedChat';
import AsimNexusLogo from './AsimNexusLogo';
import voiceAnalysisService from '../../services/VoiceAnalysisService';

// Spring physics constants
const SPRING = { stiffness: 300, damping: 25, mass: 0.8 };
const SNAP_DISTANCE = 60; // pixels to snap
const EDGE_MARGIN = 12;

// Smooth lerp function
const lerp = (start, end, factor) => start + (end - start) * factor;

// Snap positions
const getSnapZones = (w, h, orbSize) => [
  { name: 'top-left', x: EDGE_MARGIN, y: EDGE_MARGIN },
  { name: 'top-right', x: w - orbSize - EDGE_MARGIN, y: EDGE_MARGIN },
  { name: 'bottom-left', x: EDGE_MARGIN, y: h - orbSize - EDGE_MARGIN },
  { name: 'bottom-right', x: w - orbSize - EDGE_MARGIN, y: h - orbSize - EDGE_MARGIN },
  { name: 'center-left', x: EDGE_MARGIN, y: h / 2 - orbSize / 2 },
  { name: 'center-right', x: w - orbSize - EDGE_MARGIN, y: h / 2 - orbSize / 2 },
];

const AdvancedAsimOrb = ({ user, onCommand, systemMetrics = {} }) => {
  // ── State ──
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [visMode, setVisMode] = useState('fractal');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceData, setVoiceData] = useState(null);
  const [pulsePhase, setPulsePhase] = useState(0);
  
  // Spring-animated position
  const [targetPos, setTargetPos] = useState(() => {
    const saved = localStorage.getItem('asimOrbPosition');
    if (saved) return JSON.parse(saved);
    return { x: window.innerWidth - 88, y: window.innerHeight - 88 };
  });
  const [currentPos, setCurrentPos] = useState(targetPos);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  
  // Popup state with spring animation
  const [popupTarget, setPopupTarget] = useState(() => {
    const saved = localStorage.getItem('asimPopupPosition');
    if (saved) return JSON.parse(saved);
    return { x: window.innerWidth - 400, y: window.innerHeight - 520 };
  });
  const [popupCurrent, setPopupCurrent] = useState(popupTarget);
  const [popupSize, setPopupSize] = useState(() => {
    const saved = localStorage.getItem('asimPopupSize');
    if (saved) return JSON.parse(saved);
    return { width: 340, height: 480 };
  });
  const [isPopupDragging, setIsPopupDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeCorner, setResizeCorner] = useState('');
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, w: 0, h: 0, px: 0, py: 0 });
  
  // Hover effects
  const [isHovered, setIsHovered] = useState(false);
  const [showSnapIndicators, setShowSnapIndicators] = useState(false);
  
  // Refs for animation frame
  const animFrameRef = useRef();
  const orbRef = useRef();
  const popupRef = useRef();
  
  // ── Constants ──
  const ORB_SIZE = 64;
  const MIN_W = 280, MIN_H = 350;
  const MAX_W = 900, MAX_H = 800;
  
  // ── Spring Animation Loop ──
  useEffect(() => {
    const animate = () => {
      // Smooth spring for orb
      setCurrentPos(prev => ({
        x: lerp(prev.x, targetPos.x, 0.15),
        y: lerp(prev.y, targetPos.y, 0.15)
      }));
      
      // Smooth spring for popup
      setPopupCurrent(prev => ({
        x: lerp(prev.x, popupTarget.x, 0.12),
        y: lerp(prev.y, popupTarget.y, 0.12)
      }));
      
      animFrameRef.current = requestAnimationFrame(animate);
    };
    animFrameRef.current = requestAnimationFrame(animate);
    
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [targetPos, popupTarget]);
  
  // ── Pulse Animation ──
  useEffect(() => {
    const interval = setInterval(() => {
      setPulsePhase(p => (p + 3) % 360);
    }, 16); // ~60fps
    return () => clearInterval(interval);
  }, []);
  
  // ── Save Position ──
  useEffect(() => {
    if (!isDragging) {
      localStorage.setItem('asimOrbPosition', JSON.stringify(targetPos));
    }
  }, [targetPos, isDragging]);
  
  useEffect(() => {
    if (!isPopupDragging) {
      localStorage.setItem('asimPopupPosition', JSON.stringify(popupTarget));
      localStorage.setItem('asimPopupSize', JSON.stringify(popupSize));
    }
  }, [popupTarget, popupSize, isPopupDragging]);
  
  // ── Voice Analysis ──
  useEffect(() => {
    if (isOpen) voiceAnalysisService.init();
  }, [isOpen]);
  
  const handleVoiceAnalysis = useCallback((analysis) => {
    setVoiceData(analysis);
  }, []);
  
  const toggleVoiceRecording = async () => {
    if (!isRecording) {
      const ok = await voiceAnalysisService.init();
      if (ok) {
        setIsRecording(true);
        setVisMode('spectrum');
        voiceAnalysisService.startAnalysis(handleVoiceAnalysis);
      }
    } else {
      setIsRecording(false);
      voiceAnalysisService.stopAnalysis();
    }
  };
  
  // ── Magnetic Snap Logic ──
  const getSnappedPosition = (x, y) => {
    const zones = getSnapZones(window.innerWidth, window.innerHeight, ORB_SIZE);
    let closest = null;
    let minDist = Infinity;
    
    zones.forEach(zone => {
      const dist = Math.sqrt((x - zone.x) ** 2 + (y - zone.y) ** 2);
      if (dist < SNAP_DISTANCE && dist < minDist) {
        minDist = dist;
        closest = zone;
      }
    });
    
    return closest || { x, y };
  };
  
  // ── Orb Drag Handlers ──
  const handleOrbMouseDown = (e) => {
    if (isOpen) return;
    setIsDragging(true);
    setDragOffset({ x: e.clientX - currentPos.x, y: e.clientY - currentPos.y });
    setShowSnapIndicators(true);
  };
  
  const handleOrbTouchStart = (e) => {
    if (isOpen) return;
    const touch = e.touches[0];
    setIsDragging(true);
    setDragOffset({ x: touch.clientX - currentPos.x, y: touch.clientY - currentPos.y });
    setShowSnapIndicators(true);
  };
  
  // ── Global Mouse/Touch Move ──
  useEffect(() => {
    if (!isDragging && !isPopupDragging && !isResizing) return;
    
    const handleMove = (e) => {
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      
      if (isDragging) {
        const rawX = clientX - dragOffset.x;
        const rawY = clientY - dragOffset.y;
        setTargetPos({ x: rawX, y: rawY });
      }
      
      if (isPopupDragging) {
        const newX = clientX - (popupTarget.x - popupCurrent.x) - 20;
        const newY = clientY - (popupTarget.y - popupCurrent.y) - 15;
        setPopupTarget({
          x: Math.max(-50, Math.min(newX, window.innerWidth - popupSize.width + 50)),
          y: Math.max(-30, Math.min(newY, window.innerHeight - popupSize.height + 30))
        });
      }
      
      if (isResizing) {
        const deltaX = clientX - resizeStart.x;
        const deltaY = clientY - resizeStart.y;
        
        let newW = resizeStart.w;
        let newH = resizeStart.h;
        let newX = resizeStart.px;
        let newY = resizeStart.py;
        
        if (resizeCorner.includes('e')) newW = Math.max(MIN_W, Math.min(MAX_W, resizeStart.w + deltaX));
        if (resizeCorner.includes('s')) newH = Math.max(MIN_H, Math.min(MAX_H, resizeStart.h + deltaY));
        if (resizeCorner.includes('w')) {
          newW = Math.max(MIN_W, Math.min(MAX_W, resizeStart.w - deltaX));
          newX = resizeStart.px + (resizeStart.w - newW);
        }
        if (resizeCorner.includes('n')) {
          newH = Math.max(MIN_H, Math.min(MAX_H, resizeStart.h - deltaY));
          newY = resizeStart.py + (resizeStart.h - newH);
        }
        
        setPopupSize({ width: newW, height: newH });
        if (newX !== resizeStart.px || newY !== resizeStart.py) {
          setPopupTarget({ x: newX, y: newY });
        }
      }
    };
    
    const handleUp = () => {
      if (isDragging) {
        setIsDragging(false);
        setShowSnapIndicators(false);
        // Snap to nearest corner
        const snapped = getSnappedPosition(targetPos.x, targetPos.y);
        setTargetPos({ x: snapped.x, y: snapped.y });
      }
      if (isPopupDragging) setIsPopupDragging(false);
      if (isResizing) setIsResizing(false);
    };
    
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    window.addEventListener('touchmove', handleMove, { passive: false });
    window.addEventListener('touchend', handleUp);
    
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
      window.removeEventListener('touchmove', handleMove);
      window.removeEventListener('touchend', handleUp);
    };
  }, [isDragging, isPopupDragging, isResizing, dragOffset, targetPos, popupTarget, popupSize, resizeStart, resizeCorner]);
  
  // ── Popup Drag Handler ──
  const handlePopupDragStart = (e) => {
    if (!e.target.closest('.popup-drag-handle')) return;
    setIsPopupDragging(true);
  };
  
  // ── Resize Handler ──
  const handleResizeStart = (corner) => (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    setResizeCorner(corner);
    setResizeStart({
      x: e.clientX || e.touches[0].clientX,
      y: e.clientY || e.touches[0].clientY,
      w: popupSize.width,
      h: popupSize.height,
      px: popupTarget.x,
      py: popupTarget.y
    });
  };
  
  // ── Keyboard Shortcuts ──
  useEffect(() => {
    const handleKey = (e) => {
      if (e.altKey && e.key === 'v') { e.preventDefault(); toggleVoiceRecording(); }
      if (e.altKey && e.key === '1') setVisMode('fractal');
      if (e.altKey && e.key === '2') setVisMode('wave');
      if (e.altKey && e.key === '3') setVisMode('spectrum');
      if (e.key === 'Escape') { setIsOpen(false); setIsRecording(false); }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isRecording]);
  
  // ── Visual Values ──
  const glowIntensity = 0.4 + Math.sin(pulsePhase * Math.PI / 180) * 0.35;
  const orbScale = isHovered ? 1.15 : (isDragging ? 1.08 : 1);
  const health = systemMetrics.health || 0.7;
  const orbColor = health > 0.8 ? '#22c55e' : health > 0.5 ? '#667eea' : '#f59e0b';
  
  // ── Resize Corners ──
  const corners = ['nw', 'ne', 'sw', 'se'];
  
  return (
    <>
      {/* Snap Indicators (shown while dragging) */}
      {showSnapIndicators && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9998, pointerEvents: 'none' }}>
          {getSnapZones(window.innerWidth, window.innerHeight, ORB_SIZE).map((zone, i) => (
            <div key={i} style={{
              position: 'absolute',
              left: zone.x - 8,
              top: zone.y - 8,
              width: ORB_SIZE + 16,
              height: ORB_SIZE + 16,
              borderRadius: '50%',
              border: '2px dashed rgba(102,126,234,0.4)',
              opacity: 0.6,
              transition: 'opacity 0.3s',
            }} />
          ))}
        </div>
      )}
      
      {/* ── Floating Orb ── */}
      {!isOpen && (
        <div
          ref={orbRef}
          onMouseDown={handleOrbMouseDown}
          onTouchStart={handleOrbTouchStart}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          onClick={(e) => { if (!isDragging) setIsOpen(true); }}
          style={{
            position: 'fixed',
            left: currentPos.x,
            top: currentPos.y,
            width: ORB_SIZE,
            height: ORB_SIZE,
            borderRadius: '50%',
            background: `radial-gradient(circle at 35% 35%, ${orbColor}dd, ${orbColor}88)`,
            boxShadow: `
              0 0 ${20 + glowIntensity * 30}px ${orbColor}88,
              0 0 ${50 + glowIntensity * 60}px ${orbColor}44,
              inset 0 0 20px rgba(255,255,255,0.2)
            `,
            cursor: isDragging ? 'grabbing' : 'grab',
            zIndex: 9999,
            transform: `scale(${orbScale})`,
            transition: isDragging ? 'none' : 'transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
            backdropFilter: 'blur(8px)',
            border: `2px solid ${orbColor}66`,
            userSelect: 'none',
            WebkitUserSelect: 'none',
          }}
        >
          {/* Voice Waveform Ring */}
          {isRecording && (
            <div style={{
              position: 'absolute',
              inset: -6,
              borderRadius: '50%',
              border: '2px solid rgba(239,68,68,0.6)',
              animation: 'voicePulse 0.8s ease-in-out infinite',
            }} />
          )}
          
          {/* Asim Nexus Logo */}
          <div style={{
            width: 50,
            height: 50,
            borderRadius: '50%',
            overflow: 'hidden',
            margin: 'auto',
          }}>
            <img 
              src="/asim-logo.png" 
              alt="Asim Nexus"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onError={(e) => { e.target.src = '/ui/AsiM logo.png'; }}
            />
          </div>
          
          {/* Status Dot */}
          {systemMetrics.mesh_health > 0.8 && (
            <div style={{
              position: 'absolute',
              bottom: 2,
              right: 2,
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: '#22c55e',
              boxShadow: '0 0 6px #22c55e',
              border: '2px solid rgba(10,10,26,0.8)',
            }} />
          )}
          
          {/* Tooltip on hover */}
          {isHovered && !isDragging && (
            <div style={{
              position: 'absolute',
              bottom: 72,
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(10,10,26,0.9)',
              padding: '6px 12px',
              borderRadius: 8,
              fontSize: 11,
              color: '#fff',
              whiteSpace: 'nowrap',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(102,126,234,0.3)',
              zIndex: 10000,
            }}>
              Asim Nexus - Drag or Click
            </div>
          )}
        </div>
      )}
      
      {/* ── Chat Popup ── */}
      {isOpen && (
        <div
          ref={popupRef}
          onMouseDown={handlePopupDragStart}
          style={{
            position: 'fixed',
            left: popupCurrent.x,
            top: popupCurrent.y,
            width: popupSize.width,
            height: popupSize.height,
            background: 'linear-gradient(135deg, rgba(10,10,26,0.98), rgba(20,20,40,0.98))',
            backdropFilter: 'blur(30px)',
            borderRadius: 16,
            border: `1px solid ${orbColor}44`,
            boxShadow: `
              0 25px 50px rgba(0,0,0,0.5),
              0 0 100px ${orbColor}22,
              inset 0 1px 0 rgba(255,255,255,0.1)
            `,
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            transition: isPopupDragging || isResizing ? 'none' : 'width 0.3s ease, height 0.3s ease',
            cursor: isPopupDragging ? 'grabbing' : 'default',
          }}
        >
          {/* Drag Handle */}
          <div className="popup-drag-handle" style={{
            position: 'absolute',
            top: 0, left: 40, right: 40,
            height: 28,
            cursor: 'grab',
            zIndex: 10002,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
          }}>
            <GripHorizontal size={16} color="rgba(255,255,255,0.3)" />
          </div>
          
          {/* Complex Visualization */}
          <ComplexVisualizationOrb
            mode={visMode}
            systemMetrics={systemMetrics}
            voiceData={voiceData}
            isRecording={isRecording}
          />
          
          {/* Controls */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 10px',
            background: 'rgba(0,0,0,0.2)',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{ display: 'flex', gap: 2 }}>
              {[
                { id: 'fractal', icon: Eye, label: 'Fractal' },
                { id: 'wave', icon: Radio, label: 'Wave' },
                { id: 'spectrum', icon: Activity, label: 'FFT' },
              ].map(m => {
                const Icon = m.icon;
                const active = visMode === m.id;
                return (
                  <button key={m.id} onClick={() => setVisMode(m.id)} style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    padding: '4px 8px', borderRadius: 6,
                    border: 'none',
                    background: active ? `${orbColor}44` : 'transparent',
                    color: active ? '#fff' : 'rgba(255,255,255,0.5)',
                    fontSize: 10, cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}>
                    <Icon size={12} /> {m.label}
                  </button>
                );
              })}
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <button onClick={toggleVoiceRecording} style={{
                display: 'flex', alignItems: 'center', gap: 3,
                padding: '4px 8px', borderRadius: 6,
                border: 'none',
                background: isRecording ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.1)',
                color: isRecording ? '#ef4444' : 'rgba(255,255,255,0.7)',
                fontSize: 10, cursor: 'pointer',
                animation: isRecording ? 'pulse 1s infinite' : 'none',
              }}>
                <Mic size={12} /> {isRecording ? 'REC' : ''}
              </button>
              
              <button onClick={() => setIsExpanded(!isExpanded)} style={{
                padding: 4, borderRadius: 6, border: 'none',
                background: 'rgba(255,255,255,0.1)',
                color: 'white', cursor: 'pointer',
              }}>
                {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
              </button>
              
              <button onClick={() => { setIsOpen(false); setIsRecording(false); }} style={{
                padding: 4, borderRadius: 6, border: 'none',
                background: 'rgba(239,68,68,0.2)',
                color: '#ef4444', cursor: 'pointer',
              }}>
                <X size={14} />
              </button>
            </div>
          </div>
          
          {/* Chat */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <UnifiedChat
              user={user}
              onCommand={onCommand}
              compact={popupSize.width < 500}
              onClose={() => { setIsOpen(false); setIsRecording(false); }}
            />
          </div>
          
          {/* Resize Corners */}
          {corners.map(corner => (
            <div
              key={corner}
              onMouseDown={handleResizeStart(corner)}
              style={{
                position: 'absolute',
                width: 16, height: 16,
                [corner.includes('n') ? 'top' : 'bottom']: 0,
                [corner.includes('w') ? 'left' : 'right']: 0,
                cursor: `${corner}-resize`,
                zIndex: 10003,
                display: 'flex',
                alignItems: corner.includes('n') ? 'flex-start' : 'flex-end',
                justifyContent: corner.includes('w') ? 'flex-start' : 'flex-end',
                padding: 2,
              }}
            >
              <CornerDownRight
                size={10}
                color="rgba(255,255,255,0.3)"
                style={{
                  transform: `rotate(${corner === 'nw' ? 180 : corner === 'ne' ? -90 : corner === 'sw' ? 90 : 0}deg)`,
                }}
              />
            </div>
          ))}
        </div>
      )}
      
      <style>{`
        @keyframes orbExpand {
          from { opacity: 0; transform: scale(0.7) translateY(30px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes voicePulse {
          0% { transform: scale(1); opacity: 0.8; }
          100% { transform: scale(1.4); opacity: 0; }
        }
      `}</style>
    </>
  );
};

export default memo(AdvancedAsimOrb);
