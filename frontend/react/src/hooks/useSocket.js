/**
 * 🪝 ASIMNEXUS Socket Hook - Real-time Frontend Connectivity
 * Phase 1: WebSocket Integration with React
 * Real-time Frontend & Backend Sync - 100% WebSocket Support
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';
import { API_BASE_URL } from '../api/unified_api';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || API_BASE_URL || '';
const RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 1000;

export const useSocket = (userId, room = 'default') => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [roomUsers, setRoomUsers] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  // Connect to socket
  const connectSocket = useCallback(() => {
    if (socket && socket.connected) {
      console.log('🪝 Socket already connected');
      return;
    }

    console.log('🔌 Connecting to ASIMNEXUS Socket:', SOCKET_URL);
    
    const newSocket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      upgrade: false,
      rememberUpgrade: false,
      timeout: 20000,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: RECONNECT_ATTEMPTS,
      reconnectionDelay: RECONNECT_DELAY
    });

    newSocket.on('connect', () => {
      console.log('✅ Connected to ASIMNEXUS Socket');
      setConnected(true);
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
      
      // Join room
      newSocket.emit('join_room', {
        room: room,
        user_id: userId || 'anonymous'
      });
    });

    newSocket.on('disconnect', () => {
      console.log('❌ Disconnected from ASIMNEXUS Socket');
      setConnected(false);
      setConnectionStatus('disconnected');
      
      // Attempt reconnection
      if (reconnectAttemptsRef.current < RECONNECT_ATTEMPTS) {
        setTimeout(() => {
          reconnectAttemptsRef.current++;
          connectSocket();
        }, RECONNECT_DELAY);
      }
    });

    newSocket.on('connect_error', (error) => {
      console.error('🚨 Socket connection error:', error);
      setConnectionStatus('error');
    });

    // Room events
    newSocket.on('user_joined', (data) => {
      console.log('👋 User joined:', data);
      setRoomUsers(data.room_users || []);
    });

    newSocket.on('user_left', (data) => {
      console.log('👋 User left:', data);
      setRoomUsers(data.room_users || []);
    });

    // Message events
    newSocket.on('new_message', (data) => {
      console.log('💬 New message:', data);
      setMessages(prev => [...prev, data]);
    });

    newSocket.on('ai_response', (data) => {
      console.log('🤖 AI Response:', data);
      setMessages(prev => [...prev, data]);
    });

    // Private messages
    newSocket.on('private_message', (data) => {
      console.log('🔒 Private message:', data);
      setMessages(prev => [...prev, data]);
    });

    // System events
    newSocket.on('system_status', (status) => {
      console.log('📊 System status:', status);
    });

    newSocket.on('timeout', (data) => {
      console.log('⏰ Connection timeout:', data);
      setConnectionStatus('timeout');
    });

    setSocket(newSocket);
  }, [userId, room]);

  // Send message function
  const sendMessage = useCallback((message, isAI = false) => {
    if (!socket || !connected) {
      console.warn('🚨 Socket not connected');
      return false;
    }

    const messageData = {
      room: room,
      user_id: userId || 'anonymous',
      message: message,
      timestamp: new Date().toISOString()
    };

    if (isAI) {
      socket.emit('ai_response', messageData);
    } else {
      socket.emit('send_message', messageData);
    }

    console.log('📤 Message sent:', messageData);
    return true;
  }, [socket, connected, room, userId]);

  // Join/Leave room functions
  const joinRoom = useCallback((newRoom) => {
    if (socket && connected) {
      socket.emit('leave_room', { room: room, user_id: userId });
      socket.emit('join_room', { room: newRoom, user_id: userId });
    }
  }, [socket, connected, userId]);

  const leaveRoom = useCallback(() => {
    if (socket && connected) {
      socket.emit('leave_room', { room: room, user_id: userId });
    }
  }, [socket, connected, room, userId]);

  // Get connection status
  const getConnectionStatus = useCallback(() => {
    if (socket && connected) {
      socket.emit('get_status');
    }
  }, [socket, connected]);

  // Auto-connect on mount
  useEffect(() => {
    connectSocket();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  // Auto-reconnect when connection lost
  useEffect(() => {
    if (!connected && connectionStatus !== 'connecting') {
      const timer = setTimeout(() => {
        if (reconnectAttemptsRef.current < RECONNECT_ATTEMPTS) {
          connectSocket();
        }
      }, RECONNECT_DELAY * 2);
      
      return () => clearTimeout(timer);
    }
  }, [connected, connectionStatus]);

  return {
    socket,
    connected,
    messages,
    roomUsers,
    connectionStatus,
    sendMessage,
    joinRoom,
    leaveRoom,
    getConnectionStatus
  };
};

export default useSocket;
