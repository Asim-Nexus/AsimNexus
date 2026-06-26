import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import asimAPI from '../services/asimAPI';

const FALLBACK_AGENTS = [
  { name: 'Coding Agent', type: 'CODING', status: 'active' },
  { name: 'Marketing Agent', type: 'MARKETING', status: 'active' },
  { name: 'Support Agent', type: 'SUPPORT', status: 'active' },
  { name: 'Research Agent', type: 'RESEARCH', status: 'idle' },
  { name: 'Data Analysis Agent', type: 'DATA_ANALYSIS', status: 'active' },
];

const AgentsScreen = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAgents = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await asimAPI.getAgents();
      if (data && !data.error && data.agents) {
        setAgents(data.agents);
      } else {
        setAgents(FALLBACK_AGENTS);
        setError('Backend unavailable. Showing fallback data.');
      }
      setLoading(false);
    } catch (err) {
      console.error('Error loading agents:', err);
      setAgents(FALLBACK_AGENTS);
      setError('Could not connect to backend. Showing fallback data.');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#8884d8" />
        <Text style={styles.loadingText}>Loading Worker Agents...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Worker Agents</Text>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadAgents}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {agents.map((agent, index) => (
        <View key={index} style={[styles.card, agent.status === 'active' && styles.activeCard]}>
          <Text style={styles.name}>{agent.name}</Text>
          <Text style={styles.type}>{agent.type}</Text>
          <Text style={[styles.status, agent.status === 'active' && styles.activeStatus]}>
            {agent.status}
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
  type: {
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

export default AgentsScreen;
