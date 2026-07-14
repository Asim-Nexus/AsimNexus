/**
 * PersonalUniverseDashboard — AsimNexus Personal Universe Manager UI
 * ==================================================================
 * 5-layer user lifecycle management (Personal, Family, Community,
 * Enterprise, Sovereign) with universe CRUD, layer activation,
 * lifecycle state transitions, and privacy scoring.
 *
 * Reference:
 *   - routes/universe.py — REST API endpoints
 *   - core/universe/personal_universe.py — Core implementation
 *   - core/universe/__init__.py — Package exports
 */
import React, { useState, useEffect, useCallback } from 'react';
import { universeAPI } from '../../api';

// ── Types ────────────────────────────────────────────────────

interface UniverseData {
    user_id: string;
    display_name: string;
    email: string;
    current_layer: string;
    state: string;
    created_at: string;
    last_active: string;
    privacy_score: number;
    layers: Record<string, LayerInfo>;
    connections: number;
    activities: number;
}

interface LayerInfo {
    name: string;
    active: boolean;
    activated_at?: string;
    description: string;
}

interface LifecycleSummary {
    user_id: string;
    current_layer: string;
    state: string;
    total_layers: number;
    active_layers: number;
    milestones: Milestone[];
}

interface Milestone {
    layer: string;
    achieved_at: string;
    description: string;
}

interface UniverseStats {
    total_universes: number;
    active_universes: number;
    archived_universes: number;
    average_privacy_score: number;
    layer_distribution: Record<string, number>;
}

interface ActivityRecord {
    activity_id: string;
    activity_type: string;
    timestamp: string;
    details: string;
}

interface ConnectionRecord {
    connection_id: string;
    target_user_id: string;
    connection_type: string;
    established_at: string;
    status: string;
}

// ── Layer Configuration ──────────────────────────────────────

const LAYERS: Record<string, { icon: string; color: string; description: string }> = {
    PERSONAL: { icon: '👤', color: '#22d3ee', description: 'Personal identity & data' },
    FAMILY: { icon: '👨‍👩‍👧‍👦', color: '#a78bfa', description: 'Family connections & sharing' },
    COMMUNITY: { icon: '🏘️', color: '#34d399', description: 'Community governance & mesh' },
    ENTERPRISE: { icon: '🏢', color: '#fbbf24', description: 'Business & professional' },
    SOVEREIGN: { icon: '👑', color: '#f472b6', description: 'Full digital sovereignty' },
};

const LAYER_ORDER = ['PERSONAL', 'FAMILY', 'COMMUNITY', 'ENTERPRISE', 'SOVEREIGN'];

// ── Styles ───────────────────────────────────────────────────

const s: Record<string, React.CSSProperties> = {
    container: {
        padding: 24,
        height: '100%',
        overflow: 'auto',
        color: '#e2e8f0',
        fontFamily: "'Segoe UI', system-ui, sans-serif",
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
    },
    title: {
        fontSize: 24,
        fontWeight: 700,
        margin: 0,
        background: 'linear-gradient(135deg, #22d3ee, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
    },
    card: {
        background: 'rgba(15, 23, 42, 0.6)',
        borderRadius: 12,
        padding: 20,
        marginBottom: 16,
        border: '1px solid rgba(255,255,255,0.06)',
    },
    cardTitle: {
        fontSize: 14,
        fontWeight: 600,
        color: '#94a3b8',
        textTransform: 'uppercase' as const,
        letterSpacing: '0.05em',
        marginBottom: 12,
    },
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 12,
    },
    statBox: {
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 10,
        padding: 16,
        textAlign: 'center' as const,
    },
    statValue: {
        fontSize: 28,
        fontWeight: 700,
        marginBottom: 4,
    },
    statLabel: {
        fontSize: 12,
        color: '#94a3b8',
    },
    layerCard: {
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 10,
        padding: 16,
        marginBottom: 8,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        cursor: 'pointer',
        transition: 'all 0.2s',
    },
    layerCardActive: {
        borderLeft: '4px solid #22d3ee',
    },
    layerCardInactive: {
        borderLeft: '4px solid rgba(255,255,255,0.1)',
        opacity: 0.6,
    },
    badge: {
        padding: '4px 10px',
        borderRadius: 12,
        fontSize: 11,
        fontWeight: 600,
    },
    input: {
        background: 'rgba(15, 23, 42, 0.8)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8,
        padding: '10px 14px',
        color: '#e2e8f0',
        fontSize: 14,
        width: '100%',
        boxSizing: 'border-box' as const,
        marginBottom: 12,
    },
    select: {
        background: 'rgba(15, 23, 42, 0.8)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8,
        padding: '10px 14px',
        color: '#e2e8f0',
        fontSize: 14,
        width: '100%',
        marginBottom: 12,
    },
    button: {
        background: 'linear-gradient(135deg, #22d3ee, #a78bfa)',
        border: 'none',
        borderRadius: 8,
        padding: '10px 20px',
        color: '#0f172a',
        fontWeight: 600,
        fontSize: 14,
        cursor: 'pointer',
        marginRight: 8,
        marginBottom: 8,
    },
    buttonSecondary: {
        background: 'rgba(255,255,255,0.08)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8,
        padding: '10px 20px',
        color: '#e2e8f0',
        fontWeight: 600,
        fontSize: 14,
        cursor: 'pointer',
        marginRight: 8,
        marginBottom: 8,
    },
    table: {
        width: '100%',
        borderCollapse: 'collapse' as const,
        fontSize: 13,
    },
    th: {
        textAlign: 'left' as const,
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        color: '#94a3b8',
        fontWeight: 600,
        fontSize: 11,
        textTransform: 'uppercase' as const,
        letterSpacing: '0.05em',
    },
    td: {
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
    },
    errorBox: {
        background: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: 8,
        padding: 12,
        color: '#fca5a5',
        marginBottom: 16,
        fontSize: 13,
    },
    successBox: {
        background: 'rgba(16, 185, 129, 0.1)',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        borderRadius: 8,
        padding: 12,
        color: '#6ee7b7',
        marginBottom: 16,
        fontSize: 13,
    },
    tabBar: {
        display: 'flex',
        gap: 4,
        marginBottom: 20,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        paddingBottom: 0,
    },
    tab: {
        padding: '10px 18px',
        borderRadius: '8px 8px 0 0',
        cursor: 'pointer',
        fontSize: 13,
        fontWeight: 600,
        border: 'none',
        background: 'transparent',
        color: '#94a3b8',
        transition: 'all 0.2s',
    },
    tabActive: {
        background: 'rgba(34, 211, 238, 0.1)',
        color: '#22d3ee',
        borderBottom: '2px solid #22d3ee',
    },
    formGroup: {
        marginBottom: 12,
    },
    label: {
        display: 'block',
        fontSize: 12,
        color: '#94a3b8',
        marginBottom: 4,
        fontWeight: 600,
    },
    textarea: {
        background: 'rgba(15, 23, 42, 0.8)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8,
        padding: '10px 14px',
        color: '#e2e8f0',
        fontSize: 14,
        width: '100%',
        boxSizing: 'border-box' as const,
        marginBottom: 12,
        minHeight: 80,
        fontFamily: 'monospace',
        resize: 'vertical' as const,
    },
};

// ── Component ────────────────────────────────────────────────

const PersonalUniverseDashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState<string>('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Data states
    const [universe, setUniverse] = useState<UniverseData | null>(null);
    const [lifecycle, setLifecycle] = useState<LifecycleSummary | null>(null);
    const [stats, setStats] = useState<UniverseStats | null>(null);
    const [activities, setActivities] = useState<ActivityRecord[]>([]);
    const [connections, setConnections] = useState<ConnectionRecord[]>([]);
    const [privacyScore, setPrivacyScore] = useState<number | null>(null);

    // Form states
    const [userId, setUserId] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [email, setEmail] = useState('');
    const [selectedLayer, setSelectedLayer] = useState('COMMUNITY');
    const [activityType, setActivityType] = useState('');
    const [activityDetails, setActivityDetails] = useState('');
    const [connectionTargetId, setConnectionTargetId] = useState('');
    const [connectionType, setConnectionType] = useState('FAMILY');

    // ── Data Fetching ──

    const fetchAll = useCallback(async (uid: string) => {
        setLoading(true);
        setError(null);
        try {
            const [statusRes, lifecycleRes, statsRes, privacyRes] = await Promise.all([
                universeAPI.getStatus(uid).catch(() => null),
                universeAPI.getLifecycle(uid).catch(() => null),
                universeAPI.getStats().catch(() => null),
                universeAPI.getPrivacyScore(uid).catch(() => null),
            ]);

            if (statusRes?.data?.data) setUniverse(statusRes.data.data as UniverseData);
            if (lifecycleRes?.data?.data) setLifecycle(lifecycleRes.data.data as LifecycleSummary);
            if (statsRes?.data?.data) setStats(statsRes.data.data as UniverseStats);
            if (privacyRes?.data?.data) setPrivacyScore((privacyRes.data.data as { privacy_score: number }).privacy_score);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to fetch universe data';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        // Try to load from stored user
        const storedUser = localStorage.getItem('asimnexus_user');
        if (storedUser) {
            try {
                const user = JSON.parse(storedUser);
                const uid = user.id || user.user_id || user.email || 'default';
                setUserId(uid);
                setDisplayName(user.display_name || user.name || '');
                setEmail(user.email || '');
                fetchAll(uid);
            } catch {
                fetchAll('default');
            }
        } else {
            fetchAll('default');
            setLoading(false);
        }
    }, [fetchAll]);

    // ── Actions ──

    const handleCreateUniverse = async () => {
        setError(null);
        setSuccess(null);
        if (!userId || !email || !displayName) {
            setError('User ID, Email, and Display Name are required');
            return;
        }
        try {
            const res = await universeAPI.create({ user_id: userId, email, display_name: displayName });
            if (res.data.data) setUniverse(res.data.data as UniverseData);
            setSuccess('Universe created successfully!');
            await fetchAll(userId);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to create universe';
            setError(msg);
        }
    };

    const handleActivateLayer = async () => {
        setError(null);
        setSuccess(null);
        if (!userId) {
            setError('User ID is required');
            return;
        }
        try {
            const res = await universeAPI.activateLayer({ user_id: userId, layer: selectedLayer });
            if (res.data.data) setUniverse(res.data.data as UniverseData);
            setSuccess(`Layer ${selectedLayer} activated!`);
            await fetchAll(userId);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to activate layer';
            setError(msg);
        }
    };

    const handleRecordActivity = async () => {
        setError(null);
        setSuccess(null);
        if (!userId || !activityType) {
            setError('User ID and Activity Type are required');
            return;
        }
        try {
            await universeAPI.recordActivity({ user_id: userId, activity_type: activityType, details: activityDetails || activityType });
            setSuccess('Activity recorded!');
            setActivityType('');
            setActivityDetails('');
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to record activity';
            setError(msg);
        }
    };

    const handleAddConnection = async () => {
        setError(null);
        setSuccess(null);
        if (!userId || !connectionTargetId) {
            setError('User ID and Target User ID are required');
            return;
        }
        try {
            await universeAPI.addConnection({ user_id: userId, target_user_id: connectionTargetId, connection_type: connectionType });
            setSuccess('Connection added!');
            setConnectionTargetId('');
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to add connection';
            setError(msg);
        }
    };

    const handleMigrate = async () => {
        setError(null);
        setSuccess(null);
        if (!userId) {
            setError('User ID is required');
            return;
        }
        try {
            const res = await universeAPI.migrate({ user_id: userId, target_node: 'auto' });
            if (res.data.data) setUniverse(res.data.data as UniverseData);
            setSuccess('Universe migrated!');
            await fetchAll(userId);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to migrate universe';
            setError(msg);
        }
    };

    const handleArchive = async () => {
        setError(null);
        setSuccess(null);
        if (!userId) {
            setError('User ID is required');
            return;
        }
        try {
            await universeAPI.archive({ user_id: userId });
            setSuccess('Universe archived!');
            await fetchAll(userId);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to archive universe';
            setError(msg);
        }
    };

    const handleReactivate = async () => {
        setError(null);
        setSuccess(null);
        if (!userId) {
            setError('User ID is required');
            return;
        }
        try {
            await universeAPI.reactivate({ user_id: userId });
            setSuccess('Universe reactivated!');
            await fetchAll(userId);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to reactivate universe';
            setError(msg);
        }
    };

    // ── Tab Definitions ──

    const tabs = [
        { id: 'overview', label: '📊 Overview', desc: 'Universe status & stats' },
        { id: 'layers', label: '🔮 Layers', desc: '5-layer lifecycle management' },
        { id: 'activity', label: '📝 Activity', desc: 'Record & view activities' },
        { id: 'connections', label: '🔗 Connections', desc: 'Manage connections' },
        { id: 'settings', label: '⚙️ Settings', desc: 'Universe configuration' },
    ];

    // ── Render: Overview ──

    const renderOverview = () => (
        <>
            {/* Stats Grid */}
            <div style={s.grid}>
                <div style={s.statBox}>
                    <div style={{ ...s.statValue, color: '#22d3ee' }}>
                        {stats?.total_universes ?? universe ? 1 : 0}
                    </div>
                    <div style={s.statLabel}>Total Universes</div>
                </div>
                <div style={s.statBox}>
                    <div style={{ ...s.statValue, color: '#34d399' }}>
                        {stats?.active_universes ?? (universe?.state === 'active' ? 1 : 0)}
                    </div>
                    <div style={s.statLabel}>Active</div>
                </div>
                <div style={s.statBox}>
                    <div style={{ ...s.statValue, color: '#fbbf24' }}>
                        {universe?.layers ? Object.values(universe.layers).filter((l: LayerInfo) => l.active).length : 0}
                    </div>
                    <div style={s.statLabel}>Active Layers</div>
                </div>
                <div style={s.statBox}>
                    <div style={{ ...s.statValue, color: '#a78bfa' }}>
                        {privacyScore !== null ? `${privacyScore}%` : '—'}
                    </div>
                    <div style={s.statLabel}>Privacy Score</div>
                </div>
            </div>

            {/* Universe Details */}
            {universe && (
                <div style={s.card}>
                    <div style={s.cardTitle}>🌌 Universe Details</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                        <div><span style={{ color: '#94a3b8' }}>User:</span> {universe.user_id}</div>
                        <div><span style={{ color: '#94a3b8' }}>Name:</span> {universe.display_name}</div>
                        <div><span style={{ color: '#94a3b8' }}>State:</span> {universe.state}</div>
                        <div><span style={{ color: '#94a3b8' }}>Layer:</span> {universe.current_layer}</div>
                        <div><span style={{ color: '#94a3b8' }}>Created:</span> {new Date(universe.created_at).toLocaleDateString()}</div>
                        <div><span style={{ color: '#94a3b8' }}>Last Active:</span> {new Date(universe.last_active).toLocaleDateString()}</div>
                        <div><span style={{ color: '#94a3b8' }}>Connections:</span> {universe.connections}</div>
                        <div><span style={{ color: '#94a3b8' }}>Activities:</span> {universe.activities}</div>
                    </div>
                </div>
            )}

            {/* Lifecycle Milestones */}
            {lifecycle && lifecycle.milestones.length > 0 && (
                <div style={s.card}>
                    <div style={s.cardTitle}>🏆 Milestones</div>
                    {lifecycle.milestones.map((m, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 13 }}>
                            <span>{LAYERS[m.layer]?.icon} {m.description}</span>
                            <span style={{ color: '#94a3b8' }}>{new Date(m.achieved_at).toLocaleDateString()}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Layer Distribution */}
            {stats?.layer_distribution && (
                <div style={s.card}>
                    <div style={s.cardTitle}>📊 Layer Distribution</div>
                    <div style={s.grid}>
                        {Object.entries(stats.layer_distribution).map(([layer, count]) => (
                            <div key={layer} style={s.statBox}>
                                <div style={{ ...s.statValue, color: LAYERS[layer]?.color || '#94a3b8', fontSize: 20 }}>
                                    {LAYERS[layer]?.icon} {count}
                                </div>
                                <div style={s.statLabel}>{layer}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!universe && !loading && (
                <div style={s.card}>
                    <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>🌌</div>
                        <h3 style={{ color: '#e2e8f0', margin: '0 0 8px 0' }}>No Universe Found</h3>
                        <p style={{ margin: 0, fontSize: 13 }}>
                            Create a new personal universe to get started.
                        </p>
                    </div>
                </div>
            )}
        </>
    );

    // ── Render: Layers ──

    const renderLayers = () => (
        <>
            <div style={s.card}>
                <div style={s.cardTitle}>🔮 Lifecycle Layers</div>
                <p style={{ fontSize: 13, color: '#94a3b8', margin: '0 0 16px 0' }}>
                    Activate layers progressively as your digital presence grows.
                    Each layer unlocks new capabilities and responsibilities.
                </p>

                {LAYER_ORDER.map((layerKey) => {
                    const layer = LAYERS[layerKey];
                    const isActive = universe?.layers?.[layerKey]?.active ?? false;
                    const layerInfo = universe?.layers?.[layerKey];

                    return (
                        <div
                            key={layerKey}
                            style={{
                                ...s.layerCard,
                                ...(isActive ? s.layerCardActive : s.layerCardInactive),
                            }}
                        >
                            <div>
                                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                                    {layer.icon} {layerKey}
                                </div>
                                <div style={{ fontSize: 12, color: '#94a3b8' }}>
                                    {layer.description}
                                    {layerInfo?.activated_at && ` · Activated ${new Date(layerInfo.activated_at).toLocaleDateString()}`}
                                </div>
                            </div>
                            <span style={{
                                ...s.badge,
                                background: isActive ? 'rgba(34, 211, 238, 0.15)' : 'rgba(148, 163, 184, 0.1)',
                                color: isActive ? '#22d3ee' : '#94a3b8',
                            }}>
                                {isActive ? '● Active' : '○ Inactive'}
                            </span>
                        </div>
                    );
                })}
            </div>

            <div style={s.card}>
                <div style={s.cardTitle}>⚡ Activate Layer</div>
                <div style={s.formGroup}>
                    <label style={s.label}>Layer</label>
                    <select
                        style={s.select}
                        value={selectedLayer}
                        onChange={(e) => setSelectedLayer(e.target.value)}
                    >
                        {LAYER_ORDER.map((lk) => (
                            <option key={lk} value={lk}>{LAYERS[lk].icon} {lk}</option>
                        ))}
                    </select>
                </div>
                <button style={s.button} onClick={handleActivateLayer}>
                    Activate Layer
                </button>
            </div>
        </>
    );

    // ── Render: Activity ──

    const renderActivity = () => (
        <>
            <div style={s.card}>
                <div style={s.cardTitle}>📝 Record Activity</div>
                <div style={s.formGroup}>
                    <label style={s.label}>Activity Type</label>
                    <input
                        style={s.input}
                        placeholder="e.g., login, transaction, milestone"
                        value={activityType}
                        onChange={(e) => setActivityType(e.target.value)}
                    />
                </div>
                <div style={s.formGroup}>
                    <label style={s.label}>Details (optional)</label>
                    <textarea
                        style={s.textarea}
                        placeholder="Additional details about this activity"
                        value={activityDetails}
                        onChange={(e) => setActivityDetails(e.target.value)}
                    />
                </div>
                <button style={s.button} onClick={handleRecordActivity}>
                    Record Activity
                </button>
            </div>

            {activities.length > 0 && (
                <div style={s.card}>
                    <div style={s.cardTitle}>📋 Recent Activities</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Type</th>
                                    <th style={s.th}>Details</th>
                                    <th style={s.th}>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                                {activities.map((a) => (
                                    <tr key={a.activity_id}>
                                        <td style={s.td}>{a.activity_type}</td>
                                        <td style={s.td}>{a.details}</td>
                                        <td style={s.td}>{new Date(a.timestamp).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </>
    );

    // ── Render: Connections ──

    const renderConnections = () => (
        <>
            <div style={s.card}>
                <div style={s.cardTitle}>🔗 Add Connection</div>
                <div style={s.formGroup}>
                    <label style={s.label}>Target User ID</label>
                    <input
                        style={s.input}
                        placeholder="Target user's ID"
                        value={connectionTargetId}
                        onChange={(e) => setConnectionTargetId(e.target.value)}
                    />
                </div>
                <div style={s.formGroup}>
                    <label style={s.label}>Connection Type</label>
                    <select
                        style={s.select}
                        value={connectionType}
                        onChange={(e) => setConnectionType(e.target.value)}
                    >
                        <option value="FAMILY">👨‍👩‍👧‍👦 Family</option>
                        <option value="FRIEND">🤝 Friend</option>
                        <option value="COLLEAGUE">💼 Colleague</option>
                        <option value="COMMUNITY">🏘️ Community</option>
                        <option value="TRUSTED">⭐ Trusted</option>
                    </select>
                </div>
                <button style={s.button} onClick={handleAddConnection}>
                    Add Connection
                </button>
            </div>

            {connections.length > 0 && (
                <div style={s.card}>
                    <div style={s.cardTitle}>🔗 Active Connections</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Target</th>
                                    <th style={s.th}>Type</th>
                                    <th style={s.th}>Status</th>
                                    <th style={s.th}>Since</th>
                                </tr>
                            </thead>
                            <tbody>
                                {connections.map((c) => (
                                    <tr key={c.connection_id}>
                                        <td style={s.td}>{c.target_user_id}</td>
                                        <td style={s.td}>{c.connection_type}</td>
                                        <td style={s.td}>{c.status}</td>
                                        <td style={s.td}>{new Date(c.established_at).toLocaleDateString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </>
    );

    // ── Render: Settings ──

    const renderSettings = () => (
        <>
            <div style={s.card}>
                <div style={s.cardTitle}>⚙️ Universe Configuration</div>
                <div style={s.formGroup}>
                    <label style={s.label}>User ID</label>
                    <input
                        style={s.input}
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        placeholder="Your unique user ID"
                    />
                </div>
                <div style={s.formGroup}>
                    <label style={s.label}>Display Name</label>
                    <input
                        style={s.input}
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        placeholder="Your display name"
                    />
                </div>
                <div style={s.formGroup}>
                    <label style={s.label}>Email</label>
                    <input
                        style={s.input}
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="your@email.com"
                    />
                </div>
                <button style={s.button} onClick={handleCreateUniverse}>
                    🌌 Create Universe
                </button>
            </div>

            <div style={s.card}>
                <div style={s.cardTitle}>🔄 Lifecycle Actions</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    <button style={s.buttonSecondary} onClick={handleMigrate}>
                        🚀 Migrate Universe
                    </button>
                    <button style={s.buttonSecondary} onClick={handleArchive}>
                        📦 Archive Universe
                    </button>
                    <button style={s.buttonSecondary} onClick={handleReactivate}>
                        🔄 Reactivate Universe
                    </button>
                </div>
                <p style={{ fontSize: 12, color: '#94a3b8', marginTop: 12 }}>
                    Migration moves your universe to an optimal node. Archiving preserves data while freeing resources.
                </p>
            </div>

            {/* Privacy Score Detail */}
            {privacyScore !== null && (
                <div style={s.card}>
                    <div style={s.cardTitle}>🛡️ Privacy Score</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <div style={{
                            width: 80,
                            height: 80,
                            borderRadius: '50%',
                            background: `conic-gradient(${privacyScore > 70 ? '#22d3ee' : privacyScore > 40 ? '#fbbf24' : '#ef4444'} ${privacyScore}%, rgba(255,255,255,0.05) ${privacyScore}%)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 20,
                            fontWeight: 700,
                        }}>
                            {privacyScore}%
                        </div>
                        <div style={{ fontSize: 13, color: '#94a3b8' }}>
                            Your universe privacy score measures how well your data is protected
                            across all active layers. Higher scores indicate stronger privacy controls.
                        </div>
                    </div>
                </div>
            )}
        </>
    );

    // ── Main Render ──

    return (
        <div style={s.container}>
            <div style={s.header}>
                <h2 style={s.title}>🌌 Personal Universe</h2>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {universe && (
                        <span style={{
                            ...s.badge,
                            background: universe.state === 'active' ? 'rgba(16,185,129,0.15)' : 'rgba(148,163,184,0.1)',
                            color: universe.state === 'active' ? '#10b981' : '#94a3b8',
                        }}>
                            ● {universe.state}
                        </span>
                    )}
                    <button
                        style={{ ...s.buttonSecondary, margin: 0, fontSize: 12, padding: '6px 12px' }}
                        onClick={() => userId && fetchAll(userId)}
                    >
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {/* Messages */}
            {error && <div style={s.errorBox}>❌ {error}</div>}
            {success && <div style={s.successBox}>✅ {success}</div>}

            {/* Tab Bar */}
            <div style={s.tabBar}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        style={{
                            ...s.tab,
                            ...(activeTab === tab.id ? s.tabActive : {}),
                        }}
                        onClick={() => setActiveTab(tab.id)}
                        title={tab.desc}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🌌</div>
                    Loading universe data...
                </div>
            ) : (
                <>
                    {activeTab === 'overview' && renderOverview()}
                    {activeTab === 'layers' && renderLayers()}
                    {activeTab === 'activity' && renderActivity()}
                    {activeTab === 'connections' && renderConnections()}
                    {activeTab === 'settings' && renderSettings()}
                </>
            )}
        </div>
    );
};

export default PersonalUniverseDashboard;
