// components/common/VoiceInput.tsx
// Web Speech API voice-to-text toggle button

import { useState, useEffect, useRef, useCallback } from 'react';

interface VoiceInputProps {
    onTranscript: (text: string) => void;
    disabled?: boolean;
}

declare global {
    interface Window {
        SpeechRecognition?: new () => SpeechRecognition;
        webkitSpeechRecognition?: new () => SpeechRecognition;
    }
}

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start: () => void;
    stop: () => void;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    onerror: ((event: Event) => void) | null;
    onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
    results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
    length: number;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
    [index: number]: SpeechRecognitionAlternative;
    isFinal: boolean;
    length: number;
}

interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
}

export default function VoiceInput({ onTranscript, disabled }: VoiceInputProps) {
    const [listening, setListening] = useState<boolean>(false);
    const [supported, setSupported] = useState<boolean>(false);
    const recognitionRef = useRef<SpeechRecognition | null>(null);

    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            setSupported(true);
            const rec = new SpeechRecognition();
            rec.continuous = false;
            rec.interimResults = false;
            rec.lang = 'ne-NP'; // Nepali first, fallback below
            rec.onresult = (e: SpeechRecognitionEvent) => {
                const transcript = Array.from(e.results)
                    .map(r => r[0].transcript)
                    .join('');
                onTranscript(transcript);
                setListening(false);
            };
            rec.onerror = () => setListening(false);
            rec.onend = () => setListening(false);
            recognitionRef.current = rec;
        }
    }, [onTranscript]);

    const toggle = useCallback(() => {
        if (!recognitionRef.current) return;
        if (listening) {
            recognitionRef.current.stop();
        } else {
            recognitionRef.current.start();
            setListening(true);
        }
    }, [listening]);

    if (!supported) return null;

    return (
        <button
            onClick={toggle}
            disabled={disabled}
            title={listening ? 'Stop listening' : 'Voice input'}
            aria-label={listening ? 'Stop recording' : 'Start voice input'}
            style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                border: `2px solid ${listening ? '#ef4444' : 'rgba(139,92,246,0.4)'}`,
                background: listening
                    ? 'rgba(239,68,68,0.15)'
                    : 'rgba(139,92,246,0.1)',
                color: listening ? '#ef4444' : '#a78bfa',
                fontSize: '18px',
                cursor: disabled ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                outline: 'none',
                animation: listening ? 'mic-pulse 1s ease-in-out infinite' : 'none',
                flexShrink: 0,
            }}
        >
            {listening ? '⏹' : '🎤'}
            <style>{`
        @keyframes mic-pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
          50% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
        }
      `}</style>
        </button>
    );
}
