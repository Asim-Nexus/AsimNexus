/**
 * ARVRViewport — Immersive AR/VR Interface Panel
 *
 * Provides a spatial scene viewer, mode switching (AR/VR/MR),
 * element management, gesture registration, and haptic feedback triggers.
 *
 * Backend: routes/arvr.py (9 endpoints)
 * API: arvrAPI (frontend/src/api/asimnexus.ts)
 */

import { useState, useEffect, useCallback } from 'react';
import type { AxiosResponse } from 'axios';
import type { ApiResponse } from '../../types';
import { arvrAPI } from '../../api';

// ── Types ──────────────────────────────────────────────────────────

interface SpatialElement {
    id: string;
    position: { x: number; y: number; z: number };
    content: string;
    rotation?: { x: number; y: number; z: number };
    scale?: { x: number; y: number; z: number };
    interactive?: boolean;
}

interface GestureRecord {
    id: string;
    gesture_type: string;
    target_element?: string;
    timestamp: string;
    parameters?: Record<string, unknown>;
}

interface ARVRStatus {
    mode: 'ar' | 'vr' | 'mr';
    active: boolean;
    elements_count: number;
    gestures_count: number;
    session_id?: string;
}

type TabId = 'scene' | 'elements' | 'gestures' | 'haptic';

// ── Styles ─────────────────────────────────────────────────────────

const s = {
    container: {
        flex: 1,
        overflow: 'auto',
        padding: 16,
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 16,
    },
    header: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        flexWrap: 'wrap' as const,
    },
    title: {
        fontSize: '1.2rem',
        fontWeight: 700,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
    },
    modeBadge: (mode: string) => ({
        padding: '4px 14px',
        borderRadius: 20,
        fontSize: '0.75rem',
        fontWeight: 600,
        textTransform: 'uppercase' as const,
        letterSpacing: 1,
        background:
            mode === 'ar' ? 'rgba(16,185,129,0.2)' :
                mode === 'vr' ? 'rgba(102,126,234,0.2)' :
                    'rgba(245,158,11,0.2)',
        color:
            mode === 'ar' ? '#10b981' :
                mode === 'vr' ? '#667eea' :
                    '#f59e0b',
        border: `1px solid ${mode === 'ar' ? 'rgba(16,185,129,0.3)' :
            mode === 'vr' ? 'rgba(102,126,234,0.3)' :
                'rgba(245,158,11,0.3)'
            }`,
    }),
    tabs: {
        display: 'flex',
        gap: 4,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        paddingBottom: 8,
    },
    tab: (active: boolean) => ({
        padding: '6px 16px',
        borderRadius: '8px 8px 0 0',
        fontSize: '0.78rem',
        cursor: 'pointer',
        background: active ? 'rgba(102,126,234,0.15)' : 'transparent',
        color: active ? '#667eea' : 'rgba(255,255,255,0.5)',
        border: 'none',
        borderBottom: active ? '2px solid #667eea' : '2px solid transparent',
        transition: 'all 0.15s',
    }),
    card: {
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 12,
        padding: 16,
        border: '1px solid rgba(255,255,255,0.06)',
    },
    cardTitle: {
        fontSize: '0.8rem',
        fontWeight: 600,
        opacity: 0.7,
        marginBottom: 12,
        textTransform: 'uppercase' as const,
        letterSpacing: 0.5,
    },
    row: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 0',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        fontSize: '0.82rem',
    },
    input: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        outline: 'none',
        width: '100%',
        boxSizing: 'border-box' as const,
    },
    select: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        outline: 'none',
    },
    btn: (color: string = '#667eea') => ({
        padding: '8px 16px',
        borderRadius: 8,
        border: 'none',
        background: color,
        color: '#fff',
        fontSize: '0.78rem',
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'opacity 0.15s',
    }),
    btnSmall: {
        padding: '4px 10px',
        borderRadius: 6,
        border: 'none',
        fontSize: '0.7rem',
        fontWeight: 600,
        cursor: 'pointer',
    },
    grid2: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 12,
    },
    statBox: {
        background: 'rgba(255,255,255,0.03)',
        borderRadius: 10,
        padding: '12px 16px',
        textAlign: 'center' as const,
    },
    statValue: {
        fontSize: '1.4rem',
        fontWeight: 700,
        color: '#667eea',
    },
    statLabel: {
        fontSize: '0.68rem',
        opacity: 0.5,
        marginTop: 4,
        textTransform: 'uppercase' as const,
        letterSpacing: 0.5,
    },
    empty: {
        textAlign: 'center' as const,
        padding: 24,
        opacity: 0.4,
        fontSize: '0.85rem',
    },
    label: {
        fontSize: '0.72rem',
        opacity: 0.6,
        marginBottom: 4,
    },
    flexRow: {
        display: 'flex',
        gap: 8,
        alignItems: 'center',
        flexWrap: 'wrap' as const,
    },
    coordInput: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 6,
        padding: '6px 8px',
        color: '#fff',
        fontSize: '0.78rem',
        outline: 'none',
        width: 60,
    },
};

// ── Component ──────────────────────────────────────────────────────

interface ARVRViewportProps {
    user?: Record<string, unknown>;
}

export default function ARVRViewport({ user: _user }: ARVRViewportProps) {
    const [status, setStatus] = useState<ARVRStatus | null>(null);
    const [scene, setScene] = useState<SpatialElement[]>([]);
    const [gestures, setGestures] = useState<GestureRecord[]>([]);
    const [activeTab, setActiveTab] = useState<TabId>('scene');
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // ── Form state ──
    const [mode, setMode] = useState<'ar' | 'vr' | 'mr'>('ar');
    const [elementContent, setElementContent] = useState<string>('');
    const [elementX, setElementX] = useState<number>(0);
    const [elementY, setElementY] = useState<number>(0);
    const [elementZ, setElementZ] = useState<number>(0);
    const [gestureType, setGestureType] = useState<string>('tap');
    const [hapticIntensity, setHapticIntensity] = useState<number>(0.5);
    const [hapticDuration, setHapticDuration] = useState<number>(200);

    // ── Fetch status ──
    const fetchStatus = useCallback(async () => {
        try {
            const res = await arvrAPI.getStatus() as AxiosResponse<ApiResponse>;
            const data = (res?.data?.data || res?.data || {}) as Record<string, unknown>;
            if (data.status === 'ok' || data.success) {
                setStatus({
                    mode: (data.mode as 'ar' | 'vr' | 'mr') || 'ar',
                    active: !!data.active,
                    elements_count: (data.elements_count as number) || 0,
                    gestures_count: (data.gestures_count as number) || 0,
                    session_id: data.session_id as string,
                });
            }
        } catch {
            // Backend may not be available
        }
    }, []);

    // ── Fetch scene ──
    const fetchScene = useCallback(async () => {
        try {
            const res = await arvrAPI.getScene() as AxiosResponse<ApiResponse>;
            const data = (res?.data?.data || res?.data || {}) as Record<string, unknown>;
            const elements = (data.elements || data.scene || []) as SpatialElement[];
            setScene(Array.isArray(elements) ? elements : []);
        } catch {
            // Silent
        }
    }, []);

    // ── Fetch gestures ──
    const fetchGestures = useCallback(async () => {
        try {
            const res = await arvrAPI.getGestureHistory(20) as AxiosResponse<ApiResponse>;
            const data = (res?.data?.data || res?.data || {}) as Record<string, unknown>;
            const list = (data.gestures || data.history || []) as GestureRecord[];
            setGestures(Array.isArray(list) ? list : []);
        } catch {
            // Silent
        }
    }, []);

    // ── Initial load ──
    useEffect(() => {
        const init = async () => {
            setLoading(true);
            setError(null);
            try {
                await Promise.all([fetchStatus(), fetchScene(), fetchGestures()]);
            } catch (err) {
                setError('Failed to connect to AR/VR backend');
            } finally {
                setLoading(false);
            }
        };
        init();
    }, [fetchStatus, fetchScene, fetchGestures]);

    // ── Set mode ──
    const handleSetMode = async () => {
        try {
            setError(null);
            await arvrAPI.setMode(mode);
            await fetchStatus();
        } catch {
            setError('Failed to set AR/VR mode');
        }
    };

    // ── Create element ──
    const handleCreateElement = async () => {
        if (!elementContent.trim()) return;
        try {
            setError(null);
            await arvrAPI.createElement({
                position: { x: elementX, y: elementY, z: elementZ },
                content: elementContent,
            });
            setElementContent('');
            await fetchScene();
            await fetchStatus();
        } catch {
            setError('Failed to create spatial element');
        }
    };

    // ── Remove element ──
    const handleRemoveElement = async (id: string) => {
        try {
            setError(null);
            await arvrAPI.removeElement(id);
            await fetchScene();
            await fetchStatus();
        } catch {
            setError('Failed to remove element');
        }
    };

    // ── Register gesture ──
    const handleRegisterGesture = async () => {
        try {
            setError(null);
            await arvrAPI.registerGesture({ gesture_type: gestureType });
            await fetchGestures();
            await fetchStatus();
        } catch {
            setError('Failed to register gesture');
        }
    };

    // ── Trigger haptic ──
    const handleTriggerHaptic = async () => {
        try {
            setError(null);
            await arvrAPI.triggerHaptic({
                intensity: hapticIntensity,
                duration_ms: hapticDuration,
            });
        } catch {
            setError('Failed to trigger haptic feedback');
        }
    };

    // ── Render ──

    if (loading) {
        return (
            <div style={s.container}>
                <div style={{ textAlign: 'center', padding: 48, opacity: 0.5 }}>
                    <div style={{ fontSize: '2rem', marginBottom: 8 }}>🕶️</div>
                    <div>Loading AR/VR Interface...</div>
                </div>
            </div>
        );
    }

    return (
        <div style={s.container}>
            {/* Header */}
            <div style={s.header}>
                <div style={s.title}>
                    <span>🕶️</span> AR/VR Viewport
                    {status && <span style={s.modeBadge(status.mode)}>{status.mode.toUpperCase()}</span>}
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <select
                        style={s.select}
                        value={mode}
                        onChange={e => setMode(e.target.value as 'ar' | 'vr' | 'mr')}
                    >
                        <option value="ar">AR — Augmented Reality</option>
                        <option value="vr">VR — Virtual Reality</option>
                        <option value="mr">MR — Mixed Reality</option>
                    </select>
                    <button style={s.btn()} onClick={handleSetMode}>
                        Apply Mode
                    </button>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '8px 12px', fontSize: '0.8rem', color: '#ef4444' }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Status Stats */}
            {status && (
                <div style={s.grid2}>
                    <div style={s.statBox}>
                        <div style={s.statValue}>{status.elements_count}</div>
                        <div style={s.statLabel}>Spatial Elements</div>
                    </div>
                    <div style={s.statBox}>
                        <div style={s.statValue}>{status.gestures_count}</div>
                        <div style={s.statLabel}>Registered Gestures</div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div style={s.tabs}>
                {(['scene', 'elements', 'gestures', 'haptic'] as TabId[]).map(tab => (
                    <button
                        key={tab}
                        style={s.tab(activeTab === tab)}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab === 'scene' && '🌌 '}
                        {tab === 'elements' && '🧊 '}
                        {tab === 'gestures' && '✋ '}
                        {tab === 'haptic' && '📳 '}
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            {/* ── Tab: Scene ── */}
            {activeTab === 'scene' && (
                <div style={s.card}>
                    <div style={s.cardTitle}>🌌 Spatial Scene</div>
                    {scene.length === 0 ? (
                        <div style={s.empty}>No spatial elements in the scene. Create one in the Elements tab.</div>
                    ) : (
                        scene.map(el => (
                            <div key={el.id} style={s.row}>
                                <span style={{ opacity: 0.6, fontSize: '0.7rem', fontFamily: 'monospace' }}>
                                    {el.id.slice(0, 8)}…
                                </span>
                                <span style={{ flex: 1 }}>{el.content}</span>
                                <span style={{ opacity: 0.5, fontSize: '0.72rem' }}>
                                    ({el.position.x}, {el.position.y}, {el.position.z})
                                </span>
                                {el.interactive && <span style={{ fontSize: '0.7rem' }}>🖱️</span>}
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* ── Tab: Elements ── */}
            {activeTab === 'elements' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {/* Create Element */}
                    <div style={s.card}>
                        <div style={s.cardTitle}>➕ Create Spatial Element</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            <div>
                                <div style={s.label}>Content / Label</div>
                                <input
                                    style={s.input}
                                    placeholder="e.g., Data Dashboard, 3D Model, Notification"
                                    value={elementContent}
                                    onChange={e => setElementContent(e.target.value)}
                                />
                            </div>
                            <div>
                                <div style={s.label}>Position (X, Y, Z)</div>
                                <div style={s.flexRow}>
                                    <label style={{ fontSize: '0.7rem', opacity: 0.5 }}>X:</label>
                                    <input
                                        type="number"
                                        style={s.coordInput}
                                        value={elementX}
                                        onChange={e => setElementX(Number(e.target.value))}
                                    />
                                    <label style={{ fontSize: '0.7rem', opacity: 0.5 }}>Y:</label>
                                    <input
                                        type="number"
                                        style={s.coordInput}
                                        value={elementY}
                                        onChange={e => setElementY(Number(e.target.value))}
                                    />
                                    <label style={{ fontSize: '0.7rem', opacity: 0.5 }}>Z:</label>
                                    <input
                                        type="number"
                                        style={s.coordInput}
                                        value={elementZ}
                                        onChange={e => setElementZ(Number(e.target.value))}
                                    />
                                </div>
                            </div>
                            <button style={s.btn('#10b981')} onClick={handleCreateElement}>
                                Create Element
                            </button>
                        </div>
                    </div>

                    {/* Existing Elements */}
                    <div style={s.card}>
                        <div style={s.cardTitle}>📋 Existing Elements ({scene.length})</div>
                        {scene.length === 0 ? (
                            <div style={s.empty}>No elements yet</div>
                        ) : (
                            scene.map(el => (
                                <div key={el.id} style={s.row}>
                                    <span style={{ flex: 1 }}>
                                        <strong>{el.content}</strong>
                                        <span style={{ opacity: 0.4, marginLeft: 8, fontSize: '0.72rem' }}>
                                            ({el.position.x}, {el.position.y}, {el.position.z})
                                        </span>
                                    </span>
                                    <button
                                        style={{ ...s.btnSmall, background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}
                                        onClick={() => handleRemoveElement(el.id)}
                                    >
                                        ✕ Remove
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* ── Tab: Gestures ── */}
            {activeTab === 'gestures' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={s.card}>
                        <div style={s.cardTitle}>✋ Register Gesture</div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <select
                                style={s.select}
                                value={gestureType}
                                onChange={e => setGestureType(e.target.value)}
                            >
                                <option value="tap">Tap</option>
                                <option value="swipe_left">Swipe Left</option>
                                <option value="swipe_right">Swipe Right</option>
                                <option value="swipe_up">Swipe Up</option>
                                <option value="swipe_down">Swipe Down</option>
                                <option value="pinch">Pinch</option>
                                <option value="rotate">Rotate</option>
                                <option value="dwell">Dwell / Hold</option>
                            </select>
                            <button style={s.btn('#8b5cf6')} onClick={handleRegisterGesture}>
                                Register Gesture
                            </button>
                        </div>
                    </div>

                    <div style={s.card}>
                        <div style={s.cardTitle}>📜 Gesture History ({gestures.length})</div>
                        {gestures.length === 0 ? (
                            <div style={s.empty}>No gestures registered yet</div>
                        ) : (
                            gestures.map(g => (
                                <div key={g.id} style={s.row}>
                                    <span style={{
                                        padding: '2px 8px',
                                        borderRadius: 4,
                                        fontSize: '0.7rem',
                                        background: 'rgba(139,92,246,0.15)',
                                        color: '#8b5cf6',
                                    }}>
                                        {g.gesture_type}
                                    </span>
                                    <span style={{ opacity: 0.4, fontSize: '0.72rem' }}>
                                        {g.timestamp ? new Date(g.timestamp).toLocaleTimeString() : ''}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* ── Tab: Haptic ── */}
            {activeTab === 'haptic' && (
                <div style={s.card}>
                    <div style={s.cardTitle}>📳 Haptic Feedback</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                            <div style={s.label}>
                                Intensity: {hapticIntensity.toFixed(2)}
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.05"
                                value={hapticIntensity}
                                onChange={e => setHapticIntensity(Number(e.target.value))}
                                style={{ width: '100%' }}
                            />
                        </div>
                        <div>
                            <div style={s.label}>
                                Duration: {hapticDuration}ms
                            </div>
                            <input
                                type="range"
                                min="50"
                                max="1000"
                                step="50"
                                value={hapticDuration}
                                onChange={e => setHapticDuration(Number(e.target.value))}
                                style={{ width: '100%' }}
                            />
                        </div>
                        <button style={s.btn('#f59e0b')} onClick={handleTriggerHaptic}>
                            📳 Trigger Haptic
                        </button>
                    </div>
                </div>
            )}

            {/* Refresh */}
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                <button
                    style={{ ...s.btn(), background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.7)' }}
                    onClick={() => { fetchStatus(); fetchScene(); fetchGestures(); }}
                >
                    🔄 Refresh All
                </button>
            </div>
        </div>
    );
}
