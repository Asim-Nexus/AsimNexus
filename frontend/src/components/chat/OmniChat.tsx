// components/chat/OmniChat.jsx - Minimal for RC2
import { useState, useRef, useCallback } from 'react';

interface Message {
    id: number;
    role: string;
    content: string;
    timestamp: number;
}

interface BubbleProps {
    msg: Message;
    mode: string;
}

interface OmniChatProps {
    defaultMode?: string;
    user?: Record<string, unknown>;
    onCommand?: (cmd: string) => void;
}

const MODE_THEME: Record<string, { primary: string }> = {
    citizen: { primary: '#8b5cf6' },
    company: { primary: '#3b82f6' },
    government: { primary: '#10b981' },
};

function Bubble({ msg, mode }: BubbleProps) {
    const theme = MODE_THEME[mode] || MODE_THEME.citizen;
    const isUser = msg.role === 'user';
    return (
        <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 10 }}>
            <div style={{ maxWidth: '72%', padding: '12px 16px', borderRadius: 18, background: isUser ? theme.primary : 'rgba(15,23,42,0.8)', color: '#e2e8f0', fontSize: 14 }}>
                {msg.content}
            </div>
        </div>
    );
}

export default function OmniChat({ defaultMode = 'citizen' }: OmniChatProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isTyping, setIsTyping] = useState(false);
    const [mode] = useState(defaultMode);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    const theme = MODE_THEME[mode] || MODE_THEME.citizen;

    const handleSend = useCallback(() => {
        if (!input.trim() || isTyping) return;
        setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: input.trim(), timestamp: Date.now() }]);
        setInput('');
        setIsTyping(true);
        setTimeout(() => {
            setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'AsimNexus processed your request.', timestamp: Date.now() }]);
            setIsTyping(false);
        }, 1000);
    }, [input, isTyping]);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 500, background: '#0f172a', borderRadius: 24 }}>
            <div style={{ padding: '14px 20px', background: 'rgba(15,23,42,0.6)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ fontWeight: 700, color: '#e2e8f0' }}>AsimNexus · Omni-Chat · World OS</div>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                {messages.map(msg => <Bubble key={msg.id} msg={msg} mode={mode} />)}
                <div ref={messagesEndRef} />
            </div>
            <div style={{ padding: '14px 20px', background: 'rgba(15,23,42,0.7)', display: 'flex', gap: 10 }}>
                <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())} style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: 14, color: '#e2e8f0', padding: '10px 16px' }} placeholder="Type a message..." />
                <button onClick={handleSend} disabled={!input.trim()} style={{ width: 44, height: 44, borderRadius: '50%', background: input.trim() ? theme.primary : '#475569', color: '#fff', fontSize: 18, cursor: input.trim() ? 'pointer' : 'not-allowed' }}>↑</button>
            </div>
        </div>
    );
}
