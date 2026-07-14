import { useState, useEffect, useRef } from 'react';
import { personalAPI, chatAPI, consensusV1API } from '../../api/asimnexus';

/**
 * 15 World-Role Founder Clones — static defaults for offline/resilience.
 * Backend data merges on top via mergeStatic() for graceful fallback.
 */

interface CloneData {
    role: string;
    icon: string;
    specialty: string;
    color: string;
    bg: string;
    requires_human_confirm?: boolean;
    tasks_completed?: number;
    [key: string]: unknown;
}

interface ChatMessage {
    role: string;
    text: string;
    clone?: string;
    error?: boolean;
}

interface ConsensusStats {
    total_rounds?: number;
    pending_human?: number;
}

interface CloneCardProps {
    clone: CloneData;
    active: boolean;
    onClick: () => void;
}

const CLONES_STATIC: CloneData[] = [
    { role: 'Tech Architect', icon: '💻', specialty: 'Code, System Design, Architecture', color: '#00d4ff', bg: '#001a2e' },
    { role: 'Strategic Planner', icon: '🧭', specialty: 'Vision, Risk Analysis, Long-term Planning', color: '#7c3aed', bg: '#1a0a2e' },
    { role: 'Financial Oracle', icon: '💰', specialty: 'Investment, Budget, Tax, Economic Analysis', color: '#f59e0b', bg: '#1a1200' },
    { role: 'Legal Guardian', icon: '⚖️', specialty: 'Law, Contracts, Rights, Compliance', color: '#ef4444', bg: '#1a0000' },
    { role: 'Health Sage', icon: '❤️', specialty: 'Medicine, Mental Health, Nutrition, Wellness', color: '#ec4899', bg: '#1a0010' },
    { role: 'Education Mentor', icon: '📚', specialty: 'Learning, Teaching, Skill Development', color: '#3b82f6', bg: '#00102e' },
    { role: 'Creative Muse', icon: '🎨', specialty: 'Writing, Art, Music, Design, Storytelling', color: '#f97316', bg: '#1a0800' },
    { role: 'Research Explorer', icon: '🔬', specialty: 'Science, Data Analysis, Discovery', color: '#06b6d4', bg: '#001a1a' },
    { role: 'Security Sentinel', icon: '🛡️', specialty: 'Cybersecurity, Privacy, Zero-Trust', color: '#10b981', bg: '#001a0a' },
    { role: 'Logistics Master', icon: '🚚', specialty: 'Transport, Supply Chain, Travel', color: '#84cc16', bg: '#0a1a00' },
    { role: 'Environmental Steward', icon: '🌿', specialty: 'Climate, Sustainability, Conservation', color: '#22c55e', bg: '#001a04' },
    { role: 'Social Harmonizer', icon: '🤝', specialty: 'Relationships, Community, Conflict Resolution', color: '#a855f7', bg: '#0f001a' },
    { role: 'Governance Advisor', icon: '🏛️', specialty: 'Policy, Democracy, Transparency', color: '#6366f1', bg: '#06001a' },
    { role: 'Innovation Catalyst', icon: '⚡', specialty: 'Breakthroughs, Startups, Future Tech', color: '#fbbf24', bg: '#1a1000' },
    { role: 'Harmony Keeper', icon: '☯️', specialty: 'Dharma, Ethics, VETO, System Balance', color: '#ffffff', bg: '#0a0a0a' },
];

export default function WorldClones() {
    const [clones, setClones] = useState<CloneData[]>(CLONES_STATIC);
    const [activeClone, setActiveClone] = useState<CloneData | null>(null);
    const [message, setMessage] = useState('');
    const [chat, setChat] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [agentMode, setAgentMode] = useState(false);
    const [filterTag, setFilterTag] = useState('all');
    const [consensusStats, setConsensusStats] = useState<ConsensusStats | null>(null);
    const chatEndRef = useRef<HTMLDivElement | null>(null);

    // ── Load live data from backend ─────────────────────────────────
    useEffect(() => {
        personalAPI.getClones()
            .then((r) => {
                const data = r as unknown as { data?: { clones?: CloneData[] } };
                if (data?.data?.clones?.length) setClones(data.data.clones.map(mergeStatic));
            })
            .catch(() => { /* ignore */ });

        consensusV1API.getStats()
            .then((r) => {
                const data = r as unknown as { data?: ConsensusStats };
                if (data?.data) setConsensusStats(data.data);
            })
            .catch(() => { /* ignore */ });

    }, []);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chat]);

    function mergeStatic(apiClone: CloneData): CloneData {
        const s = CLONES_STATIC.find(c => c.role === apiClone.role) || {} as CloneData;
        return { ...s, ...apiClone };
    }

    async function sendMessage(): Promise<void> {
        if (!message.trim()) return;
        const userMsg: ChatMessage = { role: 'user', text: message };
        setChat(c => [...c, userMsg]);
        setMessage('');
        setLoading(true);
        try {
            const res = await chatAPI.sendMessage(
                userMsg.text,
                activeClone?.role ? `clone:${activeClone.role}` : 'web_user'
            );
            const data = (res as unknown as { data?: { response?: string; message?: string; clone_used?: string } })?.data || {};
            const responseText = data.response || data.message || '⚠️ No response';
            setChat(c => [...c, {
                role: 'assistant',
                text: responseText,
                clone: data.clone_used || activeClone?.role,
            }]);
        } catch (e) {
            setChat(c => [...c, {
                role: 'assistant',
                text: '⚠️ Connection error — backend चल्दैछ?',
                error: true,
            }]);
        }
        setLoading(false);
    }

    function toggleAgentMode(): void {
        const newMode = !agentMode;
        setAgentMode(newMode);
        if (newMode) {
            personalAPI.agentModeOn().catch(() => { /* ignore */ });
        } else {
            personalAPI.agentModeOff().catch(() => { /* ignore */ });
        }
    }

    const tags = ['all', 'tech', 'life', 'world', 'guard'];
    const tagMap: Record<string, string[]> = {
        tech: ['Tech Architect', 'Research Explorer', 'Security Sentinel', 'Innovation Catalyst'],
        life: ['Health Sage', 'Education Mentor', 'Financial Oracle', 'Logistics Master'],
        world: ['Strategic Planner', 'Environmental Steward', 'Social Harmonizer', 'Governance Advisor'],
        guard: ['Legal Guardian', 'Creative Muse', 'Harmony Keeper'],
    };

    const visibleClones = filterTag === 'all' ? clones
        : clones.filter(c => tagMap[filterTag]?.includes(c.role));

    return (
        <div style={styles.page}>
            {/* Header */}
            <div style={styles.header}>
                <div>
                    <h1 style={styles.title}>☯ 15 World-Role Founder Clones</h1>
                    <p style={styles.subtitle}>AsimNexus — Intelligence for Every Dimension of Human Life</p>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {consensusStats && (
                        <div style={styles.consensusBadge}>
                            🗳️ {consensusStats.total_rounds || 0} rounds
                            {(consensusStats.pending_human ?? 0) > 0 && (
                                <span style={{ color: '#fbbf24', marginLeft: 4 }}>
                                    · {consensusStats.pending_human} pending
                                </span>
                            )}
                        </div>
                    )}
                    <button
                        onClick={toggleAgentMode}
                        style={{ ...styles.agentBtn, background: agentMode ? '#10b981' : '#374151' }}
                    >
                        {agentMode ? '⚡ Agent Mode ON' : '💤 Agent Mode OFF'}
                    </button>
                </div>
            </div>

            {/* Filter Tags */}
            <div style={styles.tags}>
                {tags.map(t => (
                    <button key={t} onClick={() => setFilterTag(t)}
                        style={{ ...styles.tag, background: filterTag === t ? '#7c3aed' : '#1f2937' }}>
                        {t.toUpperCase()}
                    </button>
                ))}
            </div>

            <div style={styles.body}>
                {/* Clone Grid */}
                <div style={styles.grid}>
                    {visibleClones.map((clone, i) => (
                        <CloneCard
                            key={clone.role || i}
                            clone={clone}
                            active={activeClone?.role === clone.role}
                            onClick={() => setActiveClone(activeClone?.role === clone.role ? null : clone)}
                        />
                    ))}
                </div>

                {/* Chat Panel */}
                <div style={styles.chatPanel}>
                    <div style={styles.chatHeader}>
                        {activeClone
                            ? <><span style={{ fontSize: 24 }}>{activeClone.icon}</span> <strong>{activeClone.role}</strong></>
                            : <><span>🌐</span> <strong>All Clones — Auto-Routed</strong></>
                        }
                        {activeClone && (
                            <button onClick={() => setActiveClone(null)} style={styles.clearBtn}>✕ All</button>
                        )}
                    </div>

                    <div style={styles.chatMessages}>
                        {chat.length === 0 && (
                            <div style={styles.emptyChat}>
                                <div style={{ fontSize: 48, marginBottom: 12 }}>
                                    {activeClone ? activeClone.icon : '☯'}
                                </div>
                                <p style={{ color: '#9ca3af' }}>
                                    {activeClone
                                        ? `Speak to ${activeClone.role} — specialist in ${activeClone.specialty}`
                                        : 'Ask anything — the right clone will respond automatically'}
                                </p>
                            </div>
                        )}
                        {chat.map((m, i) => (
                            <div key={i} style={{ ...styles.bubble, ...(m.role === 'user' ? styles.userBubble : styles.aiBubble) }}>
                                <pre style={styles.msgText}>{m.text}</pre>
                            </div>
                        ))}
                        {loading && (
                            <div style={styles.aiBubble}>
                                <div style={styles.typing}>
                                    <span /><span /><span />
                                </div>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <div style={styles.inputRow}>
                        <input
                            style={styles.input}
                            value={message}
                            onChange={e => setMessage(e.target.value)}
                            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                            placeholder={activeClone ? `Ask ${activeClone.role}...` : 'Ask anything — Dharma-gated, human-confirmed...'}
                        />
                        <button onClick={sendMessage} disabled={loading} style={styles.sendBtn}>
                            {loading ? '...' : '➤'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function CloneCard({ clone, active, onClick }: CloneCardProps) {
    const color = clone.color || '#7c3aed';
    const bg = clone.bg || '#1a0a2e';
    return (
        <div onClick={onClick} style={{
            ...styles.card,
            border: active ? `2px solid ${color}` : '2px solid #1f2937',
            background: active ? bg : '#111827',
            boxShadow: active ? `0 0 20px ${color}44` : 'none',
            cursor: 'pointer',
        }}>
            <div style={{ fontSize: 28, marginBottom: 6 }}>{clone.icon || '🤖'}</div>
            <div style={{ fontWeight: 700, fontSize: 13, color: active ? color : '#e5e7eb', marginBottom: 4 }}>
                {clone.role}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280', lineHeight: 1.4 }}>
                {clone.specialty}
            </div>
            {clone.requires_human_confirm && (
                <div style={{ marginTop: 6, fontSize: 10, color: '#f59e0b' }}>⚠️ L3 Confirm</div>
            )}
            {clone.tasks_completed && clone.tasks_completed > 0 && (
                <div style={{ marginTop: 4, fontSize: 10, color: '#10b981' }}>✓ {clone.tasks_completed} tasks</div>
            )}
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    page: { minHeight: '100vh', background: '#030712', color: '#f9fafb', fontFamily: 'Inter, sans-serif', padding: '24px 20px' },
    header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 12 },
    title: { margin: 0, fontSize: 26, fontWeight: 800, background: 'linear-gradient(90deg,#7c3aed,#06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
    subtitle: { margin: '4px 0 0', color: '#6b7280', fontSize: 13 },
    consensusBadge: { background: '#1a0a2e', border: '1px solid #7c3aed', borderRadius: 8, padding: '5px 12px', color: '#c084fc', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' },
    agentBtn: { padding: '8px 18px', borderRadius: 8, border: 'none', color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer', transition: 'all 0.2s' },
    tags: { display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' },
    tag: { padding: '5px 14px', borderRadius: 20, border: 'none', color: '#d1d5db', fontSize: 12, fontWeight: 600, cursor: 'pointer' },
    body: { display: 'grid', gridTemplateColumns: '1fr 420px', gap: 20, alignItems: 'start' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 12 },
    card: { borderRadius: 12, padding: '14px 12px', transition: 'all 0.2s', textAlign: 'center' },
    chatPanel: { background: '#111827', borderRadius: 16, border: '1px solid #1f2937', display: 'flex', flexDirection: 'column', height: '75vh', position: 'sticky', top: 20 },
    chatHeader: { padding: '14px 16px', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 },
    clearBtn: { marginLeft: 'auto', background: 'transparent', border: '1px solid #374151', color: '#9ca3af', borderRadius: 6, padding: '2px 8px', cursor: 'pointer', fontSize: 11 },
    chatMessages: { flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 },
    emptyChat: { margin: 'auto', textAlign: 'center', padding: 24 },
    bubble: { padding: '10px 14px', borderRadius: 12, maxWidth: '95%', fontSize: 13 },
    userBubble: { background: '#1d4ed8', alignSelf: 'flex-end', borderRadius: '12px 12px 4px 12px' },
    aiBubble: { background: '#1f2937', alignSelf: 'flex-start', borderRadius: '12px 12px 12px 4px', borderLeft: '3px solid #7c3aed' },
    msgText: { margin: 0, fontFamily: 'inherit', fontSize: 13, whiteSpace: 'pre-wrap', wordBreak: 'break-word' },
    inputRow: { padding: '12px 16px', borderTop: '1px solid #1f2937', display: 'flex', gap: 8 },
    input: { flex: 1, background: '#1f2937', border: '1px solid #374151', borderRadius: 8, padding: '10px 14px', color: '#f9fafb', fontSize: 13, outline: 'none' },
    sendBtn: { background: '#7c3aed', border: 'none', color: '#fff', borderRadius: 8, padding: '10px 16px', cursor: 'pointer', fontWeight: 700, fontSize: 15 },
    typing: { display: 'flex', gap: 4, alignItems: 'center', padding: '4px 0' },
};
