import React from 'react';

const NAV_ITEMS = [
  { id: '/',            icon: '🌌', label: 'Dashboard' },
  { id: '/chat',        icon: '💬', label: 'AI Chat' },
  { id: '/clones',      icon: '🤖', label: '15 Clones' },
  { id: '/marketplace', icon: '🌍', label: 'Job Marketplace' },
];

const THEMES = ['deep-space', 'aurora', 'government', 'corporate', 'medical', 'minimal'];
const UNIVERSES = [
  { id: 'personal',   icon: '👤', label: 'Personal' },
  { id: 'family',     icon: '👨‍👩‍👧', label: 'Family' },
  { id: 'community',  icon: '🏘️', label: 'Community' },
  { id: 'company',    icon: '🏢', label: 'Company' },
  { id: 'government', icon: '🏛️', label: 'Government' },
  { id: 'global',     icon: '🌍', label: 'Global' },
];

export default function Sidebar({
  isOpen, onClose, onNavigate, activeRoute,
  universeMode, theme,
  onThemeChange, onUniverseChange, onLogout,
}) {
  if (!isOpen) return null;

  const s = {
    overlay: {
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
    },
    sidebar: {
      position: 'fixed', top: 0, left: 0, bottom: 0, width: 280, zIndex: 1001,
      background: 'rgba(10,10,26,0.95)',
      borderRight: '1px solid rgba(255,255,255,0.08)',
      backdropFilter: 'blur(20px)',
      display: 'flex', flexDirection: 'column',
      overflowY: 'auto', padding: '20px 0',
    },
    header: {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 20px 20px',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
    },
    section: { padding: '16px 20px 8px', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: 2, opacity: 0.4, color: '#fff' },
    navItem: (active) => ({
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '10px 20px', cursor: 'pointer',
      background: active ? 'rgba(102,126,234,0.15)' : 'transparent',
      borderLeft: active ? '3px solid var(--accent-primary, #667eea)' : '3px solid transparent',
      color: active ? 'var(--accent-primary, #667eea)' : 'rgba(255,255,255,0.7)',
      transition: 'all 0.2s',
      fontSize: '0.9rem',
    }),
    themeBtn: (active) => ({
      padding: '5px 10px', borderRadius: 6, cursor: 'pointer', fontSize: '0.75rem',
      border: active ? '1px solid var(--accent-primary, #667eea)' : '1px solid rgba(255,255,255,0.15)',
      background: active ? 'rgba(102,126,234,0.2)' : 'transparent',
      color: 'rgba(255,255,255,0.7)', margin: '2px',
    }),
    unBtn: (active) => ({
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '7px 12px', borderRadius: 8, cursor: 'pointer',
      background: active ? 'rgba(102,126,234,0.2)' : 'transparent',
      border: active ? '1px solid rgba(102,126,234,0.4)' : '1px solid rgba(255,255,255,0.08)',
      color: active ? '#fff' : 'rgba(255,255,255,0.6)',
      fontSize: '0.82rem', margin: '3px 0', transition: 'all 0.2s',
    }),
    logoutBtn: {
      margin: '16px 20px 0', padding: '10px', borderRadius: 8, cursor: 'pointer',
      background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
      color: '#ef4444', fontSize: '0.85rem',
    },
  };

  return (
    <>
      <div style={s.overlay} onClick={onClose} />
      <div style={s.sidebar}>
        <div style={s.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/asimnexus-logo.png" alt="" style={{ width: 32, height: 32, borderRadius: '50%' }} />
            <span style={{ fontWeight: 700, color: '#fff', fontSize: '1rem' }}>AsimNexus</span>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: 20 }}>✕</button>
        </div>

        <div style={s.section}>Navigation</div>
        {NAV_ITEMS.map(item => (
          <div key={item.id} style={s.navItem(activeRoute === item.id || activeRoute.startsWith(item.id + '/'))}
            onClick={() => onNavigate(item.id)}>
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}

        <div style={s.section}>Universe Mode</div>
        <div style={{ padding: '4px 20px' }}>
          {UNIVERSES.map(u => (
            <div key={u.id} style={s.unBtn(universeMode === u.id)}
              onClick={() => onUniverseChange(u.id)}>
              <span>{u.icon}</span>
              <span>{u.label}</span>
            </div>
          ))}
        </div>

        <div style={s.section}>Theme</div>
        <div style={{ padding: '4px 20px', display: 'flex', flexWrap: 'wrap' }}>
          {THEMES.map(t => (
            <button key={t} style={s.themeBtn(theme === t)}
              onClick={() => onThemeChange(t)}>
              {t}
            </button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ padding: '0 20px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 12 }}>
          <div style={{ fontSize: '0.7rem', opacity: 0.35, color: '#fff', textAlign: 'center', marginBottom: 4 }}>
            💬 Chat Commands: "dark mode", "family universe", "openai api key: sk-..."
          </div>
        </div>

        <button style={s.logoutBtn} onClick={onLogout}>↗ Logout</button>
      </div>
    </>
  );
}
