import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import asimAPI from '../services/asimAPI';

const FALLBACK_METRICS = {
  cpu: 45,
  memory: 62,
  network: 78,
  storage: 34,
};

const DashboardScreen = () => {
  const [metrics, setMetrics] = useState(null);
  const [worldOSStatus, setWorldOSStatus] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isNetworkError, setIsNetworkError] = useState(false);

  const loadDashboardData = useCallback(async () => {
    try {
      setError(null);

      // Get World OS status
      const worldOS = await asimAPI.getWorldOSStatus();
      if (worldOS && !worldOS.error) {
        setWorldOSStatus(worldOS);
        setIsNetworkError(false);

        if (worldOS.system_metrics) {
          setMetrics({
            cpu: worldOS.system_metrics.cpu_usage ?? FALLBACK_METRICS.cpu,
            memory: worldOS.system_metrics.memory_usage ?? FALLBACK_METRICS.memory,
            network: worldOS.system_metrics.network_usage ?? FALLBACK_METRICS.network,
            storage: worldOS.system_metrics.storage_usage ?? FALLBACK_METRICS.storage,
          });
        }
      } else {
        // API returned but with error — could be network or backend issue
        setIsNetworkError(true);
      }

      // Get analytics
      const analyticsData = await asimAPI.getAnalyticsOverview();
      if (analyticsData && !analyticsData.error) {
        setAnalytics(analyticsData);
      }

      setLoading(false);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setIsNetworkError(true);
      // Fallback to static data only on network error
      setMetrics(FALLBACK_METRICS);
      setError('Could not connect to backend. Showing fallback data.');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();

    const interval = setInterval(() => {
      loadDashboardData();
    }, 5000);

    return () => clearInterval(interval);
  }, [loadDashboardData]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#8884d8" />
        <Text style={styles.loadingText}>Connecting to ASIMNEXUS backend...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>ASIMNEXUS Dashboard</Text>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadDashboardData}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {worldOSStatus && !isNetworkError && (
        <View style={styles.statusCard}>
          <Text style={styles.statusLabel}>World OS Status</Text>
          <Text style={styles.statusValue}>{worldOSStatus.status || 'Active'}</Text>
        </View>
      )}

      <View style={styles.metricCard}>
        <Text style={styles.metricLabel}>CPU Usage</Text>
        <Text style={styles.metricValue}>{metrics ? metrics.cpu : FALLBACK_METRICS.cpu}%</Text>
      </View>

      <View style={styles.metricCard}>
        <Text style={styles.metricLabel}>Memory Usage</Text>
        <Text style={styles.metricValue}>{metrics ? metrics.memory : FALLBACK_METRICS.memory}%</Text>
      </View>

      <View style={styles.metricCard}>
        <Text style={styles.metricLabel}>Network</Text>
        <Text style={styles.metricValue}>{metrics ? metrics.network : FALLBACK_METRICS.network}%</Text>
      </View>

      <View style={styles.metricCard}>
        <Text style={styles.metricLabel}>Storage</Text>
        <Text style={styles.metricValue}>{metrics ? metrics.storage : FALLBACK_METRICS.storage}%</Text>
      </View>

      {analytics && (
        <View style={styles.analyticsCard}>
          <Text style={styles.analyticsTitle}>Analytics Overview</Text>
          <Text style={styles.analyticsText}>Total Requests: {analytics.total_requests || analytics.messages || 0}</Text>
          <Text style={styles.analyticsText}>Active Clones: {analytics.active_clones || 0}</Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#1a1a2e',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  errorBanner: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
    borderWidth: 1,
    padding: 16,
    borderRadius: 12,
    marginBottom: 15,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  errorText: {
    fontSize: 14,
    color: '#991b1b',
    flex: 1,
    marginRight: 10,
  },
  retryButton: {
    backgroundColor: '#dc2626',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  statusCard: {
    backgroundColor: '#8884d8',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusLabel: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 5,
  },
  statusValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  metricCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  metricLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  metricValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  analyticsCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  analyticsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#1a1a2e',
  },
  analyticsText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
});

export default DashboardScreen;
