/**
 * Economy Hub — Full Marketplace
 * Dashboard + Marketplace + Jobs + Contracts + Reputation + Token Bridge + MCP + Clones
 */
import SmartHub from '../shared/SmartHub';
import AgentMarketplacePanel from '../marketplace/AgentMarketplacePanel';
import ContractsPanel from '../marketplace/ContractsPanel';
import MCPPanel from '../marketplace/MCPPanel';
import WorldClones from '../clones/WorldClones';
import EconomyDashboardPanel from '../marketplace/EconomyDashboardPanel';
import ReputationPanel from '../marketplace/ReputationPanel';
import TokenBridgePanel from '../marketplace/TokenBridgePanel';
import MarketplaceEnginePanel from '../marketplace/MarketplaceEnginePanel';

const TABS = [
  { id: 'dashboard', icon: '📊', label: 'Dashboard', desc: 'Global economy stats' },
  { id: 'marketplace', icon: '🏪', label: 'Marketplace', desc: 'Digital goods & assets' },
  { id: 'agents', icon: '🤖', label: 'Jobs', desc: 'Post & hire' },
  { id: 'contracts', icon: '📜', label: 'Contracts', desc: 'Smart agreements' },
  { id: 'reputation', icon: '⭐', label: 'Reputation', desc: 'Cred & staking' },
  { id: 'bridge', icon: '🌉', label: 'Bridge', desc: 'Cross-chain' },
  { id: 'mcp', icon: '⚙️', label: 'MCP Tools', desc: 'Tool control' },
  { id: 'clones', icon: '👥', label: 'Clones', desc: '15 Founders' },
];

export default function EconomyHub({ user }) {
  return (
    <SmartHub
      tabs={TABS}
      title="Market"
      icon="🌍"
      accentColor="#10b981"
    >
      {(tab, idx) => (
        <>
          {idx === 0 && <EconomyDashboardPanel user={user} />}
          {idx === 1 && <MarketplaceEnginePanel user={user} />}
          {idx === 2 && <AgentMarketplacePanel user={user} />}
          {idx === 3 && <ContractsPanel user={user} />}
          {idx === 4 && <ReputationPanel user={user} />}
          {idx === 5 && <TokenBridgePanel user={user} />}
          {idx === 6 && <MCPPanel user={user} />}
          {idx === 7 && <WorldClones />}
        </>
      )}
    </SmartHub>
  );
}
