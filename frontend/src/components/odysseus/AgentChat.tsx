/**
 * AgentChat.tsx
 * Enhanced chat component showing agent thinking, tool calls, and results within chat bubbles.
 *
 * Message types: user, assistant, thinking, tool_call, tool_result, error
 * Mode selector: AUTO / GUIDE / PLAN / OBSERVE
 * Integrates with ChatContext for message persistence.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChatContext } from '../../contexts/ChatContext';
import { agentAPI } from '../../api';
import './odysseus.css';

interface ModeOption {
    value: string;
    label: string;
    desc: string;
}

const MODES: ModeOption[] = [
    { value: 'AUTO', label: '🤖 Auto', desc: 'Full autonomy' },
    { value: 'GUIDE', label: '🧭 Guide', desc: 'Suggest + confirm' },
    { value: 'PLAN', label: '📋 Plan', desc: 'Step-by-step' },
    { value: 'OBSERVE', label: '👁️ Observe', desc: 'Watch only' },
];

function formatTime(ts: number | string): string {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function truncate(str: string, len = 200): string {
    if (!str) return '';
    return str.length > len ? str.slice(0, len) + '...' : str;
}

// AgentChat uses a different message shape than ChatContext's ChatMessage
// (which has id/role/content/ts). Here we use a more flexible type.
interface AgentMsg {
    id?: string;
    type?: string;
    content?: string;
    ts?: number | string;
    toolName?: string;
    toolStatus?: string;
    args?: Record<string, unknown>;
    executionTime?: number;
    [key: string]: unknown;
}

function ThinkingBubble() {
    return (
        <div className="odysseus-thinking">
            <div className="odysseus-thinking-dots">
                <span className="odysseus-dot" />
                <span className="odysseus-dot" />
                <span className="odysseus-dot" />
            </div>
            <span className="odysseus-thinking-text">Asim is thinking...</span>
        </div>
    );
}

interface ToolCallBubbleProps {
    msg: AgentMsg;
}

function ToolCallBubble({ msg }: ToolCallBubbleProps) {
    const [expanded, setExpanded] = useState(false);
    const statusIcon: Record<string, string> = {
        pending: '⏳',
        running: '🔄',
        completed: '✅',
        failed: '❌',
    };
    const statusColor: Record<string, string> = {
        pending: '#f59e0b',
        running: '#3b82f6',
        completed: '#10b981',
        failed: '#ef4444',
    };

    return (
        <div className="odysseus-tool-call">
            <div className="odysseus-tool-call-header">
                <span className="odysseus-tool-badge">🔧 {msg.toolName}</span>
                <span
                    className="odysseus-tool-status"
                    style={{ color: statusColor[msg.toolStatus || ''] || '#a0a0b0' }}
                >
                    {statusIcon[msg.toolStatus || ''] || '⏳'} {msg.toolStatus || 'pending'}
                </span>
            </div>
            <div
                className="odysseus-tool-toggle"
                onClick={() => setExpanded(!expanded)}
            >
                {expanded ? '▼' : '▶'} Arguments
            </div>
            {expanded && (
                <pre className="odysseus-code-block">{JSON.stringify(msg.args, null, 2)}</pre>
            )}
        </div>
    );
}

interface ToolResultBubbleProps {
    msg: AgentMsg;
}

function ToolResultBubble({ msg }: ToolResultBubbleProps) {
    const [showFull, setShowFull] = useState(false);
    const content = msg.content || '';

    return (
        <div className="odysseus-tool-result">
            <div className="odysseus-tool-result-preview">
                {showFull ? content : truncate(content, 200)}
                {content.length > 200 && (
                    <button
                        className="odysseus-show-more"
                        onClick={() => setShowFull(!showFull)}
                    >
                        {showFull ? 'Show less' : 'Show more'}
                    </button>
                )}
            </div>
            {msg.executionTime && (
                <span className="odysseus-time-badge">⚡ {msg.executionTime}ms</span>
            )}
        </div>
    );
}

interface ErrorBubbleProps {
    msg: AgentMsg;
}

function ErrorBubble({ msg }: ErrorBubbleProps) {
    return (
        <div className="odysseus-error-bubble">
            <span className="odysseus-error-icon">⚠️</span>
            <span>{msg.content || 'An error occurred'}</span>
        </div>
    );
}

interface MessageBubbleProps {
    msg: AgentMsg;
}

function MessageBubble({ msg }: MessageBubbleProps) {
    switch (msg.type) {
        case 'thinking':
            return <ThinkingBubble />;
        case 'tool_call':
            return <ToolCallBubble msg={msg} />;
        case 'tool_result':
            return <ToolResultBubble msg={msg} />;
        case 'error':
            return <ErrorBubble msg={msg} />;
        case 'user':
            return (
                <div className="odysseus-message odysseus-user-bubble">
                    <div className="odysseus-bubble-content">{msg.content}</div>
                    <span className="odysseus-msg-time">{formatTime(msg.ts as number)}</span>
                </div>
            );
        case 'assistant':
        default:
            return (
                <div className="odysseus-message odysseus-assistant-bubble">
                    <div className="odysseus-bubble-content">{msg.content}</div>
                    <span className="odysseus-msg-time">{formatTime(msg.ts as number)}</span>
                </div>
            );
    }
}

interface AgentChatProps {
    user?: Record<string, unknown>;
    onCommand?: (cmd: string) => void;
}

export default function AgentChat(_props: AgentChatProps) {
    const chatCtx = useChatContext();
    // ChatContext messages have {id, role, content, ts} — we store extra fields via [key:string]
    const ctxMessages: Record<string, unknown>[] = (chatCtx?.messages as unknown as Record<string, unknown>[]) || [];
    const addMsg = chatCtx?.addMessage as unknown as ((msg: Record<string, unknown>) => void) | undefined;
    const loading = chatCtx?.loading || false;
    const updateLoading = chatCtx?.updateLoading as ((v: boolean) => void) | undefined;

    const [input, setInput] = useState('');
    const [mode, setMode] = useState('AUTO');
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [modeOpen, setModeOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [ctxMessages, scrollToBottom]);

    useEffect(() => {
        // Fetch active sessions on mount
        agentAPI.sessions()
            .then(() => { })
            .catch(() => { });
    }, []);

    // Poll session status if we have an active session
    useEffect(() => {
        if (!sessionId) return;
        const interval = setInterval(async () => {
            try {
                const res = await agentAPI.status(sessionId);
                const data = res.data as Record<string, unknown>;
                if (data?.status === 'completed' || data?.status === 'cancelled' || data?.status === 'error') {
                    setSessionId(null);
                    if (updateLoading) updateLoading(false);
                    if (data.result && addMsg) {
                        addMsg({
                            id: `result-${Date.now()}`,
                            type: 'assistant',
                            content: data.result as string,
                            ts: Date.now(),
                        });
                    }
                    clearInterval(interval);
                }
                if (data?.steps && addMsg) {
                    const steps = data.steps as Array<Record<string, unknown>>;
                    steps.forEach((step) => {
                        if (step.type === 'tool_call' && !ctxMessages.find((m) => m.toolName === step.tool_name && m.ts === step.ts)) {
                            addMsg({
                                id: `tool-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                                type: 'tool_call',
                                toolName: step.tool_name as string,
                                args: (step.arguments || {}) as Record<string, unknown>,
                                toolStatus: (step.status as string) || 'pending',
                                ts: (step.ts as number) || Date.now(),
                            });
                        }
                        if (step.type === 'tool_result' && !ctxMessages.find((m) => m.type === 'tool_result' && m.toolName === step.tool_name && m.ts === step.ts)) {
                            addMsg({
                                id: `result-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                                type: 'tool_result',
                                toolName: step.tool_name as string,
                                content: (step.result as string) || '',
                                executionTime: (step.execution_time as number) || 0,
                                ts: (step.ts as number) || Date.now(),
                            });
                        }
                    });
                }
            } catch {
                // Polling failed silently
            }
        }, 2000);
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionId, updateLoading]);

    const handleSend = async () => {
        const text = input.trim();
        if (!text || loading || !addMsg) return;
        setInput('');

        addMsg({
            id: `user-${Date.now()}`,
            type: 'user',
            content: text,
            ts: Date.now(),
        });

        if (updateLoading) updateLoading(true);

        addMsg({
            id: `think-${Date.now()}`,
            type: 'thinking',
            ts: Date.now(),
        });

        try {
            const res = await agentAPI.run(text, mode);
            const data = res.data as Record<string, unknown>;

            if (data.session_id) {
                setSessionId(data.session_id as string);
            }

            if (data.result && !data.session_id) {
                // Non-streaming result
                addMsg({
                    id: `assistant-${Date.now()}`,
                    type: 'assistant',
                    content: data.result as string,
                    ts: Date.now(),
                });
                if (updateLoading) updateLoading(false);
            }

            if (data.steps) {
                const steps = data.steps as Array<Record<string, unknown>>;
                steps.forEach((step) => {
                    if (step.type === 'tool_call') {
                        addMsg({
                            id: `tool-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                            type: 'tool_call',
                            toolName: step.tool_name as string,
                            args: (step.arguments || {}) as Record<string, unknown>,
                            toolStatus: (step.status as string) || 'pending',
                            ts: (step.ts as number) || Date.now(),
                        });
                    }
                    if (step.type === 'tool_result') {
                        addMsg({
                            id: `tresult-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                            type: 'tool_result',
                            toolName: step.tool_name as string,
                            content: (step.result as string) || '',
                            executionTime: (step.execution_time as number) || 0,
                            ts: (step.ts as number) || Date.now(),
                        });
                    }
                });
            }
        } catch (err) {
            if (updateLoading) updateLoading(false);
            const e = err as { response?: { data?: { detail?: string } }; message?: string };
            addMsg({
                id: `err-${Date.now()}`,
                type: 'error',
                content: e.response?.data?.detail || e.message || 'Failed to reach agent',
                ts: Date.now(),
            });
        }
    };

    const handleCancel = async () => {
        if (!sessionId) return;
        try {
            await agentAPI.cancel(sessionId);
            setSessionId(null);
            if (updateLoading) updateLoading(false);
            if (addMsg) {
                addMsg({
                    id: `cancel-${Date.now()}`,
                    type: 'assistant',
                    content: '⏹️ Session cancelled.',
                    ts: Date.now(),
                });
            }
        } catch (err) {
            if (addMsg) {
                addMsg({
                    id: `cancel-err-${Date.now()}`,
                    type: 'error',
                    content: 'Failed to cancel session',
                    ts: Date.now(),
                });
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="odysseus-agent-chat">
            {/* ── Header ── */}
            <div className="odysseus-chat-header">
                <div className="odysseus-header-left">
                    <span className="odysseus-header-icon">🧠</span>
                    <span className="odysseus-header-title">Odysseus Agent</span>
                    {sessionId && (
                        <span className="odysseus-session-badge">
                            Session: {sessionId.slice(0, 8)}...
                        </span>
                    )}
                </div>
                <div className="odysseus-header-right">
                    {/* Mode Selector */}
                    <div className="odysseus-mode-selector">
                        <button
                            className="odysseus-mode-btn"
                            onClick={() => setModeOpen(!modeOpen)}
                        >
                            {MODES.find((m) => m.value === mode)?.label || mode}
                        </button>
                        {modeOpen && (
                            <div className="odysseus-mode-dropdown">
                                {MODES.map((m) => (
                                    <button
                                        key={m.value}
                                        className={`odysseus-mode-option ${m.value === mode ? 'active' : ''}`}
                                        onClick={() => { setMode(m.value); setModeOpen(false); }}
                                        title={m.desc}
                                    >
                                        {m.label}
                                        <span className="odysseus-mode-desc">{m.desc}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                    {/* Cancel */}
                    {sessionId && (
                        <button className="odysseus-cancel-btn" onClick={handleCancel}>
                            ⏹ Cancel
                        </button>
                    )}
                </div>
            </div>

            {/* ── Messages ── */}
            <div className="odysseus-chat-messages">
                {ctxMessages.length === 0 && (
                    <div className="odysseus-empty-chat">
                        <div className="odysseus-empty-icon">🧠</div>
                        <div className="odysseus-empty-text">Ask Asim anything to begin</div>
                        <div className="odysseus-empty-hint">
                            Mode: {MODES.find((m) => m.value === mode)?.desc || 'Full autonomy'}
                        </div>
                    </div>
                )}
                {ctxMessages.map((msg) => (
                    <MessageBubble key={(msg.id as string) || Math.random().toString()} msg={msg as AgentMsg} />
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* ── Input ── */}
            <div className="odysseus-chat-input">
                <textarea
                    ref={inputRef}
                    className="odysseus-input-field"
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    disabled={loading}
                />
                <button
                    className="odysseus-send-btn"
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                >
                    {loading ? '⏳' : '➤'}
                </button>
            </div>
        </div>
    );
}
