/**
 * ASIMNEXUS Streaming Chat Hook
 * ==============================
 * Handles real-time streaming responses from backend via fetch + ReadableStream.
 */

import { useState, useCallback, useRef } from 'react';
import { getStoredToken } from '../api/asimnexus';

interface UseStreamingChatReturn {
    isStreaming: boolean;
    streamedContent: string;
    currentMessageId: string | null;
    startStreaming: (
        message: string,
        user_id?: string,
        onChunk?: (content: string) => void,
        onComplete?: (content: string) => void,
        onError?: (error: Error) => void
    ) => Promise<string>;
    stopStreaming: () => void;
}

export const useStreamingChat = (): UseStreamingChatReturn => {
    const [isStreaming, setIsStreaming] = useState<boolean>(false);
    const [streamedContent, setStreamedContent] = useState<string>('');
    const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    const startStreaming = useCallback(async (
        message: string,
        user_id: string = 'web_user',
        onChunk?: (content: string) => void,
        onComplete?: (content: string) => void,
        onError?: (error: Error) => void
    ): Promise<string> => {
        try {
            setIsStreaming(true);
            setStreamedContent('');
            setCurrentMessageId(null);

            // Create new AbortController for this request
            abortControllerRef.current = new AbortController();

            const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const token = getStoredToken();
            const response = await fetch(`${API_BASE}/api/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` }),
                },
                body: JSON.stringify({ message, user_id }),
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body!.getReader();
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
        } catch (error: unknown) {
            setIsStreaming(false);
            if (error instanceof Error && error.name === 'AbortError') {
                console.log('Streaming aborted');
            } else {
                console.error('Streaming error:', error);
                if (onError && error instanceof Error) {
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
