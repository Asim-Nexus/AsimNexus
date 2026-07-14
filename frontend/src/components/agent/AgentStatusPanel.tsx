/**
 * AgentStatusPanel — Detailed Agent Status Display
 *
 * Shows comprehensive agent status including active contracts,
 * task queue, resource usage, and agent health metrics.
 * Integrates with /api/agent/status and /api/personal/contracts.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { personalAPI } from '../../api/asimnexus';

interface AgentStatusPanelProps {
    user?: Record<string, unknown>;
}

interface Contract {
    contract_id: string;
    agent_name?: string;
    duration_days?: number;
    status?: string;
    scope?: string;
    created_at?: string;
    expires_at?: string;
}

interface AgentStatus {
    active: boolean;
    mode?: string;
    status?: string;
    started_at?: string;
    uptime_seconds?: number;
    tasks_completed?: number;
    tasks_pending?: number;
    memory_usage?: number;
    cpu_usage?: number;
}

export default function AgentStatusPanel({ user: _user }: AgentStatusPanelProps) {
    const [status, setStatus] = useState<AgentStatus | null>(null);
    const [contracts, setContracts] = useState<Contract[]>([]);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            const [statusRes, contractsRes] = await Promise.allSettled([
                personalAPI.getAgentStatus(),
                personalAPI.getContracts(),
            ]);

            if (statusRes.status === 'fulfilled') {
                const sd = (statusRes.value?.data || statusRes.value) as unknown as Record<string, unknown>;
                setStatus((sd?.data || sd) as AgentStatus);
            }

            if (contractsRes.status === 'fulfilled') {
                const cd = (contractsRes.value?.data || contractsRes.value) as unknown as Record<string, unknown>;
                const data = (cd?.data || cd) as Record<string, unknown>;
                setContracts((data?.contracts || []) as Contract[]);
            }
        } catch {
            setStatus({ active: false, status: 'unknown' });
            setContracts([]);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 20000);
        return () => clearInterval(interval);
    }, [loadData]);

    const formatUptime = (seconds?: number): string => {
        if (!seconds) return '—';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        if (h > 0) return `${h}h ${m}m`;
        return `${m}m`;
    };

    const getStatusColor = (s?: string) => {
        switch (s?.toLowerCase()) {
            case 'active': return '#10b981';
            case 'pending': return '#f59e0b';
            case 'expired': return '#ef4444';
            case 'completed': return '#3b82f6';
            default: return '#64748b';
        }
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>📊 Loading agent status...</div>
            </div>
        );
    }

    const isActive = status?.active || false;

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>📊 Agent Status</h3>
            <p style={styles.subtitle}>Comprehensive agent health and activity overview</p>

            {/* Health Metrics Grid */}
            <div style={styles.metricsGrid}>
                <div style={{
                    ...styles.metricCard,
                    borderColor: isActive ? '#10b981' : '#64748b',
                } as React.CSSProperties}>
                    <span style={styles.metricIcon}>🤖</span>
                    <span style={styles.metricValue}>{isActive ? 'Active' : 'Inactive'}</span>
                    <span style={styles.metricLabel}>Agent State</span>
                </div>
                <div style={styles.metricCard}>
                    <span style={styles.metricIcon}>⏱️</span>
                    <span style={styles.metricValue}>{formatUptime(status?.uptime_seconds)}</span>
                    <span style={styles.metricLabel}>Uptime</span>
                </div>
                <div style={styles.metricCard}>
                    <span style={styles.metricIcon}>✅</span>
                    <span style={styles.metricValue}>{status?.tasks_completed || 0}</span>
                    <span style={styles.metricLabel}>Completed</span>
                </div>
                <div style={styles.metricCard}>
                    <span style={styles.metricIcon}>⏳</span>
                    <span style={styles.metricValue}>{status?.tasks_pending || 0}</span>
                    <span style={styles.metricLabel}>Pending</span>
                </div>
                <div style={styles.metricCard}>
                    <span style={styles.metricIcon}>💾</span>
                    <span style={styles.metricValue}>{status?.memory_usage || '—'}%</span>
                    <span style={styles.metricLabel}>Memory</span>
                </div>
                <div style={styles.metricCard}>
                    <span style={styles.metricIcon}>⚡</span>
                    <span style={styles.metricValue}>{status?.cpu_usage || '—'}%</span>
                    <span style={styles.metricLabel}>CPU</span>
                </div>
            </div>

            {/* Active Contracts */}
            <h4 style={styles.listTitle}>
                Active Contracts ({contracts.filter(c => c.status === 'active').length})
            </h4>
            <div style={styles.contractList}>
                {contracts.length === 0 ? (
                    <div style={styles.emptyState}>No contracts found</div>
                ) : (
                    contracts.map((contract) => (
                        <div key={contract.contract_id} style={{
                            ...styles.contractCard,
                            borderLeftColor: getStatusColor(contract.status),
                        } as React.CSSProperties}>
                            <div style={styles.contractHeader}>
                                <span style={styles.contractName}>
                                    {contract.agent_name || contract.contract_id.slice(0, 12)}
                                </span>
                                <span style={{
                                    ...styles.contractStatus,
                                    color: getStatusColor(contract.status),
                                    borderColor: getStatusColor(contract.status),
                                } as React.CSSProperties}>
                                    {contract.status?.toUpperCase() || 'UNKNOWN'}
                                </span>
                            </div>
                            <div style={styles.contractMeta}>
                                {contract.duration_days && (
                                    <span>{contract.duration_days} days</span>
                                )}
                                {contract.scope && (
                                    <span>Scope: {contract.scope}</span>
                                )}
                            </div>
                            <div style={styles.contractDates}>
                                {contract.created_at && (
                                    <span>Created: {new Date(contract.created_at).toLocaleDateString()}</span>
                                )}
                                {contract.expires_at && (
                                    <span>Expires: {new Date(contract.expires_at).toLocaleDateString()}</span>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>Agent Status — Real-time Monitoring</span>
                <span style={styles.footerBrand}>AsimNexus 📊 Digital Nepal</span>
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
    metricsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 8,
        marginBottom: 16,
    },
    metricCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 10,
        padding: 14,
        textAlign: 'center' as const,
    },
    metricIcon: {
        display: 'block',
        fontSize: 20,
        marginBottom: 4,
    },
    metricValue: {
        display: 'block',
        fontSize: 16,
        fontWeight: 700,
        color: '#f1f5f9',
    },
    metricLabel: {
        display: 'block',
        fontSize: 10,
        color: '#64748b',
        marginTop: 2,
    },
    listTitle: {
        margin: '16px 0 10px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    contractList: {
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        marginBottom: 16,
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#64748b',
        fontSize: 14,
    },
    contractCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderLeft: '4px solid',
        borderRadius: 8,
        padding: 12,
    },
    contractHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
    },
    contractName: {
        fontSize: 13,
        fontWeight: 600,
        color: '#e2e8f0',
    },
    contractStatus: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid',
    },
    contractMeta: {
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#64748b',
        marginBottom: 4,
    },
    contractDates: {
        display: 'flex',
        gap: 16,
        fontSize: 10,
        color: '#475569',
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
