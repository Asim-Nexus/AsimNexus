import React, { useState, useEffect } from 'react';
import { dharmaAPI } from '../../api/asimnexus';

interface DharmaStats {
    total_checked: number;
    passed: number;
    blocked: number;
    warned: number;
    audit_entries: number;
}

interface DharmaEvent {
    action?: string;
    reason?: string;
    ts?: number;
}

interface DharmaVetoPanelProps {
    lastDharmaEvent?: DharmaEvent | null;
}

interface StatBoxProps {
    label: string;
    value: number;
    color: string;
    icon: string;
}

/**
 * DharmaVetoPanel — Real-time Dharma Veto Engine status widget.
 * Shows ethical checks: total checked, passed, blocked, warned.
 * Listens for WS `dharma_veto` events to update live.
 */
export default function DharmaVetoPanel({ lastDharmaEvent }: DharmaVetoPanelProps) {
    const [stats, setStats] = useState<DharmaStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [pulse, setPulse] = useState(false);

    useEffect(() => {
        loadStats();
        // Refresh every 30s
        const interval = setInterval(loadStats, 30000);
        return () => clearInterval(interval);
    }, []);

    // Animate when a veto event comes via WebSocket
    useEffect(() => {
        if (lastDharmaEvent) {
            setPulse(true);
            loadStats(); // Refresh counts
            setTimeout(() => setPulse(false), 1500);
        }
    }, [lastDharmaEvent]);

    async function loadStats() {
        try {
            const res = await dharmaAPI.getStatus();
            const data = (res?.data || res) as unknown as DharmaStats;
            setStats(data);
        } catch (e) {
            // Use fallback data
            setStats({
                total_checked: 0,
                passed: 0,
                blocked: 0,
                warned: 0,
                audit_entries: 0,
            });
        }
        setLoading(false);
    }

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>☯ Loading Dharma Engine...</div>
            </div>
        );
    }

    const passRate = stats && stats.total_checked > 0
        ? ((stats.passed / stats.total_checked) * 100).toFixed(1)
        : '100.0';

    return (
        <div style={{
            ...styles.container,
            ...(pulse ? styles.pulseAnimation : {}),
        }}>
            {/* Header */}
            <div style={styles.header}>
                <div style={styles.titleRow}>
                    <span style={styles.icon}>☯</span>
                    <h3 style={styles.title}>Dharma Veto Engine</h3>
                </div>
                <div style={{
                    ...styles.statusBadge,
                    background: stats && stats.blocked > 0 ? '#7f1d1d' : '#052e16',
                    borderColor: stats && stats.blocked > 0 ? '#dc2626' : '#16a34a',
                }}>
                    {stats && stats.blocked > 0 ? '⚠️ Active Blocks' : '✅ All Clear'}
                </div>
            </div>

            {/* Ethical Pass Rate Bar */}
            <div style={styles.passRateSection}>
                <div style={styles.passRateLabel}>
                    <span>Ethical Pass Rate</span>
                    <span style={{ color: '#10b981', fontWeight: 700 }}>{passRate}%</span>
                </div>
                <div style={styles.progressBarBg}>
                    <div style={{
                        ...styles.progressBarFill,
                        width: `${passRate}%`,
                        background: parseFloat(passRate) > 95
                            ? 'linear-gradient(90deg, #10b981, #34d399)'
                            : parseFloat(passRate) > 80
                                ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                                : 'linear-gradient(90deg, #ef4444, #f87171)',
                    }} />
                </div>
            </div>

            {/* Stats Grid */}
            <div style={styles.statsGrid}>
                <StatBox label="Total Checked" value={stats?.total_checked || 0} color="#3b82f6" icon="🔍" />
                <StatBox label="Passed" value={stats?.passed || 0} color="#10b981" icon="✅" />
                <StatBox label="Blocked" value={stats?.blocked || 0} color="#ef4444" icon="🚫" />
                <StatBox label="Warned" value={stats?.warned || 0} color="#f59e0b" icon="⚠️" />
            </div>

            {/* Latest Veto Event */}
            {lastDharmaEvent && (
                <div style={styles.latestEvent}>
                    <span style={styles.eventLabel}>Latest Event:</span>
                    <span style={styles.eventText}>
                        {lastDharmaEvent.action || lastDharmaEvent.reason || 'Dharma check triggered'}
                    </span>
                    <span style={styles.eventTime}>
                        {new Date(lastDharmaEvent.ts || Date.now()).toLocaleTimeString()}
                    </span>
                </div>
            )}

            {/* Footer */}
            <div style={styles.footer}>
                <span>Audit Entries: {stats?.audit_entries || 0}</span>
                <span style={styles.footerBrand}>AsimNexus ☯ Constitutional AI</span>
            </div>
        </div>
    );
}

function StatBox({ label, value, color, icon }: StatBoxProps) {
    return (
        <div style={styles.statBox}>
            <div style={{ fontSize: 18, marginBottom: 4 }}>{icon}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color }}>{value.toLocaleString()}</div>
            <div style={styles.statLabel}>{label}</div>
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
        border: '1px solid #312e81',
        borderRadius: 12,
        padding: 16,
        color: '#f8fafc',
        fontFamily: 'Inter, sans-serif',
        transition: 'all 0.3s ease',
    },
    pulseAnimation: {
        boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)',
    },
    loadingPulse: {
        textAlign: 'center',
        color: '#a78bfa',
        fontSize: 14,
        padding: 20,
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 14,
    },
    titleRow: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
    },
    icon: {
        fontSize: 22,
    },
    title: {
        margin: 0,
        fontSize: 15,
        fontWeight: 700,
        color: '#e2e8f0',
    },
    statusBadge: {
        fontSize: 11,
        fontWeight: 600,
        padding: '4px 10px',
        borderRadius: 6,
        border: '1px solid',
    },
    passRateSection: {
        marginBottom: 14,
    },
    passRateLabel: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 12,
        color: '#94a3b8',
        marginBottom: 6,
    },
    progressBarBg: {
        height: 8,
        background: '#1e293b',
        borderRadius: 4,
        overflow: 'hidden',
    },
    progressBarFill: {
        height: '100%',
        borderRadius: 4,
        transition: 'width 0.5s ease',
    },
    statsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 8,
        marginBottom: 14,
    },
    statBox: {
        background: '#0f172a',
        borderRadius: 8,
        padding: '10px 8px',
        textAlign: 'center',
        border: '1px solid #1e293b',
    },
    statLabel: {
        fontSize: 10,
        color: '#64748b',
        marginTop: 2,
    },
    latestEvent: {
        background: '#1e1b4b',
        borderRadius: 6,
        padding: '8px 10px',
        marginBottom: 12,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        fontSize: 11,
        border: '1px solid #312e81',
    },
    eventLabel: {
        color: '#a78bfa',
        fontWeight: 600,
        whiteSpace: 'nowrap',
    },
    eventText: {
        color: '#e2e8f0',
        flex: 1,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
    },
    eventTime: {
        color: '#64748b',
        whiteSpace: 'nowrap',
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
