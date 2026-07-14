/**
 * Nepal Dashboard — Digital Nepal Governance Hub
 * Shows Nepal connector status, ministries, provinces, districts, and governance integration.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { nepalAPI, governmentAPI } from '../../api/asimnexus';

interface ConnectorCounts {
    ministries: number;
    provinces: number;
    districts: number;
    banks: number;
    isps: number;
    schools: number;
    hospitals: number;
    palikas: number;
    hotels: number;
}

interface NepalStatus {
    status: string;
    region: string;
    connectors: ConnectorCounts;
}

interface Ministry {
    id: string;
    name: string;
    minister: string;
    website?: string;
}

interface Province {
    id: string;
    name: string;
    capital: string;
    population?: number;
}

interface District {
    id: string;
    name: string;
    province: string;
    area?: number;
}

interface GovernmentStats {
    status: string;
    identity_countries: number;
    total_identities: number;
    eresidency_programs: number;
    tax_countries: number;
    signature_regions: number;
    services_available: number;
}

interface NepalDashboardProps {
    user?: Record<string, unknown>;
}

const SECTION_HEADER: React.CSSProperties = {
    fontSize: '0.85rem',
    fontWeight: 700,
    color: '#c9a84c',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
};

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    padding: 16,
};

const BADGE_BASE: React.CSSProperties = {
    display: 'inline-block',
    padding: '2px 10px',
    borderRadius: 20,
    fontSize: '0.68rem',
    fontWeight: 600,
};

function StatusBadge({ status }: { status: string }) {
    const color = status === 'active' || status === 'operational' ? '#10b981' : '#f59e0b';
    return (
        <span style={{ ...BADGE_BASE, background: `${color}22`, color, border: `1px solid ${color}44` }}>
            {status}
        </span>
    );
}

function StatCard({ label, value, icon, color }: { label: string; value: number | string; icon: string; color: string }) {
    return (
        <div style={{
            ...CARD,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            minWidth: 140,
        }}>
            <span style={{ fontSize: '1.5rem' }}>{icon}</span>
            <div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color }}>{value}</div>
                <div style={{ fontSize: '0.68rem', opacity: 0.5, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
            </div>
        </div>
    );
}

export default function NepalDashboard({ user: _user }: NepalDashboardProps) {
    const [status, setStatus] = useState<NepalStatus | null>(null);
    const [govStats, setGovStats] = useState<GovernmentStats | null>(null);
    const [ministries, setMinistries] = useState<Ministry[]>([]);
    const [provinces, setProvinces] = useState<Province[]>([]);
    const [districts, setDistricts] = useState<District[]>([]);
    const [activeTab, setActiveTab] = useState<'overview' | 'ministries' | 'provinces' | 'government'>('overview');
    const [loading, setLoading] = useState(true);

    const loadAll = useCallback(async () => {
        setLoading(true);
        try {
            const [statusRes, govRes, minRes, provRes, distRes] = await Promise.allSettled([
                nepalAPI.getStatus(),
                governmentAPI.getStats(),
                nepalAPI.getMinistries(),
                nepalAPI.getProvinces(),
                nepalAPI.getDistricts(),
            ]);

            if (statusRes.status === 'fulfilled') {
                const d = statusRes.value.data as unknown as Record<string, unknown>;
                setStatus(d?.data as NepalStatus);
            }
            if (govRes.status === 'fulfilled') {
                const d = govRes.value.data as unknown as Record<string, unknown>;
                setGovStats(d?.data as GovernmentStats);
            }
            if (minRes.status === 'fulfilled') {
                const d = minRes.value.data as unknown as Record<string, unknown>;
                setMinistries((d?.data as Record<string, unknown>)?.ministries as Ministry[] || []);
            }
            if (provRes.status === 'fulfilled') {
                const d = provRes.value.data as unknown as Record<string, unknown>;
                setProvinces((d?.data as Record<string, unknown>)?.provinces as Province[] || []);
            }
            if (distRes.status === 'fulfilled') {
                const d = distRes.value.data as unknown as Record<string, unknown>;
                setDistricts((d?.data as Record<string, unknown>)?.districts as District[] || []);
            }
        } catch (err) {
            console.warn('[NepalDashboard] Error loading data:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadAll(); }, [loadAll]);

    const tabs = [
        { id: 'overview' as const, label: 'Overview', icon: '🇳🇵' },
        { id: 'ministries' as const, label: 'Ministries', icon: '🏛️' },
        { id: 'provinces' as const, label: 'Provinces', icon: '🗺️' },
        { id: 'government' as const, label: 'Gov Services', icon: '🆔' },
    ];

    if (loading) {
        return (
            <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>🇳🇵</div>
                <div>Loading Digital Nepal...</div>
            </div>
        );
    }

    return (
        <div style={{ padding: 16, maxWidth: 1200, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#c9a84c' }}>
                        🇳🇵 Digital Nepal
                    </div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: 2 }}>
                        AsimNexus Nepal Governance Integration
                    </div>
                </div>
                {status && <StatusBadge status={status.status} />}
            </div>

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
                {tabs.map(tab => (
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

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {/* Connector Stats Grid */}
                    <div style={SECTION_HEADER}>📡 Nepal Connectors</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        <StatCard label="Ministries" value={status?.connectors?.ministries ?? 0} icon="🏛️" color="#c9a84c" />
                        <StatCard label="Provinces" value={status?.connectors?.provinces ?? 0} icon="🗺️" color="#3b82f6" />
                        <StatCard label="Districts" value={status?.connectors?.districts ?? 0} icon="📍" color="#10b981" />
                        <StatCard label="Banks" value={status?.connectors?.banks ?? 0} icon="🏦" color="#f59e0b" />
                        <StatCard label="ISPs" value={status?.connectors?.isps ?? 0} icon="🌐" color="#8b5cf6" />
                        <StatCard label="Schools" value={status?.connectors?.schools ?? 0} icon="📚" color="#06b6d4" />
                        <StatCard label="Hospitals" value={status?.connectors?.hospitals ?? 0} icon="🏥" color="#ef4444" />
                        <StatCard label="Palikas" value={status?.connectors?.palikas ?? 0} icon="🏘️" color="#f97316" />
                        <StatCard label="Hotels" value={status?.connectors?.hotels ?? 0} icon="🏨" color="#ec4899" />
                    </div>

                    {/* Government Services Stats */}
                    {govStats && (
                        <>
                            <div style={{ ...SECTION_HEADER, marginTop: 8 }}>🆔 Government Services</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                                <StatCard label="e-ID Countries" value={govStats.identity_countries} icon="🌍" color="#c9a84c" />
                                <StatCard label="Total Identities" value={govStats.total_identities} icon="👤" color="#3b82f6" />
                                <StatCard label="e-Residency Programs" value={govStats.eresidency_programs} icon="🪪" color="#10b981" />
                                <StatCard label="Tax Countries" value={govStats.tax_countries} icon="💰" color="#f59e0b" />
                                <StatCard label="Signature Regions" value={govStats.signature_regions} icon="✍️" color="#8b5cf6" />
                                <StatCard label="Services Available" value={govStats.services_available} icon="⚙️" color="#06b6d4" />
                            </div>
                        </>
                    )}

                    {/* Quick Actions */}
                    <div style={SECTION_HEADER}>⚡ Quick Actions</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {[
                            { label: 'Apply e-Residency', icon: '🪪', action: () => setActiveTab('government') },
                            { label: 'View Ministries', icon: '🏛️', action: () => setActiveTab('ministries') },
                            { label: 'Explore Provinces', icon: '🗺️', action: () => setActiveTab('provinces') },
                            { label: 'Calculate Tax', icon: '💰', action: () => setActiveTab('government') },
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

            {/* Ministries Tab */}
            {activeTab === 'ministries' && (
                <div>
                    <div style={SECTION_HEADER}>🏛️ Nepal Ministries ({ministries.length})</div>
                    {ministries.length === 0 ? (
                        <div style={{ color: '#94a3b8', padding: 20, textAlign: 'center' }}>
                            No ministry data available. Ensure backend Nepal connectors are initialized.
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {ministries.map((m, i) => (
                                <div key={m.id || i} style={CARD}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{m.name}</div>
                                            <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>Minister: {m.minister}</div>
                                        </div>
                                        {m.website && (
                                            <a href={m.website} target="_blank" rel="noopener noreferrer"
                                                style={{ color: '#c9a84c', fontSize: '0.72rem', textDecoration: 'none' }}>
                                                Website ↗
                                            </a>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Provinces Tab */}
            {activeTab === 'provinces' && (
                <div>
                    <div style={SECTION_HEADER}>🗺️ Nepal Provinces ({provinces.length})</div>
                    {provinces.length === 0 ? (
                        <div style={{ color: '#94a3b8', padding: 20, textAlign: 'center' }}>
                            No province data available.
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {provinces.map((p, i) => (
                                <div key={p.id || i} style={CARD}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{p.name}</div>
                                            <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                                Capital: {p.capital}
                                                {p.population ? ` · Population: ${(p.population / 1_000_000).toFixed(1)}M` : ''}
                                            </div>
                                        </div>
                                        <span style={{ fontSize: '0.72rem', opacity: 0.4 }}>Province {p.id}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Districts */}
                    {districts.length > 0 && (
                        <>
                            <div style={{ ...SECTION_HEADER, marginTop: 16 }}>📍 Districts ({districts.length})</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                {districts.slice(0, 50).map((d, i) => (
                                    <div key={d.id || i} style={{
                                        ...CARD,
                                        padding: '6px 12px',
                                        fontSize: '0.72rem',
                                    }}>
                                        {d.name}
                                    </div>
                                ))}
                                {districts.length > 50 && (
                                    <div style={{ color: '#94a3b8', fontSize: '0.72rem', padding: '6px 12px' }}>
                                        +{districts.length - 50} more
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* Government Services Tab */}
            {activeTab === 'government' && (
                <div>
                    <div style={SECTION_HEADER}>🆔 Digital Identity & e-Residency</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {/* e-Residency */}
                        <div style={CARD}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>🪪 e-Residency</div>
                                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                        {govStats?.eresidency_programs ?? 0} programs available
                                    </div>
                                </div>
                                <span style={{ ...BADGE_BASE, background: '#10b98122', color: '#10b981', border: '1px solid #10b98144' }}>
                                    Active
                                </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.7, lineHeight: 1.5 }}>
                                Apply for digital residency in Nepal. Get a government-issued digital identity
                                with access to all AsimNexus governance services.
                            </div>
                        </div>

                        {/* Digital Identity */}
                        <div style={CARD}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>👤 Digital Identity</div>
                                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                        {govStats?.identity_countries ?? 0} countries supported
                                    </div>
                                </div>
                                <span style={{ ...BADGE_BASE, background: '#3b82f622', color: '#3b82f6', border: '1px solid #3b82f644' }}>
                                    {govStats?.total_identities ?? 0} identities
                                </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.7, lineHeight: 1.5 }}>
                                Create and verify your digital identity. Supports multiple verification levels
                                with blockchain-backed credentials.
                            </div>
                        </div>

                        {/* Tax Services */}
                        <div style={CARD}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>💰 Tax Services</div>
                                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                        {govStats?.tax_countries ?? 0} countries supported
                                    </div>
                                </div>
                                <span style={{ ...BADGE_BASE, background: '#f59e0b22', color: '#f59e0b', border: '1px solid #f59e0b44' }}>
                                    Available
                                </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.7, lineHeight: 1.5 }}>
                                Calculate tax liability, prepare returns, and file digitally. Supports
                                Nepal-specific tax rules and deductions.
                            </div>
                        </div>

                        {/* Digital Signatures */}
                        <div style={CARD}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>✍️ Digital Signatures</div>
                                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                        {govStats?.signature_regions ?? 0} regions supported
                                    </div>
                                </div>
                            </div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.7, lineHeight: 1.5 }}>
                                Legally binding digital signatures with government-recognized certificate authorities.
                                Supports Nepal's digital signature framework.
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
