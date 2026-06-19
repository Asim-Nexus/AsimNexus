/**
 * 📊 ASIMNEXUS Performance Utility
 * Phase 4: Mobile & Production Optimization
 * Frontend Performance Monitoring and Optimization
 */

import { useState, useEffect, useCallback } from 'react';

// Performance monitoring configuration
const PERFORMANCE_CONFIG = {
  metricsInterval: 30000,  // 30 seconds
  slowThreshold: 1000,    // 1 second
  memoryWarningThreshold: 85,  // 85%
  cpuWarningThreshold: 80,     // 80%
  maxRetries: 3
};

export const usePerformance = () => {
  const [metrics, setMetrics] = useState({
    renderTime: 0,
    componentLoadTime: 0,
    memoryUsage: 0,
    networkLatency: 0,
    errorCount: 0,
    lastUpdate: Date.now()
  });

  const [alerts, setAlerts] = useState([]);

  // Measure component render performance
  const measureRenderTime = useCallback((callback) => {
    const startTime = performance.now();
    
    return (...args) => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      setMetrics(prev => ({
        ...prev,
        renderTime: Math.max(prev.renderTime, renderTime)
      }));
      
      const result = callback(...args);
      
      // Log slow renders
      if (renderTime > PERFORMANCE_CONFIG.slowThreshold) {
        console.warn(`🐌 Slow render detected: ${renderTime.toFixed(2)}ms`);
        
        setAlerts(prev => [...prev, {
          type: 'performance',
          message: `Component rendering is slow (${renderTime.toFixed(2)}ms)`,
          timestamp: new Date(),
          severity: 'warning'
        }]);
      }
      
      return result;
    };
  }, []);

  // Monitor network performance
  const measureNetworkLatency = useCallback(async (url) => {
    const startTime = performance.now();
    
    try {
      const response = await fetch(url);
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      setMetrics(prev => ({
        ...prev,
        networkLatency: Math.max(prev.networkLatency, latency)
      }));
      
      if (latency > PERFORMANCE_CONFIG.slowThreshold) {
        console.warn(`🌐 High latency detected: ${latency.toFixed(2)}ms to ${url}`);
        
        setAlerts(prev => [...prev, {
          type: 'network',
          message: `High network latency (${latency.toFixed(2)}ms)`,
          timestamp: new Date(),
          severity: 'warning'
        }]);
      }
      
      return response;
    } catch (error) {
      setMetrics(prev => ({
        ...prev,
        errorCount: prev.errorCount + 1
      }));
      
      setAlerts(prev => [...prev, {
        type: 'error',
        message: `Network request failed: ${error.message}`,
        timestamp: new Date(),
        severity: 'error'
      }]);
      
      throw error;
    }
  }, []);

  // Check memory usage (approximate)
  const checkMemoryUsage = useCallback(() => {
    if (performance.memory) {
      const memoryInfo = performance.memory;
      const memoryUsageMB = memoryInfo.usedJSHeapSize / (1024 * 1024);
      
      setMetrics(prev => ({
        ...prev,
        memoryUsage: memoryUsageMB
      }));
      
      if (memoryUsageMB > PERFORMANCE_CONFIG.memoryWarningThreshold) {
        console.warn(`🧠 High memory usage: ${memoryUsageMB.toFixed(1)}MB`);
        
        setAlerts(prev => [...prev, {
          type: 'memory',
          message: `High memory usage (${memoryUsageMB.toFixed(1)}MB)`,
          timestamp: new Date(),
          severity: 'warning'
        }]);
      }
    }
  }, []);

  // Get performance score
  const getPerformanceScore = useCallback(() => {
    const { renderTime, memoryUsage, networkLatency, errorCount } = metrics;
    
    let score = 100;
    
    // Deduct points for issues
    if (renderTime > 100) score -= 20;        // Slow renders
    if (memoryUsage > 85) score -= 25;        // High memory
    if (networkLatency > 500) score -= 15;      // High latency
    if (errorCount > 0) score -= 30;           // Errors
    
    return Math.max(0, score);
  }, [metrics]);

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Auto-collect metrics
  useEffect(() => {
    const interval = setInterval(() => {
      checkMemoryUsage();
      
      setMetrics(prev => ({
        ...prev,
        lastUpdate: Date.now()
      }));
      
    }, PERFORMANCE_CONFIG.metricsInterval);

    // Cleanup
    return () => {
      clearInterval(interval);
    };
  }, []);

  // Responsive design utilities
  const useResponsive = () => {
    const [isMobile, setIsMobile] = useState(false);
    const [isTablet, setIsTablet] = useState(false);
    const [screenSize, setScreenSize] = useState({
      width: window.innerWidth,
      height: window.innerHeight
    });

    const checkDevice = useCallback(() => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      setScreenSize({ width, height });
      
      // Mobile detection
      setIsMobile(width <= 768);
      
      // Tablet detection
      setIsTablet(width > 768 && width <= 1024);
    }, []);

    useEffect(() => {
      checkDevice();
      
      const handleResize = () => checkDevice();
      window.addEventListener('resize', handleResize);
      
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }, []);

    return {
      metrics,
      alerts,
      measureRenderTime,
      measureNetworkLatency,
      clearAlerts,
      getPerformanceScore,
      isMobile,
      isTablet,
      screenSize,
      responsive: {
        isMobile: isMobile || screenSize.width <= 768,
        isTablet: isTablet || (screenSize.width > 768 && screenSize.width <= 1024),
        isDesktop: !isMobile && !isTablet
      }
    };
  };
};

export default usePerformance;
