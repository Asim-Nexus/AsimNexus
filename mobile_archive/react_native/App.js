import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

// Screens
import DashboardScreen from './screens/DashboardScreen';
import FoundersScreen from './screens/FoundersScreen';
import AgentsScreen from './screens/AgentsScreen';
import SecurityScreen from './screens/SecurityScreen';
import WalletScreen from './screens/WalletScreen';
import TokensScreen from './screens/TokensScreen';
import EscrowScreen from './screens/EscrowScreen';
import MarketplaceScreen from './screens/MarketplaceScreen';
import StakingScreen from './screens/StakingScreen';
import GovernanceScreen from './screens/GovernanceScreen';
import ChatScreen from './screens/ChatScreen';
import SettingsScreen from './screens/SettingsScreen';

import { API_BASE_URL } from './config';

const Tab = createBottomTabNavigator();
const EconomyStack = createNativeStackNavigator();

// ─── Connection Indicator ─────────────────────────────────────────────────────

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
        setStatus(response.ok ? 'connected' : 'error');
      } catch {
        setStatus('disconnected');
      }
    };

    checkConnection();
    intervalRef.current = setInterval(checkConnection, 10000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  const statusColors = { connected: '#4ade80', disconnected: '#ef4444', error: '#fbbf24', checking: '#9ca3af' };
  const statusLabels = { connected: 'Connected', disconnected: 'Disconnected', error: 'Error', checking: 'Checking...' };

  return (
    <View style={styles.connectionIndicator}>
      <View style={[styles.dot, { backgroundColor: statusColors[status] || '#9ca3af' }]} />
      <Text style={styles.connectionText}>{statusLabels[status] || 'Unknown'}</Text>
    </View>
  );
}

// ─── Economy Stack Navigator ──────────────────────────────────────────────────

function EconomyStackNavigator() {
  return (
    <EconomyStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#1a1a2e' },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <EconomyStack.Screen name="Wallet" component={WalletScreen} options={{ title: '💼 Wallet' }} />
      <EconomyStack.Screen name="Tokens" component={TokensScreen} options={{ title: '🪙 Tokens' }} />
      <EconomyStack.Screen name="Escrow" component={EscrowScreen} options={{ title: '🤝 Escrow' }} />
      <EconomyStack.Screen name="Marketplace" component={MarketplaceScreen} options={{ title: '🏪 Marketplace' }} />
      <EconomyStack.Screen name="Staking" component={StakingScreen} options={{ title: '🔒 Staking' }} />
    </EconomyStack.Navigator>
  );
}

// ─── Economy Menu Screen (tab entry point) ────────────────────────────────────

function EconomyMenuScreen({ navigation }) {
  const econItems = [
    { name: 'Wallet', icon: '💼', desc: 'Manage wallets, balances, deposits & transfers', screen: 'Wallet', color: '#166534' },
    { name: 'Tokens', icon: '🪙', desc: 'Register, mint, burn & lock tokens', screen: 'Tokens', color: '#7c3aed' },
    { name: 'Escrow', icon: '🤝', desc: 'Secure transactions with dispute resolution', screen: 'Escrow', color: '#2563eb' },
    { name: 'Marketplace', icon: '🏪', desc: 'Browse listings, buy & sell', screen: 'Marketplace', color: '#ca8a04' },
    { name: 'Staking', icon: '🔒', desc: 'Stake tokens, earn rewards', screen: 'Staking', color: '#059669' },
  ];

  return (
    <View style={styles.econMenuContainer}>
      <Text style={styles.econMenuTitle}>Economy</Text>
      <Text style={styles.econMenuSubtitle}>Full decentralized economy management</Text>
      {econItems.map((item, i) => (
        <View key={i} style={styles.econMenuItem}>
          <View style={styles.econItemLeft}>
            <Text style={styles.econItemIcon}>{item.icon}</Text>
            <View>
              <Text style={styles.econItemName}>{item.name}</Text>
              <Text style={styles.econItemDesc}>{item.desc}</Text>
            </View>
          </View>
          <View style={[styles.econItemBadge, { backgroundColor: item.color }]}>
            <Text
              style={styles.econItemBadgeText}
              onPress={() => navigation.navigate(item.screen)}
            >
              Open
            </Text>
          </View>
        </View>
      ))}
    </View>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <ConnectionIndicator />
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName;
              if (route.name === 'Dashboard') iconName = focused ? 'home' : 'home-outline';
              else if (route.name === 'Economy') iconName = focused ? 'wallet' : 'wallet-outline';
              else if (route.name === 'Agents') iconName = focused ? 'people' : 'people-outline';
              else if (route.name === 'Governance') iconName = focused ? 'balance-scale' : 'balance-scale-outline';
              else if (route.name === 'Chat') iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
              else if (route.name === 'Settings') iconName = focused ? 'settings' : 'settings-outline';
              return <Ionicons name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: '#8884d8',
            tabBarInactiveTintColor: 'gray',
            headerStyle: { backgroundColor: '#1a1a2e' },
            headerTintColor: '#fff',
            headerTitleStyle: { fontWeight: 'bold' },
          })}
        >
          <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title: '📊 Dashboard' }} />
          <Tab.Screen
            name="Economy"
            component={EconomyStackNavigator}
            options={{
              title: '💼 Economy',
              headerShown: false,
            }}
          />
          <Tab.Screen name="Agents" component={AgentsScreen} options={{ title: '🤖 Agents' }} />
          <Tab.Screen name="Governance" component={GovernanceScreen} options={{ title: '⚖️ Governance' }} />
          <Tab.Screen name="Chat" component={ChatScreen} options={{ title: '💬 Chat', headerShown: false }} />
          <Tab.Screen name="Settings" component={SettingsScreen} options={{ title: '⚙️ Settings' }} />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

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
  econMenuContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  econMenuTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a2e',
    marginBottom: 4,
  },
  econMenuSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
  },
  econMenuItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  econItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  econItemIcon: {
    fontSize: 32,
    marginRight: 14,
  },
  econItemName: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1a1a2e',
  },
  econItemDesc: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  econItemBadge: {
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  econItemBadgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 13,
  },
});
