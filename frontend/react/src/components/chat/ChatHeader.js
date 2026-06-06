/**
 * ASIMNEXUS Chat - Header Component
 * Modular header with search, actions, and mode toggle
 */

import React, { memo } from 'react';
import { Search, MessageSquare, Users, Moon, Sun, Download, Bot, Key, Sparkles, CheckSquare } from 'lucide-react';
import { Button } from '../../design-system/components';
import '../../styles/glassmorphism.css';

const ChatHeader = ({
  isGroupChat,
  setIsGroupChat,
  darkMode,
  setDarkMode,
  onExport,
  onToggleAutopilot,
  autopilotMode,
  onApiKeys,
  onSummarize,
  onExtractTasks,
  searchQuery,
  setSearchQuery,
}) => {
  return (
    <div className={`chat-header ${darkMode ? 'dark' : 'light'} glass glass-noise`}>
      <div className="header-content">
        <div className="header-title">
          <h2>💬 {isGroupChat ? '👥 Company Group Chat' : 'Chat with ASIMNEXUS'}</h2>
          <p className="chat-subtitle">
            {isGroupChat ? 'Coordinate with 5 Optimized Founders' : 'Autonomous AI Company System'}
            {autopilotMode && <span className="autopilot-badge">🤖 AUTOPILOT</span>}
          </p>
        </div>
        <div className="header-actions">
          <Button
            variant={autopilotMode ? 'success' : 'secondary'}
            size="sm"
            onClick={onToggleAutopilot}
            icon={Bot}
          >
            {autopilotMode ? 'Autopilot ON' : 'Autopilot'}
          </Button>
          <Button variant="secondary" size="sm" onClick={onApiKeys} icon={Key}>
            API Keys
          </Button>
          <Button variant="secondary" size="sm" onClick={onSummarize} icon={Sparkles}>
            Summarize
          </Button>
          <Button variant="secondary" size="sm" onClick={onExtractTasks} icon={CheckSquare}>
            Tasks
          </Button>
          <button
            className="icon-button"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? 'Light Mode' : 'Dark Mode'}
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <button className="icon-button" onClick={onExport} title="Export Chat">
            <Download size={20} />
          </button>
          <button
            className={`mode-toggle ${isGroupChat ? 'group-chat' : 'direct-chat'}`}
            onClick={() => setIsGroupChat(!isGroupChat)}
          >
            {isGroupChat ? <MessageSquare size={20} /> : <Users size={20} />}
            {isGroupChat ? 'Direct Chat' : 'Group Chat'}
          </button>
        </div>
      </div>

      <div className="search-bar">
        <Search size={18} className="search-icon" />
        <input
          type="text"
          placeholder="Search messages... (Ctrl+K)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>
    </div>
  );
};

export default memo(ChatHeader);
