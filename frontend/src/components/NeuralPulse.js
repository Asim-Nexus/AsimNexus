/**
 * ASIMNEXUS Neural Pulse Monitor
 * ===============================
 * Real-time system heartbeat and performance monitoring
 */

import React from 'react';
import { Activity, Cpu, HardDrive, Wifi, Brain } from 'lucide-react';

const NeuralPulse = ({ systemStatus }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
      case 'online':
        return 'text-green-400';
      case 'offline':
        return 'text-red-400';
      default:
        return 'text-yellow-400';
    }
  };

  const getUsageColor = (usage) => {
    if (usage < 50) return 'text-green-400';
    if (usage < 80) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-xl">
      <div className="flex items-center mb-4">
        <Brain className="w-6 h-6 mr-2 text-blue-400" />
        <h2 className="text-xl font-bold text-white">Neural Pulse Monitor</h2>
        <div className={`ml-auto px-2 py-1 rounded text-xs font-semibold ${
          systemStatus.connected ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
        }`}>
          {systemStatus.connected ? 'LIVE' : 'OFFLINE'}
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-900 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Neural Gateway</div>
          <div className={`text-lg font-bold ${getStatusColor(systemStatus.neural_gateway)}`}>
            {systemStatus.neural_gateway?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
        <div className="bg-slate-900 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Safety System</div>
          <div className={`text-lg font-bold ${getStatusColor(systemStatus.safety_system)}`}>
            {systemStatus.safety_system?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
      </div>

      {/* Heartbeat */}
      <div className="bg-slate-900 rounded p-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Activity className="w-4 h-4 mr-2 text-blue-400 animate-pulse" />
            <span className="text-sm text-slate-300">Heartbeat</span>
          </div>
          <div className="text-2xl font-bold text-white">
            #{systemStatus.heartbeat || 0}
          </div>
        </div>
      </div>

      {/* System Resources */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Cpu className="w-4 h-4 mr-2 text-orange-400" />
            <span className="text-sm text-slate-300">CPU Usage</span>
          </div>
          <div className="flex items-center">
            <div className="w-24 bg-slate-700 rounded-full h-2 mr-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  systemStatus.cpu_usage < 50 ? 'bg-green-400' :
                  systemStatus.cpu_usage < 80 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${Math.min(systemStatus.cpu_usage || 0, 100)}%` }}
              ></div>
            </div>
            <span className={`text-sm font-bold ${getUsageColor(systemStatus.cpu_usage)}`}>
              {systemStatus.cpu_usage?.toFixed(1) || 0}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <HardDrive className="w-4 h-4 mr-2 text-purple-400" />
            <span className="text-sm text-slate-300">Memory Usage</span>
          </div>
          <div className="flex items-center">
            <div className="w-24 bg-slate-700 rounded-full h-2 mr-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  systemStatus.memory_usage < 50 ? 'bg-green-400' :
                  systemStatus.memory_usage < 80 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${Math.min(systemStatus.memory_usage || 0, 100)}%` }}
              ></div>
            </div>
            <span className={`text-sm font-bold ${getUsageColor(systemStatus.memory_usage)}`}>
              {systemStatus.memory_usage?.toFixed(1) || 0}%
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Wifi className="w-4 h-4 mr-2 text-cyan-400" />
            <span className="text-sm text-slate-300">GPU Usage</span>
          </div>
          <div className="flex items-center">
            <div className="w-24 bg-slate-700 rounded-full h-2 mr-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  systemStatus.gpu_usage < 50 ? 'bg-green-400' :
                  systemStatus.gpu_usage < 80 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${Math.min(systemStatus.gpu_usage || 0, 100)}%` }}
              ></div>
            </div>
            <span className={`text-sm font-bold ${getUsageColor(systemStatus.gpu_usage)}`}>
              {systemStatus.gpu_usage?.toFixed(1) || 0}%
            </span>
          </div>
        </div>
      </div>

      {/* Kill Switch Status */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Kill Switch</span>
          <div className={`px-3 py-1 rounded text-xs font-bold ${
            systemStatus.kill_switch === 'armed' 
              ? 'bg-red-900 text-red-300' 
              : 'bg-green-900 text-green-300'
          }`}>
            {systemStatus.kill_switch?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NeuralPulse;
