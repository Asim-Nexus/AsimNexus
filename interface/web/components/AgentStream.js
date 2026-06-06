import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Activity, Cpu, Shield, Eye, Terminal, Zap, AlertCircle } from 'lucide-react';

export default function AgentStream() {
  const [agents, setAgents] = useState([
    {
      id: 'sys-001',
      name: 'SystemOptimizer',
      type: 'maintenance',
      status: 'active',
      task: 'Cleaning temp files',
      progress: 75,
      cpu: 15,
      memory: 256,
      lastActivity: '2024-01-10T17:30:00Z',
      logs: [
        { time: '17:30:00', level: 'info', message: 'Starting disk cleanup' },
        { time: '17:30:15', level: 'info', message: 'Found 2.3GB temp files' },
        { time: '17:30:30', level: 'warning', message: 'Registry cleanup in progress' }
      ]
    },
    {
      id: 'vis-002',
      name: 'ScreenAnalyst',
      type: 'vision',
      status: 'active',
      task: 'OCR processing document',
      progress: 45,
      cpu: 35,
      memory: 512,
      lastActivity: '2024-01-10T17:28:00Z',
      logs: [
        { time: '17:28:00', level: 'info', message: 'Screen capture initiated' },
        { time: '17:28:05', level: 'info', message: 'Detected text region' },
        { time: '17:28:15', level: 'info', message: 'OCR processing: 45% complete' }
      ]
    },
    {
      id: 'sec-003',
      name: 'SandboxExecutor',
      type: 'security',
      status: 'idle',
      task: 'Monitoring for threats',
      progress: 0,
      cpu: 5,
      memory: 128,
      lastActivity: '2024-01-10T17:25:00Z',
      logs: [
        { time: '17:25:00', level: 'info', message: 'Sandbox environment ready' },
        { time: '17:25:30', level: 'info', message: 'No threats detected' }
      ]
    },
    {
      id: 'hw-004',
      name: 'RTXStressAdaptor',
      type: 'hardware',
      status: 'active',
      task: 'GPU temperature monitoring',
      progress: 100,
      cpu: 8,
      memory: 64,
      lastActivity: '2024-01-10T17:32:00Z',
      logs: [
        { time: '17:32:00', level: 'info', message: 'GPU temp: 58°C' },
        { time: '17:32:15', level: 'info', message: 'Performance mode: Balanced' },
        { time: '17:32:30', level: 'info', message: 'Fan speed: 65%' }
      ]
    },
    {
      id: 'orc-005',
      name: 'Orchestrator',
      type: 'core',
      status: 'active',
      task: 'Coordinating agents',
      progress: 100,
      cpu: 25,
      memory: 1024,
      lastActivity: '2024-01-10T17:33:00Z',
      logs: [
        { time: '17:33:00', level: 'info', message: '5 agents online' },
        { time: '17:33:15', level: 'info', message: 'Task distribution optimized' },
        { time: '17:33:30', level: 'success', message: 'All systems nominal' }
      ]
    },
    {
      id: 'mcp-006',
      name: 'MCPConnector',
      type: 'integration',
      status: 'active',
      task: 'API data synchronization',
      progress: 60,
      cpu: 12,
      memory: 384,
      lastActivity: '2024-01-10T17:31:00Z',
      logs: [
        { time: '17:31:00', level: 'info', message: 'Connecting to external APIs' },
        { time: '17:31:20', level: 'info', message: 'Syncing 3 data sources' },
        { time: '17:31:40', level: 'warning', message: 'Rate limit approaching' }
      ]
    },
    {
      id: 'gov-007',
      name: 'GovernanceLayer',
      type: 'governance',
      status: 'active',
      task: 'Policy enforcement',
      progress: 100,
      cpu: 10,
      memory: 256,
      lastActivity: '2024-01-10T17:29:00Z',
      logs: [
        { time: '17:29:00', level: 'info', message: 'Compliance check passed' },
        { time: '17:29:15', level: 'info', message: '3 policies active' },
        { time: '17:29:30', level: 'success', message: 'No violations detected' }
      ]
    },
    {
      id: 'fin-008',
      name: 'FinanceEngine',
      type: 'finance',
      status: 'active',
      task: 'Budget monitoring',
      progress: 85,
      cpu: 18,
      memory: 512,
      lastActivity: '2024-01-10T17:27:00Z',
      logs: [
        { time: '17:27:00', level: 'info', message: 'Processing transactions' },
        { time: '17:27:20', level: 'info', message: 'Budget utilization: 67%' },
        { time: '17:27:40', level: 'info', message: 'Market analysis complete' }
      ]
    }
  ]);

  const [selectedAgent, setSelectedAgent] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prevAgents => 
        prevAgents.map(agent => ({
          ...agent,
          progress: agent.status === 'active' ? 
            Math.min(100, agent.progress + Math.random() * 5) : agent.progress,
          cpu: Math.max(0, agent.cpu + (Math.random() - 0.5) * 10),
          lastActivity: new Date().toISOString(),
          logs: Math.random() > 0.7 ? [
            ...agent.logs.slice(-4),
            {
              time: new Date().toLocaleTimeString(),
              level: ['info', 'warning', 'success'][Math.floor(Math.random() * 3)],
              message: generateLogMessage(agent.type)
            }
          ] : agent.logs
        }))
      );
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const generateLogMessage = (agentType) => {
    const messages = {
      maintenance: [
        'System optimization in progress',
        'Memory cleanup completed',
        'Registry scan running',
        'Performance metrics updated'
      ],
      vision: [
        'OCR processing complete',
        'Screen region analyzed',
        'Text extraction successful',
        'Vision data cached'
      ],
      security: [
        'Security scan initiated',
        'No threats detected',
        'Sandbox verification complete',
        'Firewall rules updated'
      ],
      hardware: [
        'GPU temperature normal',
        'Performance mode adjusted',
        'Fan speed optimized',
        'Hardware metrics collected'
      ],
      core: [
        'Agent coordination active',
        'Task distribution updated',
        'System health check passed',
        'Orchestration cycle complete'
      ],
      integration: [
        'API sync in progress',
        'Data pipeline active',
        'Connection established',
        'Integration metrics updated'
      ],
      governance: [
        'Policy compliance check',
        'Governance rules enforced',
        'Audit trail updated',
        'Regulatory validation passed'
      ],
      finance: [
        'Transaction processed',
        'Budget analysis complete',
        'Market data updated',
        'Financial metrics calculated'
      ]
    };
    
    const typeMessages = messages[agentType] || messages.core;
    return typeMessages[Math.floor(Math.random() * typeMessages.length)];
  };

  const getAgentIcon = (type) => {
    const icons = {
      maintenance: Cpu,
      vision: Eye,
      security: Shield,
      hardware: Zap,
      core: Activity,
      integration: Terminal,
      governance: Shield,
      finance: Activity
    };
    return icons[type] || Activity;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-900/20 border-green-700';
      case 'idle': return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
      case 'error': return 'text-red-400 bg-red-900/20 border-red-700';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-700';
    }
  };

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'success': return 'text-green-400';
      default: return 'text-blue-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Agent Overview */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-green-300 flex items-center gap-3">
            <Users className="w-8 h-8" />
            Digital Workforce Stream
          </h2>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              Active: <span className="text-green-400 font-bold">
                {agents.filter(a => a.status === 'active').length}
              </span> / {agents.length}
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setAutoScroll(!autoScroll)}
              className={`
                px-3 py-1 rounded-lg text-sm font-medium transition-all duration-300
                ${autoScroll 
                  ? 'bg-green-900/30 border border-green-600 text-green-300' 
                  : 'bg-gray-900/30 border border-gray-600 text-gray-300'
                }
              `}
            >
              {autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
            </motion.button>
          </div>
        </div>

        {/* Agent Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {agents.map((agent) => {
            const Icon = getAgentIcon(agent.type);
            return (
              <motion.div
                key={agent.id}
                whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedAgent(agent)}
                className={`
                  bg-gray-800/50 rounded-lg p-4 border cursor-pointer transition-all duration-300
                  ${selectedAgent?.id === agent.id 
                    ? 'border-green-400 shadow-lg shadow-green-500/25' 
                    : 'border-gray-700 hover:border-green-600'
                  }
                `}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-5 h-5 text-blue-400" />
                    <span className="font-medium text-gray-200 text-sm">{agent.name}</span>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'
                  }`} />
                </div>
                
                <div className="text-xs text-gray-400 mb-2">{agent.task}</div>
                
                {agent.status === 'active' && (
                  <div className="mb-2">
                    <div className="w-full bg-gray-700 rounded-full h-1">
                      <motion.div
                        className="h-1 rounded-full bg-green-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${agent.progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round(agent.progress)}% complete
                    </div>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div>CPU: {Math.round(agent.cpu)}%</div>
                  <div>RAM: {agent.memory}MB</div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Selected Agent Details */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-green-300">
                {selectedAgent.name} - Live Stream
              </h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedAgent(null)}
                className="px-3 py-1 rounded-lg bg-gray-800 border border-gray-600 text-gray-300 text-sm"
              >
                Close
              </motion.button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Agent Info */}
              <div>
                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 mb-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-400">Type</div>
                      <div className="text-gray-200 font-medium capitalize">{selectedAgent.type}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Status</div>
                      <div className={`font-medium capitalize ${getStatusColor(selectedAgent.status)}`}>
                        {selectedAgent.status}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400">CPU Usage</div>
                      <div className="text-gray-200 font-medium">{Math.round(selectedAgent.cpu)}%</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Memory</div>
                      <div className="text-gray-200 font-medium">{selectedAgent.memory}MB</div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="text-gray-400 text-sm mb-2">Current Task</div>
                  <div className="text-gray-200 font-medium mb-2">{selectedAgent.task}</div>
                  {selectedAgent.status === 'active' && (
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <motion.div
                        className="h-2 rounded-full bg-green-500"
                        animate={{ width: `${selectedAgent.progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Live Logs */}
              <div>
                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-gray-400 text-sm">Live Logs</div>
                    <AlertCircle className="w-4 h-4 text-yellow-400 animate-pulse" />
                  </div>
                  <div className="h-64 overflow-y-auto space-y-2 font-mono text-xs">
                    <AnimatePresence>
                      {selectedAgent.logs.map((log, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`
                            p-2 rounded border-l-2
                            ${log.level === 'error' ? 'border-red-400 bg-red-900/10' :
                              log.level === 'warning' ? 'border-yellow-400 bg-yellow-900/10' :
                              log.level === 'success' ? 'border-green-400 bg-green-900/10' :
                              'border-blue-400 bg-blue-900/10'
                            }
                          `}
                        >
                          <div className="flex items-start gap-2">
                            <span className="text-gray-500">{log.time}</span>
                            <span className={`font-medium ${getLogLevelColor(log.level)}`}>
                              [{log.level.toUpperCase()}]
                            </span>
                            <span className="text-gray-300 flex-1">{log.message}</span>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* System Metrics */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <h3 className="text-xl font-bold text-green-300 mb-4">Workforce Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Total CPU Usage</div>
            <div className="text-2xl font-bold text-blue-300">
              {Math.round(agents.reduce((sum, a) => sum + a.cpu, 0) / agents.length)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Average across agents</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Total Memory</div>
            <div className="text-2xl font-bold text-green-300">
              {Math.round(agents.reduce((sum, a) => sum + a.memory, 0) / 1024)}GB
            </div>
            <div className="text-xs text-gray-500 mt-1">Combined usage</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Active Tasks</div>
            <div className="text-2xl font-bold text-yellow-300">
              {agents.filter(a => a.status === 'active').length}
            </div>
            <div className="text-xs text-gray-500 mt-1">Currently running</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Avg Progress</div>
            <div className="text-2xl font-bold text-purple-300">
              {Math.round(agents.filter(a => a.status === 'active')
                .reduce((sum, a) => sum + a.progress, 0) / 
                Math.max(1, agents.filter(a => a.status === 'active').length))}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Task completion</div>
          </div>
        </div>
      </div>
    </div>
  );
}
