import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import asimAPI from '../services/asimAPI';

const FALLBACK_EVENTS = [
  { type: 'AUTH', level: 'INFO', description: 'User authenticated successfully' },
  { type: 'PREVENTION', level: 'MEDIUM', description: 'Rate limit check passed' },
  { type: 'DETECTION', level: 'LOW', description: 'Anomaly detected' },
];

const SecurityScreen = () => {
  const [securityStatus, setSecurityStatus] = useState(null);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSecurityData = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await asimAPI.getSecurityStatus();
      if (data && !data.error) {
        setSecurityStatus(data);
        setSecurityEvents(data.events || []);
      } else {
        // Fallback to static data only on API error
        setSecurityEvents(FALLBACK_EVENTS);
        setError('Backend unavailable. Showing fallback data.');
      }
      setLoading(false);
    } catch (err) {
      console.error('Error loading security data:', err);
      setSecurityEvents(FALLBACK_EVENTS);
      setError('Could not connect to backend. Showing fallback data.');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSecurityData();
  }, [loadSecurityData]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#8884d8" />
        <Text style={styles.loadingText}>Loading Security Data...</Text>
      </View>
    );
  }

  const threatLevel = securityStatus?.threat_level || 'LOW';
  const blockedAttacks = securityStatus?.blocked_attacks || 0;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Security Dashboard</Text>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadSecurityData}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      <View style={styles.metricCard}>
        <Text style={styles.metricLabel}>Threat Level</Text>
        <Text style={[styles.metricValue, styles[threatLevel.toLowerCase() + 'Threat']]}>{threatLevel}</Text>
      </View>
      <View style={styles.metricCard}>
        <Text style={styles.metricLabel}>Blocked Attacks</Text>
        <Text style={styles.metricValue}>{blockedAttacks}</Text>
      </View>
      <Text style={styles.sectionTitle}>Recent Events</Text>
      {securityEvents.map((event, index) => (
        <View key={index} style={styles.eventCard}>
          <Text style={styles.eventType}>{event.type}</Text>
          <Text style={styles.eventLevel}>{event.level}</Text>
          <Text style={styles.eventDescription}>{event.description}</Text>
        </View>
      ))}
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
  metricCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
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
  lowThreat: {
    color: '#166534',
  },
  mediumThreat: {
    color: '#ca8a04',
  },
  highThreat: {
    color: '#dc2626',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 10,
    color: '#1a1a2e',
  },
  eventCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
  },
  eventType: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  eventLevel: {
    fontSize: 12,
    color: '#166534',
    marginTop: 5,
  },
  eventDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
});

export default SecurityScreen;
