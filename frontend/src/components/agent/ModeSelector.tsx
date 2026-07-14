/**
 * ModeSelector — Public/Private Mode Selector
 *
 * Allows users to switch between Public Mode (visible to government
 * oversight — 51%) and Private Mode (visible only to enterprise — 49%).
 * Also supports Agent Mode activation with 5/15/30 day contract durations.
 * Integrates with /api/agent/mode/on, /api/agent/mode/off.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { personalAPI } from '../../api/asimnexus';

interface ModeSelectorProps {
    user?: Record<string, unknown>;
}

type VisibilityMode = 'public' | 'private';

interface AgentStatus {
    active: boolean;
    mode?: string;
    status?: string;
}

export default function ModeSelector({ user: _user }: ModeSelectorProps) {
    const [visibility, setVisibility] = useState<VisibilityMode>('public');
    const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [toggling, setToggling] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const loadStatus = useCallback(async () => {
        try {
            const res = await personalAPI.getAgentStatus();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as AgentStatus;
            setAgentStatus(data);
        } catch {
            setAgentStatus({ active: false, status: 'unknown' });
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadStatus();
        const interval = setInterval(loadStatus, 15000);
        return () => clearInterval(interval);
    }, [loadStatus]);

    const handleToggleAgentMode = async () => {
        setToggling(true);
        setMessage(null);
        try {
            const isActive = agentStatus?.active || false;
            const res = isActive
                ? await personalAPI.agentModeOff()
                : await personalAPI.agentModeOn();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({
                    type: 'success',
                    text: isActive ? 'Agent mode deactivated' : 'Agent mode activated',
                });
                loadStatus();
            } else {
                setMessage({
                    type: 'error',
                    text: String(responseData?.detail || responseData?.message || 'Toggle failed'),
                });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to toggle';
            setMessage({ type: 'error', text: errorMsg });
        }
        setToggling(false);
    };

    const handleVisibilityChange = (mode: VisibilityMode) => {
        setVisibility(mode);
        setMessage({
            type: 'success',
            text: `Switched to ${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode`,
        });
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>🎛️ Loading mode selector...</div>
            </div>
        );
    }

    const isActive = agentStatus?.active || false;

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>🎛️ Mode Selector</h3>
            <p style={styles.subtitle}>Control visibility and agent execution modes</p>

            {/* Message Banner */}
            {message && (
                <div style={{
                    ...styles.messageBanner,
                    background: message.type === 'success' ? '#052e16' : '#7f1d1d',
                    borderColor: message.type === 'success' ? '#16a34a' : '#dc2626',
                    color: message.type === 'success' ? '#86efac' : '#fca5a5',
                } as React.CSSProperties}>
                    {message.text}
                    <button style={styles.messageClose} onClick={() => setMessage(null)}>✕</button>
                </div>
            )}

            {/* Visibility Mode Section */}
            <div style={styles.section}>
                <h4 style={styles.sectionLabel}>Visibility Mode</h4>
                <p style={styles.sectionDesc}>Choose who can see your agent's actions</p>
                <div style={styles.modeGrid}>
                    <div
                        style={{
                            ...styles.modeCard,
                            borderColor: visibility === 'public' ? '#10b981' : '#334155',
                            background: visibility === 'public' ? '#052e16' : '#0f172a',
                        } as React.CSSProperties}
                        onClick={() => handleVisibilityChange('public')}
                    >
                        <span style={styles.modeIcon}>🌐</span>
                        <span style={styles.modeName}>Public Mode</span>
                        <span style={styles.modeDesc}>Visible to government oversight (51%)</span>
                        <div style={styles.modeFeatures}>
                            <span style={styles.featureItem}>✅ Government auditable</span>
                            <span style={styles.featureItem}>✅ Constitutional compliance</span>
                            <span style={styles.featureItem}>✅ Public transparency</span>
                        </div>
                        {visibility === 'public' && (
                            <span style={styles.activeIndicator}>ACTIVE</span>
                        )}
                    </div>
                    <div
                        style={{
                            ...styles.modeCard,
                            borderColor: visibility === 'private' ? '#f59e0b' : '#334155',
                            background: visibility === 'private' ? '#1e293b' : '#0f172a',
                        } as React.CSSProperties}
                        onClick={() => handleVisibilityChange('private')}
                    >
                        <span style={styles.modeIcon}>🔒</span>
                        <span style={styles.modeName}>Private Mode</span>
                        <span style={styles.modeDesc}>Visible only to enterprise (49%)</span>
                        <div style={styles.modeFeatures}>
                            <span style={styles.featureItem}>✅ Enterprise controlled</span>
                            <span style={styles.featureItem}>✅ Commercial privacy</span>
                            <span style={styles.featureItem}>✅ Internal auditing</span>
                        </div>
                        {visibility === 'private' && (
                            <span style={{ ...styles.activeIndicator, background: '#f59e0b', color: '#1e293b' }}>ACTIVE</span>
                        )}
                    </div>
                </div>
            </div>

            {/* Agent Mode Section */}
            <div style={styles.section}>
                <h4 style={styles.sectionLabel}>Agent Mode</h4>
                <p style={styles.sectionDesc}>Enable or disable autonomous agent execution</p>
                <div style={styles.agentModeCard}>
                    <div style={styles.agentModeHeader}>
                        <span style={styles.agentModeIcon}>🤖</span>
                        <div>
                            <span style={styles.agentModeLabel}>Autonomous Agent</span>
                            <span style={{
                                ...styles.agentModeStatus,
                                color: isActive ? '#10b981' : '#64748b',
                            }}>
                                {isActive ? '● Active' : '○ Inactive'}
                            </span>
                        </div>
                    </div>
                    <button
                        style={{
                            ...styles.toggleButton,
                            background: isActive ? '#dc2626' : '#10b981',
                            opacity: toggling ? 0.6 : 1,
                        } as React.CSSProperties}
                        onClick={handleToggleAgentMode}
                        disabled={toggling}
                    >
                        {toggling
                            ? '⏳ Processing...'
                            : isActive
                                ? '🔴 Deactivate'
                                : '🟢 Activate'
                        }
                    </button>
                </div>
            </div>

            {/* Contract Duration Info */}
            <div style={styles.section}>
                <h4 style={styles.sectionLabel}>Contract Durations</h4>
                <p style={styles.sectionDesc}>Available time-bound agent contract tiers</p>
                <div style={styles.durationGrid}>
                    <div style={{ ...styles.durationCard, borderColor: '#3b82f6' }}>
                        <span style={styles.durationDays}>5</span>
                        <span style={styles.durationLabel}>Days</span>
                        <span style={styles.durationDesc}>Trial</span>
                        <span style={styles.durationPrice}>100 credits</span>
                    </div>
                    <div style={{ ...styles.durationCard, borderColor: '#f59e0b' }}>
                        <span style={styles.durationDays}>15</span>
                        <span style={styles.durationLabel}>Days</span>
                        <span style={styles.durationDesc}>Standard</span>
                        <span style={styles.durationPrice}>250 credits</span>
                    </div>
                    <div style={{ ...styles.durationCard, borderColor: '#8b5cf6' }}>
                        <span style={styles.durationDays}>30</span>
                        <span style={styles.durationLabel}>Days</span>
                        <span style={styles.durationDesc}>Extended</span>
                        <span style={styles.durationPrice}>400 credits</span>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>Mode Selector — Public/Private/Agent Modes</span>
                <span style={styles.footerBrand}>AsimNexus 🎛️ Digital Nepal</span>
            </div>
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        padding: '20px',
        color: '#e2e8f0',
        maxHeight: 'calc(100vh - 200px)',
        overflowY: 'auto',
    },
    loadingPulse: {
        textAlign: 'center',
        padding: '40px',
        color: '#94a3b8',
        fontSize: '16px',
        animation: 'pulse 1.5s ease-in-out infinite',
    },
    sectionTitle: {
        margin: '0 0 4px 0',
        fontSize: 18,
        color: '#f1f5f9',
    },
    subtitle: {
        margin: '0 0 16px 0',
        fontSize: 13,
        color: '#64748b',
    },
    messageBanner: {
        border: '1px solid',
        borderRadius: 8,
        padding: '10px 14px',
        fontSize: 13,
        marginBottom: 12,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    messageClose: {
        background: 'none',
        border: 'none',
        color: 'inherit',
        cursor: 'pointer',
        fontSize: 14,
        padding: '0 4px',
    },
    section: {
        marginBottom: 20,
    },
    sectionLabel: {
        margin: '0 0 2px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    sectionDesc: {
        margin: '0 0 12px 0',
        fontSize: 12,
        color: '#64748b',
    },
    modeGrid: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 10,
    },
    modeCard: {
        border: '2px solid',
        borderRadius: 12,
        padding: 16,
        cursor: 'pointer',
        position: 'relative' as const,
        transition: 'all 0.2s ease',
    },
    modeIcon: {
        display: 'block',
        fontSize: 28,
        marginBottom: 8,
    },
    modeName: {
        display: 'block',
        fontSize: 15,
        fontWeight: 700,
        color: '#f1f5f9',
        marginBottom: 4,
    },
    modeDesc: {
        display: 'block',
        fontSize: 11,
        color: '#94a3b8',
        marginBottom: 10,
    },
    modeFeatures: {
        display: 'flex',
        flexDirection: 'column',
        gap: 3,
    },
    featureItem: {
        fontSize: 10,
        color: '#64748b',
    },
    activeIndicator: {
        position: 'absolute' as const,
        top: 8,
        right: 8,
        fontSize: 9,
        fontWeight: 700,
        background: '#10b981',
        color: '#fff',
        padding: '2px 8px',
        borderRadius: 4,
    },
    agentModeCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 10,
        padding: 16,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    agentModeHeader: {
        display: 'flex',
        gap: 12,
        alignItems: 'center',
    },
    agentModeIcon: {
        fontSize: 28,
    },
    agentModeLabel: {
        display: 'block',
        fontSize: 14,
        fontWeight: 600,
        color: '#e2e8f0',
    },
    agentModeStatus: {
        display: 'block',
        fontSize: 11,
    },
    toggleButton: {
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 12,
        fontWeight: 700,
        cursor: 'pointer',
    },
    durationGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 10,
    },
    durationCard: {
        background: '#1e293b',
        border: '1px solid',
        borderRadius: 10,
        padding: 14,
        textAlign: 'center' as const,
    },
    durationDays: {
        display: 'block',
        fontSize: 24,
        fontWeight: 800,
        color: '#f1f5f9',
    },
    durationLabel: {
        display: 'block',
        fontSize: 11,
        color: '#64748b',
        marginBottom: 4,
    },
    durationDesc: {
        display: 'block',
        fontSize: 12,
        color: '#94a3b8',
        marginBottom: 6,
    },
    durationPrice: {
        display: 'block',
        fontSize: 11,
        color: '#f59e0b',
        fontWeight: 600,
    },
    footer: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 10,
        color: '#475569',
        borderTop: '1px solid #1e293b',
        paddingTop: 10,
    },
    footerBrand: {
        color: '#7c3aed',
        fontWeight: 600,
    },
};
