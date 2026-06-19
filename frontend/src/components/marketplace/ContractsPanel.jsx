import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const STATUS_META = {
  proposed:      { color: '#a78bfa', label: 'Proposed',       icon: '📄' },
  gate1_pass:    { color: '#60a5fa', label: 'AI Checked',      icon: '🤖' },
  gate2_pass:    { color: '#f59e0b', label: 'Dharma Checked',  icon: '⚖️' },
  pending_human: { color: '#fb923c', label: 'Awaiting Sign',   icon: '✍️' },
  active:        { color: '#34d399', label: 'Active',          icon: '⚡' },
  paused:        { color: '#94a3b8', label: 'Paused',          icon: '⏸️' },
  completed:     { color: '#10b981', label: 'Completed',       icon: '✅' },
  cancelled:     { color: '#f87171', label: 'Cancelled',       icon: '🚫' },
  vetoed:        { color: '#ef4444', label: 'Vetoed',          icon: '🛑' },
};

const card = {
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  padding: 16,
  marginBottom: 12,
};

const btn = (color = '#667eea', small = false) => ({
  background: color,
  border: 'none',
  borderRadius: 8,
  color: '#fff',
  cursor: 'pointer',
  fontSize: small ? 12 : 13,
  fontWeight: 600,
  padding: small ? '5px 12px' : '8px 18px',
  marginRight: 6,
});

const input = {
  background: 'rgba(255,255,255,0.08)',
  border: '1px solid rgba(255,255,255,0.15)',
  borderRadius: 8,
  color: '#fff',
  fontSize: 13,
  padding: '8px 12px',
  width: '100%',
  boxSizing: 'border-box',
};

const label = { fontSize: 12, color: '#94a3b8', marginBottom: 4, display: 'block' };

export default function ContractsPanel({ user }) {
  const [contracts, setContracts]   = useState([]);
  const [stats, setStats]           = useState({});
  const [pendingHuman, setPending]  = useState([]);
  const [showForm, setShowForm]     = useState(false);
  const [selected, setSelected]     = useState(null);
  const [loading, setLoading]       = useState(false);
  const [msg, setMsg]               = useState('');

  const [form, setForm] = useState({
    provider_id: '', title: '', description: '',
    duration_days: 15, value_npr: '', skills: '',
  });

  const token = localStorage.getItem('asim_token');
  const headers = { 'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/contracts`, { headers });
      const d = await r.json();
      setContracts(d.contracts || []);
      setStats(d.stats || {});
      setPending(d.pending_human || []);
    } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 3000); };

  const post = async (path, body = {}) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}${path}`, { method: 'POST', headers, body: JSON.stringify(body) });
      const d = await r.json();
      if (d.detail) throw new Error(d.detail);
      await load();
      return d;
    } catch (e) { flash(`❌ ${e.message}`); return null; }
    finally { setLoading(false); }
  };

  const handlePropose = async () => {
    if (!form.title || !form.provider_id || !form.value_npr) {
      flash('❌ Title, provider, and value are required'); return;
    }
    const c = await post('/api/contracts/propose', {
      ...form,
      duration_days: parseInt(form.duration_days),
      value_npr: parseFloat(form.value_npr),
      skills: form.skills.split(',').map(s => s.trim()).filter(Boolean),
    });
    if (c) { flash('✅ Contract proposed — Gate 1 passed!'); setShowForm(false); setForm({ provider_id:'',title:'',description:'',duration_days:15,value_npr:'',skills:'' }); }
  };

  const handleGate2 = async (id) => {
    const c = await post(`/api/contracts/${id}/gate2`);
    if (c) flash(`✅ Gate 2 Dharma check: ${c.final3?.gate2_reason?.slice(0,60)}...`);
  };

  const handleSign = async (id, approved) => {
    const c = await post(`/api/contracts/${id}/sign`, { approved, note: approved ? 'Human confirmed' : 'Human rejected' });
    if (c) flash(approved ? '✅ Signed! Contract is now ACTIVE.' : '🚫 Contract rejected.');
  };

  const handleComplete = async (id) => {
    const c = await post(`/api/contracts/${id}/complete`, { rating: 5, note: 'Work completed successfully' });
    if (c) flash('🎉 Contract completed! Escrow released.');
  };

  const handlePause = async (id) => {
    const c = await post(`/api/contracts/${id}/pause`, { reason: 'Human pause' });
    if (c) flash('⏸️ Contract paused.');
  };

  const handleResume = async (id) => {
    const c = await post(`/api/contracts/${id}/resume`);
    if (c) flash('▶️ Contract resumed.');
  };

  const handleCancel = async (id) => {
    if (!window.confirm('Cancel this contract?')) return;
    const c = await post(`/api/contracts/${id}/cancel`, { reason: 'Human cancelled' });
    if (c) flash('🚫 Contract cancelled.');
  };

  const sm = STATUS_META;

  return (
    <div style={{ color: '#fff', fontFamily: 'system-ui, sans-serif', maxWidth: 900 }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22 }}>📜 HDT Smart Contracts</h2>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: 13 }}>
            5/15/30-day skill contracts · Dharma-gated · Final-3 human confirmation
          </p>
        </div>
        <button style={btn('#667eea')} onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Close' : '+ New Contract'}
        </button>
      </div>

      {/* Flash message */}
      {msg && (
        <div style={{ ...card, background: 'rgba(102,126,234,0.2)', border: '1px solid #667eea',
                      padding: '10px 16px', marginBottom: 12, fontSize: 13 }}>
          {msg}
        </div>
      )}

      {/* Stats bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, marginBottom: 20 }}>
        {[
          { label: 'Total',     value: stats.total || 0,         color: '#a78bfa' },
          { label: 'Active',    value: stats.active || 0,        color: '#34d399' },
          { label: 'Pending ✍️', value: stats.pending_human || 0, color: '#f59e0b' },
          { label: 'Done',      value: stats.completed || 0,     color: '#10b981' },
          { label: 'Value NPR', value: `₨${(stats.total_value_npr||0).toLocaleString()}`, color: '#60a5fa' },
        ].map(s => (
          <div key={s.label} style={{ ...card, textAlign: 'center', padding: 12 }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: '#94a3b8' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* New Contract Form */}
      {showForm && (
        <div style={{ ...card, border: '1px solid #667eea', marginBottom: 20 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>🆕 Propose New Contract</h3>

          {/* Final-3 Gate Info */}
          <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
                        borderRadius: 8, padding: 10, marginBottom: 16, fontSize: 12, color: '#fbbf24' }}>
            ⚖️ <strong>Final-3 Confirmation Required:</strong> Gate 1 (AI) → Gate 2 (Dharma) → Gate 3 (You sign)
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
            <div>
              <span style={label}>Title *</span>
              <input style={input} placeholder="e.g. Build community API"
                value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
            </div>
            <div>
              <span style={label}>Provider User ID *</span>
              <input style={input} placeholder="provider's user_id"
                value={form.provider_id} onChange={e => setForm({...form, provider_id: e.target.value})} />
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <span style={label}>Description</span>
            <textarea style={{ ...input, height: 70, resize: 'vertical' }}
              placeholder="Describe the work scope..."
              value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
            <div>
              <span style={label}>Duration</span>
              <select style={input} value={form.duration_days}
                onChange={e => setForm({...form, duration_days: parseInt(e.target.value)})}>
                <option value={5}>5 days — Task</option>
                <option value={15}>15 days — Project</option>
                <option value={30}>30 days — Ongoing</option>
              </select>
            </div>
            <div>
              <span style={label}>Value (NPR) *</span>
              <input style={input} type="number" placeholder="5000"
                value={form.value_npr} onChange={e => setForm({...form, value_npr: e.target.value})} />
            </div>
            <div>
              <span style={label}>Skills (comma-separated)</span>
              <input style={input} placeholder="python, react, design"
                value={form.skills} onChange={e => setForm({...form, skills: e.target.value})} />
            </div>
          </div>

          <button style={btn('#667eea')} onClick={handlePropose} disabled={loading}>
            {loading ? '⏳ Proposing...' : '📤 Propose Contract'}
          </button>
          <button style={btn('rgba(255,255,255,0.1)')} onClick={() => setShowForm(false)}>
            Cancel
          </button>
        </div>
      )}

      {/* Contracts list */}
      {contracts.length === 0 ? (
        <div style={{ ...card, textAlign: 'center', padding: 40, color: '#94a3b8' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>📜</div>
          <div>No contracts yet. Click <strong>+ New Contract</strong> to begin.</div>
        </div>
      ) : (
        contracts.map(c => {
          const meta = sm[c.status] || sm.proposed;
          const isPending = pendingHuman.includes(c.contract_id);
          return (
            <div key={c.contract_id} style={{
              ...card,
              border: `1px solid ${isPending ? '#f59e0b' : 'rgba(255,255,255,0.1)'}`,
              background: isPending ? 'rgba(245,158,11,0.05)' : 'rgba(255,255,255,0.05)',
            }}>
              {/* Contract header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <span style={{ fontWeight: 700, fontSize: 15 }}>{c.title}</span>
                  {isPending && (
                    <span style={{ marginLeft: 8, fontSize: 11, background: '#f59e0b',
                                   color: '#000', borderRadius: 4, padding: '2px 6px' }}>
                      ✍️ YOUR SIGNATURE NEEDED
                    </span>
                  )}
                </div>
                <span style={{ fontSize: 12, background: `${meta.color}22`,
                               color: meta.color, borderRadius: 20, padding: '3px 10px',
                               border: `1px solid ${meta.color}44` }}>
                  {meta.icon} {meta.label}
                </span>
              </div>

              {/* Contract details */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12,
                            fontSize: 12, color: '#94a3b8' }}>
                <div>⏱️ {c.duration_days} days</div>
                <div>₨ {c.value_npr?.toLocaleString()} NPR</div>
                <div>👤 {c.provider_id}</div>
                <div>🔑 {c.contract_id}</div>
              </div>

              {/* Progress bar (active/paused) */}
              {['active','paused'].includes(c.status) && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12,
                                color: '#94a3b8', marginBottom: 4 }}>
                    <span>Progress</span><span>{c.progress_pct}%</span>
                  </div>
                  <div style={{ height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3 }}>
                    <div style={{ height: '100%', background: '#34d399', borderRadius: 3,
                                  width: `${c.progress_pct}%`, transition: 'width 0.3s' }} />
                  </div>
                </div>
              )}

              {/* Final-3 Gates */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                {[
                  { n: 1, label: 'AI', pass: c.final3?.gate1_ai,   reason: c.final3?.gate1_reason },
                  { n: 2, label: 'Dharma', pass: c.final3?.gate2_dharma, reason: c.final3?.gate2_reason },
                  { n: 3, label: 'Human', pass: c.final3?.gate3_human,  reason: c.final3?.gate3_signed_at ? 'Signed' : null },
                ].map(g => (
                  <div key={g.n} style={{
                    fontSize: 11, padding: '4px 10px', borderRadius: 6,
                    background: g.pass === true ? 'rgba(52,211,153,0.15)' :
                                g.pass === false ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.06)',
                    color: g.pass === true ? '#34d399' : g.pass === false ? '#f87171' : '#64748b',
                    border: `1px solid ${g.pass === true ? 'rgba(52,211,153,0.3)' :
                                         g.pass === false ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.08)'}`,
                  }}>
                    Gate {g.n} {g.label}: {g.pass === true ? '✅' : g.pass === false ? '❌' : '⏳'}
                  </div>
                ))}
              </div>

              {/* Action buttons */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {c.status === 'gate1_pass' && (
                  <button style={btn('#f59e0b', true)} onClick={() => handleGate2(c.contract_id)}>
                    ⚖️ Run Dharma Check
                  </button>
                )}
                {(c.status === 'gate2_pass' || c.status === 'pending_human') && (
                  <>
                    <button style={btn('#10b981', true)} onClick={() => handleSign(c.contract_id, true)}>
                      ✅ Sign & Activate
                    </button>
                    <button style={btn('#ef4444', true)} onClick={() => handleSign(c.contract_id, false)}>
                      ❌ Reject
                    </button>
                  </>
                )}
                {c.status === 'active' && (
                  <>
                    <button style={btn('#10b981', true)} onClick={() => handleComplete(c.contract_id)}>
                      🎉 Mark Complete
                    </button>
                    <button style={btn('#94a3b8', true)} onClick={() => handlePause(c.contract_id)}>
                      ⏸️ Pause
                    </button>
                    <button style={btn('#ef4444', true)} onClick={() => handleCancel(c.contract_id)}>
                      🚫 Cancel
                    </button>
                  </>
                )}
                {c.status === 'paused' && (
                  <button style={btn('#667eea', true)} onClick={() => handleResume(c.contract_id)}>
                    ▶️ Resume
                  </button>
                )}
                {['proposed','gate1_pass','gate2_pass','pending_human'].includes(c.status) && (
                  <button style={btn('#ef4444', true)} onClick={() => handleCancel(c.contract_id)}>
                    🚫 Cancel
                  </button>
                )}
              </div>

              {/* Notes */}
              {c.notes?.length > 0 && (
                <div style={{ marginTop: 10, fontSize: 11, color: '#64748b',
                              borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 8 }}>
                  {c.notes.slice(-2).map((n,i) => <div key={i}>📝 {n}</div>)}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
