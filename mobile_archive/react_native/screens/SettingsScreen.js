import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, Alert, Switch } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../config';

const CONFIG_KEYS = {
    API_URL: '@asimnexus_api_url',
    THEME: '@asimnexus_theme',
    POLLING: '@asimnexus_polling',
};

const SettingsScreen = () => {
    const [apiUrl, setApiUrl] = useState(API_BASE_URL);
    const [theme, setTheme] = useState('light');
    const [pollingEnabled, setPollingEnabled] = useState(true);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        (async () => {
            try {
                const savedUrl = await AsyncStorage.getItem(CONFIG_KEYS.API_URL);
                const savedTheme = await AsyncStorage.getItem(CONFIG_KEYS.THEME);
                const savedPolling = await AsyncStorage.getItem(CONFIG_KEYS.POLLING);
                if (savedUrl) setApiUrl(savedUrl);
                if (savedTheme) setTheme(savedTheme);
                if (savedPolling !== null) setPollingEnabled(savedPolling === 'true');
            } catch (_) { }
        })();
    }, []);

    const saveSettings = async () => {
        try {
            await AsyncStorage.setItem(CONFIG_KEYS.API_URL, apiUrl);
            await AsyncStorage.setItem(CONFIG_KEYS.THEME, theme);
            await AsyncStorage.setItem(CONFIG_KEYS.POLLING, pollingEnabled ? 'true' : 'false');
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
            Alert.alert('Settings Saved', 'App will use new settings on next restart');
        } catch (err) {
            Alert.alert('Error', 'Failed to save settings');
        }
    };

    const testConnection = async () => {
        try {
            const response = await fetch(`${apiUrl}/api/health`, { method: 'GET' });
            if (response.ok) {
                const data = await response.json();
                Alert.alert('✅ Connected', `Backend is healthy\n${JSON.stringify(data, null, 2).slice(0, 200)}`);
            } else {
                Alert.alert('⚠️ Error', `Backend returned status ${response.status}`);
            }
        } catch (err) {
            Alert.alert('❌ Connection Failed', err.message);
        }
    };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>⚙️ Settings</Text>

            {/* API Configuration */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>API Configuration</Text>
                <Text style={styles.label}>Backend URL</Text>
                <TextInput style={styles.input} value={apiUrl} onChangeText={setApiUrl} placeholder="http://localhost:8000" autoCapitalize="none" autoCorrect={false} />
                <View style={styles.buttonRow}>
                    <TouchableOpacity style={[styles.button, { backgroundColor: '#2563eb', flex: 1 }]} onPress={testConnection}>
                        <Text style={styles.buttonText}>Test Connection</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Display */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Display</Text>
                <View style={styles.switchRow}>
                    <Text style={styles.label}>Theme</Text>
                    <View style={styles.themeRow}>
                        <TouchableOpacity style={[styles.themeBtn, theme === 'light' && styles.themeActive]} onPress={() => setTheme('light')}>
                            <Text style={[styles.themeText, theme === 'light' && styles.themeTextActive]}>Light</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={[styles.themeBtn, theme === 'dark' && styles.themeActive]} onPress={() => setTheme('dark')}>
                            <Text style={[styles.themeText, theme === 'dark' && styles.themeTextActive]}>Dark</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </View>

            {/* Data */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Data</Text>
                <View style={styles.switchRow}>
                    <Text style={styles.label}>Auto-refresh data</Text>
                    <Switch value={pollingEnabled} onValueChange={setPollingEnabled} trackColor={{ false: '#ddd', true: '#8884d8' }} thumbColor={pollingEnabled ? '#1a1a2e' : '#f4f3f4'} />
                </View>
            </View>

            {/* About */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>About</Text>
                <Text style={styles.detailText}>ASIMNEXUS World OS</Text>
                <Text style={styles.detailText}>Version: 1.0.0</Text>
                <Text style={styles.detailText}>Architecture: React Native (Expo)</Text>
                <Text style={styles.detailText}>Platform: iOS & Android</Text>
            </View>

            {/* Save */}
            <TouchableOpacity style={[styles.button, styles.saveBtn]} onPress={saveSettings}>
                <Text style={styles.saveBtnText}>{saved ? '✓ Saved!' : 'Save Settings'}</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5', padding: 20 },
    title: { fontSize: 28, fontWeight: 'bold', marginBottom: 20, color: '#1a1a2e' },
    card: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginBottom: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
    cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 12, color: '#1a1a2e' },
    label: { fontSize: 14, fontWeight: '600', color: '#666', marginBottom: 6 },
    input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, fontSize: 15, marginBottom: 12, color: '#333' },
    button: { paddingVertical: 12, borderRadius: 8, alignItems: 'center', marginBottom: 8 },
    buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
    buttonRow: { flexDirection: 'row', gap: 10 },
    switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
    themeRow: { flexDirection: 'row', gap: 8 },
    themeBtn: { paddingVertical: 6, paddingHorizontal: 20, borderRadius: 8, backgroundColor: '#e5e7eb' },
    themeActive: { backgroundColor: '#8884d8' },
    themeText: { fontSize: 14, color: '#666' },
    themeTextActive: { color: '#fff', fontWeight: '600' },
    detailText: { fontSize: 14, color: '#666', marginBottom: 4 },
    saveBtn: { backgroundColor: '#059669', marginTop: 10 },
    saveBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 18 },
});

export default SettingsScreen;
