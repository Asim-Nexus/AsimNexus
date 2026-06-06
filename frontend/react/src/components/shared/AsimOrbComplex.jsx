/**
 * AsimOrbComplex.jsx
 * ==================
 * Enhanced Asim Orb with Complex Visualization Integration
 * 
 * Features:
 * - Live Fractal/Wave/Spectrum backgrounds
 * - Voice-activated analysis mode
 * - Context-aware visualizations
 * - Integration with backend Complex Engine
 * 
 * i² = -1 powering the visual experience
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Mic, Activity, Radio, Eye, X, Maximize2, Minimize2 } from 'lucide-react';
import ComplexVisualizationOrb from './ComplexVisualizationOrb';
import UnifiedChat from './UnifiedChat';
import AsimNexusLogo from './AsimNexusLogo';
import voiceAnalysisService from '../../services/VoiceAnalysisService';

const VISUALIZATION_MODES = [
  { id: 'fractal', icon: Eye, label: 'Fractal', description: 'Mandelbrot z² + c' },
  { id: 'wave', icon: Radio, label: 'Wave', description: 'Mesh propagation ψ' },
  { id: 'spectrum', icon: Activity, label: 'Spectrum', description: 'FFT Analysis' }
];

const AsimOrbComplex = ({ user, onCommand, systemMetrics = {} }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [visMode, setVisMode] = useState('fractal');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceData, setVoiceData] = useState(null);
  const [pulsePhase, setPulsePhase] = useState(0);
  const [lastVoiceCommand, setLastVoiceCommand] = useState(null);
  
  // Drag state for orb
  const [position, setPosition] = useState({ x: window.innerWidth - 88, y: window.innerHeight - 88 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const orbRef = useRef(null);
  
  // Drag state for popup - adjusted for smaller default size
  const [popupPosition, setPopupPosition] = useState({ 
    x: Math.max(20, window.innerWidth - 380), 
    y: Math.max(20, window.innerHeight - 520) 
  });
  const [isPopupDragging, setIsPopupDragging] = useState(false);
  const [popupDragOffset, setPopupDragOffset] = useState({ x: 0, y: 0 });
  const popupRef = useRef(null);
  
  // Resize state - smaller default, smoother resizing
  const [popupSize, setPopupSize] = useState({ width: 340, height: 480 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 });
  
  // Min/Max sizes - smaller min for compact view
  const MIN_WIDTH = 280;
  const MIN_HEIGHT = 350;
  const MAX_WIDTH = 800;
  const MAX_HEIGHT = 700;

  // Pulse animation
  useEffect(() => {
    const interval = setInterval(() => {
      setPulsePhase(p => (p + 2) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Initialize voice analysis
  useEffect(() => {
    if (isOpen) {
      voiceAnalysisService.init();
    }
  }, [isOpen]);

  // Handle voice analysis data
  const handleVoiceAnalysis = useCallback((analysis) => {
    setVoiceData(analysis);
    
    if (analysis.command && analysis.command !== lastVoiceCommand) {
      setLastVoiceCommand(analysis.command);
      
      // Auto-switch visualization based on voice
      if (analysis.command === 'low_tone') {
        setVisMode('fractal');
      } else if (analysis.command === 'mid_tone') {
        setVisMode('wave');
      } else if (analysis.command === 'high_tone') {
        setVisMode('spectrum');
      }
    }
  }, [lastVoiceCommand]);

  // Toggle voice recording
  const toggleVoiceRecording = async () => {
    if (!isRecording) {
      const initialized = await voiceAnalysisService.init();
      if (initialized) {
        setIsRecording(true);
        setVisMode('spectrum'); // Auto-switch to spectrum mode
        voiceAnalysisService.startAnalysis(handleVoiceAnalysis);
      }
    } else {
      setIsRecording(false);
      voiceAnalysisService.stopAnalysis();
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Alt+V toggle voice
      if (e.altKey && e.key === 'v') {
        e.preventDefault();
        toggleVoiceRecording();
      }
      // Alt+1/2/3 switch modes
      if (e.altKey && e.key === '1') setVisMode('fractal');
      if (e.altKey && e.key === '2') setVisMode('wave');
      if (e.altKey && e.key === '3') setVisMode('spectrum');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isRecording, handleVoiceAnalysis]);

  const glowIntensity = 0.5 + Math.sin(pulsePhase * Math.PI / 180) * 0.3;

  // Drag handlers
  const handleMouseDown = (e) => {
    if (isOpen) return; // Don't drag when popup is open
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
  };

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    
    const newX = e.clientX - dragOffset.x;
    const newY = e.clientY - dragOffset.y;
    
    // Keep within screen bounds
    const maxX = window.innerWidth - 64;
    const maxY = window.innerHeight - 64;
    
    setPosition({
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY))
    });
  }, [isDragging, dragOffset]);

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Touch handlers for mobile
  const handleTouchStart = (e) => {
    if (isOpen) return;
    const touch = e.touches[0];
    setIsDragging(true);
    setDragOffset({
      x: touch.clientX - position.x,
      y: touch.clientY - position.y
    });
  };

  const handleTouchMove = useCallback((e) => {
    if (!isDragging) return;
    const touch = e.touches[0];
    
    const newX = touch.clientX - dragOffset.x;
    const newY = touch.clientY - dragOffset.y;
    
    const maxX = window.innerWidth - 64;
    const maxY = window.innerHeight - 64;
    
    setPosition({
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY))
    });
  }, [isDragging, dragOffset]);

  const handleTouchEnd = () => {
    setIsDragging(false);
  };

  // Add/remove global mouse/touch listeners
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('touchmove', handleTouchMove);
      window.addEventListener('touchend', handleTouchEnd);
      
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
        window.removeEventListener('touchmove', handleTouchMove);
        window.removeEventListener('touchend', handleTouchEnd);
      };
    }
  }, [isDragging, handleMouseMove, handleTouchMove]);

  // Popup drag handlers
  const handlePopupMouseDown = (e) => {
    // Only drag from header area
    if (e.target.closest('.popup-drag-handle')) {
      setIsPopupDragging(true);
      setPopupDragOffset({
        x: e.clientX - popupPosition.x,
        y: e.clientY - popupPosition.y
      });
    }
  };

  const handlePopupMouseMove = useCallback((e) => {
    if (!isPopupDragging) return;
    
    const newX = e.clientX - popupDragOffset.x;
    const newY = e.clientY - popupDragOffset.y;
    
    // Keep within screen bounds (with some margin)
    const maxX = window.innerWidth - popupSize.width;
    const maxY = window.innerHeight - popupSize.height;
    
    setPopupPosition({
      x: Math.max(-100, Math.min(newX, maxX + 100)),
      y: Math.max(-50, Math.min(newY, maxY + 50))
    });
  }, [isPopupDragging, popupDragOffset, isExpanded]);

  const handlePopupMouseUp = () => {
    setIsPopupDragging(false);
  };

  // Popup touch handlers
  const handlePopupTouchStart = (e) => {
    if (e.target.closest('.popup-drag-handle')) {
      const touch = e.touches[0];
      setIsPopupDragging(true);
      setPopupDragOffset({
        x: touch.clientX - popupPosition.x,
        y: touch.clientY - popupPosition.y
      });
    }
  };

  const handlePopupTouchMove = useCallback((e) => {
    if (!isPopupDragging) return;
    const touch = e.touches[0];
    
    const newX = touch.clientX - popupDragOffset.x;
    const newY = touch.clientY - popupDragOffset.y;
    
    const maxX = window.innerWidth - (isExpanded ? 600 : 420);
    const maxY = window.innerHeight - (isExpanded ? 700 : 580);
    
    setPopupPosition({
      x: Math.max(-100, Math.min(newX, maxX + 100)),
      y: Math.max(-50, Math.min(newY, maxY + 50))
    });
  }, [isPopupDragging, popupDragOffset, isExpanded]);

  const handlePopupTouchEnd = () => {
    setIsPopupDragging(false);
  };

  // Add popup drag listeners
  useEffect(() => {
    if (isPopupDragging) {
      window.addEventListener('mousemove', handlePopupMouseMove);
      window.addEventListener('mouseup', handlePopupMouseUp);
      window.addEventListener('touchmove', handlePopupTouchMove);
      window.addEventListener('touchend', handlePopupTouchEnd);
      
      return () => {
        window.removeEventListener('mousemove', handlePopupMouseMove);
        window.removeEventListener('mouseup', handlePopupMouseUp);
        window.removeEventListener('touchmove', handlePopupTouchMove);
        window.removeEventListener('touchend', handlePopupTouchEnd);
      };
    }
  }, [isPopupDragging, handlePopupMouseMove, handlePopupTouchMove]);

  // Resize handlers
  const handleResizeStart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      width: popupSize.width,
      height: popupSize.height
    });
  };

  const handleResizeMove = useCallback((e) => {
    if (!isResizing) return;
    
    const deltaX = e.clientX - resizeStart.x;
    const deltaY = e.clientY - resizeStart.y;
    
    // Smooth resize with requestAnimationFrame
    requestAnimationFrame(() => {
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, resizeStart.width + deltaX));
      const newHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, resizeStart.height + deltaY));
      
      setPopupSize({ width: newWidth, height: newHeight });
      
      // Auto-update expanded state based on size
      setIsExpanded(newWidth > 480);
    });
  }, [isResizing, resizeStart]);

  const handleResizeEnd = () => {
    setIsResizing(false);
  };

  // Touch resize handlers
  const handleResizeTouchStart = (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    setIsResizing(true);
    setResizeStart({
      x: touch.clientX,
      y: touch.clientY,
      width: popupSize.width,
      height: popupSize.height
    });
  };

  const handleResizeTouchMove = useCallback((e) => {
    if (!isResizing) return;
    const touch = e.touches[0];
    
    const deltaX = touch.clientX - resizeStart.x;
    const deltaY = touch.clientY - resizeStart.y;
    
    requestAnimationFrame(() => {
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, resizeStart.width + deltaX));
      const newHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, resizeStart.height + deltaY));
      
      setPopupSize({ width: newWidth, height: newHeight });
      setIsExpanded(newWidth > 480);
    });
  }, [isResizing, resizeStart]);

  const handleResizeTouchEnd = () => {
    setIsResizing(false);
  };

  // Add resize listeners
  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleResizeMove);
      window.addEventListener('mouseup', handleResizeEnd);
      window.addEventListener('touchmove', handleResizeTouchMove);
      window.addEventListener('touchend', handleResizeTouchEnd);
      
      return () => {
        window.removeEventListener('mousemove', handleResizeMove);
        window.removeEventListener('mouseup', handleResizeEnd);
        window.removeEventListener('touchmove', handleResizeTouchMove);
        window.removeEventListener('touchend', handleResizeTouchEnd);
      };
    }
  }, [isResizing, handleResizeMove, handleResizeTouchMove]);

  return (
    <>
      {/* Floating Orb Button - Asim Nexus Logo */}
      {!isOpen && (
        <div
          ref={orbRef}
          title="Asim Nexus - Drag to move, Click to open"
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
          onClick={(e) => {
            // Only open if not dragging
            if (!isDragging) setIsOpen(true);
          }}
          style={{
            position: 'fixed',
            left: position.x,
            top: position.y,
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: `linear-gradient(135deg, 
              rgba(102,126,234,${glowIntensity + 0.2}), 
              rgba(118,75,162,${glowIntensity + 0.2})
            )`,
            boxShadow: `
              0 0 ${30 + glowIntensity * 20}px rgba(102,126,234,${glowIntensity}),
              0 0 ${60 + glowIntensity * 40}px rgba(102,126,234,${glowIntensity * 0.5})
            `,
            cursor: isDragging ? 'grabbing' : 'grab',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            transition: isDragging ? 'none' : 'transform 0.3s ease, box-shadow 0.3s ease',
            transform: `scale(${1 + glowIntensity * 0.1})`,
            backdropFilter: 'blur(10px)',
            border: '2px solid rgba(255,255,255,0.2)',
            userSelect: 'none',
            WebkitUserSelect: 'none',
          }}
        >
          {/* Asim Nexus Logo - Circular Image */}
          <div style={{
            width: 52,
            height: 52,
            borderRadius: '50%',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: `linear-gradient(135deg, 
              rgba(102,126,234,${glowIntensity}), 
              rgba(118,75,162,${glowIntensity})
            )`,
            boxShadow: `0 0 ${15 + glowIntensity * 15}px rgba(102,126,234,${glowIntensity})`,
          }}>
            <img 
              src="/asim-logo.png" 
              alt="Asim Nexus"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: '50%',
              }}
              onError={(e) => {
                // Fallback to UI folder path
                e.target.src = '/ui/AsiM logo.png';
              }}
            />
          </div>
          
          {/* Status indicators */}
          <div style={{
            position: 'absolute',
            bottom: -2,
            right: -2,
            display: 'flex',
            gap: 2,
          }}>
            {systemMetrics.mesh_health > 0.8 && (
              <div style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: '#22c55e',
                boxShadow: '0 0 4px #22c55e',
              }} />
            )}
            {isRecording && (
              <div style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: '#ef4444',
                animation: 'pulse 1s infinite',
              }} />
            )}
          </div>
        </div>
      )}

      {/* Main Chat Popup */}
      {isOpen && (
        <div
          ref={popupRef}
          onMouseDown={handlePopupMouseDown}
          onTouchStart={handlePopupTouchStart}
          style={{
            position: 'fixed',
            left: popupPosition.x,
            top: popupPosition.y,
            width: popupSize.width,
            height: popupSize.height,
            background: 'rgba(10, 10, 26, 0.98)',
            backdropFilter: 'blur(20px)',
            borderRadius: 16,
            border: '1px solid rgba(102, 126, 234, 0.3)',
            boxShadow: '0 20px 40px rgba(0,0,0,0.4), 0 0 80px rgba(102, 126, 234, 0.15)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            transition: isResizing ? 'none' : 'width 0.2s ease, height 0.2s ease',
            cursor: isPopupDragging ? 'grabbing' : isResizing ? 'nwse-resize' : 'default',
            userSelect: 'none',
          }}
        >
          {/* Drag Handle - Grab area for moving popup */}
          <div 
            className="popup-drag-handle"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 80,
              height: 30,
              cursor: 'grab',
              zIndex: 10000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: isPopupDragging ? 'rgba(102, 126, 234, 0.2)' : 'transparent',
              borderRadius: '20px 0 0 0',
            }}
            title="Drag to move window"
          >
            <div style={{
              width: 40,
              height: 4,
              background: 'rgba(255,255,255,0.3)',
              borderRadius: 2,
            }} />
          </div>

          {/* Complex Visualization Header */}
          <ComplexVisualizationOrb
            mode={visMode}
            systemMetrics={systemMetrics}
            voiceData={voiceData}
            isRecording={isRecording}
            style={{ borderRadius: '20px 20px 0 0' }}
          />

          {/* Control Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            background: 'rgba(102, 126, 234, 0.1)',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
          }}>
            {/* Mode Switcher */}
            <div style={{ display: 'flex', gap: 4 }}>
              {VISUALIZATION_MODES.map((mode) => {
                const Icon = mode.icon;
                const isActive = visMode === mode.id;
                return (
                  <button
                    key={mode.id}
                    onClick={() => setVisMode(mode.id)}
                    title={`${mode.label}: ${mode.description} (Alt+${mode.id === 'fractal' ? '1' : mode.id === 'wave' ? '2' : '3'})`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '4px 10px',
                      borderRadius: 6,
                      border: 'none',
                      background: isActive ? 'rgba(102, 126, 234, 0.3)' : 'transparent',
                      color: isActive ? '#fff' : 'rgba(255,255,255,0.5)',
                      fontSize: 11,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Icon size={14} />
                    {mode.label}
                  </button>
                );
              })}
            </div>

            {/* Voice Toggle & Window Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                onClick={toggleVoiceRecording}
                title="Voice Analysis (Alt+V)"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '4px 10px',
                  borderRadius: 6,
                  border: 'none',
                  background: isRecording ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255,255,255,0.1)',
                  color: isRecording ? '#ef4444' : 'rgba(255,255,255,0.7)',
                  fontSize: 11,
                  cursor: 'pointer',
                  animation: isRecording ? 'pulse 1s infinite' : 'none',
                }}
              >
                <Mic size={14} />
                {isRecording ? 'REC' : 'Voice'}
              </button>

              <button
                onClick={() => setIsExpanded(!isExpanded)}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: 6,
                  padding: 6,
                  cursor: 'pointer',
                  color: 'white',
                }}
              >
                {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>

              <button
                onClick={() => {
                  setIsOpen(false);
                  setIsRecording(false);
                  voiceAnalysisService.stopAnalysis();
                }}
                style={{
                  background: 'rgba(239,68,68,0.2)',
                  border: 'none',
                  borderRadius: 6,
                  padding: 6,
                  cursor: 'pointer',
                  color: '#ef4444',
                }}
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Math Context Indicator */}
          {lastVoiceCommand && (
            <div style={{
              padding: '4px 12px',
              background: 'rgba(102, 126, 234, 0.15)',
              fontSize: 10,
              color: 'rgba(255,255,255,0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <span>i² = -1</span>
              <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
              <span>z = x + iy</span>
              <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
              <span>FFT: O(n log n)</span>
              {voiceData?.pitch > 0 && (
                <>
                  <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
                  <span>Pitch: {Math.round(voiceData.pitch)} Hz</span>
                </>
              )}
            </div>
          )}

          {/* Chat Component */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <UnifiedChat
              user={user}
              onCommand={onCommand}
              compact={popupSize.width < 500}
              onClose={() => {
                setIsOpen(false);
                setIsRecording(false);
                voiceAnalysisService.stopAnalysis();
              }}
            />
          </div>

          {/* Resize Handle - Bottom Right Corner */}
          <div
            onMouseDown={handleResizeStart}
            onTouchStart={handleResizeTouchStart}
            style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: 20,
              height: 20,
              cursor: 'nwse-resize',
              zIndex: 10001,
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'flex-end',
              padding: '0 4px 4px 0',
            }}
            title="Drag to resize"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" style={{ opacity: 0.5 }}>
              <path
                d="M8 12L12 12L12 8 M4 12L12 4 M0 12L12 0"
                stroke="rgba(255,255,255,0.6)"
                strokeWidth="2"
                fill="none"
              />
            </svg>
          </div>
        </div>
      )}

      <style>{`
        @keyframes orbExpand {
          from { opacity: 0; transform: scale(0.8) translateY(20px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </>
  );
};

export default AsimOrbComplex;
