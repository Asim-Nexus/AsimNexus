/**
 * Nepal Digital Identity — Nagarik App, National e-ID, PAN Integration
 * Backed by core/nepal/government_integrations.py and routes/government.py
 *
 * Features:
 *   - Nagarik App (Digital Citizenship) verification
 *   - National e-ID (National Identity Card) management
 *   - PAN / VAT registration & verification
 *   - Document verification (citizenship, passport, eid, pan, nagarik)
 *   - Biometric & multi-level verification (basic, advanced, biometric)
 *   - Government service integration status
 */
import React, { useState, useEffect, useCallback } from 'react';
import { governmentAPI } from '../../api/asimnexus';

// ── Types ─────────────────────────────────────────────────────────────────────

interface GovStatus {
    status: string;
    identity_countries: number;
    total_identities: number;
    eresidency_programs: number;
    tax_countries: number;
    signature_regions: number;
    services_available: number;
}

interface IdentityCountry {
    name: string;
    eid_system: string;
    verification_levels: string[];
    status: string;
}

interface IdentityResult {
    identity_id?: string;
    user_id?: string;
    country?: string;
    identity_type?: string;
    status?: string;
    verified?: boolean;
    verification_level?: number;
    document_type?: string;
    document_id?: string;
    authority?: string;
    verification_id?: string;
    success?: boolean;
    error?: string;
}

interface GovService {
    id: string;
    name: string;
    type: string;
    status: string;
    features: string[];
    url?: string;
}

// ── Styles ────────────────────────────────────────────────────────────────────

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    padding: 16,
};

const INPUT: React.CSSProperties = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: '10px 14px',
    color: '#e2e8f0',
    fontSize: '0.85rem',
    width: '100%',
    outline: 'none',
    boxSizing: 'border-box' as const,
};

const SELECT: React.CSSProperties = {
    ...INPUT,
    cursor: 'pointer',
};

const BTN_PRIMARY: React.CSSProperties = {
    background: 'linear-gradient(135deg, #c9a84c, #a8882e)',
    border: 'none',
    borderRadius: 8,
    padding: '10px 24px',
    color: '#0a0a1a',
    fontWeight: 700,
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'all 0.15s',
};

const BTN_SECONDARY: React.CSSProperties = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: '10px 24px',
    color: '#e2e8f0',
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'all 0.15s',
};

const BADGE_BASE: React.CSSProperties = {
    display: 'inline-block',
    padding: '2px 10px',
    borderRadius: 20,
    fontSize: '0.68rem',
    fontWeight: 600,
};

const SECTION_HEADER: React.CSSProperties = {
    fontSize: '0.85rem',
    fontWeight: 700,
    color: '#c9a84c',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
};

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
    const color = status === 'active' || status === 'operational' || status === 'verified'
        ? '#10b981'
        : status === 'pending' || status === 'processing'
            ? '#f59e0b'
            : '#ef4444';
    return (
        <span style={{ ...BADGE_BASE, background: `${color}22`, color, border: `1px solid ${color}44` }}>
            {status}
        </span>
    );
}

function ServiceCard({ service }: { service: GovService }) {
    const typeIcons: Record<string, string> = {
        digital_citizenship: '🪪',
        national_id: '🆔',
        tax: '💰',
        business: '🏢',
    };
    const icon = typeIcons[service.type] || '⚙️';
    return (
        <div style={{ ...CARD, display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <span style={{ fontSize: '1.3rem' }}>{icon}</span>
            <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: '0.82rem' }}>{service.name}</span>
                    <StatusBadge status={service.status} />
                </div>
                <div style={{ fontSize: '0.68rem', opacity: 0.5, textTransform: 'capitalize', marginBottom: 6 }}>
                    {service.type.replace(/_/g, ' ')}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {service.features.map((f, i) => (
                        <span key={i} style={{
                            ...BADGE_BASE,
                            background: 'rgba(201,168,76,0.1)',
                            color: '#c9a84c',
                            border: '1px solid rgba(201,168,76,0.2)',
                        }}>
                            {f.replace(/_/g, ' ')}
                        </span>
                    ))}
                </div>
                {service.url && (
                    <a href={service.url} target="_blank" rel="noopener noreferrer"
                        style={{ color: '#c9a84c', fontSize: '0.72rem', textDecoration: 'none', display: 'inline-block', marginTop: 6 }}>
                        Visit {service.name} ↗
                    </a>
                )}
            </div>
        </div>
    );
}

// ── Main Component ────────────────────────────────────────────────────────────

interface NepalDigitalIdentityProps {
    user?: Record<string, unknown>;
}

const DOCUMENT_TYPES = [
    { value: 'citizenship', label: '🇳🇵 Citizenship' },
    { value: 'passport', label: '🛂 Passport' },
    { value: 'eid', label: '🆔 National e-ID' },
    { value: 'pan', label: '💰 PAN Card' },
    { value: 'nagarik', label: '📱 Nagarik App' },
];

const VERIFICATION_LEVELS = [
    { value: 'basic', label: 'Basic (Name & DOB)' },
    { value: 'advanced', label: 'Advanced (Photo ID)' },
    { value: 'biometric', label: 'Biometric (Fingerprint)' },
];

export default function NepalDigitalIdentity({ user }: NepalDigitalIdentityProps) {
    const [status, setStatus] = useState<GovStatus | null>(null);
    const [countries, setCountries] = useState<IdentityCountry[]>([]);
    const [services, setServices] = useState<GovService[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Identity creation form
    const [identityType, setIdentityType] = useState<string>('basic');
    const [creating, setCreating] = useState(false);
    const [createdIdentity, setCreatedIdentity] = useState<IdentityResult | null>(null);

    // Verification form
    const [docType, setDocType] = useState<string>('citizenship');
    const [docId, setDocId] = useState<string>('');
    const [verifyLevel, setVerifyLevel] = useState<string>('basic');
    const [verifying, setVerifying] = useState(false);
    const [verifyResult, setVerifyResult] = useState<IdentityResult | null>(null);

    const [activeTab, setActiveTab] = useState<'overview' | 'create' | 'verify' | 'services'>('overview');

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [statusRes, countriesRes, servicesRes] = await Promise.allSettled([
                governmentAPI.getStats(),
                governmentAPI.getIdentityCountries(),
                governmentAPI.getServices('NP'),
            ]);

            if (statusRes.status === 'fulfilled') {
                const d = statusRes.value.data as unknown as Record<string, unknown>;
                setStatus(d?.data as GovStatus);
            }
            if (countriesRes.status === 'fulfilled') {
                const d = countriesRes.value.data as unknown as Record<string, unknown>;
                const list = (d?.data as Record<string, unknown>)?.countries as IdentityCountry[] || [];
                setCountries(list);
            }
            if (servicesRes.status === 'fulfilled') {
                const d = servicesRes.value.data as unknown as Record<string, unknown>;
                const list = (d?.data as Record<string, unknown>)?.services as GovService[] || [];
                setServices(list);
            }
        } catch (err) {
            console.warn('[NepalDigitalIdentity] Error loading data:', err);
            setError('Failed to load identity data');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadData(); }, []);

    const handleCreateIdentity = async () => {
        setCreating(true);
        setCreatedIdentity(null);
        setError(null);
        try {
            const res = await governmentAPI.createIdentity({
                user_id: (user?.id as string) || 'anonymous',
                country: 'NP',
                identity_type: identityType,
                metadata: { source: 'nepal_digital_identity_ui' },
            });
            const d = res.data as unknown as Record<string, unknown>;
            setCreatedIdentity(d?.data as IdentityResult);
        } catch (err) {
            console.warn('[NepalDigitalIdentity] Create error:', err);
            setError('Failed to create identity');
        } finally {
            setCreating(false);
        }
    };

    const handleVerifyIdentity = async () => {
        if (!docId.trim()) return;
        setVerifying(true);
        setVerifyResult(null);
        setError(null);
        try {
            const res = await governmentAPI.verifyIdentity({
                identity_id: createdIdentity?.identity_id || (user?.id as string) || 'anonymous',
                level: VERIFICATION_LEVELS.findIndex(l => l.value === verifyLevel) + 1,
                documents: [{ type: docType, id: docId }],
            });
            const d = res.data as unknown as Record<string, unknown>;
            setVerifyResult(d?.data as IdentityResult);
        } catch (err) {
            console.warn('[NepalDigitalIdentity] Verify error:', err);
            setError('Failed to verify identity');
        } finally {
            setVerifying(false);
        }
    };

    if (loading) {
        return (
            <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>🆔</div>
                <div>Loading Nepal Digital Identity...</div>
            </div>
        );
    }

    return (
        <div style={{ padding: 16, maxWidth: 900, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#c9a84c' }}>
                        🆔 Nepal Digital Identity
                    </div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: 2 }}>
                        Nagarik App · National e-ID · PAN — Government of Nepal
                    </div>
                </div>
                {status && <StatusBadge status={status.status} />}
            </div>

            {error && (
                <div style={{ ...CARD, border: '1px solid #ef444444', background: '#ef444411', color: '#ef4444', marginBottom: 16, fontSize: '0.82rem' }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
                {[
                    { id: 'overview' as const, label: 'Overview', icon: '📊' },
                    { id: 'create' as const, label: 'Create ID', icon: '🆕' },
                    { id: 'verify' as const, label: 'Verify', icon: '✅' },
                    { id: 'services' as const, label: 'Services', icon: '🏛️' },
                ].map(tab => (
                    <div
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            padding: '8px 16px',
                            borderRadius: 8,
                            cursor: 'pointer',
                            fontSize: '0.78rem',
                            background: activeTab === tab.id ? 'rgba(201,168,76,0.15)' : 'rgba(255,255,255,0.04)',
                            border: `1px solid ${activeTab === tab.id ? '#c9a84c44' : 'rgba(255,255,255,0.06)'}`,
                            color: activeTab === tab.id ? '#c9a84c' : 'rgba(255,255,255,0.6)',
                            transition: 'all 0.15s',
                        }}
                    >
                        {tab.icon} {tab.label}
                    </div>
                ))}
            </div>

            {/* ── Overview Tab ── */}
            {activeTab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {/* Stats Grid */}
                    <div style={SECTION_HEADER}>📊 Identity System Status</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        <div style={{ ...CARD, flex: '1 1 130px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#c9a84c' }}>
                                {status?.identity_countries ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>e-ID Countries</div>
                        </div>
                        <div style={{ ...CARD, flex: '1 1 130px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#3b82f6' }}>
                                {status?.total_identities ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>Total Identities</div>
                        </div>
                        <div style={{ ...CARD, flex: '1 1 130px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#10b981' }}>
                                {status?.eresidency_programs ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>e-Residency Programs</div>
                        </div>
                        <div style={{ ...CARD, flex: '1 1 130px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>
                                {status?.services_available ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>Services Available</div>
                        </div>
                    </div>

                    {/* e-ID Countries */}
                    {countries.length > 0 && (
                        <>
                            <div style={SECTION_HEADER}>🌍 e-ID Supported Countries</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {countries.map((c, i) => (
                                    <div key={i} style={{ ...CARD, display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <span style={{ fontSize: '1.3rem' }}>🌍</span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{c.name}</div>
                                            <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>{c.eid_system}</div>
                                        </div>
                                        <div style={{ display: 'flex', gap: 4 }}>
                                            {c.verification_levels.map((vl, j) => (
                                                <span key={j} style={{
                                                    ...BADGE_BASE,
                                                    background: 'rgba(16,185,129,0.1)',
                                                    color: '#10b981',
                                                    border: '1px solid rgba(16,185,129,0.2)',
                                                }}>
                                                    {vl}
                                                </span>
                                            ))}
                                        </div>
                                        <StatusBadge status={c.status} />
                                    </div>
                                ))}
                            </div>
                        </>
                    )}

                    {/* Quick Actions */}
                    <div style={SECTION_HEADER}>⚡ Quick Actions</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {[
                            { label: 'Create Digital Identity', icon: '🆕', action: () => setActiveTab('create') },
                            { label: 'Verify Document', icon: '✅', action: () => setActiveTab('verify') },
                            { label: 'View Government Services', icon: '🏛️', action: () => setActiveTab('services') },
                            { label: 'Apply e-Residency', icon: '🪪', action: () => window.location.href = '/nepal' },
                        ].map(action => (
                            <div
                                key={action.label}
                                onClick={action.action}
                                style={{
                                    ...CARD,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    fontSize: '0.78rem',
                                    transition: 'all 0.15s',
                                }}
                                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.08)'; }}
                                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'; }}
                            >
                                <span>{action.icon}</span>
                                <span>{action.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ── Create ID Tab ── */}
            {activeTab === 'create' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={SECTION_HEADER}>🆕 Create Digital Identity</div>
                    <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Identity Type</div>
                            <select
                                value={identityType}
                                onChange={e => setIdentityType(e.target.value)}
                                style={SELECT}
                            >
                                <option value="basic">Basic Identity</option>
                                <option value="verified">Verified Identity</option>
                                <option value="premium">Premium Identity (Biometric)</option>
                            </select>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Country</div>
                            <div style={{ ...INPUT, opacity: 0.6, cursor: 'not-allowed' }}>
                                🇳🇵 Nepal (NP)
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>User ID</div>
                            <div style={{ ...INPUT, opacity: 0.6, cursor: 'not-allowed' }}>
                                {(user?.id as string) || 'anonymous'}
                            </div>
                        </div>

                        <button
                            onClick={handleCreateIdentity}
                            disabled={creating}
                            style={{
                                ...BTN_PRIMARY,
                                opacity: creating ? 0.5 : 1,
                                width: '100%',
                                padding: '12px 24px',
                            }}
                        >
                            {creating ? '⏳ Creating Identity...' : '🆕 Create Digital Identity'}
                        </button>
                    </div>

                    {/* Creation Result */}
                    {createdIdentity && (
                        <div style={{
                            ...CARD,
                            border: `1px solid ${createdIdentity.success !== false ? '#10b98144' : '#ef444444'}`,
                            background: createdIdentity.success !== false ? '#10b98111' : '#ef444411',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                <span style={{ fontSize: '1.2rem' }}>{createdIdentity.success !== false ? '✅' : '❌'}</span>
                                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: createdIdentity.success !== false ? '#10b981' : '#ef4444' }}>
                                    {createdIdentity.success !== false ? 'Identity Created!' : 'Creation Failed'}
                                </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.78rem', opacity: 0.8 }}>
                                {createdIdentity.identity_id && (
                                    <div>ID: <span style={{ fontFamily: 'monospace', color: '#c9a84c' }}>{createdIdentity.identity_id}</span></div>
                                )}
                                {createdIdentity.status && <div>Status: <StatusBadge status={createdIdentity.status} /></div>}
                                {createdIdentity.identity_type && <div>Type: {createdIdentity.identity_type}</div>}
                                {createdIdentity.country && <div>Country: {createdIdentity.country}</div>}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Verify Tab ── */}
            {activeTab === 'verify' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={SECTION_HEADER}>✅ Verify Identity Document</div>
                    <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Document Type</div>
                            <select
                                value={docType}
                                onChange={e => setDocType(e.target.value)}
                                style={SELECT}
                            >
                                {DOCUMENT_TYPES.map(dt => (
                                    <option key={dt.value} value={dt.value}>{dt.label}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Document ID / Number</div>
                            <input
                                type="text"
                                value={docId}
                                onChange={e => setDocId(e.target.value)}
                                placeholder="Enter document number (e.g., citizenship no.)"
                                style={INPUT}
                            />
                        </div>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Verification Level</div>
                            <select
                                value={verifyLevel}
                                onChange={e => setVerifyLevel(e.target.value)}
                                style={SELECT}
                            >
                                {VERIFICATION_LEVELS.map(vl => (
                                    <option key={vl.value} value={vl.value}>{vl.label}</option>
                                ))}
                            </select>
                        </div>

                        <button
                            onClick={handleVerifyIdentity}
                            disabled={verifying || !docId.trim()}
                            style={{
                                ...BTN_PRIMARY,
                                opacity: verifying || !docId.trim() ? 0.5 : 1,
                                width: '100%',
                                padding: '12px 24px',
                            }}
                        >
                            {verifying ? '⏳ Verifying...' : '✅ Verify Document'}
                        </button>
                    </div>

                    {/* Verification Result */}
                    {verifyResult && (
                        <div style={{
                            ...CARD,
                            border: `1px solid ${verifyResult.verified ? '#10b98144' : '#ef444444'}`,
                            background: verifyResult.verified ? '#10b98111' : '#ef444411',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                <span style={{ fontSize: '1.2rem' }}>{verifyResult.verified ? '✅' : '❌'}</span>
                                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: verifyResult.verified ? '#10b981' : '#ef4444' }}>
                                    {verifyResult.verified ? 'Document Verified!' : 'Verification Failed'}
                                </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.78rem', opacity: 0.8 }}>
                                {verifyResult.document_type && <div>Type: {verifyResult.document_type}</div>}
                                {verifyResult.document_id && <div>Document: {verifyResult.document_id}</div>}
                                {verifyResult.verification_level && <div>Level: {verifyResult.verification_level}</div>}
                                {verifyResult.authority && <div>Authority: {verifyResult.authority}</div>}
                                {verifyResult.verification_id && (
                                    <div>Verification ID: <span style={{ fontFamily: 'monospace', color: '#c9a84c' }}>{verifyResult.verification_id}</span></div>
                                )}
                                {verifyResult.verified !== undefined && (
                                    <div>Status: <StatusBadge status={verifyResult.verified ? 'verified' : 'failed'} /></div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Document Type Guide */}
                    <div style={SECTION_HEADER}>📖 Supported Documents</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {DOCUMENT_TYPES.map(dt => (
                            <div key={dt.value} style={{ ...CARD, display: 'flex', alignItems: 'center', gap: 12 }}>
                                <span style={{ fontSize: '1.2rem' }}>{dt.label.split(' ')[0]}</span>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{dt.label}</div>
                                    <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>
                                        {dt.value === 'citizenship' && 'Nepal Citizenship Certificate'}
                                        {dt.value === 'passport' && 'Nepal Passport (Department of Passports)'}
                                        {dt.value === 'eid' && 'National Identity Card (e-ID)'}
                                        {dt.value === 'pan' && 'PAN / VAT Registration Certificate'}
                                        {dt.value === 'nagarik' && 'Nagarik App Digital Citizenship'}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ── Services Tab ── */}
            {activeTab === 'services' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={SECTION_HEADER}>🏛️ Government Services</div>
                    {services.length === 0 ? (
                        <div style={{ ...CARD, textAlign: 'center', color: '#94a3b8', padding: 24 }}>
                            <div style={{ fontSize: '2rem', marginBottom: 8 }}>🏛️</div>
                            <div>No government services data available.</div>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {services.map((s, i) => (
                                <ServiceCard key={s.id || i} service={s} />
                            ))}
                        </div>
                    )}

                    {/* Nagarik App Info */}
                    <div style={SECTION_HEADER}>📱 Nagarik App Integration</div>
                    <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: '1.5rem' }}>📱</span>
                            <div>
                                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>Nagarik App</div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>Government of Nepal — Digital Citizenship</div>
                            </div>
                            <StatusBadge status="active" />
                        </div>
                        <div style={{ fontSize: '0.78rem', opacity: 0.7, lineHeight: 1.5 }}>
                            The Nagarik App provides digital citizenship services including identity verification,
                            birth registration, marriage registration, and passport renewal. AsimNexus integrates
                            with Nagarik App for identity verification and document validation.
                        </div>
                        <a href="https://nagarik.app" target="_blank" rel="noopener noreferrer"
                            style={{ color: '#c9a84c', fontSize: '0.82rem', textDecoration: 'none' }}>
                            Visit Nagarik App ↗
                        </a>
                    </div>

                    {/* Refresh Button */}
                    <button onClick={loadData} style={{ ...BTN_SECONDARY, alignSelf: 'flex-start' }}>
                        🔄 Refresh Services
                    </button>
                </div>
            )}
        </div>
    );
}
