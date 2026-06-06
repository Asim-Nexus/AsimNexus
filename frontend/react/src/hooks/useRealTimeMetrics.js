/**
 * ASIMNEXUS Real-Time Metrics Hook
 * Connects to backend WebSocket for real-time system metrics
 * Following 2026 best practices for real-time data
 * Uses corrected API modules from asimnexus.js
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
import { API_BASE_URL } from '../api/unified_api';
import { analyticsAPI } from '../api/asimnexus';

export const useRealTimeMetrics = () => {
  const [metrics, setMetrics] = useState({
    cpu: null,
    memory: null,
    network: null,
    storage: null,
    activeFounders: null,
    activeAgents: null,
    tasksCompleted: null,
    ethicalScore: null,
  });

  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const socketRef = useRef(null);

  const connectWebSocket = useCallback(() => {
    try {
      const socketBase = process.env.REACT_APP_SOCKET_URL || API_BASE_URL || '';
      socketRef.current = socketBase ? io(socketBase, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
      }) : io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
      });

      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      });

      socketRef.current.on('disconnect', () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      });

      socketRef.current.on('metrics_update', (data) => {
        setMetrics(data);
        setLastUpdate(new Date());
      });

      socketRef.current.on('error', (error) => {
        console.error('WebSocket error:', error);
      });
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }
  }, []);

  const disconnectWebSocket = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  // Fetch real metrics from backend via corrected analyticsAPI
  const fetchMetrics = useCallback(async () => {
    try {
      const res = await analyticsAPI.getOverview();
      const data = res.data;
      setMetrics(prev => ({
        ...prev,
        cpu: data.cpu_usage ?? prev.cpu,
        memory: data.ram_usage ?? prev.memory,
        network: prev.network,
        storage: data.disk_usage ?? prev.storage,
        activeFounders: data.founders_active ?? prev.activeFounders,
        activeAgents: data.agents_active ?? prev.activeAgents,
        tasksCompleted: data.tasks_completed ?? prev.tasksCompleted,
        ethicalScore: data.ethical_score ?? prev.ethicalScore,
      }));
      setLastUpdate(new Date());
    } catch (_) { }
  }, []);

  useEffect(() => {
    if (!isConnected) {
      fetchMetrics();
      const interval = setInterval(fetchMetrics, 10000);
      return () => clearInterval(interval);
    }
  }, [isConnected, fetchMetrics]);

  return {
    metrics,
    isConnected,
    lastUpdate,
    connectWebSocket,
    disconnectWebSocket,
  };
};

export default useRealTimeMetrics;
