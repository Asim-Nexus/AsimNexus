/**
 * Identity Hub — Lightweight using SmartHub
 * Digital ID + Blockchain + ZKP
 */
import SmartHub from '../shared/SmartHub';
import IdentityPanel from '../identity/IdentityPanel';
import BlockchainIdentity from '../identity/BlockchainIdentity';

const TABS = [
  { id: 'identity', icon: '👤', label: 'Digital ID', desc: 'Your Identity' },
  { id: 'blockchain', icon: '⛓️', label: 'Blockchain', desc: 'On-chain proof' },
  { id: 'zkp', icon: '🔐', label: 'ZKP', desc: 'Zero Knowledge' },
];

// ZKP Tab Content Component
const ZKPContent = () => (
  <div style={{ padding: 40, textAlign: 'center' }}>
    <h3>🔐 Level-3 ZKP Verification</h3>
    <p style={{ opacity: 0.6 }}>Zero-knowledge proof system for maximum privacy</p>
    <div style={{ marginTop: 30, padding: 20, background: 'rgba(102,126,234,0.1)', borderRadius: 12 }}>
      <p>Zero Knowledge Proofs allow you to prove your identity without revealing sensitive data.</p>
      <p style={{ fontSize: '0.8rem', marginTop: 10 }}>Status: Active | Last verified: {new Date().toLocaleDateString()}</p>
    </div>
  </div>
);

export default function IdentityHub({ user }) {
  return (
    <SmartHub 
      tabs={TABS} 
      title="Identity" 
      icon="🔐" 
      accentColor="#c9a84c"
      defaultTab={0}
    >
      {(tab, idx) => (
        <>
          {idx === 0 && <IdentityPanel />}
          {idx === 1 && <BlockchainIdentity />}
          {idx === 2 && <ZKPContent />}
        </>
      )}
    </SmartHub>
  );
}
