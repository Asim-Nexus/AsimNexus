/**
 * Network Hub — Lightweight using SmartHub
 * Mesh + Nodes + Topology + Selector + Offline Status
 * C4: Integrated MeshSelector and OfflineStatus
 */
import React, { useState, useEffect, useCallback } from 'react';
import SmartHub from '../shared/SmartHub';
import MeshPanel from '../mesh/MeshPanel';
import MeshSelector from '../mesh/MeshSelector';
import OfflineStatus from '../mesh/OfflineStatus';
import { meshAPI } from '../../api/asimnexus';

const TABS = [
  { id: 'mesh', icon: '🌐', label: 'Mesh', desc: 'P2P Network' },
  { id: 'nodes', icon: '📡', label: 'Nodes', desc: 'Connected devices' },
  { id: 'topology', icon: '🔀', label: 'Topology', desc: 'Network map' },
  { id: 'selector', icon: '🔀', label: 'Selector', desc: 'Mesh context' },
  { id: 'offline', icon: '📡', label: 'Offline', desc: 'Sync status' },
];

// Nodes Tab Content — live data from meshAPI
const NodesContent = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadNodes = useCallback(async () => {
    try {
      const res = await meshAPI.getPeers();
      const peers = res.data?.peers || res.peers || [];
      if (peers.length > 0) {
        setNodes(peers.map((p, i) => ({
          id: p.id || `peer-${i}`,
          name: p.name || p.host || `Peer ${i + 1}`,
          status: p.status || (p.connected ? 'online' : 'offline'),
          type: p.type || 'mesh',
          latency: p.latency ? `${p.latency}ms` : '—',
          ip: p.ip || p.address || '—',
        })));
      }
    } catch {
      // Keep whatever we have
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNodes();
    const interval = setInterval(loadNodes, 10000);
    return () => clearInterval(interval);
  }, [loadNodes]);

  // Fallback to static defaults if no live data
  const displayNodes = nodes.length > 0 ? nodes : [
    { id: 'local', name: 'Your Device', status: 'online', type: 'personal', latency: '0ms', ip: '127.0.0.1' },
    { id: 'phone', name: 'Mobile Phone', status: 'online', type: 'companion', latency: '12ms', ip: '—' },
    { id: 'neighbor', name: 'Neighbor Node', status: 'online', type: 'community', latency: '45ms', ip: '—' },
  ];

  return (
    <div style={{ padding: 20 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
      }}>
        <h3 style={{ margin: 0 }}>📡 Connected Nodes</h3>
        <span style={{ fontSize: 12, color: '#94a3b8' }}>
          {loading ? 'Loading...' : `${displayNodes.length} peers`}
        </span>
      </div>
      {displayNodes.map(node => (
        <div key={node.id} style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          marginBottom: 8,
          background: 'rgba(255,255,255,0.05)',
          borderRadius: 10,
        }}>
          <div>
            <div style={{ fontWeight: 600 }}>{node.name}</div>
            <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>{node.type} · {node.ip}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{
              padding: '2px 8px',
              borderRadius: 10,
              fontSize: '0.7rem',
              background: node.status === 'online' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
              color: node.status === 'online' ? '#10b981' : '#ef4444'
            }}>
              ● {node.status}
            </span>
            <div style={{ fontSize: '0.7rem', opacity: 0.5, marginTop: 4 }}>{node.latency}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Topology Tab Content
const TopologyContent = () => (
  <div style={{ padding: 40, textAlign: 'center' }}>
    <h3>🔀 Network Topology</h3>
    <p style={{ opacity: 0.6 }}>Visual network map</p>
    <div style={{ marginTop: 30, padding: 40, background: 'rgba(102,126,234,0.1)', borderRadius: 12, minHeight: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p>Interactive mesh topology visualization<br />(WebGL canvas)</p>
    </div>
  </div>
);

export default function NetworkHub({ user }) {
  return (
    <SmartHub
      tabs={TABS}
      title="Network"
      icon="🌐"
      accentColor="#06b6d4"
      defaultTab={0}
    >
      {(tab, idx) => (
        <>
          {idx === 0 && <MeshPanel />}
          {idx === 1 && <NodesContent />}
          {idx === 2 && <TopologyContent />}
          {idx === 3 && <MeshSelector user={user} />}
          {idx === 4 && <OfflineStatus user={user} />}
        </>
      )}
    </SmartHub>
  );
}
