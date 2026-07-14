/**
 * CompliancePanel — Enterprise Compliance Check Interface
 *
 * Allows enterprises to check actions against compliance policies,
 * view compliance history, and monitor compliance status across
 * the organization. Integrates with the Enterprise Layer.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { enterpriseAPI } from '../../api/asimnexus';

interface ComplianceRecord {
    record_id: string;
    organization: string;
    action: string;
    status: string;
    details: string;
    checked_at: string;
}

interface CompliancePanelProps {
    user?: Record<string, unknown>;
}

export default function CompliancePanel({ user }: CompliancePanelProps) {
    const [records, setRecords] = useState<ComplianceRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    // Check form state
    const [actionToCheck, setActionToCheck] = useState('');
    const [checkResult, setCheckResult] = useState<Record<string, unknown> | null>(null);

    const loadRecords = useCallback(async () => {
        try {
            const res = await enterpriseAPI.getComplianceLog(
                (user?.organization as string) || undefined,
                50
            );
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;
            setRecords((data?.records || data?.compliance_log || []) as ComplianceRecord[]);
        } catch {
            setRecords([]);
        }
        setLoading(false);
    }, [user]);

    useEffect(() => {
        loadRecords();
        const interval = setInterval(loadRecords, 30000);
        return () => clearInterval(interval);
    }, [loadRecords]);

    const handleCheckCompliance = async () => {
        if (!actionToCheck.trim()) return;
        setActionLoading(true);
        setMessage(null);
        setCheckResult(null);
        try {
            const res = await enterpriseAPI.checkCompliance({
                organization: (user?.organization as string) || (user?.username as string) || 'enterprise',
                action: actionToCheck,
                current_users: 1,
                current_agents: 1,
                required_feature: 'basic',
            });
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;

            if (data?.status === 'compliant' || data?.status === 'ok' || responseData?.status === 'ok') {
                setCheckResult({
                    status: 'compliant',
                    details: data?.details || 'Action is compliant with enterprise policies',
                });
                setMessage({ type: 'success', text: 'Action is compliant ✓' });
            } else {
                setCheckResult({
                    status: 'non_compliant',
                    details: data?.details || data?.message || 'Action is not compliant',
                });
                setMessage({ type: 'error', text: String(data?.details || data?.message || 'Non-compliant') });
            }
            loadRecords();
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Compliance check failed';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(false);
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'compliant':
            case 'ok':
            case 'passed':
                return '#10b981';
            case 'non_compliant':
            case 'failed':
            case 'error':
                return '#ef4444';
            case 'pending_review':
            case 'pending':
                return '#f59e0b';
            case 'exempt':
                return '#8b5cf6';
            default:
                return '#64748b';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status.toLowerCase()) {
            case 'compliant':
            case 'ok':
            case 'passed':
                return '✅';
            case 'non_compliant':
            case 'failed':
            case 'error':
                return '❌';
            case 'pending_review':
            case 'pending':
                return '⏳';
            case 'exempt':
                return '🛡️';
            default:
                return '❓';
        }
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>✅ Loading compliance data...</div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>✅ Compliance Check</h3>
            <p style={styles.subtitle}>Check actions against enterprise compliance policies</p>

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

            {/* Compliance Check Form */}
            <div style={styles.checkCard}>
                <h4 style={styles.checkTitle}>Check Action Compliance</h4>
                <div style={styles.checkRow}>
                    <input
                        style={styles.checkInput}
                        placeholder="Enter action to check (e.g., hire_agent:general:30d)"
                        value={actionToCheck}
                        onChange={(e) => setActionToCheck(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleCheckCompliance();
                        }}
                    />
                    <button
                        style={{
                            ...styles.checkButton,
                            opacity: actionToCheck.trim() && !actionLoading ? 1 : 0.5,
                        } as React.CSSProperties}
                        onClick={handleCheckCompliance}
                        disabled={!actionToCheck.trim() || actionLoading}
                    >
                        {actionLoading ? '⏳...' : 'Check'}
                    </button>
                </div>

                {/* Check Result */}
                {checkResult && (
                    <div style={{
                        ...styles.resultCard,
                        borderColor: checkResult.status === 'compliant' ? '#16a34a' : '#dc2626',
                        background: checkResult.status === 'compliant' ? '#052e16' : '#7f1d1d',
                    } as React.CSSProperties}>
                        <div style={styles.resultHeader}>
                            <span style={{
                                fontSize: 20,
                                color: checkResult.status === 'compliant' ? '#86efac' : '#fca5a5',
                                fontWeight: 700,
                            }}>
                                {checkResult.status === 'compliant' ? '✅ COMPLIANT' : '❌ NON-COMPLIANT'}
                            </span>
                        </div>
                        <p style={styles.resultDetails}>
                            {String(checkResult.details || 'No details available')}
                        </p>
                    </div>
                )}
            </div>

            {/* Compliance History */}
            <h4 style={styles.listTitle}>
                Compliance History ({records.length})
            </h4>
            <div style={styles.recordList}>
                {records.length === 0 ? (
                    <div style={styles.emptyState}>No compliance checks recorded yet</div>
                ) : (
                    records.map((record) => (
                        <div key={record.record_id} style={styles.recordCard}>
                            <div style={styles.recordHeader}>
                                <span style={styles.recordAction}>{record.action}</span>
                                <span style={{
                                    ...styles.statusBadge,
                                    color: getStatusColor(record.status),
                                    borderColor: getStatusColor(record.status),
                                } as React.CSSProperties}>
                                    {getStatusIcon(record.status)} {record.status.replace(/_/g, ' ').toUpperCase()}
                                </span>
                            </div>
                            <div style={styles.recordMeta}>
                                <span>Organization: {record.organization}</span>
                                <span>Checked: {new Date(record.checked_at).toLocaleString()}</span>
                            </div>
                            {record.details && (
                                <p style={styles.recordDetails}>{record.details}</p>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>49% Private Sector — Compliance Monitoring</span>
                <span style={styles.footerBrand}>AsimNexus 🏢 Digital Nepal</span>
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
    checkCard: {
        background: '#1e293b',
        border: '1px solid #f59e0b',
        borderRadius: 10,
        padding: 16,
        marginBottom: 16,
    },
    checkTitle: {
        margin: '0 0 12px 0',
        fontSize: 14,
        color: '#e2e8f0',
        fontWeight: 600,
    },
    checkRow: {
        display: 'flex',
        gap: 8,
    },
    checkInput: {
        flex: 1,
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 12px',
        color: '#e2e8f0',
        fontSize: 13,
        outline: 'none',
    },
    checkButton: {
        background: '#f59e0b',
        color: '#1e293b',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
        whiteSpace: 'nowrap' as const,
    },
    resultCard: {
        border: '1px solid',
        borderRadius: 8,
        padding: 12,
        marginTop: 12,
    },
    resultHeader: {
        marginBottom: 6,
    },
    resultDetails: {
        margin: 0,
        fontSize: 12,
        color: '#cbd5e1',
        lineHeight: 1.5,
    },
    listTitle: {
        margin: '16px 0 10px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    recordList: {
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
    recordCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 8,
        padding: 12,
    },
    recordHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
    },
    recordAction: {
        fontSize: 13,
        fontWeight: 600,
        color: '#e2e8f0',
        fontFamily: 'monospace',
    },
    statusBadge: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid',
    },
    recordMeta: {
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#64748b',
        marginBottom: 4,
    },
    recordDetails: {
        margin: '4px 0 0 0',
        fontSize: 11,
        color: '#94a3b8',
        lineHeight: 1.4,
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
