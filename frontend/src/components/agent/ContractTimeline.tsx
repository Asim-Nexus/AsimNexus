/**
 * ContractTimeline — Visual Timeline of Agent Contracts
 *
 * Displays a visual timeline of 5/15/30 day agent contracts showing
 * their lifecycle: proposed → active → expiring → expired/completed.
 * Color-coded by duration tier and status.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { personalAPI } from '../../api/asimnexus';

interface ContractTimelineProps {
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
    completed_at?: string;
}

const DURATION_COLORS: Record<number, string> = {
    5: '#3b82f6',
    15: '#f59e0b',
    30: '#8b5cf6',
};

const DURATION_LABELS: Record<number, string> = {
    5: '5-Day Trial',
    15: '15-Day Standard',
    30: '30-Day Extended',
};

const STATUS_ORDER: Record<string, number> = {
    proposed: 0,
    active: 1,
    expiring: 2,
    expired: 3,
    completed: 4,
    revoked: 5,
};

export default function ContractTimeline({ user: _user }: ContractTimelineProps) {
    const [contracts, setContracts] = useState<Contract[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    const loadContracts = useCallback(async () => {
        try {
            const res = await personalAPI.getContracts();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;
            setContracts((data?.contracts || []) as Contract[]);
        } catch {
            setContracts([]);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadContracts();
        const interval = setInterval(loadContracts, 30000);
        return () => clearInterval(interval);
    }, [loadContracts]);

    const filteredContracts = contracts
        .filter(c => filter === 'all' || c.status === filter)
        .sort((a, b) => {
            const aOrder = STATUS_ORDER[a.status || ''] ?? 99;
            const bOrder = STATUS_ORDER[b.status || ''] ?? 99;
            if (aOrder !== bOrder) return aOrder - bOrder;
            return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
        });

    const getStatusColor = (s?: string) => {
        switch (s?.toLowerCase()) {
            case 'active': return '#10b981';
            case 'proposed': return '#3b82f6';
            case 'expiring': return '#f59e0b';
            case 'expired': return '#ef4444';
            case 'completed': return '#64748b';
            case 'revoked': return '#dc2626';
            default: return '#64748b';
        }
    };

    const getDurationColor = (days?: number) => {
        return DURATION_COLORS[days || 0] || '#64748b';
    };

    const getProgressPercent = (contract: Contract): number => {
        if (!contract.created_at || !contract.duration_days) return 0;
        const created = new Date(contract.created_at).getTime();
        const now = Date.now();
        const totalMs = contract.duration_days * 24 * 60 * 60 * 1000;
        const elapsed = now - created;
        return Math.min(100, Math.max(0, (elapsed / totalMs) * 100));
    };

    const getDaysRemaining = (contract: Contract): number | null => {
        if (!contract.expires_at) return null;
        const expires = new Date(contract.expires_at).getTime();
        const now = Date.now();
        const remaining = Math.ceil((expires - now) / (24 * 60 * 60 * 1000));
        return Math.max(0, remaining);
    };

    const uniqueStatuses = ['all', ...new Set(contracts.map(c => c.status || 'unknown'))];

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>📅 Loading contract timeline...</div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>📅 Contract Timeline</h3>
            <p style={styles.subtitle}>Visual lifecycle of 5/15/30 day agent contracts</p>

            {/* Filter Tabs */}
            <div style={styles.filterRow}>
                {uniqueStatuses.map((s) => (
                    <button
                        key={s}
                        style={{
                            ...styles.filterButton,
                            background: filter === s ? '#1e293b' : 'transparent',
                            borderColor: filter === s ? '#f59e0b' : '#334155',
                            color: filter === s ? '#f59e0b' : '#94a3b8',
                        } as React.CSSProperties}
                        onClick={() => setFilter(s)}
                    >
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                ))}
            </div>

            {/* Timeline */}
            <div style={styles.timeline}>
                {filteredContracts.length === 0 ? (
                    <div style={styles.emptyState}>No contracts match the selected filter</div>
                ) : (
                    filteredContracts.map((contract, idx) => {
                        const durationColor = getDurationColor(contract.duration_days);
                        const progress = getProgressPercent(contract);
                        const daysLeft = getDaysRemaining(contract);
                        const isLast = idx === filteredContracts.length - 1;

                        return (
                            <div key={contract.contract_id} style={styles.timelineItem}>
                                {/* Timeline Connector */}
                                <div style={styles.timelineConnector}>
                                    <div style={{
                                        ...styles.timelineDot,
                                        background: getStatusColor(contract.status),
                                        borderColor: durationColor,
                                    } as React.CSSProperties} />
                                    {!isLast && <div style={styles.timelineLine} />}
                                </div>

                                {/* Contract Card */}
                                <div style={styles.contractCard}>
                                    <div style={styles.cardHeader}>
                                        <div style={styles.cardHeaderLeft}>
                                            <span style={styles.agentName}>
                                                {contract.agent_name || contract.contract_id.slice(0, 12)}
                                            </span>
                                            <span style={{
                                                ...styles.durationBadge,
                                                background: durationColor,
                                            } as React.CSSProperties}>
                                                {DURATION_LABELS[contract.duration_days || 0] || `${contract.duration_days}d`}
                                            </span>
                                        </div>
                                        <span style={{
                                            ...styles.statusBadge,
                                            color: getStatusColor(contract.status),
                                            borderColor: getStatusColor(contract.status),
                                        } as React.CSSProperties}>
                                            {contract.status?.toUpperCase() || 'UNKNOWN'}
                                        </span>
                                    </div>

                                    {/* Progress Bar */}
                                    {contract.status === 'active' && (
                                        <div style={styles.progressContainer}>
                                            <div style={styles.progressBar}>
                                                <div style={{
                                                    ...styles.progressFill,
                                                    width: `${progress}%`,
                                                    background: progress > 80 ? '#ef4444' : progress > 60 ? '#f59e0b' : '#10b981',
                                                } as React.CSSProperties} />
                                            </div>
                                            <div style={styles.progressLabels}>
                                                <span style={styles.progressLabel}>
                                                    {Math.round(progress)}% elapsed
                                                </span>
                                                {daysLeft !== null && (
                                                    <span style={styles.progressLabel}>
                                                        {daysLeft} days remaining
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Contract Meta */}
                                    <div style={styles.cardMeta}>
                                        {contract.scope && (
                                            <span style={styles.metaItem}>Scope: {contract.scope}</span>
                                        )}
                                        {contract.created_at && (
                                            <span style={styles.metaItem}>
                                                {new Date(contract.created_at).toLocaleDateString()}
                                                {contract.expires_at && ` → ${new Date(contract.expires_at).toLocaleDateString()}`}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Legend */}
            <div style={styles.legend}>
                <span style={styles.legendTitle}>Duration Tiers:</span>
                {Object.entries(DURATION_LABELS).map(([days, label]) => (
                    <span key={days} style={styles.legendItem}>
                        <span style={{
                            ...styles.legendDot,
                            background: DURATION_COLORS[Number(days)],
                        } as React.CSSProperties} />
                        {label}
                    </span>
                ))}
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>Contract Timeline — 5/15/30 Day Lifecycle</span>
                <span style={styles.footerBrand}>AsimNexus 📅 Digital Nepal</span>
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
    filterRow: {
        display: 'flex',
        gap: 6,
        marginBottom: 16,
        flexWrap: 'wrap',
    },
    filterButton: {
        border: '1px solid',
        borderRadius: 6,
        padding: '4px 12px',
        fontSize: 11,
        fontWeight: 600,
        cursor: 'pointer',
    },
    timeline: {
        display: 'flex',
        flexDirection: 'column',
        gap: 0,
        marginBottom: 16,
    },
    timelineItem: {
        display: 'flex',
        gap: 12,
        minHeight: 80,
    },
    timelineConnector: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: 20,
        flexShrink: 0,
    },
    timelineDot: {
        width: 14,
        height: 14,
        borderRadius: '50%',
        border: '3px solid',
        marginTop: 4,
        zIndex: 1,
    },
    timelineLine: {
        width: 2,
        flex: 1,
        background: '#334155',
        marginTop: -2,
    },
    contractCard: {
        flex: 1,
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 8,
        padding: 12,
        marginBottom: 8,
    },
    cardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    cardHeaderLeft: {
        display: 'flex',
        gap: 8,
        alignItems: 'center',
    },
    agentName: {
        fontSize: 13,
        fontWeight: 600,
        color: '#e2e8f0',
    },
    durationBadge: {
        fontSize: 9,
        fontWeight: 700,
        color: '#fff',
        padding: '2px 8px',
        borderRadius: 4,
    },
    statusBadge: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid',
    },
    progressContainer: {
        marginBottom: 8,
    },
    progressBar: {
        height: 6,
        background: '#0f172a',
        borderRadius: 3,
        overflow: 'hidden',
    },
    progressFill: {
        height: '100%',
        borderRadius: 3,
        transition: 'width 1s ease',
    },
    progressLabels: {
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: 2,
    },
    progressLabel: {
        fontSize: 9,
        color: '#64748b',
    },
    cardMeta: {
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        fontSize: 10,
        color: '#64748b',
    },
    metaItem: {},
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#64748b',
        fontSize: 14,
    },
    legend: {
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        fontSize: 11,
        color: '#94a3b8',
        marginBottom: 16,
        flexWrap: 'wrap',
    },
    legendTitle: {
        fontWeight: 600,
        color: '#cbd5e1',
    },
    legendItem: {
        display: 'flex',
        alignItems: 'center',
        gap: 4,
    },
    legendDot: {
        width: 8,
        height: 8,
        borderRadius: '50%',
        display: 'inline-block',
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
