/**
 * MCPPanel.tsx
 * AsimNexus — Dharma-Gated MCP Monitor
 *
 * Shows:
 *  - MCP Server status + 4 Dharma layers
 *  - Live tool call tester
 *  - Pending Final-3 approvals (with Approve/Reject)
 *  - Recent audit log
 */
import { useState, useEffect, useCallback } from 'react';
import { mcpAPI } from '../../api';

const RISK_COLOR: Record<string, string> = {
    safe: '#10b981',
    moderate: '#f59e0b',
    high: '#ef4444',
    critical: '#7c3aed',
};

const VERDICT_COLOR: Record<string, string> = {
    allowed: '#10b981',
    vetoed: '#ef4444',
    pending_human: '#f59e0b',
    rate_limited: '#888',
};

interface LayerBadgeProps {
    icon: string;
    label: string;
    active: boolean;
}

function LayerBadge({ icon, label, active }: LayerBadgeProps) {
    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: active ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.03)',
            border: `1px solid ${active ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'}`,
            borderRadius: 10, padding: '6px 12px', fontSize: '0.75rem',
        }}>
            <span>{icon}</span>
            <span style={{ color: active ? '#10b981' : '#666', fontWeight: active ? 700 : 400 }}>{label}</span>
            <span style={{ marginLeft: 'auto', color: active ? '#10b981' : '#555', fontSize: '0.65rem' }}>
                {active ? 'ON' : 'OFF'}
            </span>
        </div>
    );
}

interface VerdictBadgeProps {
    verdict: string;
}

function VerdictBadge({ verdict }: VerdictBadgeProps) {
    const color = VERDICT_COLOR[verdict] || '#888';
    const icons: Record<string, string> = { allowed: '✅', vetoed: '🛑', pending_human: '⏳', rate_limited: '⏸' };
    return (
        <span style={{
            background: `${color}22`, border: `1px solid ${color}55`,
            color, borderRadius: 8, padding: '2px 10px', fontSize: '0.7rem', fontWeight: 700,
        }}>
            {icons[verdict] || '?'} {verdict?.replace('_', ' ').toUpperCase()}
        </span>
    );
}

interface PendingCallData {
    call_id: string;
    tool_name: string;
    risk: string;
    timestamp: string;
    parameters: Record<string, unknown>;
}

interface PendingCardProps {
    call: PendingCallData;
    onApprove: (callId: string) => void;
    onReject: (callId: string) => void;
    loading: boolean;
}

function PendingCard({ call, onApprove, onReject, loading }: PendingCardProps) {
    return (
        <div style={{
            background: 'rgba(245,158,11,0.06)',
            border: '1px solid rgba(245,158,11,0.25)',
            borderRadius: 12, padding: '14px 16px', marginBottom: 10,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>⏳ {call.tool_name}</span>
                    <span style={{
                        marginLeft: 8, fontSize: '0.65rem', fontWeight: 700,
                        color: RISK_COLOR[call.risk] || '#888',
                        background: `${RISK_COLOR[call.risk]}22`, borderRadius: 6, padding: '1px 8px',
                    }}>
                        {call.risk?.toUpperCase()}
                    </span>
                </div>
                <span style={{ fontSize: '0.65rem', color: '#666' }}>{call.timestamp?.slice(11, 19)} UTC</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#888', marginBottom: 10, fontFamily: 'monospace' }}>
                {JSON.stringify(call.parameters, null, 1).slice(0, 120)}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
                <button
                    onClick={() => onApprove(call.call_id)}
                    disabled={loading}
                    style={{
                        background: '#10b981', border: 'none', color: '#fff',
                        padding: '5px 16px', borderRadius: 12, cursor: 'pointer',
                        fontSize: '0.75rem', fontWeight: 700,
                    }}>
                    {loading ? '...' : '✅ Approve'}
                </button>
                <button
                    onClick={() => onReject(call.call_id)}
                    disabled={loading}
                    style={{
                        background: '#ef4444', border: 'none', color: '#fff',
                        padding: '5px 16px', borderRadius: 12, cursor: 'pointer',
                        fontSize: '0.75rem', fontWeight: 700,
                    }}>
                    🚫 Reject
                </button>
                <span style={{ fontSize: '0.65rem', color: '#666', alignSelf: 'center', marginLeft: 4 }}>
                    Call ID: {call.call_id}
                </span>
            </div>
        </div>
    );
}

interface MCPPanelProps {
    user?: Record<string, unknown>;
}

interface StatusData {
    layers?: Record<string, boolean>;
    tools_registered?: number;
}

interface ToolData {
    name: string;
    risk: string;
    available: boolean;
}

interface AuditEntry {
    verdict: string;
    tool_name: string;
    risk: string;
    timestamp: string;
    veto_reason?: string;
}

interface CallResultData {
    verdict?: string;
    execution_ms?: number;
    dharma_score?: number;
    veto_reason?: string;
    error?: string;
    output?: unknown;
    requires_human?: boolean;
}

export default function MCPPanel({ user: _user }: MCPPanelProps) {
    const [status, setStatus] = useState<StatusData | null>(null);
    const [tools, setTools] = useState<ToolData[]>([]);
    const [pending, setPending] = useState<PendingCallData[]>([]);
    const [audit, setAudit] = useState<AuditEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    // Tool call tester state
    const [selectedTool, setSelectedTool] = useState('file_list');
    const [params, setParams] = useState('{"path": "."}');
    const [callResult, setCallResult] = useState<CallResultData | null>(null);
    const [callLoading, setCallLoading] = useState(false);

    const load = useCallback(async () => {
        const [s, t, p, a] = await Promise.all([
            mcpAPI.status().then((r: unknown) => (r as { data: StatusData }).data).catch(() => null),
            mcpAPI.tools().then((r: unknown) => (r as { data: { tools?: ToolData[] } }).data).catch(() => null),
            mcpAPI.pending().then((r: unknown) => (r as { data: { pending?: PendingCallData[] } }).data).catch(() => null),
            mcpAPI.audit(20).then((r: unknown) => (r as { data: { audit?: AuditEntry[] } }).data).catch(() => null),
        ]);
        if (s) setStatus(s);
        if (t) setTools(t.tools || []);
        if (p) setPending(p.pending || []);
        if (a) setAudit(a.audit || []);
        setLoading(false);
    }, []);

    useEffect(() => { load(); }, [load]);

    // Poll pending every 5s
    useEffect(() => {
        const t = setInterval(async () => {
            const p = await mcpAPI.pending().then((r: unknown) => (r as { data: { pending?: PendingCallData[] } }).data).catch(() => null);
            if (p) setPending(p.pending || []);
        }, 5000);
        return () => clearInterval(t);
    }, []);

    const handleApprove = async (callId: string) => {
        setActionLoading(true);
        await mcpAPI.approve(callId).catch(() => { });
        await load();
        setActionLoading(false);
    };

    const handleReject = async (callId: string) => {
        setActionLoading(true);
        await mcpAPI.reject(callId).catch(() => { });
        await load();
        setActionLoading(false);
    };

    const handleCallTool = async () => {
        setCallLoading(true);
        setCallResult(null);
        try {
            const parsedParams = JSON.parse(params);
            const r = await mcpAPI.call(selectedTool, parsedParams) as unknown as { data: CallResultData };
            setCallResult(r.data);
            // Refresh audit
            const a = await mcpAPI.audit(20).then((r: unknown) => (r as { data: { audit?: AuditEntry[] } }).data).catch(() => null);
            if (a) setAudit(a.audit || []);
            const p = await mcpAPI.pending().then((r: unknown) => (r as { data: { pending?: PendingCallData[] } }).data).catch(() => null);
            if (p) setPending(p.pending || []);
        } catch (e: unknown) {
            setCallResult({ error: `JSON parse error: ${(e as Error).message}` });
        }
        setCallLoading(false);
    };

    // Update default params when tool changes
    const toolParamDefaults: Record<string, string> = {
        file_list: '{"path": "."}',
        file_read: '{"path": "readme.txt"}',
        file_write: '{"path": "notes.txt", "content": "Hello from AsimNexus!"}',
        file_delete: '{"path": "old_file.txt"}',
        get_system_info: '{}',
        run_command: '{"command": "echo", "args": ["Jay Dharma-Chakra"]}',
        memory_save: '{"key": "note1", "value": "Remember this!", "category": "personal"}',
        memory_search: '{"query": "Jay", "limit": 5}',
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#667eea' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}>⚙️</div>
                    <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>Loading DharmaMCP...</div>
                </div>
            </div>
        );
    }

    const layers = status?.layers || {};
    const registeredTools = tools.filter(t => t.available);
    const allTools = tools;

    return (
        <div style={{ padding: '20px 24px', maxWidth: 960, margin: '0 auto', color: '#fff' }}>

            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 6 }}>
                    <div style={{
                        width: 52, height: 52, borderRadius: '50%',
                        background: 'linear-gradient(135deg,#7c3aed,#667eea)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
                    }}>⚙️</div>
                    <div>
                        <div style={{ fontSize: '1.35rem', fontWeight: 800 }}>Dharma-Gated MCP</div>
                        <div style={{ fontSize: '0.75rem', color: '#888' }}>
                            Model Context Protocol 2.0 · Every tool call Dharma-filtered
                        </div>
                    </div>
                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {pending.length > 0 && (
                            <span style={{
                                background: '#ef4444', color: '#fff', borderRadius: 20,
                                padding: '3px 12px', fontSize: '0.72rem', fontWeight: 700,
                            }}>
                                {pending.length} Pending Approval{pending.length > 1 ? 's' : ''}
                            </span>
                        )}
                        <button onClick={load} style={{
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: 10, color: '#888', padding: '6px 14px',
                            cursor: 'pointer', fontSize: '0.75rem',
                        }}>↻ Refresh</button>
                    </div>
                </div>
            </div>

            {/* Dharma Layers */}
            <div style={{ marginBottom: 20 }}>
                <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#888', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Dharma Security Layers
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: 8 }}>
                    <LayerBadge icon="🛡️" label="Dharma-Chakra Veto" active={!!layers.dharma_veto} />
                    <LayerBadge icon="⚖️" label="ΔT Anti-Concentration" active={!!layers.delta_t_engine} />
                    <LayerBadge icon="✅" label="Final 3 Confirmation" active={!!layers.final3_confirmation} />
                    <LayerBadge icon="📋" label="Immutable Audit Log" active={!!layers.audit_log} />
                    <LayerBadge icon="🔒" label="Sandboxed File System" active={!!layers.sandboxed_fs} />
                </div>
            </div>

            {/* Stats row */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
                {([
                    ['⚙️', 'Tools Registered', status?.tools_registered ?? 0, '#667eea'],
                    ['✅', 'Available Tools', registeredTools.length, '#10b981'],
                    ['⏳', 'Pending Approvals', pending.length, pending.length > 0 ? '#ef4444' : '#888'],
                    ['📋', 'Audit Entries', audit.length, '#f59e0b'],
                ] as [string, string, number, string][]).map(([icon, label, val, color]) => (
                    <div key={label} style={{
                        background: 'rgba(255,255,255,0.03)',
                        border: `1px solid ${color}33`,
                        borderRadius: 12, padding: '12px 18px', minWidth: 120,
                        display: 'flex', flexDirection: 'column', alignItems: 'center',
                    }}>
                        <span style={{ fontSize: 20, marginBottom: 4 }}>{icon}</span>
                        <span style={{ fontSize: '1.2rem', fontWeight: 800, color }}>{val}</span>
                        <span style={{ fontSize: '0.65rem', color: '#666', textAlign: 'center' }}>{label}</span>
                    </div>
                ))}
            </div>

            {/* Pending Final-3 Approvals */}
            {pending.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                    <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#f59e0b', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                        ⏳ Final 3 — Awaiting Your Approval
                    </div>
                    {pending.map(call => (
                        <PendingCard
                            key={call.call_id}
                            call={call}
                            onApprove={handleApprove}
                            onReject={handleReject}
                            loading={actionLoading}
                        />
                    ))}
                </div>
            )}

            {/* Tool Tester */}
            <div style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(102,126,234,0.2)',
                borderRadius: 14, padding: '18px 20px', marginBottom: 20,
            }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', marginBottom: 14 }}>
                    🧪 Tool Call Tester
                    <span style={{ fontWeight: 400, fontSize: '0.7rem', color: '#666', marginLeft: 8 }}>
                        Every call passes through all Dharma layers
                    </span>
                </div>
                <div style={{ display: 'flex', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
                    <select
                        value={selectedTool}
                        onChange={e => {
                            setSelectedTool(e.target.value);
                            setParams(toolParamDefaults[e.target.value] || '{}');
                            setCallResult(null);
                        }}
                        style={{
                            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                            color: '#fff', borderRadius: 10, padding: '8px 12px', fontSize: '0.8rem',
                            minWidth: 180,
                        }}>
                        {allTools.map(t => (
                            <option key={t.name} value={t.name} style={{ background: '#1a1a2e' }}>
                                [{t.risk}] {t.name} {t.available ? '' : '(unavailable)'}
                            </option>
                        ))}
                    </select>
                    <button
                        onClick={handleCallTool}
                        disabled={callLoading}
                        style={{
                            background: 'linear-gradient(135deg,#667eea,#764ba2)',
                            border: 'none', color: '#fff', padding: '8px 20px',
                            borderRadius: 10, cursor: 'pointer', fontWeight: 700, fontSize: '0.8rem',
                        }}>
                        {callLoading ? '⏳ Calling...' : '▶ Call Tool'}
                    </button>
                </div>
                <textarea
                    value={params}
                    onChange={e => setParams(e.target.value)}
                    placeholder='{"key": "value"}'
                    style={{
                        width: '100%', background: 'rgba(0,0,0,0.3)',
                        border: '1px solid rgba(255,255,255,0.1)', color: '#10b981',
                        borderRadius: 10, padding: '10px 14px', fontFamily: 'monospace',
                        fontSize: '0.78rem', resize: 'vertical', minHeight: 60, boxSizing: 'border-box',
                    }}
                />
                {callResult && (
                    <div style={{
                        marginTop: 12,
                        background: `${VERDICT_COLOR[callResult.verdict || ''] || '#888'}11`,
                        border: `1px solid ${VERDICT_COLOR[callResult.verdict || ''] || '#888'}44`,
                        borderRadius: 10, padding: '12px 14px',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                            <VerdictBadge verdict={callResult.verdict || ''} />
                            {(callResult.execution_ms ?? 0) > 0 && (
                                <span style={{ fontSize: '0.65rem', color: '#666' }}>{callResult.execution_ms}ms</span>
                            )}
                            {(callResult.dharma_score ?? 0) > 0 && (
                                <span style={{ fontSize: '0.65rem', color: '#10b981' }}>
                                    Dharma: {Math.round((callResult.dharma_score ?? 0) * 100)}%
                                </span>
                            )}
                        </div>
                        {callResult.veto_reason && (
                            <div style={{ fontSize: '0.75rem', color: '#ef4444', marginBottom: 6 }}>
                                🛑 {callResult.veto_reason}
                            </div>
                        )}
                        {callResult.error && (
                            <div style={{ fontSize: '0.75rem', color: '#f59e0b', marginBottom: 6 }}>
                                {callResult.error}
                            </div>
                        )}
                        {!!callResult.output && (
                            <pre style={{
                                fontSize: '0.7rem', color: '#10b981', margin: 0,
                                maxHeight: 150, overflow: 'auto', whiteSpace: 'pre-wrap',
                            }}>
                                {JSON.stringify(callResult.output as Record<string, unknown>, null, 2).slice(0, 800)}
                            </pre>
                        )}
                        {callResult.requires_human && (
                            <div style={{ marginTop: 8, fontSize: '0.72rem', color: '#f59e0b', fontWeight: 600 }}>
                                ⏳ Moved to Pending Approvals — refresh to see it above.
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Tools Grid */}
            <div style={{ marginBottom: 20 }}>
                <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#888', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Registered Tools ({allTools.length})
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px,1fr))', gap: 8 }}>
                    {allTools.map(t => (
                        <div key={t.name} style={{
                            background: t.available ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.01)',
                            border: `1px solid ${t.available ? RISK_COLOR[t.risk] + '33' : 'rgba(255,255,255,0.05)'}`,
                            borderRadius: 10, padding: '10px 14px',
                            opacity: t.available ? 1 : 0.5,
                        }}>
                            <div style={{ fontWeight: 600, fontSize: '0.78rem', marginBottom: 4 }}>{t.name}</div>
                            <span style={{
                                fontSize: '0.65rem', fontWeight: 700,
                                color: RISK_COLOR[t.risk] || '#888',
                                background: `${RISK_COLOR[t.risk] || '#888'}22`,
                                borderRadius: 6, padding: '1px 8px',
                            }}>
                                {t.risk?.toUpperCase()}
                            </span>
                            {!t.available && (
                                <span style={{ fontSize: '0.6rem', color: '#555', marginLeft: 6 }}>not registered</span>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Audit Log */}
            <div style={{
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: 14, padding: '16px 20px',
            }}>
                <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#888', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
                    📋 Audit Log (last {audit.length})
                </div>
                {audit.length === 0 ? (
                    <div style={{ fontSize: '0.75rem', color: '#555', textAlign: 'center', padding: '20px 0' }}>
                        No tool calls yet. Use the tester above.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {[...audit].reverse().map((e, i) => (
                            <div key={i} style={{
                                display: 'flex', alignItems: 'center', gap: 10,
                                padding: '6px 10px', borderRadius: 8,
                                background: 'rgba(255,255,255,0.02)',
                                fontSize: '0.72rem',
                            }}>
                                <span style={{ width: 80, flexShrink: 0 }}>
                                    <VerdictBadge verdict={e.verdict} />
                                </span>
                                <span style={{ flex: 1, fontWeight: 600 }}>{e.tool_name}</span>
                                <span style={{
                                    fontSize: '0.65rem', fontWeight: 700,
                                    color: RISK_COLOR[e.risk] || '#888',
                                }}>
                                    {e.risk?.toUpperCase()}
                                </span>
                                <span style={{ color: '#555', fontSize: '0.65rem', flexShrink: 0 }}>
                                    {e.timestamp?.slice(11, 19)} UTC
                                </span>
                                {e.veto_reason && (
                                    <span style={{ color: '#ef4444', fontSize: '0.65rem' }} title={e.veto_reason}>🛑</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
