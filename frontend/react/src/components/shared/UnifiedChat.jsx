/**
 * UnifiedChat.jsx
 * ============
 * One chat component for ALL contexts:
 * - UniversalChat (full page /chat)
 * - AsimOrb (floating popup)
 * - Any future chat needs
 * 
 * Features: Context awareness, Clones, Voice, Files, Streaming,
 *           Smart suggestions, Slash commands, Gestures
 */
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Mic, X, Send, Paperclip, Search, Sparkles, Camera, Zap } from 'lucide-react';
import contextService from '../../services/ContextAwarenessService';
import asimBrain from '../../services/AsimBrainService';
import gestureService from '../../services/GestureService';
import { nativeBridge } from '../../native/NativeBridge';
import { useChatContext } from '../../contexts/ChatContext';

// 🤖 15 Clones (from UniversalChat)
const CLONES = [
  { id: 'auto',    icon: '🌌', name: 'Auto (Smart Route)', color: '#667eea' },
  { id: 'tech',    icon: '💻', name: 'Tech Architect', color: '#3b82f6' },
  { id: 'health',  icon: '🏥', name: 'Health Sage', color: '#22c55e' },
  { id: 'finance', icon: '💰', name: 'Financial Oracle', color: '#f59e0b' },
  { id: 'legal',   icon: '⚖️', name: 'Legal Guardian', color: '#8b5cf6' },
  { id: 'edu',     icon: '📚', name: 'Education Mentor', color: '#ec4899' },
  { id: 'creative',icon: '🎨', name: 'Creative Muse', color: '#f97316' },
  { id: 'strategy',icon: '🎯', name: 'Strategic Planner', color: '#06b6d4' },
  { id: 'science', icon: '🔬', name: 'Research Explorer', color: '#14b8a6' },
  { id: 'security',icon: '🔒', name: 'Security Sentinel', color: '#ef4444' },
  { id: 'ops',     icon: '🚀', name: 'Logistics Master', color: '#6366f1' },
  { id: 'env',     icon: '🌿', name: 'Env Steward', color: '#10b981' },
  { id: 'social',  icon: '🤝', name: 'Social Harmonizer', color: '#f472b6' },
  { id: 'govt',    icon: '🏛️', name: 'Governance Advisor', color: '#78716c' },
  { id: 'innov',   icon: '⚡', name: 'Innovation Catalyst', color: '#eab308' },
  { id: 'harmony', icon: '☯️', name: 'Harmony Keeper', color: '#a855f7' },
];

// 🎯 Smart suggestions (from AsimOrb)
const QUICK_ACTIONS = [
  { icon: '🏥', text: 'Health check', action: 'health' },
  { icon: '💼', text: 'Work mode', action: 'work' },
  { icon: '🌐', text: 'Mesh status', action: 'mesh' },
  { icon: '🤖', text: 'Hire agent', action: 'agent' },
  { icon: '📸', text: 'Screen help', action: 'screen' },
  { icon: '💻', text: 'Code help', action: 'code' },
];

// 📝 Welcome messages
const WELCOME_FULL = `🌌 **AsimNexus Chat**

मसँग कुरा गर्नुस् — Nepali वा English मा।

**⚡ Commands:** /help · /clear · /clone · /voice
**🎙️ Voice:** Mic button थिच्नुस्  
**🤖 Clones:** 15 specialists available`;

const WELCOME_COMPACT = `👋 Namaste! I'm Asim. Press Alt+A anytime to chat.`;

// ── Code block renderer ──
function renderContent(text) {
  if (!text) return '';
  const blocks = text.split(/(```[\s\S]*?```)/g);
  return blocks.map((block, i) => {
    if (block.startsWith('```')) {
      const lines = block.slice(3, -3).split('\n');
      const lang = lines[0].trim() || 'code';
      const code = lines.slice(1).join('\n');
      return (
        <div key={i} style={{ position: 'relative', margin: '8px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: 'rgba(0,0,0,0.4)', borderRadius: '8px 8px 0 0', padding: '4px 10px',
            fontSize: '0.68rem', color: '#888' }}>
            <span>{lang}</span>
            <button onClick={() => navigator.clipboard?.writeText(code)}
              style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', fontSize: '0.7rem' }}>
              📋 Copy
            </button>
          </div>
          <pre style={{ margin: 0, background: 'rgba(0,0,0,0.35)', borderRadius: '0 0 8px 8px',
            padding: '12px', overflowX: 'auto', fontSize: '0.8rem', color: '#e2e8f0',
            borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <code>{code}</code>
          </pre>
        </div>
      );
    }
    const html = block
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.12);padding:2px 6px;border-radius:4px;font-size:0.85em">$1</code>')
      .replace(/\n/g, '<br/>');
    return <span key={i} dangerouslySetInnerHTML={{ __html: html }} />;
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// UNIFIED CHAT COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════
export default function UnifiedChat({
  user,
  onCommand,
  compact = false,
  onClose = null,
  className = '',
  theme = null,
  popupSize = null,
}) {
  // ── State ──
  const chatCtx = useChatContext();
  const isShared = !!chatCtx;

  const [localMessages, setLocalMessages] = useState([
    { id: 'welcome', role: 'assistant', content: compact ? WELCOME_COMPACT : WELCOME_FULL, ts: Date.now() }
  ]);
  const messages = isShared ? chatCtx.messages : localMessages;
  const setMessages = isShared ? chatCtx.setMessages : setLocalMessages;

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  // Clones
  const [localSelectedClone, setLocalSelectedClone] = useState(CLONES[0]);
  const selectedClone = isShared ? chatCtx.selectedClone : localSelectedClone;
  const setSelectedClone = isShared ? chatCtx.setSelectedClone : setLocalSelectedClone;
  const [showCloneMenu, setShowCloneMenu] = useState(false);

  // ── WebSocket Backend Connection ──
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const WS_URL = (process.env.REACT_APP_WS_URL || 'ws://localhost:8000') + '/ws/chat';

  useEffect(() => {
    if (!compact) return;
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === 'message' && data.role === 'assistant') {
          const msg = {
            id: Date.now(),
            role: 'assistant',
            content: data.content,
            ts: Date.now(),
            clone: data.clone || 'Asim Core',
            source: 'websocket'
          };
          // Use shared setter so popup + full page stay synced
          setMessages(prev => [...prev, msg]);
          setLoading(false);
        }
      } catch (e) { console.warn('[WS] Parse error:', e); }
    };
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    return () => ws.close();
  }, [compact, WS_URL, setMessages]);
  
  // Context awareness
  const [currentContext, setCurrentContext] = useState(null);
  const [smartSuggestions, setSmartSuggestions] = useState(QUICK_ACTIONS);
  
  // Voice
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  
  // File
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = useRef(null);
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  
  // Refs
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // ── Effects ──
  useEffect(() => { 
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages, loading]);

  // Initialize context awareness & gestures
  useEffect(() => {
    if (!compact) {
      // Full mode: init all services
      try {
        contextService.init();
        setCurrentContext(contextService.getCurrentContext());
        
        gestureService.init();
        
        const ctxUnsub = contextService.subscribe((event, data) => {
          if (event === 'pageChange') {
            setCurrentContext(prev => ({ ...prev, ...data }));
            setSmartSuggestions(contextService.getSmartSuggestions() || QUICK_ACTIONS);
          }
        });
        
        const gestureUnsub = gestureService.on('shortcut', (data) => {
          if (data.action === 'toggle_orb') return; // handled by parent
          if (data.action === 'screenshot_analyze') handleScreenshot();
          if (data.action === 'voice_mode') toggleVoice();
        });
        
        return () => {
          ctxUnsub?.();
          gestureUnsub?.();
          contextService.destroy?.();
          gestureService.destroy?.();
        };
      } catch (e) {
        console.warn('[UnifiedChat] Service init failed:', e);
      }
    }
  }, [compact]);

  // Focus input on open
  useEffect(() => {
    if (!compact) setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // ── Voice Input ──
  const toggleVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Voice not supported in this browser'); return; }
    
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    
    const rec = new SR();
    rec.lang = 'ne-NP';
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setInput(prev => prev + ' ' + text);
      setIsListening(false);
    };
    rec.onerror = () => setIsListening(false);
    rec.onend = () => setIsListening(false);
    
    recognitionRef.current = rec;
    rec.start();
    setIsListening(true);
  }, [isListening]);

  // ── File Attachment ──
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAttachedFile(file);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'user', 
        content: `📎 Attached: ${file.name} (${(file.size/1024).toFixed(1)} KB)`,
        ts: Date.now(),
        file: true
      }]);
    }
  };

  // ── AI Response ──
  const handleAIResponse = useCallback(async (userMsg) => {
    setLoading(true);
    
    const context = {
      ...currentContext,
      previousMessages: messages.slice(-5),
      user,
      mode: user?.mode || 'personal',
      clone: selectedClone.id,
    };
    
    try {
      // Try backend API first (real Qwen3-4B)
      const apiResponse = await asimBrain.processMessage(userMsg, context);
      
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: apiResponse.response,
        clone: apiResponse.clone_used || selectedClone.name,
        ts: Date.now(),
        source: apiResponse.source
      }]);
    } catch (error) {
      console.warn('[UnifiedChat] Backend error, using local fallback:', error);
      // Fallback to local response
      try {
        const localResponse = asimBrain.localProcess(userMsg, context);
        
        setMessages(prev => [...prev, { 
          id: Date.now(), 
          role: 'assistant', 
          content: localResponse.response,
          clone: selectedClone.name,
          ts: Date.now(),
          source: 'local_fallback'
        }]);
      } catch (localError) {
        console.error('[UnifiedChat] Local fallback error:', localError);
        // Ultimate fallback
        setMessages(prev => [...prev, { 
          id: Date.now(), 
          role: 'assistant', 
          content: `I received: "${userMsg}"\n\n[AsimBrain processing...]`,
          clone: selectedClone.name,
          ts: Date.now(),
          source: 'error'
        }]);
      }
    } finally {
      setLoading(false);
    }
  }, [currentContext, messages, user, selectedClone]);

  // ── Send Message ──
  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text && !attachedFile) return;
    
    // Slash commands
    if (text.startsWith('/')) {
      if (text === '/clear') {
        setMessages([{ id: 'welcome', role: 'assistant', content: 'Chat cleared.', ts: Date.now() }]);
        setInput('');
        return;
      }
      if (text === '/help') {
        setMessages(prev => [...prev, { 
          id: Date.now(), 
          role: 'assistant', 
          content: '**Commands:** /clear · /clone · /voice · /search\n**Features:** Voice input, File attach, Clone select, Smart suggestions',
          ts: Date.now()
        }]);
        setInput('');
        return;
      }
      if (text === '/clone') {
        setShowCloneMenu(true);
        setInput('');
        return;
      }
      if (text === '/voice') {
        toggleVoice();
        setInput('');
        return;
      }
      if (text === '/search') {
        setShowSearch(true);
        setInput('');
        return;
      }
    }
    
    // Normal message
    // // // // // // // // // // // // // // // // // // // // // // console.log('[UnifiedChat] Sending message:', text);
    const userMsg = { id: Date.now(), role: 'user', content: text, ts: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setAttachedFile(null);

    // Try WebSocket first if connected (compact mode)
    if (compact && wsRef.current && wsConnected && wsRef.current.readyState === 1) {
      setLoading(true);
      try {
        wsRef.current.send(JSON.stringify({ message: text, clone: selectedClone.id }));
        return;
      } catch (e) { console.warn('[WS] Send failed, falling back:', e); }
    }

    // Fallback: REST API / local
    handleAIResponse(text);
  }, [input, attachedFile, onCommand, handleAIResponse, toggleVoice, compact, wsConnected, selectedClone]);

  // ── Screenshot Analysis ──
  const handleScreenshot = async () => {
    setMessages(prev => [...prev, { 
      id: Date.now(), 
      role: 'system', 
      content: '📸 Analyzing screen context...',
      ts: Date.now()
    }]);
    
    try {
      await nativeBridge.captureScreen?.();
      const ocrResult = await contextService.performOCR?.();
      const suggestions = contextService.getSmartSuggestions?.() || QUICK_ACTIONS;
      
      setSmartSuggestions(suggestions);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: `📋 Screen analyzed. Try: "${suggestions[0]?.text || 'Get help'}"`,
        ts: Date.now()
      }]);
    } catch {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'system', 
        content: 'Screenshot analysis: Native app required for full features.',
        ts: Date.now()
      }]);
    }
  };

  // ── Handle Smart Action ──
  const handleSmartAction = (action) => {
    const prompts = {
      health: 'Check my health status and give wellness tips',
      work: 'Switch to work mode - productivity tips and focus tools',
      mesh: 'Show network mesh status and connected nodes',
      agent: 'Help me hire the right agent for my current task',
      screen: 'Analyze my current screen and help with what I see',
      code: 'Help me with coding - I need technical assistance',
    };
    
    const prompt = prompts[action] || action;
    setInput(prompt);
    setTimeout(handleSend, 100);
  };

  // ── Search Filter ──
  const filteredMessages = useMemo(() => {
    if (!searchQuery) return messages;
    return messages.filter(m => m.content?.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [messages, searchQuery]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === 'Escape') {
      if (showCloneMenu) setShowCloneMenu(false);
      else if (showSearch) setShowSearch(false);
      else onClose?.();
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════════════
  
  // Compact mode = AsimOrb floating
  if (compact) {
    const t = theme || { bg:'rgba(15,15,35,0.95)', border:'1px solid rgba(102,126,234,0.3)', text:'#fff', muted:'rgba(255,255,255,0.5)', primary:'#667eea', input:'rgba(255,255,255,0.05)', controls:'rgba(0,0,0,0.2)' };
    const isTiny = popupSize && (popupSize.width < 320 || popupSize.height < 420);
    return (
      <div style={{
        width: '100%', height: '100%',
        background: t.bg,
        backdropFilter: 'blur(20px)',
        borderRadius: isTiny ? 14 : 18,
        border: t.border,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: isTiny?8:12,
          padding: isTiny?'8px 10px':'12px 14px',
          borderBottom: t.border,
          background: `linear-gradient(90deg, ${t.primary}22, transparent)`,
        }}>
          <div style={{
            width: isTiny?28:34, height: isTiny?28:34, borderRadius: '50%',
            background: `linear-gradient(135deg, ${selectedClone.color}, #764ba2)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: isTiny?14:16,
            boxShadow: `0 4px 15px ${t.primary}66`,
          }}>{selectedClone.icon}</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: isTiny?'0.75rem':'0.85rem', fontWeight: 600, color:t.text }}>Asim Chat</div>
            <div style={{ fontSize: '0.65rem', color:t.muted }}>{selectedClone.name} {wsConnected?'●':'○'}</div>
          </div>
          {onClose && <button onClick={onClose} style={{background:'none',border:'none',color:t.muted,cursor:'pointer',padding:4}}><X size={isTiny?14:18}/></button>}
        </div>

        {/* Smart Suggestions */}
        {!isTiny && (
          <div style={{display:'flex',gap:6,padding:'8px 10px',overflowX:'auto',scrollbarWidth:'none',borderBottom:`1px solid ${t.muted}11`}}>
            {smartSuggestions.slice(0,3).map((s,i)=>(
              <button key={i} onClick={()=>handleSmartAction(s.action)} style={{padding:'5px 8px',borderRadius:10,background:`${t.primary}22`,border:`1px solid ${t.primary}44`,color:t.primary,fontSize:'0.7rem',whiteSpace:'nowrap',cursor:'pointer',display:'flex',alignItems:'center',gap:4}}>
                {s.icon} {s.text}
              </button>
            ))}
          </div>
        )}

        {/* Messages */}
        <div style={{flex:1,overflow:'auto',padding:isTiny?'8px':'10px',display:'flex',flexDirection:'column',gap:8}}>
          {messages.map((m)=> (
            <div key={m.id} style={{
              alignSelf: m.role==='user'?'flex-end':'flex-start',
              background: m.role==='user'?`linear-gradient(135deg,${t.primary},#764ba2)` : m.file?`${t.muted}11`:`${t.muted}15`,
              padding: isTiny?'6px 10px':'8px 12px', borderRadius: 12,
              maxWidth: '85%', marginLeft: m.role==='user'?'auto':0,
              fontSize: isTiny?'0.75rem':'0.82rem', color: m.role==='user'?'#fff':t.text,
            }}>
              {renderContent(m.content)}
            </div>
          ))}
          {loading && (
            <div style={{display:'flex',gap:4,padding:8,justifyContent:'center'}}>
              <span style={{animation:'pulse 0.6s infinite',opacity:0.5,color:t.primary}}>●</span>
              <span style={{animation:'pulse 0.6s infinite 0.2s',opacity:0.5,color:t.primary}}>●</span>
              <span style={{animation:'pulse 0.6s infinite 0.4s',opacity:0.5,color:t.primary}}>●</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{display:'flex',alignItems:'center',gap:isTiny?4:8,padding:isTiny?'8px':'10px',borderTop:t.border,background:t.controls,flexShrink:0}}>
          <button onClick={toggleVoice} style={{background:isListening?'rgba(239,68,68,0.3)':t.input,border:'none',borderRadius:8,padding:isTiny?6:8,cursor:'pointer',color:isListening?'#ef4444':t.muted}}><Mic size={isTiny?14:16}/></button>
          <input ref={inputRef} value={input} onChange={(e)=>setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder={isTiny?'Ask...':'Ask anything...'} style={{flex:1,background:t.input,border:`1px solid ${t.muted}22`,borderRadius:10,padding:isTiny?'6px 10px':'8px 12px',color:t.text,fontSize:isTiny?'0.8rem':'0.85rem',minWidth:0}} />
          <button onClick={handleSend} style={{background:`linear-gradient(135deg,${t.primary},#764ba2)`,border:'none',borderRadius:8,padding:isTiny?6:8,cursor:'pointer',color:'#fff',display:'flex',alignItems:'center',justifyContent:'center'}}><Send size={isTiny?14:16}/></button>
        </div>

        <style>{`@keyframes pulse {0%,100%{opacity:0.3}50%{opacity:1}}`}</style>
      </div>
    );
  }

  // Full mode = UniversalChat
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      background: 'rgba(10,10,26,0.3)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(0,0,0,0.2)',
      }}>
        {/* Clone Selector */}
        <div style={{ position: 'relative' }}>
          <button onClick={() => setShowCloneMenu(!showCloneMenu)}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 16px',
              background: 'rgba(102,126,234,0.15)',
              border: '1px solid rgba(102,126,234,0.3)',
              borderRadius: 12,
              color: '#fff', cursor: 'pointer',
            }}>
            <span style={{ fontSize: 20 }}>{selectedClone.icon}</span>
            <span style={{ fontSize: '0.85rem' }}>{selectedClone.name}</span>
            <Sparkles size={16} color="#667eea" />
          </button>
          
          {showCloneMenu && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, marginTop: 8,
              background: 'rgba(15,15,35,0.98)', backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12,
              padding: 8, minWidth: 220,
              maxHeight: 300, overflow: 'auto',
              zIndex: 100,
            }}>
              {CLONES.map(c => (
                <button key={c.id} onClick={() => { setSelectedClone(c); setShowCloneMenu(false); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    width: '100%', padding: '10px 12px',
                    background: selectedClone.id === c.id ? 'rgba(102,126,234,0.2)' : 'transparent',
                    border: 'none', borderRadius: 8,
                    color: '#fff', cursor: 'pointer', textAlign: 'left',
                  }}>
                  <span>{c.icon}</span>
                  <span style={{ fontSize: '0.85rem' }}>{c.name}</span>
                  {selectedClone.id === c.id && <Zap size={14} color="#667eea" style={{ marginLeft: 'auto' }} />}
                </button>
              ))}
            </div>
          )}
        </div>

        <div style={{ flex: 1 }} />

        {/* Search Toggle */}
        <button onClick={() => setShowSearch(!showSearch)} style={{
          background: showSearch ? 'rgba(102,126,234,0.3)' : 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
          padding: 10, cursor: 'pointer',
          color: showSearch ? '#667eea' : 'rgba(255,255,255,0.6)',
        }}><Search size={18} /></button>

        {/* Screenshot */}
        <button onClick={handleScreenshot} style={{
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
          padding: 10, cursor: 'pointer',
          color: 'rgba(255,255,255,0.6)',
        }}><Camera size={18} /></button>
      </div>

      {/* Search Bar */}
      {showSearch && (
        <div style={{
          padding: '12px 20px',
          background: 'rgba(0,0,0,0.15)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}>
          <input 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search messages..."
            style={{
              width: '100%', maxWidth: 400,
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
              padding: '10px 14px', color: '#fff',
            }}
          />
        </div>
      )}

      {/* Smart Suggestions */}
      <div style={{
        display: 'flex', gap: 10, padding: '14px 20px',
        overflowX: 'auto', scrollbarWidth: 'none',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        {smartSuggestions.map((s, i) => (
          <button key={i} onClick={() => handleSmartAction(s.action)}
            style={{
              padding: '8px 14px', borderRadius: 16,
              background: 'rgba(102,126,234,0.12)',
              border: '1px solid rgba(102,126,234,0.25)',
              color: '#a5b4fc', fontSize: '0.8rem',
              whiteSpace: 'nowrap', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
            {s.icon} {s.text}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflow: 'auto', padding: '20px',
        display: 'flex', flexDirection: 'column', gap: 14,
      }}>
        {filteredMessages.map((m) => (
          <div key={m.id} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: m.role === 'user' ? '75%' : '85%',
          }}>
            {/* Avatar */}
            {m.role !== 'user' && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: m.clone?.includes('Tech') ? '#3b82f6' : 
                              m.clone?.includes('Health') ? '#22c55e' :
                              'linear-gradient(135deg, #667eea, #764ba2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14,
                }}>{m.clone ? CLONES.find(c => c.name === m.clone)?.icon || '🌌' : '🌌'}</div>
                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>{m.clone || 'Asim'}</span>
              </div>
            )}
            
            {/* Message bubble */}
            <div style={{
              background: m.role === 'user' 
                ? 'linear-gradient(135deg, #667eea, #764ba2)' 
                : m.file ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.08)',
              padding: m.role === 'user' ? '12px 16px' : '14px 18px',
              borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              fontSize: '0.95rem', lineHeight: 1.6,
              boxShadow: m.role === 'user' ? '0 4px 15px rgba(102,126,234,0.3)' : 'none',
            }}>
              {renderContent(m.content)}
            </div>
            
            {/* Timestamp */}
            <div style={{
              fontSize: '0.65rem', opacity: 0.4,
              marginTop: 4, textAlign: m.role === 'user' ? 'right' : 'left',
            }}>
              {new Date(m.ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </div>
          </div>
        ))}
        
        {loading && (
          <div style={{ display: 'flex', gap: 4, padding: 16 }}>
            <span style={{ animation: 'pulse 0.6s infinite', opacity: 0.5 }}>●</span>
            <span style={{ animation: 'pulse 0.6s infinite 0.2s', opacity: 0.5 }}>●</span>
            <span style={{ animation: 'pulse 0.6s infinite 0.4s', opacity: 0.5 }}>●</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '16px 20px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(0,0,0,0.2)',
      }}>
        {/* File attach */}
        <input type="file" ref={fileInputRef} onChange={handleFileSelect} style={{ display: 'none' }} />
        <button onClick={() => fileInputRef.current?.click()} style={{
          background: attachedFile ? 'rgba(102,126,234,0.3)' : 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12,
          padding: 12, cursor: 'pointer',
          color: attachedFile ? '#667eea' : 'rgba(255,255,255,0.6)',
        }}><Paperclip size={20} /></button>

        {/* Voice */}
        <button onClick={toggleVoice} style={{
          background: isListening ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12,
          padding: 12, cursor: 'pointer',
          color: isListening ? '#ef4444' : 'rgba(255,255,255,0.6)',
        }}><Mic size={20} /></button>

        {/* Text input */}
        <input 
          ref={inputRef}
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyDown={handleKeyDown}
          placeholder="Type / for commands, or ask anything..."
          style={{
            flex: 1,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14,
            padding: '14px 18px', color: '#fff', fontSize: '1rem',
          }} 
        />

        {/* Send */}
        <button onClick={handleSend} style={{
          background: 'linear-gradient(135deg, #667eea, #764ba2)',
          border: 'none', borderRadius: 12,
          padding: 14, cursor: 'pointer', color: '#fff',
          boxShadow: '0 4px 15px rgba(102,126,234,0.4)',
        }}><Send size={20} /></button>
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
      `}</style>
    </div>
  );
}
