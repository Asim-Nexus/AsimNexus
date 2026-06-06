/**
 * ASIMNEXUS Universal Interface
 * ============================
 * Cross-Platform Digital Workforce Dashboard
 * Works on Web, Desktop (Electron), and Mobile (React Native)
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Platform, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Import components
import NeuralHeartbeat from './components/NeuralHeartbeat';
import AgentWorkforce from './components/AgentWorkforce';
import SystemControl from './components/SystemControl';
import GlobalLayers from './components/GlobalLayers';
import UniversalDashboard from './components/UniversalDashboard';
import MobileLayout from './components/MobileLayout';
import DesktopLayout from './components/DesktopLayout';

// Import hooks and services
import { useWebSocket } from './hooks/useWebSocket';
import { useAgentRegistry } from './hooks/useAgentRegistry';
import { useSystemAgent } from './hooks/useSystemAgent';
import { useMCPConnector } from './hooks/useMCPConnector';

// Platform detection
const isWeb = Platform.OS === 'web';
const isMobile = Platform.OS === 'ios' || Platform.OS === 'android';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function MobileApp() {
  const { agents, loading: agentsLoading } = useAgentRegistry();
  const { systemInfo } = useSystemAgent();
  const { connectionStatus } = useWebSocket();

  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          tabBarStyle: {
            backgroundColor: '#0a0a0a',
            borderTopColor: '#1a1a1a',
          },
          tabBarActiveTintColor: '#00ff88',
          tabBarInactiveTintColor: '#666',
          headerStyle: {
            backgroundColor: '#0a0a0a',
            borderBottomColor: '#1a1a1a',
          },
          headerTintColor: '#fff',
        }}
      >
        <Tab.Screen
          name="Dashboard"
          component={UniversalDashboard}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Icon name="activity" size={size} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Agents"
          component={AgentWorkforce}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Icon name="users" size={size} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Control"
          component={SystemControl}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Icon name="terminal" size={size} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Layers"
          component={GlobalLayers}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Icon name="layers" size={size} color={color} />
            ),
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

function WebApp() {
  const { agents, loading: agentsLoading } = useAgentRegistry();
  const { systemInfo } = useSystemAgent();
  const { connectionStatus } = useWebSocket();

  return (
    <Router>
      <div className="app-container">
        <DesktopLayout>
          <Routes>
            <Route path="/" element={<UniversalDashboard />} />
            <Route path="/agents" element={<AgentWorkforce />} />
            <Route path="/control" element={<SystemControl />} />
            <Route path="/layers" element={<GlobalLayers />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </DesktopLayout>
      </div>
    </Router>
  );
}

function App() {
  const [platform, setPlatform] = useState('web');
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Detect platform
    if (typeof window !== 'undefined') {
      // Web environment
      setPlatform('web');
    } else {
      // React Native environment
      setPlatform('mobile');
    }
    setIsInitialized(true);
  }, []);

  if (!isInitialized) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loadingText}>ASIMNEXUS Universal Interface</div>
        <div style={styles.loadingSubtext}>Initializing Digital Workforce...</div>
      </div>
    );
  }

  // Render based on platform
  if (platform === 'mobile') {
    return <MobileApp />;
  } else {
    return <WebApp />;
  }
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a0a',
  },
  loadingText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00ff88',
    marginBottom: 10,
  },
  loadingSubtext: {
    fontSize: 16,
    color: '#666',
  },
});

// Web-specific styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
      color: #ffffff;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      background: #0a0a0a;
      color: #ffffff;
    }
    
    ::-webkit-scrollbar {
      width: 8px;
    }
    
    ::-webkit-scrollbar-track {
      background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
      background: #333;
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background: #555;
    }
  `;
  document.head.appendChild(style);
}

export default App;
