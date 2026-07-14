/**
 * Government Dashboard — 51% Public Control Hub
 *
 * Main dashboard for government officials to monitor the 51/49 power balance,
 * approve policies, issue vetoes, and track constitutional compliance.
 *
 * Uses SmartHub tab-based layout (same pattern as EconomyHub, NetworkHub).
 */
import React, { useState, useEffect, useCallback } from 'react';
import SmartHub from '../shared/SmartHub';
import BalanceMonitor from './BalanceMonitor';
import PolicyApprovalPanel from './PolicyApprovalPanel';
import VetoPanel from './VetoPanel';
import { governanceAPI } from '../../api/asimnexus';

interface GovernanceStats {
    government?: {
        total_vetoes: number;
        approved_vetoes: number;
        pending_vetoes: number;
        emergency_active: boolean;
        total_audit_entries: number;
        constitutional_amendments: number;
    };
    power_balance?: {
        total_decisions: number;
        public_share: number;
        private_share: number;
        total_amendments: number;
        total_audit_entries: number;
    };
    dharma?: {
        total_checked: number;
        passed: number;
        blocked: number;
        warned: number;
    };
}

const TABS = [
    { id: 'balance', label: 'Balance', icon: '⚖️', desc: '51/49 Power Balance' },
    { id: 'policies', label: 'Policies', icon: '📜', desc: 'Policy Approval' },
    { id: 'veto', label: 'Veto', icon: '🛑', desc: 'Veto Management' },
    { id: 'audit', label: 'Audit', icon: '📋', desc: 'Audit Trail' },
];

interface GovernmentDashboardProps {
    user?: Record<string, unknown>;
}

export default function GovernmentDashboard({ user }: GovernmentDashboardProps) {
    const [stats, setStats] = useState<GovernanceStats | null>(null);
    const [loading, setLoading] = useState(true);

    const loadStats = useCallback(async () => {
        try {
            const res = await governanceAPI.getStats();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            setStats((responseData?.data || responseData) as GovernanceStats);
        } catch {
            // Use fallback data
            setStats({
                government: {
                    total_vetoes: 0, approved_vetoes: 0, pending_vetoes: 0,
                    emergency_active: false, total_audit_entries: 0, constitutional_amendments: 0,
                },
                power_balance: {
                    total_decisions: 0, public_share: 0.51, private_share: 0.49,
                    total_amendments: 0, total_audit_entries: 0,
                },
                dharma: { total_checked: 0, passed: 0, blocked: 0, warned: 0 },
            });
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadStats();
        const interval = setInterval(loadStats, 30000);
        return () => clearInterval(interval);
    }, [loadStats]);

    return (
        <SmartHub
            tabs={TABS}
            title="Government Dashboard"
            icon="🏛️"
            accentColor="#3b82f6"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'balance':
                        return <BalanceMonitor stats={stats} loading={loading} />;
                    case 'policies':
                        return <PolicyApprovalPanel user={user} />;
                    case 'veto':
                        return <VetoPanel user={user} />;
                    case 'audit':
                        return <AuditTrailPanel />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>Select a tab</div>;
                }
            }}
        </SmartHub>
    );
}

// ── Audit Trail Panel (inline, since it's simple) ─────────────────────

function AuditTrailPanel() {
    const [entries, setEntries] = useState<Array<Record<string, unknown>>>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAudit();
        const interval = setInterval(loadAudit, 30000);
        return () => clearInterval(interval);
    }, []);

    async function loadAudit() {
        try {
            const res = await governanceAPI.getAuditLog(200);
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;
            setEntries((data?.entries || []) as Array<Record<string, unknown>>);
        } catch {
            setEntries([]);
        }
        setLoading(false);
    }

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>📋 Loading audit trail...</div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>📋 Government Audit Trail</h3>
            <p style={styles.subtitle}>Immutable log of all government-layer actions</p>

            {entries.length === 0 ? (
                <div style={styles.emptyState}>No audit entries yet</div>
            ) : (
                <div style={styles.auditList}>
                    {entries.map((entry, i) => (
                        <div key={i} style={styles.auditEntry}>
                            <div style={styles.auditHeader}>
                                <span style={styles.auditAction}>
                                    {String(entry.action || 'unknown').replace(/_/g, ' ')}
                                </span>
                                <span style={styles.auditTime}>
                                    {entry.timestamp
                                        ? new Date(String(entry.timestamp)).toLocaleString()
                                        : '—'}
                                </span>
                            </div>
                            <div style={styles.auditDetails}>
                                <span><strong>Target:</strong> {String(entry.target || '—')}</span>
                                <span><strong>By:</strong> {String(entry.initiated_by || '—')}</span>
                            </div>
                            <div style={styles.auditDesc}>{String(entry.details || '')}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Shared Styles ─────────────────────────────────────────────────────

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
        margin: '0 0 5px 0',
        fontSize: '18px',
        color: '#f1f5f9',
    },
    subtitle: {
        margin: '0 0 20px 0',
        fontSize: '13px',
        color: '#64748b',
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#64748b',
        fontSize: '14px',
    },
    auditList: {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
    },
    auditEntry: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '12px',
    },
    auditHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '6px',
    },
    auditAction: {
        fontSize: '13px',
        fontWeight: 'bold',
        color: '#60a5fa',
        textTransform: 'uppercase',
    },
    auditTime: {
        fontSize: '11px',
        color: '#64748b',
    },
    auditDetails: {
        display: 'flex',
        gap: '20px',
        fontSize: '12px',
        color: '#94a3b8',
        marginBottom: '4px',
    },
    auditDesc: {
        fontSize: '12px',
        color: '#cbd5e1',
        fontStyle: 'italic',
    },
};
