import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import DashboardScreen from './screens/DashboardScreen';
import FoundersScreen from './screens/FoundersScreen';
import AgentsScreen from './screens/AgentsScreen';
import SecurityScreen from './screens/SecurityScreen';
import { API_BASE_URL } from './config';

const Tab = createBottomTabNavigator();

/**
 * Connection status indicator component
 * Pings the backend health endpoint periodically
 */
function ConnectionIndicator() {
  const [status, setStatus] = useState('checking');
  const intervalRef = useRef(null);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });
        if (response.ok) {
          setStatus('connected');
        } else {
          setStatus('error');
        }
      } catch {
        setStatus('disconnected');
      }
    };

    checkConnection();
    intervalRef.current = setInterval(checkConnection, 10000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const statusColors = {
    connected: '#4ade80',
    disconnected: '#ef4444',
    error: '#fbbf24',
    checking: '#9ca3af',
  };

  const statusLabels = {
    connected: 'Connected',
    disconnected: 'Disconnected',
    error: 'Error',
    checking: 'Checking...',
  };

  return (
    <View style={styles.connectionIndicator}>
      <View style={[styles.dot, { backgroundColor: statusColors[status] || '#9ca3af' }]} />
      <Text style={styles.connectionText}>{statusLabels[status] || 'Unknown'}</Text>
    </View>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <ConnectionIndicator />
        <Tab.Navigator
          screenOptions={{
            tabBarActiveTintColor: '#8884d8',
            tabBarInactiveTintColor: 'gray',
          }}
        >
          <Tab.Screen name="Dashboard" component={DashboardScreen} />
          <Tab.Screen name="Founders" component={FoundersScreen} />
          <Tab.Screen name="Agents" component={AgentsScreen} />
          <Tab.Screen name="Security" component={SecurityScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  connectionIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1a1a2e',
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  connectionText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
  },
});
