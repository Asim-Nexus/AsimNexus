/**
 * AsimOrb — Universal Floating Interface
 * System-wide glowing orb that expands to full chat
 * Context-aware, voice-ready, quantum-inspired
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, X, Send, Maximize2, Minimize2, MessageSquare, Zap } from 'lucide-react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Voice waveform visualization component
const WaveformVisualizer = ({ isListening }) => {
  const [bars, setBars] = useState(Array(20).fill(5));
  
  useEffect(() => {
    if (!isListening) {
      setBars(Array(20).fill(5));
      return;
    }
    
    const interval = setInterval(() => {
      setBars(Array(20).fill(0).map(() => Math.random() * 30 + 5));
    }, 100);
    
    return () => clearInterval(interval);
  }, [isListening]);
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 2, height: 40 }}>
      {bars.map((h, i) => (
        <div
          key={i}
          style={{
            width: 3,
            height: h,
            background: `linear-gradient(to top, #667eea, #764ba2)`,
            borderRadius: 2,
            transition: 'height 0.1s ease',
          }}
        />
      ))}
    </div>
  );
};

// Suggestion chips
const SUGGESTIONS = [
  { icon: '🏥', text: 'Health check', action: 'health' },
  { icon: '💼', text: 'Work mode', action: 'work' },
  { icon: '🌐', text: 'Mesh status', action: 'mesh' },
  { icon: '🤖', text: 'Hire agent', action: 'agent' },
];

export default function AsimOrb({ user, onCommand }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { type: 'system', text: '👋 Namaste! I am Asim. How can I help you today?' }
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [pulsePhase, setPulsePhase] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Glowing pulse animation
  useEffect(() => {
    const interval = setInterval(() => {
      setPulsePhase(p => (p + 1) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', text: userMsg }]);
    setIsTyping(true);
    
    // Simulate AI response (replace with real API call)
    setTimeout(() => {
      let response = '';
      
      // Simple command detection
      const lower = userMsg.toLowerCase();
      if (lower.includes('health') || lower.includes('swasthya')) {
        response = '🏥 Health Dashboard:\n• BP: 120/80 (Normal)\n• Heart Rate: 72 bpm\n• Sleep: 7.5 hours\n• Steps today: 8,432\n\nRecommendation: Great job! Keep maintaining this routine.';
      } else if (lower.includes('work') || lower.includes('company') || lower.includes('office')) {
        response = '💼 Switching to Enterprise Mode...\n\nToday\'s Summary:\n• 3 active contracts\n• 2 pending approvals\n• Revenue: $12,500\n• AI Agents working: 2/5';
      } else if (lower.includes('agent') || lower.includes('clone') || lower.includes('hire')) {
        response = '🤖 Available Agents:\n1. 🧙‍♂️ Wizard — Coding expert ($50/day)\n2. 🥷 Rogue — Data analysis ($40/day)\n3. ⚔️ Knight — Writing ($35/day)\n\nUse command: /hire [agent-name] [days]';
      } else if (lower.includes('mesh') || lower.includes('network') || lower.includes('p2p')) {
        response = '🌐 Mesh Network Status:\n• Your Device: Online (0ms)\n• 3 neighbors connected\n• Signal strength: Strong\n• Data shared today: 45 MB\n• Offline mode: Ready';
      } else if (lower.includes('dharma') || lower.includes('balance') || lower.includes('fair')) {
        response = '⚖️ Dharma ΔT Status:\n• Current Symmetry: 94.2%\n• Gini Coefficient: 0.32 (Good)\n• Last Veto: None\n• Your Contribution: +12 ΔT today\n• System Balance: Healthy ✅';
      } else if (lower.includes('help') || lower.includes('?')) {
        response = '🎯 Available Commands:\n• "Health check" — View health data\n• "Work mode" — Switch to Enterprise\n• "Hire agent" — Browse AI agents\n• "Mesh status" — Network info\n• "Dharma status" — System balance\n\nOr just ask anything naturally!';
      } else {
        response = `🤔 I understood: "${userMsg}"\n\nLet me process this through AsimBrain...\n\n[This would connect to your local LLM or the Unified Brain for real processing]\n\nQuick actions available below ↓`;
      }
      
      setMessages(prev => [...prev, { type: 'ai', text: response }]);
      setIsTyping(false);
      
      // Call parent handler if provided
      if (onCommand) {
        onCommand(userMsg);
      }
    }, 1500);
  }, [input, onCommand]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === 'Escape') {
      if (isExpanded) {
        setIsExpanded(false);
      } else {
        setIsOpen(false);
      }
    }
  };

  // Voice toggle
  const toggleVoice = () => {
    setIsListening(!isListening);
    if (!isListening) {
      // Simulate voice input
      setTimeout(() => {
        setIsListening(false);
        setInput('Health check please');
      }, 3000);
    }
  };

  // Quick action handler
  const handleQuickAction = (action) => {
    const texts = {
      health: 'Health check',
      work: 'Switch to work mode',
      mesh: 'Mesh network status',
      agent: 'Show available agents',
    };
    setInput(texts[action]);
    setTimeout(() => handleSend(), 100);
  };

  // Format message with line breaks
  const formatMessage = (text) => {
    return text.split('\n').map((line, i) => (
      <div key={i} style={{ marginBottom: 4 }}>{line}</div>
    ));
  };

  // Pulse glow effect
  const glowIntensity = 0.5 + Math.sin(pulsePhase * Math.PI / 180) * 0.3;

  return (
    <>
      {/* Floating Orb */}
      {!isOpen && (
        <div
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: `linear-gradient(135deg, 
              rgba(102, 126, 234, ${glowIntensity}), 
              rgba(118, 75, 162, ${glowIntensity}))`,
            boxShadow: `0 0 ${30 + glowIntensity * 20}px rgba(102, 126, 234, ${glowIntensity}),
                        0 0 ${60 + glowIntensity * 40}px rgba(102, 126, 234, ${glowIntensity * 0.5})`,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            transition: 'transform 0.3s ease, box-shadow 0.3s ease',
            transform: `scale(${1 + glowIntensity * 0.1})`,
            backdropFilter: 'blur(10px)',
            border: '2px solid rgba(255,255,255,0.2)',
          }}
        >
          <Zap size={28} color="white" fill="white" />
          
          {/* Unread badge */}
          {unreadCount > 0 && (
            <div style={{
              position: 'absolute',
              top: -4,
              right: -4,
              width: 22,
              height: 22,
              borderRadius: '50%',
              background: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 12,
              fontWeight: 700,
              color: 'white',
            }}>
              {unreadCount}
            </div>
          )}
        </div>
      )}

      {/* Expanded Chat Interface */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: 20,
            right: 20,
            width: isExpanded ? 480 : 360,
            height: isExpanded ? 600 : 500,
            background: 'rgba(10, 10, 26, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 20,
            border: '1px solid rgba(102, 126, 234, 0.3)',
            boxShadow: '0 25px 50px rgba(0,0,0,0.5), 0 0 100px rgba(102, 126, 234, 0.1)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            animation: 'orbExpand 0.3s ease',
          }}
        >
          {/* Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
            background: 'linear-gradient(90deg, rgba(102,126,234,0.1), transparent)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Zap size={18} color="white" />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#fff' }}>Asim</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>
                  {isTyping ? 'Thinking...' : 'Universal Assistant'}
                </div>
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: 8,
                  padding: 8,
                  cursor: 'pointer',
                  color: 'white',
                }}
              >
                {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: 8,
                  padding: 8,
                  cursor: 'pointer',
                  color: 'white',
                }}
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  padding: '12px 16px',
                  borderRadius: msg.type === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  background: msg.type === 'user' 
                    ? 'linear-gradient(135deg, #667eea, #764ba2)' 
                    : msg.type === 'system'
                    ? 'rgba(16, 185, 129, 0.15)'
                    : 'rgba(255,255,255,0.08)',
                  color: '#fff',
                  fontSize: 13,
                  lineHeight: 1.5,
                  border: msg.type === 'system' ? '1px solid rgba(16,185,129,0.3)' : 'none',
                }}
              >
                {formatMessage(msg.text)}
              </div>
            ))}
            
            {isTyping && (
              <div style={{
                alignSelf: 'flex-start',
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.08)',
                borderRadius: '16px 16px 16px 4px',
                display: 'flex',
                gap: 4,
                alignItems: 'center',
              }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#667eea', animation: 'bounce 0.6s infinite' }} />
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#667eea', animation: 'bounce 0.6s infinite 0.2s' }} />
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#667eea', animation: 'bounce 0.6s infinite 0.4s' }} />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div style={{
            display: 'flex',
            gap: 8,
            padding: '8px 16px',
            overflowX: 'auto',
            borderTop: '1px solid rgba(255,255,255,0.05)',
          }}>
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => handleQuickAction(s.action)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 16,
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: 12,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(102,126,234,0.2)';
                  e.target.style.borderColor = 'rgba(102,126,234,0.4)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.05)';
                  e.target.style.borderColor = 'rgba(255,255,255,0.1)';
                }}
              >
                <span>{s.icon}</span>
                <span>{s.text}</span>
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div style={{
            padding: '12px 16px',
            borderTop: '1px solid rgba(255,255,255,0.08)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}>
            {/* Voice Visualizer */}
            {isListening && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '8px 0',
              }}>
                <WaveformVisualizer isListening={isListening} />
              </div>
            )}
            
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button
                onClick={toggleVoice}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  background: isListening 
                    ? 'linear-gradient(135deg, #ef4444, #dc2626)' 
                    : 'rgba(255,255,255,0.1)',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  transition: 'all 0.2s',
                }}
              >
                <Mic size={18} />
              </button>
              
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isListening ? 'Listening...' : 'Ask Asim anything...'}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 24,
                  color: 'white',
                  fontSize: 14,
                  outline: 'none',
                }}
              />
              
              <button
                onClick={handleSend}
                disabled={!input.trim() && !isListening}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  background: input.trim() || isListening
                    ? 'linear-gradient(135deg, #667eea, #764ba2)' 
                    : 'rgba(255,255,255,0.1)',
                  border: 'none',
                  cursor: input.trim() || isListening ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  transition: 'all 0.2s',
                }}
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Animations */}
      <style>{`
        @keyframes orbExpand {
          from {
            opacity: 0;
            transform: scale(0.8) translateY(20px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </>
  );
}
