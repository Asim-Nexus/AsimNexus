import React, { useState, useEffect } from 'react';
import api from '../../api/asimnexus';

const STATUS_META: Record<string, { icon: string; color: string }> = {
    proposed: { icon: '📄', color: '#f59e0b' },
    gate2_signed: { icon: '✍️', color: '#3b82f6' },
    active: { icon: '✅', color: '#10b981' },
    completed: { icon: '🏁', color: '#667eea' },
    paused: { icon: '⏸️', color: '#8b5cf6' },
    cancelled: { icon: '❌', color: '#ef4444' },
};

const card: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)', borderRadius: 14,
    border: '1px solid rgba(255,255,255,0.06)', padding: 20,
};

const btn = (color = '#667eea', small = false): React.CSSProperties => ({
    padding: small ? '6px 14px' : '10px 20px', borderRadius: 8, cursor: 'pointer',
    fontWeight: 600, border: 'none', fontSize: small ? '0.72rem' : '0.82rem',
    background: `${color}22`, color,
});

const input: React.CSSProperties = {
    padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)',
    background: 'rgba(0,0,0,0.3)', color: '#fff', fontSize: '0.85rem', outline: 'none',
    width: '100%', boxSizing: 'border-box',
};

interface ContractsPanelProps {
    user?: Record<string, unknown>;
}

interface ContractData {
    id?: string;
    title?: string;
    description?: string;
    status?: string;
    budget?: number;
    client?: string;
    provider?: string;
    created_at?: string;
    signed_by_client?: boolean;
    signed_by_provider?: boolean;
}

export default function ContractsPanel({ user: _user }: ContractsPanelProps) {
    const [contracts, setContracts] = useState<ContractData[]>([]);
    const [loading, setLoading] = useState(true);
    const [msg, setMsg] = useState('');
    const [form, setForm] = useState({
        title: '', description: '', budget: '', provider: '',
    });

    const fetchContracts = async () => {
        try {
            const r = await api.get('/api/contracts/list') as unknown as { data?: { contracts?: ContractData[] } };
            if (r.data?.contracts) setContracts(r.data.contracts);
        } catch { /* ignore */ }
        setLoading(false);
    };

    useEffect(() => { fetchContracts(); }, []);

    const post = async (path: string, body: Record<string, unknown> = {}) => {
        try {
            const r = await api.post(path, body) as unknown as { data?: { success?: boolean; detail?: string } };
            if (r.data?.success) {
                setMsg('Success!');
                fetchContracts();
            } else {
                setMsg(r.data?.detail || 'Error');
            }
        } catch { setMsg('Request failed'); }
    };

    const handlePropose = async () => {
        if (!form.title.trim()) { setMsg('Title required'); return; }
        setMsg('');
        const c = await api.post('/api/contracts/propose', {
            title: form.title, description: form.description,
            budget: parseFloat(form.budget) || 0, provider: form.provider,
        }) as unknown as { data?: { success?: boolean; detail?: string } };
        if (c.data?.success) {
            setMsg('Contract proposed!');
            setForm({ title: '', description: '', budget: '', provider: '' });
            fetchContracts();
        } else {
            setMsg(c.data?.detail || 'Failed');
        }
    };

    const handleGate2 = async (id: string) => {
        await post('/api/contracts/gate2', { contract_id: id });
    };

    const handleSign = async (id: string, approved: boolean) => {
        await post('/api/contracts/sign', { contract_id: id, approved });
    };

    const handleComplete = async (id: string) => {
        await post('/api/contracts/complete', { contract_id: id });
    };

    const handlePause = async (id: string) => {
        await post('/api/contracts/pause', { contract_id: id });
    };

    const handleResume = async (id: string) => {
        await post('/api/contracts/resume', { contract_id: id });
    };

    const handleCancel = async (id: string) => {
        if (!window.confirm('Are you sure you want to cancel this contract?')) return;
        await post('/api/contracts/cancel', { contract_id: id });
    };

    return (
        <div style={{ color: '#fff', fontFamily: 'inherit' }}>
            <div style={{
                fontSize: '1.2rem', fontWeight: 700, marginBottom: 16,
                background: 'linear-gradient(135deg, #667eea, #a78bfa)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
                📜 HDT Smart Contracts
            </div>

            {/* Propose Form */}
            <div style={{ ...card, marginBottom: 16 }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12 }}>Propose New Contract</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <input style={input} placeholder="Contract Title" value={form.title}
                        onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
                    <textarea style={{ ...input, minHeight: 60, resize: 'vertical' as const, fontFamily: 'inherit' }}
                        placeholder="Description" value={form.description}
                        onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
                    <div style={{ display: 'flex', gap: 10 }}>
                        <input style={{ ...input, flex: 1 }} placeholder="Budget ($)" type="number" value={form.budget}
                            onChange={e => setForm(f => ({ ...f, budget: e.target.value }))} />
                        <input style={{ ...input, flex: 1 }} placeholder="Provider (email or DID)" value={form.provider}
                            onChange={e => setForm(f => ({ ...f, provider: e.target.value }))} />
                    </div>
                    <button style={btn()} onClick={handlePropose}>Propose Contract</button>
                </div>
            </div>

            {msg && (
                <div style={{
                    padding: '8px 14px', borderRadius: 8, fontSize: '0.8rem', marginBottom: 12,
                    background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#10b981',
                }}>{msg}</div>
            )}

            {/* Contracts List */}
            <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12 }}>
                Contracts ({contracts.length})
            </div>

            {loading && <div style={{ opacity: 0.5, textAlign: 'center', padding: 20 }}>Loading...</div>}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {contracts.map(c => {
                    const meta = STATUS_META[c.status || ''] || { icon: '❓', color: '#888' };
                    return (
                        <div key={c.id} style={card}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{c.title}</div>
                                    <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: 2 }}>
                                        {c.client} → {c.provider} · ${c.budget}
                                    </div>
                                </div>
                                <span style={{
                                    fontSize: '0.72rem', padding: '3px 10px', borderRadius: 12,
                                    background: `${meta.color}22`, color: meta.color, fontWeight: 600,
                                }}>
                                    {meta.icon} {c.status}
                                </span>
                            </div>

                            {c.description && (
                                <div style={{ fontSize: '0.78rem', opacity: 0.6, marginBottom: 10 }}>
                                    {c.description}
                                </div>
                            )}

                            {/* Action buttons based on status */}
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                {c.status === 'proposed' && (
                                    <>
                                        <button style={btn('#3b82f6', true)} onClick={() => { if (c.id) handleGate2(c.id); }}>Gate 2 →</button>
                                        <button style={btn('#ef4444', true)} onClick={() => { if (c.id) handleCancel(c.id); }}>Cancel</button>
                                    </>
                                )}
                                {c.status === 'gate2_signed' && (
                                    <>
                                        <button style={btn('#10b981', true)} onClick={() => { if (c.id) handleSign(c.id, true); }}>✓ Sign</button>
                                        <button style={btn('#ef4444', true)} onClick={() => { if (c.id) handleSign(c.id, false); }}>✕ Reject</button>
                                    </>
                                )}
                                {c.status === 'active' && (
                                    <>
                                        <button style={btn('#10b981', true)} onClick={() => { if (c.id) handleComplete(c.id); }}>✓ Complete</button>
                                        <button style={btn('#8b5cf6', true)} onClick={() => { if (c.id) handlePause(c.id); }}>⏸ Pause</button>
                                        <button style={btn('#ef4444', true)} onClick={() => { if (c.id) handleCancel(c.id); }}>Cancel</button>
                                    </>
                                )}
                                {c.status === 'paused' && (
                                    <button style={btn('#10b981', true)} onClick={() => { if (c.id) handleResume(c.id); }}>▶ Resume</button>
                                )}
                            </div>

                            <div style={{ fontSize: '0.68rem', opacity: 0.35, marginTop: 8 }}>
                                Created: {c.created_at?.slice(0, 10)}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
