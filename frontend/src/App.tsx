import React, { useState, useEffect, useCallback } from 'react';
import { I18nProvider } from './i18n';
import NotificationToast from './components/common/NotificationToast';
import SystemTray from './components/common/SystemTray';
import { notificationService } from './services/NotificationService';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';

// API — unified barrel import
import { getStoredToken, getStoredUser, clearAuth, healthAPI, osToolsAPI } from './api';

// Layout Components
import AuthPage from './components/layout/AuthPage';
import OnboardingPage from './components/layout/OnboardingPage';
import SettingsPage from './components/layout/SettingsPage';
import TeamsPage from './components/teams/TeamsPage';
import ErrorBoundary from './components/layout/ErrorBoundary';
import AsimOrb from './components/shared/AsimOrbMaster';
import { ChatProvider } from './contexts/ChatContext';

// Main Pages
import UniversalChat from './components/chat/UniversalChat';

// Consolidated Hubs (Smart Organization)
import OSHub from './components/pages/OSHub';
import EconomyHub from './components/pages/EconomyHub';
import AIHub from './components/pages/AIHub';
import IdentityHub from './components/pages/IdentityHub';
import NetworkHub from './components/pages/NetworkHub';
import LifeHub from './components/pages/LifeHub';
import NepalHub from './components/pages/NepalHub';
import GovernanceHub from './components/pages/GovernanceHub';
import MirrorDashboard from './components/mirror/MirrorDashboard';
import SelfAwarenessHub from './components/self-awareness/SelfAwarenessHub';
import ARVRViewport from './components/arvr/ARVRViewport';

// Odysseus Agent Integration
import MCPServiceBrowser from './components/odysseus/MCPServiceBrowser';
import AgentSessionPanel from './components/odysseus/AgentSessionPanel';
import ToolAuditView from './components/odysseus/ToolAuditView';
import ToolConfirmationDialog from './components/odysseus/ToolConfirmationDialog';
import { ToolConfirmationProvider } from './components/odysseus/ToolConfirmationContext';
import './components/odysseus/odysseus.css';

import useAIPersonalization from './hooks/useAIPersonalization';
import './App.css';

interface ThemeConfig {
    bg: string;
    accent: string;
    text: string;
    card: string;
}

interface NavItem {
    path: string;
    icon: string;
    label: string;
    primary?: boolean;
    desc?: string;
}

interface UniverseMeta {
    icon: string;
    label: string;
    color: string;
}

interface ThemeMeta {
    id: string;
    icon: string;
    label: string;
}

interface AppShellProps {
    currentUser: Record<string, unknown> | null;
    onLogout: () => void;
}

const THEMES: Record<string, ThemeConfig> = {
    'deep-space': { bg: '#0a0a1a', accent: '#667eea', text: '#ffffff', card: 'rgba(255,255,255,0.05)' },
    'aurora': { bg: '#f0f9ff', accent: '#10b981', text: '#1a1a2e', card: 'rgba(0,0,0,0.05)' },
    'government': { bg: '#0d1b2a', accent: '#c9a84c', text: '#e8e8e8', card: 'rgba(255,255,255,0.06)' },
    'corporate': { bg: '#111827', accent: '#3b82f6', text: '#f9fafb', card: 'rgba(255,255,255,0.06)' },
    'medical': { bg: '#f8fafc', accent: '#0ea5e9', text: '#0f172a', card: 'rgba(0,0,0,0.04)' },
    'minimal': { bg: '#18181b', accent: '#a1a1aa', text: '#fafafa', card: 'rgba(255,255,255,0.04)' },
};

function applyTheme(themeName: string): void {
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
const NAV_RAIL: NavItem[] = [
    { path: '/', icon: '💬', label: 'Chat', primary: true },
    { path: '/dashboard', icon: '📊', label: 'Dashboard' },
    { path: '/os', icon: '🖥️', label: 'OS', desc: 'Personal/World/Control' },
    { path: '/marketplace', icon: '🌍', label: 'Market', desc: 'Agents/Contracts/MCP' },
    { path: '/ai', icon: '🧠', label: 'AI', desc: 'Memory/Local LLM' },
    { path: '/identity', icon: '🔐', label: 'Identity', desc: 'ID/Blockchain/ZKP' },
    { path: '/life', icon: '🧬', label: 'Life', desc: 'Journey/Milestones' },
    { path: '/nepal', icon: '🇳🇵', label: 'Nepal', desc: 'Digital Nepal' },
    { path: '/network', icon: '🌐', label: 'Network', desc: 'Mesh/Nodes' },
    { path: '/self-awareness', icon: '🪞', label: 'Self', desc: 'Self-Awareness' },
    { path: '/teams', icon: '👥', label: 'Teams', desc: 'Collaboration' },
    { path: '/settings', icon: '⚙️', label: 'Settings', primary: true },
];

const UNIVERSE_META: Record<string, UniverseMeta> = {
    personal: { icon: '👤', label: 'Personal', color: '#667eea' },
    family: { icon: '👨‍👩‍👧', label: 'Family', color: '#10b981' },
    community: { icon: '🏘️', label: 'Community', color: '#f59e0b' },
    company: { icon: '🏢', label: 'Company', color: '#3b82f6' },
    government: { icon: '🏛️', label: 'Govt', color: '#c9a84c' },
    global: { icon: '🌍', label: 'Global', color: '#8b5cf6' },
};

const THEME_META: ThemeMeta[] = [
    { id: 'deep-space', icon: '🌌', label: 'Space' },
    { id: 'aurora', icon: '🌿', label: 'Aurora' },
    { id: 'corporate', icon: '💼', label: 'Corp' },
    { id: 'government', icon: '🏛️', label: 'Govt' },
    { id: 'medical', icon: '🏥', label: 'Med' },
    { id: 'minimal', icon: '⬛', label: 'Minimal' },
];

function AppShell({ currentUser, onLogout }: AppShellProps) {
    const navigate = useNavigate();
    const location = useLocation();
    useAIPersonalization();
    const [theme, setTheme] = useState<string>((currentUser?.theme as string) || 'deep-space');
    const [universeMode, setUniverseMode] = useState<string>((currentUser?.universe_mode as string) || 'personal');
    const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
    const [pendingExecution, setPendingExecution] = useState<Record<string, unknown> | null>(null);
    const [dialogOpen, setDialogOpen] = useState<boolean>(false);
    const [trayOpen, setTrayOpen] = useState<boolean>(false);
    const [notifCount, setNotifCount] = useState<number>(0);
    useEffect(() => { applyTheme(theme); }, [theme]);

    // Track unread notification count for bell badge
    useEffect(() => {
        const updateCount = () => setNotifCount(notificationService.getUnreadCount());
        updateCount();
        const unsub = notificationService.onNotification(() => updateCount());
        // Also poll periodically for changes from other tabs
        const interval = setInterval(updateCount, 5000);
        return () => { unsub(); clearInterval(interval); };
    }, []);

    // Health check on app start — verify backend connectivity
    useEffect(() => {
        healthAPI.check().then((res: unknown) => {
            const data = (res as Record<string, unknown>)?.data as Record<string, unknown> || {};
            if (data.status === 'ok' || data.success) {
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
                const res = await osToolsAPI.getPending() as unknown as Record<string, unknown>;
                const data = (res.data as Record<string, unknown>) || {};
                const pendingList = (data.pending || data.executions || []) as Record<string, unknown>[];
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

    const handleChatCommand = useCallback((cmd: string) => {
        if (!cmd) return;
        // cmd is a JSON string from the chat system
        try {
            const parsed = JSON.parse(cmd) as Record<string, unknown>;
            if (parsed.type === 'theme') { setTheme(parsed.value as string); applyTheme(parsed.value as string); }
            if (parsed.type === 'universe') setUniverseMode(parsed.value as string);
            if (parsed.type === 'os') {
                const toolName = (parsed.tool_name as string) || 'hw.status';
                const params = (parsed.parameters as Record<string, unknown>) || {};
                osToolsAPI.execute(toolName, params).then((result: unknown) => {
                    console.log(`[OS] tool [${toolName}] executed:`, result);
                }).catch((err: unknown) => {
                    console.error(`[OS] tool [${toolName}] error:`, err);
                });
            }
        } catch {
            // Not JSON, treat as plain command string
            console.log('[Chat] command:', cmd);
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
                                color: active ? '#667eea' : 'rgba(255,255,255,0.5)',
                                fontSize: active ? 20 : 18,
                            } as React.CSSProperties}
                        >
                            <span>{item.icon}</span>
                        </div>
                    );
                })}
            </nav>

            {/* ── SETTINGS DRAWER (slide-in) ── */}
            {drawerOpen && (
                <div style={{
                    position: 'fixed', top: 0, left: 64, bottom: 0, width: 280,
                    background: 'rgba(10,10,26,0.92)', backdropFilter: 'blur(24px)',
                    borderRight: '1px solid rgba(255,255,255,0.08)',
                    zIndex: 20, display: 'flex', flexDirection: 'column', padding: 16, gap: 16,
                    overflow: 'auto',
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', opacity: 0.8 }}>Settings</span>
                        <span style={{ cursor: 'pointer', opacity: 0.5, fontSize: '1.1rem' }} onClick={() => setDrawerOpen(false)}>✕</span>
                    </div>

                    {/* Universe Mode Selector */}
                    <div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.4, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>Universe Mode</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {Object.entries(UNIVERSE_META).map(([key, meta]) => (
                                <div key={key} onClick={() => setUniverseMode(key)}
                                    style={{
                                        padding: '6px 12px', borderRadius: 20, fontSize: '0.72rem', cursor: 'pointer',
                                        background: universeMode === key ? `${meta.color}33` : 'rgba(255,255,255,0.05)',
                                        border: `1px solid ${universeMode === key ? meta.color : 'transparent'}`,
                                        color: universeMode === key ? meta.color : 'rgba(255,255,255,0.6)',
                                    }}>
                                    {meta.icon} {meta.label}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Theme Grid */}
                    <div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.4, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>Theme</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {THEME_META.map(tm => (
                                <div key={tm.id} onClick={() => { setTheme(tm.id); applyTheme(tm.id); }}
                                    style={{
                                        padding: '6px 12px', borderRadius: 20, fontSize: '0.72rem', cursor: 'pointer',
                                        background: theme === tm.id ? 'rgba(102,126,234,0.25)' : 'rgba(255,255,255,0.05)',
                                        border: `1px solid ${theme === tm.id ? '#667eea' : 'transparent'}`,
                                        color: theme === tm.id ? '#667eea' : 'rgba(255,255,255,0.6)',
                                    }}>
                                    {tm.icon} {tm.label}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Logout */}
                    <div style={{ marginTop: 'auto' }}>
                        <div onClick={onLogout}
                            style={{
                                padding: '10px 16px', borderRadius: 12, fontSize: '0.8rem', cursor: 'pointer',
                                background: 'rgba(239,68,68,0.15)', color: '#ef4444', textAlign: 'center',
                            }}>
                            🚪 Logout
                        </div>
                    </div>
                </div>
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
                        {/* Notification Bell */}
                        <div
                            onClick={() => setTrayOpen(v => !v)}
                            style={{
                                position: 'relative',
                                padding: '4px 8px',
                                borderRadius: 8,
                                cursor: 'pointer',
                                fontSize: '1rem',
                                background: trayOpen ? 'rgba(139,92,246,0.15)' : 'transparent',
                                transition: 'all 0.15s',
                            }}
                            title="Notifications"
                        >
                            🔔
                            {notifCount > 0 && (
                                <span style={{
                                    position: 'absolute',
                                    top: -2,
                                    right: -2,
                                    background: '#ef4444',
                                    borderRadius: '50%',
                                    width: 16,
                                    height: 16,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '0.6rem',
                                    fontWeight: 700,
                                    color: '#fff',
                                    boxShadow: '0 0 6px rgba(239,68,68,0.6)',
                                }}>
                                    {notifCount > 9 ? '9+' : notifCount}
                                </span>
                            )}
                        </div>

                        <span style={{
                            padding: '2px 10px', borderRadius: 20, fontSize: '0.68rem',
                            background: `${uMeta.color}22`, border: `1px solid ${uMeta.color}44`,
                            color: uMeta.color, cursor: 'pointer',
                        }} onClick={() => setDrawerOpen(v => !v)}>
                            {uMeta.icon} {uMeta.label}
                        </span>
                        <span style={{ fontSize: '0.72rem', opacity: 0.45, cursor: 'pointer' }} onClick={() => setDrawerOpen(v => !v)}>
                            {(currentUser?.display_name as string) || 'User'} ⚙️
                        </span>
                    </div>
                </header>

                {/* System Tray (Notification Center) */}
                {trayOpen && <SystemTray onClose={() => setTrayOpen(false)} />}

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
                            <Route path="/" element={<UniversalChat user={currentUser ?? undefined} onCommand={handleChatCommand} />} />
                            <Route path="/chat" element={<UniversalChat user={currentUser ?? undefined} onCommand={handleChatCommand} />} />
                            <Route path="/dashboard" element={<div style={{ flex: 1, overflow: 'auto', padding: 16 }}><MirrorDashboard userId={(currentUser?.id as string) || 'default'} /></div>} />

                            {/* Odysseus Agent Routes */}
                            <Route path="/agent" element={<AgentSessionPanel user={currentUser ?? undefined} />} />
                            <Route path="/audit" element={<ToolAuditView user={currentUser ?? undefined} />} />

                            {/* Consolidated Hubs */}
                            <Route path="/os" element={<OSHub user={currentUser ?? undefined} />} />
                            <Route path="/mirror" element={<div style={{ flex: 1, overflow: 'auto', padding: 16 }}><MirrorDashboard userId={(currentUser?.id as string) || 'default'} /></div>} />
                            <Route path="/marketplace" element={<EconomyHub user={currentUser ?? undefined} />} />
                            <Route path="/ai" element={<AIHub user={currentUser ?? undefined} onCommand={handleChatCommand} />} />
                            <Route path="/identity" element={<IdentityHub user={currentUser ?? undefined} />} />
                            <Route path="/nepal" element={<NepalHub user={currentUser ?? undefined} />} />
                            <Route path="/governance" element={<GovernanceHub user={currentUser ?? undefined} />} />
                            <Route path="/network" element={<NetworkHub user={currentUser ?? undefined} />} />
                            <Route path="/life" element={<LifeHub user={currentUser ?? undefined} />} />

                            {/* Self-Awareness Dashboard */}
                            <Route path="/self-awareness" element={<div style={{ flex: 1, overflow: 'auto', padding: 16 }}><SelfAwarenessHub /></div>} />

                            {/* AR/VR Immersive Interface */}
                            <Route path="/arvr" element={<div style={{ flex: 1, overflow: 'auto' }}><ARVRViewport user={currentUser ?? undefined} /></div>} />

                            {/* Teams */}
                            <Route path="/teams" element={<TeamsPage />} />

                            {/* Settings */}
                            <Route path="/settings" element={<SettingsPage {...({ user: currentUser } as any)} />} />

                            {/* MCP Browser (before legacy redirect) */}
                            <Route path="/mcp" element={<MCPServiceBrowser user={currentUser ?? undefined} />} />

                            {/* Legacy Redirects (backward compatibility) */}
                            <Route path="/personal" element={<OSHub user={currentUser ?? undefined} />} />
                            <Route path="/world-os" element={<OSHub user={currentUser ?? undefined} />} />
                            <Route path="/os-panel" element={<OSHub user={currentUser ?? undefined} />} />
                            <Route path="/contracts" element={<EconomyHub user={currentUser ?? undefined} />} />
                            <Route path="/clones" element={<EconomyHub user={currentUser ?? undefined} />} />
                            <Route path="/memory" element={<AIHub user={currentUser ?? undefined} />} />
                            <Route path="/local-llm" element={<AIHub user={currentUser ?? undefined} />} />
                            <Route path="/mesh" element={<NetworkHub user={currentUser ?? undefined} />} />

                            {/* Onboarding */}
                            <Route path="/onboard" element={<OnboardingPage onComplete={(user: Record<string, unknown>, token: string) => { localStorage.setItem('asimnexus_token', token); localStorage.setItem('asimnexus_user', JSON.stringify(user)); window.location.href = '/'; }} />} />

                            {/* Catch All */}
                            <Route path="*" element={<UniversalChat user={currentUser ?? undefined} onCommand={handleChatCommand} />} />
                        </Routes>
                    </div>
                </main>
            </div>
            {/* ── In-App Toast Notifications ── */}
            <NotificationToast />
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
    const [authed, setAuthed] = useState<boolean>(!!getStoredToken());
    const [currentUser, setCurrentUser] = useState<Record<string, unknown> | null>(getStoredUser() as Record<string, unknown> | null);
    const handleAuthSuccess = (user: Record<string, unknown>, _token: string) => {
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
                <I18nProvider>
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
                                onCommand={(cmd: string) => console.log('Demo command:', cmd)}
                                systemMetrics={{ health: 0.8, mesh_health: 0.9, work: 0.7, wallet: 0.6 }}
                            />
                        </div>
                    </ChatProvider>
                </I18nProvider>
            </ErrorBoundary>
        );
    }

    return (
        <ErrorBoundary>
            <I18nProvider>
                <ChatProvider>
                    <ToolConfirmationProvider>
                        <Router>
                            <AppShell currentUser={currentUser} onLogout={handleLogout} />
                            <AsimOrb
                                user={currentUser ?? undefined}
                                onCommand={(cmd: string) => console.log('Orb command:', cmd)}
                                systemMetrics={{ health: 0.85, mesh_health: 0.9, work: 0.75, wallet: 0.7 }}
                            />
                        </Router>
                    </ToolConfirmationProvider>
                </ChatProvider>
            </I18nProvider>
        </ErrorBoundary>
    );
}

export default App;
