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

interface Metrics {
    cpu: number | null;
    memory: number | null;
    network: number | null;
    storage: number | null;
    activeFounders: number | null;
    activeAgents: number | null;
    tasksCompleted: number | null;
    ethicalScore: number | null;
}

interface UseRealTimeMetricsReturn {
    metrics: Metrics;
    isConnected: boolean;
    lastUpdate: Date | null;
    connectWebSocket: () => void;
    disconnectWebSocket: () => void;
}

export const useRealTimeMetrics = (): UseRealTimeMetricsReturn => {
    const [metrics, setMetrics] = useState<Metrics>({
        cpu: null,
        memory: null,
        network: null,
        storage: null,
        activeFounders: null,
        activeAgents: null,
        tasksCompleted: null,
        ethicalScore: null,
    });

    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const cleanupRef = useRef<Array<() => void>>([]);

    const connectWebSocket = useCallback(() => {
        try {
            const wsUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/ws/metrics`;

            wsService.connect(wsUrl).then((connected: boolean) => {
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

            const unsubMetrics = wsService.on('metrics_update', (data: unknown) => {
                setMetrics(data as Metrics);
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
            const data = res.data as unknown as Record<string, unknown>;
            setMetrics(prev => ({
                ...prev,
                cpu: (data.cpu_usage as number) ?? prev.cpu,
                memory: (data.ram_usage as number) ?? prev.memory,
                network: prev.network,
                storage: (data.disk_usage as number) ?? prev.storage,
                activeFounders: (data.founders_active as number) ?? prev.activeFounders,
                activeAgents: (data.agents_active as number) ?? prev.activeAgents,
                tasksCompleted: (data.tasks_completed as number) ?? prev.tasksCompleted,
                ethicalScore: (data.ethical_score as number) ?? prev.ethicalScore,
            }));
            setLastUpdate(new Date());
        } catch (_) { /* ignore polling errors */ }
    }, []);

    useEffect(() => {
        if (isConnected) return;
        fetchMetrics();
        const interval = setInterval(fetchMetrics, 10000);
        return () => clearInterval(interval);
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
