/**
 * ASIMNEXUS Dharma-Chakra Monitor
 * =================================
 * Constitutional Safety System Interface
 */

import React, { useState } from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, Lock, Unlock } from 'lucide-react';

const DharmaChakra = ({ policies, systemStatus }) => {
  const [autonomousMode, setAutonomousMode] = useState(false);
  const [expandedPolicy, setExpandedPolicy] = useState(null);

  const getPolicyIcon = (policy) => {
    if (policy.severity === 'emergency') return <AlertTriangle className="w-4 h-4 text-red-400" />;
    if (policy.severity === 'critical') return <XCircle className="w-4 h-4 text-orange-400" />;
    return <CheckCircle className="w-4 h-4 text-green-400" />;
  };

  const getPolicyStatus = (policy) => {
    return policy.immutable ? 'Immutable' : 'Mutable';
  };

  const toggleAutonomousMode = () => {
    setAutonomousMode(!autonomousMode);
    // In real implementation, this would call API to toggle mode
    console.log('Autonomous Mode:', !autonomousMode ? 'ENABLED' : 'DISABLED');
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Shield className="w-6 h-6 mr-2 text-blue-400" />
          <h2 className="text-xl font-bold text-white">Dharma-Chakra</h2>
        </div>
        <button
          onClick={toggleAutonomousMode}
          className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
            autonomousMode 
              ? 'bg-red-900 text-red-300 hover:bg-red-800' 
              : 'bg-green-900 text-green-300 hover:bg-green-800'
          }`}
        >
          {autonomousMode ? (
            <div className="flex items-center">
              <Unlock className="w-3 h-3 mr-1" />
              AUTO
            </div>
          ) : (
            <div className="flex items-center">
              <Lock className="w-3 h-3 mr-1" />
              MANUAL
            </div>
          )}
        </button>
      </div>

      {/* Safety System Status */}
      <div className="bg-slate-900 rounded p-3 mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-300">Safety System Status</span>
          <div className={`px-2 py-1 rounded text-xs font-bold ${
            systemStatus.safety_system === 'active' 
              ? 'bg-green-900 text-green-300' 
              : 'bg-red-900 text-red-300'
          }`}>
            {systemStatus.safety_system?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
      </div>

      {/* Policies List */}
      <div className="space-y-2">
        <div className="text-sm font-semibold text-slate-300 mb-2">
          Constitutional Policies ({policies.length})
        </div>
        
        {policies.map((policy, index) => (
          <div 
            key={policy.policy_id || index}
            className="bg-slate-900 rounded border border-slate-700 overflow-hidden"
          >
            <button
              onClick={() => setExpandedPolicy(expandedPolicy === policy.policy_id ? null : policy.policy_id)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-slate-800 transition-colors"
            >
              <div className="flex items-center space-x-2">
                {getPolicyIcon(policy)}
                <span className="text-sm text-white font-medium">
                  {policy.title || policy.policy_id}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-xs px-2 py-1 rounded ${
                  policy.immutable 
                    ? 'bg-blue-900 text-blue-300' 
                    : 'bg-gray-700 text-gray-300'
                }`}>
                  {getPolicyStatus(policy)}
                </span>
                <span className={`text-xs px-2 py-1 rounded ${
                  policy.severity === 'emergency' ? 'bg-red-900 text-red-300' :
                  policy.severity === 'critical' ? 'bg-orange-900 text-orange-300' :
                  'bg-green-900 text-green-300'
                }`}>
                  {policy.severity?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
            </button>
            
            {/* Expanded Policy Details */}
            {expandedPolicy === policy.policy_id && (
              <div className="px-3 py-3 border-t border-slate-700 bg-slate-800">
                <div className="text-xs text-slate-400 mb-2">
                  {policy.description}
                </div>
                {policy.rules && policy.rules.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-300 mb-1">Rules:</div>
                    <ul className="text-xs text-slate-400 space-y-1">
                      {policy.rules.map((rule, ruleIndex) => (
                        <li key={ruleIndex} className="flex items-start">
                          <span className="text-blue-400 mr-2">•</span>
                          <span>{rule}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="mt-2 pt-2 border-t border-slate-700">
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>Version: {policy.version || '1.0'}</span>
                    <span>Created: {new Date(policy.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        
        {policies.length === 0 && (
          <div className="text-center py-4 text-slate-500 text-sm">
            No constitutional policies loaded
          </div>
        )}
      </div>

      {/* Decision Logs */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="text-sm font-semibold text-slate-300 mb-2">
          Recent Decisions
        </div>
        <div className="space-y-1">
          <div className="text-xs text-slate-400 p-2 bg-slate-900 rounded">
            <div className="flex justify-between">
              <span>System Boot</span>
              <span className="text-green-400">APPROVED</span>
            </div>
          </div>
          <div className="text-xs text-slate-400 p-2 bg-slate-900 rounded">
            <div className="flex justify-between">
              <span>Neural Request: Get Status</span>
              <span className="text-green-400">APPROVED</span>
            </div>
          </div>
          <div className="text-xs text-slate-400 p-2 bg-slate-900 rounded">
            <div className="flex justify-between">
              <span>Command: System Scan</span>
              <span className="text-green-400">APPROVED</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DharmaChakra;
