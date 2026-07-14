/**
 * SystemTray — Notification Center Panel
 * Phase 21.13: Mobile & Desktop polish
 *
 * Shows all notifications with read/unread state, filtering by type,
 * mark as read, clear all, and notification settings.
 * Integrates with NotificationService for browser notifications.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { AppNotification, notificationService } from '../../services/NotificationService';

// ── Type Colors ───────────────────────────────────────────────────────────────

const TYPE_META: Record<string, { color: string; bg: string; icon: string }> = {
    info: { color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', icon: 'ℹ️' },
    success: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '✅' },
    warning: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '⚠️' },
    error: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '❌' },
    payment: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '💳' },
    identity: { color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)', icon: '🆔' },
    mesh: { color: '#06b6d4', bg: 'rgba(6,182,212,0.12)', icon: '🔗' },
    system: { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', icon: '⚙️' },
};

// ── Styles ────────────────────────────────────────────────────────────────────

const PANEL: React.CSSProperties = {
    position: 'fixed',
    top: 60,
    right: 16,
    width: 400,
    maxHeight: 'calc(100vh - 100px)',
    background: 'rgba(15,23,42,0.95)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 16,
    backdropFilter: 'blur(20px)',
    boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
};

const HEADER: React.CSSProperties = {
    padding: '16px 20px',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
};

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 10,
    border: '1px solid rgba(255,255,255,0.06)',
    padding: '12px 14px',
    cursor: 'pointer',
    transition: 'all 0.15s',
};

const BTN_SMALL: React.CSSProperties = {
    background: 'rgba(255,255,255,0.08)',
    border: 'none',
    borderRadius: 6,
    color: '#94a3b8',
    cursor: 'pointer',
    fontSize: '0.72rem',
    fontWeight: 600,
    padding: '4px 10px',
};

// ── Component ─────────────────────────────────────────────────────────────────

interface SystemTrayProps {
    onClose: () => void;
}

export default function SystemTray({ onClose }: SystemTrayProps) {
    const [notifications, setNotifications] = useState<AppNotification[]>([]);
    const [filter, setFilter] = useState<string>('all');
    const [showSettings, setShowSettings] = useState(false);
    const [browserPermission, setBrowserPermission] = useState<NotificationPermission>(
        'Notification' in window ? Notification.permission : 'denied'
    );

    const refresh = useCallback(() => {
        setNotifications(notificationService.getAll());
    }, []);

    useEffect(() => {
        refresh();
        const unsub = notificationService.onNotification(() => refresh());
        return unsub;
    }, [refresh]);

    const filtered = filter === 'all'
        ? notifications
        : notifications.filter(n => n.type === filter);

    const unreadCount = notificationService.getUnreadCount();

    const handleRequestPermission = async () => {
        const granted = await notificationService.requestBrowserPermission();
        setBrowserPermission(granted ? 'granted' : 'denied');
    };

    const formatTime = (ts: number): string => {
        const d = new Date(ts);
        const now = new Date();
        const diff = now.getTime() - d.getTime();
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return d.toLocaleDateString();
    };

    return (
        <div style={PANEL}>
            {/* Header */}
            <div style={HEADER}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '1.1rem' }}>🔔</span>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#e2e8f0' }}>
                        Notifications
                    </span>
                    {unreadCount > 0 && (
                        <span style={{
                            background: '#8b5cf6',
                            borderRadius: 10,
                            padding: '1px 7px',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            color: '#fff',
                        }}>
                            {unreadCount}
                        </span>
                    )}
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                    <button
                        onClick={() => { notificationService.markAllAsRead(); refresh(); }}
                        style={BTN_SMALL}
                        title="Mark all as read"
                    >
                        ✓ All
                    </button>
                    <button
                        onClick={() => { notificationService.clearAll(); refresh(); }}
                        style={{ ...BTN_SMALL, color: '#ef4444' }}
                        title="Clear all"
                    >
                        ✕ All
                    </button>
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        style={BTN_SMALL}
                        title="Settings"
                    >
                        ⚙️
                    </button>
                    <button
                        onClick={onClose}
                        style={{ ...BTN_SMALL, fontSize: '0.85rem' }}
                        title="Close"
                    >
                        ✕
                    </button>
                </div>
            </div>

            {/* Settings Panel */}
            {showSettings && (
                <div style={{
                    padding: '12px 20px',
                    borderBottom: '1px solid rgba(255,255,255,0.08)',
                    background: 'rgba(139,92,246,0.05)',
                }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#94a3b8', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        Notification Settings
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#cbd5e1', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={notificationService.isSoundEnabled()}
                                onChange={e => notificationService.setSoundEnabled(e.target.checked)}
                                style={{ accentColor: '#8b5cf6' }}
                            />
                            Sound alerts
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#cbd5e1', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={notificationService.isVibrationEnabled()}
                                onChange={e => notificationService.setVibrationEnabled(e.target.checked)}
                                style={{ accentColor: '#8b5cf6' }}
                            />
                            Vibration (mobile)
                        </label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#cbd5e1' }}>
                            <span>🔔 Browser notifications:</span>
                            {browserPermission === 'granted' ? (
                                <span style={{ color: '#10b981' }}>Enabled ✓</span>
                            ) : (
                                <button
                                    onClick={handleRequestPermission}
                                    style={{
                                        background: '#8b5cf6',
                                        border: 'none',
                                        borderRadius: 6,
                                        color: '#fff',
                                        cursor: 'pointer',
                                        fontSize: '0.72rem',
                                        fontWeight: 600,
                                        padding: '3px 10px',
                                    }}
                                >
                                    {browserPermission === 'denied' ? 'Blocked' : 'Enable'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Filter Tabs */}
            <div style={{
                padding: '10px 20px',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                display: 'flex',
                gap: 6,
                flexWrap: 'wrap',
            }}>
                {['all', 'info', 'success', 'warning', 'error', 'payment', 'identity', 'mesh', 'system'].map(type => (
                    <button
                        key={type}
                        onClick={() => setFilter(type)}
                        style={{
                            background: filter === type ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.05)',
                            border: `1px solid ${filter === type ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.08)'}`,
                            borderRadius: 6,
                            color: filter === type ? '#a78bfa' : '#94a3b8',
                            cursor: 'pointer',
                            fontSize: '0.68rem',
                            fontWeight: 600,
                            padding: '3px 8px',
                            textTransform: 'capitalize',
                            transition: 'all 0.15s',
                        }}
                    >
                        {type === 'all' ? 'All' : `${TYPE_META[type]?.icon || ''} ${type}`}
                    </button>
                ))}
            </div>

            {/* Notification List */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: 12,
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
            }}>
                {filtered.length === 0 ? (
                    <div style={{
                        textAlign: 'center',
                        padding: 40,
                        color: '#64748b',
                        fontSize: '0.82rem',
                    }}>
                        <div style={{ fontSize: '2rem', marginBottom: 8 }}>🔔</div>
                        No notifications
                    </div>
                ) : (
                    filtered.map(n => {
                        const meta = TYPE_META[n.type] || TYPE_META.info;
                        return (
                            <div
                                key={n.id}
                                onClick={() => {
                                    notificationService.markAsRead(n.id);
                                    refresh();
                                }}
                                style={{
                                    ...CARD,
                                    opacity: n.read ? 0.6 : 1,
                                    borderLeft: `3px solid ${n.read ? 'transparent' : meta.color}`,
                                }}
                                onMouseEnter={e => {
                                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.07)';
                                }}
                                onMouseLeave={e => {
                                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)';
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                                    <span style={{ fontSize: '1rem', flexShrink: 0 }}>{meta.icon}</span>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            marginBottom: 2,
                                        }}>
                                            <span style={{
                                                fontWeight: 600,
                                                fontSize: '0.8rem',
                                                color: n.read ? '#94a3b8' : '#e2e8f0',
                                            }}>
                                                {n.title}
                                            </span>
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', flexShrink: 0 }}>
                                                {formatTime(n.timestamp)}
                                            </span>
                                        </div>
                                        <div style={{
                                            fontSize: '0.73rem',
                                            color: '#94a3b8',
                                            lineHeight: 1.4,
                                            wordBreak: 'break-word',
                                        }}>
                                            {n.message}
                                        </div>
                                    </div>
                                    {!n.read && (
                                        <span style={{
                                            width: 8,
                                            height: 8,
                                            borderRadius: '50%',
                                            background: meta.color,
                                            flexShrink: 0,
                                            marginTop: 4,
                                        }} />
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Footer */}
            <div style={{
                padding: '10px 20px',
                borderTop: '1px solid rgba(255,255,255,0.06)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.68rem',
                color: '#64748b',
            }}>
                <span>{filtered.length} notification{filtered.length !== 1 ? 's' : ''}</span>
                <span>{unreadCount} unread</span>
            </div>
        </div>
    );
}
