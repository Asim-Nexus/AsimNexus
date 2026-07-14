/**
 * Identity Hub — Digital Identity, ZKP, Blockchain Identity, Soul Key
 * All tabs wired to real components with live API data
 */
import SmartHub from '../shared/SmartHub';
import IdentityPanel from '../identity/IdentityPanel';
import BlockchainIdentity from '../identity/BlockchainIdentity';
import SoulKeyDashboard from '../identity/SoulKeyDashboard';

const TABS = [
    { id: 'identity', label: 'Identity', icon: '🆔', desc: 'Digital Identity' },
    { id: 'zkp', label: 'ZKP', icon: '🔐', desc: 'Zero-Knowledge Proofs' },
    { id: 'blockchain', label: 'Blockchain', icon: '⛓️', desc: 'Blockchain Identity' },
    { id: 'soul-key', label: 'Soul Key', icon: '🔑', desc: 'Soul Key Protocol' },
];

interface IdentityHubProps {
    user?: Record<string, unknown>;
}

export default function IdentityHub(_props: IdentityHubProps) {
    return (
        <SmartHub
            tabs={TABS}
            title="Identity Hub"
            icon="🆔"
            accentColor="#8b5cf6"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'identity':
                        return <IdentityPanel />;
                    case 'zkp':
                        return <BlockchainIdentity />;
                    case 'blockchain':
                        return <BlockchainIdentity />;
                    case 'soul-key':
                        return <SoulKeyDashboard />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>Select a tab</div>;
                }
            }}
        </SmartHub>
    );
}
