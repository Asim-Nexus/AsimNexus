import React, { useState, useEffect, useCallback } from 'react';
import { memoryAPI } from '../../api/asimnexus';

const ROLE_META: Record<string, { icon: string; color: string; label: string }> = {
    user: { icon: '👤', color: '#667eea', label: 'You' },
    assistant: { icon: '🤖', color: '#10b981', label: 'AsimNexus' },
    system: { icon: '⚙️', color: '#f59e0b', label: 'System' },
};

interface MemoryItem {
    id: string;
    role: string;
    content: string;
    timestamp: string | number;
    clone?: string;
}

interface StatsData {
    total_messages?: number;
    status?: string;
}

export default function MemoryPage() {
    const [memories, setMemories] = useState<MemoryItem[]>([]);
    const [stats, setStats] = useState<StatsData | null>(null);
    const [search, setSearch] = useState('');
    const [searchResults, setSearchResults] = useState<MemoryItem[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState<string | null>(null);
    const [filter, setFilter] = useState('all');

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [mRes, sRes] = await Promise.all([
                memoryAPI.getRecent(50) as unknown as { data: { memories?: MemoryItem[] } },
                memoryAPI.getStats() as unknown as { data: StatsData },
            ]);
            setMemories(mRes.data.memories || []);
            setStats(sRes.data);
        } catch (_) { /* ignore */ }
        setLoading(false);
    }, []);

    useEffect(() => { load(); }, [load]);

    const doSearch = useCallback(async (q: string) => {
        if (!q.trim()) { setSearchResults(null); return; }
        try {
            const res = await memoryAPI.search(q) as unknown as { data: { memories?: MemoryItem[] } };
            setSearchResults(res.data.memories || []);
        } catch (_) { /* ignore */ }
    }, []);

    const doDelete = useCallback(async (id: string) => {
        setDeleting(id);
        try {
            await memoryAPI.deleteMessage(id);
            setMemories(prev => prev.filter(m => m.id !== id));
            if (stats) setStats(prev => ({ ...(prev || stats), total_messages: Math.max(0, ((prev || stats).total_messages || 1) - 1) }));
        } catch (_) { /* ignore */ }
        setDeleting(null);
    }, [stats]);

    const display = searchResults !== null ? searchResults
        : filter === 'all' ? memories
            : memories.filter(m => m.role === filter);

    const s: Record<string, React.CSSProperties | ((...args: unknown[]) => React.CSSProperties)> = {
        page: { display: 'flex', flexDirection: 'column', height: '100%', color: 'var(--theme-text)', fontFamily: 'system-ui, sans-serif' } as React.CSSProperties,
        header: { padding: '16px 20px 12px', borderBottom: '1px solid rgba(255,255,255,0.07)', flexShrink: 0 },
        title: { fontSize: '1.15rem', fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 },
        statsRow: { display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 },
        stat: { padding: '6px 14px', borderRadius: 20, fontSize: '0.72rem', background: 'rgba(102,126,234,0.12)', border: '1px solid rgba(102,126,234,0.25)', color: '#a78bfa' },
        controls: { display: 'flex', gap: 8, flexWrap: 'wrap' },
        searchBox: { flex: 1, minWidth: 200, padding: '7px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.05)', color: 'inherit', fontSize: '0.85rem', outline: 'none' },
        filterBtn: (active: unknown) => ({ padding: '6px 14px', borderRadius: 20, fontSize: '0.72rem', cursor: 'pointer', border: 'none', background: active ? 'rgba(102,126,234,0.3)' : 'rgba(255,255,255,0.06)', color: active ? '#a78bfa' : 'rgba(255,255,255,0.55)' }) as React.CSSProperties,
        list: { flex: 1, overflowY: 'auto', padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: 6 },
        item: (role: unknown) => ({
            display: 'flex', gap: 10, padding: '10px 14px', borderRadius: 10,
            background: role === 'user' ? 'rgba(102,126,234,0.07)' : 'rgba(16,185,129,0.06)',
            border: `1px solid ${role === 'user' ? 'rgba(102,126,234,0.15)' : 'rgba(16,185,129,0.12)'}`,
            position: 'relative' as const,
        }) as React.CSSProperties,
        avatar: (color: unknown) => ({ width: 28, height: 28, borderRadius: '50%', background: `${color}22`, border: `1px solid ${color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0, marginTop: 1 }) as React.CSSProperties,
        content: { flex: 1, minWidth: 0 },
        meta: { fontSize: '0.65rem', opacity: 0.4, marginBottom: 2, display: 'flex', gap: 8 },
        text: { fontSize: '0.85rem', opacity: 0.85, lineHeight: 1.5, wordBreak: 'break-word' },
        del: { position: 'absolute', top: 8, right: 8, background: 'none', border: 'none', cursor: 'pointer', opacity: 0.3, fontSize: 14, color: '#ef4444', padding: '2px 4px', borderRadius: 4 },
        empty: { textAlign: 'center', padding: '60px 20px', opacity: 0.3, fontSize: '0.9rem' },
    };

    const sf = (fn: unknown, ...args: unknown[]): React.CSSProperties => {
        return typeof fn === 'function' ? (fn as (...a: unknown[]) => React.CSSProperties)(...args) : fn as React.CSSProperties;
    };

    return (
        <div style={s.page as React.CSSProperties}>
            <div style={s.header as React.CSSProperties}>
                <div style={s.title as React.CSSProperties}>
                    🧠 Memory Browser
                    <button onClick={load} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, opacity: 0.5, color: 'inherit' }} title="Refresh">↻</button>
                </div>

                {stats && (
                    <div style={s.statsRow as React.CSSProperties}>
                        <span style={s.stat as React.CSSProperties}>💬 {stats.total_messages || 0} messages</span>
                        <span style={s.stat as React.CSSProperties}>🟢 {stats.status || 'active'}</span>
                        <span style={{ ...s.stat as React.CSSProperties, color: '#10b981', borderColor: 'rgba(16,185,129,0.3)', background: 'rgba(16,185,129,0.1)' }}>🧠 VectorMemory active</span>
                    </div>
                )}

                <div style={s.controls as React.CSSProperties}>
                    <input
                        style={s.searchBox as React.CSSProperties}
                        placeholder="🔍 Memory खोज्नुस्..."
                        value={search}
                        onChange={e => { setSearch(e.target.value); doSearch(e.target.value); }}
                    />
                    {['all', 'user', 'assistant'].map(f => (
                        <button key={f} style={sf(s.filterBtn, filter === f && searchResults === null)} onClick={() => { setFilter(f); setSearchResults(null); setSearch(''); }}>
                            {f === 'all' ? 'सबै' : f === 'user' ? '👤 तपाईं' : '🤖 AI'}
                        </button>
                    ))}
                </div>
            </div>

            <div style={s.list as React.CSSProperties}>
                {loading ? (
                    <div style={s.empty as React.CSSProperties}>🧠 Memory लोड हुँदैछ...</div>
                ) : display.length === 0 ? (
                    <div style={s.empty as React.CSSProperties}>
                        {search ? '🔍 कुनै result फेला परेन' : '🗒️ Memory खाली छ — Chat सुरु गर्नुस्!'}
                    </div>
                ) : (
                    display.map(m => {
                        const meta = ROLE_META[m.role] || ROLE_META.assistant;
                        const ts = typeof m.timestamp === 'number' ? m.timestamp * 1000 : Date.parse(m.timestamp as string);
                        const time = ts && !isNaN(ts) ? new Date(ts).toLocaleString() : '';
                        return (
                            <div key={m.id} style={sf(s.item, m.role)}>
                                <div style={sf(s.avatar, meta.color)}>{meta.icon}</div>
                                <div style={s.content as React.CSSProperties}>
                                    <div style={s.meta as React.CSSProperties}>
                                        <span style={{ color: meta.color }}>{meta.label}</span>
                                        {m.clone && m.role === 'assistant' && <span>· {m.clone}</span>}
                                        {time && <span>· {time}</span>}
                                    </div>
                                    <div style={s.text as React.CSSProperties}>{m.content}</div>
                                </div>
                                <button
                                    style={s.del as React.CSSProperties}
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
