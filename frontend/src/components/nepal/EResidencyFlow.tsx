/**
 * e-Residency Flow — Apply for Digital Residency in Nepal
 * Multi-step application wizard with document upload and verification.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { governmentAPI } from '../../api/asimnexus';

interface Program {
    id: string;
    name: string;
    country: string;
    description: string;
    fee: number;
    duration_days: number;
    requirements: string[];
}

interface EResidencyFlowProps {
    user?: Record<string, unknown>;
    onComplete?: () => void;
}

const STEP_ICONS = ['🪪', '📋', '📎', '✅'];
const STEP_LABELS = ['Select Program', 'Personal Info', 'Documents', 'Review & Submit'];

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    padding: 16,
};

const INPUT: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: 8,
    border: '1px solid rgba(255,255,255,0.1)',
    background: 'rgba(0,0,0,0.3)',
    color: '#e8e8e8',
    fontSize: '0.82rem',
    outline: 'none',
    boxSizing: 'border-box',
};

const LABEL: React.CSSProperties = {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: '#94a3b8',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
};

export default function EResidencyFlow({ user, onComplete }: EResidencyFlowProps) {
    const [step, setStep] = useState(0);
    const [programs, setPrograms] = useState<Program[]>([]);
    const [selectedProgram, setSelectedProgram] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Form fields
    const [fullName, setFullName] = useState(user?.display_name as string || '');
    const [email, setEmail] = useState(user?.email as string || '');
    const [phone, setPhone] = useState('');
    const [nationality, setNationality] = useState('NP');
    const [reason, setReason] = useState('');
    const [documents, setDocuments] = useState<string[]>([]);

    const loadPrograms = useCallback(async () => {
        setLoading(true);
        try {
            const res = await governmentAPI.getEResidencyPrograms();
            const d = res.data as unknown as Record<string, unknown>;
            const data = d?.data as Record<string, unknown>;
            setPrograms(data?.programs as Program[] || []);
            if ((data?.programs as Program[])?.length > 0) {
                setSelectedProgram((data?.programs as Program[])[0].id);
            }
        } catch (err) {
            console.warn('[EResidency] Error loading programs:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadPrograms(); }, [loadPrograms]);

    const handleSubmit = async () => {
        setSubmitting(true);
        setError(null);
        try {
            const res = await governmentAPI.applyEResidency({
                user_id: (user?.id as string) || 'anonymous',
                program_id: selectedProgram,
                documents,
                reason,
            });
            const d = res.data as unknown as Record<string, unknown>;
            if (d?.success || d?.status === 'ok') {
                setStep(4);
                if (onComplete) onComplete();
            } else {
                setError((d?.message as string) || 'Application failed');
            }
        } catch (err) {
            setError('Failed to submit application. Please try again.');
            console.warn('[EResidency] Submit error:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const canProceed = () => {
        switch (step) {
            case 0: return !!selectedProgram;
            case 1: return fullName.length > 0 && email.length > 0;
            case 2: return documents.length > 0;
            case 3: return true;
            default: return false;
        }
    };

    const selectedProg = programs.find(p => p.id === selectedProgram);

    if (loading) {
        return (
            <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>🪪</div>
                <div>Loading e-Residency programs...</div>
            </div>
        );
    }

    return (
        <div style={{ padding: 16, maxWidth: 700, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10b981', marginBottom: 4 }}>
                🪪 e-Residency Application
            </div>
            <div style={{ fontSize: '0.75rem', opacity: 0.5, marginBottom: 20 }}>
                Apply for digital residency in Nepal — 4-step application process
            </div>

            {/* Step Progress */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
                {STEP_ICONS.map((icon, i) => (
                    <div key={i} style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 4,
                    }}>
                        <div style={{
                            width: 36,
                            height: 36,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1rem',
                            background: step >= i ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.05)',
                            border: `2px solid ${step >= i ? '#10b981' : 'rgba(255,255,255,0.1)'}`,
                            transition: 'all 0.3s',
                        }}>
                            {step > i ? '✓' : icon}
                        </div>
                        <div style={{
                            fontSize: '0.6rem',
                            opacity: step >= i ? 0.8 : 0.3,
                            textAlign: 'center',
                            color: step >= i ? '#10b981' : undefined,
                        }}>
                            {STEP_LABELS[i]}
                        </div>
                    </div>
                ))}
            </div>

            {/* Step 0: Select Program */}
            {step === 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={CARD}>
                        <div style={LABEL}>Select e-Residency Program</div>
                        <select
                            value={selectedProgram}
                            onChange={e => setSelectedProgram(e.target.value)}
                            style={INPUT}
                        >
                            {programs.map(p => (
                                <option key={p.id} value={p.id}>{p.name} — {p.country}</option>
                            ))}
                        </select>
                    </div>

                    {selectedProg && (
                        <div style={CARD}>
                            <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: 8 }}>{selectedProg.name}</div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.7, lineHeight: 1.6, marginBottom: 8 }}>
                                {selectedProg.description}
                            </div>
                            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: '0.72rem' }}>
                                <span style={{ color: '#f59e0b' }}>💰 Fee: ${selectedProg.fee}</span>
                                <span style={{ color: '#3b82f6' }}>⏱ Duration: {selectedProg.duration_days} days</span>
                            </div>
                            {selectedProg.requirements?.length > 0 && (
                                <div style={{ marginTop: 8 }}>
                                    <div style={{ fontSize: '0.68rem', opacity: 0.5, marginBottom: 4 }}>Requirements:</div>
                                    {selectedProg.requirements.map((req, i) => (
                                        <div key={i} style={{ fontSize: '0.72rem', opacity: 0.7, paddingLeft: 12 }}>
                                            • {req}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Step 1: Personal Info */}
            {step === 1 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={CARD}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div>
                                <div style={LABEL}>Full Name</div>
                                <input style={INPUT} value={fullName} onChange={e => setFullName(e.target.value)}
                                    placeholder="Enter your full name" />
                            </div>
                            <div>
                                <div style={LABEL}>Email</div>
                                <input style={INPUT} value={email} onChange={e => setEmail(e.target.value)}
                                    placeholder="email@example.com" type="email" />
                            </div>
                            <div>
                                <div style={LABEL}>Phone</div>
                                <input style={INPUT} value={phone} onChange={e => setPhone(e.target.value)}
                                    placeholder="+977-XXXXXXXXX" />
                            </div>
                            <div>
                                <div style={LABEL}>Nationality</div>
                                <select value={nationality} onChange={e => setNationality(e.target.value)} style={INPUT}>
                                    <option value="NP">🇳🇵 Nepal</option>
                                    <option value="IN">🇮🇳 India</option>
                                    <option value="CN">🇨🇳 China</option>
                                    <option value="US">🇺🇸 United States</option>
                                    <option value="GB">🇬🇧 United Kingdom</option>
                                    <option value="OTHER">🌍 Other</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Step 2: Documents */}
            {step === 2 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={CARD}>
                        <div style={LABEL}>Upload Documents</div>
                        <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 12 }}>
                            Upload scanned copies of required documents (passport, national ID, etc.)
                        </div>
                        <div style={{
                            border: '2px dashed rgba(255,255,255,0.15)',
                            borderRadius: 12,
                            padding: 24,
                            textAlign: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                        }}
                            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = '#10b98166'; }}
                            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.15)'; }}
                            onClick={() => {
                                // Simulate document upload
                                const newDocs = [...documents, `document_${documents.length + 1}.pdf`];
                                setDocuments(newDocs);
                            }}
                        >
                            <div style={{ fontSize: '2rem', marginBottom: 8 }}>📎</div>
                            <div style={{ fontSize: '0.78rem', opacity: 0.7 }}>Click to upload documents</div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.4, marginTop: 4 }}>PDF, JPG, PNG accepted</div>
                        </div>
                        {documents.length > 0 && (
                            <div style={{ marginTop: 12 }}>
                                <div style={{ fontSize: '0.68rem', opacity: 0.5, marginBottom: 4 }}>Uploaded ({documents.length}):</div>
                                {documents.map((doc, i) => (
                                    <div key={i} style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        padding: '6px 10px',
                                        background: 'rgba(16,185,129,0.1)',
                                        borderRadius: 6,
                                        marginBottom: 4,
                                        fontSize: '0.72rem',
                                    }}>
                                        <span>📄 {doc}</span>
                                        <span style={{ color: '#10b981', cursor: 'pointer' }}
                                            onClick={() => setDocuments(docs => docs.filter((_, idx) => idx !== i))}>
                                            ✕
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Step 3: Review & Submit */}
            {step === 3 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={CARD}>
                        <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: 12, color: '#10b981' }}>
                            📋 Review Your Application
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.78rem' }}>
                            <div><span style={{ opacity: 0.5 }}>Program:</span> <strong>{selectedProg?.name}</strong></div>
                            <div><span style={{ opacity: 0.5 }}>Full Name:</span> <strong>{fullName}</strong></div>
                            <div><span style={{ opacity: 0.5 }}>Email:</span> <strong>{email}</strong></div>
                            <div><span style={{ opacity: 0.5 }}>Phone:</span> <strong>{phone || 'Not provided'}</strong></div>
                            <div><span style={{ opacity: 0.5 }}>Nationality:</span> <strong>{nationality}</strong></div>
                            <div><span style={{ opacity: 0.5 }}>Documents:</span> <strong>{documents.length} files</strong></div>
                            {reason && <div><span style={{ opacity: 0.5 }}>Reason:</span> <strong>{reason}</strong></div>}
                        </div>
                    </div>

                    <div style={CARD}>
                        <div style={LABEL}>Reason for Application (Optional)</div>
                        <textarea
                            value={reason}
                            onChange={e => setReason(e.target.value)}
                            style={{ ...INPUT, minHeight: 80, resize: 'vertical' }}
                            placeholder="Why are you applying for e-Residency?"
                        />
                    </div>

                    {error && (
                        <div style={{ padding: 12, background: 'rgba(239,68,68,0.1)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '0.78rem' }}>
                            {error}
                        </div>
                    )}
                </div>
            )}

            {/* Step 4: Success */}
            {step === 4 && (
                <div style={{ textAlign: 'center', padding: 32 }}>
                    <div style={{ fontSize: '3rem', marginBottom: 12 }}>🎉</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10b981', marginBottom: 8 }}>
                        Application Submitted!
                    </div>
                    <div style={{ fontSize: '0.78rem', opacity: 0.7, lineHeight: 1.6 }}>
                        Your e-Residency application has been received. You will be notified
                        once it is processed. This typically takes {selectedProg?.duration_days || 14} business days.
                    </div>
                </div>
            )}

            {/* Navigation Buttons */}
            {step < 4 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
                    <button
                        onClick={() => setStep(s => Math.max(0, s - 1))}
                        disabled={step === 0}
                        style={{
                            padding: '10px 20px',
                            borderRadius: 8,
                            border: '1px solid rgba(255,255,255,0.1)',
                            background: 'rgba(255,255,255,0.05)',
                            color: step === 0 ? 'rgba(255,255,255,0.2)' : '#e8e8e8',
                            cursor: step === 0 ? 'not-allowed' : 'pointer',
                            fontSize: '0.82rem',
                        }}
                    >
                        ← Back
                    </button>

                    {step < 3 ? (
                        <button
                            onClick={() => setStep(s => s + 1)}
                            disabled={!canProceed()}
                            style={{
                                padding: '10px 24px',
                                borderRadius: 8,
                                border: 'none',
                                background: canProceed() ? 'linear-gradient(135deg, #10b981, #059669)' : 'rgba(255,255,255,0.1)',
                                color: canProceed() ? 'white' : 'rgba(255,255,255,0.3)',
                                cursor: canProceed() ? 'pointer' : 'not-allowed',
                                fontSize: '0.82rem',
                                fontWeight: 600,
                            }}
                        >
                            Next →
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            disabled={submitting}
                            style={{
                                padding: '10px 24px',
                                borderRadius: 8,
                                border: 'none',
                                background: submitting ? 'rgba(16,185,129,0.5)' : 'linear-gradient(135deg, #10b981, #059669)',
                                color: 'white',
                                cursor: submitting ? 'not-allowed' : 'pointer',
                                fontSize: '0.82rem',
                                fontWeight: 600,
                            }}
                        >
                            {submitting ? 'Submitting...' : '📤 Submit Application'}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
