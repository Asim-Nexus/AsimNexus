/**
 * OS Hub — Personal OS, World OS, Deployment, Control Panel
 * All tabs wired to real components with live API data
 */
import SmartHub from '../shared/SmartHub';
import PersonalOS from '../os/PersonalOS';
import WorldOSDashboard from '../os/WorldOSDashboard';
import OSDeploymentPanel from '../os/OSDeploymentPanel';
import OSControlPanel from '../os/OSControlPanel';

const TABS = [
    { id: 'personal-os', label: 'Personal OS', icon: '💻', desc: 'Your Personal OS' },
    { id: 'world-os', label: 'World OS', icon: '🌍', desc: 'Global Operating System' },
    { id: 'deployment', label: 'Deployment', icon: '🚀', desc: 'OS Deployment' },
    { id: 'control', label: 'Control', icon: '🎮', desc: 'OS Control Panel' },
];

interface OSHubProps {
    user?: Record<string, unknown>;
}

export default function OSHub(_props: OSHubProps) {
    return (
        <SmartHub
            tabs={TABS}
            title="OS Hub"
            icon="💻"
            accentColor="#10b981"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'personal-os':
                        return <PersonalOS />;
                    case 'world-os':
                        return <WorldOSDashboard />;
                    case 'deployment':
                        return <OSDeploymentPanel />;
                    case 'control':
                        return <OSControlPanel />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>Select a tab</div>;
                }
            }}
        </SmartHub>
    );
}
