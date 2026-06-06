/**
 * Economy Hub — Lightweight using SmartHub
 * Agents + Contracts + MCP + Clones
 */
import SmartHub from '../shared/SmartHub';
import AgentMarketplacePanel from '../marketplace/AgentMarketplacePanel';
import ContractsPanel from '../marketplace/ContractsPanel';
import MCPPanel from '../marketplace/MCPPanel';
import WorldClones from '../clones/WorldClones';

const TABS = [
  { id: 'agents', icon: '🤖', label: 'Agents', desc: 'Hire AI (5/15/30d)' },
  { id: 'contracts', icon: '📜', label: 'Contracts', desc: 'Smart agreements' },
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
      defaultTab={0}
    >
      {(tab, idx) => (
        <>
          {idx === 0 && <AgentMarketplacePanel user={user} />}
          {idx === 1 && <ContractsPanel user={user} />}
          {idx === 2 && <MCPPanel user={user} />}
          {idx === 3 && <WorldClones />}
        </>
      )}
    </SmartHub>
  );
}
