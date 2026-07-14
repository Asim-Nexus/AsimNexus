/**
 * MeshSelector — Mesh Context Mode Switcher
 * C4: 4 mesh modes: Local, Personal, Cloud, Public
 * Each mode represents a different connectivity context
 */
import React, { useState, useEffect, useCallback } from 'react';
import { meshAPI } from '../../api/asimnexus';

// ── Mesh Mode Definitions ──
interface MeshMode {
    id: string;
    icon: string;
    label: string;
    desc: string;
    details: string;
    color: string;
    bgColor: string;
}

const MESH_MODES: MeshMode[] = [
    {
        id: 'local',
        icon: '🖥️',
        label: 'Local Mesh',
        desc: 'Your device only — no external routing',
        details: 'LAN-only P2P mesh. Best for offline-first operations, local file sync, and air-gap isolation. No data leaves your network.',
        color: '#10b981',
        bgColor: 'rgba(16,185,129,0.1)',
    },
    {
        id: 'personal',
        icon: '📱',
        label: 'Personal Mesh',
        desc: 'Your authenticated devices',
        details: 'Connect all your devices — phone, laptop, desktop, tablet. Encrypted peer auth. Personal sync across devices with CRDT conflict resolution.',
        color: '#3b82f6',
        bgColor: 'rgba(59,130,246,0.1)',
    },
    {
        id: 'cloud',
        icon: '☁️',
        label: 'Cloud Mesh',
        desc: 'Routed through cloud gateways',
        details: 'Persistent cloud relay for always-on connectivity. Access your mesh from anywhere. Cloud-backed storage + compute routing for heavy workloads.',
        color: '#f59e0b',
        bgColor: 'rgba(245,158,11,0.1)',
    },
    {
        id: 'public',
        icon: '🌍',
        label: 'Public Mesh',
        desc: 'Federated, open peer discovery',
        details: 'Global mesh federation. Discover and connect with public peers. Participate in the world mesh. Sovereign node routing with consent-based data sharing.',
        color: '#8b5cf6',
        bgColor: 'rgba(139,92,246,0.1)',
    },
];

// ── Style helpers ──
const card: React.CSSProperties = {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
};

const btn = (color = '#667eea', small = false): React.CSSProperties => ({
    background: color,
    border: 'none',
    borderRadius: 8,
    color: '#fff',
    cursor: 'pointer',
    fontSize: small ? 11 : 13,
    fontWeight: 600,
    padding: small ? '5px 10px' : '8px 18px',
    marginRight: 6,
});

interface MeshStatusData {
    air_gap?: {
        level?: number;
        label?: string;
    };
    discovery?: {
        running?: boolean;
        local_ip?: string;
    };
    p2p?: {
        running?: boolean;
    };
    peers?: unknown[];
    status?: string;
    uptime?: number;
}

interface MeshSelectorProps {
    user?: Record<string, unknown>;
}

export default function MeshSelector({ user: _user }: MeshSelectorProps) {
    const [activeMode, setActiveMode] = useState('local');
    const [meshStatus, setMeshStatus] = useState<MeshStatusData | null>(null);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    const flash = useCallback((m: string) => {
        setMsg(m);
        setTimeout(() => setMsg(''), 3500);
    }, []);

    // Load mesh status
    const loadStatus = useCallback(async () => {
        try {
            const res = await meshAPI.getStatus();
            setMeshStatus((res.data || res) as unknown as MeshStatusData);
        } catch {
            // Silently fail — mesh may not be initialized
        }
    }, []);

    useEffect(() => {
        loadStatus();
        const interval = setInterval(loadStatus, 15000);
        return () => clearInterval(interval);
    }, [loadStatus]);

    // Switch mesh mode
    const switchMode = async (modeId: string) => {
        setLoading(true);
        try {
            // If switching to a higher isolation level, engage air-gap accordingly
            if (modeId === 'local') {
                await meshAPI.airGapEngage(2, 'Switched to Local Mesh mode');
                flash('🖥️ Local Mesh active — LAN-only mode');
            } else if (modeId === 'personal' && activeMode === 'local') {
                // Coming out of isolation — disengage air-gap
                await meshAPI.airGapDisengage();
                flash('📱 Personal Mesh active — device sync enabled');
            } else if (modeId === 'cloud') {
                // Ensure air-gap is disengaged for cloud routing
                await meshAPI.airGapDisengage();
                flash('☁️ Cloud Mesh active — cloud relay connected');
            } else if (modeId === 'public') {
                await meshAPI.airGapDisengage();
                flash('🌍 Public Mesh active — federation enabled');
            }

            setActiveMode(modeId);
            await loadStatus();
        } catch (e) {
            flash(`⚠️ Mode switch error: ${(e as Error).message}`);
        } finally {
            setLoading(false);
        }
    };

    // Determine current air-gap level from mesh status
    const airGapLevel = meshStatus?.air_gap?.level ?? 0;
    const peerCount = meshStatus?.peers?.length ?? 0;
    const isOnline = meshStatus?.status === 'connected' || meshStatus?.status === 'online';

    return (
        <div style={{ color: '#fff', fontFamily: 'system-ui,sans-serif', maxWidth: 860 }}>
            {/* Header */}
            <div style={{ marginBottom: 20 }}>
                <h2 style={{ margin: 0, fontSize: 22 }}>🔀 Mesh Context Selector</h2>
                <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: 13 }}>
                    Choose your mesh connectivity context
                </p>
            </div>

            {/* Flash message */}
            {msg && (
                <div style={{
                    ...card,
                    background: 'rgba(102,126,234,0.2)',
                    border: '1px solid #667eea',
                    padding: '10px 16px',
                    fontSize: 13,
                }}>
                    {msg}
                </div>
            )}

            {/* Current Status Bar */}
            <div style={{
                ...card,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12,
                marginBottom: 20,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                        width: 10, height: 10, borderRadius: '50%',
                        background: isOnline ? '#10b981' : airGapLevel > 0 ? '#f59e0b' : '#ef4444',
                        display: 'inline-block',
                    }} />
                    <span style={{ fontSize: 13, fontWeight: 600 }}>
                        {isOnline ? 'Connected' : airGapLevel > 0 ? `Air-gap Lv${airGapLevel}` : 'Disconnected'}
                    </span>
                </div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>
                    {peerCount} peer{peerCount !== 1 ? 's' : ''} · Mode: <strong style={{ color: MESH_MODES.find(m => m.id === activeMode)?.color }}>{activeMode}</strong>
                </div>
            </div>

            {/* Mesh Mode Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {MESH_MODES.map((mode) => {
                    const isActive = activeMode === mode.id;
                    return (
                        <div
                            key={mode.id}
                            onClick={() => !isActive && switchMode(mode.id)}
                            style={{
                                ...card,
                                cursor: isActive ? 'default' : 'pointer',
                                border: isActive
                                    ? `2px solid ${mode.color}`
                                    : '1px solid rgba(255,255,255,0.1)',
                                background: isActive
                                    ? mode.bgColor
                                    : 'rgba(255,255,255,0.03)',
                                transition: 'all 0.2s ease',
                                opacity: loading && !isActive ? 0.5 : 1,
                                position: 'relative',
                            }}
                        >
                            {/* Active Badge */}
                            {isActive && (
                                <div style={{
                                    position: 'absolute',
                                    top: -8,
                                    right: -8,
                                    background: mode.color,
                                    borderRadius: '50%',
                                    width: 24,
                                    height: 24,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: 12,
                                    boxShadow: `0 2px 8px ${mode.color}50`,
                                }}>
                                    ✓
                                </div>
                            )}

                            {/* Mode Icon + Label */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                                <span style={{ fontSize: 28 }}>{mode.icon}</span>
                                <div>
                                    <div style={{ fontWeight: 700, fontSize: 15 }}>{mode.label}</div>
                                    <div style={{ fontSize: 11, color: '#94a3b8' }}>{mode.desc}</div>
                                </div>
                            </div>

                            {/* Details */}
                            <p style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
                                {mode.details}
                            </p>

                            {/* Activate Button */}
                            {!isActive && (
                                <button
                                    onClick={(e: React.MouseEvent) => { e.stopPropagation(); switchMode(mode.id); }}
                                    disabled={loading}
                                    style={{
                                        ...btn(mode.color, true),
                                        marginTop: 12,
                                        width: '100%',
                                        textAlign: 'center',
                                    }}
                                >
                                    {loading ? 'Switching...' : `Activate ${mode.label}`}
                                </button>
                            )}

                            {isActive && (
                                <div style={{
                                    marginTop: 12,
                                    fontSize: 11,
                                    color: mode.color,
                                    fontWeight: 600,
                                    textAlign: 'center',
                                    padding: '6px 0',
                                    background: `${mode.color}15`,
                                    borderRadius: 8,
                                }}>
                                    ● Currently Active
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Mesh Status Details */}
            {meshStatus && (
                <div style={{ ...card, marginTop: 16 }}>
                    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 600 }}>
                        📊 MESH STATUS
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, fontSize: 12 }}>
                        <div>
                            <span style={{ color: '#64748b' }}>Discovery:</span>{' '}
                            {meshStatus.discovery?.running ? '🔍 Active' : '⏹️ Stopped'}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>P2P Node:</span>{' '}
                            {meshStatus.p2p?.running ? '🟢 Online' : '🔴 Offline'}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Air-gap:</span>{' '}
                            <span style={{ color: airGapLevel > 0 ? '#f59e0b' : '#10b981' }}>
                                Lv{airGapLevel}
                            </span>
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Local IP:</span>{' '}
                            {meshStatus.discovery?.local_ip || '—'}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Peers:</span> {peerCount}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Uptime:</span>{' '}
                            {meshStatus.uptime ? `${Math.round(meshStatus.uptime / 60)}m` : '—'}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
