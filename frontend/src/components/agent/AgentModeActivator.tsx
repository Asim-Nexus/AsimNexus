/**
 * AgentModeActivator — Toggle Agent Mode On/Off
 *
 * Allows users to activate or deactivate autonomous agent mode.
 * When active, the system can execute tasks autonomously within
 * the bounds of the user's contract and scope restrictions.
 * Integrates with /api/agent/mode/on and /api/agent/mode/off.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { personalAPI } from '../../api/asimnexus';

interface AgentModeActivatorProps {
    user?: Record<string, unknown>;
}

interface AgentStatus {
    active: boolean;
    mode?: string;
    status?: string;
    started_at?: string;
    uptime_seconds?: number;
    tasks_completed?: number;
}

export default function AgentModeActivator({ user: _user }: AgentModeActivatorProps) {
    const [status, setStatus] = useState<AgentStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [toggling, setToggling] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const loadStatus = useCallback(async () => {
        try {
            const res = await personalAPI.getAgentStatus();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as AgentStatus;
            setStatus(data);
        } catch {
            setStatus({ active: false, status: 'unknown' });
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadStatus();
        const interval = setInterval(loadStatus, 15000);
        return () => clearInterval(interval);
    }, [loadStatus]);

    const handleToggle = async () => {
        setToggling(true);
        setMessage(null);
        try {
            const isActive = status?.active || false;
            const res = isActive
                ? await personalAPI.agentModeOff()
                : await personalAPI.agentModeOn();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({
                    type: 'success',
                    text: isActive ? 'Agent mode deactivated ✓' : 'Agent mode activated ✓',
                });
                loadStatus();
            } else {
                setMessage({
                    type: 'error',
                    text: String(responseData?.detail || responseData?.message || 'Toggle failed'),
                });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to toggle agent mode';
            setMessage({ type: 'error', text: errorMsg });
        }
        setToggling(false);
    };

    const formatUptime = (seconds?: number): string => {
        if (!seconds) return '—';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}h ${m}m ${s}s`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>🤖 Loading agent status...</div>
            </div>
        );
    }

    const isActive = status?.active || false;

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>🤖 Agent Mode</h3>
            <p style={styles.subtitle}>Control autonomous agent execution</p>

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

            {/* Status Card */}
            <div style={{
                ...styles.statusCard,
                borderColor: isActive ? '#10b981' : '#64748b',
                background: isActive ? '#052e16' : '#1e293b',
            } as React.CSSProperties}>
                <div style={styles.statusHeader}>
                    <span style={{
                        ...styles.statusDot,
                        background: isActive ? '#10b981' : '#64748b',
                        boxShadow: isActive ? '0 0 12px rgba(16, 185, 129, 0.6)' : 'none',
                    } as React.CSSProperties} />
                    <span style={{
                        ...styles.statusLabel,
                        color: isActive ? '#86efac' : '#94a3b8',
                    }}>
                        {isActive ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                </div>

                {/* Toggle Button */}
                <button
                    style={{
                        ...styles.toggleButton,
                        background: isActive ? '#dc2626' : '#10b981',
                        opacity: toggling ? 0.6 : 1,
                    } as React.CSSProperties}
                    onClick={handleToggle}
                    disabled={toggling}
                >
                    {toggling
                        ? '⏳ Processing...'
                        : isActive
                            ? '🔴 Deactivate Agent Mode'
                            : '🟢 Activate Agent Mode'
                    }
                </button>

                {/* Status Details */}
                {isActive && status && (
                    <div style={styles.detailsGrid}>
                        <div style={styles.detailItem}>
                            <span style={styles.detailLabel}>Mode</span>
                            <span style={styles.detailValue}>{status.mode || 'autonomous'}</span>
                        </div>
                        <div style={styles.detailItem}>
                            <span style={styles.detailLabel}>Uptime</span>
                            <span style={styles.detailValue}>{formatUptime(status.uptime_seconds)}</span>
                        </div>
                        <div style={styles.detailItem}>
                            <span style={styles.detailLabel}>Tasks Done</span>
                            <span style={styles.detailValue}>{status.tasks_completed || 0}</span>
                        </div>
                        {status.started_at && (
                            <div style={styles.detailItem}>
                                <span style={styles.detailLabel}>Started</span>
                                <span style={styles.detailValue}>
                                    {new Date(status.started_at).toLocaleString()}
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Info Card */}
            <div style={styles.infoCard}>
                <h4 style={styles.infoTitle}>About Agent Mode</h4>
                <ul style={styles.infoList}>
                    <li>Agent mode allows autonomous task execution</li>
                    <li>All actions are bound by time-limited contracts (5/15/30 days)</li>
                    <li>Scope restrictions prevent unauthorized actions</li>
                    <li>Public mode: visible to government oversight (51%)</li>
                    <li>Private mode: visible only to enterprise (49%)</li>
                    <li>All actions are audited and immutable</li>
                </ul>
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>Agent Mode — Time-bound Autonomous Execution</span>
                <span style={styles.footerBrand}>AsimNexus 🤖 Digital Nepal</span>
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
    statusCard: {
        border: '1px solid',
        borderRadius: 12,
        padding: 20,
        marginBottom: 16,
        textAlign: 'center' as const,
    },
    statusHeader: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 10,
        marginBottom: 16,
    },
    statusDot: {
        width: 14,
        height: 14,
        borderRadius: '50%',
        display: 'inline-block',
    },
    statusLabel: {
        fontSize: 20,
        fontWeight: 800,
        letterSpacing: 2,
    },
    toggleButton: {
        color: '#fff',
        border: 'none',
        borderRadius: 8,
        padding: '10px 24px',
        fontSize: 14,
        fontWeight: 700,
        cursor: 'pointer',
        marginBottom: 16,
    },
    detailsGrid: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 8,
        textAlign: 'left' as const,
    },
    detailItem: {
        background: '#0f172a',
        borderRadius: 6,
        padding: '8px 12px',
    },
    detailLabel: {
        display: 'block',
        fontSize: 10,
        color: '#64748b',
        marginBottom: 2,
    },
    detailValue: {
        display: 'block',
        fontSize: 13,
        color: '#e2e8f0',
        fontWeight: 600,
    },
    infoCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 10,
        padding: 16,
        marginBottom: 16,
    },
    infoTitle: {
        margin: '0 0 10px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    infoList: {
        margin: 0,
        paddingLeft: 20,
        fontSize: 12,
        color: '#94a3b8',
        lineHeight: 1.8,
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
