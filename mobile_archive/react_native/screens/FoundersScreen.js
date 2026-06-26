import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import asimAPI from '../services/asimAPI';

const FALLBACK_FOUNDERS = [
  { name: 'CEO Clone', role: 'CEO', status: 'active' },
  { name: 'CTO Clone', role: 'CTO', status: 'active' },
  { name: 'CFO Clone', role: 'CFO', status: 'active' },
  { name: 'COO Clone', role: 'COO', status: 'active' },
  { name: 'CPO Clone', role: 'CPO', status: 'idle' },
];

const FoundersScreen = () => {
  const [founders, setFounders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadFounders = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await asimAPI.getFounders();
      if (data && !data.error && data.founders) {
        setFounders(data.founders);
      } else {
        // Fallback to static data only on API error/network failure
        setFounders(FALLBACK_FOUNDERS);
        setError('Backend unavailable. Showing fallback data.');
      }
      setLoading(false);
    } catch (err) {
      console.error('Error loading founders:', err);
      setFounders(FALLBACK_FOUNDERS);
      setError('Could not connect to backend. Showing fallback data.');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFounders();
  }, [loadFounders]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#8884d8" />
        <Text style={styles.loadingText}>Loading Founder Clones...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Founder Clones</Text>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadFounders}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {founders.map((founder, index) => (
        <View key={index} style={[styles.card, founder.status === 'active' && styles.activeCard]}>
          <Text style={styles.name}>{founder.name}</Text>
          <Text style={styles.role}>{founder.role}</Text>
          <Text style={[styles.status, founder.status === 'active' && styles.activeStatus]}>
            {founder.status}
          </Text>
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
  card: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#8884d8',
  },
  activeCard: {
    borderLeftColor: '#4ade80',
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  role: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  status: {
    fontSize: 14,
    color: '#fbbf24',
    marginTop: 5,
  },
  activeStatus: {
    color: '#4ade80',
  },
});

export default FoundersScreen;
