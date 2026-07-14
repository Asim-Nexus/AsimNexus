/**
 * Economy Hub — Overview, Marketplace, Contracts, Reputation, Bridge, MCP
 * All tabs wired to real components with live API data
 */
import SmartHub from '../shared/SmartHub';
import EconomyDashboardPanel from '../marketplace/EconomyDashboardPanel';
import MarketplaceEnginePanel from '../marketplace/MarketplaceEnginePanel';
import ContractsPanel from '../marketplace/ContractsPanel';
import ReputationPanel from '../marketplace/ReputationPanel';
import TokenBridgePanel from '../marketplace/TokenBridgePanel';
import MCPPanel from '../marketplace/MCPPanel';

const TABS = [
    { id: 'overview', label: 'Overview', icon: '📊', desc: 'Economy Overview' },
    { id: 'marketplace', label: 'Marketplace', icon: '🏪', desc: 'Agent Marketplace' },
    { id: 'contracts', label: 'Contracts', icon: '📝', desc: 'Smart Contracts' },
    { id: 'reputation', label: 'Reputation', icon: '⭐', desc: 'Reputation System' },
    { id: 'bridge', label: 'Bridge', icon: '🌉', desc: 'Token Bridge' },
    { id: 'mcp', label: 'MCP', icon: '🔌', desc: 'MCP Services' },
];

interface EconomyHubProps {
    user?: Record<string, unknown>;
}

export default function EconomyHub({ user }: EconomyHubProps) {
    return (
        <SmartHub
            tabs={TABS}
            title="Economy Hub"
            icon="💰"
            accentColor="#f59e0b"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'overview':
                        return <EconomyDashboardPanel user={user} />;
                    case 'marketplace':
                        return <MarketplaceEnginePanel user={user} />;
                    case 'contracts':
                        return <ContractsPanel user={user} />;
                    case 'reputation':
                        return <ReputationPanel />;
                    case 'bridge':
                        return <TokenBridgePanel />;
                    case 'mcp':
                        return <MCPPanel />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>Select a tab</div>;
                }
            }}
        </SmartHub>
    );
}
