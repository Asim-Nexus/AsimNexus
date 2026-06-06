import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const g = (color, a=1) => `rgba(${color},${a})`;
const LAYER_COLORS = {
  personal:   '#667eea', family: '#10b981', community: '#f59e0b',
  enterprise: '#3b82f6', sovereign: '#8b5cf6',
};
const QUAD_COLORS = {
  citizen: '#34d399', corporate: '#60a5fa', government: '#f59e0b', community: '#c084fc',
};

const card = (extra={}) => ({
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 16, padding: 16, ...extra,
});
const pulse = {
  display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
  background: '#34d399', boxShadow: '0 0 0 2px rgba(52,211,153,0.3)',
  marginRight: 6,
};

export default function WorldOSDashboard() {
  const [data, setData]         = useState({});
  const [svt,  setSvt]          = useState(null);
  const [quad, setQuad]         = useState(null);
  const [bugs, setBugs]         = useState(null);
  const [cons, setCons]         = useState(null);
  const [dht,  setDht]          = useState(null);
  const [fw,   setFw]           = useState(null);
  const [loading, setLoading]   = useState(true);

  const loadAll = useCallback(async () => {
    try {
      const [svtR, quadR, bugsR, consR, dhtR, fwR] = await Promise.allSettled([
        fetch(`${API}/api/svt/stats`).then(r=>r.json()),
        fetch(`${API}/api/quad/status`).then(r=>r.json()),
        fetch(`${API}/api/bugs/stats`).then(r=>r.json()),
        fetch(`${API}/api/consensus/stats`).then(r=>r.json()),
        fetch(`${API}/api/dht/status`).then(r=>r.json()),
        fetch(`${API}/api/firewall/status`).then(r=>r.json()),
      ]);
      if (svtR.status  === 'fulfilled') setSvt(svtR.value);
      if (quadR.status === 'fulfilled') setQuad(quadR.value);
      if (bugsR.status === 'fulfilled') setBugs(bugsR.value);
      if (consR.status === 'fulfilled') setCons(consR.value);
      if (dhtR.status  === 'fulfilled') setDht(dhtR.value);
      if (fwR.status   === 'fulfilled') setFw(fwR.value);
      setLoading(false);
    } catch {}
  }, []);

  useEffect(() => { loadAll(); const t = setInterval(loadAll, 15000); return () => clearInterval(t); }, [loadAll]);

  return (
    <div style={{ color: '#fff', fontFamily: 'system-ui,sans-serif', maxWidth: 1200 }}>

      {/* ── HEADER ── */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, background: 'linear-gradient(135deg,#667eea,#a78bfa,#34d399)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>
            🌍 AsimNexus World OS
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 13 }}>
            Full-stack sovereign intelligence platform · Local-first · Dharma-protected
          </p>
        </div>
        <div style={{ display:'flex', gap: 8 }}>
          <span style={{ ...pulse }} /><span style={{ fontSize: 12, color:'#34d399' }}>Live</span>
        </div>
      </div>

      {loading && <div style={{ color:'#64748b', textAlign:'center', padding: 40 }}>Loading system state…</div>}

      {/* ── ROW 1: Token + Bugs + Consensus ── */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap: 12, marginBottom: 12 }}>

        {/* SVT Token */}
        <div style={{ ...card(), borderColor:'rgba(251,146,60,0.3)' }}>
          <div style={{ fontSize: 11, color:'#94a3b8', marginBottom: 8 }}>💰 SOVEREIGN TOKEN (SVT)</div>
          {svt ? <>
            <div style={{ fontSize: 22, fontWeight: 800, color:'#fb923c' }}>
              {Number(svt.total_supply).toLocaleString()}
            </div>
            <div style={{ fontSize: 11, color:'#64748b', marginTop: 4 }}>
              Supply · Burned: {Number(svt.total_burned).toLocaleString()} · Gini: {svt.gini}
            </div>
            <div style={{ display:'flex', gap: 6, marginTop: 8, flexWrap:'wrap' }}>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(251,146,60,0.15)', color:'#fb923c' }}>
                Wallets: {svt.total_wallets}
              </span>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(239,68,68,0.15)', color:'#f87171' }}>
                Burn: {svt.burn_rate}
              </span>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(52,211,153,0.15)', color:'#34d399' }}>
                Cap: {svt.concentration_cap}
              </span>
            </div>
          </> : <div style={{ color:'#64748b', fontSize: 12 }}>—</div>}
        </div>

        {/* Bug Triage */}
        <div style={{ ...card(), borderColor:'rgba(239,68,68,0.2)' }}>
          <div style={{ fontSize: 11, color:'#94a3b8', marginBottom: 8 }}>🐛 SELF-HEALING PIPELINE</div>
          {bugs ? <>
            <div style={{ fontSize: 22, fontWeight: 800, color: bugs.critical > 0 ? '#ef4444' : '#34d399' }}>
              {bugs.total} <span style={{ fontSize: 13, color:'#64748b' }}>bugs</span>
            </div>
            <div style={{ display:'flex', gap: 6, marginTop: 8, flexWrap:'wrap' }}>
              {bugs.critical > 0 && <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(239,68,68,0.15)', color:'#f87171' }}>⛔ {bugs.critical} critical</span>}
              {bugs.high > 0     && <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(251,146,60,0.15)', color:'#fb923c' }}>⚠️ {bugs.high} high</span>}
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(52,211,153,0.15)', color:'#34d399' }}>✅ {bugs.applied} applied</span>
              {bugs.pending_human > 0 && <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(167,139,250,0.15)', color:'#a78bfa' }}>👤 {bugs.pending_human} awaiting you</span>}
            </div>
            <div style={{ fontSize: 11, color:'#64748b', marginTop: 6 }}>Auto-rate: {bugs.auto_rate_pct}%</div>
          </> : <div style={{ color:'#64748b', fontSize: 12 }}>—</div>}
        </div>

        {/* Consensus */}
        <div style={{ ...card(), borderColor:'rgba(167,139,250,0.2)' }}>
          <div style={{ fontSize: 11, color:'#94a3b8', marginBottom: 8 }}>🗳️ 15-CLONE CONSENSUS</div>
          {cons ? <>
            <div style={{ fontSize: 22, fontWeight: 800, color:'#a78bfa' }}>
              {cons.clone_count} <span style={{ fontSize: 13, color:'#64748b' }}>clones</span>
            </div>
            <div style={{ display:'flex', gap: 6, marginTop: 8, flexWrap:'wrap' }}>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(52,211,153,0.15)', color:'#34d399' }}>✅ {cons.approved} approved</span>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(239,68,68,0.15)', color:'#f87171' }}>❌ {cons.rejected} rejected</span>
              {cons.pending_human > 0 && <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(251,146,60,0.15)', color:'#fb923c' }}>👤 {cons.pending_human} pending</span>}
            </div>
            <div style={{ fontSize: 10, color:'#64748b', marginTop: 6 }}>
              HIGH:8/15 · CRITICAL:11/15 · SOVEREIGNTY:15/15+Human
            </div>
          </> : <div style={{ color:'#64748b', fontSize: 12 }}>—</div>}
        </div>
      </div>

      {/* ── ROW 2: Quad Mesh ── */}
      <div style={{ ...card({ marginBottom: 12 }) }}>
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 14 }}>🌐 Quad Mesh — 4 Layer Architecture</div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap: 10 }}>
          {quad && Object.entries(quad).map(([layer, info]) => (
            <div key={layer} style={{
              padding: 12, borderRadius: 12,
              background: `${QUAD_COLORS[layer] || '#667eea'}11`,
              border: `1px solid ${QUAD_COLORS[layer] || '#667eea'}33`,
            }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: QUAD_COLORS[layer], textTransform:'uppercase', marginBottom: 6 }}>
                {layer}
              </div>
              <div style={{ fontSize: 18, fontWeight: 800, color:'#fff' }}>
                {info.peer_count ?? info.stats?.total_peers ?? 0}
                <span style={{ fontSize: 11, color:'#64748b', marginLeft: 4 }}>peers</span>
              </div>
              <div style={{ fontSize: 10, color:'#64748b', marginTop: 4 }}>
                {info.trust_rules?.description?.slice(0,40)}…
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── ROW 3: DHT + Firewall ── */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap: 12, marginBottom: 12 }}>

        {/* DHT */}
        <div style={card()}>
          <div style={{ fontSize: 11, color:'#94a3b8', marginBottom: 8 }}>🔮 KADEMLIA DHT</div>
          {dht ? <>
            <div style={{ fontSize: 14, fontWeight: 700, color:'#60a5fa' }}>
              {dht.node_id}
            </div>
            <div style={{ display:'flex', gap: 8, marginTop: 8, flexWrap:'wrap' }}>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(96,165,250,0.15)', color:'#60a5fa' }}>
                Nodes: {dht.routing?.total_nodes ?? 0}
              </span>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(96,165,250,0.15)', color:'#60a5fa' }}>
                Stored: {dht.stored_keys ?? 0} keys
              </span>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(96,165,250,0.15)', color:'#60a5fa' }}>
                Buckets: {dht.routing?.occupied_buckets ?? 0}
              </span>
            </div>
          </> : <div style={{ color:'#64748b', fontSize: 12 }}>—</div>}
        </div>

        {/* Cognitive Firewall */}
        <div style={{ ...card(), borderColor:'rgba(52,211,153,0.2)' }}>
          <div style={{ fontSize: 11, color:'#94a3b8', marginBottom: 8 }}>🧠 COGNITIVE FIREWALL</div>
          {fw ? <>
            <div style={{ fontSize: 18, fontWeight: 700, color:'#34d399' }}>
              {fw.pattern_count} <span style={{ fontSize: 12, color:'#64748b' }}>patterns</span>
            </div>
            <div style={{ fontSize: 11, color:'#64748b', marginTop: 6 }}>
              Types: {fw.bias_types?.slice(0,4).join(', ')}…
            </div>
            <div style={{ display:'flex', gap: 6, marginTop: 8 }}>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(52,211,153,0.15)', color:'#34d399' }}>
                Sensitivity: {fw.sensitivity}
              </span>
              <span style={{ fontSize: 10, padding:'2px 6px', borderRadius: 6, background:'rgba(52,211,153,0.15)', color:'#34d399' }}>
                Logged: {fw.log_count}
              </span>
            </div>
          </> : <div style={{ color:'#64748b', fontSize: 12 }}>—</div>}
        </div>
      </div>

      {/* ── ROW 4: Architecture Summary ── */}
      <div style={{ ...card(), background:'rgba(102,126,234,0.04)', borderColor:'rgba(102,126,234,0.15)' }}>
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 14, color:'#a78bfa' }}>
          🏗️ Full Architecture — Implemented Modules
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap: 8 }}>
          {[
            { phase:'2-A', label:'Dharma Engine', items:['DharmaVeto','CulturalCompiler','ΔT Engine'], color:'#667eea' },
            { phase:'2-B', label:'Smart Contracts', items:['5/15/30d lifecycle','Final-3 gate','Escrow'], color:'#10b981' },
            { phase:'2-C', label:'LAN Mesh', items:['mDNS discovery','P2P WebSocket','Air-Gap 5 levels'], color:'#f59e0b' },
            { phase:'2-D', label:'ZKP + Firewall', items:['DID + Ed25519','Cognitive Firewall','Bug Pipeline'], color:'#ef4444' },
            { phase:'3-A', label:'DHT + HDT', items:['Kademlia DHT','Human Digital Twin','Skill VCs'], color:'#3b82f6' },
            { phase:'3-B', label:'15-Clone Consensus', items:['Domain voting','3 thresholds','Human override'], color:'#8b5cf6' },
            { phase:'4-A', label:'SVT Economy', items:['Mint/Burn/Escrow','Anti-concentration','Gini check'], color:'#fb923c' },
            { phase:'4-B', label:'Quad Mesh', items:['Citizen/Corporate','Govt/Community','Data flow rules'], color:'#c084fc' },
          ].map(s => (
            <div key={s.phase} style={{
              padding: 10, borderRadius: 10,
              background: `${s.color}0d`,
              border: `1px solid ${s.color}22`,
            }}>
              <div style={{ fontSize: 10, color: s.color, fontWeight: 700, marginBottom: 4 }}>
                Phase {s.phase} · {s.label}
              </div>
              {s.items.map(i => (
                <div key={i} style={{ fontSize: 10, color:'#94a3b8', paddingLeft: 6 }}>✓ {i}</div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
