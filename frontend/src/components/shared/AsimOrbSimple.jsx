/**
 * AsimOrbEnhanced.jsx (Simplified with UnifiedChat)
 * ================================================
 * Floating Orb Interface using UnifiedChat component
 * 
 * Features:
 * - Orb toggle with animation
 * - Gesture shortcuts (Alt+A, Alt+S, Alt+V)
 * - UnifiedChat for actual chat interface
 * - Context awareness through UnifiedChat
 */
import React, { useState, useEffect, useRef } from 'react';
import { Zap, Maximize2, Minimize2 } from 'lucide-react';
import UnifiedChat from './UnifiedChat';
import gestureService from '../../services/GestureService';
import { nativeBridge, PLATFORM } from '../../native/NativeBridge';

export default function AsimOrbEnhanced({ user, onCommand }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [platform, setPlatform] = useState('web');
  const [pulsePhase, setPulsePhase] = useState(0);

  // Initialize platform & gestures
  useEffect(() => {
    try {
      nativeBridge.init();
      setPlatform(PLATFORM);
    } catch (e) {
      console.warn('[AsimOrb] Native init failed:', e);
    }

    try {
      gestureService.init();
      const gestureUnsub = gestureService.on('shortcut', (data) => {
        if (data.action === 'toggle_orb') setIsOpen(prev => !prev);
        if (data.action === 'escape' && isOpen) setIsOpen(false);
      });
      
      return () => {
        gestureUnsub?.();
        gestureService.destroy?.();
      };
    } catch (e) {
      console.warn('[AsimOrb] Gesture init failed:', e);
    }
  }, [isOpen]);

  // Pulse animation
  useEffect(() => {
    const pulseInterval = setInterval(() => setPulsePhase(p => (p + 1) % 360), 50);
    return () => clearInterval(pulseInterval);
  }, []);

  const glowIntensity = 0.5 + Math.sin(pulsePhase * Math.PI / 180) * 0.3;

  return (
    <>
      {/* Floating Orb Button */}
      {!isOpen && (
        <div onClick={() => setIsOpen(true)} style={{
          position: 'fixed', bottom: 24, right: 24, 
          width: 64, height: 64, borderRadius: '50%',
          background: `linear-gradient(135deg, rgba(102,126,234,${glowIntensity}), rgba(118,75,162,${glowIntensity}))`,
          boxShadow: `0 0 ${30 + glowIntensity * 20}px rgba(102,126,234,${glowIntensity}), 0 0 ${60 + glowIntensity * 40}px rgba(102,126,234,${glowIntensity * 0.5})`,
          cursor: 'pointer', 
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999, 
          transition: 'transform 0.3s ease', 
          transform: `scale(${1 + glowIntensity * 0.1})`,
          backdropFilter: 'blur(10px)', 
          border: '2px solid rgba(255,255,255,0.2)',
        }}>
          <Zap size={28} color="white" fill="white" />
          <div style={{ 
            position: 'absolute', bottom: -4, right: -4, 
            fontSize: 10, background: 'rgba(0,0,0,0.5)', 
            borderRadius: 4, padding: '1px 4px', 
            color: 'rgba(255,255,255,0.7)' 
          }}>
            {platform === 'web' ? '🌐' : '📱'}
          </div>
        </div>
      )}

      {/* Chat Popup using UnifiedChat */}
      {isOpen && (
        <div style={{
          position: 'fixed', 
          bottom: 20, right: 20, 
          width: isExpanded ? 500 : 380, 
          height: isExpanded ? 620 : 520,
          background: 'rgba(10, 10, 26, 0.95)', 
          backdropFilter: 'blur(20px)', 
          borderRadius: 20,
          border: '1px solid rgba(102, 126, 234, 0.3)',
          boxShadow: '0 25px 50px rgba(0,0,0,0.5), 0 0 100px rgba(102, 126, 234, 0.1)',
          zIndex: 9999, 
          display: 'flex', flexDirection: 'column', 
          overflow: 'hidden',
          animation: 'orbExpand 0.3s ease',
        }}>
          {/* Header with expand/collapse */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'flex-end', 
            padding: '10px 14px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            background: 'linear-gradient(90deg, rgba(102,126,234,0.1), transparent)',
            gap: 8,
          }}>
            <button onClick={() => setIsExpanded(!isExpanded)} style={{
              background: 'rgba(255,255,255,0.1)', border: 'none', 
              borderRadius: 8, padding: 8, cursor: 'pointer', 
              color: 'white',
            }}>
              {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <button onClick={() => setIsOpen(false)} style={{
              background: 'rgba(239,68,68,0.2)', border: 'none', 
              borderRadius: 8, padding: 8, cursor: 'pointer', 
              color: '#ef4444',
            }}>
              ✕
            </button>
          </div>

          {/* UnifiedChat Component */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <UnifiedChat 
              user={user} 
              onCommand={onCommand} 
              compact={true}
              onClose={() => setIsOpen(false)}
            />
          </div>
        </div>
      )}

      <style>{`
        @keyframes orbExpand {
          from { opacity: 0; transform: scale(0.8) translateY(20px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
    </>
  );
}
