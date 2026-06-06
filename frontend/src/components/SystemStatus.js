/**
 * ASIMNEXUS System Status Component
 * ====================================
 * Overall system health and metrics display
 */

import React from 'react';
import { Server, Cpu, HardDrive, Wifi, Shield, Users, Cloud, Smartphone } from 'lucide-react';

const SystemStatus = ({ systemStatus }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
      case 'online':
      case 'ready':
        return 'text-green-400';
      case 'offline':
      case 'error':
        return 'text-red-400';
      case 'standby':
      case 'warning':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const getProgressBarColor = (value) => {
    if (value >= 90) return 'bg-red-500';
    if (value >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const systemMetrics = [
    {
      icon: <Server className="w-5 h-5 text-blue-400" />,
      label: 'Neural Gateway',
      status: systemStatus.neural_gateway || 'unknown',
      color: getStatusColor(systemStatus.neural_gateway)
    },
    {
      icon: <Shield className="w-5 h-5 text-purple-400" />,
      label: 'Safety System',
      status: systemStatus.safety_system || 'unknown',
      color: getStatusColor(systemStatus.safety_system)
    },
    {
      icon: <Cpu className="w-5 h-5 text-orange-400" />,
      label: 'Hardware Sync',
      status: systemStatus.hardware_status || 'active',
      color: getStatusColor('active')
    },
    {
      icon: <HardDrive className="w-5 h-5 text-cyan-400" />,
      label: 'Vector Memory',
      status: `${systemStatus.memory_count || 0} items`,
      color: 'text-cyan-400'
    },
    {
      icon: <Users className="w-5 h-5 text-green-400" />,
      label: 'Identity Manager',
      status: 'OCR Active',
      color: 'text-green-400'
    },
    {
      icon: <Smartphone className="w-5 h-5 text-pink-400" />,
      label: 'Mobile Bridge',
      status: 'Connected',
      color: 'text-pink-400'
    },
    {
      icon: <Cloud className="w-5 h-5 text-indigo-400" />,
      label: 'Cloud Connector',
      status: 'Available',
      color: 'text-indigo-400'
    }
  ];

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Shield className="w-6 h-6 mr-2 text-blue-400" />
          <h2 className="text-xl font-bold text-white">System Status</h2>
        </div>
        <div className="text-sm text-slate-400">
          Last Update: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* System Overview */}
      <div className="bg-slate-900 rounded-lg p-4 mb-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {systemStatus.heartbeat || 0}
            </div>
            <div className="text-xs text-slate-400">Heartbeat Cycles</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${
              systemStatus.connected ? 'text-green-400' : 'text-red-400'
            }`}>
              {systemStatus.connected ? 'ONLINE' : 'OFFLINE'}
            </div>
            <div className="text-xs text-slate-400">Connection Status</div>
          </div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="space-y-3">
        {systemMetrics.map((metric, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-slate-900 rounded-lg border border-slate-700">
            <div className="flex items-center space-x-3">
              {metric.icon}
              <div>
                <div className="text-sm font-medium text-white">{metric.label}</div>
                <div className={`text-xs ${metric.color}`}>{metric.status}</div>
              </div>
            </div>
            <div className="text-xs text-slate-400">
              {metric.status.includes('Active') || metric.status.includes('Online') ? '●' : '○'}
            </div>
          </div>
        ))}
      </div>

      {/* Resource Usage */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="text-sm font-semibold text-slate-300 mb-3">Resource Usage</div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-slate-300">CPU</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-slate-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(systemStatus.cpu_usage)}`}
                  style={{ width: `${Math.min(systemStatus.cpu_usage || 0, 100)}%` }}
                ></div>
              </div>
              <span className="text-sm font-medium text-white w-12 text-right">
                {systemStatus.cpu_usage?.toFixed(1) || 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <HardDrive className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-slate-300">Memory</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-slate-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(systemStatus.memory_usage)}`}
                  style={{ width: `${Math.min(systemStatus.memory_usage || 0, 100)}%` }}
                ></div>
              </div>
              <span className="text-sm font-medium text-white w-12 text-right">
                {systemStatus.memory_usage?.toFixed(1) || 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Wifi className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-slate-300">GPU</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-slate-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(systemStatus.gpu_usage)}`}
                  style={{ width: `${Math.min(systemStatus.gpu_usage || 0, 100)}%` }}
                ></div>
              </div>
              <span className="text-sm font-medium text-white w-12 text-right">
                {systemStatus.gpu_usage?.toFixed(1) || 0}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* System Actions */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="text-sm font-semibold text-slate-300 mb-3">Quick Actions</div>
        <div className="grid grid-cols-2 gap-2">
          <button className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
            System Diagnostics
          </button>
          <button className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors">
            Performance Monitor
          </button>
          <button className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded transition-colors">
            Memory Cleanup
          </button>
          <button className="px-3 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors">
            Security Audit
          </button>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
