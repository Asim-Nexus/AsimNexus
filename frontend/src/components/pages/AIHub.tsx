/**
 * AI Hub — Chat, Memory, Clones, Local LLM, Self-Awareness, Mirror
 * All tabs wired to real components with live API data
 */
import SmartHub from '../shared/SmartHub';
import UniversalChat from '../chat/UniversalChat';
import MemoryPage from '../memory/MemoryPage';
import WorldClones from '../clones/WorldClones';
import LocalLLMChat from '../memory/LocalLLMChat';
import SelfAwarenessHub from '../self-awareness/SelfAwarenessHub';
import MirrorEvolutionHub from '../mirror/MirrorEvolutionHub';

const TABS = [
    { id: 'chat', label: 'Chat', icon: '💬', desc: 'AI Chat Interface' },
    { id: 'memory', label: 'Memory', icon: '🧠', desc: 'AI Memory & Context' },
    { id: 'clones', label: 'Clones', icon: '👥', desc: 'Founder Clones' },
    { id: 'local-llm', label: 'Local LLM', icon: '🤖', desc: 'Local AI Models' },
    { id: 'self-awareness', label: 'Self-Awareness', icon: '🪞', desc: 'Self-Awareness Dashboard' },
    { id: 'mirror-evolution', label: 'Mirror', icon: '🔄', desc: 'Mirror Evolution Hub' },
];

interface AIHubProps {
    user?: Record<string, unknown>;
    onCommand?: (cmd: string) => void;
}

export default function AIHub({ user, onCommand }: AIHubProps) {
    return (
        <SmartHub
            tabs={TABS}
            title="AI Hub"
            icon="🤖"
            accentColor="#667eea"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'chat':
                        return <UniversalChat user={user} onCommand={onCommand} />;
                    case 'memory':
                        return <MemoryPage />;
                    case 'clones':
                        return <WorldClones />;
                    case 'local-llm':
                        return <LocalLLMChat />;
                    case 'self-awareness':
                        return <SelfAwarenessHub />;
                    case 'mirror-evolution':
                        return <MirrorEvolutionHub />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>Select a tab</div>;
                }
            }}
        </SmartHub>
    );
}
