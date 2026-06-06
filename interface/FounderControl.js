/**
 * ASIMNEXUS Founder Control Center
 * ================================
 * React component for founder dashboard
 * Monitor and control 15 ASIMNEXUS founder clones
 * Real-time status, performance metrics, and control actions
 */

import React, { useState, useEffect } from 'react';

const FounderControlCenter = () => {
  const [clones, setClones] = useState([]);
  const [selectedClone, setSelectedClone] = useState(null);
  const [activeTab, setActiveTab] = useState('clones');
  const [systemStatus, setSystemStatus] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching clone data
    const fetchClones = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockClones = Array.from({ length: 15 }, (_, i) => ({
        id: `clone_${i + 1}`,
        name: `Founder Clone ${i + 1}`,
        status: Math.random() > 0.2 ? 'active' : 'idle',
        health: Math.floor(Math.random() * 20) + 80,
        performance: Math.floor(Math.random() * 30) + 70,
        cpu: Math.floor(Math.random() * 40) + 30,
        memory: Math.floor(Math.random() * 50) + 30,
        network: Math.floor(Math.random() * 30) + 50,
        gpu: Math.floor(Math.random() * 40) + 40,
        tasksCompleted: Math.floor(Math.random() * 100),
        earnings: Math.floor(Math.random() * 10000),
        lastActive: new Date().toISOString()
      }));
      
      setClones(mockClones);
      setSystemStatus({
        totalClones: 15,
        activeClones: mockClones.filter(c => c.status === 'active').length,
        totalTasks: mockClones.reduce((sum, c) => sum + c.tasksCompleted, 0),
        totalEarnings: mockClones.reduce((sum, c) => sum + c.earnings, 0),
        systemHealth: 95,
        uptime: 99.99
      });
      setLoading(false);
    };

    fetchClones();
    const interval = setInterval(fetchClones, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const handleCloneSelect = (clone) => {
    setSelectedClone(clone);
    setActiveTab('details');
  };

  const handleCloneAction = async (action, cloneId) => {
    console.log(`Action: ${action} on clone ${cloneId}`);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    // Update clone status
    setClones(clones.map(c => 
      c.id === cloneId 
        ? { ...c, status: action === 'activate' ? 'active' : 'idle' }
        : c
    ));
  };

  const renderClonesTab = () => (
    <div className="clones-grid">
      {clones.map(clone => (
        <div 
          key={clone.id} 
          className={`clone-card ${clone.status}`}
          onClick={() => handleCloneSelect(clone)}
        >
          <div className="clone-header">
            <h3>{clone.name}</h3>
            <span className={`status-badge ${clone.status}`}>
              {clone.status}
            </span>
          </div>
          <div className="clone-metrics">
            <div className="metric">
              <span className="label">Health</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill health" 
                  style={{ width: `${clone.health}%` }}
                />
              </div>
              <span className="value">{clone.health}%</span>
            </div>
            <div className="metric">
              <span className="label">Performance</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill performance" 
                  style={{ width: `${clone.performance}%` }}
                />
              </div>
              <span className="value">{clone.performance}%</span>
            </div>
            <div className="metric">
              <span className="label">Tasks</span>
              <span className="value">{clone.tasksCompleted}</span>
            </div>
            <div className="metric">
              <span className="label">Earnings</span>
              <span className="value">${clone.earnings.toLocaleString()}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderDetailsTab = () => {
    if (!selectedClone) return <div className="no-selection">Select a clone to view details</div>;

    return (
      <div className="clone-details">
        <div className="details-header">
          <h2>{selectedClone.name}</h2>
          <span className={`status-badge ${selectedClone.status}`}>
            {selectedClone.status}
          </span>
        </div>

        <div className="details-section">
          <h3>Performance Metrics</h3>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="label">CPU Usage</span>
              <span className="value">{selectedClone.cpu}%</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill cpu" 
                  style={{ width: `${selectedClone.cpu}%` }}
                />
              </div>
            </div>
            <div className="metric-card">
              <span className="label">Memory Usage</span>
              <span className="value">{selectedClone.memory}%</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill memory" 
                  style={{ width: `${selectedClone.memory}%` }}
                />
              </div>
            </div>
            <div className="metric-card">
              <span className="label">Network</span>
              <span className="value">{selectedClone.network}%</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill network" 
                  style={{ width: `${selectedClone.network}%` }}
                />
              </div>
            </div>
            <div className="metric-card">
              <span className="label">GPU Usage</span>
              <span className="value">{selectedClone.gpu}%</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill gpu" 
                  style={{ width: `${selectedClone.gpu}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="details-section">
          <h3>Actions</h3>
          <div className="actions-grid">
            <button 
              className="action-btn activate"
              onClick={() => handleCloneAction('activate', selectedClone.id)}
            >
              Activate
            </button>
            <button 
              className="action-btn deactivate"
              onClick={() => handleCloneAction('deactivate', selectedClone.id)}
            >
              Deactivate
            </button>
            <button 
              className="action-btn restart"
              onClick={() => handleCloneAction('restart', selectedClone.id)}
            >
              Restart
            </button>
            <button 
              className="action-btn logs"
              onClick={() => handleCloneAction('logs', selectedClone.id)}
            >
              View Logs
            </button>
          </div>
        </div>

        <div className="details-section">
          <h3>Task History</h3>
          <div className="task-history">
            <div className="task-item">
              <span className="task-name">Document Verification</span>
              <span className="task-status completed">Completed</span>
              <span className="task-time">2 hours ago</span>
            </div>
            <div className="task-item">
              <span className="task-name">Data Analysis</span>
              <span className="task-status completed">Completed</span>
              <span className="task-time">5 hours ago</span>
            </div>
            <div className="task-item">
              <span className="task-name">System Audit</span>
              <span className="task-status in-progress">In Progress</span>
              <span className="task-time">1 hour ago</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderPerformanceTab = () => (
    <div className="performance-overview">
      <div className="performance-summary">
        <div className="summary-card">
          <h3>Total Clones</h3>
          <span className="value">{systemStatus.totalClones}</span>
        </div>
        <div className="summary-card">
          <h3>Active Clones</h3>
          <span className="value">{systemStatus.activeClones}</span>
        </div>
        <div className="summary-card">
          <h3>Total Tasks</h3>
          <span className="value">{systemStatus.totalTasks}</span>
        </div>
        <div className="summary-card">
          <h3>Total Earnings</h3>
          <span className="value">${systemStatus.totalEarnings?.toLocaleString()}</span>
        </div>
        <div className="summary-card">
          <h3>System Health</h3>
          <span className="value">{systemStatus.systemHealth}%</span>
        </div>
        <div className="summary-card">
          <h3>Uptime</h3>
          <span className="value">{systemStatus.uptime}%</span>
        </div>
      </div>

      <div className="performance-chart">
        <h3>Performance Over Time</h3>
        <div className="chart-placeholder">
          {/* Chart would be rendered here using a library like Chart.js */}
          <p>Performance chart visualization</p>
        </div>
      </div>
    </div>
  );

  const renderSystemTab = () => (
    <div className="system-overview">
      <div className="system-metrics">
        <h3>System Metrics</h3>
        <div className="metrics-list">
          <div className="metric-item">
            <span className="label">Constitutional Compliance</span>
            <span className="value">98.5%</span>
          </div>
          <div className="metric-item">
            <span className="label">Data Privacy Compliance</span>
            <span className="value">100%</span>
          </div>
          <div className="metric-item">
            <span className="label">Security Status</span>
            <span className="value secure">Secure</span>
          </div>
          <div className="metric-item">
            <span className="label">Government Control</span>
            <span className="value">51%</span>
          </div>
          <div className="metric-item">
            <span className="label">Private Sector Control</span>
            <span className="value">49%</span>
          </div>
        </div>
      </div>

      <div className="system-alerts">
        <h3>Recent Alerts</h3>
        <div className="alerts-list">
          <div className="alert-item info">
            <span className="alert-time">10 minutes ago</span>
            <span className="alert-message">System backup completed successfully</span>
          </div>
          <div className="alert-item warning">
            <span className="alert-time">1 hour ago</span>
            <span className="alert-message">High CPU usage detected on Clone 3</span>
          </div>
          <div className="alert-item success">
            <span className="alert-time">2 hours ago</span>
            <span className="alert-message">Constitutional audit passed</span>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return <div className="loading">Loading Founder Control Center...</div>;
  }

  return (
    <div className="founder-control-center">
      <div className="header">
        <h1>🌍 ASIMNEXUS Founder Control Center</h1>
        <div className="header-stats">
          <span>Active Clones: {systemStatus.activeClones}/{systemStatus.totalClones}</span>
          <span>System Health: {systemStatus.systemHealth}%</span>
          <span>Uptime: {systemStatus.uptime}%</span>
        </div>
      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'clones' ? 'active' : ''}`}
          onClick={() => setActiveTab('clones')}
        >
          Clones
        </button>
        <button 
          className={`tab ${activeTab === 'details' ? 'active' : ''}`}
          onClick={() => setActiveTab('details')}
        >
          Details
        </button>
        <button 
          className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button 
          className={`tab ${activeTab === 'system' ? 'active' : ''}`}
          onClick={() => setActiveTab('system')}
        >
          System
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'clones' && renderClonesTab()}
        {activeTab === 'details' && renderDetailsTab()}
        {activeTab === 'performance' && renderPerformanceTab()}
        {activeTab === 'system' && renderSystemTab()}
      </div>

      <style jsx>{`
        .founder-control-center {
          padding: 20px;
          font-family: Arial, sans-serif;
          background: #1a1a2e;
          color: #fff;
          min-height: 100vh;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding: 20px;
          background: #16213e;
          border-radius: 10px;
        }

        .header h1 {
          margin: 0;
          font-size: 24px;
        }

        .header-stats {
          display: flex;
          gap: 20px;
        }

        .tabs {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
        }

        .tab {
          padding: 10px 20px;
          background: #16213e;
          border: none;
          color: #fff;
          cursor: pointer;
          border-radius: 5px;
          transition: background 0.3s;
        }

        .tab:hover {
          background: #0f3460;
        }

        .tab.active {
          background: #e94560;
        }

        .clones-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }

        .clone-card {
          background: #16213e;
          padding: 20px;
          border-radius: 10px;
          cursor: pointer;
          transition: transform 0.3s, box-shadow 0.3s;
        }

        .clone-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 5px 15px rgba(233, 69, 96, 0.3);
        }

        .clone-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }

        .status-badge {
          padding: 5px 10px;
          border-radius: 15px;
          font-size: 12px;
        }

        .status-badge.active {
          background: #4caf50;
        }

        .status-badge.idle {
          background: #ff9800;
        }

        .clone-metrics {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .metric {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .metric .label {
          width: 100px;
          font-size: 14px;
        }

        .progress-bar {
          flex: 1;
          height: 8px;
          background: #0f3460;
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          transition: width 0.3s;
        }

        .progress-fill.health { background: #4caf50; }
        .progress-fill.performance { background: #2196f3; }
        .progress-fill.cpu { background: #ff9800; }
        .progress-fill.memory { background: #9c27b0; }
        .progress-fill.network { background: #00bcd4; }
        .progress-fill.gpu { background: #e91e63; }

        .metric .value {
          width: 50px;
          text-align: right;
          font-weight: bold;
        }

        .loading {
          text-align: center;
          padding: 50px;
          font-size: 18px;
        }
      `}</style>
    </div>
  );
};

export default FounderControlCenter;
