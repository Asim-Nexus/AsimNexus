/**
 * NotificationToast — In-App Toast Notification
 * Phase 21.13: Mobile & Desktop polish
 *
 * Slides in from top-right, auto-dismisses after 5s.
 * Supports info, success, warning, error, payment, identity, mesh, system types.
 */
import { useState, useEffect, useCallback } from 'react';
import { AppNotification, notificationService } from '../../services/NotificationService';

// ── Type Colors ───────────────────────────────────────────────────────────────

const TYPE_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
    info: { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.4)', icon: 'ℹ️' },
    success: { bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.4)', icon: '✅' },
    warning: { bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.4)', icon: '⚠️' },
    error: { bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.4)', icon: '❌' },
    payment: { bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.4)', icon: '💳' },
    identity: { bg: 'rgba(139,92,246,0.15)', border: 'rgba(139,92,246,0.4)', icon: '🆔' },
    mesh: { bg: 'rgba(6,182,212,0.15)', border: 'rgba(6,182,212,0.4)', icon: '🔗' },
    system: { bg: 'rgba(148,163,184,0.15)', border: 'rgba(148,163,184,0.4)', icon: '⚙️' },
};

// ── Toast Item ────────────────────────────────────────────────────────────────

interface ToastItem extends AppNotification {
    dismissing?: boolean;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function NotificationToast() {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.map(t => t.id === id ? { ...t, dismissing: true } : t));
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 300);
    }, []);

    useEffect(() => {
        const unsub = notificationService.onNotification((notification) => {
            if (!notification) return;
            // Only show toast for new notifications (not read updates)
            const toast: ToastItem = { ...notification };
            setToasts(prev => {
                // Don't add duplicates
                if (prev.some(t => t.id === notification.id)) return prev;
                return [...prev, toast];
            });
            // Auto-dismiss after 5s
            setTimeout(() => removeToast(notification.id), 5000);
        });
        return unsub;
    }, [removeToast]);

    if (toasts.length === 0) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 16,
            right: 16,
            zIndex: 10000,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            maxWidth: 380,
            pointerEvents: 'none',
        }}>
            {toasts.map(toast => {
                const style = TYPE_STYLES[toast.type] || TYPE_STYLES.info;
                return (
                    <div
                        key={toast.id}
                        onClick={() => {
                            notificationService.markAsRead(toast.id);
                            removeToast(toast.id);
                        }}
                        style={{
                            pointerEvents: 'auto',
                            background: style.bg,
                            border: `1px solid ${style.border}`,
                            borderRadius: 12,
                            padding: '12px 16px',
                            backdropFilter: 'blur(12px)',
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            opacity: toast.dismissing ? 0 : 1,
                            transform: toast.dismissing ? 'translateX(100%)' : 'translateX(0)',
                            animation: 'slideInRight 0.3s ease',
                            boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
                        }}
                        onMouseEnter={e => {
                            (e.currentTarget as HTMLElement).style.transform = 'scale(1.02)';
                        }}
                        onMouseLeave={e => {
                            (e.currentTarget as HTMLElement).style.transform = 'scale(1)';
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                            <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{style.icon}</span>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                    fontWeight: 600,
                                    fontSize: '0.82rem',
                                    color: '#e2e8f0',
                                    marginBottom: 2,
                                }}>
                                    {toast.title}
                                </div>
                                <div style={{
                                    fontSize: '0.75rem',
                                    color: '#94a3b8',
                                    lineHeight: 1.4,
                                    wordBreak: 'break-word',
                                }}>
                                    {toast.message}
                                </div>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    removeToast(toast.id);
                                }}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: '#64748b',
                                    cursor: 'pointer',
                                    fontSize: '0.85rem',
                                    padding: 0,
                                    lineHeight: 1,
                                    flexShrink: 0,
                                }}
                            >
                                ✕
                            </button>
                        </div>
                    </div>
                );
            })}

            {/* Keyframes for slide-in animation */}
            <style>{`
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
}
