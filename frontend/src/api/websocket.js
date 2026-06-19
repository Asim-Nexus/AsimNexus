/**
 * ASIMNEXUS WebSocket Integration
 * ================================
 * Delegates to WebSocketService.js (native WebSocket with exponential backoff).
 * Kept for backward compatibility — all new code should import from services/WebSocketService.js directly.
 *
 * @see ../services/WebSocketService.js for the full implementation
 */

import wsService from '../services/WebSocketService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE_URL.replace(/^http/, 'ws');

/**
 * Backward-compatible WebSocketManager that wraps WebSocketService.js.
 * Maintains the same API as the original implementation.
 */
class WebSocketManager {
  constructor() {
    this.connections = new Map();
    this.messageHandlers = new Map();
  }

  // Connect to WebSocket endpoint
  connect(endpoint, onMessage, onConnect = null, onDisconnect = null) {
    const wsUrl = `${WS_BASE}${endpoint}`;

    wsService.connect(wsUrl).then((connected) => {
      if (connected && onConnect) onConnect();
    });

    // Register message handler
    if (onMessage) {
      const unsub = wsService.on('message', onMessage);
      this.messageHandlers.set(endpoint, unsub);
    }

    // Register connect handler
    if (onConnect) {
      const unsub = wsService.on('connected', onConnect);
      this.messageHandlers.set(`connect:${endpoint}`, unsub);
    }

    // Register disconnect handler
    if (onDisconnect) {
      const unsub = wsService.on('disconnected', onDisconnect);
      this.messageHandlers.set(`disconnect:${endpoint}`, unsub);
    }

    this.connections.set(endpoint, { url: wsUrl, connected: false });
    return { close: () => this.disconnect(endpoint) };
  }

  // Disconnect specific endpoint
  disconnect(endpoint) {
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
    wsService.disconnect();
  }

  // Send message to specific endpoint
  send(endpoint, message) {
    wsService.send(endpoint, message);
    return true;
  }

  // Disconnect all connections
  disconnectAll() {
    this.messageHandlers.forEach((unsub) => {
      if (typeof unsub === 'function') unsub();
    });
    this.messageHandlers.clear();
    this.connections.clear();
    wsService.disconnect();
  }
}

// Singleton instance
export const wsManager = new WebSocketManager();

// ═══════════════════════════════════════════════════════════════════
// WEBSOCKET API ENDPOINTS
// ═══════════════════════════════════════════════════════════════════

export const websocketAPI = {
  // Connect to main chat WebSocket
  connectChat: (onMessage, onConnect, onDisconnect) =>
    wsManager.connect('/ws/chat', onMessage, onConnect, onDisconnect),

  // Connect to group chat (Founder Clones)
  connectGroupChat: (onMessage, onConnect, onDisconnect) =>
    wsManager.connect('/ws/group-chat', onMessage, onConnect, onDisconnect),

  // Connect to system metrics
  connectMetrics: (onMessage, onConnect, onDisconnect) =>
    wsManager.connect('/ws/metrics', onMessage, onConnect, onDisconnect),

  // Send chat message
  sendChatMessage: (message) =>
    wsManager.send('/ws/chat', { type: 'message', content: message }),

  // Disconnect all
  disconnectAll: () => wsManager.disconnectAll(),
};

export default wsManager;
