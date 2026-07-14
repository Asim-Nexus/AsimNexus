/**
 * WebSocketService.ts
 * Phase 3: Real-time AI streaming and messaging
 * Enhanced with exponential backoff reconnection, connection state tracking,
 * graceful fallback when backend WebSocket is unavailable, and multi-endpoint
 * management via WebSocketManager.
 *
 * This is the SINGLE canonical WebSocket service for AsimNexus.
 * All WebSocket functionality is consolidated here.
 *
 * Usage:
 *   import wsService from '../../services/WebSocketService';
 *   // or
 *   import { wsService, websocketAPI } from '../../api';
 */

type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error' | 'fallback';

type ListenerCallback = (data: unknown) => void;

interface ChatMessageOptions {
    userId?: string | number;
    mode?: string;
    context?: Record<string, unknown>;
}

interface AIStreamOptions {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    context?: Record<string, unknown>;
}

interface EndpointConnection {
    url: string;
    connected: boolean;
}

const WS_BASE: string = process.env.REACT_APP_WS_URL || (() => {
    if (typeof window !== 'undefined') {
        const proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        return `${proto}${window.location.host}`;
    }
    return 'ws://localhost:8000';
})();

class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts: number = 0;
    private readonly maxReconnectAttempts: number = 10;
    private readonly baseReconnectDelay: number = 1000;
    private readonly maxReconnectDelay: number = 30000;
    private listeners: Map<string, ListenerCallback[]> = new Map();
    private messageQueue: string[] = [];
    private isConnected: boolean = false;
    private connectionState: ConnectionState = 'disconnected';
    private url: string | null = null;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private _destroyed: boolean = false;
    private _connectPromise: Promise<boolean> | null = null;

    // Multi-endpoint management
    private connections: Map<string, EndpointConnection> = new Map();
    private messageHandlers: Map<string, () => void> = new Map();


    /**
     * Connect to the WebSocket backend.
     * @param url - WebSocket URL (default: WS_BASE + /ws/chat)
     * @returns resolves true if connected, false if fallback
     */
    connect(url: string = `${WS_BASE}/ws/chat`): Promise<boolean> {
        // If already connected or connecting to the same URL, return current state
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.isConnected = true;
            this.connectionState = 'connected';
            return Promise.resolve(true);
        }

        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            return this._connectPromise || Promise.resolve(false);
        }

        this.url = url;
        this.connectionState = 'connecting';
        this._destroyed = false;

        this._connectPromise = new Promise<boolean>((resolve) => {
            try {
                this.ws = new WebSocket(url);

                this.ws.onopen = () => {
                    if (this._destroyed) return;
                    console.log('[WebSocket] Connected to', url);
                    this.isConnected = true;
                    this.connectionState = 'connected';
                    this.reconnectAttempts = 0;
                    this.flushMessageQueue();
                    this.emit('connected', { url });
                    resolve(true);
                };

                this.ws.onmessage = (event: MessageEvent) => {
                    if (this._destroyed) return;
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (e) {
                        console.warn('[WebSocket] Invalid message format:', event.data);
                    }
                };

                this.ws.onclose = (event: CloseEvent) => {
                    if (this._destroyed) return;
                    const wasConnected = this.isConnected;
                    console.log(`[WebSocket] Disconnected (code: ${event.code})`);
                    this.isConnected = false;
                    this.connectionState = 'disconnected';
                    this.ws = null;
                    this.emit('disconnected', { code: event.code, wasConnected });

                    // Don't reconnect on auth failures or intentional close
                    if (event.code === 1000 || event.code === 1001 || event.code === 4001) {
                        console.log('[WebSocket] Clean close — no reconnection');
                        return;
                    }

                    // Schedule reconnection with exponential backoff
                    this.scheduleReconnect();
                };

                this.ws.onerror = (error: Event) => {
                    if (this._destroyed) return;
                    const target = error.target as WebSocket | null;
                    const msg = target?.url || 'Connection failed (backend may not support WebSocket)';
                    console.warn('[WebSocket] Error:', msg);
                    this.emit('error', { message: msg });
                    this.connectionState = 'error';

                    // Don't reject — just resolve false so UI falls back gracefully
                    resolve(false);
                };

            } catch (error: unknown) {
                const errMsg = error instanceof Error ? error.message : String(error);
                console.warn('[WebSocket] Init error:', errMsg);
                this.connectionState = 'error';
                this.isConnected = false;
                resolve(false);
            }
        });

        return this._connectPromise;
    }

    /**
     * Schedule reconnection with exponential backoff.
     * Starts at 1s, doubles each attempt up to 30s max.
     */
    private scheduleReconnect(): void {
        if (this._destroyed) return;
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn(`[WebSocket] Max reconnection attempts (${this.maxReconnectAttempts}) reached — falling back to HTTP mode`);
            this.connectionState = 'fallback';
            this.emit('fallback', { reason: 'max_retries_exceeded' });
            return;
        }

        // Clear any existing reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        this.reconnectAttempts++;
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s, 30s...
        const delay = Math.min(
            this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );
        // Add jitter: ±20% random variance
        const jitter = delay * (0.8 + Math.random() * 0.4);

        console.log(`[WebSocket] Reconnecting in ${Math.round(jitter)}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connectionState = 'connecting';

        this.reconnectTimer = setTimeout(() => {
            if (this._destroyed) return;
            if (this.url) {
                this.connect(this.url).catch(() => { /* ignore */ });
            }
        }, jitter);
    }

    private handleMessage(data: Record<string, unknown>): void {
        const { type, payload } = data;

        switch (type) {
            case 'ai_response':
                this.emit('ai_response', payload);
                break;
            case 'ai_stream':
                this.emit('ai_stream', payload);
                break;
            case 'context_update':
                this.emit('context_update', payload);
                break;
            case 'notification':
                this.emit('notification', payload);
                break;
            case 'agent_status':
                this.emit('agent_status', payload);
                break;
            case 'mesh_update':
                this.emit('mesh_update', payload);
                break;
            case 'dharma_alert':
                this.emit('dharma_alert', payload);
                break;
            default:
                this.emit(type as string, payload);
        }
    }

    send(type: string, payload: Record<string, unknown>): void {
        const message = JSON.stringify({ type, payload, timestamp: Date.now() });

        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        } else {
            // Queue for when connection is restored
            if (this.messageQueue.length < 100) {
                this.messageQueue.push(message);
            }
        }
    }

    private flushMessageQueue(): void {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (message && this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(message);
            } else {
                // Re-queue if connection dropped
                if (message) {
                    this.messageQueue.unshift(message);
                }
                break;
            }
        }
    }

    // Send chat message with streaming
    sendChatMessage(message: string, options: ChatMessageOptions = {}): void {
        this.send('chat_message', {
            text: message,
            user_id: options.userId,
            mode: options.mode || 'personal',
            stream: true,
            context: options.context,
        });
    }

    // Request AI streaming response
    requestAIStream(prompt: string, options: AIStreamOptions = {}): void {
        this.send('ai_stream_request', {
            prompt,
            model: options.model || 'local',
            temperature: options.temperature || 0.7,
            max_tokens: options.maxTokens || 1024,
            context: options.context,
        });
    }

    // Subscribe to events
    on(event: string, callback: ListenerCallback): () => void {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event)!.push(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(event);
            if (callbacks) {
                const index = callbacks.indexOf(callback);
                if (index > -1) callbacks.splice(index, 1);
            }
        };
    }

    private emit(event: string, data: unknown): void {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(cb => {
                try {
                    cb(data);
                } catch (err) {
                    console.warn('[WebSocket] Listener error:', err);
                }
            });
        }
    }

    /**
     * Get current connection state.
     * Returns: 'connected' | 'connecting' | 'disconnected' | 'error' | 'fallback'
     */
    getConnectionState(): ConnectionState {
        return this.connectionState;
    }

    /**
     * Check if WebSocket is connected.
     */
    isSocketConnected(): boolean {
        return this.isConnected;
    }

    /**
     * Reset reconnection counter (call after successful manual reconnect).
     */
    resetReconnectCounter(): void {
        this.reconnectAttempts = 0;
    }

    /**
     * Manually attempt to reconnect.
     */
    reconnect(): Promise<boolean> {
        this.reconnectAttempts = 0;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        this.disconnect();
        return this.connect(this.url || undefined);
    }

    disconnect(): void {
        this._destroyed = true;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            try {
                this.ws.close(1000, 'Client disconnect');
            } catch (e) {
                // Ignore close errors
            }
            this.ws = null;
        }
        this.isConnected = false;
        this.connectionState = 'disconnected';
        this.messageQueue = [];
    }

    // ═══════════════════════════════════════════════════════════════════
    // Multi-Endpoint Management (formerly in WebSocketManager)
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Connect to a specific WebSocket endpoint with callbacks.
     * Maintains a registry of connections and message handlers per endpoint.
     *
     * @param endpoint - WebSocket path (e.g., '/ws/chat')
     * @param onMessage - Message handler callback
     * @param onConnect - Connection established callback
     * @param onDisconnect - Disconnection callback
     * @returns Object with close() method
     */
    connectEndpoint(
        endpoint: string,
        onMessage: ((data: unknown) => void) | null,
        onConnect: ((data: unknown) => void) | null = null,
        onDisconnect: ((data: unknown) => void) | null = null
    ): { close: () => void } {
        const wsUrl = `${WS_BASE}${endpoint}`;

        const connectResult = this.connect(wsUrl);
        if (connectResult && typeof connectResult.then === 'function') {
            connectResult.then((connected) => {
                if (connected && onConnect) onConnect({ url: wsUrl });
            });
        } else if (onConnect) {
            onConnect({ url: wsUrl });
        }

        // Register message handler
        if (onMessage) {
            const unsub = this.on('message', onMessage);
            this.messageHandlers.set(endpoint, unsub);
        }

        // Register connect handler
        if (onConnect) {
            const unsub = this.on('connected', onConnect);
            this.messageHandlers.set(`connect:${endpoint}`, unsub);
        }

        // Register disconnect handler
        if (onDisconnect) {
            const unsub = this.on('disconnected', onDisconnect);
            this.messageHandlers.set(`disconnect:${endpoint}`, unsub);
        }

        this.connections.set(endpoint, { url: wsUrl, connected: false });
        return { close: () => this.disconnectEndpoint(endpoint) };
    }

    /**
     * Disconnect a specific endpoint and clean up its handlers.
     * @param endpoint - WebSocket path to disconnect
     */
    disconnectEndpoint(endpoint: string): void {
        // Clean up handlers
        const handlerKeys = [`connect:${endpoint}`, `disconnect:${endpoint}`, endpoint];
        handlerKeys.forEach((key) => {
            const unsub = this.messageHandlers.get(key);
            if (typeof unsub === 'function') {
                unsub();
                this.messageHandlers.delete(key);
            }
        });

        this.connections.delete(endpoint);
        this.disconnect();
    }

    /**
     * Disconnect all endpoints and clean up all handlers.
     */
    disconnectAllEndpoints(): void {
        this.messageHandlers.forEach((unsub) => {
            if (typeof unsub === 'function') unsub();
        });
        this.messageHandlers.clear();
        this.connections.clear();
        this.disconnect();
    }
}

// Singleton instance
const wsService = new WebSocketService();
export { wsService };

// ═══════════════════════════════════════════════════════════════════
// WEBSOCKET API ENDPOINTS (convenience helpers)
// ═══════════════════════════════════════════════════════════════════

export const websocketAPI = {
    // Connect to main chat WebSocket
    connectChat: (
        onMessage?: ((data: unknown) => void) | null,
        onConnect?: ((data: unknown) => void) | null,
        onDisconnect?: ((data: unknown) => void) | null
    ) => wsService.connectEndpoint('/ws/chat', onMessage || null, onConnect || null, onDisconnect || null),

    // Connect to group chat (Founder Clones)
    connectGroupChat: (
        onMessage?: ((data: unknown) => void) | null,
        onConnect?: ((data: unknown) => void) | null,
        onDisconnect?: ((data: unknown) => void) | null
    ) => wsService.connectEndpoint('/ws/group-chat', onMessage || null, onConnect || null, onDisconnect || null),

    // Connect to system metrics
    connectMetrics: (
        onMessage?: ((data: unknown) => void) | null,
        onConnect?: ((data: unknown) => void) | null,
        onDisconnect?: ((data: unknown) => void) | null
    ) => wsService.connectEndpoint('/ws/metrics', onMessage || null, onConnect || null, onDisconnect || null),

    // Send chat message
    sendChatMessage: (message: string) =>
        wsService.send('chat_message', { type: 'message', content: message }),

    // Disconnect all
    disconnectAll: () => wsService.disconnectAllEndpoints(),
};

export default wsService;
