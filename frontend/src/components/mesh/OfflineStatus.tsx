/**
 * OfflineStatus — Offline-First State Panel
 * C4: Queued actions, sync pending, connectivity health, last known state
 */
import React, { useState, useEffect, useCallback } from 'react';
import { offlineAPI, meshAPI } from '../../api/asimnexus';

// ── Style helpers ──
const card: React.CSSProperties = {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
};

const btn = (color = '#667eea', small = false): React.CSSProperties => ({
    background: color,
    border: 'none',
    borderRadius: 8,
    color: '#fff',
    cursor: 'pointer',
    fontSize: small ? 11 : 13,
    fontWeight: 600,
    padding: small ? '5px 10px' : '8px 18px',
    marginRight: 6,
});

interface HealthInfo {
    level: string;
    color: string;
    label: string;
}

interface MeshStatusData {
    air_gap?: {
        level?: number;
        label?: string;
    };
    p2p?: {
        running?: boolean;
    };
    discovery?: {
        running?: boolean;
    };
    last_sync?: string;
}

interface SyncQueueItem {
    id?: string;
    status?: string;
    op_type?: string;
    type?: string;
    entity_type?: string;
    target?: string;
    created_at?: string;
    timestamp?: string;
}

interface OfflineStatusData {
    last_sync?: string;
    sync_mode?: string;
    state?: string;
    status?: string;
    pending_operations?: number;
    pending?: number;
    synced_entities?: number;
    entities?: number;
    last_active?: string;
    last_seen?: string;
}

interface OfflineCapsData {
    [key: string]: unknown;
}

interface OfflineStatusProps {
    user?: Record<string, unknown>;
}

/**
 * Compute connectivity health from mesh status + air-gap check
 */
function computeHealth(meshStatus: MeshStatusData | null): HealthInfo {
    if (!meshStatus) return { level: 'unknown', color: '#64748b', label: 'Unknown' };

    const agLevel = meshStatus.air_gap?.level ?? 0;
    const p2pRunning = meshStatus.p2p?.running;
    const discRunning = meshStatus.discovery?.running;

    if (agLevel >= 4) return { level: 'emergency', color: '#7f1d1d', label: '🚨 Emergency Isolation' };
    if (agLevel >= 3) return { level: 'isolated', color: '#ef4444', label: '🔴 Isolated' };
    if (agLevel >= 2) return { level: 'lan-only', color: '#fb923c', label: '🟠 LAN Only' };
    if (agLevel >= 1) return { level: 'reduced', color: '#f59e0b', label: '🟡 Reduced' };
    if (p2pRunning && discRunning) return { level: 'full', color: '#10b981', label: '🟢 Full Connectivity' };
    if (p2pRunning) return { level: 'p2p', color: '#34d399', label: '🟢 P2P Connected' };

    return { level: 'degraded', color: '#f59e0b', label: '🟡 Degraded' };
}

/**
 * Format relative time
 */
function timeAgo(dateStr: string | undefined): string {
    if (!dateStr) return 'Never';
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diff = Math.floor((now - then) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

export default function OfflineStatus({ user }: OfflineStatusProps) {
    const [syncStatus, setSyncStatus] = useState<Record<string, unknown> | null>(null);
    const [syncQueue, setSyncQueue] = useState<SyncQueueItem[]>([]);
    const [offlineStatus, setOfflineStatus] = useState<OfflineStatusData | null>(null);
    const [meshStatus, setMeshStatus] = useState<MeshStatusData | null>(null);
    const [offlineCaps, setOfflineCaps] = useState<OfflineCapsData | null>(null);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    const flash = useCallback((m: string) => {
        setMsg(m);
        setTimeout(() => setMsg(''), 3500);
    }, []);

    // Load all offline-related status
    const loadAll = useCallback(async () => {
        try {
            const [syncRes, queueRes, meshRes, capsRes] = await Promise.allSettled([
                offlineAPI.getSyncStatus(),
                offlineAPI.getQueue(),
                meshAPI.getStatus(),
                offlineAPI.getCapabilities(),
            ]);

            if (syncRes.status === 'fulfilled') setSyncStatus((syncRes.value.data || syncRes.value) as unknown as Record<string, unknown>);
            if (queueRes.status === 'fulfilled') {
                const data = (queueRes.value.data || queueRes.value) as unknown as Record<string, unknown>;
                setSyncQueue(Array.isArray(data) ? data as SyncQueueItem[] : (data.queue || data.items || []) as SyncQueueItem[]);
            }
            if (meshRes.status === 'fulfilled') setMeshStatus((meshRes.value.data || meshRes.value) as unknown as MeshStatusData);
            if (capsRes.status === 'fulfilled') setOfflineCaps((capsRes.value.data || capsRes.value) as unknown as OfflineCapsData);

            // Also try user-specific offline status
            if ((user as Record<string, unknown>)?.id) {
                try {
                    const userOffline = await offlineAPI.getUserOfflineStatus((user as Record<string, unknown>).id as string);
                    setOfflineStatus((userOffline.data || userOffline) as OfflineStatusData);
                } catch {
                    // User-specific offline status may not be available
                }
            }
        } catch {
            // Silently fail on initial load
        }
    }, [user]);

    useEffect(() => {
        loadAll();
        const interval = setInterval(loadAll, 10000);
        return () => clearInterval(interval);
    }, [loadAll]);

    // Flush sync queue
    const handleFlush = async () => {
        setLoading(true);
        try {
            await offlineAPI.flushQueue();
            flash('✅ Sync queue flushed successfully');
            await loadAll();
        } catch (e) {
            flash(`❌ Flush failed: ${(e as Error).message}`);
        } finally {
            setLoading(false);
        }
    };

    // Retry sync
    const handleRetrySync = async () => {
        setLoading(true);
        try {
            await offlineAPI.flushQueue();
            flash('🔄 Sync retry initiated');
            await loadAll();
        } catch (e) {
            flash(`❌ Sync retry failed: ${(e as Error).message}`);
        } finally {
            setLoading(false);
        }
    };

    const health = computeHealth(meshStatus);
    const queueCount = syncQueue.length;
    const lastSync = (syncStatus as Record<string, unknown>)?.last_sync as string | undefined
        || offlineStatus?.last_sync
        || meshStatus?.last_sync;

    return (
        <div style={{ color: '#fff', fontFamily: 'system-ui,sans-serif', maxWidth: 860 }}>
            {/* Header */}
            <div style={{ marginBottom: 20 }}>
                <h2 style={{ margin: 0, fontSize: 22 }}>📡 Offline-First Status</h2>
                <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: 13 }}>
                    Connectivity health · Sync queue · Last known state
                </p>
            </div>

            {/* Flash message */}
            {msg && (
                <div style={{
                    ...card,
                    background: 'rgba(102,126,234,0.2)',
                    border: '1px solid #667eea',
                    padding: '10px 16px',
                    fontSize: 13,
                }}>
                    {msg}
                </div>
            )}

            {/* Connectivity Health Card */}
            <div style={{
                ...card,
                border: `1px solid ${health.color}40`,
                background: `${health.color}08`,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>CONNECTIVITY HEALTH</div>
                        <div style={{ fontSize: 20, fontWeight: 700, color: health.color }}>{health.label}</div>
                    </div>
                    <div style={{
                        width: 48,
                        height: 48,
                        borderRadius: '50%',
                        border: `3px solid ${health.color}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 20,
                    }}>
                        {health.level === 'full' || health.level === 'p2p' ? '✓' : health.level === 'unknown' ? '?' : '!'}
                    </div>
                </div>

                {/* Status details */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 12, fontSize: 12 }}>
                    <div>
                        <span style={{ color: '#64748b' }}>Last Sync:</span>{' '}
                        <span style={{ color: lastSync ? '#fff' : '#64748b' }}>
                            {timeAgo(lastSync)}
                        </span>
                    </div>
                    <div>
                        <span style={{ color: '#64748b' }}>Queue:</span>{' '}
                        <span style={{ color: queueCount > 0 ? '#f59e0b' : '#10b981', fontWeight: 600 }}>
                            {queueCount} pending
                        </span>
                    </div>
                    <div>
                        <span style={{ color: '#64748b' }}>Mode:</span>{' '}
                        {offlineStatus?.sync_mode || (meshStatus?.air_gap?.label) || 'Normal'}
                    </div>
                </div>

                {/* Action Buttons */}
                <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                    <button
                        onClick={handleFlush}
                        disabled={loading || queueCount === 0}
                        style={{
                            ...btn('#3b82f6', true),
                            opacity: loading || queueCount === 0 ? 0.5 : 1,
                        }}
                    >
                        {loading ? '⏳' : '📤 Flush Queue'}
                    </button>
                    <button
                        onClick={handleRetrySync}
                        disabled={loading}
                        style={{
                            ...btn('#8b5cf6', true),
                            opacity: loading ? 0.5 : 1,
                        }}
                    >
                        {loading ? '⏳' : '🔄 Retry Sync'}
                    </button>
                </div>
            </div>

            {/* Sync Queue */}
            <div style={card}>
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 12,
                }}>
                    <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>
                        📋 SYNC QUEUE ({queueCount} items)
                    </div>
                    {queueCount > 0 && (
                        <span style={{ fontSize: 11, color: '#f59e0b' }}>
                            ⏳ Changes pending sync
                        </span>
                    )}
                </div>

                {syncQueue.length === 0 ? (
                    <div style={{
                        textAlign: 'center',
                        padding: 24,
                        color: '#64748b',
                        fontSize: 13,
                    }}>
                        ✅ Sync queue is empty — all changes synced
                    </div>
                ) : (
                    <div>
                        {syncQueue.slice(0, 10).map((item, idx) => (
                            <div key={item.id || idx} style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '8px 12px',
                                marginBottom: 4,
                                background: 'rgba(255,255,255,0.03)',
                                borderRadius: 8,
                                fontSize: 12,
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <span style={{
                                        width: 6, height: 6, borderRadius: '50%',
                                        background: item.status === 'synced' ? '#10b981'
                                            : item.status === 'failed' ? '#ef4444'
                                                : '#f59e0b',
                                        display: 'inline-block',
                                    }} />
                                    <span style={{ color: '#94a3b8', fontFamily: 'monospace', fontSize: 11 }}>
                                        {item.op_type || item.type || 'sync'}
                                    </span>
                                    <span>{item.entity_type || item.target || '—'}</span>
                                </div>
                                <div style={{ color: '#64748b', fontSize: 11 }}>
                                    {timeAgo(item.created_at || item.timestamp)}
                                </div>
                            </div>
                        ))}
                        {syncQueue.length > 10 && (
                            <div style={{ textAlign: 'center', padding: 8, fontSize: 11, color: '#64748b' }}>
                                +{syncQueue.length - 10} more items
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Offline Capabilities */}
            {offlineCaps && (
                <div style={card}>
                    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 600 }}>
                        ⚡ OFFLINE CAPABILITIES
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 12 }}>
                        {Object.entries(offlineCaps).map(([key, val]) => (
                            <div key={key} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                padding: '6px 10px',
                                background: 'rgba(255,255,255,0.03)',
                                borderRadius: 6,
                            }}>
                                <span style={{
                                    width: 8, height: 8, borderRadius: '50%',
                                    background: val === true || val === 'available' || val === 'yes'
                                        ? '#10b981'
                                        : val === false || val === 'unavailable' || val === 'no'
                                            ? '#ef4444'
                                            : '#f59e0b',
                                    display: 'inline-block',
                                    flexShrink: 0,
                                }} />
                                <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>
                                    {key.replace(/_/g, ' ')}:
                                </span>
                                <span style={{ marginLeft: 'auto', fontWeight: 600 }}>
                                    {String(val)}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Last Known State */}
            {offlineStatus && (
                <div style={card}>
                    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 600 }}>
                        💾 LAST KNOWN STATE
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                        <div>
                            <span style={{ color: '#64748b' }}>State:</span>{' '}
                            {offlineStatus.state || offlineStatus.status || 'Active'}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Pending Ops:</span>{' '}
                            {offlineStatus.pending_operations ?? offlineStatus.pending ?? 0}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Synced Entities:</span>{' '}
                            {offlineStatus.synced_entities ?? offlineStatus.entities ?? 0}
                        </div>
                        <div>
                            <span style={{ color: '#64748b' }}>Last Active:</span>{' '}
                            {timeAgo(offlineStatus.last_active || offlineStatus.last_seen)}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
