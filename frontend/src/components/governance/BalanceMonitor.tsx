/**
 * BalanceMonitor — 51/49 Power Balance Visualization
 *
 * Displays the current power balance across all sectors with visual indicators
 * showing public (51%) vs private (49%) control distribution.
 * Supports sector-specific drill-down and real-time balance updates.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { governanceAPI } from '../../api/asimnexus';

// ── Types ────────────────────────────────────────────────────────────────

interface SectorBalance {
    sector: string;
    control: string;
    public_weight: number;
    private_weight: number;
    public_share: number;
    private_share: number;
    total_decisions: number;
    recent_public: number;
    recent_private: number;
}

interface BalanceData {
    sectors: SectorBalance[];
    overall_public_share: number;
    overall_private_share: number;
    total_decisions: number;
    total_amendments: number;
    total_audit_entries: number;
}

interface GovernanceStats {
    government?: Record<string, unknown>;
    power_balance?: {
        total_decisions: number;
        public_share: number;
        private_share: number;
        total_amendments: number;
        total_audit_entries: number;
    };
    dharma?: Record<string, unknown>;
}

interface BalanceMonitorProps {
    stats?: GovernanceStats | null;
    loading?: boolean;
}

// ── Constants ────────────────────────────────────────────────────────────

const SECTOR_COLORS: Record<string, string> = {
    education: '#3b82f6',
    healthcare: '#10b981',
    infrastructure: '#f59e0b',
    defense: '#ef4444',
    agriculture: '#22c55e',
    technology: '#8b5cf6',
    finance: '#ec4899',
    energy: '#f97316',
    transportation: '#06b6d4',
    communication: '#6366f1',
    manufacturing: '#14b8a6',
    trade: '#e11d48',
    tourism: '#a855f7',
    culture: '#d946ef',
    environment: '#84cc16',
};

// ── Component ────────────────────────────────────────────────────────────

export default function BalanceMonitor({ stats, loading: parentLoading }: BalanceMonitorProps) {
    const [balanceData, setBalanceData] = useState<BalanceData | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedSector, setSelectedSector] = useState<string | null>(null);
    const [sectorDetail, setSectorDetail] = useState<SectorBalance | null>(null);
    const [error, setError] = useState<string | null>(null);

    const loadBalance = useCallback(async () => {
        try {
            const res = await governanceAPI.getBalance();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as BalanceData;
            setBalanceData(data);
            setError(null);
        } catch {
            // Use fallback data
            setBalanceData({
                sectors: [
                    { sector: 'education', control: 'PUBLIC_COORDINATED', public_weight: 0.6, private_weight: 0.4, public_share: 0.6, private_share: 0.4, total_decisions: 0, recent_public: 0, recent_private: 0 },
                    { sector: 'healthcare', control: 'PUBLIC_COORDINATED', public_weight: 0.55, private_weight: 0.45, public_share: 0.55, private_share: 0.45, total_decisions: 0, recent_public: 0, recent_private: 0 },
                    { sector: 'infrastructure', control: 'MIXED', public_weight: 0.5, private_weight: 0.5, public_share: 0.5, private_share: 0.5, total_decisions: 0, recent_public: 0, recent_private: 0 },
                    { sector: 'technology', control: 'PRIVATE_OPERATED', public_weight: 0.3, private_weight: 0.7, public_share: 0.3, private_share: 0.7, total_decisions: 0, recent_public: 0, recent_private: 0 },
                    { sector: 'defense', control: 'PUBLIC_COORDINATED', public_weight: 0.8, private_weight: 0.2, public_share: 0.8, private_share: 0.2, total_decisions: 0, recent_public: 0, recent_private: 0 },
                ],
                overall_public_share: 0.51,
                overall_private_share: 0.49,
                total_decisions: 0,
                total_amendments: 0,
                total_audit_entries: 0,
            });
        }
        setLoading(false);
    }, []);

    const loadSectorDetail = useCallback(async (sector: string) => {
        try {
            const res = await governanceAPI.getSectorBalance(sector);
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as SectorBalance;
            setSectorDetail(data);
        } catch {
            setSectorDetail(null);
        }
    }, []);

    useEffect(() => {
        loadBalance();
        const interval = setInterval(loadBalance, 30000);
        return () => clearInterval(interval);
    }, [loadBalance]);

    useEffect(() => {
        if (selectedSector) {
            loadSectorDetail(selectedSector);
        } else {
            setSectorDetail(null);
        }
    }, [selectedSector, loadSectorDetail]);

    const displayLoading = parentLoading !== undefined ? parentLoading : loading;

    if (displayLoading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>⚖️ Loading power balance...</div>
            </div>
        );
    }

    const publicShare = balanceData?.overall_public_share ?? (stats?.power_balance?.public_share ?? 0.51);
    const privateShare = balanceData?.overall_private_share ?? (stats?.power_balance?.private_share ?? 0.49);
    const totalDecisions = balanceData?.total_decisions ?? (stats?.power_balance?.total_decisions ?? 0);
    const sectors = balanceData?.sectors ?? [];

    return (
        <div style={styles.container}>
            {/* Overall Balance Gauge */}
            <div style={styles.balanceGauge}>
                <div style={styles.gaugeHeader}>
                    <span style={styles.gaugeTitle}>⚖️ 51/49 Power Balance</span>
                    <span style={styles.gaugeSubtitle}>Constitutional Mandate</span>
                </div>
                <div style={styles.gaugeBar}>
                    <div style={styles.gaugePublicBar as React.CSSProperties}>
                        <div style={{
                            ...styles.gaugeFill,
                            width: `${publicShare * 100}%`,
                            background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
                        } as React.CSSProperties}>
                            <span style={styles.gaugeLabel}>Public {(publicShare * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    <div style={styles.gaugePrivateBar as React.CSSProperties}>
                        <div style={{
                            ...styles.gaugeFill,
                            width: `${privateShare * 100}%`,
                            background: 'linear-gradient(90deg, #f59e0b, #fbbf24)',
                            marginLeft: 'auto',
                        } as React.CSSProperties}>
                            <span style={styles.gaugeLabel}>Private {(privateShare * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
                <div style={styles.gaugeStats}>
                    <span>Total Decisions: {totalDecisions.toLocaleString()}</span>
                    <span>Amendments: {(balanceData?.total_amendments ?? stats?.power_balance?.total_amendments ?? 0).toLocaleString()}</span>
                </div>
            </div>

            {/* Sector Breakdown */}
            <h3 style={styles.sectionTitle}>Sector Breakdown</h3>
            <div style={styles.sectorGrid}>
                {sectors.length === 0 ? (
                    <div style={styles.emptyState}>No sector data available</div>
                ) : (
                    sectors.map((sector) => (
                        <div
                            key={sector.sector}
                            style={{
                                ...styles.sectorCard,
                                borderColor: selectedSector === sector.sector ? '#60a5fa' : '#334155',
                                cursor: 'pointer',
                            }}
                            onClick={() => setSelectedSector(
                                selectedSector === sector.sector ? null : sector.sector
                            )}
                        >
                            <div style={styles.sectorHeader}>
                                <span style={styles.sectorIcon}>
                                    {SECTOR_COLORS[sector.sector] ? '🏛️' : '📋'}
                                </span>
                                <span style={styles.sectorName}>
                                    {sector.sector.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                                </span>
                            </div>
                            <div style={styles.controlBadge}>
                                {sector.control.replace(/_/g, ' ')}
                            </div>
                            <div style={styles.sectorBar}>
                                <div style={{
                                    ...styles.sectorBarFill,
                                    width: `${sector.public_share * 100}%`,
                                    background: SECTOR_COLORS[sector.sector] || '#3b82f6',
                                } as React.CSSProperties} />
                            </div>
                            <div style={styles.sectorShares}>
                                <span style={{ color: '#60a5fa' }}>Pub: {(sector.public_share * 100).toFixed(0)}%</span>
                                <span style={{ color: '#fbbf24' }}>Pvt: {(sector.private_share * 100).toFixed(0)}%</span>
                            </div>
                            <div style={styles.sectorDecisions}>
                                {sector.total_decisions} decisions
                            </div>

                            {/* Expanded Detail */}
                            {selectedSector === sector.sector && sectorDetail && (
                                <div style={styles.sectorDetail}>
                                    <div style={styles.detailRow}>
                                        <span>Control Type</span>
                                        <span style={{ color: '#60a5fa', fontWeight: 600 }}>{sectorDetail.control}</span>
                                    </div>
                                    <div style={styles.detailRow}>
                                        <span>Public Weight</span>
                                        <span style={{ color: '#60a5fa' }}>{(sectorDetail.public_weight * 100).toFixed(0)}%</span>
                                    </div>
                                    <div style={styles.detailRow}>
                                        <span>Private Weight</span>
                                        <span style={{ color: '#fbbf24' }}>{(sectorDetail.private_weight * 100).toFixed(0)}%</span>
                                    </div>
                                    <div style={styles.detailRow}>
                                        <span>Recent Public Actions</span>
                                        <span style={{ color: '#60a5fa' }}>{sectorDetail.recent_public}</span>
                                    </div>
                                    <div style={styles.detailRow}>
                                        <span>Recent Private Actions</span>
                                        <span style={{ color: '#fbbf24' }}>{sectorDetail.recent_private}</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Error State */}
            {error && (
                <div style={styles.errorBanner}>
                    ⚠️ {error}
                </div>
            )}

            {/* Footer */}
            <div style={styles.footer}>
                <span>Constitutionally enforced 51% public / 49% private balance</span>
                <span style={styles.footerBrand}>AsimNexus ⚖️ Digital Nepal</span>
            </div>
        </div>
    );
}

// ── Styles ───────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
    container: {
        padding: '20px',
        color: '#e2e8f0',
        maxHeight: 'calc(100vh - 200px)',
        overflowY: 'auto',
    },
    loadingPulse: {
        textAlign: 'center',
        padding: '40px',
        color: '#94a3b8',
        fontSize: '16px',
        animation: 'pulse 1.5s ease-in-out infinite',
    },
    balanceGauge: {
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
        border: '1px solid #312e81',
        borderRadius: 12,
        padding: 16,
        marginBottom: 20,
    },
    gaugeHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    gaugeTitle: {
        fontSize: 16,
        fontWeight: 700,
        color: '#f1f5f9',
    },
    gaugeSubtitle: {
        fontSize: 11,
        color: '#64748b',
    },
    gaugeBar: {
        display: 'flex',
        height: 32,
        borderRadius: 8,
        overflow: 'hidden',
        marginBottom: 8,
    },
    gaugePublicBar: {
        flex: 1,
        display: 'flex',
    },
    gaugePrivateBar: {
        flex: 1,
        display: 'flex',
    },
    gaugeFill: {
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'width 0.5s ease',
        borderRadius: 4,
    },
    gaugeLabel: {
        fontSize: 11,
        fontWeight: 700,
        color: '#fff',
        textShadow: '0 1px 2px rgba(0,0,0,0.5)',
    },
    gaugeStats: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 11,
        color: '#64748b',
    },
    sectionTitle: {
        margin: '0 0 12px 0',
        fontSize: 15,
        color: '#f1f5f9',
    },
    sectorGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 10,
        marginBottom: 16,
    },
    emptyState: {
        gridColumn: '1 / -1',
        textAlign: 'center',
        padding: '40px',
        color: '#64748b',
        fontSize: 14,
    },
    sectorCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: 10,
        padding: 14,
        transition: 'all 0.2s ease',
    },
    sectorHeader: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 8,
    },
    sectorIcon: {
        fontSize: 18,
    },
    sectorName: {
        fontSize: 13,
        fontWeight: 600,
        color: '#e2e8f0',
    },
    controlBadge: {
        fontSize: 10,
        fontWeight: 600,
        color: '#94a3b8',
        background: '#0f172a',
        padding: '2px 8px',
        borderRadius: 4,
        display: 'inline-block',
        marginBottom: 8,
    },
    sectorBar: {
        height: 6,
        background: '#0f172a',
        borderRadius: 3,
        overflow: 'hidden',
        marginBottom: 6,
    },
    sectorBarFill: {
        height: '100%',
        borderRadius: 3,
        transition: 'width 0.5s ease',
    },
    sectorShares: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 11,
        marginBottom: 4,
    },
    sectorDecisions: {
        fontSize: 10,
        color: '#64748b',
    },
    sectorDetail: {
        marginTop: 10,
        paddingTop: 10,
        borderTop: '1px solid #334155',
    },
    detailRow: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 12,
        color: '#94a3b8',
        padding: '3px 0',
    },
    errorBanner: {
        background: '#7f1d1d',
        border: '1px solid #dc2626',
        borderRadius: 8,
        padding: '10px 14px',
        fontSize: 13,
        color: '#fca5a5',
        marginBottom: 12,
    },
    footer: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 10,
        color: '#475569',
        borderTop: '1px solid #1e293b',
        paddingTop: 10,
    },
    footerBrand: {
        color: '#7c3aed',
        fontWeight: 600,
    },
};
