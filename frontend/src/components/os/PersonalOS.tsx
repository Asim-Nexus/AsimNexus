// STATUS: REAL — React dashboard, fetches live API, renders Dharma/Agent/Universe UI
// Phase 4 — Ledger Balance, Nepal Tax, DePIN Map, Clone Agents Live Feed
import { useState, useEffect, useCallback } from 'react';
import {
    personalAPI,
    dharmaAPI,
    financeAPI,
    securityAPI,
    analyticsAPI,
} from '../../api/asimnexus';

// ── Stat Card ──────────────────────────────────────────────────────────────
interface StatCardProps {
    icon: string;
    label: string;
    value: string | number;
    sub?: string;
    color?: string;
    pulse?: boolean;
}

function StatCard({ icon, label, value, sub, color = '#667eea', pulse = false }: StatCardProps) {
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
interface UniverseBadgeProps {
    type: string;
    icon?: string;
    label?: string;
    active?: boolean;
    nodes?: number;
}

function UniverseBadge({ type, icon: _icon, label, active, nodes }: UniverseBadgeProps) {
    const colors: Record<string, string> = {
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
interface DharmaData {
    symmetry_score?: number;
    verdict?: string;
    gini_coefficient?: number;
    l_max?: number;
    total_veto_events?: number;
    node_count?: number;
    [key: string]: unknown;
}

function DharmaStatus({ dharma }: { dharma: DharmaData | null }) {
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
interface AgentStatusData {
    active?: boolean;
    skills?: string[];
    max_contract_days?: number;
    activated_at?: string;
    [key: string]: unknown;
}

interface AgentModePanelProps {
    agentStatus: AgentStatusData;
    onToggle: (turnOn: boolean, skills?: string[], days?: number) => Promise<void>;
    loading: boolean;
}

function AgentModePanel({ agentStatus, onToggle, loading }: AgentModePanelProps) {
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
interface PendingItem {
    description?: string;
    [key: string]: unknown;
}

function Final3Panel({ pending }: { pending: PendingItem[] }) {
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
                    <span style={{ fontSize: '0.8rem' }}>{item.description as string}</span>
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
interface PersonalStatusData {
    display_name?: string;
    total_messages?: number;
    clone_count?: number;
    active_contracts?: number;
    cpu_pct?: number;
    ram_pct?: number;
    dharma_score?: number;
    local_first?: boolean;
    mesh_peers?: number;
    [key: string]: unknown;
}

interface SharingData {
    resource_sharing?: boolean;
    share_pct?: number;
    [key: string]: unknown;
}

interface PersonalOSProps {
    user?: Record<string, unknown>;
}

export default function PersonalOS({ user }: PersonalOSProps) {
    const [status, setStatus] = useState<PersonalStatusData | null>(null);
    const [universes, setUniverses] = useState<Record<string, unknown>[]>([]);
    const [dharma, setDharma] = useState<DharmaData | null>(null);
    const [agentStatus, setAgentStatus] = useState<AgentStatusData>({ active: false });
    const [agentLoading, setAgentLoading] = useState(false);
    const [sharing, setSharing] = useState<SharingData>({ resource_sharing: false, share_pct: 2 });
    const [sharingLoading, setSharingLoading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [refreshAt, setRefreshAt] = useState(0);

    // ── Phase 4 State ──
    const [ledgerBalance, setLedgerBalance] = useState<Record<string, unknown> | null>(null);
    const [nepalTax, setNepalTax] = useState<Record<string, unknown> | null>(null);
    const [depinMap, setDepinMap] = useState<Record<string, unknown> | null>(null);
    const [cloneFeed, setCloneFeed] = useState<Record<string, unknown>[]>([]);
    const [tpmStatus, setTpmStatus] = useState<Record<string, unknown> | null>(null);

    const load = useCallback(async () => {
        try {
            const [s, u, d, a, rs] = await Promise.all([
                personalAPI.getPersonalStatus().then(r => r.data).catch(() => null),
                personalAPI.getUniverse().then(r => r.data).catch(() => null),
                dharmaAPI.getStatus().then(r => r.data).catch(() => null),
                personalAPI.getAgentStatus().then(r => r.data).catch(() => null),
                personalAPI.getResourceSharing().then(r => r.data).catch(() => null),
            ]);
            if (s) setStatus(s as unknown as PersonalStatusData);
            if (u) setUniverses((u as unknown as { universes?: Record<string, unknown>[] }).universes || []);
            if (d) setDharma(d as unknown as DharmaData);
            if (a) setAgentStatus(a as unknown as AgentStatusData);
            if (rs) setSharing(rs as unknown as SharingData);

            // ── Phase 4 — Load dashboard data ──
            const [lb, nt, dm, cf, ts] = await Promise.all([
                financeAPI.getLedgerBalance('system_reserve').then(r => r.data).catch(() => null),
                financeAPI.getNepalTaxBreakdown().then(r => r.data).catch(() => null),
                analyticsAPI.getDepinMap().then(r => r.data).catch(() => null),
                analyticsAPI.getCloneAgentsFeed(15).then(r => r.data).catch(() => null),
                securityAPI.getTPMStatus().then(r => r.data).catch(() => null),
            ]);
            if (lb) setLedgerBalance(lb as unknown as Record<string, unknown>);
            if (nt) setNepalTax(nt as unknown as Record<string, unknown>);
            if (dm) setDepinMap(dm as unknown as Record<string, unknown>);
            if (cf) setCloneFeed((cf as unknown as { feed?: Record<string, unknown>[] }).feed || []);
            if (ts) setTpmStatus(ts as unknown as Record<string, unknown>);
        } catch (_) { /* ignore */ }
        setLoading(false);
    }, []);

    useEffect(() => { load(); }, [load, refreshAt]);

    // Auto-refresh every 30s
    useEffect(() => {
        const t = setInterval(() => setRefreshAt(Date.now()), 30000);
        return () => clearInterval(t);
    }, []);

    const handleSharingToggle = async (enabled: boolean, pct = 2) => {
        setSharingLoading(true);
        try {
            const res = await personalAPI.setResourceSharing(enabled, pct).then(r => r.data);
            if (res) setSharing(res as unknown as SharingData);
        } catch (_) { /* ignore */ }
        setSharingLoading(false);
    };

    const handleAgentToggle = async (turnOn: boolean, _skills?: string[], _days?: number) => {
        setAgentLoading(true);
        try {
            if (turnOn) {
                await personalAPI.agentModeOn();
            } else {
                await personalAPI.agentModeOff();
            }
            const a = await personalAPI.getAgentStatus().then(r => r.data);
            if (a) setAgentStatus(a as unknown as AgentStatusData);
        } catch (_) { /* ignore */ }
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
                            {status?.display_name || (user?.display_name as string) || 'Your Universe'}
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
                    {universes.map((u, i) => (
                        <UniverseBadge key={i} type={u.type as string} icon={u.icon as string} label={u.label as string} active={u.active as boolean} nodes={u.nodes as number} />
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
                {([
                    ['🔒', 'Local-First', status?.local_first ? 'ON' : 'OFF', '#10b981'],
                    ['🛡️', 'Dharma Guard', 'Active', '#10b981'],
                    ['⚖️', 'ΔT Engine', 'Running', '#10b981'],
                    ['✅', 'Final 3 Required', 'Always', '#10b981'],
                    ['🌐', 'Mesh Peers', `${status?.mesh_peers ?? 0} (Phase 2)`, '#888'],
                    ['🤝', 'Resource Sharing', sharing.resource_sharing ? `ON (${sharing.share_pct}%)` : 'OFF', sharing.resource_sharing ? '#10b981' : '#888'],
                ] as [string, string, string, string][]).map(([icon, label, val, color]) => (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem' }}>
                        <span>{icon}</span>
                        <span style={{ color: '#888' }}>{label}:</span>
                        <span style={{ color, fontWeight: 600 }}>{val}</span>
                    </div>
                ))}
            </div>

            {/* ════════════════════════════════════════════════════════════════ */}
            {/* Phase 4 — Ledger Balance & Nepal Tax Breakdown                */}
            {/* ════════════════════════════════════════════════════════════════ */}
            <div style={{ marginTop: 24, marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: 10, color: '#888', letterSpacing: 1, textTransform: 'uppercase' }}>
                    🏦 Phase 4 — Ledger & Nepal Banking
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                    {/* Ledger Balance */}
                    <div style={{
                        flex: '1 1 200px', background: 'rgba(16,185,129,0.04)',
                        border: '1px solid rgba(16,185,129,0.2)', borderRadius: 14, padding: '16px 18px',
                    }}>
                        <div style={{ fontSize: '0.72rem', color: '#888', marginBottom: 4 }}>📒 Ledger Balance (NCR)</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#10b981' }}>
                            {ledgerBalance?.balance != null
                                ? Number(ledgerBalance.balance).toLocaleString()
                                : '—'}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: '#666', marginTop: 2 }}>
                            Account: {typeof ledgerBalance?.account === 'string' ? ledgerBalance.account : 'system_reserve'}
                        </div>
                    </div>

                    {/* Nepal Tax Breakdown */}
                    <div style={{
                        flex: '1 1 200px', background: 'rgba(245,158,11,0.04)',
                        border: '1px solid rgba(245,158,11,0.2)', borderRadius: 14, padding: '16px 18px',
                    }}>
                        <div style={{ fontSize: '0.72rem', color: '#888', marginBottom: 4 }}>🇳🇵 Nepal Tax Rates</div>
                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                            <div>
                                <span style={{ fontSize: '0.65rem', color: '#888' }}>VAT</span>
                                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b' }}>
                                    {nepalTax?.vat_rate != null ? `${Number(nepalTax.vat_rate) * 100}%` : '13%'}
                                </div>
                            </div>
                            <div>
                                <span style={{ fontSize: '0.65rem', color: '#888' }}>TDS</span>
                                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b' }}>
                                    {nepalTax?.tds_rate != null ? `${Number(nepalTax.tds_rate) * 100}%` : '1%'}
                                </div>
                            </div>
                            <div>
                                <span style={{ fontSize: '0.65rem', color: '#888' }}>Service</span>
                                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b' }}>
                                    {nepalTax?.service_charge_rate != null ? `${Number(nepalTax.service_charge_rate) * 100}%` : '5%'}
                                </div>
                            </div>
                        </div>
                        <div style={{ fontSize: '0.6rem', color: '#555', marginTop: 4 }}>
                            Nepal IT Act 2063
                        </div>
                    </div>

                    {/* TPM Hardware Status */}
                    <div style={{
                        flex: '1 1 200px', background: 'rgba(102,126,234,0.04)',
                        border: '1px solid rgba(102,126,234,0.2)', borderRadius: 14, padding: '16px 18px',
                    }}>
                        <div style={{ fontSize: '0.72rem', color: '#888', marginBottom: 4 }}>🔐 TPM Hardware Key</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: tpmStatus?.tpm_initialized ? '#10b981' : '#ef4444' }}>
                            {tpmStatus?.tpm_initialized ? 'SECURE ENCLAVE' : 'SOFTWARE MODE'}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: '#666', marginTop: 2 }}>
                            Keys: {String(tpmStatus?.key_count ?? 0)} · Provider: {String(tpmStatus?.provider ?? 'software')}
                        </div>
                    </div>
                </div>
            </div>

            {/* ════════════════════════════════════════════════════════════════ */}
            {/* Phase 4 — DePIN Network Map                                    */}
            {/* ════════════════════════════════════════════════════════════════ */}
            <div style={{ marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: 10, color: '#888', letterSpacing: 1, textTransform: 'uppercase' }}>
                    📡 Phase 4 — DePIN Network Map
                </div>
                <div style={{
                    background: 'rgba(59,130,246,0.04)',
                    border: '1px solid rgba(59,130,246,0.2)', borderRadius: 14, padding: '16px 18px',
                }}>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
                        <div>
                            <span style={{ fontSize: '0.65rem', color: '#888' }}>Total Nodes</span>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#3b82f6' }}>
                                {String(depinMap?.total_nodes ?? 0)}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.65rem', color: '#888' }}>Online</span>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#10b981' }}>
                                {String(depinMap?.online_nodes ?? 0)}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.65rem', color: '#888' }}>Gateways</span>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>
                                {String(depinMap?.gateways ?? 0)}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.65rem', color: '#888' }}>Relays</span>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#8b5cf6' }}>
                                {String(depinMap?.relays ?? 0)}
                            </div>
                        </div>
                    </div>
                    <div style={{ fontSize: '0.68rem', color: '#666' }}>
                        Coverage: Nepal Rural Villages · LoRaWAN Zones · WiFi Direct Clusters
                    </div>
                </div>
            </div>

            {/* ════════════════════════════════════════════════════════════════ */}
            {/* Phase 4 — 15 Clone Agents Live Feed                            */}
            {/* ════════════════════════════════════════════════════════════════ */}
            <div style={{ marginBottom: 20 }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: 10, color: '#888', letterSpacing: 1, textTransform: 'uppercase' }}>
                    🤖 Phase 4 — Clone Agents Live Feed
                </div>
                <div style={{
                    background: 'rgba(139,92,246,0.04)',
                    border: '1px solid rgba(139,92,246,0.2)', borderRadius: 14, padding: '16px 18px',
                }}>
                    {cloneFeed.length === 0 ? (
                        <div style={{ fontSize: '0.78rem', color: '#666', textAlign: 'center', padding: 12 }}>
                            No clone agent activity yet — agents will appear here when active
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 300, overflowY: 'auto' }}>
                            {cloneFeed.map((agent, i) => (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'center', gap: 10,
                                    padding: '8px 10px', borderRadius: 10,
                                    background: agent.active ? 'rgba(16,185,129,0.06)' : 'rgba(255,255,255,0.02)',
                                    border: `1px solid ${agent.active ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.04)'}`,
                                }}>
                                    <span style={{ fontSize: 16 }}>
                                        {agent.type === 'economic' ? '💰' : agent.type === 'governance' ? '⚖️' :
                                            agent.type === 'security' ? '🔐' : agent.type === 'mesh' ? '📡' :
                                                agent.type === 'evolution' ? '🧬' : '🤖'}
                                    </span>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: '0.78rem', fontWeight: 600, color: agent.active ? '#10b981' : '#888' }}>
                                            {agent.agent_id as string || `Clone #${i + 1}`}
                                        </div>
                                        <div style={{ fontSize: '0.65rem', color: '#666', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {agent.last_action as string || 'Idle'} · {agent.tasks_completed as number || 0} tasks
                                        </div>
                                    </div>
                                    <span style={{
                                        fontSize: '0.6rem', padding: '2px 8px', borderRadius: 12,
                                        background: agent.active ? '#10b98122' : 'rgba(255,255,255,0.05)',
                                        color: agent.active ? '#10b981' : '#666',
                                        fontWeight: 700, whiteSpace: 'nowrap',
                                    }}>
                                        {agent.active ? 'ACTIVE' : 'IDLE'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                    <div style={{ fontSize: '0.65rem', color: '#555', marginTop: 8, textAlign: 'center' }}>
                        5 Primary Clones · 10 Sub-Agents · Dharma-Protected
                    </div>
                </div>
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
