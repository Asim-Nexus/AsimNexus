import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, AlertTriangle, CheckCircle, XCircle, Activity, Eye, Lock } from 'lucide-react';

export default function DharmaChakra() {
  const [safetyPolicies, setSafetyPolicies] = useState([
    {
      id: 'human_override',
      name: 'Human Override',
      status: 'active',
      description: 'Human intervention can override AI decisions',
      lastTriggered: '2024-01-10T14:30:00Z',
      violations: 0
    },
    {
      id: 'resource_conservation',
      name: 'Resource Conservation',
      status: 'active',
      description: 'Prevents resource exhaustion and optimizes usage',
      lastTriggered: '2024-01-10T15:45:00Z',
      violations: 2
    },
    {
      id: 'financial_stability',
      name: 'Financial Stability',
      status: 'active',
      description: 'Monitors and protects financial operations',
      lastTriggered: '2024-01-10T16:20:00Z',
      violations: 0
    },
    {
      id: 'governance_integrity',
      name: 'Governance Integrity',
      status: 'active',
      description: 'Ensures compliance with governance protocols',
      lastTriggered: '2024-01-10T13:15:00Z',
      violations: 1
    },
    {
      id: 'system_safety',
      name: 'System Safety',
      status: 'active',
      description: 'Protects system from harmful operations',
      lastTriggered: '2024-01-10T17:00:00Z',
      violations: 0
    }
  ]);

  const [recentDecisions, setRecentDecisions] = useState([
    {
      id: 1,
      type: 'approval',
      policy: 'Resource Conservation',
      action: 'Memory allocation request',
      result: 'approved',
      timestamp: '2024-01-10T17:30:00Z',
      details: 'Allocated 2GB RAM for AI model execution'
    },
    {
      id: 2,
      type: 'warning',
      policy: 'System Safety',
      action: 'File execution request',
      result: 'warning',
      timestamp: '2024-01-10T17:25:00Z',
      details: 'Suspicious file detected, requires manual review'
    },
    {
      id: 3,
      type: 'block',
      policy: 'Governance Integrity',
      action: 'Data export request',
      result: 'blocked',
      timestamp: '2024-01-10T17:20:00Z',
      details: 'Export blocked due to privacy policy violation'
    }
  ]);

  const [autonomousMode, setAutonomousMode] = useState(false);
  const [systemIntegrity, setSystemIntegrity] = useState(98.5);

  useEffect(() => {
    const interval = setInterval(() => {
      setSystemIntegrity(prev => 95 + Math.random() * 5);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'blocked': return <XCircle className="w-5 h-5 text-red-400" />;
      default: return <Activity className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-400 bg-green-900/20 border-green-700';
      case 'warning': return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
      case 'blocked': return 'text-red-400 bg-red-900/20 border-red-700';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Dharma-Chakra Visualization */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-green-300 flex items-center gap-3">
            <Shield className="w-8 h-8" />
            Dharma-Chakra Safety System
          </h2>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              System Integrity: <span className="text-green-400 font-bold">{systemIntegrity.toFixed(1)}%</span>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setAutonomousMode(!autonomousMode)}
              className={`
                px-4 py-2 rounded-lg font-medium transition-all duration-300
                ${autonomousMode 
                  ? 'bg-red-900/30 border border-red-600 text-red-300' 
                  : 'bg-green-900/30 border border-green-600 text-green-300'
                }
              `}
            >
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4" />
                {autonomousMode ? 'Manual Override' : 'Autonomous Mode'}
              </div>
            </motion.button>
          </div>
        </div>

        {/* Animated Dharma-Chakra */}
        <div className="flex justify-center mb-8">
          <div className="relative w-64 h-64">
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute inset-0 rounded-full border-2 border-green-500/30"
                style={{
                  transform: `rotate(${i * 45}deg)`,
                  transformOrigin: 'center'
                }}
                animate={{ 
                  rotate: [i * 45, i * 45 + 360],
                  scale: [1, 1.1, 1]
                }}
                transition={{ 
                  duration: 10 + i * 2,
                  repeat: Infinity,
                  ease: "linear"
                }}
              />
            ))}
            <motion.div
              className="absolute inset-8 rounded-full bg-gradient-to-br from-green-600/20 to-blue-600/20 border border-green-400/50 flex items-center justify-center"
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Shield className="w-12 h-12 text-green-400" />
            </motion.div>
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <div className="text-center">
                <div className="text-3xl font-bold text-green-300">
                  {systemIntegrity.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-400">Integrity</div>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Safety Policies Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {safetyPolicies.map((policy) => (
            <motion.div
              key={policy.id}
              whileHover={{ scale: 1.02 }}
              className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getStatusIcon(policy.status)}
                  <span className="font-medium text-gray-300">{policy.name}</span>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  policy.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-gray-600'
                }`} />
              </div>
              <div className="text-sm text-gray-400 mb-3">{policy.description}</div>
              <div className="flex items-center justify-between text-xs">
                <div className="text-gray-500">
                  Violations: <span className={policy.violations > 0 ? 'text-red-400' : 'text-green-400'}>
                    {policy.violations}
                  </span>
                </div>
                <div className="text-gray-500">
                  Last: {new Date(policy.lastTriggered).toLocaleTimeString()}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Decisions */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-green-300">Recent Safety Decisions</h3>
          <Eye className="w-5 h-5 text-gray-400" />
        </div>

        <div className="space-y-3">
          <AnimatePresence>
            {recentDecisions.map((decision) => (
              <motion.div
                key={decision.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className={`
                  p-4 rounded-lg border transition-all duration-300
                  ${getStatusColor(decision.result)}
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {getStatusIcon(decision.result)}
                      <span className="font-medium text-gray-200">{decision.policy}</span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        decision.type === 'approval' ? 'bg-green-800/50 text-green-300' :
                        decision.type === 'warning' ? 'bg-yellow-800/50 text-yellow-300' :
                        'bg-red-800/50 text-red-300'
                      }`}>
                        {decision.type.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-sm text-gray-300 mb-1">
                      Action: {decision.action}
                    </div>
                    <div className="text-xs text-gray-400">
                      {decision.details}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 ml-4">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Safety Metrics */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <h3 className="text-xl font-bold text-green-300 mb-4">Safety Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Total Violations</div>
            <div className="text-2xl font-bold text-red-300">
              {safetyPolicies.reduce((sum, p) => sum + p.violations, 0)}
            </div>
            <div className="text-xs text-gray-500 mt-1">Last 24 hours</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Active Policies</div>
            <div className="text-2xl font-bold text-green-300">
              {safetyPolicies.filter(p => p.status === 'active').length}
            </div>
            <div className="text-xs text-gray-500 mt-1">Monitoring</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Response Time</div>
            <div className="text-2xl font-bold text-blue-300">
              12ms
            </div>
            <div className="text-xs text-gray-500 mt-1">Average</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Safety Score</div>
            <div className="text-2xl font-bold text-purple-300">
              {systemIntegrity.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500 mt-1">Out of 100</div>
          </div>
        </div>
      </div>
    </div>
  );
}
