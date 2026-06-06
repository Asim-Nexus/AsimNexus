/**
 * FoundersScreen — Bare React Native stub
 *
 * Redirects users to the Expo variant for full functionality.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Linking } from 'react-native';

const FoundersScreen: React.FC = () => {
    return (
        <View style={styles.container}>
            <Text style={styles.icon}>👥</Text>
            <Text style={styles.title}>Founders</Text>
            <Text style={styles.description}>
                Founder clone management and status monitoring is available in the Expo
                variant.
            </Text>
            <TouchableOpacity
                style={styles.button}
                onPress={() =>
                    Linking.openURL(
                        'https://github.com/asimnexus/asimnexus/tree/main/mobile/react_native/screens/FoundersScreen.js',
                    )
                }>
                <Text style={styles.buttonText}>Open Expo Founders</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        padding: 20,
    },
    icon: {
        fontSize: 48,
        marginBottom: 16,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1a1a2e',
        marginBottom: 12,
    },
    description: {
        fontSize: 14,
        color: '#666',
        textAlign: 'center',
        lineHeight: 20,
        marginBottom: 24,
    },
    button: {
        backgroundColor: '#8884d8',
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 8,
    },
    buttonText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 14,
    },
});

export default FoundersScreen;
