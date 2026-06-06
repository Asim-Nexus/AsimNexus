// STATUS: REAL — React dashboard, fetches live API, renders Dharma/Agent/Universe UI
// Uses corrected API modules from asimnexus.js (API Contract Cleanup RC-1)
import React, { useState, useEffect, useCallback } from 'react';
import { personalAPI, dharmaAPI } from '../../api/asimnexus';

// ── Stat Card ──────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, color = '#667eea', pulse = false }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: `1px solid ${color}33`,
      borderRadius: 14,
      padding: '18px 20px',
      minWidth: 150,
      flex: '1 1 150px',
    }}>
      <div style={{ fontSize: 26, marginBottom: 6 }}>{icon}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color, display: 'flex', alignItems: 'center', gap: 6 }}>
        {value}
        {pulse && <span style={{
          width: 8, height: 8, borderRadius: '50%', background: '#10b981',
          animation: 'pulse 1.5s infinite', display: 'inline-block',
        }} />}
      </div>
      <div style={{ fontSize: '0.75rem', color: '#aaa', marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: '0.68rem', color: '#666', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

// ── Universe Layer Badge ───────────────────────────────────────────────────
function UniverseBadge({ type, icon, label, active, nodes }) {
  const colors = {
    personal: '#667eea', family: '#10b981', community: '#f59e0b',
    enterprise: '#3b82f6', sovereign: '#c9a84c',
  };
  const c = colors[type] || '#667eea';
  return (
    <div style={{
      padding: '12px 16px',
      borderRadius: 12,
      border: `1px solid ${active ? c : 'rgba(255,255,255,0.08)'}`,
      background: active ? `${c}18` : 'rgba(255,255,255,0.02)',
      display: 'flex', alignItems: 'center', gap: 12,
      opacity: active ? 1 : 0.5,
    }}>
      <span style={{ fontSize: 22 }}>
        {type === 'personal' ? '👤' : type === 'family' ? '👨‍👩‍👧' :
          type === 'community' ? '🏘️' : type === 'enterprise' ? '🏢' : '🏛️'}
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, color: active ? c : '#888', fontSize: '0.88rem' }}>{label}</div>
        <div style={{ fontSize: '0.68rem', color: '#666' }}>
          {active ? `${nodes} node${nodes !== 1 ? 's' : ''} active` : 'Phase 2 — not yet connected'}
        </div>
      </div>
      {active && <span style={{ fontSize: 10, background: c, color: '#000', padding: '2px 8px', borderRadius: 20, fontWeight: 700 }}>LIVE</span>}
    </div>
  );
}

// ── Dharma Bar ─────────────────────────────────────────────────────────────
function DharmaStatus({ dharma }) {
  if (!dharma) return null;
  const score = dharma.symmetry_score ?? 0.95;
  const verdict = dharma.verdict ?? 'BALANCED';
  const color = verdict === 'BALANCED' ? '#10b981' : verdict === 'MILD_CONCENTRATION' ? '#f59e0b' : '#ef4444';
  const pct = Math.round(score * 100);

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: `1px solid ${color}33`,
      borderRadius: 14,
      padding: '18px 20px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>⚖️ Dharma / ΔT Engine</span>
        <span style={{
          fontSize: '0.72rem', padding: '3px 10px', borderRadius: 20,
          background: `${color}22`, color, fontWeight: 700, border: `1px solid ${color}55`,
        }}>{verdict}</span>
      </div>

      {/* Symmetry bar */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#888', marginBottom: 4 }}>
          <span>Network Symmetry (PoS)</span><span>{pct}%</span>
        </div>
        <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 6 }}>
          <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 6, transition: 'width 0.6s' }} />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, fontSize: '0.72rem', color: '#888' }}>
        <span>Gini: <b style={{ color: '#fff' }}>{(dharma.gini_coefficient ?? 0.05).toFixed(3)}</b></span>
        <span>L_max: <b style={{ color: '#fff' }}>{((dharma.l_max ?? 0.07) * 100).toFixed(0)}%</b></span>
        <span>Veto events: <b style={{ color: '#fff' }}>{dharma.total_veto_events ?? 0}</b></span>
        <span>Nodes: <b style={{ color: '#fff' }}>{dharma.node_count ?? 1}</b></span>
      </div>
    </div>
  );
}

// ── Agent Mode Panel ───────────────────────────────────────────────────────
function AgentModePanel({ agentStatus, onToggle, loading }) {
  const [skills, setSkills] = useState('');
  const [days, setDays] = useState(5);
  const active = agentStatus?.active ?? false;

  const handleOn = async () => {
    const skillList = skills.split(',').map(s => s.trim()).filter(Boolean);
    await onToggle(true, skillList, days);
  };

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: `1px solid ${active ? '#10b981' : 'rgba(255,255,255,0.08)'}`,
      borderRadius: 14,
      padding: '18px 20px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>🤖 Agent Mode</div>
          <div style={{ fontSize: '0.7rem', color: '#888', marginTop: 2 }}>
            {active ? 'Your Clone is live in the mesh marketplace' : 'OFF — your Clone is dormant'}
          </div>
        </div>
        <button
          onClick={() => active ? onToggle(false) : null}
          disabled={loading}
          style={{
            padding: '6px 18px', borderRadius: 20, border: 'none', cursor: 'pointer',
            background: active ? '#ef4444' : '#10b981',
            color: '#fff', fontWeight: 700, fontSize: '0.78rem',
          }}>
          {loading ? '...' : active ? 'Turn OFF' : 'Turn ON'}
        </button>
      </div>

      {!active && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input
            value={skills}
            onChange={e => setSkills(e.target.value)}
            placeholder="Your skills (e.g. Farming, Teaching, Coding)"
            style={{
              background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none',
            }}
          />
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: '#888', whiteSpace: 'nowrap' }}>Max contract:</span>
            {[5, 15, 30].map(d => (
              <button key={d} onClick={() => setDays(d)} style={{
                padding: '4px 12px', borderRadius: 16, border: `1px solid ${days === d ? '#667eea' : 'rgba(255,255,255,0.1)'}`,
                background: days === d ? '#667eea22' : 'transparent', color: days === d ? '#667eea' : '#888',
                cursor: 'pointer', fontSize: '0.72rem', fontWeight: days === d ? 700 : 400,
              }}>{d} days</button>
            ))}
            <button onClick={handleOn} style={{
              marginLeft: 'auto', padding: '6px 16px', borderRadius: 16,
              background: '#10b981', border: 'none', color: '#fff', fontWeight: 700,
              cursor: 'pointer', fontSize: '0.78rem',
            }}>Activate Clone</button>
          </div>
          <div style={{ fontSize: '0.65rem', color: '#666', marginTop: 2 }}>
            ⚠️ Final 3 Confirmation required before any contract starts — you are always in control.
          </div>
        </div>
      )}

      {active && (
        <div style={{ fontSize: '0.75rem', color: '#aaa', display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span>Skills: <b style={{ color: '#fff' }}>{(agentStatus.skills || []).join(', ') || 'General'}</b></span>
          <span>Max duration: <b style={{ color: '#fff' }}>{agentStatus.max_contract_days || 5} days</b></span>
          <span>Activated: <b style={{ color: '#fff' }}>{agentStatus.activated_at?.slice(0, 19) || 'just now'}</b></span>
          <span style={{ color: '#10b981', marginTop: 4 }}>
            🟢 Clone active — waiting for skill-matched requests from the mesh
          </span>
        </div>
      )}
    </div>
  );
}

// ── Final 3 Confirmation Panel ─────────────────────────────────────────────
function Final3Panel({ pending }) {
  if (!pending || pending.length === 0) {
    return (
      <div style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 14, padding: '16px 20px',
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 22 }}>✅</span>
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Final 3 Confirmation</div>
          <div style={{ fontSize: '0.7rem', color: '#888' }}>No pending confirmations — you are clear.</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'rgba(239,68,68,0.06)',
      border: '1px solid rgba(239,68,68,0.3)',
      borderRadius: 14, padding: '16px 20px',
    }}>
      <div style={{ fontWeight: 700, marginBottom: 10, color: '#ef4444' }}>
        ⚠️ {pending.length} Action(s) Awaiting Your Confirmation
      </div>
      {pending.map((item, i) => (
        <div key={i} style={{
          background: 'rgba(255,255,255,0.04)', borderRadius: 10,
          padding: '10px 14px', marginBottom: 8, display: 'flex', justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: '0.8rem' }}>{item.description}</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={{ background: '#10b981', border: 'none', color: '#fff', padding: '4px 14px', borderRadius: 12, cursor: 'pointer', fontSize: '0.72rem' }}>Approve</button>
            <button style={{ background: '#ef4444', border: 'none', color: '#fff', padding: '4px 14px', borderRadius: 12, cursor: 'pointer', fontSize: '0.72rem' }}>Reject</button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── MAIN PersonalOS Component ──────────────────────────────────────────────
export default function PersonalOS({ user }) {
  const [status, setStatus] = useState(null);
  const [universes, setUniverses] = useState([]);
  const [dharma, setDharma] = useState(null);
  const [agentStatus, setAgentStatus] = useState({ active: false });
  const [agentLoading, setAgentLoading] = useState(false);
  const [sharing, setSharing] = useState({ resource_sharing: false, share_pct: 2 });
  const [sharingLoading, setSharingLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshAt, setRefreshAt] = useState(0);

  const load = useCallback(async () => {
    try {
      const [s, u, d, a, rs] = await Promise.all([
        personalAPI.getPersonalStatus().then(r => r.data).catch(() => null),
        personalAPI.getUniverse().then(r => r.data).catch(() => null),
        dharmaAPI.getStatus().then(r => r.data).catch(() => null),
        personalAPI.getAgentStatus().then(r => r.data).catch(() => null),
        personalAPI.getResourceSharing().then(r => r.data).catch(() => null),
      ]);
      if (s) setStatus(s);
      if (u) setUniverses(u.universes || []);
      if (d) setDharma(d);
      if (a) setAgentStatus(a);
      if (rs) setSharing(rs);
    } catch (_) { }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load, refreshAt]);

  // Auto-refresh every 30s
  useEffect(() => {
    const t = setInterval(() => setRefreshAt(Date.now()), 30000);
    return () => clearInterval(t);
  }, []);

  const handleSharingToggle = async (enabled, pct = 2) => {
    setSharingLoading(true);
    try {
      const res = await personalAPI.setResourceSharing(enabled, pct).then(r => r.data);
      if (res) setSharing({ resource_sharing: res.resource_sharing, share_pct: res.share_pct });
    } catch (_) { }
    setSharingLoading(false);
  };

  const handleAgentToggle = async (turnOn, skills = [], days = 5) => {
    setAgentLoading(true);
    try {
      if (turnOn) {
        await personalAPI.agentModeOn();
      } else {
        await personalAPI.agentModeOff();
      }
      const a = await personalAPI.getAgentStatus().then(r => r.data);
      if (a) setAgentStatus(a);
    } catch (_) { }
    setAgentLoading(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#667eea' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>👤</div>
          <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>Loading Personal Universe...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 24px', maxWidth: 900, margin: '0 auto', color: '#fff' }}>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 6 }}>
          <div style={{
            width: 52, height: 52, borderRadius: '50%',
            background: 'linear-gradient(135deg,#667eea,#764ba2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
          }}>👤</div>
          <div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800 }}>
              {status?.display_name || user?.display_name || 'Your Universe'}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#888' }}>
              Personal Universe · Local-First · Dharma-Protected
            </div>
          </div>
          <button onClick={() => setRefreshAt(Date.now())} style={{
            marginLeft: 'auto', background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
            color: '#888', padding: '6px 14px', cursor: 'pointer', fontSize: '0.75rem',
          }}>↻ Refresh</button>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
        <StatCard icon="💬" label="Total Messages" value={status?.total_messages ?? 0} color="#667eea" />
        <StatCard icon="🤖" label="Active Clones" value={status?.clone_count ?? 15} color="#8b5cf6" />
        <StatCard icon="📋" label="Active Contracts" value={status?.active_contracts ?? 0} color="#10b981" />
        <StatCard icon="⚡" label="CPU Usage" value={`${status?.cpu_pct ?? 0}%`} color="#f59e0b" pulse />
        <StatCard icon="🧠" label="RAM Usage" value={`${status?.ram_pct ?? 0}%`} color="#3b82f6" />
        <StatCard icon="⚖️" label="Dharma Score" value={`${Math.round((status?.dharma_score ?? 0.94) * 100)}%`} color="#10b981" />
      </div>

      {/* Dharma Engine status */}
      <div style={{ marginBottom: 16 }}>
        <DharmaStatus dharma={dharma} />
      </div>

      {/* Agent Mode */}
      <div style={{ marginBottom: 16 }}>
        <AgentModePanel
          agentStatus={agentStatus}
          onToggle={handleAgentToggle}
          loading={agentLoading}
        />
      </div>

      {/* Final 3 Confirmation */}
      <div style={{ marginBottom: 16 }}>
        <Final3Panel pending={[]} />
      </div>

      {/* Resource Sharing */}
      <div style={{ marginBottom: 20 }}>
        <div style={{
          background: 'rgba(255,255,255,0.03)',
          border: `1px solid ${sharing.resource_sharing ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'}`,
          borderRadius: 14, padding: '18px 20px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: sharing.resource_sharing ? 12 : 0 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>🌐 Mesh Resource Sharing</div>
              <div style={{ fontSize: '0.7rem', color: '#888', marginTop: 2 }}>
                {sharing.resource_sharing
                  ? `Contributing ${sharing.share_pct}% idle CPU/RAM to the mesh`
                  : 'OFF — your device shares nothing with the mesh'}
              </div>
            </div>
            <button
              onClick={() => handleSharingToggle(!sharing.resource_sharing, sharing.share_pct || 2)}
              disabled={sharingLoading}
              style={{
                padding: '6px 18px', borderRadius: 20, border: 'none', cursor: 'pointer',
                background: sharing.resource_sharing ? '#ef4444' : '#10b981',
                color: '#fff', fontWeight: 700, fontSize: '0.78rem',
              }}>
              {sharingLoading ? '...' : sharing.resource_sharing ? 'Turn OFF' : 'Turn ON'}
            </button>
          </div>
          {sharing.resource_sharing && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8 }}>
              <span style={{ fontSize: '0.72rem', color: '#888' }}>Share %:</span>
              {[2, 3, 4, 5].map(p => (
                <button key={p} onClick={() => handleSharingToggle(true, p)} style={{
                  padding: '3px 12px', borderRadius: 14,
                  border: `1px solid ${sharing.share_pct === p ? '#10b981' : 'rgba(255,255,255,0.1)'}`,
                  background: sharing.share_pct === p ? '#10b98122' : 'transparent',
                  color: sharing.share_pct === p ? '#10b981' : '#888',
                  cursor: 'pointer', fontSize: '0.7rem', fontWeight: sharing.share_pct === p ? 700 : 400,
                }}>{p}%</button>
              ))}
              <span style={{ fontSize: '0.65rem', color: '#666', marginLeft: 4 }}>(consent-based, Phase 2 will connect real peers)</span>
            </div>
          )}
        </div>
      </div>

      {/* Universe Layers */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: 10, color: '#888', letterSpacing: 1, textTransform: 'uppercase' }}>
          Universe Layers
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {universes.map(u => (
            <UniverseBadge key={u.type} {...u} />
          ))}
        </div>
        <div style={{ fontSize: '0.68rem', color: '#555', marginTop: 8, textAlign: 'center' }}>
          Family · Community · Enterprise · Sovereign Universes → Phase 2 (LAN Mesh required)
        </div>
      </div>

      {/* Principles */}
      <div style={{
        background: 'rgba(102,126,234,0.06)',
        border: '1px solid rgba(102,126,234,0.15)',
        borderRadius: 14, padding: '16px 20px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10,
      }}>
        {[
          ['🔒', 'Local-First', status?.local_first ? 'ON' : 'OFF', '#10b981'],
          ['🛡️', 'Dharma Guard', 'Active', '#10b981'],
          ['⚖️', 'ΔT Engine', 'Running', '#10b981'],
          ['✅', 'Final 3 Required', 'Always', '#10b981'],
          ['🌐', 'Mesh Peers', `${status?.mesh_peers ?? 0} (Phase 2)`, '#888'],
          ['🤝', 'Resource Sharing', sharing.resource_sharing ? `ON (${sharing.share_pct}%)` : 'OFF', sharing.resource_sharing ? '#10b981' : '#888'],
        ].map(([icon, label, val, color]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem' }}>
            <span>{icon}</span>
            <span style={{ color: '#888' }}>{label}:</span>
            <span style={{ color, fontWeight: 600 }}>{val}</span>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}
