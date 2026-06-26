import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';

// API — unified barrel import
import { getStoredToken, getStoredUser, clearAuth, healthAPI, personalAPI, osToolsAPI } from './api';

// Layout Components
import AuthPage from './components/layout/AuthPage';
import OnboardingPage from './components/layout/OnboardingPage';
import Sidebar from './components/layout/Sidebar';
import SettingsPage from './components/layout/SettingsPage';
import TeamsPage from './components/teams/TeamsPage';
import ErrorBoundary from './components/layout/ErrorBoundary';
import AsimOrb from './components/shared/AsimOrbMaster';
import { ChatProvider } from './contexts/ChatContext';

// Main Pages
import UniversalChat from './components/chat/UniversalChat';
import Dashboard from './components/dashboard/Dashboard';

// Consolidated Hubs (Smart Organization)
import OSHub from './components/pages/OSHub';
import EconomyHub from './components/pages/EconomyHub';
import AIHub from './components/pages/AIHub';
import IdentityHub from './components/pages/IdentityHub';
import NetworkHub from './components/pages/NetworkHub';
import LifeHub from './components/pages/LifeHub';
import MirrorDashboard from './components/mirror/MirrorDashboard';

// Odysseus Agent Integration
import AgentChat from './components/odysseus/AgentChat';
import MCPServiceBrowser from './components/odysseus/MCPServiceBrowser';
import AgentSessionPanel from './components/odysseus/AgentSessionPanel';
import ToolAuditView from './components/odysseus/ToolAuditView';
import ToolConfirmationDialog from './components/odysseus/ToolConfirmationDialog';
import { ToolConfirmationProvider, useToolConfirmation } from './components/odysseus/ToolConfirmationContext';
import './components/odysseus/odysseus.css';

import useAIPersonalization from './hooks/useAIPersonalization';
import './App.css';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const THEMES = {
  'deep-space': { bg: '#0a0a1a', accent: '#667eea', text: '#ffffff', card: 'rgba(255,255,255,0.05)' },
  'aurora': { bg: '#f0f9ff', accent: '#10b981', text: '#1a1a2e', card: 'rgba(0,0,0,0.05)' },
  'government': { bg: '#0d1b2a', accent: '#c9a84c', text: '#e8e8e8', card: 'rgba(255,255,255,0.06)' },
  'corporate': { bg: '#111827', accent: '#3b82f6', text: '#f9fafb', card: 'rgba(255,255,255,0.06)' },
  'medical': { bg: '#f8fafc', accent: '#0ea5e9', text: '#0f172a', card: 'rgba(0,0,0,0.04)' },
  'minimal': { bg: '#18181b', accent: '#a1a1aa', text: '#fafafa', card: 'rgba(255,255,255,0.04)' },
};

function applyTheme(themeName) {
  const t = THEMES[themeName] || THEMES['deep-space'];
  const r = document.documentElement;
  r.style.setProperty('--theme-bg', t.bg);
  r.style.setProperty('--accent-primary', t.accent);
  r.style.setProperty('--theme-text', t.text);
  r.style.setProperty('--theme-card', t.card);
  document.body.style.background = t.bg;
  document.body.style.color = t.text;
}

// Consolidated Navigation — 8 Main Routes
const NAV_RAIL = [
  { path: '/', icon: '💬', label: 'Chat', primary: true },
  { path: '/dashboard', icon: '📊', label: 'Dashboard' },
  { path: '/os', icon: '🖥️', label: 'OS', desc: 'Personal/World/Control' },
  { path: '/marketplace', icon: '🌍', label: 'Market', desc: 'Agents/Contracts/MCP' },
  { path: '/ai', icon: '🧠', label: 'AI', desc: 'Memory/Local LLM' },
  { path: '/identity', icon: '🔐', label: 'Identity', desc: 'ID/Blockchain/ZKP' },
  { path: '/life', icon: '🧬', label: 'Life', desc: 'Journey/Milestones' },
  { path: '/network', icon: '🌐', label: 'Network', desc: 'Mesh/Nodes' },
  { path: '/teams', icon: '👥', label: 'Teams', desc: 'Collaboration' },
  { path: '/settings', icon: '⚙️', label: 'Settings', primary: true },
];

const UNIVERSE_META = {
  personal: { icon: '👤', label: 'Personal', color: '#667eea' },
  family: { icon: '👨‍👩‍👧', label: 'Family', color: '#10b981' },
  community: { icon: '🏘️', label: 'Community', color: '#f59e0b' },
  company: { icon: '🏢', label: 'Company', color: '#3b82f6' },
  government: { icon: '🏛️', label: 'Govt', color: '#c9a84c' },
  global: { icon: '🌍', label: 'Global', color: '#8b5cf6' },
};

const THEME_META = [
  { id: 'deep-space', icon: '🌌', label: 'Space' },
  { id: 'aurora', icon: '🌿', label: 'Aurora' },
  { id: 'corporate', icon: '💼', label: 'Corp' },
  { id: 'government', icon: '🏛️', label: 'Govt' },
  { id: 'medical', icon: '🏥', label: 'Med' },
  { id: 'minimal', icon: '⬛', label: 'Minimal' },
];

function AppShell({ currentUser, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  useAIPersonalization();
  const [theme, setTheme] = useState(currentUser?.theme || 'deep-space');
  const [universeMode, setUniverseMode] = useState(currentUser?.universe_mode || 'personal');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [pendingExecution, setPendingExecution] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { openDialog, closeDialog } = useToolConfirmation();

  useEffect(() => { applyTheme(theme); }, [theme]);

  // Health check on app start — verify backend connectivity
  useEffect(() => {
    healthAPI.check().then(res => {
      if (res.data?.status === 'ok' || res.data?.success) {
        console.log('[AsimNexus] Backend connected');
      }
    }).catch(() => {
      console.warn('[AsimNexus] Backend unreachable');
    });
  }, []);

  // Poll for pending tool executions requiring human approval
  useEffect(() => {
    const checkPending = async () => {
      try {
        const res = await osToolsAPI.getPending();
        const pendingList = res.data?.pending || res.data?.executions || [];
        if (pendingList.length > 0) {
          setPendingExecution(pendingList[0]);
          setDialogOpen(true);
        }
      } catch {
        // Silently handle — backend may not support this endpoint yet
      }
    };
    const interval = setInterval(checkPending, 5000);
    checkPending();
    return () => clearInterval(interval);
  }, []);

  const handleToolApproved = useCallback(() => {
    setDialogOpen(false);
    setPendingExecution(null);
  }, []);

  const handleToolRejected = useCallback(() => {
    setDialogOpen(false);
    setPendingExecution(null);
  }, []);

  const handleCloseDialog = useCallback(() => {
    setDialogOpen(false);
    setPendingExecution(null);
  }, []);

  const handleChatCommand = useCallback((cmd) => {
    if (!cmd) return;
    if (cmd.type === 'theme') { setTheme(cmd.value); applyTheme(cmd.value); }
    if (cmd.type === 'universe') setUniverseMode(cmd.value);
    if (cmd.type === 'os') {
      const toolName = cmd.tool_name || 'hw.status';
      const params = cmd.parameters || {};
      osToolsAPI.execute(toolName, params).then(result => {
        console.log(`[OS] tool [${toolName}] executed:`, result);
      }).catch(err => {
        console.error(`[OS] tool [${toolName}] error:`, err);
      });
    }
  }, []);

  const activeNav = NAV_RAIL.find(n => n.path === location.pathname) || NAV_RAIL[0];
  const uMeta = UNIVERSE_META[universeMode] || UNIVERSE_META.personal;

  return (
    <div style={{ height: '100vh', overflow: 'hidden', background: 'var(--theme-bg)', color: 'var(--theme-text)', display: 'flex', position: 'relative' }}>

      {/* Background image */}
      <div style={{ position: 'fixed', inset: 0, backgroundImage: 'url("/asim-nexus-background.png")', backgroundSize: 'cover', backgroundPosition: 'center', zIndex: 0, opacity: 0.12, pointerEvents: 'none' }} />

      {/* ── PERMANENT LEFT ICON RAIL ── */}
      <nav style={{
        position: 'relative', zIndex: 10, width: 64, flexShrink: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        background: 'rgba(10,10,26,0.7)', backdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(255,255,255,0.06)',
        paddingTop: 8, gap: 4,
      }}>
        {/* Logo */}
        <div style={{ width: 40, height: 40, marginBottom: 8, cursor: 'pointer' }} onClick={() => navigate('/')}>
          <img src="/asimnexus-logo.png" alt="" style={{ width: 40, height: 40, borderRadius: '50%', filter: 'drop-shadow(0 0 8px var(--accent-primary))' }} />
        </div>

        {/* Nav icons */}
        {NAV_RAIL.map(item => {
          const active = location.pathname === item.path || (item.path === '/' && location.pathname === '/');
          return (
            <div key={item.path}
              title={item.label}
              onClick={() => navigate(item.path)}
              style={{
                width: 46, height: 46, borderRadius: 12, display: 'flex',
                flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', transition: 'all 0.18s',
                background: active ? 'rgba(102,126,234,0.22)' : 'transparent',
                border: active ? '1px solid rgba(102,126,234,0.45)' : '1px solid transparent',
                fontSize: item.primary ? 22 : 18,
                boxShadow: active ? '0 0 12px rgba(102,126,234,0.3)' : 'none',
              }}>
              <span>{item.icon}</span>
              <span style={{ fontSize: '0.45rem', opacity: 0.5, marginTop: 1, letterSpacing: 0.2 }}>{item.label.split(' ')[0]}</span>
            </div>
          );
        })}

        <div style={{ flex: 1 }} />

        {/* Universe badge */}
        <div title={`Universe: ${uMeta.label}`}
          onClick={() => setDrawerOpen(v => !v)}
          style={{
            width: 40, height: 40, borderRadius: '50%', display: 'flex',
            alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            background: `${uMeta.color}22`, border: `1px solid ${uMeta.color}55`,
            fontSize: 18, marginBottom: 4,
          }}>
          {uMeta.icon}
        </div>

        {/* Settings / drawer */}
        <div title="Settings"
          onClick={() => setDrawerOpen(v => !v)}
          style={{
            width: 40, height: 40, borderRadius: '50%', display: 'flex',
            alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            background: 'rgba(255,255,255,0.05)', fontSize: 18, marginBottom: 8,
          }}>
          ⚙️
        </div>
      </nav>

      {/* ── SETTINGS DRAWER (slides in from left over rail) ── */}
      {drawerOpen && (
        <>
          <div style={{ position: 'fixed', inset: 0, zIndex: 19, background: 'rgba(0,0,0,0.4)' }} onClick={() => setDrawerOpen(false)} />
          <div style={{
            position: 'fixed', top: 0, left: 64, bottom: 0, width: 260, zIndex: 20,
            background: 'rgba(10,10,28,0.97)', backdropFilter: 'blur(24px)',
            borderRight: '1px solid rgba(255,255,255,0.08)',
            display: 'flex', flexDirection: 'column', padding: '20px 0', overflowY: 'auto',
          }}>
            <div style={{ padding: '0 18px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>⚙️ Settings</span>
              <button onClick={() => setDrawerOpen(false)} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', fontSize: 18 }}>✕</button>
            </div>

            <div style={{ padding: '12px 18px 6px', fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: 2, opacity: 0.4 }}>Universe Mode</div>
            <div style={{ padding: '0 18px', display: 'flex', flexDirection: 'column', gap: 4 }}>
              {Object.entries(UNIVERSE_META).map(([id, u]) => (
                <div key={id} onClick={() => { setUniverseMode(id); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px',
                    borderRadius: 10, cursor: 'pointer', transition: 'all 0.15s',
                    background: universeMode === id ? `${u.color}22` : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${universeMode === id ? u.color + '55' : 'transparent'}`,
                    color: universeMode === id ? u.color : 'rgba(255,255,255,0.65)',
                    fontSize: '0.85rem',
                  }}>
                  <span>{u.icon}</span><span>{u.label}</span>
                  {universeMode === id && <span style={{ marginLeft: 'auto', fontSize: '0.7rem' }}>✓</span>}
                </div>
              ))}
            </div>

            <div style={{ padding: '16px 18px 6px', fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: 2, opacity: 0.4 }}>Theme</div>
            <div style={{ padding: '0 18px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {THEME_META.map(t => (
                <button key={t.id} onClick={() => { setTheme(t.id); applyTheme(t.id); }}
                  style={{
                    padding: '8px 6px', borderRadius: 8, cursor: 'pointer', fontSize: '0.78rem',
                    background: theme === t.id ? 'rgba(102,126,234,0.2)' : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${theme === t.id ? 'rgba(102,126,234,0.5)' : 'rgba(255,255,255,0.08)'}`,
                    color: theme === t.id ? '#667eea' : 'rgba(255,255,255,0.6)',
                  }}>
                  {t.icon} {t.label}
                </button>
              ))}
            </div>

            <div style={{ flex: 1 }} />

            <div style={{ padding: '12px 18px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 8 }}>
                👤 {currentUser?.display_name || 'User'}
              </div>
              <button onClick={onLogout}
                style={{ width: '100%', padding: '9px', borderRadius: 8, cursor: 'pointer', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '0.85rem' }}>
                ↗ Logout
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── MAIN CONTENT ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 1, overflow: 'hidden' }}>

        {/* Slim top bar */}
        <header style={{
          flexShrink: 0, height: 44,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 16px',
          background: 'rgba(10,10,26,0.5)', backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem', background: 'linear-gradient(45deg, #667eea, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>ASIMNEXUS</span>
            <span style={{ fontSize: '0.65rem', opacity: 0.35 }}>·</span>
            <span style={{ fontSize: '0.78rem', opacity: 0.6 }}>{activeNav.icon} {activeNav.label}</span>
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <span style={{
              padding: '2px 10px', borderRadius: 20, fontSize: '0.68rem',
              background: `${uMeta.color}22`, border: `1px solid ${uMeta.color}44`,
              color: uMeta.color, cursor: 'pointer',
            }} onClick={() => setDrawerOpen(v => !v)}>
              {uMeta.icon} {uMeta.label}
            </span>
            <span style={{ fontSize: '0.72rem', opacity: 0.45, cursor: 'pointer' }} onClick={() => setDrawerOpen(v => !v)}>
              {currentUser?.display_name || 'User'} ⚙️
            </span>
          </div>
        </header>

        {/* Page content — full height with glass background */}
        <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
          {/* 🌌 Cosmic Background */}
          <div style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundImage: 'url("/asim-nexus-background.png")',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundAttachment: 'fixed',
            zIndex: 0,
          }} />
          {/* 🧊 Glass Overlay */}
          <div style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(10, 10, 26, 0.60)',
            backdropFilter: 'blur(3px)',
            WebkitBackdropFilter: 'blur(3px)',
            zIndex: 1,
          }} />
          {/* Routes */}
          <div style={{ position: 'relative', zIndex: 2, flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <Routes>
              {/* Core Routes */}
              <Route path="/" element={<UniversalChat user={currentUser} onCommand={handleChatCommand} />} />
              <Route path="/chat" element={<UniversalChat user={currentUser} onCommand={handleChatCommand} />} />
              <Route path="/dashboard" element={<div style={{ flex: 1, overflow: 'auto', padding: 16 }}><Dashboard user={currentUser} universeMode={universeMode} theme={theme} /></div>} />

              {/* Odysseus Agent Routes */}
              <Route path="/agent" element={<AgentSessionPanel user={currentUser} />} />
              <Route path="/audit" element={<ToolAuditView user={currentUser} />} />

              {/* Consolidated Hubs */}
              <Route path="/os" element={<OSHub user={currentUser} />} />
              <Route path="/mirror" element={<div style={{ flex: 1, overflow: 'auto', padding: 16 }}><MirrorDashboard userId={currentUser?.id || 'default'} /></div>} />
              <Route path="/marketplace" element={<EconomyHub user={currentUser} />} />
              <Route path="/ai" element={<AIHub user={currentUser} />} />
              <Route path="/identity" element={<IdentityHub user={currentUser} />} />
              <Route path="/network" element={<NetworkHub user={currentUser} />} />
              <Route path="/life" element={<LifeHub user={currentUser} />} />

              {/* Teams */}
              <Route path="/teams" element={<TeamsPage />} />

              {/* Settings */}
              <Route path="/settings" element={<SettingsPage user={currentUser} />} />

              {/* MCP Browser (before legacy redirect) */}
              <Route path="/mcp" element={<MCPServiceBrowser user={currentUser} />} />

              {/* Legacy Redirects (backward compatibility) */}
              <Route path="/personal" element={<OSHub user={currentUser} />} />
              <Route path="/world-os" element={<OSHub user={currentUser} />} />
              <Route path="/os-panel" element={<OSHub user={currentUser} />} />
              <Route path="/contracts" element={<EconomyHub user={currentUser} />} />
              <Route path="/clones" element={<EconomyHub user={currentUser} />} />
              <Route path="/memory" element={<AIHub user={currentUser} />} />
              <Route path="/local-llm" element={<AIHub user={currentUser} />} />
              <Route path="/mesh" element={<NetworkHub user={currentUser} />} />

              {/* Onboarding */}
              <Route path="/onboard" element={<OnboardingPage onComplete={(user, token) => { localStorage.setItem('asimnexus_token', token); localStorage.setItem('asimnexus_user', JSON.stringify(user)); window.location.href = '/'; }} />} />

              {/* Catch All */}
              <Route path="*" element={<UniversalChat user={currentUser} onCommand={handleChatCommand} />} />
            </Routes>
          </div>
        </main>
      </div>
      {/* ── Global Tool Confirmation Dialog ── */}
      <ToolConfirmationDialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        execution={pendingExecution}
        onApproved={handleToolApproved}
        onRejected={handleToolRejected}
      />
    </div>
  );
}

function App() {
  const [authed, setAuthed] = useState(!!getStoredToken());
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleAuthSuccess = (user) => {
    setCurrentUser(user);
    setAuthed(true);
  };

  const handleLogout = () => {
    clearAuth();
    setAuthed(false);
    setCurrentUser(null);
  };

  if (!authed) {
    return (
      <ErrorBoundary>
        <ChatProvider>
          <div style={{ position: 'relative', minHeight: '100vh' }}>
            <div style={{
              position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
              backgroundImage: 'url("/asim-nexus-background.png")',
              backgroundSize: 'cover', backgroundPosition: 'center', zIndex: 0,
            }} />
            <div style={{ position: 'relative', zIndex: 1 }}>
              <AuthPage onAuthSuccess={handleAuthSuccess} />
            </div>
            {/* Demo Mode Orb - with Asim Nexus Logo */}
            <AsimOrb
              user={{ display_name: 'Guest', mode: 'demo' }}
              onCommand={(cmd) => console.log('Demo command:', cmd)}
              systemMetrics={{ health: 0.8, mesh_health: 0.9, work: 0.7, wallet: 0.6 }}
            />
          </div>
        </ChatProvider>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <ChatProvider>
        <ToolConfirmationProvider>
          <Router>
            <AppShell currentUser={currentUser} onLogout={handleLogout} />
            <AsimOrb
              user={currentUser}
              onCommand={(cmd) => console.log('Orb command:', cmd)}
              systemMetrics={{ health: 0.85, mesh_health: 0.9, work: 0.75, wallet: 0.7 }}
            />
          </Router>
        </ToolConfirmationProvider>
      </ChatProvider>
    </ErrorBoundary>
  );
}

export default App;
