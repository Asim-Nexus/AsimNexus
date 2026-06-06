/**
 * ASIMNEXUS Chat - Message Component
 * Individual message with actions, reactions, and markdown support
 */

import React, { memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { MessageSquare, Edit2, Pin, Trash2, Copy, Share2, Smile, Star, Zap } from 'lucide-react';
import '../../styles/glassmorphism.css';

const ChatMessage = ({
  msg,
  onReply,
  onEdit,
  onPin,
  onDelete,
  onCopy,
  onShare,
  onAddReaction,
  showEmojiPicker,
  setShowEmojiPicker,
  isUser,
}) => {
  const getRelativeTime = (timestamp) => {
    const now = new Date();
    const msgTime = new Date(timestamp);
    const diffMs = now - msgTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 8640000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return msgTime.toLocaleDateString();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className={`message ${msg.role}`}
    >
      <div className="message-content glass-card glass-noise">
        {msg.replyTo && (
          <div className="reply-indicator">
            <MessageSquare size={12} />
            <span>Replying to: {msg.replyTo.content}</span>
          </div>
        )}
        <div className="message-header">
          <div className="message-role">
            {msg.role === 'user' ? '👤 You' : '🤖 ASIMNEXUS'}
          </div>
          <div className="message-actions">
            <button className="action-button" onClick={() => onReply(msg.id)} title="Reply">
              <MessageSquare size={16} />
            </button>
            {isUser && (
              <button className="action-button" onClick={() => onEdit(msg.id)} title="Edit">
                <Edit2 size={16} />
              </button>
            )}
            <button className="action-button" onClick={() => onPin(msg.id)} title={msg.pinned ? 'Unpin' : 'Pin'}>
              <Pin size={16} className={msg.pinned ? 'pinned' : ''} />
            </button>
            {isUser && (
              <button className="action-button" onClick={() => onDelete(msg.id)} title="Delete">
                <Trash2 size={16} />
              </button>
            )}
            <button className="action-button" onClick={() => onCopy(msg.content)} title="Copy">
              <Copy size={16} />
            </button>
            <button className="action-button" onClick={() => onShare(msg.content)} title="Share">
              <Share2 size={16} />
            </button>
          </div>
        </div>

        <div className="message-text">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code: ({ node, inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                return !inline ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={language}
                    PreTag="pre"
                    className="code-block"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="inline-code" {...props}>
                    {children}
                  </code>
                );
              },
              a: ({ node, children, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            }}
          >
            {msg.content}
          </ReactMarkdown>
        </div>

        <div className="message-footer">
          <div className="message-time">
            {getRelativeTime(msg.timestamp)}
            {msg.edited && <span className="edited-indicator"> (edited)</span>}
          </div>
          {msg.priority === 'high' && (
            <div className="priority-indicator high">
              <Star size={12} />
              High
            </div>
          )}
          {msg.priority === 'urgent' && (
            <div className="priority-indicator urgent">
              <Zap size={12} />
              Urgent
            </div>
          )}

          <div className="message-reactions">
            {msg.reactions?.map((reaction, rIndex) => (
              <button
                key={rIndex}
                className="reaction-badge"
                onClick={() => onAddReaction(msg.id, reaction.emoji)}
              >
                {reaction.emoji} {reaction.count}
              </button>
            ))}
            <button
              className="add-reaction-button"
              onClick={() => setShowEmojiPicker(!showEmojiPicker)}
            >
              <Smile size={16} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default memo(ChatMessage);
