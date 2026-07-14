/**
 * AsimNexus Mobile — Login Screen
 */
import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    ActivityIndicator,
    Alert,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService } from '../services/api';

interface Props {
    onLogin: () => void;
}

export default function LoginScreen({ onLogin }: Props) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isRegister, setIsRegister] = useState(false);
    const [username, setUsername] = useState('');

    async function handleSubmit() {
        if (!email || !password) {
            Alert.alert('Error', 'Please fill in all fields');
            return;
        }
        if (isRegister && !username) {
            Alert.alert('Error', 'Please enter a username');
            return;
        }

        setIsLoading(true);
        try {
            const result = isRegister
                ? await apiService.register(username, email, password)
                : await apiService.login(email, password);

            if (result.success && result.data?.token) {
                await AsyncStorage.setItem('asimnexus_token', result.data.token);
                apiService.setToken(result.data.token);
                onLogin();
            } else {
                Alert.alert('Error', result.error || 'Authentication failed');
            }
        } catch (error: any) {
            const message = error?.response?.data?.error || error?.message || 'Connection failed';
            Alert.alert('Error', message);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
            <View style={styles.content}>
                <Text style={styles.logo}>🪞</Text>
                <Text style={styles.title}>AsimNexus</Text>
                <Text style={styles.subtitle}>Universal AI Operating System</Text>

                <View style={styles.form}>
                    {isRegister && (
                        <TextInput
                            style={styles.input}
                            placeholder="Username"
                            placeholderTextColor="#64748b"
                            value={username}
                            onChangeText={setUsername}
                            autoCapitalize="none"
                        />
                    )}
                    <TextInput
                        style={styles.input}
                        placeholder="Email"
                        placeholderTextColor="#64748b"
                        value={email}
                        onChangeText={setEmail}
                        keyboardType="email-address"
                        autoCapitalize="none"
                    />
                    <TextInput
                        style={styles.input}
                        placeholder="Password"
                        placeholderTextColor="#64748b"
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                    />

                    <TouchableOpacity
                        style={[styles.button, isLoading && styles.buttonDisabled]}
                        onPress={handleSubmit}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <ActivityIndicator color="#0f172a" />
                        ) : (
                            <Text style={styles.buttonText}>
                                {isRegister ? 'Register' : 'Login'}
                            </Text>
                        )}
                    </TouchableOpacity>

                    <TouchableOpacity onPress={() => setIsRegister(!isRegister)}>
                        <Text style={styles.switchText}>
                            {isRegister
                                ? 'Already have an account? Login'
                                : "Don't have an account? Register"}
                        </Text>
                    </TouchableOpacity>
                </View>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
    },
    content: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
    },
    logo: {
        fontSize: 64,
        marginBottom: 8,
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#10b981',
        marginBottom: 4,
    },
    subtitle: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 48,
    },
    form: {
        width: '100%',
        maxWidth: 320,
    },
    input: {
        backgroundColor: '#1e293b',
        borderWidth: 1,
        borderColor: '#334155',
        borderRadius: 12,
        padding: 16,
        fontSize: 16,
        color: '#f1f5f9',
        marginBottom: 12,
    },
    button: {
        backgroundColor: '#10b981',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        marginTop: 8,
    },
    buttonDisabled: {
        opacity: 0.6,
    },
    buttonText: {
        color: '#0f172a',
        fontSize: 16,
        fontWeight: '600',
    },
    switchText: {
        color: '#10b981',
        textAlign: 'center',
        marginTop: 16,
        fontSize: 14,
    },
});
