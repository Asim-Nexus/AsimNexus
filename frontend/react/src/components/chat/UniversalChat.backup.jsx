/**
 * Universal Chat Interface — AsimNexus v3
 * ==========================================
 * Features:
 * 1. 🎙️ Voice Input (Web Speech API)
 * 2. 📎 File/Image Attach + preview
 * 3. 🤖 Clone Selector (pick which of 15 clones to talk to)
 * 4. 💬 Message Reactions (emoji reactions per message)
 * 5. 📌 Pin important messages
 * 6. 💻 Code block syntax highlight + copy button
 * 7. 📤 Export chat as .txt / .md
 * 8. 🔍 In-chat message search
 * 9. 🧠 Context memory indicator (shows how much context is used)
 * 10. ⚡ Slash commands (/help /clear /export /clone /search)
 */
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
const getStoredToken = () => localStorage.getItem('asimnexus_token');

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const CLONES = [
  { id: 'auto', icon: '🌌', name: 'Auto (Smart Route)' },
  { id: 'tech', icon: '💻', name: 'Tech Architect' },
  { id: 'health', icon: '🏥', name: 'Health Sage' },
  { id: 'finance', icon: '💰', name: 'Financial Oracle' },
  { id: 'legal', icon: '⚖️', name: 'Legal Guardian' },
  { id: 'edu', icon: '📚', name: 'Education Mentor' },
  { id: 'creative', icon: '🎨', name: 'Creative Muse' },
  { id: 'strategy', icon: '🎯', name: 'Strategic Planner' },
  { id: 'science', icon: '🔬', name: 'Research Explorer' },
  { id: 'security', icon: '🔒', name: 'Security Sentinel' },
  { id: 'ops', icon: '🚀', name: 'Logistics Master' },
  { id: 'env', icon: '🌿', name: 'Env Steward' },
  { id: 'social', icon: '🤝', name: 'Social Harmonizer' },
  { id: 'govt', icon: '�️', name: 'Governance Advisor' },
  { id: 'innov', icon: '⚡', name: 'Innovation Catalyst' },
  { id: 'harmony', icon: '☯️', name: 'Harmony Keeper' },
];

const QUICK_PROMPTS = [
  { label: '🧠 Explain AI', text: 'Explain artificial intelligence in simple words' },
  { label: '💻 Write code', text: 'Write a Python function to sort a list' },
  { label: '🌿 Health tip', text: 'Give me a simple daily health routine' },
  { label: '💰 Save money', text: 'How can I save money on a small salary?' },
  { label: '📖 Nepali poem', text: 'एउटा छोटो नेपाली कविता लेख' },
  { label: '🌍 World news', text: 'What are the most important global issues in 2026?' },
];

const REACTIONS = ['👍', '❤️', '🔥', '😂', '🤯', '☯️'];

const SLASH_COMMANDS = {
  '/help': '**Commands:** /clear · /export · /clone · /search · /pin · /voice\n\n**Chat commands:** `dark mode` · `light mode` · `family universe` · `company universe` · `resource sharing`',
  '/clear': '__CLEAR__',
  '/export': '__EXPORT__',
  '/clone': '__SHOW_CLONE__',
  '/search': '__SHOW_SEARCH__',
  '/voice': '__VOICE__',
};

const WELCOME_MSG = {
  id: 'welcome',
  role: 'assistant',
  content: `🌌 **AsimNexus v3 सुरु भयो!**\n\nमसँग कुरा गर्नुस् — Nepali वा English मा।\n\n**⚡ Slash Commands:** \`/help\` · \`/clear\` · \`/export\` · \`/clone\` · \`/search\` · \`/voice\`\n\n**🎙️ Voice:** Mic button थिच्नुस्\n**📎 File:** Attach button बाट image/file पठाउनुस्\n**🤖 Clone:** कुन Clone सँग कुरा गर्ने select गर्नुस्\n\n**🤖 15 Clones ready:** Tech, Health, Finance, Legal, Creative...`,
  clone: 'AsimNexus 🌌',
  source: 'system',
  pinned: false,
  reactions: {},
  ts: Date.now(),
};

// ── Feature 6: Code block renderer ──────────────────────────────────────────
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
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: 'rgba(0,0,0,0.4)', borderRadius: '8px 8px 0 0', padding: '4px 10px',
            fontSize: '0.68rem', color: '#888'
          }}>
            <span>{lang}</span>
            <button onClick={() => navigator.clipboard?.writeText(code)}
              style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', fontSize: '0.7rem' }}>
              📋 Copy
            </button>
          </div>
          <pre style={{
            margin: 0, background: 'rgba(0,0,0,0.35)', borderRadius: '0 0 8px 8px',
            padding: '12px', overflowX: 'auto', fontSize: '0.8rem', color: '#e2e8f0',
            borderTop: '1px solid rgba(255,255,255,0.06)'
          }}>
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

export default function UniversalChat({ user, onCommand }) {
  const [messages, setMessages] = useState([WELCOME_MSG]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [backendOk, setBackendOk] = useState(false);
  const [localLlm, setLocalLlm] = useState(false);
  const [cloudProviders, setCloudProviders] = useState([]);

  // Feature 3: Clone selector
  const [selectedClone, setSelectedClone] = useState(CLONES[0]);
  const [showCloneMenu, setShowCloneMenu] = useState(false);

  // Feature 8: Search
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  // Feature 1: Voice
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // Feature 2: File attach
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Feature 9: Context token counter
  const contextTokens = useMemo(() => {
    const chars = messages.slice(-10).reduce((s, m) => s + (m.content?.length || 0), 0);
    return Math.min(Math.round(chars / 4), 4096);
  }, [messages]);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Status check
  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(d => { setBackendOk(true); setLocalLlm(!!d.local_llm); })
      .catch(() => setBackendOk(false));
    const token = getStoredToken();
    if (token) {
      fetch(`${API}/api/apis/status`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json())
        .then(d => setCloudProviders(Object.entries(d.providers || {}).filter(([, v]) => v === 'configured').map(([k]) => k)))
        .catch(() => { });
    }
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  // Feature 1: Voice Input
  const toggleVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Voice not supported in this browser'); return; }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const r = new SR();
    r.lang = 'ne-NP,en-US';
    r.interimResults = true;
    r.onresult = (e) => {
      const t = Array.from(e.results).map(r => r[0].transcript).join('');
      setInput(t);
    };
    r.onend = () => setIsListening(false);
    r.start();
    recognitionRef.current = r;
    setIsListening(true);
  }, [isListening]);

  // Feature 4+5: Reactions & Pin
  const addReaction = useCallback((msgId, emoji) => {
    setMessages(prev => prev.map(m => {
      if (m.id !== msgId) return m;
      const reactions = { ...(m.reactions || {}) };
      reactions[emoji] = (reactions[emoji] || 0) + 1;
      return { ...m, reactions };
    }));
  }, []);

  const togglePin = useCallback((msgId) => {
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, pinned: !m.pinned } : m));
  }, []);

  // Feature 7: Export
  const exportChat = useCallback((fmt = 'md') => {
    const lines = messages.map(m => {
      const time = new Date(m.ts).toLocaleTimeString();
      if (m.role === 'user') return `**You** [${time}]\n${m.content}\n`;
      return `**${m.clone || 'AsimNexus'}** [${time}]\n${m.content}\n`;
    });
    const content = fmt === 'md'
      ? `# AsimNexus Chat Export\n_${new Date().toLocaleString()}_\n\n---\n\n${lines.join('\n---\n\n')}`
      : lines.map(l => l.replace(/\*\*/g, '')).join('\n---\n\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `asimnexus-chat-${Date.now()}.${fmt}`;
    a.click();
  }, [messages]);

  // Feature 10: Slash command handler
  const handleSlash = useCallback((text) => {
    const cmd = text.trim().split(' ')[0].toLowerCase();
    if (!SLASH_COMMANDS[cmd]) return false;
    const action = SLASH_COMMANDS[cmd];
    if (action === '__CLEAR__') { setMessages([WELCOME_MSG]); setInput(''); return true; }
    if (action === '__EXPORT__') { exportChat('md'); setInput(''); return true; }
    if (action === '__SHOW_CLONE__') { setShowCloneMenu(true); setInput(''); return true; }
    if (action === '__SHOW_SEARCH__') { setShowSearch(true); setInput(''); return true; }
    if (action === '__VOICE__') { toggleVoice(); setInput(''); return true; }
    // /help → show as assistant message
    setMessages(prev => [...prev, {
      id: Date.now(), role: 'assistant', content: action,
      clone: 'AsimNexus', source: 'system', ts: Date.now(), reactions: {}, pinned: false,
    }]);
    setInput('');
    return true;
  }, [exportChat, toggleVoice]);

  const sendMessage = useCallback(async (overrideText) => {
    const text = (overrideText || input).trim();
    if (!text || loading) return;

    // Slash commands
    if (text.startsWith('/') && handleSlash(text)) return;

    const userMsg = {
      id: Date.now(), role: 'user', content: text,
      attachment: attachedFile?.name || null, ts: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setAttachedFile(null);
    setLoading(true);

    try {
      const token = getStoredToken();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const body = { message: text };
      if (selectedClone.id !== 'auto') body.clone_hint = selectedClone.id;
      if (attachedFile) body.file_name = attachedFile.name;

      const resp = await fetch(`${API}/chat`, { method: 'POST', headers, body: JSON.stringify(body) });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      let aiContent = data.response || 'No response';
      let fwAdvisory = '';
      let fwVerdict = 'clean';
      try {
        const fwRes = await fetch(`${API}/api/firewall/check`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: aiContent, sensitivity: 0.5 }),
        }).then(r => r.json());
        fwVerdict = fwRes.verdict || 'clean';
        if (fwVerdict === 'filtered' && fwRes.filtered_text) {
          aiContent = fwRes.filtered_text;
        }
        if (fwVerdict !== 'clean') {
          fwAdvisory = fwRes.advisory_msg || '';
        }
      } catch { }

      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'assistant',
        content: aiContent,
        clone: data.clone || selectedClone.name,
        source: data.source || 'unknown',
        model: data.model || '',
        intent: data.intent || '',
        fw_verdict: fwVerdict,
        fw_advisory: fwAdvisory,
        reactions: {}, pinned: false, ts: Date.now(),
      }]);

      if (data.command && onCommand) onCommand(data.command);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 2, role: 'assistant',
        content: `⚠️ Error: ${err.message}\n\n💡 Backend सुरु गर्न: \`python simple_backend.py\``,
        clone: 'System', source: 'error', ts: Date.now(), reactions: {}, pinned: false,
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [input, loading, onCommand, selectedClone, attachedFile, handleSlash]);

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  // Feature 8: Filtered messages
  const displayedMessages = useMemo(() => {
    if (!searchQuery) return messages;
    return messages.filter(m => m.content?.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [messages, searchQuery]);

  const pinnedMsgs = useMemo(() => messages.filter(m => m.pinned), [messages]);

  const SOURCE_ICON = { local_gguf: '🖥️', local: '🖥️', ollama: '🦙', openai: '🌐', anthropic: '🌐', gemini: '🌐', deepseek: '🌐', grok: '🌐', fallback: '⚡', system: '⚙️', error: '⚠️', dharma: '☯️' };

  const ctxPct = Math.round((contextTokens / 4096) * 100);
  const ctxColor = ctxPct > 80 ? '#ef4444' : ctxPct > 50 ? '#f59e0b' : '#10b981';

  const s = {
    wrap: { display: 'flex', flexDirection: 'column', height: 'calc(100vh - 44px)', overflow: 'hidden', position: 'relative' },
    statusBar: {
      display: 'flex', gap: 6, padding: '6px 14px', flexShrink: 0,
      background: 'rgba(0,0,0,0.25)', borderBottom: '1px solid rgba(255,255,255,0.06)',
      flexWrap: 'wrap', alignItems: 'center',
    },
    badge: (ok, color) => ({
      padding: '2px 9px', borderRadius: 20, fontSize: '0.65rem', cursor: 'default',
      background: color ? `${color}22` : ok ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
      border: `1px solid ${color || (ok ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.25)')}`,
      color: color || (ok ? '#10b981' : '#ef4444'),
    }),
    msgs: { flex: 1, overflow: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 },
    userBubble: {
      alignSelf: 'flex-end', maxWidth: '72%',
      background: 'linear-gradient(135deg, #667eea, #764ba2)',
      borderRadius: '18px 18px 4px 18px', padding: '10px 15px',
      color: '#fff', fontSize: '0.9rem', lineHeight: 1.5, wordBreak: 'break-word',
    },
    aiBubble: {
      alignSelf: 'flex-start', maxWidth: '82%',
      background: 'var(--theme-card, rgba(255,255,255,0.05))',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '4px 18px 18px 18px', padding: '10px 14px',
      color: 'var(--theme-text, #fff)', fontSize: '0.9rem', lineHeight: 1.6, wordBreak: 'break-word',
    },
    metaRow: { display: 'flex', gap: 6, alignItems: 'center', marginBottom: 5, fontSize: '0.68rem', opacity: 0.55 },
    reactionRow: { display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap', alignItems: 'center' },
    inputArea: {
      flexShrink: 0, background: 'rgba(0,0,0,0.3)', borderTop: '1px solid rgba(255,255,255,0.06)',
    },
    toolbar: {
      display: 'flex', gap: 4, padding: '6px 14px 4px', alignItems: 'center', flexWrap: 'wrap',
    },
    toolBtn: (active) => ({
      padding: '4px 10px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: '0.78rem',
      background: active ? 'rgba(102,126,234,0.25)' : 'rgba(255,255,255,0.05)',
      color: active ? '#667eea' : 'rgba(255,255,255,0.55)',
      transition: 'all 0.15s',
    }),
    inputRow: { display: 'flex', gap: 8, padding: '4px 14px 10px', alignItems: 'flex-end' },
    textarea: {
      flex: 1, resize: 'none', minHeight: 42, maxHeight: 120,
      background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 12, padding: '10px 13px', color: 'var(--theme-text, #fff)',
      fontSize: '0.9rem', outline: 'none', fontFamily: 'inherit', lineHeight: 1.4,
    },
    sendBtn: (active) => ({
      width: 42, height: 42, borderRadius: 12, border: 'none', cursor: active ? 'pointer' : 'default',
      background: active ? 'linear-gradient(135deg, #667eea, #764ba2)' : 'rgba(255,255,255,0.06)',
      color: active ? '#fff' : 'rgba(255,255,255,0.3)', fontSize: 17,
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.2s',
    }),
    typing: {
      alignSelf: 'flex-start', padding: '8px 14px',
      background: 'rgba(255,255,255,0.04)', borderRadius: '4px 12px 12px 12px',
      fontSize: '0.78rem', opacity: 0.65, display: 'flex', gap: 6, alignItems: 'center',
    },
    overlay: {
      position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.65)',
      zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center',
    },
    modal: {
      background: '#13132a', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 18, padding: 24, width: '90%', maxWidth: 420, maxHeight: '70vh', overflow: 'auto',
    },
  };

  return (
    <div style={s.wrap}>
      {/* STATUS BAR */}
      <div style={s.statusBar}>
        <span style={s.badge(backendOk)}>{backendOk ? '🟢 Online' : '🔴 Offline'}</span>
        <span style={s.badge(localLlm)}>{localLlm ? '🖥️ Qwen3' : '☁️ Cloud'}</span>
        {cloudProviders.map(p => <span key={p} style={s.badge(true, '#3b82f6')}>{p}</span>)}
        <span style={s.badge(true, '#8b5cf6')}>🤖 {selectedClone.icon} {selectedClone.name}</span>

        {/* Feature 9: Context meter */}
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.65rem', opacity: 0.7 }}>
          🧠 ctx
          <div style={{ width: 50, height: 5, background: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${ctxPct}%`, background: ctxColor, transition: 'width 0.3s' }} />
          </div>
          <span style={{ color: ctxColor }}>{contextTokens}</span>
        </span>

        {/* Export */}
        <span style={{ ...s.badge(true, '#f59e0b'), cursor: 'pointer' }} onClick={() => exportChat('md')}>📤 Export</span>
        {/* Search toggle */}
        <span style={{ ...s.badge(showSearch, '#667eea'), cursor: 'pointer' }} onClick={() => setShowSearch(v => !v)}>🔍</span>
      </div>

      {/* Feature 8: Search bar */}
      {showSearch && (
        <div style={{ padding: '6px 14px', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: 8 }}>
          <input
            autoFocus
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="🔍 Messages खोज्नुस्…"
            style={{ flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '5px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
          />
          <button onClick={() => { setSearchQuery(''); setShowSearch(false); }}
            style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: 16 }}>✕</button>
          {searchQuery && <span style={{ fontSize: '0.72rem', opacity: 0.5, alignSelf: 'center' }}>{displayedMessages.length} results</span>}
        </div>
      )}

      {/* Pinned messages bar */}
      {pinnedMsgs.length > 0 && (
        <div style={{ padding: '5px 14px', background: 'rgba(102,126,234,0.08)', borderBottom: '1px solid rgba(102,126,234,0.2)', fontSize: '0.72rem', color: '#667eea' }}>
          📌 {pinnedMsgs.length} pinned — "{pinnedMsgs[pinnedMsgs.length - 1].content?.slice(0, 60)}…"
        </div>
      )}

      {/* MESSAGES */}
      <div style={s.msgs}>
        {/* Quick prompts — only show when just welcome message */}
        {messages.length === 1 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
            {QUICK_PROMPTS.map(qp => (
              <button key={qp.text} onClick={() => sendMessage(qp.text)}
                style={{
                  padding: '5px 12px', borderRadius: 20, border: '1px solid rgba(102,126,234,0.35)',
                  background: 'rgba(102,126,234,0.08)', color: 'rgba(255,255,255,0.7)',
                  cursor: 'pointer', fontSize: '0.75rem'
                }}>
                {qp.label}
              </button>
            ))}
          </div>
        )}

        {displayedMessages.map(msg => (
          <div key={msg.id} style={{ display: 'flex', flexDirection: 'column' }}>
            {msg.role === 'user' ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3 }}>
                {msg.attachment && (
                  <div style={{ fontSize: '0.72rem', opacity: 0.6, color: '#667eea' }}>📎 {msg.attachment}</div>
                )}
                <div style={s.userBubble}>{msg.content}</div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {REACTIONS.map(e => (
                    <span key={e} onClick={() => addReaction(msg.id, e)}
                      style={{ cursor: 'pointer', fontSize: '0.8rem', opacity: 0.5, transition: 'opacity 0.15s' }}
                      onMouseEnter={ev => ev.target.style.opacity = 1}
                      onMouseLeave={ev => ev.target.style.opacity = 0.5}>
                      {e}{msg.reactions?.[e] ? ` ${msg.reactions[e]}` : ''}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 3 }}>
                <div style={{ ...s.aiBubble, outline: msg.pinned ? '1px solid rgba(102,126,234,0.5)' : 'none' }}>
                  <div style={s.metaRow}>
                    <span>{SOURCE_ICON[msg.source] || '🤖'}</span>
                    <span style={{ fontWeight: 600 }}>{msg.clone || 'AsimNexus'}</span>
                    {msg.model && msg.model !== 'fallback' && <span>· {msg.model}</span>}
                    {msg.pinned && <span style={{ color: '#667eea' }}>📌</span>}
                    <span style={{ marginLeft: 'auto' }}>{new Date(msg.ts).toLocaleTimeString()}</span>
                  </div>
                  <div>{renderContent(msg.content)}</div>

                  {/* Cognitive Firewall badge */}
                  {msg.fw_verdict && msg.fw_verdict !== 'clean' && (
                    <div style={{
                      marginTop: 6, padding: '4px 10px', borderRadius: 8, fontSize: '0.7rem',
                      background: msg.fw_verdict === 'blocked' ? 'rgba(239,68,68,0.12)' :
                        msg.fw_verdict === 'filtered' ? 'rgba(251,146,60,0.12)' :
                          'rgba(234,179,8,0.12)',
                      border: `1px solid ${msg.fw_verdict === 'blocked' ? 'rgba(239,68,68,0.3)' :
                        msg.fw_verdict === 'filtered' ? 'rgba(251,146,60,0.3)' :
                          'rgba(234,179,8,0.3)'}`,
                      color: msg.fw_verdict === 'blocked' ? '#f87171' :
                        msg.fw_verdict === 'filtered' ? '#fb923c' : '#fbbf24',
                    }}>
                      🧠 Firewall: <strong>{msg.fw_verdict.toUpperCase()}</strong>
                      {msg.fw_advisory && <span style={{ marginLeft: 6, opacity: 0.85 }}>· {msg.fw_advisory}</span>}
                    </div>
                  )}

                  {/* Feature 4: Reactions */}
                  <div style={s.reactionRow}>
                    {REACTIONS.map(e => (
                      <span key={e} onClick={() => addReaction(msg.id, e)}
                        style={{
                          cursor: 'pointer', fontSize: '0.82rem', padding: '1px 5px',
                          borderRadius: 10, background: msg.reactions?.[e] ? 'rgba(102,126,234,0.2)' : 'transparent',
                          border: `1px solid ${msg.reactions?.[e] ? 'rgba(102,126,234,0.4)' : 'transparent'}`
                        }}>
                        {e}{msg.reactions?.[e] ? ` ${msg.reactions[e]}` : ''}
                      </span>
                    ))}
                    {/* Feature 5: Pin */}
                    <span onClick={() => togglePin(msg.id)}
                      style={{
                        cursor: 'pointer', fontSize: '0.75rem', marginLeft: 4, opacity: 0.5,
                        color: msg.pinned ? '#667eea' : 'inherit'
                      }}>
                      {msg.pinned ? '📌 Unpin' : '📌 Pin'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={s.typing}>
            {[0, 1, 2].map(i => (
              <span key={i} style={{
                width: 6, height: 6, borderRadius: '50%',
                background: '#667eea', display: 'inline-block',
                animation: `bounce 1.2s ${i * 0.2}s ease-in-out infinite`
              }} />
            ))}
            {selectedClone.icon} {selectedClone.name} सोच्दैछ…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* INPUT AREA */}
      <div style={s.inputArea}>
        {/* Toolbar */}
        <div style={s.toolbar}>
          {/* Feature 1: Voice */}
          <button style={s.toolBtn(isListening)} onClick={toggleVoice} title="Voice input">
            {isListening ? '🔴 Listening…' : '🎙️ Voice'}
          </button>

          {/* Feature 2: File attach */}
          <button style={s.toolBtn(!!attachedFile)} onClick={() => fileInputRef.current?.click()} title="Attach file">
            📎 {attachedFile ? attachedFile.name.slice(0, 12) + '…' : 'Attach'}
          </button>
          <input ref={fileInputRef} type="file" style={{ display: 'none' }}
            onChange={e => setAttachedFile(e.target.files[0] || null)} />

          {/* Feature 3: Clone selector */}
          <button style={s.toolBtn(showCloneMenu)} onClick={() => setShowCloneMenu(v => !v)} title="Select Clone">
            {selectedClone.icon} Clone ▾
          </button>

          {/* Export md/txt */}
          <button style={s.toolBtn(false)} onClick={() => exportChat('txt')} title="Export as text">📄 .txt</button>

          {/* Clear */}
          <button style={{ ...s.toolBtn(false), marginLeft: 'auto', color: 'rgba(239,68,68,0.7)' }}
            onClick={() => { if (window.confirm('Chat clear गर्ने?')) setMessages([WELCOME_MSG]); }}>
            🗑️ Clear
          </button>
        </div>

        {/* Input row */}
        <div style={s.inputRow}>
          <textarea
            ref={inputRef}
            style={s.textarea}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={`${selectedClone.icon} ${selectedClone.name} लाई सोध्नुस्… (/ = commands)`}
            rows={1}
          />
          <button style={s.sendBtn(!(!input.trim() || loading))}
            onClick={() => sendMessage()} disabled={!input.trim() || loading}>
            ➤
          </button>
        </div>
      </div>

      {/* Feature 3: Clone selector modal */}
      {showCloneMenu && (
        <div style={s.overlay} onClick={() => setShowCloneMenu(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <div style={{ fontWeight: 700, marginBottom: 14, fontSize: '1rem' }}>🤖 Clone छान्नुस्</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {CLONES.map(c => (
                <button key={c.id}
                  onClick={() => { setSelectedClone(c); setShowCloneMenu(false); }}
                  style={{
                    padding: '8px 12px', borderRadius: 10, border: `1px solid ${selectedClone.id === c.id ? 'rgba(102,126,234,0.6)' : 'rgba(255,255,255,0.08)'}`,
                    background: selectedClone.id === c.id ? 'rgba(102,126,234,0.15)' : 'rgba(255,255,255,0.03)',
                    color: '#fff', cursor: 'pointer', textAlign: 'left', fontSize: '0.82rem'
                  }}>
                  {c.icon} {c.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.4); opacity: 0.3; }
          40% { transform: scale(1); opacity: 1; }
        }
        textarea::placeholder { opacity: 0.35; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }
      `}</style>
    </div>
  );
}
