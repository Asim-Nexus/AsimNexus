import React, { useState, useEffect, useCallback } from 'react';
import { meshAPI } from '../../api/asimnexus';

interface MeshStatusData {
    air_gap?: {
        level?: number;
        engaged?: boolean;
        engaged_for_s?: number;
        event_count?: number;
        rules?: Record<string, boolean>;
        recent_events?: Array<{
            timestamp: string;
            level_from: number;
            level_to: number;
            triggered_by: string;
            reason: string;
        }>;
    };
    discovery?: {
        running?: boolean;
        local_ip?: string;
        peer_count?: number;
    };
    p2p?: {
        running?: boolean;
        node_id?: string;
        port?: number;
        peer_count?: number;
    };
}

interface PeerData {
    ip: string;
    port: number;
    node_id: string;
    universe: string;
    version: string;
    via: string;
    trusted?: boolean;
    is_stale?: boolean;
}

const card: React.CSSProperties = {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 12, padding: 16, marginBottom: 12,
};
const btn = (color = '#667eea', small = false): React.CSSProperties => ({
    background: color, border: 'none', borderRadius: 8,
    color: '#fff', cursor: 'pointer',
    fontSize: small ? 11 : 13, fontWeight: 600,
    padding: small ? '5px 10px' : '8px 18px', marginRight: 6,
});
const inp: React.CSSProperties = {
    background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: 8, color: '#fff', fontSize: 13, padding: '7px 12px',
};

const AIR_GAP_COLORS: Record<number, string> = {
    0: '#10b981', 1: '#f59e0b', 2: '#fb923c', 3: '#ef4444', 4: '#7f1d1d',
};
const AIR_GAP_LABELS: Record<number, string> = {
    0: '🟢 Normal', 1: '🟡 Reduced', 2: '🟠 LAN Only', 3: '🔴 Isolated', 4: '⛔ Emergency',
};

export default function MeshPanel() {
    const [status, setStatus] = useState<MeshStatusData | null>(null);
    const [peers, setPeers] = useState<PeerData[]>([]);
    const [addIp, setAddIp] = useState('');
    const [addPort, setAddPort] = useState('8765');
    const [msg, setMsg] = useState('');
    const [loading, setLoading] = useState(false);

    const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 3500); };

    const load = useCallback(async () => {
        try {
            const [s, p] = await Promise.all([
                meshAPI.getStatus().then(r => r.data as MeshStatusData),
                meshAPI.getPeers().then(r => r.data as { peers?: PeerData[] }),
            ]);
            setStatus(s as MeshStatusData);
            setPeers((p as { peers?: PeerData[] }).peers || []);
        } catch { }
    }, []);

    useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, [load]);

    const startDiscovery = async () => {
        setLoading(true);
        try {
            const r = await meshAPI.discoverStart();
            if (r.data) { flash('🔍 LAN discovery started!'); await load(); }
        } catch (e) { flash(`❌ ${(e as Error).message}`); }
        finally { setLoading(false); }
    };

    const addPeer = async () => {
        if (!addIp) { flash('❌ Enter an IP address'); return; }
        setLoading(true);
        try {
            const r = await meshAPI.addPeer(addIp, parseInt(addPort));
            const rData = r.data as unknown as Record<string, unknown>;
            if (rData?.ip) { flash(`✅ Peer added: ${rData.ip}`); setAddIp(''); await load(); }
        } catch (e) { flash(`❌ ${(e as Error).message}`); }
        finally { setLoading(false); }
    };

    const engageAirGap = async (level: number) => {
        const labels: Record<number, string> = { 1: 'Reduced', 2: 'LAN Only', 3: 'Isolated', 4: 'EMERGENCY' };
        if (level >= 3 && !window.confirm(`Engage ${labels[level]} air-gap? This will restrict network access.`)) return;
        setLoading(true);
        try {
            const r = await meshAPI.airGapEngage(level, 'Human-initiated');
            const rData = r.data as unknown as Record<string, unknown>;
            if (r.data) { flash(`🔴 Air-gap: ${rData.label}`); await load(); }
        } catch (e) { flash(`❌ ${(e as Error).message}`); }
        finally { setLoading(false); }
    };

    const disengage = async () => {
        setLoading(true);
        try {
            const r = await meshAPI.airGapDisengage();
            if (r.data) { flash('🟢 Air-gap disengaged — back to normal'); await load(); }
        } catch (e) { flash(`❌ ${(e as Error).message}`); }
        finally { setLoading(false); }
    };

    const ag = status?.air_gap;
    const disc = status?.discovery;
    const p2p = status?.p2p;
    const agLevel = ag?.level ?? 0;

    return (
        <div style={{ color: '#fff', fontFamily: 'system-ui,sans-serif', maxWidth: 860 }}>

            {/* Header */}
            <div style={{ marginBottom: 20 }}>
                <h2 style={{ margin: 0, fontSize: 22 }}>🌐 LAN Mesh Network</h2>
                <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: 13 }}>
                    Local-first P2P · No cloud required · Air-gap emergency isolation
                </p>
            </div>

            {msg && (
                <div style={{
                    ...card, background: 'rgba(102,126,234,0.2)',
                    border: '1px solid #667eea', padding: '10px 16px', fontSize: 13
                }}>
                    {msg}
                </div>
            )}

            {/* Status row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 16 }}>
                {/* Discovery */}
                <div style={card}>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6 }}>📡 DISCOVERY</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: disc?.running ? '#34d399' : '#94a3b8' }}>
                        {disc?.running ? '● Live' : '○ Stopped'}
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                        Local IP: {disc?.local_ip || '—'}
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>
                        Peers: {disc?.peer_count ?? 0}
                    </div>
                    {!disc?.running && (
                        <button style={{ ...btn('#667eea', true), marginTop: 8 }} onClick={startDiscovery} disabled={loading}>
                            Start Discovery
                        </button>
                    )}
                </div>

                {/* P2P Node */}
                <div style={card}>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6 }}>🔗 P2P NODE</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: p2p?.running ? '#34d399' : '#94a3b8' }}>
                        {p2p?.running ? '● Running' : '○ Standby'}
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                        ID: {p2p?.node_id || '—'}
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>
                        Port: {p2p?.port || 8765} · Peers: {p2p?.peer_count ?? 0}
                    </div>
                </div>

                {/* Air-Gap */}
                <div style={{
                    ...card, border: `1px solid ${AIR_GAP_COLORS[agLevel]}44`,
                    background: agLevel > 0 ? `${AIR_GAP_COLORS[agLevel]}11` : 'rgba(255,255,255,0.05)'
                }}>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6 }}>🛡️ AIR-GAP</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: AIR_GAP_COLORS[agLevel] }}>
                        {AIR_GAP_LABELS[agLevel]}
                    </div>
                    {ag?.engaged && (
                        <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                            Active {ag.engaged_for_s}s · {ag.event_count} events
                        </div>
                    )}
                    {agLevel > 0 && (
                        <button style={{ ...btn('#10b981', true), marginTop: 8 }} onClick={disengage} disabled={loading}>
                            🟢 Disengage
                        </button>
                    )}
                </div>
            </div>

            {/* Air-Gap Control Panel */}
            <div style={{ ...card, marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>🚨 Emergency Air-Gap Control</div>
                <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>
                    Instantly restrict network access. Only <strong>you</strong> can re-enable it.
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {[
                        { level: 1, label: '🟡 Reduced', color: '#f59e0b', desc: 'Block cloud' },
                        { level: 2, label: '🟠 LAN Only', color: '#fb923c', desc: 'Block outbound' },
                        { level: 3, label: '🔴 Isolated', color: '#ef4444', desc: 'Block all' },
                        { level: 4, label: '⛔ Emergency', color: '#7f1d1d', desc: 'Total lockdown' },
                    ].map(l => (
                        <button
                            key={l.level}
                            style={{ ...btn(l.color, true), opacity: agLevel === l.level ? 1 : 0.7 }}
                            onClick={() => engageAirGap(l.level)}
                            disabled={loading || agLevel === l.level}
                            title={l.desc}
                        >
                            {l.label}
                        </button>
                    ))}
                    {agLevel > 0 && (
                        <button style={btn('#10b981', true)} onClick={disengage} disabled={loading}>
                            🟢 Back to Normal
                        </button>
                    )}
                </div>

                {/* Traffic rules */}
                {ag?.rules && (
                    <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                        {Object.entries(ag.rules).map(([k, v]) => (
                            <span key={k} style={{
                                fontSize: 11, padding: '3px 8px', borderRadius: 6,
                                background: v ? 'rgba(52,211,153,0.15)' : 'rgba(239,68,68,0.15)',
                                color: v ? '#34d399' : '#f87171',
                                border: `1px solid ${v ? 'rgba(52,211,153,0.3)' : 'rgba(239,68,68,0.3)'}`,
                            }}>
                                {k}: {v ? '✅' : '🚫'}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Add peer manually */}
            <div style={{ ...card, marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>➕ Add Peer Manually</div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <input style={{ ...inp, flex: 2 }} placeholder="IP address (e.g. 192.168.1.5)"
                        value={addIp} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAddIp(e.target.value)}
                        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && addPeer()} />
                    <input style={{ ...inp, width: 80 }} placeholder="Port"
                        value={addPort} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAddPort(e.target.value)} />
                    <button style={btn('#667eea')} onClick={addPeer} disabled={loading || !addIp}>
                        Add Peer
                    </button>
                </div>
            </div>

            {/* Peers list */}
            <div style={card}>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>
                    🌍 Known Peers ({peers.length})
                </div>
                {peers.length === 0 ? (
                    <div style={{ color: '#64748b', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
                        No peers discovered yet. Start discovery or add peers manually.
                    </div>
                ) : (
                    peers.map((p, i) => (
                        <div key={i} style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: '10px 12px', borderRadius: 8, marginBottom: 6,
                            background: p.is_stale ? 'rgba(239,68,68,0.06)' : 'rgba(52,211,153,0.06)',
                            border: `1px solid ${p.is_stale ? 'rgba(239,68,68,0.15)' : 'rgba(52,211,153,0.15)'}`,
                        }}>
                            <div>
                                <span style={{ fontWeight: 600, fontSize: 13 }}>{p.ip}:{p.port}</span>
                                <span style={{ marginLeft: 10, fontSize: 11, color: '#94a3b8' }}>
                                    {p.node_id} · {p.universe} · v{p.version}
                                </span>
                            </div>
                            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                                <span style={{ fontSize: 11, color: '#64748b' }}>via {p.via}</span>
                                {p.trusted && <span style={{ fontSize: 11, color: '#34d399' }}>🤝 trusted</span>}
                                {p.is_stale && <span style={{ fontSize: 11, color: '#f87171' }}>⚠️ stale</span>}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Recent air-gap events */}
            {ag?.recent_events && ag.recent_events.length > 0 && (
                <div style={card}>
                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>📋 Air-Gap History</div>
                    {ag.recent_events.map((e, i) => (
                        <div key={i} style={{
                            fontSize: 11, color: '#94a3b8', padding: '4px 0',
                            borderBottom: '1px solid rgba(255,255,255,0.04)'
                        }}>
                            {e.timestamp} — Level {e.level_from}→{e.level_to} by <strong>{e.triggered_by}</strong>: {e.reason}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
