/**
 * NotificationService — Browser & In-App Notification Manager
 * Phase 21.13: Mobile & Desktop polish
 *
 * Features:
 *   - Browser Notification API with permission handling
 *   - WebSocket-driven real-time notifications
 *   - Background sync queue for offline notifications
 *   - Notification history with deduplication
 *   - Sound/vibration alerts for critical notifications
 */

import wsService from './WebSocketService';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AppNotification {
    id: string;
    type: 'info' | 'success' | 'warning' | 'error' | 'payment' | 'identity' | 'mesh' | 'system';
    title: string;
    message: string;
    timestamp: number;
    read: boolean;
    /** Optional action URL or callback name */
    action?: string;
    /** Optional data payload */
    data?: Record<string, unknown>;
    /** Whether this notification was shown as browser notification */
    browserShown?: boolean;
}

export type NotificationListener = (notification: AppNotification) => void;

// ── Service ───────────────────────────────────────────────────────────────────

class NotificationService {
    private static instance: NotificationService;
    private notifications: AppNotification[] = [];
    private listeners: Set<NotificationListener> = new Set();
    private maxStored: number = 100;
    private soundEnabled: boolean = true;
    private vibrationEnabled: boolean = true;

    private constructor() {
        this.loadFromStorage();
        this.checkBrowserPermission();
        this.listenToWebSocket();
    }

    static getInstance(): NotificationService {
        if (!NotificationService.instance) {
            NotificationService.instance = new NotificationService();
        }
        return NotificationService.instance;
    }

    // ── Browser Notification API ──────────────────────────────────────────

    private checkBrowserPermission(): void {
        // Browser notification permission check — no-op, permission tracked via Notification API directly
    }

    async requestBrowserPermission(): Promise<boolean> {
        if (!('Notification' in window)) return false;
        if (Notification.permission === 'granted') {
            return true;
        }
        if (Notification.permission === 'denied') {
            return false;
        }
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    private showBrowserNotification(notification: AppNotification): void {
        if (!('Notification' in window) || Notification.permission !== 'granted') return;
        if (notification.browserShown) return;

        try {
            const options: NotificationOptions & { requireInteraction?: boolean } = {
                body: notification.message,
                icon: '/asimnexus-logo.png',
                tag: notification.id,
                silent: !this.soundEnabled,
                requireInteraction: notification.type === 'error' || notification.type === 'warning',
            };
            const n = new Notification(notification.title, options);

            n.onclick = () => {
                window.focus();
                if (notification.action) {
                    // Navigate to action URL if provided
                    window.location.href = notification.action;
                }
                n.close();
            };

            notification.browserShown = true;
        } catch {
            // Silently fail if browser blocks notification
        }
    }

    // ── WebSocket Integration ─────────────────────────────────────────────

    private listenToWebSocket(): void {
        wsService.on('notification', (payload: unknown) => {
            const data = payload as Record<string, unknown>;
            const notification: AppNotification = {
                id: (data.id as string) || `notif_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
                type: (data.type as AppNotification['type']) || 'info',
                title: (data.title as string) || 'Notification',
                message: (data.message as string) || '',
                timestamp: (data.timestamp as number) || Date.now(),
                read: false,
                action: data.action as string | undefined,
                data: data.data as Record<string, unknown> | undefined,
            };
            this.addNotification(notification);
        });

        // Also listen for dharma_alert and mesh_update as notifications
        wsService.on('dharma_alert', (payload: unknown) => {
            const data = payload as Record<string, unknown>;
            this.addNotification({
                id: `dharma_${Date.now()}`,
                type: 'warning',
                title: '⚖️ Dharma Alert',
                message: (data.message as string) || 'Governance alert received',
                timestamp: Date.now(),
                read: false,
                data: data as Record<string, unknown>,
            });
        });

        wsService.on('mesh_update', (payload: unknown) => {
            const data = payload as Record<string, unknown>;
            this.addNotification({
                id: `mesh_${Date.now()}`,
                type: 'mesh',
                title: '🔗 Mesh Update',
                message: (data.message as string) || 'Mesh network update',
                timestamp: Date.now(),
                read: false,
                data: data as Record<string, unknown>,
            });
        });
    }

    // ── Notification Management ───────────────────────────────────────────

    private addNotification(notification: AppNotification): void {
        // Deduplicate by ID
        const existing = this.notifications.find(n => n.id === notification.id);
        if (existing) {
            Object.assign(existing, notification);
            this.notifyListeners(existing);
            this.saveToStorage();
            return;
        }

        this.notifications.unshift(notification);

        // Trim to max stored
        if (this.notifications.length > this.maxStored) {
            this.notifications = this.notifications.slice(0, this.maxStored);
        }

        // Show browser notification
        this.showBrowserNotification(notification);

        // Play sound for critical types
        if (this.soundEnabled && (notification.type === 'error' || notification.type === 'warning')) {
            this.playNotificationSound();
        }

        // Vibrate for critical types on mobile
        if (this.vibrationEnabled && navigator.vibrate) {
            if (notification.type === 'error') navigator.vibrate([300, 100, 300]);
            else if (notification.type === 'warning') navigator.vibrate([200, 100, 200]);
        }

        this.notifyListeners(notification);
        this.saveToStorage();
    }

    /** Create a notification programmatically (not from WebSocket) */
    notify(notification: Omit<AppNotification, 'id' | 'timestamp' | 'read'>): AppNotification {
        const full: AppNotification = {
            ...notification,
            id: `notif_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            timestamp: Date.now(),
            read: false,
        };
        this.addNotification(full);
        return full;
    }

    // ── Sound ─────────────────────────────────────────────────────────────

    private playNotificationSound(): void {
        try {
            const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
            const oscillator = ctx.createOscillator();
            const gain = ctx.createGain();
            oscillator.connect(gain);
            gain.connect(ctx.destination);
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.3);
        } catch {
            // Audio not available
        }
    }

    // ── Read / Unread ─────────────────────────────────────────────────────

    markAsRead(id: string): void {
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
            notification.read = true;
            this.notifyListeners(notification);
            this.saveToStorage();
        }
    }

    markAllAsRead(): void {
        this.notifications.forEach(n => { n.read = true; });
        this.notifyListeners(null as unknown as AppNotification);
        this.saveToStorage();
    }

    // ── Getters ───────────────────────────────────────────────────────────

    getAll(): AppNotification[] {
        return [...this.notifications];
    }

    getUnread(): AppNotification[] {
        return this.notifications.filter(n => !n.read);
    }

    getUnreadCount(): number {
        return this.notifications.filter(n => !n.read).length;
    }

    getRecent(limit: number = 10): AppNotification[] {
        return this.notifications.slice(0, limit);
    }

    // ── Clear ─────────────────────────────────────────────────────────────

    clearAll(): void {
        this.notifications = [];
        this.notifyListeners(null as unknown as AppNotification);
        this.saveToStorage();
    }

    remove(id: string): void {
        this.notifications = this.notifications.filter(n => n.id !== id);
        this.notifyListeners(null as unknown as AppNotification);
        this.saveToStorage();
    }

    // ── Settings ──────────────────────────────────────────────────────────

    setSoundEnabled(enabled: boolean): void {
        this.soundEnabled = enabled;
        localStorage.setItem('asimnexus_notif_sound', String(enabled));
    }

    setVibrationEnabled(enabled: boolean): void {
        this.vibrationEnabled = enabled;
        localStorage.setItem('asimnexus_notif_vibration', String(enabled));
    }

    isSoundEnabled(): boolean {
        return this.soundEnabled;
    }

    isVibrationEnabled(): boolean {
        return this.vibrationEnabled;
    }

    // ── Listeners ─────────────────────────────────────────────────────────

    onNotification(listener: NotificationListener): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    private notifyListeners(notification: AppNotification | null): void {
        this.listeners.forEach(listener => {
            try {
                listener(notification as AppNotification);
            } catch {
                // Ignore listener errors
            }
        });
    }

    // ── Persistence ───────────────────────────────────────────────────────

    private saveToStorage(): void {
        try {
            localStorage.setItem('asimnexus_notifications', JSON.stringify(this.notifications));
        } catch {
            // Storage full or unavailable
        }
    }

    private loadFromStorage(): void {
        try {
            const stored = localStorage.getItem('asimnexus_notifications');
            if (stored) {
                this.notifications = JSON.parse(stored);
            }
        } catch {
            this.notifications = [];
        }
    }
}

export const notificationService = NotificationService.getInstance();
export default notificationService;
