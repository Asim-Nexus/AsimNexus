/**
 * PolicyApprovalPanel — Government Policy Approval Workflow
 *
 * Allows government officials to review, approve, and manage policies
 * with constitutional compliance checking and power balance enforcement.
 * Integrates with Dharma Veto Engine for ethical validation.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { governanceAPI } from '../../api/asimnexus';

// ── Types ────────────────────────────────────────────────────────────────

interface Policy {
    id: string;
    title: string;
    description: string;
    sector: string;
    status: 'pending' | 'approved' | 'rejected' | 'vetoed';
    proposed_by: string;
    proposed_at: string;
    approved_at?: string;
    veto_id?: string;
    constitutional_score?: number;
}

interface VetoRecord {
    veto_id: string;
    veto_type: string;
    reason: string;
    initiated_by: string;
    timestamp: string;
    status: 'pending' | 'approved' | 'rejected';
    target_action?: string;
}

interface PolicyApprovalPanelProps {
    user?: Record<string, unknown>;
}

// ── Component ────────────────────────────────────────────────────────────

export default function PolicyApprovalPanel({ user }: PolicyApprovalPanelProps) {
    const [policies, setPolicies] = useState<Policy[]>([]);
    const [vetoes, setVetoes] = useState<VetoRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [showProposeForm, setShowProposeForm] = useState(false);
    const [showVetoForm, setShowVetoForm] = useState(false);

    // New policy form state
    const [newTitle, setNewTitle] = useState('');
    const [newDescription, setNewDescription] = useState('');
    const [newSector, setNewSector] = useState('education');

    // Veto form state
    const [vetoAction, setVetoAction] = useState('');
    const [vetoReason, setVetoReason] = useState('');
    const [vetoType, setVetoType] = useState('POLICY');

    const loadData = useCallback(async () => {
        try {
            const res = await governanceAPI.getPolicies();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;
            setPolicies((data?.policies || []) as Policy[]);
            setVetoes((data?.vetoes || []) as VetoRecord[]);
        } catch {
            setPolicies([]);
            setVetoes([]);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    }, [loadData]);

    const handleApprovePolicy = async (policyId: string) => {
        setActionLoading(policyId);
        setMessage(null);
        try {
            const res = await governanceAPI.approvePolicy({
                policy_id: policyId,
                approved_by: (user?.username as string) || 'government_official',
            });
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Policy approved successfully ✓' });
                loadData();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Approval failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to approve policy';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const handleProposePolicy = async () => {
        if (!newTitle.trim()) return;
        setActionLoading('propose');
        setMessage(null);
        try {
            const res = await governanceAPI.approvePolicy({
                title: newTitle,
                description: newDescription,
                sector: newSector,
                proposed_by: (user?.username as string) || 'government_official',
                action: 'propose',
            });
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Policy proposed successfully ✓' });
                setNewTitle('');
                setNewDescription('');
                setShowProposeForm(false);
                loadData();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Proposal failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to propose policy';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const handleIssueVeto = async () => {
        if (!vetoAction.trim() || !vetoReason.trim()) return;
        setActionLoading('veto');
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
                setShowVetoForm(false);
                loadData();
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
        setActionLoading(`approve-veto-${vetoId}`);
        setMessage(null);
        try {
            const res = await governanceAPI.approveVeto(vetoId, (user?.username as string) || 'government');
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'Veto approved ✓' });
                loadData();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Approval failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to approve veto';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'approved': return '#10b981';
            case 'rejected': return '#ef4444';
            case 'vetoed': return '#f59e0b';
            default: return '#64748b';
        }
    };

    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>📜 Loading policies...</div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            {/* Header Actions */}
            <div style={styles.headerActions}>
                <h3 style={styles.sectionTitle}>📜 Policy Management</h3>
                <div style={styles.actionButtons}>
                    <button
                        style={styles.actionButton}
                        onClick={() => {
                            setShowProposeForm(!showProposeForm);
                            setShowVetoForm(false);
                        }}
                    >
                        {showProposeForm ? '✕ Cancel' : '➕ Propose Policy'}
                    </button>
                    <button
                        style={{ ...styles.actionButton, background: '#7f1d1d', borderColor: '#dc2626' }}
                        onClick={() => {
                            setShowVetoForm(!showVetoForm);
                            setShowProposeForm(false);
                        }}
                    >
                        {showVetoForm ? '✕ Cancel' : '🛑 Issue Veto'}
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

            {/* Propose Policy Form */}
            {showProposeForm && (
                <div style={styles.formCard}>
                    <h4 style={styles.formTitle}>Propose New Policy</h4>
                    <input
                        style={styles.formInput}
                        placeholder="Policy Title"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                    />
                    <textarea
                        style={styles.formTextarea}
                        placeholder="Policy Description"
                        value={newDescription}
                        onChange={(e) => setNewDescription(e.target.value)}
                        rows={3}
                    />
                    <select
                        style={styles.formSelect}
                        value={newSector}
                        onChange={(e) => setNewSector(e.target.value)}
                    >
                        <option value="education">Education</option>
                        <option value="healthcare">Healthcare</option>
                        <option value="infrastructure">Infrastructure</option>
                        <option value="defense">Defense</option>
                        <option value="agriculture">Agriculture</option>
                        <option value="technology">Technology</option>
                        <option value="finance">Finance</option>
                        <option value="energy">Energy</option>
                        <option value="environment">Environment</option>
                    </select>
                    <button
                        style={{
                            ...styles.submitButton,
                            opacity: newTitle.trim() ? 1 : 0.5,
                        } as React.CSSProperties}
                        onClick={handleProposePolicy}
                        disabled={!newTitle.trim() || actionLoading === 'propose'}
                    >
                        {actionLoading === 'propose' ? '⏳ Submitting...' : '📤 Submit Policy'}
                    </button>
                </div>
            )}

            {/* Issue Veto Form */}
            {showVetoForm && (
                <div style={{ ...styles.formCard, borderColor: '#dc2626' }}>
                    <h4 style={{ ...styles.formTitle, color: '#fca5a5' }}>🛑 Issue Government Veto</h4>
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
                        disabled={!vetoAction.trim() || !vetoReason.trim() || actionLoading === 'veto'}
                    >
                        {actionLoading === 'veto' ? '⏳ Processing...' : '🛑 Issue Veto'}
                    </button>
                </div>
            )}

            {/* Policies List */}
            <h4 style={styles.listTitle}>
                Active Policies ({policies.length})
            </h4>
            <div style={styles.policyList}>
                {policies.length === 0 ? (
                    <div style={styles.emptyState}>No policies found</div>
                ) : (
                    policies.map((policy) => (
                        <div key={policy.id} style={styles.policyCard}>
                            <div style={styles.policyHeader}>
                                <span style={styles.policyTitle}>{policy.title}</span>
                                <span style={{
                                    ...styles.policyStatus,
                                    color: getStatusColor(policy.status),
                                    borderColor: getStatusColor(policy.status),
                                } as React.CSSProperties}>
                                    {policy.status.toUpperCase()}
                                </span>
                            </div>
                            <div style={styles.policyDesc}>{policy.description}</div>
                            <div style={styles.policyMeta}>
                                <span>Sector: <strong>{policy.sector}</strong></span>
                                <span>By: {policy.proposed_by}</span>
                                <span>{new Date(policy.proposed_at).toLocaleDateString()}</span>
                            </div>
                            {policy.constitutional_score !== undefined && (
                                <div style={styles.policyScore}>
                                    Constitutional Score: {(policy.constitutional_score * 100).toFixed(0)}%
                                </div>
                            )}
                            {policy.status === 'pending' && (
                                <button
                                    style={{
                                        ...styles.approveButton,
                                        opacity: actionLoading === policy.id ? 0.6 : 1,
                                    } as React.CSSProperties}
                                    onClick={() => handleApprovePolicy(policy.id)}
                                    disabled={actionLoading === policy.id}
                                >
                                    {actionLoading === policy.id ? '⏳ Approving...' : '✅ Approve Policy'}
                                </button>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Pending Vetoes */}
            {vetoes.filter(v => v.status === 'pending').length > 0 && (
                <>
                    <h4 style={styles.listTitle}>
                        Pending Vetoes ({vetoes.filter(v => v.status === 'pending').length})
                    </h4>
                    <div style={styles.vetoList}>
                        {vetoes.filter(v => v.status === 'pending').map((veto) => (
                            <div key={veto.veto_id} style={{ ...styles.vetoCard, borderColor: '#f59e0b' }}>
                                <div style={styles.vetoHeader}>
                                    <span style={styles.vetoType}>{veto.veto_type}</span>
                                    <span style={styles.vetoTime}>
                                        {new Date(veto.timestamp).toLocaleString()}
                                    </span>
                                </div>
                                <div style={styles.vetoReason}>{veto.reason}</div>
                                <div style={styles.vetoMeta}>
                                    <span>Target: {veto.target_action || '—'}</span>
                                    <span>By: {veto.initiated_by}</span>
                                </div>
                                <button
                                    style={{
                                        ...styles.approveButton,
                                        background: '#f59e0b',
                                        opacity: actionLoading === `approve-veto-${veto.veto_id}` ? 0.6 : 1,
                                    } as React.CSSProperties}
                                    onClick={() => handleApproveVeto(veto.veto_id)}
                                    disabled={actionLoading === `approve-veto-${veto.veto_id}`}
                                >
                                    {actionLoading === `approve-veto-${veto.veto_id}` ? '⏳ Approving...' : '✅ Approve Veto'}
                                </button>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Footer */}
            <div style={styles.footer}>
                <span>All policies checked against constitutional compliance</span>
                <span style={styles.footerBrand}>AsimNexus 📜 Digital Nepal</span>
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
        background: '#1e3a5f',
        color: '#93c5fd',
        border: '1px solid #3b82f6',
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
        border: '1px solid #3b82f6',
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
        background: '#3b82f6',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
    },
    listTitle: {
        margin: '16px 0 10px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    policyList: {
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
    policyCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 8,
        padding: 12,
    },
    policyHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
    },
    policyTitle: {
        fontSize: 14,
        fontWeight: 600,
        color: '#e2e8f0',
    },
    policyStatus: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid',
    },
    policyDesc: {
        fontSize: 12,
        color: '#94a3b8',
        marginBottom: 6,
    },
    policyMeta: {
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#64748b',
        marginBottom: 6,
    },
    policyScore: {
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
    vetoList: {
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        marginBottom: 16,
    },
    vetoCard: {
        background: '#1e293b',
        border: '1px solid #f59e0b',
        borderRadius: 8,
        padding: 12,
    },
    vetoHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
    },
    vetoType: {
        fontSize: 11,
        fontWeight: 700,
        color: '#fbbf24',
        textTransform: 'uppercase',
    },
    vetoTime: {
        fontSize: 10,
        color: '#64748b',
    },
    vetoReason: {
        fontSize: 12,
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
