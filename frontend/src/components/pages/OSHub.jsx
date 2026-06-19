/**
 * OS Hub — Lightweight using SmartHub
 * Personal + World + Control
 */
import SmartHub from '../shared/SmartHub';
import PersonalOS from '../os/PersonalOS';
import WorldOSDashboard from '../os/WorldOSDashboard';
import OSControlPanel from '../os/OSControlPanel';
import OSDeploymentPanel from '../os/OSDeploymentPanel';

const TABS = [
  { id: 'personal', icon: '👤', label: 'Personal', desc: 'Your Universe' },
  { id: 'world', icon: '🌍', label: 'World', desc: 'Global View' },
  { id: 'control', icon: '🎛️', label: 'Control', desc: 'System Settings' },
  { id: 'deploy', icon: '🚀', label: 'Deploy', desc: 'Build & Release' },
];

export default function OSHub({ user }) {
  return (
    <SmartHub 
      tabs={TABS} 
      title="OS" 
      icon="🖥️" 
      accentColor="#667eea"
      defaultTab={0}
    >
      {(tab, idx) => (
        <>
          {idx === 0 && <PersonalOS user={user} />}
          {idx === 1 && <WorldOSDashboard />}
          {idx === 2 && <OSControlPanel />}
          {idx === 3 && <OSDeploymentPanel />}
        </>
      )}
    </SmartHub>
  );
}
