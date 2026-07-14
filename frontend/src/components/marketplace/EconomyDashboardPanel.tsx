import React, { useState, useEffect } from 'react';
import { marketplaceAPI } from '../../api/asimnexus';

interface EconomyDashboardPanelProps {
    user?: Record<string, unknown>;
}

interface StatsData {
    marketplace_engine?: Record<string, unknown>;
    marketplace?: Record<string, unknown>;
    credits?: Record<string, unknown>;
    contracts?: Record<string, unknown>;
    hybrid_economy?: Record<string, unknown>;
    reputation?: Record<string, unknown>;
    svt?: Record<string, unknown>;
    task_bus?: Record<string, unknown>;
    token_bridge?: Record<string, unknown>;
    [key: string]: unknown;
}

const EconomyDashboardPanel: React.FC<EconomyDashboardPanelProps> = ({ user: _user }) => {
    const [stats, setStats] = useState<StatsData | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    const fetchStats = async () => {
        setLoading(true);
        try {
            const r = await marketplaceAPI.getGlobalStats();
            const response = r as unknown as { data?: StatsData };
            setStats(response.data || null);
            setError('');
        } catch (e: unknown) {
            const err = e as { response?: { data?: { error?: string } }; message?: string };
            setError(err.response?.data?.error || err.message || 'Unknown error');
        }
        setLoading(false);
    };

    useEffect(() => { fetchStats(); }, []);

    const s: Record<string, React.CSSProperties> = {
        wrap: { padding: 24 },
        header: { marginBottom: 20 },
        title: {
            fontSize: '1.5rem', fontWeight: 700,
            background: 'linear-gradient(45deg, #10b981, #3b82f6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        } as React.CSSProperties,
        grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14 },
        card: {
            background: 'var(--theme-card, rgba(255,255,255,0.04))',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 14, padding: 16,
        },
        cardTitle: { fontSize: '0.7rem', opacity: 0.5, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 } as React.CSSProperties,
        statRow: { display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '0.82rem' },
        statLabel: { opacity: 0.6 },
        statVal: { fontWeight: 600, color: '#10b981' },
        refreshBtn: {
            padding: '6px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.12)',
            background: 'rgba(255,255,255,0.04)', color: 'var(--theme-text, #fff)',
            cursor: 'pointer', fontSize: '0.78rem', marginBottom: 16,
        },
        loading: { opacity: 0.5, textAlign: 'center', paddingTop: 60 },
        error: { padding: '12px 16px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', marginBottom: 16, fontSize: '0.85rem' },
    };

    if (loading) return <div style={s.wrap}><div style={s.loading}>Loading economy dashboard…</div></div>;

    const renderModule = (title: string, data: Record<string, unknown> | undefined, fields: [string, string][]) => {
        if (!data || data.error) return null;
        return (
            <div style={s.card}>
                <div style={s.cardTitle}>{title}</div>
                {fields.map(([label, key]) => (
                    <div key={key} style={s.statRow}>
                        <span style={s.statLabel}>{label}</span>
                        <span style={s.statVal}>{String(data[key] ?? '—')}</span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div style={s.wrap}>
            <div style={s.header}>
                <div style={s.title}>📊 Economy Dashboard</div>
                <div style={{ fontSize: '0.82rem', opacity: 0.5, marginTop: 4 }}>
                    Global economic overview — all modules
                </div>
            </div>
            {error && <div style={s.error}>{error}</div>}
            <button style={s.refreshBtn} onClick={fetchStats}>🔄 Refresh</button>
            {stats && (
                <div style={s.grid}>
                    {renderModule('Digital Marketplace', stats.marketplace_engine, [
                        ['Active Listings', 'active_listings'], ['Total Orders', 'total_orders'],
                        ['Completed', 'completed_orders'], ['Revenue', 'total_revenue'],
                        ['Sellers', 'total_sellers'], ['Buyers', 'total_buyers'],
                    ])}
                    {renderModule('Job Marketplace', stats.marketplace, [
                        ['Total Jobs', 'total_jobs'], ['Open Jobs', 'open_jobs'],
                        ['Completed', 'completed_jobs'], ['Total Agents', 'total_agents'],
                        ['Available Agents', 'available_agents'], ['Open Disputes', 'open_disputes'],
                    ])}
                    {renderModule('Nexus Credits', stats.credits, [
                        ['Total Circulation', 'total_credits_in_circulation'],
                        ['Total Users', 'total_users'],
                        ['Total Transactions', 'total_transactions'],
                        ['Completed', 'completed_transactions'],
                        ['ZKPs Generated', 'zkp_proofs_generated'],
                    ])}
                    {renderModule('Contracts', stats.contracts, [
                        ['Total', 'total_contracts'], ['Active', 'active_contracts'],
                        ['Completed', 'completed_contracts'], ['Disputed', 'disputed_contracts'],
                        ['Escrow Locked', 'total_escrow_locked'],
                    ])}
                    {renderModule('Hybrid Economy', stats.hybrid_economy, [
                        ['Mode', 'current_mode'], ['Accounts', 'total_accounts'],
                        ['Total Balance', 'total_balance'], ['Total Earned', 'total_earned'],
                        ['Tasks (Total)', 'total_tasks'], ['Completed', 'completed_tasks'],
                    ])}
                    {renderModule('Reputation', stats.reputation, [
                        ['Entities', 'total_entities'], ['Total Staked', 'total_staked'],
                        ['Active Stakes', 'active_stakes'], ['Total Events', 'total_events'],
                        ['Avg Score', 'average_score'],
                    ])}
                    {renderModule('SVT Token', stats.svt, [
                        ['Total Supply', 'total_supply'], ['Total Burned', 'total_burned'],
                        ['Wallets', 'total_wallets'], ['Gini Coef', 'gini'],
                        ['Escrows', 'escrow_count'],
                    ])}
                    {renderModule('Task Bus', stats.task_bus, [
                        ['Total Tasks', 'total_tasks'], ['Queued', 'queued_tasks'],
                        ['Active', 'active_tasks'], ['Agents', 'registered_agents'],
                        ['Online', 'online_agents'], ['Utilization', 'utilization_pct'],
                    ])}
                    {renderModule('Token Bridge', stats.token_bridge, [
                        ['Transactions', 'total_transactions'],
                        ['Volume Bridged', 'total_volume_bridged'],
                        ['Fees Collected', 'total_fees_collected'],
                        ['Pools', 'total_pools'], ['Liquidity', 'total_liquidity'],
                    ])}
                </div>
            )}
        </div>
    );
};

export default EconomyDashboardPanel;
