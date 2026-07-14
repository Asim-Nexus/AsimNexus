/**
 * AgentHiringPanel — Enterprise Agent Hiring Interface
 *
 * Allows enterprises to hire AI agents with time-bound contracts
 * (5/15/30 day durations), specify scope boundaries, and manage
 * the hiring lifecycle. Integrates with the Agent Contract System.
 */
import React, { useState } from 'react';
import { enterpriseAPI } from '../../api/asimnexus';

interface AgentHiringPanelProps {
    user?: Record<string, unknown>;
}

const CONTRACT_DURATIONS = [
    { value: 5, label: '5 Days', desc: 'Trial — Quick task completion', price: 100 },
    { value: 15, label: '15 Days', desc: 'Standard — Medium projects', price: 250 },
    { value: 30, label: '30 Days', desc: 'Extended — Long-term engagement', price: 400 },
];

const AGENT_SPECIALTIES = [
    'general', 'coding', 'analysis', 'research', 'writing',
    'design', 'data_science', 'customer_support', 'marketing', 'finance',
];

export default function AgentHiringPanel({ user }: AgentHiringPanelProps) {
    const [step, setStep] = useState<'select' | 'configure' | 'review' | 'complete'>('select');
    const [selectedDuration, setSelectedDuration] = useState<number>(5);
    const [selectedSpecialty, setSelectedSpecialty] = useState('general');
    const [agentName, setAgentName] = useState('');
    const [taskDescription, setTaskDescription] = useState('');
    const [scopeRestrictions, setScopeRestrictions] = useState('');
    const [actionLoading, setActionLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [contractResult, setContractResult] = useState<Record<string, unknown> | null>(null);

    const handleStartHire = () => {
        if (!agentName.trim()) return;
        setStep('review');
    };

    const handleConfirmHire = async () => {
        setActionLoading(true);
        setMessage(null);
        try {
            const res = await enterpriseAPI.checkCompliance({
                organization: (user?.organization as string) || (user?.username as string) || 'enterprise',
                action: `hire_agent:${selectedSpecialty}:${selectedDuration}d`,
                current_users: 1,
                current_agents: 1,
                required_feature: selectedDuration > 15 ? 'api_access' : 'basic',
            });
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;

            if (data?.status === 'compliant' || data?.status === 'ok' || responseData?.status === 'ok') {
                setContractResult({
                    agent_name: agentName,
                    specialty: selectedSpecialty,
                    duration_days: selectedDuration,
                    scope: taskDescription || 'General assistance',
                    restrictions: scopeRestrictions || 'None',
                    organization: (user?.organization as string) || (user?.username as string) || 'enterprise',
                    status: 'active',
                    hired_at: new Date().toISOString(),
                });
                setStep('complete');
                setMessage({ type: 'success', text: `Agent "${agentName}" hired for ${selectedDuration} days ✓` });
            } else {
                setMessage({ type: 'error', text: String(data?.details || data?.message || 'Compliance check failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to hire agent';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(false);
    };

    const handleReset = () => {
        setStep('select');
        setAgentName('');
        setTaskDescription('');
        setScopeRestrictions('');
        setContractResult(null);
        setMessage(null);
    };

    const durationInfo = CONTRACT_DURATIONS.find(d => d.value === selectedDuration) || CONTRACT_DURATIONS[0];

    return (
        <div style={styles.container}>
            <h3 style={styles.sectionTitle}>🤝 Hire AI Agent</h3>
            <p style={styles.subtitle}>Hire time-bound AI agents with 5/15/30 day contracts</p>

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

            {/* Step 1: Select Duration & Specialty */}
            {step === 'select' && (
                <div>
                    <h4 style={styles.stepTitle}>1. Select Contract Duration</h4>
                    <div style={styles.durationGrid}>
                        {CONTRACT_DURATIONS.map((d) => (
                            <div
                                key={d.value}
                                style={{
                                    ...styles.durationCard,
                                    borderColor: selectedDuration === d.value ? '#f59e0b' : '#334155',
                                    background: selectedDuration === d.value ? '#1e293b' : '#0f172a',
                                } as React.CSSProperties}
                                onClick={() => setSelectedDuration(d.value)}
                            >
                                <span style={styles.durationValue}>{d.label}</span>
                                <span style={styles.durationDesc}>{d.desc}</span>
                                <span style={styles.durationPrice}>{d.price} credits</span>
                            </div>
                        ))}
                    </div>

                    <h4 style={styles.stepTitle}>2. Select Agent Specialty</h4>
                    <div style={styles.specialtyGrid}>
                        {AGENT_SPECIALTIES.map((s) => (
                            <div
                                key={s}
                                style={{
                                    ...styles.specialtyChip,
                                    borderColor: selectedSpecialty === s ? '#f59e0b' : '#334155',
                                    background: selectedSpecialty === s ? '#1e293b' : '#0f172a',
                                } as React.CSSProperties}
                                onClick={() => setSelectedSpecialty(s)}
                            >
                                {s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                            </div>
                        ))}
                    </div>

                    <button style={styles.nextButton} onClick={() => setStep('configure')}>
                        Next: Configure Agent →
                    </button>
                </div>
            )}

            {/* Step 2: Configure Agent */}
            {step === 'configure' && (
                <div>
                    <h4 style={styles.stepTitle}>3. Configure Agent</h4>
                    <input
                        style={styles.formInput}
                        placeholder="Agent Name (e.g., DataAnalyst-01)"
                        value={agentName}
                        onChange={(e) => setAgentName(e.target.value)}
                    />
                    <textarea
                        style={styles.formTextarea}
                        placeholder="Task Description — What should this agent do?"
                        value={taskDescription}
                        onChange={(e) => setTaskDescription(e.target.value)}
                        rows={3}
                    />
                    <textarea
                        style={styles.formTextarea}
                        placeholder="Scope Restrictions — What should the agent NOT do? (optional)"
                        value={scopeRestrictions}
                        onChange={(e) => setScopeRestrictions(e.target.value)}
                        rows={2}
                    />
                    <div style={styles.navButtons}>
                        <button style={styles.backButton} onClick={() => setStep('select')}>
                            ← Back
                        </button>
                        <button
                            style={{
                                ...styles.nextButton,
                                opacity: agentName.trim() ? 1 : 0.5,
                            } as React.CSSProperties}
                            onClick={handleStartHire}
                            disabled={!agentName.trim()}
                        >
                            Review & Confirm →
                        </button>
                    </div>
                </div>
            )}

            {/* Step 3: Review */}
            {step === 'review' && (
                <div>
                    <h4 style={styles.stepTitle}>Review Hire Details</h4>
                    <div style={styles.reviewCard}>
                        <div style={styles.reviewRow}>
                            <span>Agent Name</span>
                            <span style={{ fontWeight: 600 }}>{agentName}</span>
                        </div>
                        <div style={styles.reviewRow}>
                            <span>Specialty</span>
                            <span>{selectedSpecialty.replace(/_/g, ' ')}</span>
                        </div>
                        <div style={styles.reviewRow}>
                            <span>Duration</span>
                            <span>{durationInfo.label} ({durationInfo.price} credits)</span>
                        </div>
                        <div style={styles.reviewRow}>
                            <span>Task</span>
                            <span>{taskDescription || 'General assistance'}</span>
                        </div>
                        <div style={styles.reviewRow}>
                            <span>Restrictions</span>
                            <span>{scopeRestrictions || 'None'}</span>
                        </div>
                        <div style={styles.reviewRow}>
                            <span>Organization</span>
                            <span>{(user?.organization as string) || (user?.username as string) || 'Enterprise'}</span>
                        </div>
                    </div>
                    <div style={styles.navButtons}>
                        <button style={styles.backButton} onClick={() => setStep('configure')}>
                            ← Back
                        </button>
                        <button
                            style={{
                                ...styles.confirmButton,
                                opacity: actionLoading ? 0.6 : 1,
                            } as React.CSSProperties}
                            onClick={handleConfirmHire}
                            disabled={actionLoading}
                        >
                            {actionLoading ? '⏳ Processing...' : '✅ Confirm Hire'}
                        </button>
                    </div>
                </div>
            )}

            {/* Step 4: Complete */}
            {step === 'complete' && contractResult && (
                <div>
                    <div style={styles.successCard}>
                        <span style={styles.successIcon}>✅</span>
                        <h4 style={styles.successTitle}>Agent Hired Successfully!</h4>
                        <div style={styles.contractDetails}>
                            <div style={styles.detailRow}>
                                <span>Agent</span>
                                <span>{String(contractResult.agent_name)}</span>
                            </div>
                            <div style={styles.detailRow}>
                                <span>Duration</span>
                                <span>{String(contractResult.duration_days)} days</span>
                            </div>
                            <div style={styles.detailRow}>
                                <span>Status</span>
                                <span style={{ color: '#10b981' }}>{String(contractResult.status).toUpperCase()}</span>
                            </div>
                            <div style={styles.detailRow}>
                                <span>Hired At</span>
                                <span>{new Date(String(contractResult.hired_at)).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                    <button style={styles.nextButton} onClick={handleReset}>
                        Hire Another Agent →
                    </button>
                </div>
            )}

            {/* Footer */}
            <div style={styles.footer}>
                <span>All agents hired with time-bound contracts (5/15/30 day durations)</span>
                <span style={styles.footerBrand}>AsimNexus 🤝 Digital Nepal</span>
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
    stepTitle: {
        margin: '16px 0 10px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    durationGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 10,
        marginBottom: 8,
    },
    durationCard: {
        border: '1px solid',
        borderRadius: 10,
        padding: 14,
        cursor: 'pointer',
        textAlign: 'center',
        transition: 'all 0.2s ease',
    },
    durationValue: {
        display: 'block',
        fontSize: 16,
        fontWeight: 700,
        color: '#f1f5f9',
        marginBottom: 4,
    },
    durationDesc: {
        display: 'block',
        fontSize: 11,
        color: '#94a3b8',
        marginBottom: 6,
    },
    durationPrice: {
        display: 'block',
        fontSize: 12,
        color: '#f59e0b',
        fontWeight: 600,
    },
    specialtyGrid: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: 6,
        marginBottom: 16,
    },
    specialtyChip: {
        border: '1px solid',
        borderRadius: 20,
        padding: '6px 14px',
        cursor: 'pointer',
        fontSize: 12,
        color: '#e2e8f0',
        transition: 'all 0.2s ease',
    },
    nextButton: {
        background: '#f59e0b',
        color: '#1e293b',
        border: 'none',
        borderRadius: 6,
        padding: '8px 20px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
        marginTop: 8,
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
        resize: 'vertical' as const,
        fontFamily: 'inherit',
        boxSizing: 'border-box' as const,
    },
    navButtons: {
        display: 'flex',
        gap: 10,
        marginTop: 12,
    },
    backButton: {
        background: '#1e293b',
        color: '#94a3b8',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 20px',
        fontSize: 13,
        cursor: 'pointer',
    },
    confirmButton: {
        background: '#059669',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '8px 20px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
    },
    reviewCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 10,
        padding: 16,
        marginBottom: 12,
    },
    reviewRow: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '6px 0',
        fontSize: 13,
        color: '#94a3b8',
        borderBottom: '1px solid #0f172a',
    },
    successCard: {
        background: '#052e16',
        border: '1px solid #16a34a',
        borderRadius: 12,
        padding: 24,
        textAlign: 'center' as const,
        marginBottom: 16,
    },
    successIcon: {
        fontSize: 40,
        display: 'block',
        marginBottom: 8,
    },
    successTitle: {
        margin: '0 0 16px 0',
        fontSize: 16,
        color: '#86efac',
        fontWeight: 700,
    },
    contractDetails: {
        textAlign: 'left' as const,
        maxWidth: 300,
        margin: '0 auto',
    },
    detailRow: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '4px 0',
        fontSize: 13,
        color: '#a7f3d0',
        borderBottom: '1px solid #064e3b',
    },
    footer: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 10,
        color: '#475569',
        borderTop: '1px solid #1e293b',
        paddingTop: 10,
        marginTop: 16,
    },
    footerBrand: {
        color: '#7c3aed',
        fontWeight: 600,
    },
};
