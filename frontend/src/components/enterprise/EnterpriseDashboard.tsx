/**
 * EnterpriseDashboard — 49% Private Sector Hub
 *
 * Main dashboard for enterprise/commercial users to manage licenses,
 * check compliance, hire agents, and monitor private sector operations.
 * Uses SmartHub tab-based layout.
 */
import { useState, useEffect, useCallback } from 'react';
import SmartHub from '../shared/SmartHub';
import LicenseManager from './LicenseManager';
import AgentHiringPanel from './AgentHiringPanel';
import CompliancePanel from './CompliancePanel';
import { enterpriseAPI } from '../../api/asimnexus';

interface EnterpriseStats {
    total_licenses: number;
    active_licenses: number;
    total_compliance_checks: number;
    compliance_breakdown?: Record<string, number>;
    organizations?: string[];
}

const TABS = [
    { id: 'licenses', label: 'Licenses', icon: '🔑', desc: 'License Management' },
    { id: 'hiring', label: 'Hiring', icon: '🤝', desc: 'Agent Hiring' },
    { id: 'compliance', label: 'Compliance', icon: '✅', desc: 'Compliance Checks' },
];

interface EnterpriseDashboardProps {
    user?: Record<string, unknown>;
}

export default function EnterpriseDashboard({ user }: EnterpriseDashboardProps) {
    const [stats, setStats] = useState<EnterpriseStats | null>(null);
    const [loading, setLoading] = useState(true);

    const loadStats = useCallback(async () => {
        try {
            const res = await enterpriseAPI.getStats();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            setStats((responseData?.data || responseData) as EnterpriseStats);
        } catch {
            setStats({
                total_licenses: 0,
                active_licenses: 0,
                total_compliance_checks: 0,
                compliance_breakdown: {},
                organizations: [],
            });
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadStats();
        const interval = setInterval(loadStats, 30000);
        return () => clearInterval(interval);
    }, [loadStats]);

    return (
        <SmartHub
            tabs={TABS}
            title="Enterprise Dashboard"
            icon="🏢"
            accentColor="#f59e0b"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'licenses':
                        return <LicenseManager user={user} stats={stats} loading={loading} />;
                    case 'hiring':
                        return <AgentHiringPanel user={user} />;
                    case 'compliance':
                        return <CompliancePanel user={user} />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>Select a tab</div>;
                }
            }}
        </SmartHub>
    );
}
