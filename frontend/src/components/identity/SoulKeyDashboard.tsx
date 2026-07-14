/**
 * SoulKeyDashboard — AsimNexus Soul Key Security Protocol UI
 * ============================================================
 * Cryptographic identity protection with Merkle Tree life events,
 * hardware attestation, and automated lockout mechanism.
 *
 * Reference:
 *   - routes/soul_key.py — REST API endpoints
 *   - core/security/soul_key.py — Core protocol implementation
 *   - docs/DIGITAL_NEPAL_ACT.md — Digital Nepal Act whitepaper
 */

import React, { useState, useEffect, useCallback } from 'react';
import { soulKeyAPI } from '../../api';

// ── Types ────────────────────────────────────────────────────

interface SoulKeyData {
    citizen_id: string;
    merkle_root: string;
    life_events_count: number;
    created_at: string;
    last_verified: string | null;
    device_fingerprint: string;
    revoked: boolean;
}

interface LifeEvent {
    event_id: string;
    event_type: string;
    timestamp: string;
    data_hash: string;
    metadata: Record<string, unknown>;
}

interface LockoutRecord {
    record_id: string;
    state: string;
    detected_at: string;
    reason: string;
    ncsc_incident_id: string | null;
}

interface SoulKeyStats {
    total_soul_keys: number;
    total_events: number;
    total_lockouts: number;
    active_keys: number;
    revoked_keys: number;
}

interface AttestationResult {
    citizen_id: string;
    result: string;
    message: string;
}

interface VerifyResult {
    citizen_id: string;
    is_valid: boolean;
    merkle_root: string | null;
    verified_at: string | null;
}

// ── Styling ──────────────────────────────────────────────────

const s = {
    container: {
        flex: 1,
        overflow: 'auto',
        padding: '20px 24px',
        color: '#e0e0e0',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    } as React.CSSProperties,
    header: {
        fontSize: '1.4rem',
        fontWeight: 700,
        marginBottom: 20,
        background: 'linear-gradient(135deg, #f472b6, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
    } as React.CSSProperties,
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 16,
        marginBottom: 24,
    } as React.CSSProperties,
    card: {
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 12,
        padding: '16px 20px',
        border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(8px)',
    } as React.CSSProperties,
    cardTitle: {
        fontSize: '0.75rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        opacity: 0.5,
        marginBottom: 8,
    } as React.CSSProperties,
    statValue: {
        fontSize: '1.8rem',
        fontWeight: 700,
        color: '#f472b6',
    } as React.CSSProperties,
    statLabel: {
        fontSize: '0.78rem',
        opacity: 0.6,
        marginTop: 2,
    } as React.CSSProperties,
    section: {
        marginBottom: 24,
    } as React.CSSProperties,
    sectionTitle: {
        fontSize: '1rem',
        fontWeight: 600,
        marginBottom: 12,
        opacity: 0.8,
    } as React.CSSProperties,
    table: {
        width: '100%',
        borderCollapse: 'collapse' as const,
        fontSize: '0.82rem',
    } as React.CSSProperties,
    th: {
        textAlign: 'left' as const,
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        fontWeight: 600,
        opacity: 0.5,
        fontSize: '0.72rem',
        textTransform: 'uppercase' as const,
        letterSpacing: '0.05em',
    } as React.CSSProperties,
    td: {
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
    } as React.CSSProperties,
    badge: (color: string) => ({
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 10,
        fontSize: '0.7rem',
        fontWeight: 600,
        background: `${color}22`,
        color: color,
        border: `1px solid ${color}44`,
    } as React.CSSProperties),
    btn: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(244,114,182,0.3)',
        background: 'rgba(244,114,182,0.1)',
        color: '#f472b6',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    btnDanger: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(239,68,68,0.3)',
        background: 'rgba(239,68,68,0.1)',
        color: '#ef4444',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    btnSuccess: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(52,211,153,0.3)',
        background: 'rgba(52,211,153,0.1)',
        color: '#34d399',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    input: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        width: '100%',
        outline: 'none',
        boxSizing: 'border-box' as const,
    } as React.CSSProperties,
    errorBox: {
        padding: 12,
        borderRadius: 8,
        background: 'rgba(239,68,68,0.1)',
        border: '1px solid rgba(239,68,68,0.2)',
        color: '#ef4444',
        fontSize: '0.82rem',
        marginBottom: 16,
    } as React.CSSProperties,
    successBox: {
        padding: 12,
        borderRadius: 8,
        background: 'rgba(52,211,153,0.1)',
        border: '1px solid rgba(52,211,153,0.2)',
        color: '#34d399',
        fontSize: '0.82rem',
        marginBottom: 16,
    } as React.CSSProperties,
    loadingText: {
        opacity: 0.4,
        fontSize: '0.85rem',
        fontStyle: 'italic',
    } as React.CSSProperties,
    formRow: {
        display: 'flex',
        gap: 12,
        marginBottom: 12,
        alignItems: 'flex-end',
        flexWrap: 'wrap' as const,
    } as React.CSSProperties,
    formGroup: {
        flex: 1,
        minWidth: 200,
    } as React.CSSProperties,
    label: {
        fontSize: '0.75rem',
        fontWeight: 600,
        opacity: 0.5,
        marginBottom: 4,
        display: 'block',
    } as React.CSSProperties,
    select: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        width: '100%',
        outline: 'none',
        boxSizing: 'border-box' as const,
    } as React.CSSProperties,
};

// ── Event Type Options ───────────────────────────────────────

const EVENT_TYPES = [
    'birth', 'citizenship', 'nid', 'education', 'land',
    'health', 'tax', 'marriage', 'passport', 'license',
    'voter', 'pension',
];

// ── Color Maps ───────────────────────────────────────────────

const eventTypeColor: Record<string, string> = {
    birth: '#34d399',
    citizenship: '#60a5fa',
    nid: '#a78bfa',
    education: '#f472b6',
    land: '#fbbf24',
    health: '#ef4444',
    tax: '#f97316',
    marriage: '#22d3ee',
    passport: '#94a3b8',
    license: '#eab308',
    voter: '#34d399',
    pension: '#60a5fa',
};

const lockoutStateColor: Record<string, string> = {
    LOCKED: '#ef4444',
    REVOKED: '#f97316',
    SELF_DESTRUCT: '#dc2626',
    INCIDENT_REPORTED: '#eab308',
    RESOLVED: '#34d399',
};

// ── Component ────────────────────────────────────────────────

const SoulKeyDashboard: React.FC = () => {
    // ── State ──────────────────────────────────────────────
    const [stats, setStats] = useState<SoulKeyStats | null>(null);
    const [searchId, setSearchId] = useState('');
    const [soulKey, setSoulKey] = useState<SoulKeyData | null>(null);
    const [events, setEvents] = useState<LifeEvent[]>([]);
    const [lockoutHistory, setLockoutHistory] = useState<LockoutRecord[]>([]);
    const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
    const [attestResult, setAttestResult] = useState<AttestationResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'search' | 'create' | 'events' | 'lockout'>('overview');

    // ── Create Form State ──────────────────────────────────
    const [createId, setCreateId] = useState('');
    const [createFingerprint, setCreateFingerprint] = useState('');

    // ── Event Form State ───────────────────────────────────
    const [eventType, setEventType] = useState('birth');
    const [eventData, setEventData] = useState('');
    const [eventMetadata, setEventMetadata] = useState('{}');

    // ── Attest Form State ──────────────────────────────────
    const [attestFingerprint, setAttestFingerprint] = useState('');

    // ── Lockout Form State ─────────────────────────────────
    const [lockoutSessionId, setLockoutSessionId] = useState('');
    const [lockoutFingerprint, setLockoutFingerprint] = useState('');
    const [lockoutReason, setLockoutReason] = useState('');

    // ── Data Fetching ──────────────────────────────────────

    const fetchStats = useCallback(async () => {
        try {
            const res = await soulKeyAPI.getStats();
            setStats((res.data.data as SoulKeyStats) || null);
        } catch {
            // Stats fetch is non-critical
        }
    }, []);

    const fetchSoulKey = useCallback(async (citizenId: string) => {
        try {
            const [keyRes, eventsRes, lockoutRes] = await Promise.all([
                soulKeyAPI.getSoulKey(citizenId),
                soulKeyAPI.listEvents(citizenId),
                soulKeyAPI.getLockoutHistory(citizenId),
            ]);
            setSoulKey((keyRes.data.data as SoulKeyData) || null);
            setEvents((eventsRes.data.data as { events: LifeEvent[] })?.events || []);
            setLockoutHistory((lockoutRes.data.data as { records: LockoutRecord[] })?.records || []);
            setVerifyResult(null);
            setAttestResult(null);
            setError(null);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to fetch Soul Key';
            setError(msg);
            setSoulKey(null);
            setEvents([]);
            setLockoutHistory([]);
        }
    }, []);

    useEffect(() => {
        fetchStats();
        setLoading(false);
    }, [fetchStats]);

    // ── Actions ────────────────────────────────────────────

    const handleCreate = async () => {
        if (!createId || !createFingerprint) {
            setError('citizen_id and device_fingerprint are required');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            const res = await soulKeyAPI.create({ citizen_id: createId, device_fingerprint: createFingerprint });
            const data = res.data.data as SoulKeyData;
            setSuccess(`Soul Key created for ${data.citizen_id}`);
            setCreateId('');
            setCreateFingerprint('');
            await fetchStats();
            await fetchSoulKey(data.citizen_id);
            setActiveTab('search');
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Creation failed';
            setError(msg);
        }
    };

    const handleAddEvent = async () => {
        if (!soulKey) {
            setError('Search for a Soul Key first');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            const res = await soulKeyAPI.addEvent(soulKey.citizen_id, {
                event_type: eventType,
                raw_data: eventData,
                metadata: JSON.parse(eventMetadata || '{}'),
            });
            const data = res.data.data as { event_id: string; new_merkle_root: string };
            setSuccess(`Event ${data.event_id} added. New Merkle Root: ${data.new_merkle_root}`);
            setEventData('');
            setEventMetadata('{}');
            await fetchSoulKey(soulKey.citizen_id);
            await fetchStats();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to add event';
            setError(msg);
        }
    };

    const handleVerify = async () => {
        if (!soulKey) {
            setError('Search for a Soul Key first');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            const res = await soulKeyAPI.verify(soulKey.citizen_id);
            const data = res.data.data as VerifyResult;
            setVerifyResult(data);
            if (data.is_valid) {
                setSuccess('Soul Key integrity verified successfully!');
            } else {
                setError('Soul Key integrity check FAILED — possible tampering detected!');
            }
            await fetchSoulKey(soulKey.citizen_id);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Verification failed';
            setError(msg);
        }
    };

    const handleAttest = async () => {
        if (!soulKey) {
            setError('Search for a Soul Key first');
            return;
        }
        if (!attestFingerprint) {
            setError('device_fingerprint is required');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            const res = await soulKeyAPI.attest(soulKey.citizen_id, { device_fingerprint: attestFingerprint });
            const data = res.data.data as AttestationResult;
            setAttestResult(data);
            if (data.result === 'trusted') {
                setSuccess(data.message);
            } else {
                setError(data.message);
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Attestation failed';
            setError(msg);
        }
    };

    const handleTriggerLockout = async () => {
        if (!soulKey) {
            setError('Search for a Soul Key first');
            return;
        }
        if (!lockoutSessionId || !lockoutFingerprint || !lockoutReason) {
            setError('session_id, device_fingerprint_attempted, and reason are required');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            const res = await soulKeyAPI.triggerLockout(soulKey.citizen_id, {
                session_id: lockoutSessionId,
                device_fingerprint_attempted: lockoutFingerprint,
                reason: lockoutReason,
            });
            const data = res.data.data as LockoutRecord & { message: string };
            setSuccess(data.message);
            setLockoutSessionId('');
            setLockoutFingerprint('');
            setLockoutReason('');
            await fetchSoulKey(soulKey.citizen_id);
            await fetchStats();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Lockout failed';
            setError(msg);
        }
    };

    const handleResolveLockout = async (recordId: string) => {
        setError(null);
        setSuccess(null);
        try {
            const res = await soulKeyAPI.resolveLockout(recordId);
            const data = res.data.data as { resolved: boolean };
            if (data.resolved) {
                setSuccess(`Lockout record ${recordId} resolved`);
            } else {
                setError(`Failed to resolve lockout record ${recordId}`);
            }
            if (soulKey) await fetchSoulKey(soulKey.citizen_id);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Resolve failed';
            setError(msg);
        }
    };

    const handleSearch = () => {
        if (!searchId) {
            setError('Enter a citizen_id to search');
            return;
        }
        setError(null);
        setSuccess(null);
        fetchSoulKey(searchId);
    };

    // ── Render Helpers ─────────────────────────────────────

    const renderStatCard = (title: string, value: string | number, label: string, color = '#f472b6') => (
        <div style={s.card}>
            <div style={s.cardTitle}>{title}</div>
            <div style={{ ...s.statValue, color }}>{value}</div>
            <div style={s.statLabel}>{label}</div>
        </div>
    );

    // ── Overview Tab ───────────────────────────────────────

    const renderOverview = () => (
        <>
            <div style={s.grid}>
                {renderStatCard('Total Soul Keys', stats?.total_soul_keys ?? '—', 'Registered identities', '#f472b6')}
                {renderStatCard('Active Keys', stats?.active_keys ?? '—', 'Non-revoked', '#34d399')}
                {renderStatCard('Revoked Keys', stats?.revoked_keys ?? '—', 'Revoked/compromised', '#ef4444')}
                {renderStatCard('Life Events', stats?.total_events ?? '—', 'Across all keys', '#60a5fa')}
                {renderStatCard('Lockouts', stats?.total_lockouts ?? '—', 'Total lockout records', '#f97316')}
            </div>

            <div style={s.section}>
                <div style={s.sectionTitle}>Quick Actions</div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <button style={s.btn} onClick={() => setActiveTab('create')}>
                        ✨ Create Soul Key
                    </button>
                    <button style={s.btn} onClick={() => setActiveTab('search')}>
                        🔍 Search Soul Key
                    </button>
                </div>
            </div>

            <div style={s.card}>
                <div style={s.cardTitle}>About Soul Key Protocol</div>
                <div style={{ fontSize: '0.82rem', opacity: 0.7, lineHeight: 1.6 }}>
                    The Soul Key Protocol provides cryptographic identity protection using a Merkle Tree
                    of life events. Each event is hashed and stored in an append-only structure, ensuring
                    tamper-evident identity history. Hardware attestation verifies trusted devices, and
                    the automated lockout mechanism protects against unauthorized access with
                    session revocation, data self-encryption, and NCSC incident reporting.
                </div>
            </div>
        </>
    );

    // ── Search Tab ─────────────────────────────────────────

    const renderSearch = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Search Soul Key</div>

            <div style={s.formRow}>
                <div style={s.formGroup}>
                    <label style={s.label}>Citizen ID</label>
                    <input
                        style={s.input}
                        placeholder="e.g., NID-12345-ABCDE"
                        value={searchId}
                        onChange={(e) => setSearchId(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                </div>
                <button style={s.btn} onClick={handleSearch}>
                    🔍 Search
                </button>
            </div>

            {soulKey && (
                <>
                    <div style={{ ...s.card, marginTop: 16 }}>
                        <div style={s.cardTitle}>Soul Key Details</div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                            <div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Citizen ID</div>
                                <div style={{ fontSize: '0.9rem', fontWeight: 600, fontFamily: 'monospace' }}>
                                    {soulKey.citizen_id}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Status</div>
                                <div>
                                    <span style={s.badge(soulKey.revoked ? '#ef4444' : '#34d399')}>
                                        {soulKey.revoked ? 'REVOKED' : 'ACTIVE'}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Merkle Root</div>
                                <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', opacity: 0.7, wordBreak: 'break-all' }}>
                                    {soulKey.merkle_root || '—'}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Life Events</div>
                                <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{soulKey.life_events_count}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Created</div>
                                <div style={{ fontSize: '0.82rem', opacity: 0.7 }}>
                                    {soulKey.created_at ? new Date(soulKey.created_at).toLocaleString() : '—'}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Last Verified</div>
                                <div style={{ fontSize: '0.82rem', opacity: 0.7 }}>
                                    {soulKey.last_verified ? new Date(soulKey.last_verified).toLocaleString() : 'Never'}
                                </div>
                            </div>
                            <div style={{ gridColumn: '1 / -1' }}>
                                <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>Device Fingerprint</div>
                                <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', opacity: 0.7, wordBreak: 'break-all' }}>
                                    {soulKey.device_fingerprint}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
                        <button style={s.btnSuccess} onClick={handleVerify}>
                            ✓ Verify Integrity
                        </button>
                        <button style={s.btn} onClick={() => setActiveTab('events')}>
                            📋 Manage Events
                        </button>
                        <button style={s.btnDanger} onClick={() => setActiveTab('lockout')}>
                            🔒 Lockout Actions
                        </button>
                    </div>

                    {verifyResult && (
                        <div style={verifyResult.is_valid ? s.successBox : s.errorBox}>
                            <strong>Verification: </strong>
                            {verifyResult.is_valid ? 'PASSED' : 'FAILED'}
                            {verifyResult.verified_at && (
                                <span style={{ opacity: 0.6, marginLeft: 8 }}>
                                    at {new Date(verifyResult.verified_at).toLocaleTimeString()}
                                </span>
                            )}
                        </div>
                    )}

                    {attestResult && (
                        <div style={attestResult.result === 'trusted' ? s.successBox : s.errorBox}>
                            <strong>Attestation: </strong>
                            {attestResult.result} — {attestResult.message}
                        </div>
                    )}

                    {events.length > 0 && (
                        <div style={{ marginTop: 16 }}>
                            <div style={s.sectionTitle}>Life Events ({events.length})</div>
                            <div style={{ overflowX: 'auto' }}>
                                <table style={s.table}>
                                    <thead>
                                        <tr>
                                            <th style={s.th}>Event ID</th>
                                            <th style={s.th}>Type</th>
                                            <th style={s.th}>Timestamp</th>
                                            <th style={s.th}>Data Hash</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {events.map((evt) => (
                                            <tr key={evt.event_id}>
                                                <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5 }}>
                                                    {evt.event_id}
                                                </td>
                                                <td style={s.td}>
                                                    <span style={s.badge(eventTypeColor[evt.event_type] || '#94a3b8')}>
                                                        {evt.event_type}
                                                    </span>
                                                </td>
                                                <td style={{ ...s.td, opacity: 0.6, fontSize: '0.78rem' }}>
                                                    {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : '—'}
                                                </td>
                                                <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5, wordBreak: 'break-all', maxWidth: 200 }}>
                                                    {evt.data_hash}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {lockoutHistory.length > 0 && (
                        <div style={{ marginTop: 16 }}>
                            <div style={s.sectionTitle}>Lockout History ({lockoutHistory.length})</div>
                            <div style={{ overflowX: 'auto' }}>
                                <table style={s.table}>
                                    <thead>
                                        <tr>
                                            <th style={s.th}>Record ID</th>
                                            <th style={s.th}>State</th>
                                            <th style={s.th}>Detected</th>
                                            <th style={s.th}>Reason</th>
                                            <th style={s.th}>NCSC ID</th>
                                            <th style={s.th}>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {lockoutHistory.map((rec) => (
                                            <tr key={rec.record_id}>
                                                <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5 }}>
                                                    {rec.record_id}
                                                </td>
                                                <td style={s.td}>
                                                    <span style={s.badge(lockoutStateColor[rec.state] || '#94a3b8')}>
                                                        {rec.state}
                                                    </span>
                                                </td>
                                                <td style={{ ...s.td, opacity: 0.6, fontSize: '0.78rem' }}>
                                                    {rec.detected_at ? new Date(rec.detected_at).toLocaleString() : '—'}
                                                </td>
                                                <td style={{ ...s.td, opacity: 0.7, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                    {rec.reason}
                                                </td>
                                                <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5 }}>
                                                    {rec.ncsc_incident_id || '—'}
                                                </td>
                                                <td style={s.td}>
                                                    {rec.state !== 'RESOLVED' && (
                                                        <button
                                                            style={s.btnSuccess}
                                                            onClick={() => handleResolveLockout(rec.record_id)}
                                                        >
                                                            Resolve
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </>
            )}

            {!soulKey && !loading && (
                <div style={s.loadingText}>Enter a Citizen ID and click Search to view Soul Key details.</div>
            )}
        </div>
    );

    // ── Create Tab ─────────────────────────────────────────

    const renderCreate = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Create New Soul Key</div>
            <div style={s.card}>
                <div style={s.formRow}>
                    <div style={s.formGroup}>
                        <label style={s.label}>Citizen ID</label>
                        <input
                            style={s.input}
                            placeholder="e.g., NID-12345-ABCDE"
                            value={createId}
                            onChange={(e) => setCreateId(e.target.value)}
                        />
                    </div>
                    <div style={s.formGroup}>
                        <label style={s.label}>Device Fingerprint</label>
                        <input
                            style={s.input}
                            placeholder="TPM or hardware fingerprint"
                            value={createFingerprint}
                            onChange={(e) => setCreateFingerprint(e.target.value)}
                        />
                    </div>
                </div>
                <button style={s.btn} onClick={handleCreate}>
                    ✨ Create Soul Key
                </button>
            </div>
        </div>
    );

    // ── Events Tab ─────────────────────────────────────────

    const renderEvents = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Add Life Event</div>
            {!soulKey ? (
                <div style={s.loadingText}>Search for a Soul Key first to add events.</div>
            ) : (
                <div style={s.card}>
                    <div style={{ fontSize: '0.82rem', opacity: 0.6, marginBottom: 12 }}>
                        Adding event for: <strong style={{ color: '#f472b6' }}>{soulKey.citizen_id}</strong>
                    </div>
                    <div style={s.formRow}>
                        <div style={s.formGroup}>
                            <label style={s.label}>Event Type</label>
                            <select
                                style={s.select}
                                value={eventType}
                                onChange={(e) => setEventType(e.target.value)}
                            >
                                {EVENT_TYPES.map((t) => (
                                    <option key={t} value={t}>{t}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div style={s.formRow}>
                        <div style={s.formGroup}>
                            <label style={s.label}>Raw Data (will be hashed, NEVER stored)</label>
                            <textarea
                                style={{
                                    ...s.input,
                                    minHeight: 60,
                                    fontFamily: 'monospace',
                                    resize: 'vertical',
                                } as React.CSSProperties}
                                placeholder="Enter data to hash for this life event"
                                value={eventData}
                                onChange={(e) => setEventData(e.target.value)}
                            />
                        </div>
                    </div>
                    <div style={s.formRow}>
                        <div style={s.formGroup}>
                            <label style={s.label}>Metadata (JSON)</label>
                            <textarea
                                style={{
                                    ...s.input,
                                    minHeight: 60,
                                    fontFamily: 'monospace',
                                    resize: 'vertical',
                                } as React.CSSProperties}
                                placeholder='{"source": "government", "region": "nepal"}'
                                value={eventMetadata}
                                onChange={(e) => setEventMetadata(e.target.value)}
                            />
                        </div>
                    </div>
                    <button style={s.btn} onClick={handleAddEvent}>
                        ➕ Add Life Event
                    </button>
                </div>
            )}
        </div>
    );

    // ── Lockout Tab ────────────────────────────────────────

    const renderLockout = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Lockout Protocol</div>
            {!soulKey ? (
                <div style={s.loadingText}>Search for a Soul Key first to manage lockout.</div>
            ) : (
                <>
                    {/* Attestation */}
                    <div style={s.card}>
                        <div style={s.cardTitle}>Hardware Attestation</div>
                        <div style={s.formRow}>
                            <div style={s.formGroup}>
                                <label style={s.label}>Device Fingerprint</label>
                                <input
                                    style={s.input}
                                    placeholder="Enter device fingerprint to attest"
                                    value={attestFingerprint}
                                    onChange={(e) => setAttestFingerprint(e.target.value)}
                                />
                            </div>
                        </div>
                        <button style={s.btn} onClick={handleAttest}>
                            🔐 Attest Device
                        </button>
                    </div>

                    {/* Trigger Lockout */}
                    <div style={{ ...s.card, marginTop: 16 }}>
                        <div style={s.cardTitle}>Trigger Lockout</div>
                        <div style={s.formRow}>
                            <div style={s.formGroup}>
                                <label style={s.label}>Session ID</label>
                                <input
                                    style={s.input}
                                    placeholder="Session to revoke"
                                    value={lockoutSessionId}
                                    onChange={(e) => setLockoutSessionId(e.target.value)}
                                />
                            </div>
                            <div style={s.formGroup}>
                                <label style={s.label}>Device Fingerprint (attempted)</label>
                                <input
                                    style={s.input}
                                    placeholder="Device that triggered lockout"
                                    value={lockoutFingerprint}
                                    onChange={(e) => setLockoutFingerprint(e.target.value)}
                                />
                            </div>
                        </div>
                        <div style={s.formRow}>
                            <div style={s.formGroup}>
                                <label style={s.label}>Reason</label>
                                <textarea
                                    style={{
                                        ...s.input,
                                        minHeight: 60,
                                        fontFamily: 'monospace',
                                        resize: 'vertical',
                                    } as React.CSSProperties}
                                    placeholder="Reason for lockout"
                                    value={lockoutReason}
                                    onChange={(e) => setLockoutReason(e.target.value)}
                                />
                            </div>
                        </div>
                        <button style={s.btnDanger} onClick={handleTriggerLockout}>
                            🔒 Trigger Lockout
                        </button>
                    </div>
                </>
            )}
        </div>
    );

    // ── Main Render ───────────────────────────────────────────

    const tabs = [
        { key: 'overview', label: 'Overview', icon: '📊' },
        { key: 'search', label: 'Search', icon: '🔍' },
        { key: 'create', label: 'Create', icon: '✨' },
        { key: 'events', label: 'Events', icon: '📋' },
        { key: 'lockout', label: 'Lockout', icon: '🔒' },
    ] as const;

    return (
        <div style={s.container}>
            <div style={s.header}>Soul Key Protocol Dashboard</div>

            {error && <div style={s.errorBox}>{error}</div>}
            {success && <div style={s.successBox}>{success}</div>}

            {loading ? (
                <div style={s.loadingText}>Loading Soul Key data...</div>
            ) : (
                <>
                    {/* Tab Navigation */}
                    <div style={{
                        display: 'flex',
                        gap: 4,
                        marginBottom: 20,
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                        paddingBottom: 0,
                        flexWrap: 'wrap',
                    }}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key)}
                                style={{
                                    padding: '8px 16px',
                                    border: 'none',
                                    background: 'transparent',
                                    color: activeTab === tab.key ? '#f472b6' : 'rgba(255,255,255,0.4)',
                                    cursor: 'pointer',
                                    fontSize: '0.82rem',
                                    fontWeight: activeTab === tab.key ? 600 : 400,
                                    borderBottom: activeTab === tab.key ? '2px solid #f472b6' : '2px solid transparent',
                                    transition: 'all 0.2s ease',
                                    fontFamily: 'inherit',
                                }}
                            >
                                {tab.icon} {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    {activeTab === 'overview' && renderOverview()}
                    {activeTab === 'search' && renderSearch()}
                    {activeTab === 'create' && renderCreate()}
                    {activeTab === 'events' && renderEvents()}
                    {activeTab === 'lockout' && renderLockout()}
                </>
            )}
        </div>
    );
};

export default SoulKeyDashboard;