import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ROLE_META = {
  user:      { icon: '👤', color: '#667eea', label: 'You' },
  assistant: { icon: '🤖', color: '#10b981', label: 'AsimNexus' },
  system:    { icon: '⚙️', color: '#f59e0b', label: 'System' },
};

export default function MemoryPage() {
  const [memories, setMemories]     = useState([]);
  const [stats, setStats]           = useState(null);
  const [search, setSearch]         = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading]       = useState(true);
  const [deleting, setDeleting]     = useState(null);
  const [filter, setFilter]         = useState('all');

  const token = localStorage.getItem('asim_token');
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [mRes, sRes] = await Promise.all([
        fetch(`${API}/api/memory/recent?limit=50`, { headers }),
        fetch(`${API}/api/memory/stats`, { headers }),
      ]);
      if (mRes.ok) { const d = await mRes.json(); setMemories(d.memories || []); }
      if (sRes.ok) { const d = await sRes.json(); setStats(d); }
    } catch (_) {}
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setSearchResults(null); return; }
    try {
      const res = await fetch(`${API}/api/memory/search?q=${encodeURIComponent(q)}`, { headers });
      if (res.ok) { const d = await res.json(); setSearchResults(d.memories || []); }
    } catch (_) {}
  }, []);

  const doDelete = useCallback(async (id) => {
    setDeleting(id);
    try {
      await fetch(`${API}/api/memory/${id}`, { method: 'DELETE', headers });
      setMemories(prev => prev.filter(m => m.id !== id));
      if (stats) setStats(s => ({ ...s, total_messages: Math.max(0, (s.total_messages || 1) - 1) }));
    } catch (_) {}
    setDeleting(null);
  }, [stats]);

  const display = searchResults !== null ? searchResults
    : filter === 'all' ? memories
    : memories.filter(m => m.role === filter);

  const s = {
    page: { display: 'flex', flexDirection: 'column', height: '100%', color: 'var(--theme-text)', fontFamily: 'system-ui, sans-serif' },
    header: { padding: '16px 20px 12px', borderBottom: '1px solid rgba(255,255,255,0.07)', flexShrink: 0 },
    title: { fontSize: '1.15rem', fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 },
    statsRow: { display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 },
    stat: { padding: '6px 14px', borderRadius: 20, fontSize: '0.72rem', background: 'rgba(102,126,234,0.12)', border: '1px solid rgba(102,126,234,0.25)', color: '#a78bfa' },
    controls: { display: 'flex', gap: 8, flexWrap: 'wrap' },
    searchBox: { flex: 1, minWidth: 200, padding: '7px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.05)', color: 'inherit', fontSize: '0.85rem', outline: 'none' },
    filterBtn: (active) => ({ padding: '6px 14px', borderRadius: 20, fontSize: '0.72rem', cursor: 'pointer', border: 'none', background: active ? 'rgba(102,126,234,0.3)' : 'rgba(255,255,255,0.06)', color: active ? '#a78bfa' : 'rgba(255,255,255,0.55)' }),
    list: { flex: 1, overflowY: 'auto', padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: 6 },
    item: (role) => ({
      display: 'flex', gap: 10, padding: '10px 14px', borderRadius: 10,
      background: role === 'user' ? 'rgba(102,126,234,0.07)' : 'rgba(16,185,129,0.06)',
      border: `1px solid ${role === 'user' ? 'rgba(102,126,234,0.15)' : 'rgba(16,185,129,0.12)'}`,
      position: 'relative',
    }),
    avatar: (color) => ({ width: 28, height: 28, borderRadius: '50%', background: `${color}22`, border: `1px solid ${color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0, marginTop: 1 }),
    content: { flex: 1, minWidth: 0 },
    meta: { fontSize: '0.65rem', opacity: 0.4, marginBottom: 2, display: 'flex', gap: 8 },
    text: { fontSize: '0.85rem', opacity: 0.85, lineHeight: 1.5, wordBreak: 'break-word' },
    del: { position: 'absolute', top: 8, right: 8, background: 'none', border: 'none', cursor: 'pointer', opacity: 0.3, fontSize: 14, color: '#ef4444', padding: '2px 4px', borderRadius: 4 },
    empty: { textAlign: 'center', padding: '60px 20px', opacity: 0.3, fontSize: '0.9rem' },
  };

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div style={s.title}>
          🧠 Memory Browser
          <button onClick={load} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, opacity: 0.5, color: 'inherit' }} title="Refresh">↻</button>
        </div>

        {stats && (
          <div style={s.statsRow}>
            <span style={s.stat}>💬 {stats.total_messages || 0} messages</span>
            <span style={s.stat}>🟢 {stats.status || 'active'}</span>
            <span style={{ ...s.stat, color: '#10b981', borderColor: 'rgba(16,185,129,0.3)', background: 'rgba(16,185,129,0.1)' }}>🧠 VectorMemory active</span>
          </div>
        )}

        <div style={s.controls}>
          <input
            style={s.searchBox}
            placeholder="🔍 Memory खोज्नुस्..."
            value={search}
            onChange={e => { setSearch(e.target.value); doSearch(e.target.value); }}
          />
          {['all', 'user', 'assistant'].map(f => (
            <button key={f} style={s.filterBtn(filter === f && searchResults === null)} onClick={() => { setFilter(f); setSearchResults(null); setSearch(''); }}>
              {f === 'all' ? 'सबै' : f === 'user' ? '👤 तपाईं' : '🤖 AI'}
            </button>
          ))}
        </div>
      </div>

      <div style={s.list}>
        {loading ? (
          <div style={s.empty}>🧠 Memory लोड हुँदैछ...</div>
        ) : display.length === 0 ? (
          <div style={s.empty}>
            {search ? '🔍 कुनै result फेला परेन' : '🗒️ Memory खाली छ — Chat सुरु गर्नुस्!'}
          </div>
        ) : (
          display.map(m => {
            const meta = ROLE_META[m.role] || ROLE_META.assistant;
            const ts = typeof m.timestamp === 'number' ? m.timestamp * 1000 : Date.parse(m.timestamp);
            const time = ts && !isNaN(ts) ? new Date(ts).toLocaleString() : '';
            return (
              <div key={m.id} style={s.item(m.role)}>
                <div style={s.avatar(meta.color)}>{meta.icon}</div>
                <div style={s.content}>
                  <div style={s.meta}>
                    <span style={{ color: meta.color }}>{meta.label}</span>
                    {m.clone && m.role === 'assistant' && <span>· {m.clone}</span>}
                    {time && <span>· {time}</span>}
                  </div>
                  <div style={s.text}>{m.content}</div>
                </div>
                <button
                  style={s.del}
                  onClick={() => doDelete(m.id)}
                  disabled={deleting === m.id}
                  title="Delete">
                  {deleting === m.id ? '...' : '✕'}
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
