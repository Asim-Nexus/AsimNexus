/**
 * VetoPanel — Government Veto Management
 *
 * Manages the full lifecycle of government vetoes: issue new vetoes,
 * approve pending vetoes, view veto history, and check actions against
 * the Dharma Veto Engine for constitutional compliance.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { governanceAPI } from '../../api/asimnexus';

// ── Types ────────────────────────────────────────────────────────────────

interface VetoRecord {
    veto_id: string;
    veto_type: string;
    reason: string;
    initiated_by: string;
    timestamp: string;
    status: 'pending' | 'approved' | 'rejected';
    target_action?: string;
    approver?: string;
    approved_at?: string;
}

interface DharmaResult {
    allowed: boolean;
    level: string;
    reason: string;
    details?: string;
}

interface VetoPanelProps {
    user?: Record<string, unknown>;
}

// ── Component ────────────────────────────────────────────────────────────

export default function VetoPanel({ user }: VetoPanelProps) {
    const [vetoes, setVetoes] = useState<VetoRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'approved'>('all');

    // Issue Veto Form
    const [showIssueForm, setShowIssueForm] = useState(false);
    const [vetoAction, setVetoAction] = useState('');
    const [vetoReason, setVetoReason] = useState('');
    const [vetoType, setVetoType] = useState('POLICY');

    // Dharma Check
    const [dharmaAction, setDharmaAction] = useState('');
    const [dharmaResult, setDharmaResult] = useState<DharmaResult | null>(null);
    const [dharmaLoading, setDharmaLoading] = useState(false);

    // Emergency
    const [emergencyReason, setEmergencyReason] = useState('');
    const [emergencyActive, setEmergencyActive] = useState(false);
    const [emergencyLoading, setEmergencyLoading] = useState(false);

    const loadVetoes = useCallback(async () => {
        try {
            const res = await governanceAPI.getPolicies();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;
            setVetoes((data?.vetoes || []) as VetoRecord[]);
        } catch {
            setVetoes([]);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadVetoes();
        const interval = setInterval(loadVetoes, 30000);
        return () => clearInterval(interval);
    }, [loadVetoes]);

    const handleIssueVeto = async () => {
        if (!vetoAction.trim() || !vetoReason.trim()) return;
        setActionLoading('issue-veto');
        setMessage(null);
        try {
            const res = await governanceAPI.issueVeto({
                action: vetoAction,
                reason: vetoReason,
                veto_type: vetoType,
                initiated_by: (user?.username as string) || 'government',
            });
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Veto issued successfully ✓' });
                setVetoAction('');
                setVetoReason('');
                setShowIssueForm(false);
                loadVetoes();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Veto failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to issue veto';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const handleApproveVeto = async (vetoId: string) => {
        setActionLoading(`approve-${vetoId}`);
        setMessage(null);
        try {
            const res = await governanceAPI.approveVeto(vetoId, (user?.username as string) || 'government');
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Veto approved ✓' });
                loadVetoes();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Approval failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to approve veto';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const handleDharmaCheck = async () => {
        if (!dharmaAction.trim()) return;
        setDharmaLoading(true);
        setDharmaResult(null);
        try {
            const res = await governanceAPI.dharmaCheck(dharmaAction, (user?.username as string) || 'government', {});
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as DharmaResult;
            setDharmaResult(data);
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Dharma check failed';
            setDharmaResult({ allowed: false, level: 'ERROR', reason: errorMsg });
        }
        setDharmaLoading(false);
    };

    const handleDeclareEmergency = async () => {
        if (!emergencyReason.trim()) return;
        setEmergencyLoading(true);
        setMessage(null);
        try {
            const res = await governanceAPI.declareEmergency(emergencyReason, (user?.username as string) || 'government');
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Emergency declared ✓' });
                setEmergencyActive(true);
                setEmergencyReason('');
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to declare emergency';
            setMessage({ type: 'error', text: errorMsg });
        }
        setEmergencyLoading(false);
    };

    const handleResolveEmergency = async () => {
        setEmergencyLoading(true);
        setMessage(null);
        try {
            const res = await governanceAPI.resolveEmergency((user?.username as string) || 'government');
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Emergency resolved ✓' });
                setEmergencyActive(false);
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to resolve emergency';
            setMessage({ type: 'error', text: errorMsg });
        }
        setEmergencyLoading(false);
    };

    const filteredVetoes = vetoes.filter((v) => {
        if (activeTab === 'pending') return v.status === 'pending';
        if (activeTab === 'approved') return v.status === 'approved';
        return true;
    });

    const getVetoTypeColor = (type: string) => {
        switch (type) {
            case 'CONSTITUTIONAL': return '#8b5cf6';
            case 'POLICY': return '#3b82f6';
            case 'OPERATIONAL': return '#f59e0b';
            case 'EMERGENCY': return '#ef4444';
            default: return '#64748b';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'approved': return '#10b981';
            case 'rejected': return '#ef4444';
            case 'pending': return '#f59e0b';
            default: return '#64748b';
        }
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>🛑 Loading veto data...</div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Header */}
            <div style={styles.headerActions}>
                <h3 style={styles.sectionTitle}>🛑 Veto Management</h3>
                <div style={styles.actionButtons}>
                    <button
                        style={styles.actionButton}
                        onClick={() => setShowIssueForm(!showIssueForm)}
                    >
                        {showIssueForm ? '✕ Cancel' : '➕ New Veto'}
                    </button>
                </div>
            </div>

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

            {/* Issue Veto Form */}
            {showIssueForm && (
                <div style={{ ...styles.formCard, borderColor: '#dc2626' }}>
                    <h4 style={{ ...styles.formTitle, color: '#fca5a5' }}>🛑 Issue New Veto</h4>
                    <input
                        style={styles.formInput}
                        placeholder="Action to veto (e.g., approve_policy:xxx)"
                        value={vetoAction}
                        onChange={(e) => setVetoAction(e.target.value)}
                    />
                    <textarea
                        style={styles.formTextarea}
                        placeholder="Reason for veto"
                        value={vetoReason}
                        onChange={(e) => setVetoReason(e.target.value)}
                        rows={3}
                    />
                    <select
                        style={styles.formSelect}
                        value={vetoType}
                        onChange={(e) => setVetoType(e.target.value)}
                    >
                        <option value="POLICY">Policy Veto</option>
                        <option value="CONSTITUTIONAL">Constitutional Veto</option>
                        <option value="OPERATIONAL">Operational Veto</option>
                        <option value="EMERGENCY">Emergency Veto</option>
                    </select>
                    <button
                        style={{
                            ...styles.submitButton,
                            background: '#dc2626',
                            opacity: (vetoAction.trim() && vetoReason.trim()) ? 1 : 0.5,
                        } as React.CSSProperties}
                        onClick={handleIssueVeto}
                        disabled={!vetoAction.trim() || !vetoReason.trim() || actionLoading === 'issue-veto'}
                    >
                        {actionLoading === 'issue-veto' ? '⏳ Processing...' : '🛑 Issue Veto'}
                    </button>
                </div>
            )}

            {/* Dharma Check Section */}
            <div style={styles.dharmaSection}>
                <h4 style={styles.dharmaTitle}>☯ Dharma Veto Engine Check</h4>
                <div style={styles.dharmaRow}>
                    <input
                        style={{ ...styles.formInput, flex: 1, marginBottom: 0 }}
                        placeholder="Action to check (e.g., approve_budget:education:1000000)"
                        value={dharmaAction}
                        onChange={(e) => setDharmaAction(e.target.value)}
                    />
                    <button
                        style={{
                            ...styles.dharmaButton,
                            opacity: dharmaAction.trim() ? 1 : 0.5,
                        } as React.CSSProperties}
                        onClick={handleDharmaCheck}
                        disabled={!dharmaAction.trim() || dharmaLoading}
                    >
                        {dharmaLoading ? '⏳' : '☯ Check'}
                    </button>
                </div>
                {dharmaResult && (
                    <div style={{
                        ...styles.dharmaResult,
                        borderColor: dharmaResult.allowed ? '#16a34a' : '#dc2626',
                        background: dharmaResult.allowed ? '#052e16' : '#7f1d1d',
                    } as React.CSSProperties}>
                        <div style={styles.dharmaResultHeader}>
                            <span style={{
                                color: dharmaResult.allowed ? '#86efac' : '#fca5a5',
                                fontWeight: 700,
                            }}>
                                {dharmaResult.allowed ? '✅ ALLOWED' : '🚫 BLOCKED'}
                            </span>
                            <span style={styles.dharmaLevel}>{dharmaResult.level}</span>
                        </div>
                        <div style={styles.dharmaReason}>{dharmaResult.reason}</div>
                        {dharmaResult.details && (
                            <div style={styles.dharmaDetails}>{dharmaResult.details}</div>
                        )}
                    </div>
                )}
            </div>

            {/* Emergency Section */}
            <div style={styles.emergencySection}>
                <h4 style={styles.emergencyTitle}>
                    {emergencyActive ? '🔴 Emergency Active' : '⚪ Emergency Controls'}
                </h4>
                {emergencyActive ? (
                    <button
                        style={styles.resolveButton}
                        onClick={handleResolveEmergency}
                        disabled={emergencyLoading}
                    >
                        {emergencyLoading ? '⏳ Resolving...' : '✅ Resolve Emergency'}
                    </button>
                ) : (
                    <div style={styles.emergencyForm}>
                        <input
                            style={styles.formInput}
                            placeholder="Reason for emergency declaration"
                            value={emergencyReason}
                            onChange={(e) => setEmergencyReason(e.target.value)}
                        />
                        <button
                            style={{
                                ...styles.emergencyButton,
                                opacity: emergencyReason.trim() ? 1 : 0.5,
                            } as React.CSSProperties}
                            onClick={handleDeclareEmergency}
                            disabled={!emergencyReason.trim() || emergencyLoading}
                        >
                            {emergencyLoading ? '⏳ Declaring...' : '🔴 Declare Emergency'}
                        </button>
                    </div>
                )}
            </div>

            {/* Tab Navigation */}
            <div style={styles.tabBar}>
                {(['all', 'pending', 'approved'] as const).map((tab) => (
                    <button
                        key={tab}
                        style={{
                            ...styles.tabButton,
                            borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
                            color: activeTab === tab ? '#60a5fa' : '#64748b',
                        } as React.CSSProperties}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        {tab === 'pending' && ` (${vetoes.filter(v => v.status === 'pending').length})`}
                    </button>
                ))}
            </div>

            {/* Veto List */}
            <div style={styles.vetoList}>
                {filteredVetoes.length === 0 ? (
                    <div style={styles.emptyState}>No {activeTab === 'all' ? '' : activeTab} vetoes found</div>
                ) : (
                    filteredVetoes.map((veto) => (
                        <div key={veto.veto_id} style={{
                            ...styles.vetoCard,
                            borderLeftColor: getVetoTypeColor(veto.veto_type),
                        } as React.CSSProperties}>
                            <div style={styles.vetoHeader}>
                                <div style={styles.vetoHeaderLeft}>
                                    <span style={{
                                        ...styles.vetoTypeBadge,
                                        background: getVetoTypeColor(veto.veto_type),
                                    } as React.CSSProperties}>
                                        {veto.veto_type}
                                    </span>
                                    <span style={{
                                        ...styles.vetoStatusBadge,
                                        color: getStatusColor(veto.status),
                                        borderColor: getStatusColor(veto.status),
                                    } as React.CSSProperties}>
                                        {veto.status.toUpperCase()}
                                    </span>
                                </div>
                                <span style={styles.vetoTime}>
                                    {new Date(veto.timestamp).toLocaleString()}
                                </span>
                            </div>
                            <div style={styles.vetoReason}>{veto.reason}</div>
                            <div style={styles.vetoMeta}>
                                <span>Target: <strong>{veto.target_action || '—'}</strong></span>
                                <span>By: {veto.initiated_by}</span>
                            </div>
                            {veto.status === 'approved' && veto.approver && (
                                <div style={styles.vetoApprovedBy}>
                                    Approved by {veto.approver}
                                    {veto.approved_at ? ` on ${new Date(veto.approved_at).toLocaleDateString()}` : ''}
                                </div>
                            )}
                            {veto.status === 'pending' && (
                                <button
                                    style={{
                                        ...styles.approveButton,
                                        opacity: actionLoading === `approve-${veto.veto_id}` ? 0.6 : 1,
                                    } as React.CSSProperties}
                                    onClick={() => handleApproveVeto(veto.veto_id)}
                                    disabled={actionLoading === `approve-${veto.veto_id}`}
                                >
                                    {actionLoading === `approve-${veto.veto_id}` ? '⏳ Approving...' : '✅ Approve Veto'}
                                </button>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>Total vetoes: {vetoes.length} | Pending: {vetoes.filter(v => v.status === 'pending').length}</span>
                <span style={styles.footerBrand}>AsimNexus 🛑 Digital Nepal</span>
            </div>
        </div>
    );
}

// ── Styles ───────────────────────────────────────────────────────────────

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
    headerActions: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
        flexWrap: 'wrap',
        gap: 10,
    },
    sectionTitle: {
        margin: 0,
        fontSize: 18,
        color: '#f1f5f9',
    },
    actionButtons: {
        display: 'flex',
        gap: 8,
    },
    actionButton: {
        background: '#7f1d1d',
        color: '#fca5a5',
        border: '1px solid #dc2626',
        borderRadius: 6,
        padding: '6px 14px',
        fontSize: 12,
        fontWeight: 600,
        cursor: 'pointer',
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
    formCard: {
        background: '#1e293b',
        border: '1px solid #dc2626',
        borderRadius: 10,
        padding: 16,
        marginBottom: 16,
    },
    formTitle: {
        margin: '0 0 12px 0',
        fontSize: 14,
        color: '#e2e8f0',
        fontWeight: 600,
    },
    formInput: {
        width: '100%',
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 12px',
        color: '#e2e8f0',
        fontSize: 13,
        marginBottom: 8,
        outline: 'none',
        boxSizing: 'border-box' as const,
    },
    formTextarea: {
        width: '100%',
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 12px',
        color: '#e2e8f0',
        fontSize: 13,
        marginBottom: 8,
        outline: 'none',
        fontFamily: 'inherit',
        resize: 'vertical' as const,
        boxSizing: 'border-box' as const,
    },
    formSelect: {
        width: '100%',
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 12px',
        color: '#e2e8f0',
        fontSize: 13,
        marginBottom: 12,
        outline: 'none',
        boxSizing: 'border-box' as const,
    },
    submitButton: {
        width: '100%',
        background: '#dc2626',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
    },
    dharmaSection: {
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
        border: '1px solid #312e81',
        borderRadius: 10,
        padding: 14,
        marginBottom: 16,
    },
    dharmaTitle: {
        margin: '0 0 10px 0',
        fontSize: 14,
        color: '#a78bfa',
        fontWeight: 600,
    },
    dharmaRow: {
        display: 'flex',
        gap: 8,
        alignItems: 'flex-start',
    },
    dharmaButton: {
        background: '#7c3aed',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
        whiteSpace: 'nowrap' as const,
        height: 36,
    },
    dharmaResult: {
        marginTop: 10,
        border: '1px solid',
        borderRadius: 8,
        padding: 10,
    },
    dharmaResultHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 4,
    },
    dharmaLevel: {
        fontSize: 11,
        color: '#94a3b8',
        fontWeight: 600,
    },
    dharmaReason: {
        fontSize: 12,
        color: '#e2e8f0',
    },
    dharmaDetails: {
        fontSize: 11,
        color: '#94a3b8',
        marginTop: 4,
        fontStyle: 'italic',
    },
    emergencySection: {
        background: '#1e293b',
        border: '1px solid #dc2626',
        borderRadius: 10,
        padding: 14,
        marginBottom: 16,
    },
    emergencyTitle: {
        margin: '0 0 10px 0',
        fontSize: 14,
        color: '#fca5a5',
        fontWeight: 600,
    },
    emergencyForm: {
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 8,
    },
    emergencyButton: {
        width: '100%',
        background: '#dc2626',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
    },
    resolveButton: {
        width: '100%',
        background: '#16a34a',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
    },
    tabBar: {
        display: 'flex',
        gap: 0,
        marginBottom: 12,
        borderBottom: '1px solid #334155',
    },
    tabButton: {
        background: 'none',
        border: 'none',
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
    },
    vetoList: {
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 8,
        marginBottom: 16,
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#64748b',
        fontSize: 14,
    },
    vetoCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderLeft: '4px solid',
        borderRadius: 8,
        padding: 12,
    },
    vetoHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
    },
    vetoHeaderLeft: {
        display: 'flex',
        gap: 6,
        alignItems: 'center',
    },
    vetoTypeBadge: {
        fontSize: 10,
        fontWeight: 700,
        color: '#fff',
        padding: '2px 8px',
        borderRadius: 4,
    },
    vetoStatusBadge: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid',
    },
    vetoTime: {
        fontSize: 10,
        color: '#64748b',
    },
    vetoReason: {
        fontSize: 13,
        color: '#e2e8f0',
        marginBottom: 6,
    },
    vetoMeta: {
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#64748b',
        marginBottom: 6,
    },
    vetoApprovedBy: {
        fontSize: 11,
        color: '#10b981',
        marginBottom: 6,
    },
    approveButton: {
        width: '100%',
        background: '#16a34a',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '6px 12px',
        fontSize: 12,
        fontWeight: 600,
        cursor: 'pointer',
        marginTop: 6,
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
