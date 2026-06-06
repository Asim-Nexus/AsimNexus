import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Crown, Activity, DollarSign, Shield, Settings, Power, TrendingUp, AlertTriangle, CheckCircle, Clock, Globe, Lock } from 'lucide-react';

export default function FoundersPortal() {
  const [founderAgents, setFounderAgents] = useState([
    {
      id: 'clone-001',
      name: 'Nexus Clone Alpha',
      type: 'founder_clone',
      status: 'active',
      health: 95,
      performance: 88,
      uptime: '24d 15h',
      location: 'Kathmandu, Nepal',
      subscription: 'premium',
      billing: {
        plan: 'Premium Founder',
        cost: 299,
        next_billing: '2024-02-10',
        auto_renew: true
      },
      resources: {
        cpu: 45,
        memory: 62,
        gpu: 78,
        storage: 34
      },
      last_activity: '2024-01-10T17:45:00Z',
      tasks_completed: 1247,
      alerts: 0
    },
    {
      id: 'clone-002',
      name: 'Nexus Clone Beta',
      type: 'founder_clone',
      status: 'active',
      health: 92,
      performance: 91,
      uptime: '18d 3h',
      location: 'Pokhara, Nepal',
      subscription: 'premium',
      billing: {
        plan: 'Premium Founder',
        cost: 299,
        next_billing: '2024-02-10',
        auto_renew: true
      },
      resources: {
        cpu: 52,
        memory: 71,
        gpu: 65,
        storage: 41
      },
      last_activity: '2024-01-10T17:30:00Z',
      tasks_completed: 982,
      alerts: 1
    },
    {
      id: 'clone-003',
      name: 'Nexus Clone Gamma',
      type: 'founder_clone',
      status: 'idle',
      health: 88,
      performance: 85,
      uptime: '12d 8h',
      location: 'Biratnagar, Nepal',
      subscription: 'standard',
      billing: {
        plan: 'Standard Founder',
        cost: 149,
        next_billing: '2024-02-05',
        auto_renew: false
      },
      resources: {
        cpu: 15,
        memory: 28,
        gpu: 12,
        storage: 22
      },
      last_activity: '2024-01-10T14:20:00Z',
      tasks_completed: 654,
      alerts: 0
    },
    {
      id: 'agent-004',
      name: 'SystemOptimizer Pro',
      type: 'system_agent',
      status: 'active',
      health: 98,
      performance: 94,
      uptime: '30d 0h',
      location: 'Global Cloud',
      subscription: 'enterprise',
      billing: {
        plan: 'Enterprise Agent',
        cost: 499,
        next_billing: '2024-02-01',
        auto_renew: true
      },
      resources: {
        cpu: 35,
        memory: 45,
        gpu: 0,
        storage: 12
      },
      last_activity: '2024-01-10T17:50:00Z',
      tasks_completed: 2156,
      alerts: 0
    },
    {
      id: 'agent-005',
      name: 'ScreenAnalyst Elite',
      type: 'vision_agent',
      status: 'active',
      health: 91,
      performance: 87,
      uptime: '25d 12h',
      location: 'Singapore',
      subscription: 'premium',
      billing: {
        plan: 'Premium Vision',
        cost: 349,
        next_billing: '2024-02-15',
        auto_renew: true
      },
      resources: {
        cpu: 68,
        memory: 74,
        gpu: 89,
        storage: 56
      },
      last_activity: '2024-01-10T17:35:00Z',
      tasks_completed: 1876,
      alerts: 2
    },
    {
      id: 'agent-006',
      name: 'SandboxExecutor Max',
      type: 'security_agent',
      status: 'active',
      health: 96,
      performance: 92,
      uptime: '28d 6h',
      location: 'Frankfurt, Germany',
      subscription: 'enterprise',
      billing: {
        plan: 'Enterprise Security',
        cost: 599,
        next_billing: '2024-02-01',
        auto_renew: true
      },
      resources: {
        cpu: 42,
        memory: 58,
        gpu: 15,
        storage: 28
      },
      last_activity: '2024-01-10T17:40:00Z',
      tasks_completed: 1543,
      alerts: 0
    },
    {
      id: 'agent-007',
      name: 'RTX Stress Master',
      type: 'hardware_agent',
      status: 'active',
      health: 94,
      performance: 90,
      uptime: '22d 18h',
      location: 'Local RTX 2060',
      subscription: 'premium',
      billing: {
        plan: 'Hardware Optimizer',
        cost: 199,
        next_billing: '2024-02-10',
        auto_renew: true
      },
      resources: {
        cpu: 25,
        memory: 32,
        gpu: 85,
        storage: 8
      },
      last_activity: '2024-01-10T17:42:00Z',
      tasks_completed: 892,
      alerts: 0
    },
    {
      id: 'agent-008',
      name: 'Orchestrator Prime',
      type: 'core_agent',
      status: 'active',
      health: 99,
      performance: 96,
      uptime: '45d 0h',
      location: 'Core System',
      subscription: 'enterprise',
      billing: {
        plan: 'Core Orchestrator',
        cost: 799,
        next_billing: '2024-02-01',
        auto_renew: true
      },
      resources: {
        cpu: 78,
        memory: 82,
        gpu: 45,
        storage: 34
      },
      last_activity: '2024-01-10T17:55:00Z',
      tasks_completed: 3421,
      alerts: 0
    },
    {
      id: 'agent-009',
      name: 'MCP Connector Pro',
      type: 'integration_agent',
      status: 'active',
      health: 93,
      performance: 88,
      uptime: '20d 14h',
      location: 'AWS Mumbai',
      subscription: 'premium',
      billing: {
        plan: 'Integration Pro',
        cost: 249,
        next_billing: '2024-02-12',
        auto_renew: true
      },
      resources: {
        cpu: 38,
        memory: 52,
        gpu: 8,
        storage: 18
      },
      last_activity: '2024-01-10T17:38:00Z',
      tasks_completed: 1234,
      alerts: 1
    },
    {
      id: 'agent-010',
      name: 'Governance Sentinel',
      type: 'governance_agent',
      status: 'active',
      health: 97,
      performance: 93,
      uptime: '35d 8h',
      location: 'Global Network',
      subscription: 'enterprise',
      billing: {
        plan: 'Governance Shield',
        cost: 449,
        next_billing: '2024-02-01',
        auto_renew: true
      },
      resources: {
        cpu: 28,
        memory: 41,
        gpu: 5,
        storage: 12
      },
      last_activity: '2024-01-10T17:48:00Z',
      tasks_completed: 1876,
      alerts: 0
    },
    {
      id: 'agent-011',
      name: 'Finance Engine Plus',
      type: 'finance_agent',
      status: 'active',
      health: 95,
      performance: 90,
      uptime: '26d 16h',
      location: 'Zurich, Switzerland',
      subscription: 'premium',
      billing: {
        plan: 'Finance Pro',
        cost: 399,
        next_billing: '2024-02-08',
        auto_renew: true
      },
      resources: {
        cpu: 45,
        memory: 58,
        gpu: 22,
        storage: 24
      },
      last_activity: '2024-01-10T17:44:00Z',
      tasks_completed: 1567,
      alerts: 0
    },
    {
      id: 'agent-012',
      name: 'Resource Manager Max',
      type: 'resource_agent',
      status: 'idle',
      health: 89,
      performance: 82,
      uptime: '15d 4h',
      location: 'Tokyo, Japan',
      subscription: 'standard',
      billing: {
        plan: 'Resource Basic',
        cost: 179,
        next_billing: '2024-02-20',
        auto_renew: false
      },
      resources: {
        cpu: 12,
        memory: 24,
        gpu: 6,
        storage: 14
      },
      last_activity: '2024-01-10T12:30:00Z',
      tasks_completed: 432,
      alerts: 3
    },
    {
      id: 'agent-013',
      name: 'Privacy Shield Elite',
      type: 'privacy_agent',
      status: 'active',
      health: 98,
      performance: 95,
      uptime: '40d 0h',
      location: 'GDPR Compliant EU',
      subscription: 'enterprise',
      billing: {
        plan: 'Privacy Enterprise',
        cost: 699,
        next_billing: '2024-02-01',
        auto_renew: true
      },
      resources: {
        cpu: 32,
        memory: 48,
        gpu: 12,
        storage: 28
      },
      last_activity: '2024-01-10T17:52:00Z',
      tasks_completed: 2341,
      alerts: 0
    },
    {
      id: 'agent-014',
      name: 'Cloud Connector Pro',
      type: 'cloud_agent',
      status: 'active',
      health: 94,
      performance: 89,
      uptime: '18d 22h',
      location: 'Multi-Cloud',
      subscription: 'premium',
      billing: {
        plan: 'Cloud Premium',
        cost: 349,
        next_billing: '2024-02-10',
        auto_renew: true
      },
      resources: {
        cpu: 55,
        memory: 67,
        gpu: 34,
        storage: 42
      },
      last_activity: '2024-01-10T17:46:00Z',
      tasks_completed: 1456,
      alerts: 1
    },
    {
      id: 'agent-015',
      name: 'Government Gateway',
      type: 'govt_agent',
      status: 'active',
      health: 96,
      performance: 91,
      uptime: '32d 12h',
      location: 'Kathmandu Govt',
      subscription: 'enterprise',
      billing: {
        plan: 'Govt Enterprise',
        cost: 899,
        next_billing: '2024-02-01',
        auto_renew: true
      },
      resources: {
        cpu: 41,
        memory: 54,
        gpu: 18,
        storage: 22
      },
      last_activity: '2024-01-10T17:49:00Z',
      tasks_completed: 1987,
      alerts: 0
    }
  ]);

  const [selectedAgent, setSelectedAgent] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('name');

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setFounderAgents(prevAgents => 
        prevAgents.map(agent => ({
          ...agent,
          health: Math.max(0, Math.min(100, agent.health + (Math.random() - 0.5) * 2)),
          performance: Math.max(0, Math.min(100, agent.performance + (Math.random() - 0.5) * 3)),
          resources: {
            cpu: Math.max(0, Math.min(100, agent.resources.cpu + (Math.random() - 0.5) * 5)),
            memory: Math.max(0, Math.min(100, agent.resources.memory + (Math.random() - 0.5) * 5)),
            gpu: Math.max(0, Math.min(100, agent.resources.gpu + (Math.random() - 0.5) * 5)),
            storage: Math.max(0, Math.min(100, agent.resources.storage + (Math.random() - 0.5) * 3))
          }
        }))
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const filteredAgents = founderAgents
    .filter(agent => filterStatus === 'all' || agent.status === filterStatus)
    .filter(agent => filterType === 'all' || agent.type === filterType)
    .sort((a, b) => {
      switch (sortBy) {
        case 'name': return a.name.localeCompare(b.name);
        case 'health': return b.health - a.health;
        case 'performance': return b.performance - a.performance;
        case 'cost': return b.billing.cost - a.billing.cost;
        default: return a.name.localeCompare(b.name);
      }
    });

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-900/20 border-green-700';
      case 'idle': return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
      case 'offline': return 'text-red-400 bg-red-900/20 border-red-700';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-700';
    }
  };

  const getHealthColor = (health) => {
    if (health >= 90) return 'text-green-400';
    if (health >= 75) return 'text-yellow-400';
    if (health >= 60) return 'text-orange-400';
    return 'text-red-400';
  };

  const getSubscriptionColor = (subscription) => {
    switch (subscription) {
      case 'enterprise': return 'text-purple-400 bg-purple-900/20 border-purple-700';
      case 'premium': return 'text-blue-400 bg-blue-900/20 border-blue-700';
      case 'standard': return 'text-gray-400 bg-gray-900/20 border-gray-700';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-700';
    }
  };

  const totalCost = founderAgents.reduce((sum, agent) => sum + agent.billing.cost, 0);
  const activeCount = founderAgents.filter(agent => agent.status === 'active').length;
  const avgHealth = Math.round(founderAgents.reduce((sum, agent) => sum + agent.health, 0) / founderAgents.length);
  const totalTasks = founderAgents.reduce((sum, agent) => sum + agent.tasks_completed, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-green-300 flex items-center gap-3">
            <Crown className="w-8 h-8" />
            Founders Portal - Agent Management
          </h2>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
            <span className="text-sm text-green-400">15 Agents Active</span>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-gray-400">Active Agents</span>
            </div>
            <div className="text-2xl font-bold text-blue-300">{activeCount}/15</div>
            <div className="text-xs text-gray-500 mt-1">System Online</div>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <Heart className="w-5 h-5 text-green-400" />
              <span className="text-sm text-gray-400">Avg Health</span>
            </div>
            <div className="text-2xl font-bold text-green-300">{avgHealth}%</div>
            <div className="text-xs text-gray-500 mt-1">System Status</div>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="w-5 h-5 text-yellow-400" />
              <span className="text-sm text-gray-400">Monthly Cost</span>
            </div>
            <div className="text-2xl font-bold text-yellow-300">${totalCost}</div>
            <div className="text-xs text-gray-500 mt-1">Total Billing</div>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-5 h-5 text-purple-400" />
              <span className="text-sm text-gray-400">Tasks Completed</span>
            </div>
            <div className="text-2xl font-bold text-purple-300">{totalTasks.toLocaleString()}</div>
            <div className="text-xs text-gray-500 mt-1">All Time</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Status:</span>
            <select 
              value={filterStatus} 
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm text-gray-300"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="idle">Idle</option>
              <option value="offline">Offline</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Type:</span>
            <select 
              value={filterType} 
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm text-gray-300"
            >
              <option value="all">All Types</option>
              <option value="founder_clone">Founder Clones</option>
              <option value="system_agent">System Agents</option>
              <option value="vision_agent">Vision Agents</option>
              <option value="security_agent">Security Agents</option>
              <option value="core_agent">Core Agents</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Sort:</span>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm text-gray-300"
            >
              <option value="name">Name</option>
              <option value="health">Health</option>
              <option value="performance">Performance</option>
              <option value="cost">Cost</option>
            </select>
          </div>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map((agent) => (
          <motion.div
            key={agent.id}
            whileHover={{ scale: 1.02 }}
            onClick={() => setSelectedAgent(agent)}
            className="bg-gray-900/50 rounded-xl p-4 border border-gray-700 cursor-pointer hover:border-green-600 transition-all duration-300"
          >
            {/* Agent Header */}
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-bold text-gray-200">{agent.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-1 rounded ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${getSubscriptionColor(agent.subscription)}`}>
                    {agent.subscription}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${getHealthColor(agent.health)}`}>
                  {agent.health}%
                </div>
                <div className="text-xs text-gray-500">Health</div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div>
                <div className="text-xs text-gray-400">Performance</div>
                <div className="flex items-center gap-1">
                  <div className="flex-1 bg-gray-700 rounded-full h-1">
                    <div 
                      className="h-1 rounded-full bg-blue-500"
                      style={{ width: `${agent.performance}%` }}
                    />
                  </div>
                  <span className="text-xs text-blue-300">{agent.performance}%</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Uptime</div>
                <div className="text-xs text-gray-300">{agent.uptime}</div>
              </div>
            </div>

            {/* Resource Usage */}
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-1">Resources</div>
              <div className="grid grid-cols-4 gap-1 text-xs">
                <div className="text-center">
                  <div className="text-blue-300">{agent.resources.cpu}%</div>
                  <div className="text-gray-500">CPU</div>
                </div>
                <div className="text-center">
                  <div className="text-green-300">{agent.resources.memory}%</div>
                  <div className="text-gray-500">MEM</div>
                </div>
                <div className="text-center">
                  <div className="text-purple-300">{agent.resources.gpu}%</div>
                  <div className="text-gray-500">GPU</div>
                </div>
                <div className="text-center">
                  <div className="text-yellow-300">{agent.resources.storage}%</div>
                  <div className="text-gray-500">STO</div>
                </div>
              </div>
            </div>

            {/* Location & Billing */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1 text-gray-400">
                <Globe className="w-3 h-3" />
                <span>{agent.location}</span>
              </div>
              <div className="flex items-center gap-1 text-yellow-400">
                <DollarSign className="w-3 h-3" />
                <span>${agent.billing.cost}/mo</span>
              </div>
            </div>

            {/* Alerts */}
            {agent.alerts > 0 && (
              <div className="mt-2 flex items-center gap-1 text-xs text-red-400">
                <AlertTriangle className="w-3 h-3" />
                <span>{agent.alerts} alert{agent.alerts > 1 ? 's' : ''}</span>
              </div>
            )}
          </motion.div>
        ))}
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
                {selectedAgent.name} - Detailed View
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
                  <h4 className="text-lg font-semibold text-gray-200 mb-3">Agent Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Type:</span>
                      <span className="text-gray-200 capitalize">{selectedAgent.type.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Status:</span>
                      <span className={`capitalize ${getStatusColor(selectedAgent.status)}`}>
                        {selectedAgent.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Location:</span>
                      <span className="text-gray-200">{selectedAgent.location}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Uptime:</span>
                      <span className="text-gray-200">{selectedAgent.uptime}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Last Activity:</span>
                      <span className="text-gray-200">
                        {new Date(selectedAgent.last_activity).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <h4 className="text-lg font-semibold text-gray-200 mb-3">Performance Metrics</h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-400">Health</span>
                        <span className={`font-bold ${getHealthColor(selectedAgent.health)}`}>
                          {selectedAgent.health}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            selectedAgent.health >= 90 ? 'bg-green-500' :
                            selectedAgent.health >= 75 ? 'bg-yellow-500' :
                            selectedAgent.health >= 60 ? 'bg-orange-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${selectedAgent.health}%` }}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-400">Performance</span>
                        <span className="text-blue-300 font-bold">{selectedAgent.performance}%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div 
                          className="h-2 rounded-full bg-blue-500"
                          style={{ width: `${selectedAgent.performance}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Billing & Resources */}
              <div>
                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 mb-4">
                  <h4 className="text-lg font-semibold text-gray-200 mb-3">Billing Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Plan:</span>
                      <span className="text-gray-200">{selectedAgent.billing.plan}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Monthly Cost:</span>
                      <span className="text-yellow-300 font-bold">${selectedAgent.billing.cost}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Next Billing:</span>
                      <span className="text-gray-200">{selectedAgent.billing.next_billing}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Auto Renew:</span>
                      <span className={selectedAgent.billing.auto_renew ? 'text-green-300' : 'text-red-300'}>
                        {selectedAgent.billing.auto_renew ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <h4 className="text-lg font-semibold text-gray-200 mb-3">Resource Usage</h4>
                  <div className="space-y-3">
                    {Object.entries(selectedAgent.resources).map(([resource, value]) => (
                      <div key={resource}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-400 capitalize">{resource}</span>
                          <span className="text-gray-200 font-bold">{value}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              resource === 'cpu' ? 'bg-blue-500' :
                              resource === 'memory' ? 'bg-green-500' :
                              resource === 'gpu' ? 'bg-purple-500' :
                              'bg-yellow-500'
                            }`}
                            style={{ width: `${value}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex flex-wrap gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium"
              >
                <Power className="w-4 h-4 inline mr-1" />
                {selectedAgent.status === 'active' ? 'Stop Agent' : 'Start Agent'}
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
              >
                <Settings className="w-4 h-4 inline mr-1" />
                Configure
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium"
              >
                <Activity className="w-4 h-4 inline mr-1" />
                View Logs
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg text-sm font-medium"
              >
                <DollarSign className="w-4 h-4 inline mr-1" />
                Upgrade Plan
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
