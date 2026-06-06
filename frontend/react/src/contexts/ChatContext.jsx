/**
 * ChatContext.jsx
 * Shared chat state for ALL chat instances (popup + full page)
 */
import React, { createContext, useContext, useState, useCallback } from 'react';

const ChatContext = createContext(null);

const WELCOME_MESSAGE = {
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

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = sessionStorage.getItem('asim_chat_messages');
      return saved ? JSON.parse(saved) : [WELCOME_MESSAGE];
    } catch {
      return [WELCOME_MESSAGE];
    }
  });
  const [loading, setLoading] = useState(false);
  const [selectedClone, setSelectedClone] = useState({
    id: 'auto', icon: '🌌', name: 'Auto (Smart Route)', color: '#667eea'
  });

  const addMessage = useCallback((msg) => {
    setMessages(prev => {
      const next = [...prev, msg];
      try {
        sessionStorage.setItem('asim_chat_messages', JSON.stringify(next));
      } catch {}
      return next;
    });
  }, []);

  const updateLoading = useCallback((val) => setLoading(val), []);

  const clearMessages = useCallback(() => {
    const fresh = [WELCOME_MESSAGE];
    setMessages(fresh);
    try {
      sessionStorage.setItem('asim_chat_messages', JSON.stringify(fresh));
    } catch {}
  }, []);

  const value = {
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

export function useChatContext() {
  return useContext(ChatContext);
}
