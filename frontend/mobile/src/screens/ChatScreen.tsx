/**
 * AsimNexus Mobile — Chat Screen
 */
import React, { useState, useRef } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    FlatList,
    StyleSheet,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { apiService } from '../services/api';
import { ChatMessage } from '../types';

export default function ChatScreen() {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: 'Welcome to AsimNexus! How can I help you today?',
            timestamp: new Date().toISOString(),
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const flatListRef = useRef<FlatList>(null);

    async function sendMessage() {
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await apiService.sendMessage(userMessage.content);
            const assistantMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.data?.response || response.data?.message || 'No response',
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '⚠️ Failed to get response. Backend may be unavailable.',
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }

    function renderMessage({ item }: { item: ChatMessage }) {
        const isUser = item.role === 'user';
        return (
            <View style={[styles.messageRow, isUser ? styles.userRow : styles.assistantRow]}>
                <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
                    <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
                        {item.content}
                    </Text>
                    <Text style={styles.timestamp}>
                        {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Text>
                </View>
            </View>
        );
    }

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            keyboardVerticalOffset={90}
        >
            <FlatList
                ref={flatListRef}
                data={messages}
                renderItem={renderMessage}
                keyExtractor={(item) => item.id}
                style={styles.messageList}
                contentContainerStyle={styles.messageListContent}
                onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
            />

            <View style={styles.inputContainer}>
                <TextInput
                    style={styles.input}
                    placeholder="Type a message..."
                    placeholderTextColor="#64748b"
                    value={input}
                    onChangeText={setInput}
                    multiline
                    maxLength={2000}
                />
                <TouchableOpacity
                    style={[styles.sendButton, (!input.trim() || isLoading) && styles.sendButtonDisabled]}
                    onPress={sendMessage}
                    disabled={!input.trim() || isLoading}
                >
                    <Text style={styles.sendButtonText}>{isLoading ? '...' : '➤'}</Text>
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
    },
    messageList: {
        flex: 1,
    },
    messageListContent: {
        padding: 16,
    },
    messageRow: {
        marginBottom: 12,
        flexDirection: 'row',
    },
    userRow: {
        justifyContent: 'flex-end',
    },
    assistantRow: {
        justifyContent: 'flex-start',
    },
    bubble: {
        maxWidth: '80%',
        borderRadius: 16,
        padding: 12,
    },
    userBubble: {
        backgroundColor: '#10b981',
        borderBottomRightRadius: 4,
    },
    assistantBubble: {
        backgroundColor: '#1e293b',
        borderBottomLeftRadius: 4,
    },
    messageText: {
        fontSize: 15,
        lineHeight: 20,
    },
    userText: {
        color: '#0f172a',
    },
    assistantText: {
        color: '#f1f5f9',
    },
    timestamp: {
        fontSize: 10,
        color: '#94a3b8',
        marginTop: 4,
        textAlign: 'right',
    },
    inputContainer: {
        flexDirection: 'row',
        padding: 12,
        borderTopWidth: 1,
        borderTopColor: '#334155',
        backgroundColor: '#1e293b',
        alignItems: 'flex-end',
    },
    input: {
        flex: 1,
        backgroundColor: '#0f172a',
        borderRadius: 20,
        paddingHorizontal: 16,
        paddingVertical: 10,
        fontSize: 15,
        color: '#f1f5f9',
        maxHeight: 100,
    },
    sendButton: {
        backgroundColor: '#10b981',
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: 8,
    },
    sendButtonDisabled: {
        opacity: 0.5,
    },
    sendButtonText: {
        color: '#0f172a',
        fontSize: 18,
    },
});
