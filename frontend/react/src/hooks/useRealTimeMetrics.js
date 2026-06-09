/**
 * ASIMNEXUS Real-Time Metrics Hook
 * =================================
 * Connects to backend WebSocket for real-time system metrics.
 * Uses WebSocketService.js (native WebSocket with exponential backoff reconnection).
 * Falls back to HTTP polling when WebSocket is unavailable.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import wsService from '../services/WebSocketService';
import { analyticsAPI } from '../api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
  const cleanupRef = useRef([]);

  const connectWebSocket = useCallback(() => {
    try {
      const wsUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/ws/metrics`;

      wsService.connect(wsUrl).then((connected) => {
        if (connected) {
          setIsConnected(true);
        }
      });

      // Register event listeners
      const unsubConnected = wsService.on('connected', () => {
        setIsConnected(true);
      });

      const unsubDisconnected = wsService.on('disconnected', () => {
        setIsConnected(false);
      });

      const unsubMetrics = wsService.on('metrics_update', (data) => {
        setMetrics(data);
        setLastUpdate(new Date());
      });

      const unsubError = wsService.on('error', () => {
        setIsConnected(false);
      });

      const unsubFallback = wsService.on('fallback', () => {
        setIsConnected(false);
      });

      cleanupRef.current = [unsubConnected, unsubDisconnected, unsubMetrics, unsubError, unsubFallback];
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }
  }, []);

  const disconnectWebSocket = useCallback(() => {
    // Clean up listeners
    cleanupRef.current.forEach((unsub) => {
      if (typeof unsub === 'function') unsub();
    });
    cleanupRef.current = [];

    wsService.disconnect();
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  // Fetch real metrics from backend via analyticsAPI (HTTP fallback)
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
