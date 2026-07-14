import React, { useState, useEffect } from 'react';
import { identityAPI, consensusV1API, svtAPI, hdtAPI } from '../../api/asimnexus';

const card = (extra: React.CSSProperties = {}): React.CSSProperties => ({
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 14, padding: 16, ...extra,
});
const btn = (color = '#667eea', extra: React.CSSProperties = {}): React.CSSProperties => ({
    background: `${color}22`, border: `1px solid ${color}44`,
    color, borderRadius: 8, padding: '8px 16px', cursor: 'pointer',
    fontSize: 13, fontWeight: 600, ...extra,
});
const input: React.CSSProperties = {
    background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: 13, width: '100%',
    outline: 'none', boxSizing: 'border-box',
};

interface IdentityData {
    did: string;
    display_name?: string;
    universe?: string;
    created_at?: string;
}

interface IdentityListItem {
    did: string;
    display_name?: string;
}

interface StatsData {
    total: number;
    active: number;
    algorithm?: string;
}

interface ConsStatsData {
    total: number;
    approved: number;
    rejected: number;
    pending_human: number;
    clone_count: number;
}

interface ConsRound {
    round_id: string;
    topic: string;
    summary?: string;
    outcome?: string;
    level?: string;
    created_at?: string;
}

interface HDTData {
    skills: number;
    verified_skills: number;
    reputation: number;
    dharma_score: number;
    autonomy_level: number;
    contracts_done: number;
}

interface SVTWalletData {
    exists: boolean;
    balance: number;
    earned_total: number;
    staked: number;
    pct_of_supply: number;
    tx_count: number;
}

export default function IdentityPanel() {
    const [tab, setTab] = useState('identity');
    const [identity, setIdentity] = useState<IdentityData | null>(null);
    const [idList, setIdList] = useState<IdentityListItem[]>([]);
    const [stats, setStats] = useState<StatsData | null>(null);
    const [consStats, setConsStats] = useState<ConsStatsData | null>(null);
    const [consList, setConsList] = useState<ConsRound[]>([]);
    const [pending, setPending] = useState<ConsRound[]>([]);
    const [hdt, setHdt] = useState<HDTData | null>(null);
    const [svtInfo, setSvtInfo] = useState<SVTWalletData | null>(null);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    const [form, setForm] = useState({
        passphrase: '', display_name: '', universe: 'personal', biometric_raw: ''
    });
    const [verifyForm, setVerifyForm] = useState({ did: '', passphrase: '' });
    const [voteForm, setVoteForm] = useState({ topic: '', description: '', level: 'high' });
    const [skillForm, setSkillForm] = useState({ name: '', level: 'expert' });
    const [mintForm, setMintForm] = useState({ amount: 100 });

    const load = async () => {
        try {
            const [st, li, cs, cl, pe] = await Promise.allSettled([
                identityAPI.getStats().then(r => r.data),
                identityAPI.getList().then(r => r.data),
                consensusV1API.getStats().then(r => r.data),
                consensusV1API.getList().then(r => r.data),
                consensusV1API.getPending().then(r => r.data),
            ]);
            if (st.status === 'fulfilled') setStats(st.value as unknown as StatsData);
            if (li.status === 'fulfilled') setIdList((li.value as unknown as { identities?: IdentityListItem[] })?.identities || []);
            if (cs.status === 'fulfilled') setConsStats(cs.value as unknown as ConsStatsData);
            if (cl.status === 'fulfilled') setConsList((cl.value as unknown as { rounds?: ConsRound[] })?.rounds?.slice(0, 10) || []);
            if (pe.status === 'fulfilled') setPending((pe.value as unknown as { rounds?: ConsRound[] })?.rounds || []);
        } catch { /* ignore */ }
    };

    useEffect(() => { load(); }, [tab]);

    const createIdentity = async () => {
        if (!form.passphrase || form.passphrase.length < 8) {
            setMsg('❌ Passphrase must be ≥ 8 characters'); return;
        }
        setLoading(true);
        try {
            const res = await identityAPI.create(form).then(r => r.data) as unknown as IdentityData;
            if (res.did) {
                setIdentity(res);
                setMsg(`✅ Identity created: ${res.did.slice(0, 28)}…`);
                await load();
                // Auto-create SVT wallet
                await svtAPI.createWallet(res.did);
                await svtAPI.mint(res.did, 500, 'Welcome bonus');
                const w = await svtAPI.getWallet(res.did).then(r => r.data) as unknown as SVTWalletData;
                setSvtInfo(w);
                // Auto-create HDT
                const h = await hdtAPI.create({
                    did: res.did, display_name: form.display_name, universe: form.universe
                }).then(r => r.data) as unknown as HDTData;
                setHdt(h);
            } else {
                setMsg(`❌ ${(res as unknown as { detail?: string }).detail || 'Error creating identity'}`);
            }
        } catch (e) { setMsg(`❌ ${(e as Error).message}`); }
        setLoading(false);
    };

    const verifyIdentity = async () => {
        setLoading(true);
        try {
            const res = await identityAPI.verify(verifyForm).then(r => r.data) as unknown as { verified: boolean; reason: string };
            setMsg(res.verified
                ? `✅ ${res.reason}`
                : `❌ ${res.reason}`);
        } catch (e) { setMsg(`❌ ${(e as Error).message}`); }
        setLoading(false);
    };

    const addSkill = async () => {
        const did = identity?.did || idList[0]?.did;
        if (!did) { setMsg('❌ Create identity first'); return; }
        setLoading(true);
        try {
            const res = await hdtAPI.addSkill(did, skillForm).then(r => r.data) as unknown as { name: string; level: string };
            setMsg(`✅ Skill added: ${res.name} [${res.level}]`);
            const h = await hdtAPI.getStatus(did).then(r => r.data) as unknown as HDTData;
            setHdt(h);
        } catch (e) { setMsg(`❌ ${(e as Error).message}`); }
        setLoading(false);
    };

    const startVote = async () => {
        if (!voteForm.topic) { setMsg('❌ Topic required'); return; }
        setLoading(true);
        try {
            const res = await consensusV1API.vote(voteForm.topic, voteForm.description, voteForm.level).then(r => r.data) as unknown as { outcome: string; summary: string };
            setMsg(`${res.outcome === 'approved' ? '✅' : '❌'} ${res.summary}`);
            await load();
        } catch (e) { setMsg(`❌ ${(e as Error).message}`); }
        setLoading(false);
    };

    const overrideConsensus = async (round_id: string, approved: boolean) => {
        setLoading(true);
        try {
            const res = await consensusV1API.override(round_id, approved, approved ? 'Human approved' : 'Human rejected').then(r => r.data) as unknown as { outcome: string };
            setMsg(`👤 Override: ${res.outcome}`);
            await load();
        } catch (e) { setMsg(`❌ ${(e as Error).message}`); }
        setLoading(false);
    };

    const mintTokens = async () => {
        const did = identity?.did || idList[0]?.did;
        if (!did) { setMsg('❌ Create identity first'); return; }
        setLoading(true);
        try {
            await svtAPI.mint(did, Number(mintForm.amount), 'Manual mint').then(r => r.data);
            setMsg(`✅ Minted ${mintForm.amount} SVT`);
            const w = await svtAPI.getWallet(did).then(r => r.data) as unknown as SVTWalletData;
            setSvtInfo(w);
        } catch (e) { setMsg(`❌ ${(e as Error).message}`); }
        setLoading(false);
    };

    const activeDid = identity?.did || idList[0]?.did || '';
    const TABS = [
        { id: 'identity', label: '🔐 ZKP Identity' },
        { id: 'hdt', label: '👤 Digital Twin' },
        { id: 'token', label: '💰 SVT Token' },
        { id: 'consensus', label: '🗳️ Consensus' },
    ];

    return (
        <div style={{ color: '#fff', fontFamily: 'system-ui,sans-serif', maxWidth: 860 }}>

            <h2 style={{ margin: '0 0 4px', fontSize: 22, background: 'linear-gradient(135deg,#667eea,#a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                🔐 Sovereign Identity & Governance
            </h2>
            <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 20px' }}>
                Zero-Knowledge Proof · Human Digital Twin · 15-Clone Consensus · Sovereign Token
            </p>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
                {TABS.map(t => (
                    <button key={t.id} onClick={() => setTab(t.id)} style={{
                        ...btn(tab === t.id ? '#667eea' : '#64748b'),
                        background: tab === t.id ? 'rgba(102,126,234,0.2)' : 'transparent',
                    }}>{t.label}</button>
                ))}
            </div>

            {msg && (
                <div style={{
                    padding: '10px 14px', borderRadius: 10, marginBottom: 16,
                    background: msg.startsWith('✅') ? 'rgba(52,211,153,0.12)' : 'rgba(239,68,68,0.12)',
                    border: `1px solid ${msg.startsWith('✅') ? 'rgba(52,211,153,0.3)' : 'rgba(239,68,68,0.3)'}`,
                    color: msg.startsWith('✅') ? '#34d399' : '#f87171', fontSize: 13,
                }}>
                    {msg} <button onClick={() => setMsg('')} style={{ marginLeft: 8, cursor: 'pointer', background: 'none', border: 'none', color: 'inherit' }}>✕</button>
                </div>
            )}

            {/* ── IDENTITY TAB ── */}
            {tab === 'identity' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div style={card()}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Create ZKP Identity</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <input placeholder="Display name" style={input} value={form.display_name}
                                onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))} />
                            <input type="password" placeholder="Passphrase (≥8 chars)" style={input}
                                value={form.passphrase}
                                onChange={e => setForm(f => ({ ...f, passphrase: e.target.value }))} />
                            <select style={{ ...input, color: form.universe ? '#fff' : '#64748b' }}
                                value={form.universe} onChange={e => setForm(f => ({ ...f, universe: e.target.value }))}>
                                {['personal', 'family', 'community', 'enterprise', 'sovereign'].map(u =>
                                    <option key={u} value={u}>{u}</option>)}
                            </select>
                            <input placeholder="Biometric hash (optional)" style={input}
                                value={form.biometric_raw}
                                onChange={e => setForm(f => ({ ...f, biometric_raw: e.target.value }))} />
                            <button onClick={createIdentity} disabled={loading} style={btn('#667eea', { width: '100%' })}>
                                {loading ? '…' : '🆔 Create Sovereign Identity'}
                            </button>
                        </div>
                    </div>

                    <div style={card()}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Verify ZKP Identity</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <select style={{ ...input, color: verifyForm.did ? '#fff' : '#64748b' }}
                                value={verifyForm.did} onChange={e => setVerifyForm(f => ({ ...f, did: e.target.value }))}>
                                <option value="">Select identity…</option>
                                {idList.map(i => <option key={i.did} value={i.did}>{i.display_name} ({i.did.slice(0, 20)}…)</option>)}
                            </select>
                            <input type="password" placeholder="Passphrase" style={input}
                                value={verifyForm.passphrase}
                                onChange={e => setVerifyForm(f => ({ ...f, passphrase: e.target.value }))} />
                            <button onClick={verifyIdentity} disabled={loading} style={btn('#34d399', { width: '100%' })}>
                                {loading ? '…' : '🔍 Verify (Zero-Knowledge)'}
                            </button>
                        </div>

                        {identity && (
                            <div style={{ marginTop: 16, padding: 12, borderRadius: 10, background: 'rgba(102,126,234,0.08)', border: '1px solid rgba(102,126,234,0.2)' }}>
                                <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>Active Identity</div>
                                <div style={{ fontSize: 12, color: '#a78bfa', wordBreak: 'break-all' }}>{identity.did}</div>
                                <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{identity.universe} · created {identity.created_at?.slice(0, 10)}</div>
                            </div>
                        )}

                        {stats && (
                            <div style={{ marginTop: 12, fontSize: 11, color: '#64748b' }}>
                                Total: {stats.total} · Active: {stats.active} · Algorithm: {stats.algorithm?.split('+')[0]}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── HDT TAB ── */}
            {tab === 'hdt' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div style={card()}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Add Skill to Digital Twin</div>
                        <div style={{ fontSize: 11, color: '#64748b', marginBottom: 10 }}>
                            DID: {activeDid ? activeDid.slice(0, 28) + '…' : 'No identity yet'}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <input placeholder="Skill name (e.g. python, farming)" style={input}
                                value={skillForm.name}
                                onChange={e => setSkillForm(f => ({ ...f, name: e.target.value }))} />
                            <select style={input} value={skillForm.level}
                                onChange={e => setSkillForm(f => ({ ...f, level: e.target.value }))}>
                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="expert">Expert</option>
                            </select>
                            <button onClick={addSkill} disabled={loading} style={btn('#10b981', { width: '100%' })}>
                                {loading ? '…' : '➕ Add Skill'}
                            </button>
                        </div>

                        <button onClick={async () => {
                            if (!activeDid) return;
                            const res = await hdtAPI.announce(activeDid).then(r => r.data) as unknown as { skills?: number; reason?: string };
                            setMsg(res.skills ? `✅ Announced ${res.skills} skills to DHT` : `❌ ${res.reason || 'error'}`);
                        }} style={{ ...btn('#60a5fa', { width: '100%', marginTop: 8 }) }}>
                            📢 Announce Skills to Mesh
                        </button>
                    </div>

                    <div style={card()}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Digital Twin Status</div>
                        {hdt ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Skills</span>
                                    <span style={{ color: '#fff', fontWeight: 700 }}>{hdt.skills}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Verified</span>
                                    <span style={{ color: '#34d399', fontWeight: 700 }}>{hdt.verified_skills}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Reputation</span>
                                    <span style={{ color: '#f59e0b', fontWeight: 700 }}>{hdt.reputation}/5.0</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Dharma Score</span>
                                    <span style={{ color: '#a78bfa', fontWeight: 700 }}>{hdt.dharma_score}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Autonomy Level</span>
                                    <span style={{ color: '#60a5fa', fontWeight: 700 }}>{hdt.autonomy_level}/5</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Contracts Done</span>
                                    <span style={{ color: '#34d399', fontWeight: 700 }}>{hdt.contracts_done}</span>
                                </div>
                            </div>
                        ) : (
                            <div style={{ color: '#64748b', fontSize: 12 }}>
                                Create an identity first to initialize your Digital Twin.
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── TOKEN TAB ── */}
            {tab === 'token' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div style={card()}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>💰 Mint SVT Tokens</div>
                        <div style={{ fontSize: 11, color: '#64748b', marginBottom: 10 }}>
                            Wallet: {activeDid ? activeDid.slice(0, 24) + '…' : 'No identity'}
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <input type="number" min="1" max="10000" style={{ ...input, flex: 1 }}
                                value={mintForm.amount}
                                onChange={e => setMintForm({ amount: Number(e.target.value) })} />
                            <button onClick={mintTokens} disabled={loading} style={btn('#fb923c')}>
                                {loading ? '…' : 'Mint'}
                            </button>
                        </div>
                        <div style={{ fontSize: 11, color: '#64748b', marginTop: 8 }}>
                            1% burned on every transfer · Max wallet: 1,000,000 SVT · Anti-concentration cap: 15%
                        </div>
                    </div>

                    <div style={card()}>
                        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Wallet Info</div>
                        {svtInfo && svtInfo.exists ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Balance</span>
                                    <span style={{ color: '#fb923c', fontWeight: 800, fontSize: 18 }}>{Number(svtInfo.balance).toLocaleString()} SVT</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Earned Total</span>
                                    <span style={{ color: '#34d399' }}>{Number(svtInfo.earned_total).toLocaleString()}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Staked (Escrow)</span>
                                    <span style={{ color: '#60a5fa' }}>{Number(svtInfo.staked).toLocaleString()}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>% of Supply</span>
                                    <span style={{ color: '#a78bfa' }}>{svtInfo.pct_of_supply}%</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: '#94a3b8', fontSize: 12 }}>Transactions</span>
                                    <span style={{ color: '#fff' }}>{svtInfo.tx_count}</span>
                                </div>
                            </div>
                        ) : (
                            <div style={{ color: '#64748b', fontSize: 12 }}>
                                {activeDid ? 'Loading wallet…' : 'Create identity to get wallet'}
                            </div>
                        )}
                        {activeDid && !svtInfo && (
                            <button onClick={async () => {
                                const w = await svtAPI.getWallet(activeDid).then(r => r.data) as unknown as SVTWalletData;
                                setSvtInfo(w);
                            }} style={btn('#fb923c', { width: '100%', marginTop: 8 })}>
                                Load Wallet
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* ── CONSENSUS TAB ── */}
            {tab === 'consensus' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                        <div style={card()}>
                            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>🗳️ Start Consensus Vote</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <input placeholder="Decision topic…" style={input}
                                    value={voteForm.topic}
                                    onChange={e => setVoteForm(f => ({ ...f, topic: e.target.value }))} />
                                <textarea placeholder="Description…" style={{ ...input, minHeight: 60, resize: 'vertical' }}
                                    value={voteForm.description}
                                    onChange={e => setVoteForm(f => ({ ...f, description: e.target.value }))} />
                                <select style={input} value={voteForm.level}
                                    onChange={e => setVoteForm(f => ({ ...f, level: e.target.value }))}>
                                    <option value="high">HIGH — 8/15 majority</option>
                                    <option value="critical">CRITICAL — 11/15 supermajority</option>
                                    <option value="sovereignty">SOVEREIGNTY — 15/15 + Human</option>
                                </select>
                                <button onClick={startVote} disabled={loading} style={btn('#a78bfa', { width: '100%' })}>
                                    {loading ? '…' : '🗳️ Call 15-Clone Vote'}
                                </button>
                            </div>
                        </div>

                        <div style={card()}>
                            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Stats</div>
                            {consStats ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {([
                                        ['Total rounds', consStats.total, '#fff'],
                                        ['Approved', consStats.approved, '#34d399'],
                                        ['Rejected', consStats.rejected, '#f87171'],
                                        ['Pending human', consStats.pending_human, '#fb923c'],
                                        ['Clone count', consStats.clone_count, '#a78bfa'],
                                    ] as [string, number, string][]).map(([l, v, c]) => (
                                        <div key={l} style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <span style={{ color: '#94a3b8', fontSize: 12 }}>{l}</span>
                                            <span style={{ color: c, fontWeight: 700 }}>{v}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : <div style={{ color: '#64748b', fontSize: 12 }}>No votes yet</div>}
                        </div>
                    </div>

                    {pending.length > 0 && (
                        <div style={card({ borderColor: 'rgba(251,146,60,0.3)' })}>
                            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: '#fb923c' }}>
                                ⚠️ Pending Human Override ({pending.length})
                            </div>
                            {pending.map(r => (
                                <div key={r.round_id} style={{ padding: 10, borderRadius: 8, background: 'rgba(251,146,60,0.06)', border: '1px solid rgba(251,146,60,0.15)', marginBottom: 8 }}>
                                    <div style={{ fontSize: 13, fontWeight: 600 }}>{r.topic}</div>
                                    <div style={{ fontSize: 11, color: '#94a3b8', margin: '4px 0 8px' }}>{r.summary?.slice(0, 100)}</div>
                                    <div style={{ display: 'flex', gap: 8 }}>
                                        <button onClick={() => overrideConsensus(r.round_id, true)}
                                            style={btn('#34d399')}>✅ Approve</button>
                                        <button onClick={() => overrideConsensus(r.round_id, false)}
                                            style={btn('#f87171')}>❌ Reject</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {consList.length > 0 && (
                        <div style={card()}>
                            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Recent Votes</div>
                            {consList.map(r => (
                                <div key={r.round_id} style={{
                                    padding: '8px 12px', borderRadius: 8, marginBottom: 6,
                                    background: r.outcome === 'approved' ? 'rgba(52,211,153,0.06)' : 'rgba(239,68,68,0.06)',
                                    border: `1px solid ${r.outcome === 'approved' ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.2)'}`,
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                }}>
                                    <div>
                                        <div style={{ fontSize: 12, fontWeight: 600 }}>{r.topic}</div>
                                        <div style={{ fontSize: 10, color: '#64748b' }}>{r.level} · {r.created_at?.slice(0, 10)}</div>
                                    </div>
                                    <span style={{
                                        fontSize: 11, padding: '3px 8px', borderRadius: 6,
                                        background: r.outcome === 'approved' ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.2)',
                                        color: r.outcome === 'approved' ? '#34d399' : '#f87171',
                                    }}>{r.outcome}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
