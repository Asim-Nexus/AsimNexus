/**
 * 🪝 ASIMNEXUS Socket Hook - Real-time Frontend Connectivity
 * ==========================================================
 * Uses WebSocketService.js (native WebSocket with exponential backoff reconnection).
 * Provides room-based messaging, connection state tracking, and auto-reconnect.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import wsService from '../services/WebSocketService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE_URL.replace(/^http/, 'ws');

export const useSocket = (userId, room = 'default') => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [roomUsers, setRoomUsers] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const cleanupRef = useRef([]);
  const roomRef = useRef(room);
  const userIdRef = useRef(userId);

  // Keep refs in sync
  roomRef.current = room;
  userIdRef.current = userId;

  // Connect to WebSocket
  const connectSocket = useCallback(() => {
    if (wsService.isSocketConnected()) {
      setConnected(true);
      setConnectionStatus('connected');
      return;
    }

    setConnectionStatus('connecting');

    const wsUrl = `${WS_BASE}/ws/chat`;

    wsService.connect(wsUrl).then((isConnected) => {
      if (isConnected) {
        setConnected(true);
        setConnectionStatus('connected');

        // Join room
        wsService.send('join_room', {
          room: roomRef.current,
          user_id: userIdRef.current || 'anonymous',
        });
      }
    });

    // Register event listeners
    const unsubConnected = wsService.on('connected', () => {
      setConnected(true);
      setConnectionStatus('connected');
    });

    const unsubDisconnected = wsService.on('disconnected', () => {
      setConnected(false);
      setConnectionStatus('disconnected');
    });

    const unsubError = wsService.on('error', () => {
      setConnectionStatus('error');
    });

    const unsubFallback = wsService.on('fallback', () => {
      setConnected(false);
      setConnectionStatus('fallback');
    });

    // Room events
    const unsubUserJoined = wsService.on('user_joined', (data) => {
      setRoomUsers(data.room_users || []);
    });

    const unsubUserLeft = wsService.on('user_left', (data) => {
      setRoomUsers(data.room_users || []);
    });

    // Message events
    const unsubNewMessage = wsService.on('new_message', (data) => {
      setMessages(prev => [...prev, data]);
    });

    const unsubAIResponse = wsService.on('ai_response', (data) => {
      setMessages(prev => [...prev, data]);
    });

    // Private messages
    const unsubPrivateMessage = wsService.on('private_message', (data) => {
      setMessages(prev => [...prev, data]);
    });

    // System events
    const unsubSystemStatus = wsService.on('system_status', () => { });

    cleanupRef.current = [
      unsubConnected, unsubDisconnected, unsubError, unsubFallback,
      unsubUserJoined, unsubUserLeft,
      unsubNewMessage, unsubAIResponse, unsubPrivateMessage,
      unsubSystemStatus,
    ];
  }, []);

  // Send message function
  const sendMessage = useCallback((message, isAI = false) => {
    if (!wsService.isSocketConnected()) {
      console.warn('🚨 Socket not connected');
      return false;
    }

    const messageData = {
      room: roomRef.current,
      user_id: userIdRef.current || 'anonymous',
      message: message,
      timestamp: new Date().toISOString(),
    };

    if (isAI) {
      wsService.send('ai_response', messageData);
    } else {
      wsService.send('send_message', messageData);
    }

    return true;
  }, []);

  // Join/Leave room functions
  const joinRoom = useCallback((newRoom) => {
    if (wsService.isSocketConnected()) {
      wsService.send('leave_room', { room: roomRef.current, user_id: userIdRef.current });
      wsService.send('join_room', { room: newRoom, user_id: userIdRef.current });
      roomRef.current = newRoom;
    }
  }, []);

  const leaveRoom = useCallback(() => {
    if (wsService.isSocketConnected()) {
      wsService.send('leave_room', { room: roomRef.current, user_id: userIdRef.current });
    }
  }, []);

  // Get connection status
  const getConnectionStatus = useCallback(() => {
    return wsService.getConnectionState();
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connectSocket();

    // Cleanup on unmount
    return () => {
      cleanupRef.current.forEach((unsub) => {
        if (typeof unsub === 'function') unsub();
      });
      cleanupRef.current = [];
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    connected,
    messages,
    roomUsers,
    connectionStatus,
    sendMessage,
    joinRoom,
    leaveRoom,
    getConnectionStatus,
  };
};

export default useSocket;
