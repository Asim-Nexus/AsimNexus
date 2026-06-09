import React, { useState, useRef, useEffect } from 'react';
import {
    View, Text, StyleSheet, TextInput, TouchableOpacity,
    FlatList, KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import asimAPI from '../services/asimAPI';

const STORAGE_KEY = '@asimnexus_chat_history';

const ChatScreen = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [useWorldOS, setUseWorldOS] = useState(true);
    const flatListRef = useRef(null);

    // Load saved chat history
    useEffect(() => {
        (async () => {
            try {
                const saved = await AsyncStorage.getItem(STORAGE_KEY);
                if (saved) setMessages(JSON.parse(saved));
            } catch (_) { }
        })();
    }, []);

    // Save chat history
    const saveMessages = async (msgs) => {
        try {
            // Keep last 100 messages for storage
            const toSave = msgs.slice(-100);
            await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
        } catch (_) { }
    };

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;

        const userMsg = { id: Date.now().toString(), role: 'user', text, timestamp: new Date().toISOString() };
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setInput('');
        setLoading(true);

        try {
            const res = await asimAPI.chat(text, useWorldOS);
            const responseText = res.response || res.message || res.reply || JSON.stringify(res);

            const botMsg = {
                id: (Date.now() + 1).toString(),
                role: 'bot',
                text: responseText,
                timestamp: new Date().toISOString(),
            };
            const finalMessages = [...updatedMessages, botMsg];
            setMessages(finalMessages);
            saveMessages(finalMessages);
        } catch (err) {
            const errorMsg = {
                id: (Date.now() + 1).toString(),
                role: 'bot',
                text: `⚠️ Connection error: ${err.message}. Make sure the backend is running.`,
                timestamp: new Date().toISOString(),
                isError: true,
            };
            const finalMessages = [...updatedMessages, errorMsg];
            setMessages(finalMessages);
            saveMessages(finalMessages);
        }
        setLoading(false);
    };

    const clearHistory = async () => {
        setMessages([]);
        await AsyncStorage.removeItem(STORAGE_KEY);
    };

    const renderMessage = ({ item }) => (
        <View style={[styles.msgBubble, item.role === 'user' ? styles.userBubble : styles.botBubble, item.isError && styles.errorBubble]}>
            <Text style={styles.msgRole}>{item.role === 'user' ? 'You' : 'ASIMNEXUS'}</Text>
            <Text style={[styles.msgText, item.isError && styles.errorText]}>{item.text}</Text>
            <Text style={styles.msgTime}>{new Date(item.timestamp).toLocaleTimeString()}</Text>
        </View>
    );

    return (
        <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
            <View style={styles.header}>
                <Text style={styles.title}>💬 Chat</Text>
                <View style={styles.headerRight}>
                    <TouchableOpacity
                        style={[styles.toggleBtn, useWorldOS && styles.toggleActive]}
                        onPress={() => setUseWorldOS(!useWorldOS)}
                    >
                        <Text style={[styles.toggleText, useWorldOS && styles.toggleTextActive]}>
                            {useWorldOS ? '🌐 OS' : '💬 Chat'}
                        </Text>
                    </TouchableOpacity>
                    {messages.length > 0 && (
                        <TouchableOpacity style={styles.clearBtn} onPress={clearHistory}>
                            <Text style={styles.clearText}>Clear</Text>
                        </TouchableOpacity>
                    )}
                </View>
            </View>

            <FlatList
                ref={flatListRef}
                data={messages}
                keyExtractor={(item) => item.id}
                renderItem={renderMessage}
                style={styles.chatList}
                contentContainerStyle={styles.chatContent}
                onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
                ListEmptyComponent={
                    <View style={styles.emptyChat}>
                        <Text style={styles.emptyIcon}>🤖</Text>
                        <Text style={styles.emptyTitle}>ASIMNEXUS AI Assistant</Text>
                        <Text style={styles.emptySubtitle}>Ask me anything about the system, economy, or your agents</Text>
                    </View>
                }
            />

            {loading && (
                <View style={styles.loadingBar}>
                    <ActivityIndicator size="small" color="#8884d8" />
                    <Text style={styles.loadingText}>Thinking...</Text>
                </View>
            )}

            <View style={styles.inputBar}>
                <TextInput
                    style={styles.input}
                    placeholder="Type a message..."
                    placeholderTextColor="#999"
                    value={input}
                    onChangeText={setInput}
                    multiline
                    maxLength={2000}
                    onSubmitEditing={sendMessage}
                    blurOnSubmit
                />
                <TouchableOpacity style={[styles.sendBtn, !input.trim() && styles.sendBtnDisabled]} onPress={sendMessage} disabled={!input.trim() || loading}>
                    <Text style={styles.sendText}>Send</Text>
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: {
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
        padding: 16, backgroundColor: '#1a1a2e',
    },
    title: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
    headerRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
    toggleBtn: { paddingVertical: 4, paddingHorizontal: 12, borderRadius: 16, backgroundColor: '#333' },
    toggleActive: { backgroundColor: '#8884d8' },
    toggleText: { fontSize: 12, color: '#999' },
    toggleTextActive: { color: '#fff', fontWeight: '600' },
    clearBtn: { paddingVertical: 4, paddingHorizontal: 12, borderRadius: 16, backgroundColor: '#dc2626' },
    clearText: { fontSize: 12, color: '#fff', fontWeight: '600' },
    chatList: { flex: 1 },
    chatContent: { padding: 16, paddingBottom: 8 },
    msgBubble: { padding: 14, borderRadius: 16, marginBottom: 10, maxWidth: '85%' },
    userBubble: { backgroundColor: '#8884d8', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
    botBubble: { backgroundColor: '#fff', alignSelf: 'flex-start', borderBottomLeftRadius: 4, borderWidth: 1, borderColor: '#e5e7eb' },
    errorBubble: { backgroundColor: '#fef2f2', borderColor: '#fecaca' },
    msgRole: { fontSize: 11, fontWeight: '600', color: '#999', marginBottom: 4 },
    msgText: { fontSize: 15, color: '#1a1a2e', lineHeight: 22 },
    errorText: { color: '#991b1b' },
    msgTime: { fontSize: 10, color: '#999', marginTop: 6, alignSelf: 'flex-end' },
    emptyChat: { alignItems: 'center', paddingTop: 60 },
    emptyIcon: { fontSize: 64, marginBottom: 16 },
    emptyTitle: { fontSize: 20, fontWeight: 'bold', color: '#1a1a2e', marginBottom: 8 },
    emptySubtitle: { fontSize: 14, color: '#666', textAlign: 'center', paddingHorizontal: 40, lineHeight: 20 },
    loadingBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 8, gap: 8 },
    loadingText: { fontSize: 13, color: '#8884d8' },
    inputBar: {
        flexDirection: 'row', alignItems: 'flex-end', padding: 12,
        backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#e5e7eb',
    },
    input: {
        flex: 1, borderWidth: 1, borderColor: '#ddd', borderRadius: 24,
        paddingHorizontal: 16, paddingVertical: 10, fontSize: 16,
        maxHeight: 120, color: '#333', backgroundColor: '#f9f9f9',
    },
    sendBtn: {
        backgroundColor: '#8884d8', width: 60, height: 44, borderRadius: 22,
        justifyContent: 'center', alignItems: 'center', marginLeft: 8,
    },
    sendBtnDisabled: { backgroundColor: '#ccc' },
    sendText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
});

export default ChatScreen;
