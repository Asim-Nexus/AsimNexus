/**
 * Local LLM Chat Component (Gemma 2 Integration)
 * 
 * Features:
 * - Connects to local Gemma 2 model via API
 * - Real-time chat interface
 * - Model selection (Gemma, Llama, Mistral)
 * - System info display
 * - Action execution (create folder, etc.)
 */

import React, { useState, useEffect, useRef } from 'react';
import { asimnexusAPI } from '../../api/asimnexus';

const LocalLLMChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gemma-2-2b-it');
  const [availableModels, setAvailableModels] = useState([]);
  const [systemInfo, setSystemInfo] = useState(null);
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load available models on mount
  useEffect(() => {
    loadModels();
    loadSystemInfo();
  }, []);

  const loadModels = async () => {
    try {
      const response = await asimnexusAPI.getModels();
      if (response.data) {
        setAvailableModels(response.data.models || []);
        // Set Gemma as default if available
        if (response.data.active_model) {
          setSelectedModel(response.data.active_model);
        }
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const loadSystemInfo = async () => {
    try {
      const response = await asimnexusAPI.getSystemInfo();
      if (response.data) {
        setSystemInfo(response.data);
      }
    } catch (error) {
      console.error('Failed to load system info:', error);
    }
  };

  // Check if message is an action command
  const detectAction = (message) => {
    const lowerMsg = message.toLowerCase();

    // Create folder patterns
    if (lowerMsg.includes('create folder') || lowerMsg.includes('make folder') ||
      lowerMsg.includes('new folder') || lowerMsg.includes('बनाउ')) {
      const folderName = message.match(/(?:folder|directory)\s+(?:named\s+)?['"]?([^'"\n]+)['"]?/i)?.[1] ||
        message.match(/(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:folder|directory)\s+(?:called\s+)?['"]?([^'"\n]+)['"]?/i)?.[1];
      return { type: 'create_folder', data: folderName || 'new_folder' };
    }

    // Create file patterns
    if (lowerMsg.includes('create file') || lowerMsg.includes('make file') ||
      lowerMsg.includes('new file') || lowerMsg.includes('file बनाउ')) {
      const fileName = message.match(/(?:file)\s+(?:named\s+)?['"]?([^'"\n]+)['"]?/i)?.[1] ||
        message.match(/(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:file)\s+(?:called\s+)?['"]?([^'"\n]+)['"]?/i)?.[1];
      return { type: 'create_file', data: fileName || 'new_file.txt' };
    }

    // List directory
    if (lowerMsg.includes('list files') || lowerMsg.includes('show files') ||
      lowerMsg.includes('what files') || lowerMsg.includes('फाइलहरू देखाउ')) {
      return { type: 'list_directory', data: '.' };
    }

    // System info
    if (lowerMsg.includes('system info') || lowerMsg.includes('computer info') ||
      lowerMsg.includes('cpu ram') || lowerMsg.includes('सिस्टम जानकारी')) {
      return { type: 'system_info', data: null };
    }

    return null;
  };

  // Execute action
  const executeAction = async (action) => {
    try {
      switch (action.type) {
        case 'create_folder':
          const folderResult = await asimnexusAPI.createFolder(action.data);
          return `✅ Folder "${action.data}" created successfully!\nPath: ${folderResult.data?.path || action.data}`;

        case 'create_file':
          const fileResult = await asimnexusAPI.createFile(action.data, '');
          return `✅ File "${action.data}" created successfully!\nPath: ${fileResult.data?.path || action.data}`;

        case 'list_directory':
          const dirResult = await asimnexusAPI.listDirectory(action.data);
          const items = dirResult.data?.items || [];
          const fileList = items.map(item => `${item.type === 'directory' ? '📁' : '📄'} ${item.name}`).join('\n');
          return `📂 Directory contents:\n${fileList || 'No items found'}`;

        case 'system_info':
          const sysResult = await asimnexusAPI.getSystemInfo();
          const sys = sysResult.data;
          return `💻 System Info:
• Platform: ${sys?.platform?.system} ${sys?.platform?.release}
• CPU: ${sys?.cpu?.count} cores (${sys?.cpu?.usage_percent}% usage)
• RAM: ${sys?.memory?.used_gb}/${sys?.memory?.total_gb} GB (${sys?.memory?.usage_percent}%)
• Disk: ${sys?.disk?.used_gb}/${sys?.disk?.total_gb} GB (${sys?.disk?.usage_percent}% used)`;

        default:
          return null;
      }
    } catch (error) {
      console.error('Action execution failed:', error);
      return `❌ Failed to execute action: ${error.response?.data?.detail || error.message}`;
    }
  };

  // Handle sending message
  const handleSend = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // First, check if this is an action command
      const action = detectAction(inputMessage);

      if (action) {
        // Execute action
        const actionResult = await executeAction(action);

        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: actionResult,
          isAction: true,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Regular chat with LLM
        let response;

        // Use Gemma endpoint for Gemma model
        if (selectedModel === 'gemma-2-2b-it') {
          response = await asimnexusAPI.generateGemma(inputMessage, 512);
        } else {
          // Use general endpoint for other models
          response = await asimnexusAPI.generate(inputMessage, selectedModel, 512);
        }

        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.data?.text || 'Sorry, I could not generate a response.',
          model: response.data?.model_used || selectedModel,
          tokens: response.data?.tokens_generated || response.data?.tokens,
          timeMs: response.data?.generation_time_ms || response.data?.time_ms,
          timestamp: new Date().toLocaleTimeString()
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message || 'Failed to get response from local LLM.'}`,
        isError: true,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Clear chat
  const clearChat = () => {
    setMessages([]);
  };

  // Quick action buttons
  const quickActions = [
    { label: '📁 New Folder', text: 'Create a folder named Projects' },
    { label: '📄 New File', text: 'Create a file named notes.txt' },
    { label: '📂 List Files', text: 'List files in current directory' },
    { label: '💻 System Info', text: 'Show system information' },
  ];

  return (
    <div className="agi-chat">
      <div className="chat-header">
        <h3>🧠 Local LLM Chat (Gemma 2)</h3>
        <div className="header-controls">
          {/* Model Selector */}
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="reasoning-selector"
          >
            <option value="gemma-2-2b-it">Gemma 2 2B (Local)</option>
            {availableModels.map((model) => (
              <option key={model.id || model.name} value={model.id || model.name}>
                {model.name}
              </option>
            ))}
          </select>

          {/* System Info Toggle */}
          <button
            onClick={() => setShowSystemInfo(!showSystemInfo)}
            className="clear-btn"
            title="Toggle System Info"
          >
            💻
          </button>

          <button onClick={clearChat} className="clear-btn">
            Clear
          </button>
        </div>
      </div>

      {/* System Info Panel */}
      {showSystemInfo && systemInfo && (
        <div className="system-info-panel" style={{
          background: '#1a1a2e',
          padding: '10px 15px',
          borderBottom: '1px solid #333',
          fontSize: '12px',
          color: '#aaa'
        }}>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <span>💻 {systemInfo.platform?.system} {systemInfo.platform?.release}</span>
            <span>🖥️ {systemInfo.cpu?.count} Cores ({systemInfo.cpu?.usage_percent}%)</span>
            <span>🧠 {systemInfo.memory?.used_gb}/{systemInfo.memory?.total_gb} GB RAM</span>
            <span>💾 {systemInfo.disk?.free_gb} GB Free</span>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="quick-actions" style={{
        padding: '10px 15px',
        borderBottom: '1px solid #333',
        display: 'flex',
        gap: '10px',
        flexWrap: 'wrap'
      }}>
        {quickActions.map((action, idx) => (
          <button
            key={idx}
            onClick={() => {
              setInputMessage(action.text);
            }}
            style={{
              padding: '5px 12px',
              fontSize: '12px',
              background: '#2a2a4a',
              border: '1px solid #444',
              borderRadius: '15px',
              color: '#fff',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.background = '#3a3a6a'}
            onMouseLeave={(e) => e.target.style.background = '#2a2a4a'}
          >
            {action.label}
          </button>
        ))}
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="agi-icon">🤖</div>
            <p>Welcome to Local LLM Chat</p>
            <p className="hint">Chat with Gemma 2 (local, no internet needed!)</p>
            <p className="hint">Try: "Create a folder named Projects" or "What is Nepal famous for?"</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={message.id || index}
            className={`message ${message.role === 'user' ? 'user-message' : 'agi-message'}`}
          >
            <div className="message-header">
              <span className="role-badge">
                {message.role === 'user' ? '👤 You' : message.isAction ? '🛠️ Action' : '🤖 Gemma'}
              </span>
              <span className="timestamp">{message.timestamp}</span>
              {message.model && (
                <span style={{ fontSize: '10px', color: '#888', marginLeft: '10px' }}>
                  {message.model} • {message.tokens} tokens • {message.timeMs}ms
                </span>
              )}
            </div>
            <div className="message-content" style={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message agi-message streaming">
            <div className="message-header">
              <span className="role-badge">🤖 Gemma</span>
              <span className="timestamp">{new Date().toLocaleTimeString()}</span>
              <span className="streaming-indicator">
                <span className="dot">.</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
              </span>
            </div>
            <div className="message-content">
              Thinking... (using {selectedModel})
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Chat with Gemma 2 or type commands like 'Create folder Projects'..."
            disabled={isLoading}
            rows={2}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !inputMessage.trim()}
            className="send-btn"
          >
            {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </div>
        <div className="input-hint">
          Press Enter to send • Shift+Enter for new line • Try: create folder, list files, system info
        </div>
      </div>
    </div>
  );
};

export default LocalLLMChat;
