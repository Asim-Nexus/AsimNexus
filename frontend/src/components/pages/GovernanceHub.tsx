/**
 * GovernanceHub.tsx
 * SmartHub-based page for governance features:
 * - Government Dashboard (51%)
 * - Enterprise Dashboard (49%)
 * - Governance Chat (100% User)
 * - Stakeholder Coordinator
 * - Dharma Veto (Ethics Engine)
 */
import { useState, useEffect, useCallback } from 'react';
import SmartHub from '../shared/SmartHub';
import GovernmentDashboard from '../governance/GovernmentDashboard';
import EnterpriseDashboard from '../enterprise/EnterpriseDashboard';
import GovernanceChat from '../governance/GovernanceChat';
import VetoPanel from '../governance/VetoPanel';
import { stakeholderAPI } from '../../api/asimnexus';

interface GovernanceHubProps {
    user?: Record<string, unknown>;
}

const TABS = [
    { id: 'government', label: '🏛️ Government', icon: '🏛️', desc: '51% Public Control' },
    { id: 'enterprise', label: '🏢 Enterprise', icon: '🏢', desc: '49% Private Sector' },
    { id: 'chat', label: '💬 Governance Chat', icon: '💬', desc: 'Natural Language' },
    { id: 'stakeholder', label: '🤝 Stakeholder', icon: '🤝', desc: 'Coordinator' },
    { id: 'veto', label: '⚖️ Dharma Veto', icon: '⚖️', desc: 'Ethics & Veto Engine' },
];

export default function GovernanceHub({ user }: GovernanceHubProps) {
    const [stakeholderStats, setStakeholderStats] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(true);

    const loadStakeholderStats = useCallback(async () => {
        try {
            const res = await stakeholderAPI.getStats();
            const data = res.data?.data || res.data;
            setStakeholderStats((data || {}) as Record<string, unknown>);
        } catch {
            setStakeholderStats(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadStakeholderStats();
    }, [loadStakeholderStats]);

    return (
        <SmartHub
            tabs={TABS}
            defaultTab={0}
            accentColor="#10b981"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'government':
                        return <GovernmentDashboard user={user} />;
                    case 'enterprise':
                        return <EnterpriseDashboard user={user} />;
                    case 'chat':
                        return (
                            <div style={{ height: '100%', padding: 16 }}>
                                <GovernanceChat user={user} />
                            </div>
                        );
                    case 'stakeholder':
                        return (
                            <div style={{ padding: 16, height: '100%', overflow: 'auto' }}>
                                <h3 style={{ color: '#e2e8f0', margin: '0 0 16px 0' }}>🤝 Stakeholder Coordinator</h3>
                                {loading ? (
                                    <div style={{ color: '#94a3b8' }}>Loading stakeholder stats...</div>
                                ) : stakeholderStats ? (
                                    <pre style={{
                                        background: 'rgba(15,23,42,0.6)',
                                        padding: 16, borderRadius: 12,
                                        color: '#e2e8f0', fontSize: 13,
                                        overflow: 'auto', maxHeight: '70vh',
                                    }}>
                                        {JSON.stringify(stakeholderStats, null, 2)}
                                    </pre>
                                ) : (
                                    <div style={{ color: '#94a3b8' }}>
                                        Stakeholder coordinator stats unavailable. Use the Governance Chat or individual dashboards.
                                    </div>
                                )}
                            </div>
                        );
                    case 'veto':
                        return <VetoPanel user={user} />;
                    default:
                        return <GovernmentDashboard user={user} />;
                }
            }}
        </SmartHub>
    );
}
