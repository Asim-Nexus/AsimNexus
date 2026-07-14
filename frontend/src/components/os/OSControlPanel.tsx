import { useState, useEffect, useCallback } from 'react';
import api from '../../api/asimnexus';

const g = async (path: string): Promise<Record<string, unknown>> => { try { const r = await api.get(path); return r.data as Record<string, unknown>; } catch { return {}; } };
const p = async (path: string, data: Record<string, unknown>): Promise<Record<string, unknown>> => { try { const r = await api.post(path, data); return r.data as Record<string, unknown>; } catch { return {}; } };

// ── OS Tool Executor Component ──────────────────────────────────────────
interface ToolMeta {
    name?: string;
    risk_level?: string;
    description?: string;
    requires_confirmation?: boolean;
    [key: string]: unknown;
}

function OSToolExecutor() {
    const [tools, setTools] = useState<ToolMeta[]>([]);
    const [selectedTool, setSelectedTool] = useState('');
    const [params, setParams] = useState('{}');
    const [result, setResult] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        g('/api/os/tools').then(r => {
            if ((r as Record<string, unknown>).tools) setTools((r as Record<string, unknown>).tools as ToolMeta[]);
        }).catch(() => { });
    }, []);

    const handleExecute = async () => {
        if (!selectedTool) { setError('Select a tool first'); return; }
        setLoading(true); setError(''); setResult(null);
        try {
            let parsedParams: Record<string, unknown> = {};
            try { parsedParams = JSON.parse(params); } catch { setError('Invalid JSON parameters'); setLoading(false); return; }
            const res = await p('/api/os/execute', { tool_name: selectedTool, parameters: parsedParams });
            setResult(res);
            if ((res as Record<string, unknown>).verdict === 'denied') setError(((res as Record<string, unknown>).error as string) || 'Permission denied');
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setLoading(false);
        }
    };

    const selectedMeta = tools.find(t => t.name === selectedTool);

    return (
        <div style={{
            marginBottom: 16, padding: '12px 16px',
            background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10
        }}>
            <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: 2, opacity: 0.4, marginBottom: 8 }}>
                🔧 OS Tool Executor
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 8 }}>
                <select value={selectedTool} onChange={e => setSelectedTool(e.target.value)}
                    style={{
                        flex: 1, minWidth: 180, padding: '6px 10px', borderRadius: 8,
                        background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                        color: '#fff', fontSize: '0.78rem',
                    }}>
                    <option value="">— Select OS Tool —</option>
                    {tools.map(t => (
                        <option key={t.name} value={t.name} style={{ background: '#1a1a2e' }}>
                            {t.name} [{t.risk_level}]
                        </option>
                    ))}
                </select>
                <input value={params} onChange={e => setParams(e.target.value)}
                    placeholder='{"key": "value"}'
                    style={{
                        flex: 1, minWidth: 140, padding: '6px 10px', borderRadius: 8,
                        background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                        color: 'rgba(255,255,255,0.7)', fontSize: '0.75rem', fontFamily: 'monospace',
                    }} />
                <button onClick={handleExecute} disabled={loading}
                    style={{
                        padding: '6px 16px', borderRadius: 8, border: '1px solid rgba(16,185,129,0.3)',
                        background: loading ? 'rgba(16,185,129,0.05)' : 'rgba(16,185,129,0.12)',
                        color: loading ? 'rgba(255,255,255,0.3)' : '#10b981',
                        cursor: loading ? 'not-allowed' : 'pointer', fontSize: '0.78rem',
                        fontWeight: 600,
                    }}>
                    {loading ? '⏳ Executing…' : '▶ Execute'}
                </button>
            </div>
            {selectedMeta && (
                <div style={{ fontSize: '0.7rem', opacity: 0.5, marginBottom: 6 }}>
                    {selectedMeta.description} · Risk: {selectedMeta.risk_level}
                    {selectedMeta.requires_confirmation ? ' · ⚠️ Confirmation required' : ''}
                </div>
            )}
            {error && (
                <div style={{
                    marginTop: 6, padding: '6px 12px', borderRadius: 8,
                    background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                    color: '#f87171', fontSize: '0.75rem',
                }}>
                    ✕ {error}
                </div>
            )}
            {result && (result as Record<string, unknown>).verdict === 'allowed' && (
                <div style={{
                    marginTop: 6, padding: '6px 12px', borderRadius: 8,
                    background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
                    color: '#10b981', fontSize: '0.75rem',
                }}>
                    ✓ Executed in {((result as Record<string, unknown>).execution_ms as number)?.toFixed(0)}ms
                    <pre style={{ marginTop: 4, fontSize: '0.65rem', opacity: 0.7, maxHeight: 100, overflow: 'auto' }}>
                        {JSON.stringify((result as Record<string, unknown>).output || result, null, 2).slice(0, 500)}
                    </pre>
                </div>
            )}
            {result && (result as Record<string, unknown>).verdict === 'pending_human' && (
                <div style={{
                    marginTop: 6, padding: '6px 12px', borderRadius: 8,
                    background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)',
                    color: '#f59e0b', fontSize: '0.75rem',
                }}>
                    ⏳ Pending human approval — Call ID: {String((result as Record<string, unknown>).call_id)}
                </div>
            )}
        </div>
    );
}

// ── Module Definitions ──────────────────────────────────────────────────
interface ModuleDef {
    key: string;
    label: string;
    endpoint?: string;
    fetch?: () => Promise<Record<string, unknown>>;
    badge: (data: Record<string, unknown>) => string;
}

interface ModuleGroup {
    group: string;
    color: string;
    modules: ModuleDef[];
}

const MODULE_GROUPS: ModuleGroup[] = [
    {
        group: '🧠 Intelligence', color: '#667eea', modules: [
            { key: 'clones', label: '15 Clones', endpoint: '/api/clones/specs', badge: d => ((d.status as Record<string, unknown>)?.total_clones as string) + ' clones' },
            { key: 'dreaming', label: 'Dreaming Engine', endpoint: '/api/bugs/stats', badge: d => (d.total as number) + ' bugs tracked' },
            { key: 'consensus', label: '15-Clone Consensus', endpoint: '/api/consensus/stats', badge: d => (d.clone_count as number) + ' clones' },
            { key: 'hdt', label: 'Human Digital Twin', endpoint: '/api/hdt/status', badge: d => (d.did as string) ? 'active' : 'no twin' },
        ]
    },
    {
        group: '🔐 Security', color: '#ef4444', modules: [
            { key: 'runtime', label: 'Zero-Trust Runtime', endpoint: '/api/runtime/status', badge: d => (d.active_tokens as number) + ' tokens' },
            { key: 'firewall', label: 'Cognitive Firewall', endpoint: '/api/firewall/status', badge: d => (d.pattern_count as number) + ' patterns' },
            { key: 'zkp', label: 'ZKP Identity', endpoint: '/api/identity/status', badge: d => (d.total_identities as number) + ' DIDs' },
            { key: 'pq', label: 'Post-Quantum Crypto', endpoint: '/api/pq/status', badge: d => (d.total_keys as number) + ' keys' },
        ]
    },
    {
        group: '🌐 Mesh & Network', color: '#10b981', modules: [
            { key: 'quad', label: 'Quad Mesh', endpoint: '/api/quad/status', badge: d => Object.keys(d).length + ' layers' },
            { key: 'dht', label: 'Kademlia DHT', endpoint: '/api/dht/status', badge: d => (d.node_id as string) ? 'online' : 'offline' },
            { key: 'federation', label: 'Global Federation', endpoint: '/api/federation/status', badge: d => (d.peers as number) + ' peers' },
            { key: 'sync', label: 'Offline Sync', endpoint: '/api/sync/status', badge: d => 'q=' + (d.queue_depth as number) },
        ]
    },
    {
        group: '💰 Economy', color: '#f59e0b', modules: [
            { key: 'svt', label: 'Sovereign Token', endpoint: '/api/svt/stats', badge: d => ((d.total_wallets || 0) as number) + ' wallets' },
            { key: 'depin', label: 'DePIN Bridge', endpoint: '/api/depin/status', badge: d => (d.active_nodes as number) + ' nodes' },
            { key: 'jobs', label: 'Job Marketplace', endpoint: '/api/jobs/stats', badge: d => (d.total_jobs as number) + ' jobs' },
            { key: 'events', label: 'Event Bus', endpoint: '/api/events/stats', badge: d => (d.total_delivered as number) + ' events' },
        ]
    },
    {
        group: '🌍 Universe', color: '#8b5cf6', modules: [
            { key: 'universe', label: 'Universe Containers', endpoint: '/api/universe/list', badge: d => ((d.universes as Record<string, unknown>[])?.length || 0) + ' universes' },
            { key: 'dharma', label: 'Dharma Engine', endpoint: '/api/dharma/status', badge: d => (d.verdict as string) || 'ok' },
            { key: 'evolution', label: 'Self-Evolution', endpoint: '/api/evolution/stats', badge: d => (d.total as number) + ' patches' },
            { key: 'nepal', label: 'Nepal Layer', endpoint: '/api/nepal/status', badge: () => 'cultural' },
        ]
    },
    {
        group: '📡 Infrastructure', color: '#06b6d4', modules: [
            { key: 'health', label: 'System Health', endpoint: '/health', badge: d => d.status as string },
            { key: 'personal', label: 'Personal Universe', endpoint: '/api/personal/status', badge: d => (d.username as string) || 'user' },
            { key: 'bugs', label: 'Bug Triage', endpoint: '/api/bugs/stats', badge: d => (d.total as number) + ' bugs' },
            { key: 'agent', label: 'Agent Mode', endpoint: '/api/agent/status', badge: d => (d.active as boolean) ? 'ACTIVE' : 'off' },
        ]
    },
    {
        group: '🖥️ Hardware', color: '#f97316', modules: [
            { key: 'cpu', label: 'CPU', fetch: () => p('/api/os/execute', { tool_name: 'hw.cpu', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.name as string) || '…' },
            { key: 'gpu', label: 'GPU', fetch: () => p('/api/os/execute', { tool_name: 'hw.gpu', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.name as string) || '…' },
            { key: 'npu', label: 'NPU / AI', fetch: () => p('/api/os/execute', { tool_name: 'hw.npu', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.name as string) || '…' },
            { key: 'motherboard', label: 'Motherboard', fetch: () => p('/api/os/execute', { tool_name: 'hw.motherboard', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.manufacturer as string) || '…' },
            { key: 'chipset', label: 'Chipset', fetch: () => p('/api/os/execute', { tool_name: 'hw.chipset', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.name as string) || '…' },
            { key: 'ram', label: 'RAM Modules', fetch: () => p('/api/os/execute', { tool_name: 'hw.ram', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => ((d.module_count || 0) as number) + ' modules' },
            { key: 'rom', label: 'ROM / BIOS', fetch: () => p('/api/os/execute', { tool_name: 'hw.rom', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.vendor as string) || '…' },
            { key: 'storage_ctrl', label: 'Storage Ctrl', fetch: () => p('/api/os/execute', { tool_name: 'hw.storage_controller', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => ((d.controller_count || 0) as number) + ' ctrls' },
            { key: 'usb', label: 'USB Devices', fetch: () => p('/api/os/execute', { tool_name: 'hw.usb', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => ((d.device_count || 0) as number) + ' devices' },
            { key: 'display', label: 'Display', fetch: () => p('/api/os/execute', { tool_name: 'hw.display', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.name as string) || '…' },
            { key: 'audio', label: 'Audio', fetch: () => p('/api/os/execute', { tool_name: 'hw.audio', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => ((d.device_count || 0) as number) + ' devices' },
            { key: 'sensor', label: 'Sensors', fetch: () => p('/api/os/execute', { tool_name: 'hw.sensor', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => ((d.temperature_count || 0) as number) + ' temps' },
            { key: 'thermal', label: 'Thermal', fetch: () => p('/api/os/execute', { tool_name: 'hw.thermal', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => ((d.fan_count || 0) as number) + ' fans' },
            { key: 'bios', label: 'BIOS/UEFI', fetch: () => p('/api/os/execute', { tool_name: 'hw.bios', parameters: {} }).then(r => (r as Record<string, unknown>).output as Record<string, unknown> || r), badge: d => (d.vendor as string) || '…' },
        ]
    },
];

// ── Module Card ─────────────────────────────────────────────────────────
interface ModuleCardProps {
    mod: ModuleDef;
    color: string;
}

function ModuleCard({ mod, color }: ModuleCardProps) {
    const [data, setData] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        if (mod.fetch) {
            mod.fetch().then(d => { setData(d); setLoading(false); });
        } else {
            g(mod.endpoint as string).then(d => { setData(d); setLoading(false); });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mod.endpoint, mod.fetch]);

    const badge = data ? mod.badge(data) : '…';
    const ok = data && !data.error;

    return (
        <div onClick={() => setExpanded(v => !v)} style={{
            background: ok ? `${color}0e` : 'rgba(239,68,68,0.05)',
            border: `1px solid ${ok ? color + '30' : 'rgba(239,68,68,0.2)'}`,
            borderRadius: 10, padding: '10px 14px', cursor: 'pointer',
            transition: 'all 0.18s', position: 'relative', overflow: 'hidden',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: ok ? '#fff' : '#f87171' }}>
                    {mod.label}
                </span>
                <span style={{
                    fontSize: '0.65rem', padding: '2px 8px', borderRadius: 20,
                    background: ok ? `${color}25` : 'rgba(239,68,68,0.15)',
                    color: ok ? color : '#f87171', fontWeight: 600,
                }}>
                    {loading ? '…' : badge}
                </span>
            </div>
            {/* status dot */}
            <div style={{
                position: 'absolute', top: 8, right: 8, width: 6, height: 6,
                borderRadius: '50%',
                background: loading ? '#f59e0b' : ok ? '#10b981' : '#ef4444',
                boxShadow: `0 0 6px ${loading ? '#f59e0b' : ok ? '#10b981' : '#ef4444'}`,
            }} />
            {/* expanded JSON */}
            {expanded && data && (
                <pre style={{
                    marginTop: 8, fontSize: '0.62rem', color: 'rgba(255,255,255,0.5)',
                    maxHeight: 120, overflow: 'auto', background: 'rgba(0,0,0,0.3)',
                    borderRadius: 6, padding: 6, lineHeight: 1.4,
                }}>
                    {JSON.stringify(data, null, 2).slice(0, 600)}
                </pre>
            )}
        </div>
    );
}

// ── System Vitals ───────────────────────────────────────────────────────
function SystemVitals() {
    const [vitals, setVitals] = useState<Record<string, unknown>>({});
    useEffect(() => {
        const load = () => g('/health').then(setVitals);
        load();
        const t = setInterval(load, 5000);
        return () => clearInterval(t);
    }, []);

    const bars = [
        { label: 'CPU', val: (vitals.cpu_percent as number) || 0, color: '#667eea' },
        { label: 'RAM', val: (vitals.ram_percent as number) || 0, color: '#10b981' },
        { label: 'Disk', val: (vitals.disk_percent as number) || 0, color: '#f59e0b' },
    ];

    return (
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
            {bars.map(b => (
                <div key={b.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '0.7rem', opacity: 0.6, width: 32 }}>{b.label}</span>
                    <div style={{ width: 80, height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${b.val}%`, background: b.color, borderRadius: 3, transition: 'width 0.5s' }} />
                    </div>
                    <span style={{ fontSize: '0.7rem', color: b.color, width: 34 }}>{b.val.toFixed(0)}%</span>
                </div>
            ))}
            <span style={{ fontSize: '0.68rem', opacity: 0.4, marginLeft: 'auto' }}>
                {vitals.status === 'healthy' ? '🟢 healthy' : '🔴 offline'}
            </span>
        </div>
    );
}

// ── Quick Actions ───────────────────────────────────────────────────────
function QuickActions() {
    const [result, setResult] = useState('');

    const actions = [
        {
            label: '🧬 Propose Patch', fn: async () => {
                const r = await p('/api/evolution/propose', {
                    title: 'Perf tweak', target_file: 'core/events/reactive_bus.py',
                    old_code: '# placeholder', new_code: '# optimized placeholder',
                    description: 'Minor performance improvement', proposed_by: 'human',
                });
                return `Patch ${(r as Record<string, unknown>).patch_id} [${(r as Record<string, unknown>).risk}]`;
            }
        },
        {
            label: '🔑 Register Clone Token', fn: async () => {
                const r = await p('/api/runtime/register', { principal: 'clone:dharma', role: 'clone', ttl: 7200 });
                return `Token ${((r as Record<string, unknown>).token_id as string)?.slice(0, 8)} issued`;
            }
        },
        {
            label: '📡 Collect DePIN Rewards', fn: async () => {
                const st = await g('/api/depin/status');
                return `${(st.active_nodes as number) || 0} active nodes, ${(st.total_svt_earned as number) || 0} SVT earned`;
            }
        },
        {
            label: '🔄 Flush Sync Queue', fn: async () => {
                const r = await p('/api/sync/flush', {});
                return `Synced ${(r as Record<string, unknown>).synced}, conflicts ${(r as Record<string, unknown>).conflicts}`;
            }
        },
        {
            label: '⚡ Publish Test Event', fn: async () => {
                const r = await p('/api/events/publish', { topic: 'os.heartbeat', payload: { ts: Date.now() }, source: 'control_panel' });
                return `Event ${((r as Record<string, unknown>).event_id as string)?.slice(0, 8)} → ${(r as Record<string, unknown>).status}`;
            }
        },
        {
            label: '🔐 PQ Keygen', fn: async () => {
                const r = await p('/api/pq/keygen', { did: 'did:asim:admin', algorithm: 'ML-KEM-768' });
                return `Key ${((r as Record<string, unknown>).key_id as string)?.slice(0, 8)} [${(r as Record<string, unknown>).algorithm}]`;
            }
        },
    ];

    return (
        <div>
            <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: 2, opacity: 0.4, marginBottom: 8 }}>
                Quick Actions
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {actions.map(a => (
                    <button key={a.label} onClick={async () => {
                        setResult('running…');
                        try { setResult(await a.fn()); }
                        catch (e) { setResult('Error: ' + (e as Error).message); }
                    }} style={{
                        padding: '6px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)',
                        background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.8)',
                        cursor: 'pointer', fontSize: '0.75rem', transition: 'all 0.15s',
                    }}
                        onMouseEnter={e => (e.target as HTMLElement).style.background = 'rgba(102,126,234,0.15)'}
                        onMouseLeave={e => (e.target as HTMLElement).style.background = 'rgba(255,255,255,0.04)'}>
                        {a.label}
                    </button>
                ))}
            </div>
            {result && (
                <div style={{
                    marginTop: 8, padding: '6px 12px', borderRadius: 8,
                    background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
                    color: '#10b981', fontSize: '0.75rem',
                }}>
                    ✓ {result}
                </div>
            )}
        </div>
    );
}

// ── Module Count Banner ─────────────────────────────────────────────────
function ModuleCountBanner({ total, online }: { total: number; online: number }) {
    return (
        <div style={{
            display: 'flex', gap: 20, padding: '10px 20px',
            background: 'rgba(102,126,234,0.06)', borderRadius: 12,
            border: '1px solid rgba(102,126,234,0.15)', alignItems: 'center',
            flexWrap: 'wrap',
        }}>
            {([
                { label: 'Total Modules', val: total, color: '#667eea' },
                { label: 'Online', val: online, color: '#10b981' },
                { label: 'Offline', val: total - online, color: '#ef4444' },
                { label: 'Health', val: total > 0 ? Math.round(online / total * 100) + '%' : '–', color: '#f59e0b' },
            ] as { label: string; val: string | number; color: string }[]).map(s => (
                <div key={s.label} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: 700, color: s.color }}>{s.val}</div>
                    <div style={{ fontSize: '0.6rem', opacity: 0.5, textTransform: 'uppercase', letterSpacing: 1 }}>{s.label}</div>
                </div>
            ))}
            <div style={{ marginLeft: 'auto', fontSize: '0.7rem', opacity: 0.4 }}>
                AsimNexus OS v4.0 · Future-Proof Architecture
            </div>
        </div>
    );
}

// ── MAIN OSControlPanel Component ───────────────────────────────────────
export default function OSControlPanel() {
    const [moduleStatus, setModuleStatus] = useState<Record<string, boolean>>({});
    const [refreshKey, setRefreshKey] = useState(0);

    const refresh = useCallback(() => setRefreshKey(k => k + 1), []);

    // Count online modules
    const allMods = MODULE_GROUPS.flatMap(g => g.modules);
    const onlineCount = Object.values(moduleStatus).filter(Boolean).length;

    useEffect(() => {
        // Poll all endpoints to build status map
        allMods.forEach(mod => {
            if (mod.endpoint) {
                g(mod.endpoint).then(d => {
                    setModuleStatus(prev => ({ ...prev, [mod.key]: !d.error }));
                });
            }
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [refreshKey]);

    return (
        <div style={{ color: '#fff', fontFamily: 'inherit', padding: '4px 0' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                    <h2 style={{
                        margin: 0, fontSize: '1.1rem', fontWeight: 700,
                        background: 'linear-gradient(90deg, #667eea, #a78bfa, #10b981)',
                        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
                    }}>
                        🎛️ AsimNexus OS Control Panel
                    </h2>
                    <div style={{ fontSize: '0.68rem', opacity: 0.4, marginTop: 2 }}>
                        All 50+ modules • Live status • Click any card to inspect
                    </div>
                </div>
                <button onClick={refresh} style={{
                    padding: '6px 16px', borderRadius: 8, border: '1px solid rgba(102,126,234,0.3)',
                    background: 'rgba(102,126,234,0.1)', color: '#667eea', cursor: 'pointer', fontSize: '0.78rem',
                }}>↺ Refresh</button>
            </div>

            {/* System vitals */}
            <div style={{
                marginBottom: 14, padding: '10px 16px',
                background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10
            }}>
                <SystemVitals />
            </div>

            {/* Module count banner */}
            <div style={{ marginBottom: 16 }}>
                <ModuleCountBanner total={allMods.length} online={onlineCount} />
            </div>

            {/* Quick actions */}
            <div style={{
                marginBottom: 16, padding: '12px 16px',
                background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10
            }}>
                <QuickActions />
            </div>

            {/* OS Tool Executor */}
            <OSToolExecutor />

            {/* Module groups */}
            {MODULE_GROUPS.map(grp => (
                <div key={grp.group} style={{ marginBottom: 16 }}>
                    <div style={{
                        fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: 2,
                        color: grp.color, marginBottom: 8, fontWeight: 600,
                    }}>
                        {grp.group}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
                        {grp.modules.map(mod => (
                            <ModuleCard key={mod.key} mod={mod} color={grp.color} />
                        ))}
                    </div>
                </div>
            ))}

            <div style={{ marginTop: 8, fontSize: '0.62rem', opacity: 0.25, textAlign: 'center' }}>
                "Not just software — civilization architecture for 8 billion people."
            </div>
        </div>
    );
}
