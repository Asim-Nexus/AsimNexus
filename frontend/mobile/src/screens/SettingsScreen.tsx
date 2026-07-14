/**
 * AsimNexus Mobile — Settings Screen
 * App configuration, server connection, security, about
 */
import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    TextInput,
    Switch,
    Alert,
    Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService, checkBackendHealth } from '../services/api';

const STORAGE_KEYS = {
    SERVER_URL: 'asimnexus_server_url',
    NOTIFICATIONS: 'asimnexus_notifications',
    BIOMETRIC: 'asimnexus_biometric',
    THEME: 'asimnexus_theme',
};

export default function SettingsScreen({ onLogout }: { onLogout?: () => void }) {
    const [serverUrl, setServerUrl] = useState('http://localhost:8000');
    const [isConnected, setIsConnected] = useState<boolean | null>(null);
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);
    const [biometricEnabled, setBiometricEnabled] = useState(false);
    const [editingUrl, setEditingUrl] = useState(false);
    const [tempUrl, setTempUrl] = useState('');

    useEffect(() => {
        loadSettings();
        checkConnection();
    }, []);

    async function loadSettings() {
        try {
            const savedUrl = await AsyncStorage.getItem(STORAGE_KEYS.SERVER_URL);
            const savedNotifications = await AsyncStorage.getItem(STORAGE_KEYS.NOTIFICATIONS);
            const savedBiometric = await AsyncStorage.getItem(STORAGE_KEYS.BIOMETRIC);

            if (savedUrl) setServerUrl(savedUrl);
            if (savedNotifications !== null) setNotificationsEnabled(savedNotifications === 'true');
            if (savedBiometric !== null) setBiometricEnabled(savedBiometric === 'true');
        } catch (error) {
            console.warn('[Settings] Load error:', error);
        }
    }

    async function checkConnection() {
        const healthy = await checkBackendHealth();
        setIsConnected(healthy);
    }

    async function handleSaveUrl() {
        const url = tempUrl.trim();
        if (!url) {
            Alert.alert('Error', 'Please enter a valid server URL.');
            return;
        }
        try {
            await AsyncStorage.setItem(STORAGE_KEYS.SERVER_URL, url);
            setServerUrl(url);
            setEditingUrl(false);
            // Re-check connection with new URL
            setTimeout(checkConnection, 1000);
            Alert.alert('Saved', 'Server URL updated. Reconnecting...');
        } catch (error) {
            Alert.alert('Error', 'Failed to save server URL.');
        }
    }

    async function handleToggleNotifications(value: boolean) {
        setNotificationsEnabled(value);
        await AsyncStorage.setItem(STORAGE_KEYS.NOTIFICATIONS, String(value));
    }

    async function handleToggleBiometric(value: boolean) {
        setBiometricEnabled(value);
        await AsyncStorage.setItem(STORAGE_KEYS.BIOMETRIC, String(value));
    }

    async function handleClearCache() {
        Alert.alert(
            'Clear Cache',
            'This will clear all locally cached data. You will need to re-download data from the server.',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Clear',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await AsyncStorage.clear();
                            Alert.alert('Done', 'Cache cleared. Please restart the app.');
                        } catch (error) {
                            Alert.alert('Error', 'Failed to clear cache.');
                        }
                    },
                },
            ]
        );
    }

    async function handleLogout() {
        Alert.alert('Logout', 'Are you sure you want to logout?', [
            { text: 'Cancel', style: 'cancel' },
            {
                text: 'Logout',
                style: 'destructive',
                onPress: async () => {
                    await AsyncStorage.removeItem('asimnexus_token');
                    await AsyncStorage.removeItem('asimnexus_user');
                    onLogout?.();
                },
            },
        ]);
    }

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>Settings</Text>
            <Text style={styles.subtitle}>Configure your AsimNexus experience</Text>

            {/* Server Connection */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Server Connection</Text>

                <View style={styles.settingRow}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Status</Text>
                        <Text style={styles.settingDescription}>
                            {isConnected === null
                                ? 'Checking...'
                                : isConnected
                                    ? 'Connected'
                                    : 'Disconnected'}
                        </Text>
                    </View>
                    <View
                        style={[
                            styles.statusDot,
                            {
                                backgroundColor:
                                    isConnected === null
                                        ? '#64748b'
                                        : isConnected
                                            ? '#10b981'
                                            : '#ef4444',
                            },
                        ]}
                    />
                </View>

                {editingUrl ? (
                    <View style={styles.editUrlContainer}>
                        <TextInput
                            style={styles.urlInput}
                            value={tempUrl}
                            onChangeText={setTempUrl}
                            placeholder="http://your-server:8000"
                            placeholderTextColor="#64748b"
                            autoCapitalize="none"
                            autoCorrect={false}
                        />
                        <View style={styles.editUrlActions}>
                            <TouchableOpacity
                                style={styles.cancelButton}
                                onPress={() => setEditingUrl(false)}
                            >
                                <Text style={styles.cancelButtonText}>Cancel</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.saveButton} onPress={handleSaveUrl}>
                                <Text style={styles.saveButtonText}>Save</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                ) : (
                    <TouchableOpacity
                        style={styles.settingRow}
                        onPress={() => {
                            setTempUrl(serverUrl);
                            setEditingUrl(true);
                        }}
                    >
                        <View style={styles.settingInfo}>
                            <Text style={styles.settingLabel}>Server URL</Text>
                            <Text style={styles.settingDescription}>{serverUrl}</Text>
                        </View>
                        <Text style={styles.editIcon}>✏️</Text>
                    </TouchableOpacity>
                )}
            </View>

            {/* Notifications */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Notifications</Text>

                <View style={styles.settingRow}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Push Notifications</Text>
                        <Text style={styles.settingDescription}>
                            Receive alerts for important events
                        </Text>
                    </View>
                    <Switch
                        value={notificationsEnabled}
                        onValueChange={handleToggleNotifications}
                        trackColor={{ false: '#334155', true: '#10b981' }}
                        thumbColor={notificationsEnabled ? '#f1f5f9' : '#64748b'}
                    />
                </View>
            </View>

            {/* Security */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Security</Text>

                <View style={styles.settingRow}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Biometric Auth</Text>
                        <Text style={styles.settingDescription}>
                            Use fingerprint / face ID to unlock
                        </Text>
                    </View>
                    <Switch
                        value={biometricEnabled}
                        onValueChange={handleToggleBiometric}
                        trackColor={{ false: '#334155', true: '#10b981' }}
                        thumbColor={biometricEnabled ? '#f1f5f9' : '#64748b'}
                    />
                </View>
            </View>

            {/* Data Management */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Data</Text>

                <TouchableOpacity style={styles.settingRow} onPress={handleClearCache}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Clear Cache</Text>
                        <Text style={styles.settingDescription}>
                            Remove locally stored data
                        </Text>
                    </View>
                    <Text style={styles.destructiveIcon}>🗑️</Text>
                </TouchableOpacity>
            </View>

            {/* About */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>About</Text>

                <View style={styles.settingRow}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Version</Text>
                        <Text style={styles.settingDescription}>1.0.0-rc.1</Text>
                    </View>
                </View>

                <View style={styles.settingRow}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Platform</Text>
                        <Text style={styles.settingDescription}>
                            {Platform.OS === 'ios' ? 'iOS' : 'Android'}
                        </Text>
                    </View>
                </View>

                <View style={styles.settingRow}>
                    <View style={styles.settingInfo}>
                        <Text style={styles.settingLabel}>Framework</Text>
                        <Text style={styles.settingDescription}>React Native</Text>
                    </View>
                </View>
            </View>

            {/* Logout */}
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                <Text style={styles.logoutButtonText}>Logout</Text>
            </TouchableOpacity>

            <View style={styles.footer}>
                <Text style={styles.footerText}>AsimNexus — Universal AI Operating System</Text>
                <Text style={styles.footerText}>© 2025 AsimNexus</Text>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
        padding: 16,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#f1f5f9',
        marginBottom: 4,
    },
    subtitle: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 24,
    },
    section: {
        backgroundColor: '#1e293b',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
    },
    sectionTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: '#10b981',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 12,
    },
    settingRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 8,
    },
    settingInfo: {
        flex: 1,
        marginRight: 12,
    },
    settingLabel: {
        fontSize: 15,
        color: '#f1f5f9',
        fontWeight: '500',
    },
    settingDescription: {
        fontSize: 13,
        color: '#64748b',
        marginTop: 2,
    },
    statusDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
    },
    editUrlContainer: {
        marginTop: 8,
    },
    urlInput: {
        backgroundColor: '#0f172a',
        borderRadius: 8,
        padding: 12,
        fontSize: 14,
        color: '#f1f5f9',
        fontFamily: 'monospace',
    },
    editUrlActions: {
        flexDirection: 'row',
        justifyContent: 'flex-end',
        gap: 8,
        marginTop: 8,
    },
    cancelButton: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 6,
        backgroundColor: '#334155',
    },
    cancelButtonText: {
        fontSize: 14,
        color: '#94a3b8',
    },
    saveButton: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 6,
        backgroundColor: '#10b981',
    },
    saveButtonText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#0f172a',
    },
    editIcon: {
        fontSize: 16,
    },
    destructiveIcon: {
        fontSize: 18,
    },
    logoutButton: {
        backgroundColor: '#ef4444',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        marginBottom: 24,
    },
    logoutButtonText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#ffffff',
    },
    footer: {
        alignItems: 'center',
        marginBottom: 32,
    },
    footerText: {
        fontSize: 12,
        color: '#475569',
        marginBottom: 2,
    },
});
