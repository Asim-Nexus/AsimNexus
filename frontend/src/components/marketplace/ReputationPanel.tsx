import React, { useState, useEffect } from 'react';
import { reputationAPI } from '../../api/asimnexus';

interface ReputationPanelProps {
    user?: Record<string, unknown>;
}

interface EntityData {
    entity_id: string;
    level: string;
    score: number;
    staked_amount: number;
    total_earned: number;
    total_lost: number;
    [key: string]: unknown;
}

interface EventData {
    event_type: string;
    amount: number;
    reason: string;
    [key: string]: unknown;
}

interface StatsData {
    total_entities?: number;
    total_staked?: number;
    active_stakes?: number;
    average_score?: number;
    [key: string]: unknown;
}

const LEVEL_COLORS: Record<string, string> = {
    new: '#6b7280', bronze: '#b45309', silver: '#9ca3af',
    gold: '#f59e0b', platinum: '#14b8a6', diamond: '#8b5cf6',
};

const ReputationPanel: React.FC<ReputationPanelProps> = ({ user: _user }) => {
    const [tab, setTab] = useState<string>('leaderboard');
    const [stats, setStats] = useState<StatsData | null>(null);
    const [leaderboard, setLeaderboard] = useState<EntityData[]>([]);
    const [entityId, setEntityId] = useState<string>('');
    const [entity, setEntity] = useState<EntityData | null>(null);
    const [events, setEvents] = useState<EventData[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [msg, setMsg] = useState<string>('');
    const [amount, setAmount] = useState<number>(10);
    const [reason, setReason] = useState<string>('');

    const fetchStats = async () => {
        try {
            const r = await reputationAPI.getStats();
            const response = r as unknown as { data?: StatsData };
            setStats(response.data || null);
        } catch { /* ignore */ }
    };

    const fetchLeaderboard = async () => {
        try {
            const r = await reputationAPI.getLeaderboard(20);
            const response = r as unknown as { data?: { leaderboard?: EntityData[] } };
            setLeaderboard(response.data?.leaderboard || []);
        } catch { /* ignore */ }
    };

    useEffect(() => { fetchStats(); fetchLeaderboard(); }, []);

    const lookupEntity = async () => {
        if (!entityId.trim()) return;
        setLoading(true);
        try {
            const r = await reputationAPI.get(entityId);
            const response = r as unknown as { data?: EntityData };
            setEntity(response.data || null);
            const evR = await reputationAPI.getEvents(entityId, 20);
            const evResponse = evR as unknown as { data?: { events?: EventData[] } };
            setEvents(evResponse.data?.events || []);
            setMsg('');
        } catch {
            setMsg('Entity not found');
            setEntity(null);
        }
        setLoading(false);
    };

    const registerEntity = async () => {
        if (!entityId.trim()) return;
        try {
            const r = await reputationAPI.register(entityId);
            const d = r as unknown as { data?: { success?: boolean; detail?: string } };
            const data = d.data || {};
            setMsg(data.success ? `✅ Registered ${entityId}` : (data.detail || 'Error'));
            if (data.success) lookupEntity();
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }; message?: string };
            setMsg(err.response?.data?.detail || err.message || 'Error');
        }
    };

    const doAction = async (action: string) => {
        if (!entityId.trim()) return;
        try {
            let r;
            if (action === 'add') r = await reputationAPI.add(entityId, +amount, reason);
            else if (action === 'remove') r = await reputationAPI.remove(entityId, +amount, reason);
            else if (action === 'stake') r = await reputationAPI.stake(entityId, +amount, reason);
            else return;
            const d = r as unknown as { data?: { success?: boolean; detail?: string } };
            const data = d.data || {};
            setMsg(data.success ? `✅ ${action} success` : (data.detail || 'Error'));
            if (data.success) { lookupEntity(); fetchLeaderboard(); fetchStats(); }
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }; message?: string };
            setMsg(err.response?.data?.detail || err.message || 'Error');
        }
    };

    const s: Record<string, React.CSSProperties | ((active: boolean) => React.CSSProperties)> = {
        wrap: { padding: 24 },
        header: { marginBottom: 20 },
        title: {
            fontSize: '1.5rem', fontWeight: 700,
            background: 'linear-gradient(45deg, #f59e0b, #8b5cf6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        } as React.CSSProperties,
        tabs: { display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' },
        tab: (active: boolean): React.CSSProperties => ({
            padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem',
            background: active ? 'rgba(139,92,246,0.2)' : 'transparent',
            border: active ? '1px solid rgba(139,92,246,0.5)' : '1px solid rgba(255,255,255,0.1)',
            color: active ? '#8b5cf6' : 'rgba(255,255,255,0.6)',
        }),
        statsRow: { display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 },
        statCard: {
            background: 'var(--theme-card, rgba(255,255,255,0.05))',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 12, padding: '12px 18px', minWidth: 100, textAlign: 'center',
        },
        statNum: { fontSize: '1.4rem', fontWeight: 700, color: '#f59e0b' },
        statLabel: { fontSize: '0.7rem', opacity: 0.5 },
        input: {
            width: '100%', padding: '10px 14px', borderRadius: 8, marginBottom: 12,
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'var(--theme-text, #fff)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
        },
        btn: {
            padding: '8px 18px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: 'linear-gradient(135deg, #f59e0b, #8b5cf6)',
            color: '#fff', fontWeight: 600, fontSize: '0.85rem', marginRight: 8, marginBottom: 8,
        },
        card: {
            background: 'var(--theme-card, rgba(255,255,255,0.04))',
            border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: 16,
            marginBottom: 14,
        },
        listCard: {
            background: 'var(--theme-card, rgba(255,255,255,0.04))',
            border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: 14,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: 8,
        },
        msg: {
            padding: '10px 16px', borderRadius: 8, marginBottom: 14, fontSize: '0.85rem',
            background: 'rgba(139,92,246,0.12)', border: '1px solid rgba(139,92,246,0.3)',
        },
        grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 },
    };

    return (
        <div style={s.wrap as React.CSSProperties}>
            <div style={s.header as React.CSSProperties}>
                <div style={s.title as React.CSSProperties}>⭐ Reputation System</div>
                <div style={{ fontSize: '0.82rem', opacity: 0.5, marginTop: 4 }}>
                    Track reputation, stake, and leaderboard rankings
                </div>
            </div>

            {msg && <div style={s.msg as React.CSSProperties}>{msg} <span style={{ cursor: 'pointer', marginLeft: 8 }} onClick={() => setMsg('')}>✕</span></div>}

            {stats && (
                <div style={s.statsRow as React.CSSProperties}>
                    {([
                        ['Entities', stats.total_entities],
                        ['Total Staked', stats.total_staked],
                        ['Active Stakes', stats.active_stakes],
                        ['Avg Score', stats.average_score],
                    ] as [string, number | undefined][]).map(([l, v]) => (
                        <div key={l} style={s.statCard as React.CSSProperties}>
                            <div style={s.statNum as React.CSSProperties}>{v}</div>
                            <div style={s.statLabel as React.CSSProperties}>{l}</div>
                        </div>
                    ))}
                </div>
            )}

            <div style={s.tabs as React.CSSProperties}>
                {[['leaderboard', '🏆 Leaderboard'], ['lookup', '🔍 Lookup'], ['actions', '⚡ Actions'], ['register', '➕ Register']].map(([id, label]) => (
                    <button key={id} style={(s.tab as (active: boolean) => React.CSSProperties)(tab === id)} onClick={() => setTab(id)}>{label}</button>
                ))}
            </div>

            {tab === 'leaderboard' && (
                <div>
                    <div style={{ fontWeight: 600, marginBottom: 12, fontSize: '0.95rem' }}>Top 20 Reputation</div>
                    {leaderboard.map((e, i) => (
                        <div key={e.entity_id} style={s.listCard as React.CSSProperties}
                            onClick={() => { setEntityId(e.entity_id); setTab('lookup'); }}>
                            <div>
                                <span style={{ fontWeight: 600 }}>#{i + 1}</span>
                                <span style={{ marginLeft: 12, opacity: 0.8 }}>{e.entity_id}</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{
                                    padding: '2px 8px', borderRadius: 8, fontSize: '0.7rem',
                                    background: `${LEVEL_COLORS[e.level] || '#6b7280'}33`,
                                    color: LEVEL_COLORS[e.level] || '#6b7280',
                                    border: `1px solid ${LEVEL_COLORS[e.level] || '#6b7280'}66`,
                                }}>{e.level}</span>
                                <span style={{ fontWeight: 700, color: '#f59e0b' }}>{e.score}</span>
                            </div>
                        </div>
                    ))}
                    {leaderboard.length === 0 && <div style={{ opacity: 0.4, textAlign: 'center', padding: 40 }}>No entities registered yet</div>}
                </div>
            )}

            {tab === 'lookup' && (
                <div>
                    <input style={s.input as React.CSSProperties} placeholder="Entity ID (e.g. user_001, agent_007)"
                        value={entityId} onChange={e => setEntityId(e.target.value)} />
                    <button style={s.btn as React.CSSProperties} onClick={lookupEntity}>🔍 Lookup</button>
                    <button style={{ ...s.btn as React.CSSProperties, background: 'rgba(255,255,255,0.1)' }} onClick={registerEntity}>➕ Register if New</button>
                    {entity && (
                        <div style={s.card as React.CSSProperties}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                                <span style={{ fontWeight: 700 }}>{entity.entity_id}</span>
                                <span style={{
                                    padding: '3px 10px', borderRadius: 8, fontSize: '0.75rem',
                                    background: `${LEVEL_COLORS[entity.level] || '#6b7280'}33`,
                                    color: LEVEL_COLORS[entity.level] || '#6b7280',
                                    border: `1px solid ${LEVEL_COLORS[entity.level] || '#6b7280'}66`,
                                }}>{entity.level}</span>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.85rem' }}>
                                <span>Score: <strong>{entity.score}</strong></span>
                                <span>Staked: <strong>{entity.staked_amount}</strong></span>
                                <span>Total Earned: <strong>{entity.total_earned}</strong></span>
                                <span>Total Lost: <strong>{entity.total_lost}</strong></span>
                            </div>
                        </div>
                    )}
                    {events.length > 0 && (
                        <div>
                            <div style={{ fontWeight: 600, marginTop: 16, marginBottom: 8, fontSize: '0.9rem' }}>Recent Events</div>
                            {events.slice(0, 10).map((ev, i) => (
                                <div key={i} style={{ padding: '6px 0', fontSize: '0.78rem', borderBottom: '1px solid rgba(255,255,255,0.04)', display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.6 }}>{ev.event_type}</span>
                                    <span style={{ color: ev.amount >= 0 ? '#10b981' : '#ef4444' }}>{ev.amount > 0 ? '+' : ''}{ev.amount}</span>
                                    <span style={{ opacity: 0.4, fontSize: '0.7rem' }}>{ev.reason}</span>
                                </div>
                            ))}
                        </div>
                    )}
                    {!entity && !loading && <div style={{ opacity: 0.4, textAlign: 'center', padding: 20 }}>Enter an entity ID to look up</div>}
                </div>
            )}

            {tab === 'actions' && (
                <div>
                    <input style={s.input as React.CSSProperties} placeholder="Entity ID"
                        value={entityId} onChange={e => setEntityId(e.target.value)} />
                    <input style={s.input as React.CSSProperties} type="number" placeholder="Amount"
                        value={amount} onChange={e => setAmount(+e.target.value)} />
                    <input style={s.input as React.CSSProperties} placeholder="Reason (optional)"
                        value={reason} onChange={e => setReason(e.target.value)} />
                    <button style={s.btn as React.CSSProperties} onClick={() => doAction('add')}>⭐ Add Reputation</button>
                    <button style={{ ...s.btn as React.CSSProperties, background: 'linear-gradient(135deg, #ef4444, #b45309)' }} onClick={() => doAction('remove')}>⬇️ Remove</button>
                    <button style={{ ...s.btn as React.CSSProperties, background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' }} onClick={() => doAction('stake')}>🔒 Stake</button>
                    <div style={{ fontSize: '0.72rem', opacity: 0.4, marginTop: 8 }}>For unstaking and slashing, use the API directly.</div>
                </div>
            )}

            {tab === 'register' && (
                <div>
                    <input style={s.input as React.CSSProperties} placeholder="New Entity ID"
                        value={entityId} onChange={e => setEntityId(e.target.value)} />
                    <button style={s.btn as React.CSSProperties} onClick={registerEntity}>➕ Register Entity</button>
                </div>
            )}
        </div>
    );
};

export default ReputationPanel;
