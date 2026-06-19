/**
 * AI Hub — Lightweight using SmartHub
 * Memory + Local LLM
 */
import SmartHub from '../shared/SmartHub';
import MemoryDashboard from '../memory/MemoryDashboard';
import LocalLLMChat from '../memory/LocalLLMChat';

const TABS = [
  { id: 'memory', icon: '🧠', label: 'Memory', desc: 'Vector Store' },
  { id: 'local', icon: '🖥️', label: 'Local LLM', desc: 'Gemma/Llama' },
];

export default function AIHub({ user }) {
  return (
    <SmartHub 
      tabs={TABS} 
      title="AI" 
      icon="🧠" 
      accentColor="#8b5cf6"
      defaultTab={0}
    >
      {(tab, idx) => (
        <>
          {idx === 0 && <MemoryDashboard />}
          {idx === 1 && <LocalLLMChat />}
        </>
      )}
    </SmartHub>
  );
}
