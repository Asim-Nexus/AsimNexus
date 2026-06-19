import React from 'react';
import { Link } from 'react-router-dom';

const Sidebar = ({ systemStatus }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <img src="/asimnexus-logo.png" alt="ASIMNEXUS Logo" className="logo" />
        <h2>ASIMNEXUS</h2>
        <div className={`status-dot ${systemStatus}`}></div>
      </div>
      <nav className="sidebar-nav">
        <Link to="/" className="nav-item">
          <span className="nav-icon">📊</span>
          Dashboard
        </Link>
        <Link to="/founders" className="nav-item">
          <span className="nav-icon">👥</span>
          Founders
        </Link>
        <Link to="/agents" className="nav-item">
          <span className="nav-icon">🤖</span>
          Agents
        </Link>
        <Link to="/security" className="nav-item">
          <span className="nav-icon">🔒</span>
          Security
        </Link>
        <Link to="/analytics" className="nav-item">
          <span className="nav-icon">📈</span>
          Analytics
        </Link>
        <Link to="/virtual-office" className="nav-item">
          <span className="nav-icon">🏢</span>
          Virtual Office
        </Link>
        <Link to="/chat" className="nav-item">
          <span className="nav-icon">💬</span>
          Chat
        </Link>
      </nav>
      <div className="sidebar-footer">
        <p>Version 1.0.0</p>
        <p>Status: {systemStatus}</p>
      </div>
    </aside>
  );
};

export default Sidebar;
