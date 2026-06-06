/**
 * ASIMNEXUS Chat - Suggestions Component
 * Suggested prompts for new users
 */

import React, { memo } from 'react';

const ChatSuggestions = ({ suggestions, onSuggestionClick }) => {
  return (
    <div className="chat-suggestions">
      <span className="suggestion-label">Try:</span>
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="suggestion-button"
          onClick={() => onSuggestionClick(suggestion.text)}
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
};

export default memo(ChatSuggestions);
