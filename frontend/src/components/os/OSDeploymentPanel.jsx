import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getJSON = (path) => fetch(API + path).then(r => r.json()).catch(() => ({}));
const postJSON = (path, data) => fetch(API + path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
}).then(r => r.json()).catch(() => ({}));

export default function OSDeploymentPanel() {
  const [targets, setTargets] = useState([]);
  const [status, setStatus] = useState({});
  const [releases, setReleases] = useState([]);
  const [currentRelease, setCurrentRelease] = useState({});
  const [buildTarget, setBuildTarget] = useState('pwa');
  const [buildVersion, setBuildVersion] = useState('0.1.0');
  const [rollbackVersion, setRollbackVersion] = useState('');
  const [buildLoading, setBuildLoading] = useState(false);
  const [buildResult, setBuildResult] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState(null);

  const refreshData = useCallback(() => {
    // 1. Get targets
    getJSON('/api/deploy/targets').then(res => {
      if (res.targets) setTargets(res.targets);
    });
    // 2. Get deploy status (built artifacts)
    getJSON('/api/deploy/status').then(res => {
      setStatus(res || {});
    });
    // 3. Get current version for selected build target
    getJSON(`/api/release/current?target=${buildTarget}`).then(res => {
      setCurrentRelease(res || {});
    });
    // 4. Get list of releases
    getJSON(`/api/deploy/releases?target=${buildTarget}`).then(res => {
      setReleases(res || []);
    });
  }, [buildTarget]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const handleBuild = async (e) => {
    e.preventDefault();
    setBuildLoading(true);
    setBuildResult(null);
    try {
      const res = await postJSON('/api/deploy/build', {
        target: buildTarget,
        version: buildVersion
      });
      if (res.error) {
        setBuildResult({ success: false, message: res.error });
      } else {
        setBuildResult({ success: true, message: `Successfully built ${buildTarget} v${buildVersion}!` });
        // Automatically publish the built release for convenience
        await postJSON('/api/deploy/release', {
          version: buildVersion,
          target: buildTarget,
          checksum: res.artifact?.checksum || ''
        });
        refreshData();
      }
    } catch (err) {
      setBuildResult({ success: false, message: err.message });
    } finally {
      setBuildLoading(false);
    }
  };

  const handleRollback = async (e) => {
    e.preventDefault();
    if (!rollbackVersion) return;
    setActionLoading(true);
    setActionResult(null);
    try {
      const res = await postJSON('/api/deploy/rollback', {
        target: buildTarget,
        to_version: rollbackVersion
      });
      if (res.error) {
        setActionResult({ success: false, message: res.error });
      } else {
        setActionResult({ success: true, message: `Successfully rolled back to v${rollbackVersion}!` });
        refreshData();
      }
    } catch (err) {
      setActionResult({ success: false, message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSetCurrent = async (version, checksum) => {
    setActionLoading(true);
    setActionResult(null);
    try {
      const res = await postJSON('/api/deploy/release', {
        version,
        target: buildTarget,
        checksum
      });
      setActionResult({ success: true, message: `Activated version ${version}!` });
      refreshData();
    } catch (err) {
      setActionResult({ success: false, message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div style={{ color: '#fff', padding: '4px 0' }}>
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700,
            background: 'linear-gradient(90deg, #667eea, #a78bfa, #10b981)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            🚀 AsimNexus Deployment & Release Spine
          </h2>
          <div style={{ fontSize: '0.68rem', opacity: 0.4, marginTop: 2 }}>
            Deterministic cross-platform packaging, installation bundles, and fail-safe rollbacks
          </div>
        </div>
        <button onClick={refreshData} style={{
          padding: '6px 16px', borderRadius: 8, border: '1px solid rgba(102,126,234,0.3)',
          background: 'rgba(102,126,234,0.1)', color: '#667eea', cursor: 'pointer', fontSize: '0.78rem',
        }}>↺ Refresh</button>
      </div>

      {/* Main Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
        
        {/* Left Side: Build Console */}
        <div style={{
          background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 12, padding: 16
        }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: '#667eea' }}>🛠️ Build Packager</h3>
          
          <form onSubmit={handleBuild} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.72rem', opacity: 0.6, marginBottom: 4 }}>Target Platform</label>
              <select 
                value={buildTarget} 
                onChange={(e) => setBuildTarget(e.target.value)}
                style={{
                  width: '100%', padding: 8, borderRadius: 8, background: '#0a0a20',
                  border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem'
                }}
              >
                {targets.map(t => (
                  <option key={t} value={t}>{t.toUpperCase()}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.72rem', opacity: 0.6, marginBottom: 4 }}>Release Version</label>
              <input 
                type="text" 
                value={buildVersion} 
                onChange={(e) => setBuildVersion(e.target.value)}
                placeholder="e.g. 0.1.0"
                style={{
                  width: '100%', padding: 8, borderRadius: 8, background: '#0a0a20',
                  border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.85rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <button 
              type="submit" 
              disabled={buildLoading}
              style={{
                width: '100%', padding: 10, borderRadius: 8, background: 'linear-gradient(45deg, #667eea, #764ba2)',
                border: 'none', color: '#fff', fontWeight: 600, cursor: buildLoading ? 'not-allowed' : 'pointer',
                fontSize: '0.85rem', transition: 'opacity 0.2s', opacity: buildLoading ? 0.6 : 1
              }}
            >
              {buildLoading ? 'Building & Packaging...' : '🚀 Trigger Build'}
            </button>
          </form>

          {buildResult && (
            <div style={{
              marginTop: 12, padding: '8px 12px', borderRadius: 8,
              background: buildResult.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
              border: `1px solid ${buildResult.success ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
              color: buildResult.success ? '#10b981' : '#f87171', fontSize: '0.75rem'
            }}>
              {buildResult.message}
            </div>
          )}
        </div>

        {/* Right Side: Active Release Status */}
        <div style={{
          background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 12, padding: 16, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: '#10b981' }}>🟢 Active Release</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>Target:</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#10b981' }}>{buildTarget.toUpperCase()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>Current Version:</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{currentRelease.version || 'No active release'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>Checksum:</span>
                <span style={{ fontSize: '0.62rem', fontFamily: 'monospace', opacity: 0.8 }}>
                  {currentRelease.checksum ? currentRelease.checksum.slice(0, 16) + '...' : 'N/A'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6 }}>
                <span style={{ fontSize: '0.75rem', opacity: 0.6 }}>Published At:</span>
                <span style={{ fontSize: '0.72rem', opacity: 0.8 }}>
                  {currentRelease.published_at ? new Date(currentRelease.published_at).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Rollback Trigger Section */}
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 12, marginTop: 12 }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '0.78rem', color: '#ef4444' }}>⚠️ Rollback Spine</h4>
            <form onSubmit={handleRollback} style={{ display: 'flex', gap: 8 }}>
              <select
                value={rollbackVersion}
                onChange={(e) => setRollbackVersion(e.target.value)}
                style={{
                  flex: 1, padding: 6, borderRadius: 6, background: '#0a0a20',
                  border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.78rem'
                }}
              >
                <option value="">Select roll back target...</option>
                {releases.filter(r => r.version !== currentRelease.version).map(r => (
                  <option key={r.version} value={r.version}>v{r.version} ({new Date(r.published_at).toLocaleDateString()})</option>
                ))}
              </select>
              <button
                type="submit"
                disabled={actionLoading || !rollbackVersion}
                style={{
                  padding: '6px 12px', borderRadius: 6, background: '#ef4444',
                  border: 'none', color: '#fff', fontWeight: 600, cursor: (actionLoading || !rollbackVersion) ? 'not-allowed' : 'pointer',
                  fontSize: '0.78rem', opacity: (actionLoading || !rollbackVersion) ? 0.6 : 1
                }}
              >
                Rollback
              </button>
            </form>
          </div>
        </div>

      </div>

      {/* Quick Action Alerts */}
      {actionResult && (
        <div style={{
          marginTop: 16, padding: '8px 12px', borderRadius: 8,
          background: actionResult.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
          border: `1px solid ${actionResult.success ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
          color: actionResult.success ? '#10b981' : '#f87171', fontSize: '0.75rem'
        }}>
          {actionResult.message}
        </div>
      )}

      {/* Section: Built Artifacts Status */}
      <div style={{
        marginTop: 16, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 12, padding: 16
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: '#8b5cf6' }}>📦 Release Catalog</h3>
        
        {Object.keys(status).length === 0 ? (
          <div style={{ fontSize: '0.78rem', opacity: 0.4, textAlign: 'center', padding: '20px 0' }}>
            No artifacts packaged yet. Select a target above and click "Trigger Build".
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Object.entries(status).map(([targetName, items]) => (
              <div key={targetName} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 10 }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '0.8rem', color: '#a78bfa' }}>
                  {targetName.toUpperCase()} Releases
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
                  {items.map(item => (
                    <div 
                      key={item.version}
                      style={{
                        background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)',
                        borderRadius: 8, padding: 10, display: 'flex', flexDirection: 'column', gap: 4
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.78rem', fontWeight: 600 }}>Version {item.version}</span>
                        {currentRelease.version === item.version && currentRelease.target === targetName ? (
                          <span style={{ fontSize: '0.62rem', background: '#10b98122', border: '1px solid #10b98155', color: '#10b981', padding: '1px 6px', borderRadius: 4 }}>
                            CURRENT
                          </span>
                        ) : (
                          <button
                            onClick={() => handleSetCurrent(item.version, item.checksum)}
                            style={{
                              fontSize: '0.62rem', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                              color: '#fff', padding: '2px 6px', borderRadius: 4, cursor: 'pointer'
                            }}
                          >
                            Activate
                          </button>
                        )}
                      </div>
                      <div style={{ fontSize: '0.68rem', opacity: 0.5, wordBreak: 'break-all' }}>
                        Checksum: {item.checksum.slice(0, 24)}...
                      </div>
                      <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>
                        Size: {(item.size_bytes / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section: Installation Bundles */}
      <div style={{
        marginTop: 16, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 12, padding: 16
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: '#f59e0b' }}>📲 Install Center</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          {/* PWA Install */}
          <div style={{ background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 10, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 6 }}>🌐</div>
            <h4 style={{ margin: '0 0 4px 0', fontSize: '0.82rem' }}>PWA Install</h4>
            <p style={{ margin: '0 0 10px 0', fontSize: '0.68rem', opacity: 0.6 }}>Install directly on your device via browser shell.</p>
            <button 
              onClick={() => alert('PWA Install Triggered (Add to Home Screen)')}
              style={{
                width: '100%', padding: '6px 12px', borderRadius: 6, background: '#f59e0b',
                border: 'none', color: '#fff', fontWeight: 600, fontSize: '0.78rem', cursor: 'pointer'
              }}
            >
              Install App
            </button>
          </div>

          {/* Desktop App */}
          <div style={{ background: 'rgba(102,126,234,0.05)', border: '1px solid rgba(102,126,234,0.2)', borderRadius: 10, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 6 }}>💻</div>
            <h4 style={{ margin: '0 0 4px 0', fontSize: '0.82rem' }}>Desktop App</h4>
            <p style={{ margin: '0 0 10px 0', fontSize: '0.68rem', opacity: 0.6 }}>Download Tauri standalone bundle for Windows / macOS.</p>
            <button 
              onClick={() => alert('Downloading stand-alone Desktop installer bundle...')}
              style={{
                width: '100%', padding: '6px 12px', borderRadius: 6, background: '#667eea',
                border: 'none', color: '#fff', fontWeight: 600, fontSize: '0.78rem', cursor: 'pointer'
              }}
            >
              Download Standalone
            </button>
          </div>

          {/* Mobile App */}
          <div style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 10, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 6 }}>📱</div>
            <h4 style={{ margin: '0 0 4px 0', fontSize: '0.82rem' }}>Mobile Wrapper</h4>
            <p style={{ margin: '0 0 10px 0', fontSize: '0.68rem', opacity: 0.6 }}>Download Expo / Capacitor wrapped Android APK.</p>
            <button 
              onClick={() => alert('Downloading wrapped Mobile app APK...')}
              style={{
                width: '100%', padding: '6px 12px', borderRadius: 6, background: '#10b981',
                border: 'none', color: '#fff', fontWeight: 600, fontSize: '0.78rem', cursor: 'pointer'
              }}
            >
              Download APK
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
