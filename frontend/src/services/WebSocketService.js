/**
 * WebSocketService.js
 * Phase 3: Real-time AI streaming and messaging
 * Enhanced with exponential backoff reconnection, connection state tracking,
 * and graceful fallback when backend WebSocket is unavailable.
 */

const WS_BASE = process.env.REACT_APP_WS_URL || (() => {
  if (typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    return `${proto}${window.location.host}`;
  }
  return 'ws://localhost:8000';
})();

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.baseReconnectDelay = 1000;   // 1 second
    this.maxReconnectDelay = 30000;   // 30 seconds
    this.listeners = new Map();
    this.messageQueue = [];
    this.isConnected = false;
    this.connectionState = 'disconnected'; // 'connected' | 'connecting' | 'disconnected' | 'error' | 'fallback'
    this.url = null;
    this.reconnectTimer = null;
    this._destroyed = false;
    this._connectPromise = null;
  }

  /**
   * Connect to the WebSocket backend.
   * @param {string} url - WebSocket URL (default: WS_BASE + /ws/chat)
   * @returns {Promise<boolean>} - resolves true if connected, false if fallback
   */
  connect(url = `${WS_BASE}/ws/chat`) {
    // If already connected or connecting to the same URL, return current state
    if (this.ws && (this.ws.readyState === WebSocket.OPEN)) {
      this.isConnected = true;
      this.connectionState = 'connected';
      return Promise.resolve(true);
    }

    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING)) {
      return this._connectPromise || Promise.resolve(false);
    }

    this.url = url;
    this.connectionState = 'connecting';
    this._destroyed = false;

    this._connectPromise = new Promise((resolve) => {
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

        this.ws.onmessage = (event) => {
          if (this._destroyed) return;
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (e) {
            console.warn('[WebSocket] Invalid message format:', event.data);
          }
        };

        this.ws.onclose = (event) => {
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

        this.ws.onerror = (error) => {
          if (this._destroyed) return;
          const msg = error?.message || error?.type || 'Connection failed (backend may not support WebSocket)';
          console.warn('[WebSocket] Error:', msg);
          this.emit('error', { message: msg });
          this.connectionState = 'error';

          // Don't reject — just resolve false so UI falls back gracefully
          resolve(false);
        };

      } catch (error) {
        console.warn('[WebSocket] Init error:', error.message);
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
  scheduleReconnect() {
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
      this.connect(this.url).catch(() => { });
    }, jitter);
  }

  handleMessage(data) {
    const { type, payload } = data;

    switch (type) {
      case 'ai_response':
        this.emit('ai_response', payload);
        break;
      case 'ai_stream':
        this.emit('ai_stream', payload); // Streaming chunks
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
        this.emit(type, payload);
    }
  }

  send(type, payload) {
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

  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(message);
      } else {
        // Re-queue if connection dropped
        this.messageQueue.unshift(message);
        break;
      }
    }
  }

  // Send chat message with streaming
  sendChatMessage(message, options = {}) {
    this.send('chat_message', {
      text: message,
      user_id: options.userId,
      mode: options.mode || 'personal',
      stream: true,
      context: options.context,
    });
  }

  // Request AI streaming response
  requestAIStream(prompt, options = {}) {
    this.send('ai_stream_request', {
      prompt,
      model: options.model || 'local',
      temperature: options.temperature || 0.7,
      max_tokens: options.maxTokens || 1024,
      context: options.context,
    });
  }

  // Subscribe to events
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) callbacks.splice(index, 1);
      }
    };
  }

  emit(event, data) {
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
  getConnectionState() {
    return this.connectionState;
  }

  /**
   * Check if WebSocket is connected.
   */
  isSocketConnected() {
    return this.isConnected;
  }

  /**
   * Reset reconnection counter (call after successful manual reconnect).
   */
  resetReconnectCounter() {
    this.reconnectAttempts = 0;
  }

  /**
   * Manually attempt to reconnect.
   */
  reconnect() {
    this.reconnectAttempts = 0;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.disconnect();
    return this.connect(this.url);
  }

  disconnect() {
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
}

const wsService = new WebSocketService();
export default wsService;
