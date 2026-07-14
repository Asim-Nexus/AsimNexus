/**
 * GovernanceChat.tsx
 * Unified chat interface for governance actions — User × Government × Company
 * Allows natural-language interaction with all governance features.
 *
 * Refactored to use GovernanceChatService for command processing logic.
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import {
    processCommand,
    createMessage,
    createWelcomeMessage,
    MODE_CONFIG,
    QUICK_ACTIONS,
    ChatMode,
    ChatMessage,
} from '../../services/GovernanceChatService';

interface GovernanceChatProps {
    user?: Record<string, unknown>;
    defaultMode?: 'citizen' | 'government' | 'company';
}

export default function GovernanceChat({ user, defaultMode = 'citizen' }: GovernanceChatProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([createWelcomeMessage()]);
    const [input, setInput] = useState('');
    const [mode, setMode] = useState<ChatMode>(defaultMode);
    const [isProcessing, setIsProcessing] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    const inputRef = useRef<HTMLTextAreaElement | null>(null);

    const config = MODE_CONFIG[mode] || MODE_CONFIG.citizen;

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const addMessage = useCallback((msg: ChatMessage) => {
        setMessages(prev => [...prev, msg]);
    }, []);

    const handleCommand = useCallback(async (cmd: string) => {
        setIsProcessing(true);

        try {
            // Add user message
            addMessage(createMessage('user', { content: cmd }));

            // Process command via service
            const result = await processCommand(cmd, { user, mode });

            // Add assistant response
            addMessage(createMessage('assistant', result));
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Unknown error';
            addMessage(createMessage('assistant', {
                content: `❌ **Error:** ${errorMsg}\n\nThe backend may be unavailable. Try again later or use the dashboard panels directly.`,
                action: { type: 'error', status: 'error', error: errorMsg },
            }));
        } finally {
            setIsProcessing(false);
        }
    }, [addMessage, user, mode]);

    const handleSend = useCallback(() => {
        if (!input.trim() || isProcessing) return;
        handleCommand(input.trim());
        setInput('');
    }, [input, isProcessing, handleCommand]);

    const handleQuickAction = useCallback((cmd: string) => {
        handleCommand(cmd);
    }, [handleCommand]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }, [handleSend]);

    return (
        <div style={{
            display: 'flex', flexDirection: 'column', height: '100%',
            background: 'rgba(15, 23, 42, 0.95)', borderRadius: 16,
            border: '1px solid rgba(255,255,255,0.08)', overflow: 'hidden',
        }}>
            {/* ── Header ── */}
            <div style={{
                padding: '12px 20px',
                background: `linear-gradient(135deg, ${config.color}22, transparent)`,
                borderBottom: `1px solid ${config.color}33`,
                display: 'flex', alignItems: 'center', gap: 12,
            }}>
                <span style={{ fontSize: 24 }}>{config.icon}</span>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: 15 }}>
                        Governance Chat · {config.label}
                    </div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>
                        51% Government · 49% Enterprise · 100% User
                    </div>
                </div>
                {/* Mode Selector */}
                <div style={{ display: 'flex', gap: 4 }}>
                    {(Object.entries(MODE_CONFIG) as [ChatMode, typeof MODE_CONFIG[ChatMode]][]).map(([key, cfg]) => (
                        <button
                            key={key}
                            onClick={() => setMode(key)}
                            style={{
                                padding: '4px 10px', borderRadius: 8, fontSize: 12,
                                background: mode === key ? cfg.color : 'rgba(255,255,255,0.05)',
                                color: '#e2e8f0', border: `1px solid ${mode === key ? cfg.color : 'transparent'}`,
                                cursor: 'pointer', fontWeight: mode === key ? 700 : 400,
                            }}
                        >
                            {cfg.icon} {cfg.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* ── Messages ── */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
                {messages.map(msg => (
                    <div key={msg.id} style={{
                        display: 'flex',
                        justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        marginBottom: 12,
                    }}>
                        <div style={{
                            maxWidth: '80%',
                            padding: '10px 16px',
                            borderRadius: 16,
                            background: msg.role === 'user'
                                ? config.color
                                : msg.role === 'system'
                                    ? 'rgba(234,179,8,0.15)'
                                    : 'rgba(30, 41, 59, 0.8)',
                            color: msg.role === 'user' ? '#fff' : '#e2e8f0',
                            fontSize: 14,
                            lineHeight: 1.5,
                            whiteSpace: 'pre-wrap',
                            fontFamily: msg.content.includes('```') ? 'monospace' : 'inherit',
                        }}>
                            {msg.content}
                            {msg.action?.status === 'executing' && (
                                <span style={{ marginLeft: 8, opacity: 0.7 }}>⏳</span>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* ── Quick Actions ── */}
            <div style={{
                padding: '8px 20px',
                borderTop: '1px solid rgba(255,255,255,0.06)',
                display: 'flex', gap: 6, flexWrap: 'wrap',
            }}>
                {(QUICK_ACTIONS[mode] || QUICK_ACTIONS.citizen).map((action, i) => (
                    <button
                        key={i}
                        onClick={() => handleQuickAction(action.cmd)}
                        disabled={isProcessing}
                        style={{
                            padding: '4px 12px', borderRadius: 12, fontSize: 12,
                            background: 'rgba(255,255,255,0.06)',
                            color: '#94a3b8', border: '1px solid rgba(255,255,255,0.08)',
                            cursor: isProcessing ? 'not-allowed' : 'pointer',
                            opacity: isProcessing ? 0.5 : 1,
                            whiteSpace: 'nowrap',
                        }}
                    >
                        {action.label}
                    </button>
                ))}
            </div>

            {/* ── Input ── */}
            <div style={{
                padding: '12px 20px',
                borderTop: '1px solid rgba(255,255,255,0.06)',
                display: 'flex', gap: 10, alignItems: 'flex-end',
            }}>
                <textarea
                    ref={inputRef}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isProcessing}
                    placeholder={`Ask about governance, policies, licenses...`}
                    rows={2}
                    style={{
                        flex: 1,
                        background: 'rgba(255,255,255,0.05)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 12,
                        color: '#e2e8f0',
                        padding: '10px 14px',
                        fontSize: 14,
                        resize: 'none',
                        fontFamily: 'inherit',
                    }}
                />
                <button
                    onClick={handleSend}
                    disabled={!input.trim() || isProcessing}
                    style={{
                        width: 44, height: 44, borderRadius: '50%',
                        background: input.trim() && !isProcessing ? config.color : '#475569',
                        color: '#fff', fontSize: 18, border: 'none',
                        cursor: input.trim() && !isProcessing ? 'pointer' : 'not-allowed',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        transition: 'all 0.2s',
                    }}
                >
                    {isProcessing ? '⏳' : '↑'}
                </button>
            </div>
        </div>
    );
}
