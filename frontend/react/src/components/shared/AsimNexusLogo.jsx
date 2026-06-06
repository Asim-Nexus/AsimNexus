/**
 * AsimNexusLogo.jsx
 * =================
 * Asim Nexus Logo Component - Circular SVG
 * 
 * Features:
 * - Animated pulse ring (i² = -1 inspired)
 * - Gradient orb design
 * - Nexus/network nodes
 * - Scalable SVG
 */
import React from 'react';

const AsimNexusLogo = ({ 
  size = 64, 
  pulsePhase = 0,
  showGlow = true,
  className = '' 
}) => {
  const center = size / 2;
  const radius = size * 0.4;
  
  // Glow intensity based on pulse
  const glowOpacity = 0.5 + Math.sin(pulsePhase * Math.PI / 180) * 0.3;
  
  return (
    <div 
      className={`asim-nexus-logo ${className}`}
      style={{
        width: size,
        height: size,
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{
          filter: showGlow ? `drop-shadow(0 0 ${8 + glowOpacity * 8}px rgba(102, 126, 234, ${glowOpacity}))` : 'none',
        }}
      >
        <defs>
          {/* Gradient for main orb */}
          <linearGradient id="orbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#667eea" />
            <stop offset="50%" stopColor="#764ba2" />
            <stop offset="100%" stopColor="#667eea" />
          </linearGradient>
          
          {/* Inner glow gradient */}
          <radialGradient id="innerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.3)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0)" />
          </radialGradient>
          
          {/* Pulse ring gradient */}
          <linearGradient id="pulseGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(102, 126, 234, 0)" />
            <stop offset="50%" stopColor="rgba(102, 126, 234, 0.8)" />
            <stop offset="100%" stopColor="rgba(102, 126, 234, 0)" />
          </linearGradient>
        </defs>
        
        {/* Outer pulse ring (i² = -1 rotation) */}
        <circle
          cx={center}
          cy={center}
          r={radius + 2}
          fill="none"
          stroke="url(#pulseGradient)"
          strokeWidth={2}
          strokeDasharray={`${radius * 0.5} ${radius * 2}`}
          transform={`rotate(${pulsePhase}, ${center}, ${center})`}
          style={{
            opacity: glowOpacity,
          }}
        />
        
        {/* Main orb circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="url(#orbGradient)"
        />
        
        {/* Inner glow */}
        <circle
          cx={center}
          cy={center}
          r={radius * 0.7}
          fill="url(#innerGlow)"
        />
        
        {/* Nexus network nodes - representing mesh connectivity */}
        {[0, 72, 144, 216, 288].map((angle, i) => {
          const rad = (angle * Math.PI) / 180;
          const x = center + (radius * 0.5) * Math.cos(rad);
          const y = center + (radius * 0.5) * Math.sin(rad);
          return (
            <g key={i}>
              {/* Node */}
              <circle
                cx={x}
                cy={y}
                r={radius * 0.12}
                fill="white"
                opacity={0.9}
              />
              {/* Connection to center */}
              <line
                x1={x}
                y1={y}
                x2={center}
                y2={center}
                stroke="rgba(255,255,255,0.4)"
                strokeWidth={1}
              />
            </g>
          );
        })}
        
        {/* Center core - glowing white orb */}
        <circle
          cx={center}
          cy={center}
          r={radius * 0.25}
          fill="white"
          opacity={0.9}
        />
        <circle
          cx={center}
          cy={center}
          r={radius * 0.15}
          fill="url(#innerGlow)"
          opacity={0.8}
        />
      </svg>
    </div>
  );
};

// Simple icon version for compact use
export const AsimNexusIcon = ({ size = 24, color = '#667eea' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" fill={`url(#iconGrad-${size})`} />
    <defs>
      <linearGradient id={`iconGrad-${size}`} x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#667eea" />
        <stop offset="100%" stopColor="#764ba2" />
      </linearGradient>
    </defs>
    <circle cx="12" cy="12" r="4" fill="white" />
    <text x="12" y="15" textAnchor="middle" fontSize="8" fill="#667eea" fontWeight="bold">i</text>
  </svg>
);

export default AsimNexusLogo;
