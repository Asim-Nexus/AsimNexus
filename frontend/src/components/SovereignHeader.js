/**
 * ASIMNEXUS Sovereign Header Component
 * ======================================
 * Main navigation and system identity display
 */

import React from 'react';
import { Brain, Crown, Activity, Shield, Database, Settings, Menu } from 'lucide-react';

const SovereignHeader = ({ systemStatus }) => {
  const getCurrentTime = () => {
    return new Date().toLocaleString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getSystemStatusText = () => {
    if (!systemStatus.connected) return 'OFFLINE';
    if (systemStatus.neural_gateway === 'active') return 'SOVEREIGN';
    if (systemStatus.neural_gateway === 'standby') return 'STANDBY';
    return 'INITIALIZING';
  };

  const getSystemStatusColor = () => {
    if (!systemStatus.connected) return 'text-red-400';
    if (systemStatus.neural_gateway === 'active') return 'text-green-400';
    if (systemStatus.neural_gateway === 'standby') return 'text-yellow-400';
    return 'text-blue-400';
  };

  return (
    <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-slate-700 shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <Brain className="w-8 h-8 text-blue-400 mr-2" />
              <div>
                <h1 className="text-2xl font-bold text-white">ASIMNEXUS</h1>
                <p className="text-xs text-slate-400">Digital Sovereign Entity</p>
              </div>
            </div>
          </div>

          {/* System Status Badge */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <div className="text-right">
                <div className={`text-sm font-bold ${getSystemStatusColor()}`}>
                  {getSystemStatusText()}
                </div>
                <div className="text-xs text-slate-400">
                  Status: {systemStatus.neural_gateway?.toUpperCase() || 'UNKNOWN'}
                </div>
              </div>
            </div>

            {/* Crown Icon for Sovereign Status */}
            {systemStatus.connected && systemStatus.neural_gateway === 'active' && (
              <div className="flex items-center">
                <Crown className="w-5 h-5 text-yellow-400" />
              </div>
            )}
          </div>

          {/* Navigation Menu */}
          <div className="flex items-center space-x-4">
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors">
              <Shield className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors">
              <Database className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors">
              <Settings className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors">
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* System Information Bar */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center space-x-6">
              <span>Version: 1.0.0</span>
              <span>Build: 2026.05.10</span>
              <span>Environment: Production</span>
            </div>
            <div className="flex items-center space-x-4">
              <span>Heartbeat: #{systemStatus.heartbeat || 0}</span>
              <span>CPU: {systemStatus.cpu_usage?.toFixed(1) || 0}%</span>
              <span>Memory: {systemStatus.memory_usage?.toFixed(1) || 0}%</span>
              <span>GPU: {systemStatus.gpu_usage?.toFixed(1) || 0}%</span>
            </div>
            <div className="text-slate-300">
              {getCurrentTime()}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Status Indicators */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
      
      {/* Neural Activity Indicator */}
      {systemStatus.connected && (
        <div className="absolute top-4 left-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-400 font-medium">Neural Core Active</span>
          </div>
        </div>
      )}

      {/* Safety System Indicator */}
      <div className="absolute top-4 right-4">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            systemStatus.safety_system === 'active' ? 'bg-green-400' : 'bg-red-400'
          }`}></div>
          <span className={`text-xs font-medium ${
            systemStatus.safety_system === 'active' ? 'text-green-400' : 'text-red-400'
          }`}>
            Safety {systemStatus.safety_system === 'active' ? 'Engaged' : 'Disengaged'}
          </span>
        </div>
      </div>
    </header>
  );
};

export default SovereignHeader;
