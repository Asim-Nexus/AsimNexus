/**
 * Life Hub — Life Journey, Timeline, Milestones
 * Uses SmartHub for consistent tab layout
 */
import SmartHub from '../shared/SmartHub';
import LifeJourney from '../life/LifeJourney';

const TABS = [
    { id: 'journey', icon: '🧬', label: 'Journey', desc: 'Life Stages & Milestones' },
];

export default function LifeHub({ user }) {
    return (
        <SmartHub
            tabs={TABS}
            title="Life"
            icon="🌱"
            accentColor="#a855f7"
            defaultTab={0}
        >
            {(tab, idx) => (
                <>
                    {idx === 0 && <LifeJourney user={user} />}
                </>
            )}
        </SmartHub>
    );
}
