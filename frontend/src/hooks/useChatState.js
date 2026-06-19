/**
 * ASIMNEXUS Chat State Management Hook
 * Separates Local UI State from Server State
 * Following 2026 best practices for state management
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import toast from 'react-hot-toast';

export const useChatState = () => {
  // Local UI State (component-level, ephemeral)
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGroupChat, setIsGroupChat] = useState(false);
  const [selectedFounders, setSelectedFounders] = useState([]);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [typingIndicator, setTypingIndicator] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [editingMessage, setEditingMessage] = useState(null);
  const [replyingTo, setReplyingTo] = useState(null);
  const [showSummary, setShowSummary] = useState(false);
  const [chatSummary, setChatSummary] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [autopilotMode, setAutopilotMode] = useState(false);
  const [showAutopilotPanel, setShowAutopilotPanel] = useState(false);
  const [autonomousStatus, setAutonomousStatus] = useState(null);

  // Server State (data from backend, should be cached)
  const [messages, setMessages] = useState([
    {
      id: 'msg_0',
      role: 'asimnexus',
      content: '🚀 **Welcome to ASIMNEXUS!** I am your autonomous AI company system with 5 optimized founder clones (consolidated from 15). Type `/help` to see all commands, or just ask me anything!\n\n👑 **CEO Strategy** | 💻 **CTO Innovation** | 💰 **CFO Operations** | 📈 **CPO Market** | 📊 **CDO Analytics**\n\n🤖 Enable **Autopilot** for 24/7 autonomous operation!',
      timestamp: new Date().toISOString(),
      reactions: [],
      pinned: false,
      edited: false,
      priority: 'normal'
    }
  ]);
  const [filteredMessages, setFilteredMessages] = useState([]);

  // Refs
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const emojiPickerRef = useRef(null);

  // Derived state
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (searchQuery) {
      const filtered = messages.filter(msg =>
        msg.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredMessages(filtered);
    } else {
      setFilteredMessages(messages);
    }
  }, [searchQuery, messages]);

  // Actions
  const addReaction = useCallback((messageId, emoji) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const existingReaction = msg.reactions?.find(r => r.emoji === emoji);
        if (existingReaction) {
          return {
            ...msg,
            reactions: msg.reactions.map(r =>
              r.emoji === emoji ? { ...r, count: r.count + 1 } : r
            )
          };
        } else {
          return {
            ...msg,
            reactions: [...(msg.reactions || []), { emoji, count: 1 }]
          };
        }
      }
      return msg;
    }));
    toast.success(`Added ${emoji} reaction`);
  }, []);

  const editMessage = useCallback((messageId) => {
    const message = messages.find(m => m.id === messageId);
    if (message && message.role === 'user') {
      setEditingMessage(messageId);
      setInput(message.content);
    }
  }, [messages, setInput]);

  const saveEdit = useCallback(() => {
    if (editingMessage) {
      setMessages(prev => prev.map(msg => 
        msg.id === editingMessage 
          ? { ...msg, content: input, edited: true }
          : msg
      ));
      setEditingMessage(null);
      setInput('');
    }
  }, [editingMessage, input, setInput]);

  const deleteMessage = useCallback((messageId) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  }, []);

  const pinMessage = useCallback((messageId) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, pinned: !msg.pinned }
        : msg
    ));
  }, []);

  const setPriority = useCallback((messageId, priority) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, priority }
        : msg
    ));
  }, []);

  const replyToMessage = useCallback((messageId) => {
    const message = messages.find(m => m.id === messageId);
    if (message) {
      setReplyingTo(message);
      setInput('');
      document.querySelector('.chat-input')?.focus();
    }
  }, [messages, setInput]);

  const cancelReply = useCallback(() => {
    setReplyingTo(null);
  }, []);

  const handleFileUpload = useCallback((e) => {
    const files = Array.from(e.target.files);
    setUploadedFiles([...uploadedFiles, ...files]);
  }, [uploadedFiles]);

  const removeFile = useCallback((index) => {
    setUploadedFiles(uploadedFiles.filter((_, i) => i !== index));
  }, [uploadedFiles]);

  const startRecording = useCallback(() => {
    setIsRecording(true);
  }, []);

  const stopRecording = useCallback(() => {
    setIsRecording(false);
  }, []);

  const toggleAutopilot = useCallback(() => {
    setAutopilotMode(!autopilotMode);
  }, [autopilotMode]);

  const quickReplies = [
    "/founders",
    "/status",
    "/autopilot on",
    "/keys",
    "/help"
  ];

  const sendQuickReply = useCallback((reply) => {
    setInput(reply);
  }, [setInput]);

  return {
    // State
    input,
    setInput,
    isLoading,
    setIsLoading,
    isGroupChat,
    setIsGroupChat,
    selectedFounders,
    setSelectedFounders,
    showEmojiPicker,
    setShowEmojiPicker,
    searchQuery,
    setSearchQuery,
    typingIndicator,
    setTypingIndicator,
    darkMode,
    setDarkMode,
    editingMessage,
    setEditingMessage,
    replyingTo,
    setReplyingTo,
    showSummary,
    setShowSummary,
    chatSummary,
    setChatSummary,
    isRecording,
    setIsRecording,
    uploadedFiles,
    setUploadedFiles,
    autopilotMode,
    setAutopilotMode,
    showAutopilotPanel,
    setShowAutopilotPanel,
    autonomousStatus,
    setAutonomousStatus,
    messages,
    setMessages,
    filteredMessages,
    
    // Refs
    fileInputRef,
    messagesEndRef,
    emojiPickerRef,
    
    // Actions
    addReaction,
    editMessage,
    saveEdit,
    deleteMessage,
    pinMessage,
    setPriority,
    replyToMessage,
    cancelReply,
    handleFileUpload,
    removeFile,
    startRecording,
    stopRecording,
    toggleAutopilot,
    quickReplies,
    sendQuickReply,
    scrollToBottom,
  };
};

export default useChatState;
