import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function authHeaders() {
  const token = localStorage.getItem('asimnexus_token');
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

const LEVEL_COLORS = {
  new: '#6b7280', bronze: '#b45309', silver: '#9ca3af',
  gold: '#f59e0b', platinum: '#14b8a6', diamond: '#8b5cf6',
};

export default function ReputationPanel({ user }) {
  const [tab, setTab] = useState('leaderboard');
  const [stats, setStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [entityId, setEntityId] = useState('');
  const [entity, setEntity] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [amount, setAmount] = useState(10);
  const [reason, setReason] = useState('');

  const fetchStats = async () => {
    try {
      const r = await fetch(`${API}/api/reputation/stats`, { headers: authHeaders() });
      const d = await r.json();
      setStats(d);
    } catch {}
  };

  const fetchLeaderboard = async () => {
    try {
      const r = await fetch(`${API}/api/reputation/leaderboard?limit=20`, { headers: authHeaders() });
      const d = await r.json();
      setLeaderboard(d.leaderboard || []);
    } catch {}
  };

  useEffect(() => { fetchStats(); fetchLeaderboard(); }, []);

  const lookupEntity = async () => {
    if (!entityId.trim()) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/reputation/${entityId}`, { headers: authHeaders() });
      if (r.ok) {
        const d = await r.json();
        setEntity(d);
        const evR = await fetch(`${API}/api/reputation/${entityId}/events?limit=20`, { headers: authHeaders() });
        const evD = await evR.json();
        setEvents(evD.events || []);
        setMsg('');
      } else {
        setMsg('Entity not found');
        setEntity(null);
      }
    } catch (e) { setMsg(e.message); }
    setLoading(false);
  };

  const registerEntity = async () => {
    if (!entityId.trim()) return;
    try {
      const r = await fetch(`${API}/api/reputation/register`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ entity_id: entityId }),
      });
      const d = await r.json();
      setMsg(d.success ? `✅ Registered ${entityId}` : (d.detail || 'Error'));
      if (d.success) lookupEntity();
    } catch (e) { setMsg(e.message); }
  };

  const doAction = async (action) => {
    if (!entityId.trim()) return;
    try {
      const r = await fetch(`${API}/api/reputation/${action}`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ entity_id: entityId, amount: +amount, reason }),
      });
      const d = await r.json();
      setMsg(d.success ? `✅ ${action} success` : (d.detail || 'Error'));
      if (d.success) { lookupEntity(); fetchLeaderboard(); fetchStats(); }
    } catch (e) { setMsg(e.message); }
  };

  const s = {
    wrap: { padding: 24 },
    header: { marginBottom: 20 },
    title: {
      fontSize: '1.5rem', fontWeight: 700,
      background: 'linear-gradient(45deg, #f59e0b, #8b5cf6)',
      WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
    },
    tabs: { display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' },
    tab: (active) => ({
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
    <div style={s.wrap}>
      <div style={s.header}>
        <div style={s.title}>⭐ Reputation System</div>
        <div style={{ fontSize: '0.82rem', opacity: 0.5, marginTop: 4 }}>
          Track reputation, stake, and leaderboard rankings
        </div>
      </div>

      {msg && <div style={s.msg}>{msg} <span style={{ cursor: 'pointer', marginLeft: 8 }} onClick={() => setMsg('')}>✕</span></div>}

      {stats && (
        <div style={s.statsRow}>
          {[
            ['Entities', stats.total_entities],
            ['Total Staked', stats.total_staked],
            ['Active Stakes', stats.active_stakes],
            ['Avg Score', stats.average_score],
          ].map(([l, v]) => (
            <div key={l} style={s.statCard}>
              <div style={s.statNum}>{v}</div>
              <div style={s.statLabel}>{l}</div>
            </div>
          ))}
        </div>
      )}

      <div style={s.tabs}>
        {[['leaderboard', '🏆 Leaderboard'], ['lookup', '🔍 Lookup'], ['actions', '⚡ Actions'], ['register', '➕ Register']].map(([id, label]) => (
          <button key={id} style={s.tab(tab === id)} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {tab === 'leaderboard' && (
        <div>
          <div style={{ fontWeight: 600, marginBottom: 12, fontSize: '0.95rem' }}>Top 20 Reputation</div>
          {leaderboard.map((e, i) => (
            <div key={e.entity_id} style={{ ...s.listCard, cursor: 'pointer' }}
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
          <input style={s.input} placeholder="Entity ID (e.g. user_001, agent_007)"
            value={entityId} onChange={e => setEntityId(e.target.value)} />
          <button style={s.btn} onClick={lookupEntity}>🔍 Lookup</button>
          <button style={{ ...s.btn, background: 'rgba(255,255,255,0.1)' }} onClick={registerEntity}>➕ Register if New</button>
          {entity && (
            <div style={s.card}>
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
          <input style={s.input} placeholder="Entity ID"
            value={entityId} onChange={e => setEntityId(e.target.value)} />
          <input style={s.input} type="number" placeholder="Amount"
            value={amount} onChange={e => setAmount(+e.target.value)} />
          <input style={s.input} placeholder="Reason (optional)"
            value={reason} onChange={e => setReason(e.target.value)} />
          <button style={s.btn} onClick={() => doAction('add')}>⭐ Add Reputation</button>
          <button style={{ ...s.btn, background: 'linear-gradient(135deg, #ef4444, #b45309)' }} onClick={() => doAction('remove')}>⬇️ Remove</button>
          <button style={{ ...s.btn, background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' }} onClick={() => doAction('stake')}>🔒 Stake</button>
          <div style={{ fontSize: '0.72rem', opacity: 0.4, marginTop: 8 }}>For unstaking and slashing, use the API directly.</div>
        </div>
      )}

      {tab === 'register' && (
        <div>
          <input style={s.input} placeholder="New Entity ID"
            value={entityId} onChange={e => setEntityId(e.target.value)} />
          <button style={s.btn} onClick={registerEntity}>➕ Register Entity</button>
        </div>
      )}
    </div>
  );
}
