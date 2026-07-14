/**
 * ChatContext.tsx
 * Shared chat state for ALL chat instances (popup + full page)
 */
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface ChatMessage {
    id: string;
    role: string;
    content: string;
    ts: number;
}

interface CloneOption {
    id: string;
    icon: string;
    name: string;
    color: string;
}

interface ChatContextValue {
    messages: ChatMessage[];
    setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
    addMessage: (msg: ChatMessage) => void;
    loading: boolean;
    updateLoading: (val: boolean) => void;
    selectedClone: CloneOption;
    setSelectedClone: React.Dispatch<React.SetStateAction<CloneOption>>;
    clearMessages: () => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

const WELCOME_MESSAGE: ChatMessage = {
    id: 'welcome',
    role: 'assistant',
    content: `👋 **Namaste! Welcome to AsimNexus Chat**

म तपाईंको AI सहयोगी Asim हुँ। म यसमा मद्दत गर्न सक्छु:
• 🏥 **Health** — "Health check"
• 💼 **Work** — "Work status"
• 🤖 **Agents** — "Hire agent"
• 🌐 **Mesh** — "Mesh info"
• ⚖️ **Governance** — "Dharma balance"
• 💰 **Wallet** — "Check balance"
• 📊 **System** — "Show status"

Type **/help** for commands or ask anything!`,
    ts: Date.now()
};

interface ChatProviderProps {
    children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
    const [messages, setMessages] = useState<ChatMessage[]>(() => {
        try {
            const saved = sessionStorage.getItem('asim_chat_messages');
            return saved ? JSON.parse(saved) : [WELCOME_MESSAGE];
        } catch {
            return [WELCOME_MESSAGE];
        }
    });
    const [loading, setLoading] = useState<boolean>(false);
    const [selectedClone, setSelectedClone] = useState<CloneOption>({
        id: 'auto', icon: '🌌', name: 'Auto (Smart Route)', color: '#667eea'
    });

    const addMessage = useCallback((msg: ChatMessage) => {
        setMessages(prev => {
            const next = [...prev, msg];
            try {
                sessionStorage.setItem('asim_chat_messages', JSON.stringify(next));
            } catch { /* ignore quota errors */ }
            return next;
        });
    }, []);

    const updateLoading = useCallback((val: boolean) => setLoading(val), []);

    const clearMessages = useCallback(() => {
        const fresh = [WELCOME_MESSAGE];
        setMessages(fresh);
        try {
            sessionStorage.setItem('asim_chat_messages', JSON.stringify(fresh));
        } catch { /* ignore quota errors */ }
    }, []);

    const value: ChatContextValue = {
        messages,
        setMessages,
        addMessage,
        loading,
        updateLoading,
        selectedClone,
        setSelectedClone,
        clearMessages
    };

    return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChatContext(): ChatContextValue {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChatContext must be used within ChatProvider');
    }
    return context;
}
