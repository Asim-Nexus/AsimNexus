/**
 * ASIMNEXUS World OS — Mobile Application (Bare React Native)
 *
 * This is the bare React Native variant. For the full-featured mobile app
 * with all screens and functionality, use the Expo variant at:
 *   mobile/react_native/
 *
 * This stub exists to satisfy the bare RN build configuration and
 * redirects users to the Expo variant.
 */

import React from 'react';
import {
    SafeAreaView,
    ScrollView,
    StatusBar,
    StyleSheet,
    Text,
    useColorScheme,
    View,
    Linking,
    TouchableOpacity,
} from 'react-native';

const EXPO_APP_PATH = '../react_native'; // Relative path to the Expo variant

const Section: React.FC<{
    title: string;
    children: React.ReactNode;
}> = ({ title, children }) => {
    const isDarkMode = useColorScheme() === 'dark';
    return (
        <View style={styles.sectionContainer}>
            <Text
                style={[
                    styles.sectionTitle,
                    { color: isDarkMode ? '#fff' : '#1a1a2e' },
                ]}>
                {title}
            </Text>
            <Text
                style={[
                    styles.sectionDescription,
                    { color: isDarkMode ? '#ccc' : '#666' },
                ]}>
                {children}
            </Text>
        </View>
    );
};

function App(): React.JSX.Element {
    const isDarkMode = useColorScheme() === 'dark';

    const backgroundStyle = {
        backgroundColor: isDarkMode ? '#0d0d1a' : '#f5f5f5',
    };

    return (
        <SafeAreaView style={backgroundStyle}>
            <StatusBar
                barStyle={isDarkMode ? 'light-content' : 'dark-content'}
                backgroundColor={backgroundStyle.backgroundColor}
            />
            <ScrollView
                contentInsetAdjustmentBehavior="automatic"
                style={backgroundStyle}>
                <View style={styles.header}>
                    <Text style={styles.logo}>🌐 ASIMNEXUS</Text>
                    <Text style={styles.subtitle}>World OS for 8 Billion People</Text>
                </View>

                <View
                    style={{
                        backgroundColor: isDarkMode ? '#1a1a2e' : '#e0e7ff',
                        padding: 20,
                        marginHorizontal: 20,
                        borderRadius: 12,
                        borderWidth: 1,
                        borderColor: isDarkMode ? '#8884d8' : '#a5b4fc',
                    }}>
                    <Text
                        style={{
                            fontSize: 18,
                            fontWeight: 'bold',
                            color: isDarkMode ? '#fff' : '#1a1a2e',
                            marginBottom: 8,
                        }}>
                        🚧 Coming Soon
                    </Text>
                    <Text
                        style={{
                            fontSize: 14,
                            color: isDarkMode ? '#ccc' : '#4b5563',
                            lineHeight: 20,
                        }}>
                        This is the bare React Native stub. The full-featured mobile app
                        with all screens (Dashboard, Founders, Agents, Security) is
                        available in the Expo variant.
                    </Text>
                    <TouchableOpacity
                        style={styles.linkButton}
                        onPress={() => {
                            Linking.openURL('https://github.com/asimnexus/asimnexus/tree/main/mobile/react_native');
                        }}>
                        <Text style={styles.linkButtonText}>
                            Open Expo Variant (react_native/)
                        </Text>
                    </TouchableOpacity>
                </View>

                <View style={styles.sectionList}>
                    <Section title="📊 Dashboard">
                        System metrics, World OS status, and analytics overview.
                    </Section>
                    <Section title="👥 Founders">
                        Founder clones with status monitoring.
                    </Section>
                    <Section title="🤖 Agents">
                        Worker agent tracking and management.
                    </Section>
                    <Section title="🔒 Security">
                        Threat level monitoring and security events.
                    </Section>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    header: {
        padding: 40,
        alignItems: 'center',
    },
    logo: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#8884d8',
    },
    subtitle: {
        fontSize: 14,
        color: '#666',
        marginTop: 4,
    },
    sectionList: {
        marginTop: 20,
        paddingHorizontal: 20,
    },
    sectionContainer: {
        marginBottom: 16,
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        marginBottom: 6,
    },
    sectionDescription: {
        fontSize: 14,
        lineHeight: 20,
    },
    linkButton: {
        backgroundColor: '#8884d8',
        paddingVertical: 12,
        paddingHorizontal: 20,
        borderRadius: 8,
        marginTop: 16,
        alignItems: 'center',
    },
    linkButtonText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 14,
    },
});

export default App;
