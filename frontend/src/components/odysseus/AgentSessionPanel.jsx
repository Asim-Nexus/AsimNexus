/**
 * AgentSessionPanel.jsx
 * Sidebar/drawer panel showing active agent sessions.
 *
 * Lists active sessions with ID, mode badge, step count, duration, status.
 * Click to expand, cancel button per session, empty state.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { agentAPI } from '../../api/odysseus';
import './odysseus.css';

const MODE_COLORS = {
    AUTO: '#667eea',
    GUIDE: '#10b981',
    PLAN: '#f59e0b',
    OBSERVE: '#8b5cf6',
};

const STATUS_COLORS = {
    running: '#3b82f6',
    pending: '#f59e0b',
    completed: '#10b981',
    cancelled: '#6b7280',
    error: '#ef4444',
};

function formatDuration(startTs) {
    const elapsed = Date.now() - new Date(startTs).getTime();
    const secs = Math.floor(elapsed / 1000);
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    const remSecs = secs % 60;
    return `${mins}m ${remSecs}s`;
}

function SessionCard({ session, onCancel, onSelect, selected }) {
    const [duration, setDuration] = useState(
        session.start_time ? formatDuration(session.start_time) : '—'
    );

    useEffect(() => {
        if (session.status === 'running' && session.start_time) {
            const interval = setInterval(() => {
                setDuration(formatDuration(session.start_time));
            }, 10000);
            return () => clearInterval(interval);
        }
    }, [session.status, session.start_time]);

    const modeColor = MODE_COLORS[session.mode] || '#667eea';
    const statusColor = STATUS_COLORS[session.status] || '#6b7280';

    return (
        <div
            className={`odysseus-session-card ${selected ? 'selected' : ''} ${session.status === 'running' ? 'running' : ''
                }`}
            onClick={() => onSelect(session.session_id)}
        >
            {/* Header */}
            <div className="odysseus-session-header">
                <span className="odysseus-session-id">
                    {session.session_id ? session.session_id.slice(0, 10) + '...' : 'N/A'}
                </span>
                <span
                    className="odysseus-mode-badge"
                    style={{ background: `${modeColor}22`, color: modeColor, borderColor: `${modeColor}44` }}
                >
                    {session.mode || 'AUTO'}
                </span>
            </div>

            {/* Meta */}
            <div className="odysseus-session-meta">
                <span className="odysseus-session-stat">
                    👣 {session.step_count || 0} steps
                </span>
                <span className="odysseus-session-stat">⏱ {duration}</span>
                <span
                    className="odysseus-session-status"
                    style={{ color: statusColor }}
                >
                    ● {session.status || 'unknown'}
                </span>
            </div>

            {/* Expanded detail */}
            {selected && (
                <div className="odysseus-session-detail">
                    <div className="odysseus-session-detail-row">
                        <span className="odysseus-detail-label">Session ID</span>
                        <code className="odysseus-detail-value">{session.session_id}</code>
                    </div>
                    {session.user_input && (
                        <div className="odysseus-session-detail-row">
                            <span className="odysseus-detail-label">Input</span>
                            <span className="odysseus-detail-value">
                                {session.user_input.slice(0, 100)}
                                {session.user_input.length > 100 ? '...' : ''}
                            </span>
                        </div>
                    )}
                    {session.result && (
                        <div className="odysseus-session-detail-row">
                            <span className="odysseus-detail-label">Result</span>
                            <span className="odysseus-detail-value">
                                {session.result.slice(0, 120)}
                                {session.result.length > 120 ? '...' : ''}
                            </span>
                        </div>
                    )}
                    {session.steps && session.steps.length > 0 && (
                        <div className="odysseus-session-detail-row">
                            <span className="odysseus-detail-label">Steps</span>
                            <div className="odysseus-steps-list">
                                {session.steps.slice(0, 8).map((step, i) => (
                                    <div key={i} className="odysseus-step-item">
                                        {step.type === 'tool_call' ? '🔧' : '💬'} {step.tool_name || step.content?.slice(0, 40)}
                                    </div>
                                ))}
                                {session.steps.length > 8 && (
                                    <div className="odysseus-step-item more">
                                        +{session.steps.length - 8} more steps
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Cancel button */}
                    {(session.status === 'running' || session.status === 'pending') && (
                        <button
                            className="odysseus-session-cancel-btn"
                            onClick={(e) => {
                                e.stopPropagation();
                                onCancel(session.session_id);
                            }}
                        >
                            ⏹ Cancel Session
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

export default function AgentSessionPanel({ user }) {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedId, setSelectedId] = useState(null);
    const [stats, setStats] = useState(null);

    const fetchSessions = useCallback(async () => {
        setLoading(true);
        try {
            const [sessionsRes, statsRes] = await Promise.all([
                agentAPI.sessions(),
                agentAPI.stats(),
            ]);
            setSessions(sessionsRes.data?.sessions || []);
            setStats(statsRes.data || null);
            setError(null);
        } catch (err) {
            setSessions([]);
            setError('Failed to fetch agent sessions');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSessions();
        const interval = setInterval(fetchSessions, 15000);
        return () => clearInterval(interval);
    }, [fetchSessions]);

    const handleCancel = useCallback(async (sessionId) => {
        try {
            await agentAPI.cancel(sessionId);
            setSessions((prev) =>
                prev.map((s) =>
                    s.session_id === sessionId ? { ...s, status: 'cancelled' } : s
                )
            );
        } catch {
            // Silently handle
        }
    }, []);

    const handleSelect = useCallback((sessionId) => {
        setSelectedId((prev) => (prev === sessionId ? null : sessionId));
    }, []);

    if (loading && sessions.length === 0) {
        return (
            <div className="odysseus-loading-container">
                <div className="odysseus-loading-spinner" />
                <span>Loading sessions...</span>
            </div>
        );
    }

    return (
        <div className="odysseus-session-panel">
            {/* Header */}
            <div className="odysseus-panel-header">
                <h3 className="odysseus-panel-title">🔄 Agent Sessions</h3>
                <button className="odysseus-refresh-btn" onClick={fetchSessions}>
                    ↻ Refresh
                </button>
            </div>

            {/* Stats bar */}
            {stats && (
                <div className="odysseus-stats-bar">
                    <span className="odysseus-stat-item">
                        🟢 {stats.active || 0} active
                    </span>
                    <span className="odysseus-stat-item">
                        ✅ {stats.completed || 0} completed
                    </span>
                    <span className="odysseus-stat-item">
                        ⏱ {stats.avg_duration || '—'} avg
                    </span>
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="odysseus-error-banner">
                    ⚠️ {error}
                    <button className="odysseus-retry-btn" onClick={fetchSessions}>
                        Retry
                    </button>
                </div>
            )}

            {/* Session list */}
            <div className="odysseus-sessions-list">
                {sessions.length === 0 ? (
                    <div className="odysseus-empty-state">
                        <div className="odysseus-empty-icon">🔄</div>
                        <div className="odysseus-empty-text">No active agent sessions</div>
                        <div className="odysseus-empty-hint">
                            Start a conversation in the Agent Chat to create a session
                        </div>
                    </div>
                ) : (
                    sessions.map((session) => (
                        <SessionCard
                            key={session.session_id}
                            session={session}
                            onCancel={handleCancel}
                            onSelect={handleSelect}
                            selected={selectedId === session.session_id}
                        />
                    ))
                )}
            </div>
        </div>
    );
}
