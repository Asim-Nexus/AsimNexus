/**
 * SmartHub — Reusable Tab-Based Hub Layout
 * DRY: Don't Repeat Yourself — One component, all hubs
 */
import React, { useState, useEffect } from 'react';

export default function SmartHub({ 
  tabs = [], 
  children, 
  defaultTab = 0,
  accentColor = '#667eea',
  title = '',
  icon = ''
}) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [isCompact, setIsCompact] = useState(false);

  // Background image path
  const bgImage = '/asim-nexus-background.png';

  // Keyboard shortcuts: Alt+1, Alt+2, etc.
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey && e.key >= '1' && e.key <= '9') {
        const idx = parseInt(e.key) - 1;
        if (idx < tabs.length) {
          setActiveTab(idx);
          e.preventDefault();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tabs.length]);

  const activeTabData = tabs[activeTab];

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      position: 'relative',
    }}>
      {/* 🌌 Cosmic Background Image */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url(${bgImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
        zIndex: 0,
      }} />
      
      {/* 🧊 Glass Overlay with Blur */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(10, 10, 26, 0.65)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        zIndex: 1,
      }} />
      
      {/* Content Container */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}>
      {/* Smart Header with Tabs */}
      <div style={{ 
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 16px',
        borderBottom: `1px solid ${accentColor}22`,
        background: `linear-gradient(90deg, ${accentColor}08, transparent)`,
      }}>
        {/* Title */}
        {title && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8,
            marginRight: 16,
            minWidth: 120
          }}>
            <span style={{ fontSize: 20 }}>{icon}</span>
            <span style={{ 
              fontWeight: 700, 
              fontSize: '1rem',
              color: accentColor 
            }}>{title}</span>
          </div>
        )}

        {/* Compact Mode Toggle */}
        <button
          onClick={() => setIsCompact(!isCompact)}
          style={{
            marginLeft: 'auto',
            padding: '4px 8px',
            fontSize: '0.7rem',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 6,
            color: 'rgba(255,255,255,0.5)',
            cursor: 'pointer'
          }}
        >
          {isCompact ? '□' : '◫'}
        </button>
      </div>

      {/* Tab Navigation — Smart & Adaptive */}
      <div style={{ 
        display: 'flex', 
        gap: isCompact ? 2 : 6, 
        padding: isCompact ? '6px 12px' : '10px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(10,10,26,0.6)',
        overflowX: 'auto',
        scrollbarWidth: 'none',
      }}>
        {tabs.map((tab, idx) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(idx)}
            title={`Alt+${idx + 1}: ${tab.label}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: isCompact ? 4 : 8,
              padding: isCompact ? '6px 10px' : '8px 14px',
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
              background: activeTab === idx 
                ? `${accentColor}25` 
                : 'rgba(255,255,255,0.03)',
              color: activeTab === idx 
                ? accentColor 
                : 'rgba(255,255,255,0.5)',
              boxShadow: activeTab === idx 
                ? `0 2px 8px ${accentColor}30` 
                : 'none',
            }}
          >
            <span style={{ fontSize: isCompact ? 14 : 16 }}>{tab.icon}</span>
            {!isCompact && (
              <div style={{ textAlign: 'left' }}>
                <div style={{ 
                  fontSize: '0.8rem', 
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}>
                  {tab.label}
                  {activeTab === idx && (
                    <span style={{ 
                      fontSize: '0.6rem', 
                      opacity: 0.5,
                      marginLeft: 2
                    }}>⌥{idx + 1}</span>
                  )}
                </div>
                <div style={{ 
                  fontSize: '0.6rem', 
                  opacity: 0.4,
                  marginTop: 1
                }}>{tab.desc}</div>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Content Area with Animation */}
      <div style={{ 
        flex: 1, 
        overflow: 'auto',
        position: 'relative'
      }}>
        <div 
          key={activeTab}
          style={{
            animation: 'fadeIn 0.2s ease',
            padding: isCompact ? 12 : 16
          }}
        >
          {/* Render active tab content */}
          {typeof children === 'function' 
            ? children(activeTabData, activeTab)
            : Array.isArray(children) 
              ? children[activeTab]
              : children
          }
        </div>
      </div>

      {/* CSS Animation */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      </div>
    </div>
  );
}
