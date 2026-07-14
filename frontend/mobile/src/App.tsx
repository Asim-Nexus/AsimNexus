/**
 * AsimNexus Mobile App — Root Component
 * React Native app with tab navigation for all core features
 */
import React, { useEffect, useState } from 'react';
import {
    SafeAreaView,
    StatusBar,
    StyleSheet,
    Text,
    View,
    ActivityIndicator,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Screens
import LoginScreen from './screens/LoginScreen';
import DashboardScreen from './screens/DashboardScreen';
import ChatScreen from './screens/ChatScreen';
import EconomyScreen from './screens/EconomyScreen';
import IdentityScreen from './screens/IdentityScreen';
import GovernanceScreen from './screens/GovernanceScreen';
import AgentModeScreen from './screens/AgentModeScreen';
import NepalScreen from './screens/NepalScreen';
import SettingsScreen from './screens/SettingsScreen';

// Services
import { apiService, checkBackendHealth } from './services/api';

// Types
import { User } from './types';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MainTabs() {
    return (
        <Tab.Navigator
            screenOptions={{
                tabBarStyle: styles.tabBar,
                tabBarActiveTintColor: '#10b981',
                tabBarInactiveTintColor: '#64748b',
                headerStyle: styles.header,
                headerTintColor: '#f1f5f9',
                headerTitleStyle: styles.headerTitle,
            }}
        >
            <Tab.Screen
                name="Dashboard"
                component={DashboardScreen}
                options={{ tabBarLabel: 'Home', tabBarIcon: () => <Text>🏠</Text> }}
            />
            <Tab.Screen
                name="Chat"
                component={ChatScreen}
                options={{ tabBarLabel: 'Chat', tabBarIcon: () => <Text>💬</Text> }}
            />
            <Tab.Screen
                name="Economy"
                component={EconomyScreen}
                options={{ tabBarLabel: 'Economy', tabBarIcon: () => <Text>💰</Text> }}
            />
            <Tab.Screen
                name="Identity"
                component={IdentityScreen}
                options={{ tabBarLabel: 'Identity', tabBarIcon: () => <Text>🆔</Text> }}
            />
            <Tab.Screen
                name="Governance"
                component={GovernanceScreen}
                options={{ tabBarLabel: 'Governance', tabBarIcon: () => <Text>🏛️</Text> }}
            />
            <Tab.Screen
                name="Agent"
                component={AgentModeScreen}
                options={{ tabBarLabel: 'Agent', tabBarIcon: () => <Text>🤖</Text> }}
            />
            <Tab.Screen
                name="Nepal"
                component={NepalScreen}
                options={{ tabBarLabel: 'Nepal', tabBarIcon: () => <Text>🇳🇵</Text> }}
            />
            <Tab.Screen
                name="Settings"
                component={SettingsScreen}
                options={{ tabBarLabel: 'Settings', tabBarIcon: () => <Text>⚙️</Text> }}
            />
        </Tab.Navigator>
    );
}

export default function App() {
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [backendHealthy, setBackendHealthy] = useState(false);

    useEffect(() => {
        initializeApp();
    }, []);

    async function initializeApp() {
        try {
            // Check backend health
            const healthy = await checkBackendHealth();
            setBackendHealthy(healthy);

            // Check stored auth token
            const token = await AsyncStorage.getItem('asimnexus_token');
            if (token) {
                apiService.setToken(token);
                setIsAuthenticated(true);
            }
        } catch (error) {
            console.warn('[Mobile] Initialization error:', error);
        } finally {
            setIsLoading(false);
        }
    }

    if (isLoading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#10b981" />
                <Text style={styles.loadingText}>AsimNexus Mobile</Text>
                <Text style={styles.loadingSubtext}>Initializing...</Text>
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
            {!backendHealthy && (
                <View style={styles.offlineBanner}>
                    <Text style={styles.offlineText}>⚠️ Backend unreachable — offline mode</Text>
                </View>
            )}
            <NavigationContainer>
                <Stack.Navigator screenOptions={{ headerShown: false }}>
                    {isAuthenticated ? (
                        <Stack.Screen name="Main" component={MainTabs} />
                    ) : (
                        <Stack.Screen name="Login">
                            {(props) => (
                                <LoginScreen
                                    {...props}
                                    onLogin={() => setIsAuthenticated(true)}
                                />
                            )}
                        </Stack.Screen>
                    )}
                </Stack.Navigator>
            </NavigationContainer>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#0f172a',
    },
    loadingText: {
        color: '#10b981',
        fontSize: 24,
        fontWeight: 'bold',
        marginTop: 16,
    },
    loadingSubtext: {
        color: '#64748b',
        fontSize: 14,
        marginTop: 8,
    },
    tabBar: {
        backgroundColor: '#1e293b',
        borderTopColor: '#334155',
        borderTopWidth: 1,
        paddingBottom: 4,
        paddingTop: 4,
        height: 60,
    },
    header: {
        backgroundColor: '#1e293b',
        elevation: 0,
        shadowOpacity: 0,
    },
    headerTitle: {
        color: '#f1f5f9',
        fontWeight: '600',
    },
    offlineBanner: {
        backgroundColor: '#f59e0b',
        padding: 8,
        alignItems: 'center',
    },
    offlineText: {
        color: '#1e293b',
        fontSize: 12,
        fontWeight: '600',
    },
});
