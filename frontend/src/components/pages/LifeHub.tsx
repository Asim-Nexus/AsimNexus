/**
 * Life Hub — Life Journey, Universe, Mirror Evolution
 * Uses SmartHub for consistent tab layout
 */
import SmartHub from '../shared/SmartHub';
import LifeJourney from '../life/LifeJourney';
import PersonalUniverseDashboard from '../universe/PersonalUniverseDashboard';
import MirrorEvolutionHub from '../mirror/MirrorEvolutionHub';

const TABS = [
    { id: 'journey', icon: '🧬', label: 'Journey', desc: 'Life Stages & Milestones' },
    { id: 'universe', icon: '🌌', label: 'Universe', desc: 'Personal Universe Manager' },
    { id: 'mirror', icon: '🪞', label: 'Mirror', desc: 'Digital Twin & Evolution' },
];

interface LifeHubProps {
    user?: Record<string, unknown>;
}

export default function LifeHub({ user }: LifeHubProps) {
    return (
        <SmartHub
            tabs={TABS}
            title="Life"
            icon="🌱"
            accentColor="#a855f7"
            defaultTab={0}
        >
            {(tab) => {
                switch (tab.id) {
                    case 'journey':
                        return <LifeJourney user={(user ?? null) as { id?: string } | null} />;
                    case 'universe':
                        return <PersonalUniverseDashboard />;
                    case 'mirror':
                        return <MirrorEvolutionHub />;
                    default:
                        return <LifeJourney user={(user ?? null) as { id?: string } | null} />;
                }
            }}
        </SmartHub>
    );
}
