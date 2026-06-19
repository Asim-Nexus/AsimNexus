/**
 * ASIMNEXUS Chat - Input Component
 * Message input with file upload, voice recording, and emoji support
 */

import React, { memo } from 'react';
import { Send, Smile, Paperclip, Mic, X, FileText, CheckCheck, MessageSquare } from 'lucide-react';
import EmojiPicker from 'emoji-picker-react';
import '../../styles/glassmorphism.css';

const ChatInput = ({
  input,
  setInput,
  onSend,
  isLoading,
  editingMessage,
  onSaveEdit,
  onCancelEdit,
  onFileUpload,
  onToggleEmoji,
  showEmojiPicker,
  onStartRecording,
  onStopRecording,
  isRecording,
  uploadedFiles,
  onRemoveFile,
  replyingTo,
  onCancelReply,
  fileInputRef,
  emojiPickerRef,
}) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const files = Array.from(e.dataTransfer.files);
    onFileUpload({ target: { files } });
  };

  return (
    <div
      className="chat-input-container glass-panel glass-noise"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {replyingTo && (
        <div className="reply-preview">
          <div className="reply-preview-content">
            <MessageSquare size={14} />
            <span>Replying to: {replyingTo.content.slice(0, 50)}...</span>
          </div>
          <button className="cancel-reply-button" onClick={onCancelReply}>
            ✕
          </button>
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="file-preview">
          {uploadedFiles.map((file, index) => (
            <div key={index} className="file-item">
              <FileText size={16} />
              <span>{file.name}</span>
              <button onClick={() => onRemoveFile(index)}>
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="input-actions">
        <button
          className="action-icon-button"
          onClick={() => fileInputRef.current?.click()}
          title="Attach file"
        >
          <Paperclip size={20} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={onFileUpload}
        />
        <button
          className="action-icon-button"
          onClick={isRecording ? onStopRecording : onStartRecording}
          title={isRecording ? "Stop recording" : "Record voice"}
        >
          <Mic size={20} className={isRecording ? 'recording' : ''} />
        </button>
        <button
          className="emoji-button"
          onClick={onToggleEmoji}
          title="Add emoji"
        >
          <Smile size={20} />
        </button>
      </div>

      <textarea
        className="chat-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={editingMessage ? "Edit your message..." : "Type your message to ASIMNEXUS... (Markdown supported)"}
        rows={2}
        disabled={isLoading}
      />

      {editingMessage ? (
        <>
          <button className="cancel-button" onClick={onCancelEdit}>
            Cancel
          </button>
          <button className="send-button" onClick={onSaveEdit} disabled={!input.trim()}>
            <CheckCheck size={20} />
          </button>
        </>
      ) : (
        <button className="send-button" onClick={onSend} disabled={isLoading || !input.trim()}>
          {isLoading ? '...' : <Send size={20} />}
        </button>
      )}

      {showEmojiPicker && (
        <div className="emoji-picker-container" ref={emojiPickerRef}>
          <EmojiPicker onEmojiClick={(emojiObject) => setInput(prev => prev + emojiObject.emoji)} />
        </div>
      )}
    </div>
  );
};

export default memo(ChatInput);
