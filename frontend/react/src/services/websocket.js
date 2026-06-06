/**
 * WebSocket Service for Real-time Updates
 * Connects React frontend to ASIMNEXUS backend via WebSocket
 */

import io from 'socket.io-client';
import { API_BASE_URL } from '../api/unified_api';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || API_BASE_URL || '';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = {};
  }

  connect() {
    if (!this.socket) {
      this.socket = io(SOCKET_URL);
      
      this.socket.on('connect', () => {
        console.log('Connected to ASIMNEXUS WebSocket');
      });
      
      this.socket.on('disconnect', () => {
        console.log('Disconnected from ASIMNEXUS WebSocket');
      });
      
      this.socket.on('error', (error) => {
        console.error('WebSocket error:', error);
      });
    }
    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  emit(event, data) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  // Specific event listeners
  onFounderUpdate(callback) {
    this.on('founder-update', callback);
  }

  onAgentUpdate(callback) {
    this.on('agent-update', callback);
  }

  onSecurityEvent(callback) {
    this.on('security-event', callback);
  }

  onSystemMetrics(callback) {
    this.on('system-metrics', callback);
  }

  onVirtualRoomUpdate(callback) {
    this.on('virtual-room-update', callback);
  }

  onVRAvatarUpdate(callback) {
    this.on('vr-avatar-update', callback);
  }
}

export const wsService = new WebSocketService();
export default wsService;
