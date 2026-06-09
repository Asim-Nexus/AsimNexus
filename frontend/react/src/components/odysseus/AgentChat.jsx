/**
 * AgentChat.jsx
 * Enhanced chat component showing agent thinking, tool calls, and results within chat bubbles.
 *
 * Message types: user, assistant, thinking, tool_call, tool_result, error
 * Mode selector: AUTO / GUIDE / PLAN / OBSERVE
 * Integrates with ChatContext for message persistence.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChatContext } from '../../contexts/ChatContext';
import { agentAPI } from '../../api/odysseus';
import './odysseus.css';

const MODES = [
    { value: 'AUTO', label: '🤖 Auto', desc: 'Full autonomy' },
    { value: 'GUIDE', label: '🧭 Guide', desc: 'Suggest + confirm' },
    { value: 'PLAN', label: '📋 Plan', desc: 'Step-by-step' },
    { value: 'OBSERVE', label: '👁️ Observe', desc: 'Watch only' },
];

const SECURITY_COLORS = {
    dangerous: '#ef4444',
    sensitive: '#f59e0b',
    secure: '#10b981',
};

function formatTime(ts) {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function truncate(str, len = 200) {
    if (!str) return '';
    return str.length > len ? str.slice(0, len) + '...' : str;
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

function ToolCallBubble({ msg }) {
    const [expanded, setExpanded] = useState(false);
    const statusIcon = {
        pending: '⏳',
        running: '🔄',
        completed: '✅',
        failed: '❌',
    };
    const statusColor = {
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
                    style={{ color: statusColor[msg.toolStatus] || '#a0a0b0' }}
                >
                    {statusIcon[msg.toolStatus] || '⏳'} {msg.toolStatus || 'pending'}
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

function ToolResultBubble({ msg }) {
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

function ErrorBubble({ msg }) {
    return (
        <div className="odysseus-error-bubble">
            <span className="odysseus-error-icon">⚠️</span>
            <span>{msg.content || 'An error occurred'}</span>
        </div>
    );
}

function MessageBubble({ msg }) {
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
                    <span className="odysseus-msg-time">{formatTime(msg.ts)}</span>
                </div>
            );
        case 'assistant':
        default:
            return (
                <div className="odysseus-message odysseus-assistant-bubble">
                    <div className="odysseus-bubble-content">{msg.content}</div>
                    <span className="odysseus-msg-time">{formatTime(msg.ts)}</span>
                </div>
            );
    }
}

export default function AgentChat({ user, onCommand }) {
    const chatCtx = useChatContext();
    const messages = chatCtx?.messages || [];
    const addMessage = chatCtx?.addMessage || (() => { });
    const loading = chatCtx?.loading || false;
    const updateLoading = chatCtx?.updateLoading || (() => { });

    const [input, setInput] = useState('');
    const [mode, setMode] = useState('AUTO');
    const [sessionId, setSessionId] = useState(null);
    const [modeOpen, setModeOpen] = useState(false);
    const [sessions, setSessions] = useState([]);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    useEffect(() => {
        // Fetch active sessions on mount
        agentAPI.sessions()
            .then((res) => setSessions(res.data?.sessions || []))
            .catch(() => { });
    }, []);

    // Poll session status if we have an active session
    useEffect(() => {
        if (!sessionId) return;
        const interval = setInterval(async () => {
            try {
                const res = await agentAPI.status(sessionId);
                const data = res.data;
                if (data?.status === 'completed' || data?.status === 'cancelled' || data?.status === 'error') {
                    setSessionId(null);
                    updateLoading(false);
                    if (data.result) {
                        addMessage({
                            id: `result-${Date.now()}`,
                            type: 'assistant',
                            content: data.result,
                            ts: Date.now(),
                        });
                    }
                    clearInterval(interval);
                }
                if (data?.steps) {
                    data.steps.forEach((step) => {
                        if (step.type === 'tool_call' && !messages.find((m) => m.toolName === step.tool_name && m.ts === step.ts)) {
                            addMessage({
                                id: `tool-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                                type: 'tool_call',
                                toolName: step.tool_name,
                                args: step.arguments || {},
                                toolStatus: step.status || 'pending',
                                ts: step.ts || Date.now(),
                            });
                        }
                        if (step.type === 'tool_result' && !messages.find((m) => m.type === 'tool_result' && m.toolName === step.tool_name && m.ts === step.ts)) {
                            addMessage({
                                id: `result-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                                type: 'tool_result',
                                toolName: step.tool_name,
                                content: step.result || '',
                                executionTime: step.execution_time || 0,
                                ts: step.ts || Date.now(),
                            });
                        }
                    });
                }
            } catch {
                // Polling failed silently
            }
        }, 2000);
        return () => clearInterval(interval);
    }, [sessionId, updateLoading]);

    const handleSend = async () => {
        const text = input.trim();
        if (!text || loading) return;
        setInput('');

        addMessage({
            id: `user-${Date.now()}`,
            type: 'user',
            content: text,
            ts: Date.now(),
        });

        updateLoading(true);

        addMessage({
            id: `think-${Date.now()}`,
            type: 'thinking',
            ts: Date.now(),
        });

        try {
            const res = await agentAPI.run(text, mode);
            const data = res.data;

            if (data.session_id) {
                setSessionId(data.session_id);
            }

            if (data.result && !data.session_id) {
                // Non-streaming result
                addMessage({
                    id: `assistant-${Date.now()}`,
                    type: 'assistant',
                    content: data.result,
                    ts: Date.now(),
                });
                updateLoading(false);
            }

            if (data.steps) {
                data.steps.forEach((step) => {
                    if (step.type === 'tool_call') {
                        addMessage({
                            id: `tool-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                            type: 'tool_call',
                            toolName: step.tool_name,
                            args: step.arguments || {},
                            toolStatus: step.status || 'pending',
                            ts: step.ts || Date.now(),
                        });
                    }
                    if (step.type === 'tool_result') {
                        addMessage({
                            id: `tresult-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
                            type: 'tool_result',
                            toolName: step.tool_name,
                            content: step.result || '',
                            executionTime: step.execution_time || 0,
                            ts: step.ts || Date.now(),
                        });
                    }
                });
            }
        } catch (err) {
            updateLoading(false);
            addMessage({
                id: `err-${Date.now()}`,
                type: 'error',
                content: err.response?.data?.detail || err.message || 'Failed to reach agent',
                ts: Date.now(),
            });
        }
    };

    const handleCancel = async () => {
        if (!sessionId) return;
        try {
            await agentAPI.cancel(sessionId);
            setSessionId(null);
            updateLoading(false);
            addMessage({
                id: `cancel-${Date.now()}`,
                type: 'assistant',
                content: '⏹️ Session cancelled.',
                ts: Date.now(),
            });
        } catch (err) {
            addMessage({
                id: `cancel-err-${Date.now()}`,
                type: 'error',
                content: 'Failed to cancel session',
                ts: Date.now(),
            });
        }
    };

    const handleKeyDown = (e) => {
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
                {messages.length === 0 && (
                    <div className="odysseus-empty-chat">
                        <div className="odysseus-empty-icon">🧠</div>
                        <div className="odysseus-empty-text">Ask Asim anything to begin</div>
                        <div className="odysseus-empty-hint">
                            Mode: {MODES.find((m) => m.value === mode)?.desc || 'Full autonomy'}
                        </div>
                    </div>
                )}
                {messages.map((msg) => (
                    <MessageBubble key={msg.id || Math.random()} msg={msg} />
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
                    onChange={(e) => setInput(e.target.value)}
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
