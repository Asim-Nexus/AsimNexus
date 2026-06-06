/**
 * ASIMNEXUS WebSocket Integration
 * Real-time communication with backend
 */

import { WS_BASE_URL } from './unified_api';

class WebSocketManager {
  constructor() {
    this.connections = new Map();
    this.messageHandlers = new Map();
    this.reconnectAttempts = 3;
    this.reconnectDelay = 1000;
  }

  // Connect to WebSocket endpoint
  connect(endpoint, onMessage, onConnect = null, onDisconnect = null) {
    const wsUrl = `${WS_BASE_URL}${endpoint}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`✅ WebSocket connected: ${endpoint}`);
        if (onConnect) onConnect();
        this.connections.set(endpoint, ws);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };
      
      ws.onclose = () => {
        console.log(`🔌 WebSocket disconnected: ${endpoint}`);
        this.connections.delete(endpoint);
        if (onDisconnect) onDisconnect();
      };
      
      ws.onerror = (error) => {
        console.error(`❌ WebSocket error on ${endpoint}:`, error);
      };
      
      return ws;
    } catch (error) {
      console.error(`Failed to connect WebSocket: ${endpoint}`, error);
      return null;
    }
  }

  // Disconnect specific endpoint
  disconnect(endpoint) {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close();
      this.connections.delete(endpoint);
    }
  }

  // Send message to specific endpoint
  send(endpoint, message) {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  // Disconnect all connections
  disconnectAll() {
    this.connections.forEach((ws, endpoint) => {
      ws.close();
    });
    this.connections.clear();
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
