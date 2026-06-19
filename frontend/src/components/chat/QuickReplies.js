/**
 * ASIMNEXUS Chat - Quick Replies Component
 * Quick action buttons for common commands
 */

import React, { memo } from 'react';
import { Zap } from 'lucide-react';

const QuickReplies = ({ quickReplies, onSendQuickReply }) => {
  return (
    <div className="quick-replies">
      <span className="quick-reply-label">Quick Replies:</span>
      {quickReplies.map((reply, index) => (
        <button
          key={index}
          className="quick-reply-button"
          onClick={() => onSendQuickReply(reply)}
        >
          <Zap size={14} />
          {reply}
        </button>
      ))}
    </div>
  );
};

export default memo(QuickReplies);
