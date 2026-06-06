/**
 * ASIMNEXUS Streaming Chat Hook
 * Handles real-time streaming responses from backend
 * Following 2026 best practices for streaming chat UI
 */

import { useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../api/unified_api';

export const useStreamingChat = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState('');
  const [currentMessageId, setCurrentMessageId] = useState(null);
  const abortControllerRef = useRef(null);

  const startStreaming = useCallback(async (message, user_id = 'web_user', onChunk, onComplete, onError) => {
    try {
      setIsStreaming(true);
      setStreamedContent('');
      setCurrentMessageId(null);
      
      // Create new AbortController for this request
      abortControllerRef.current = new AbortController();
      
      const response = await fetch(`${API_BASE_URL || ''}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, user_id }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        accumulatedContent += chunk;
        setStreamedContent(accumulatedContent);
        
        if (onChunk) {
          onChunk(accumulatedContent);
        }
      }

      setIsStreaming(false);
      
      if (onComplete) {
        onComplete(accumulatedContent);
      }
      
      return accumulatedContent;
    } catch (error) {
      setIsStreaming(false);
      if (error.name === 'AbortError') {
        console.log('Streaming aborted');
      } else {
        console.error('Streaming error:', error);
        if (onError) {
          onError(error);
        }
      }
      throw error;
    }
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  return {
    isStreaming,
    streamedContent,
    currentMessageId,
    startStreaming,
    stopStreaming,
  };
};

export default useStreamingChat;
