/**
 * ASIMNEXUS Memory Dashboard
 * =========================
 * Visualize Redis and PostgreSQL memory systems
 * 
 * Features:
 * - Real-time memory statistics
 * - Database health monitoring
 * - Conversation management
 * - API key management
 * - System metrics
 */

import React, { useState, useEffect } from 'react';
import {
  Database,
  Zap,
  Server,
  Activity,
  HardDrive,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Key,
  Users,
  MessageSquare,
  BarChart3,
  Cpu,
  AlertCircle,
  Terminal,
  ChevronRight,
  ChevronDown,
  Shield,
  Lock
} from 'lucide-react';
import { memoryAPI, databaseAPI, systemOperationsAPI } from '../../api/asimnexus';

export default function MemoryDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [memoryStats, setMemoryStats] = useState(null);
  const [dbHealth, setDbHealth] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Load all data
  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadMemoryStats(),
        loadDbHealth(),
        loadConversations(),
        loadApiKeys(),
        loadSystemInfo()
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load memory stats
  const loadMemoryStats = async () => {
    try {
      const response = await memoryAPI.getStats();
      if (response.data?.success) {
        setMemoryStats(response.data.stats);
      }
    } catch (error) {
      console.error('Failed to load memory stats:', error);
    }
  };

  // Load database health
  const loadDbHealth = async () => {
    try {
      const response = await databaseAPI.health();
      setDbHealth(response.data);
    } catch (error) {
      console.error('Failed to load DB health:', error);
      setDbHealth({ status: 'unhealthy', error: error.message });
    }
  };

  // Load conversations
  const loadConversations = async () => {
    try {
      const response = await databaseAPI.getUserConversations(1, 20);
      if (response.data?.success) {
        setConversations(response.data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  // Load API keys
  const loadApiKeys = async () => {
    try {
      const response = await databaseAPI.getApiKeys(1);
      if (response.data?.success) {
        setApiKeys(response.data.keys || []);
      }
    } catch (error) {
      console.error('Failed to load API keys:', error);
    }
  };

  // Load system info
  const loadSystemInfo = async () => {
    try {
      const response = await systemOperationsAPI.getSystemInfo();
      setSystemInfo(response.data);
    } catch (error) {
      console.error('Failed to load system info:', error);
    }
  };

  // Load conversation messages
  const loadConversationMessages = async (convId) => {
    try {
      const response = await databaseAPI.getMessages(convId, 50);
      if (response.data?.success) {
        setConversationMessages(response.data.messages || []);
        setSelectedConversation(convId);
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  // Delete conversation
  const deleteConversation = async (convId) => {
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
      // Note: Add delete endpoint to API
      // await databaseAPI.deleteConversation(convId);
      loadConversations();
      if (selectedConversation === convId) {
        setSelectedConversation(null);
        setConversationMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  // Clear Redis cache
  const clearRedisCache = async () => {
    try {
      // This would need a specific endpoint
      alert('Redis cache cleared (simulated)');
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  // Auto-refresh
  useEffect(() => {
    loadData();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadMemoryStats();
      loadDbHealth();
    }, 30000);
    
    setRefreshInterval(interval);
    
    return () => clearInterval(interval);
  }, []);

  // Format bytes to human readable
  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString();
  };

  // Status badge component
  const StatusBadge = ({ status, text }) => {
    const colors = {
      healthy: 'bg-green-500/20 text-green-400 border-green-500/30',
      unhealthy: 'bg-red-500/20 text-red-400 border-red-500/30',
      running: 'bg-green-500/20 text-green-400 border-green-500/30',
      stopped: 'bg-red-500/20 text-red-400 border-red-500/30',
      warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-sm border ${colors[status] || colors.warning}`}>
        {text || status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-400" />
              ASIMNEXUS Memory Dashboard
            </h1>
            <p className="text-gray-400 mt-2">
              Monitor Redis cache, PostgreSQL database, and system metrics
            </p>
          </div>
          
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-500 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-700">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'memory', label: 'Redis Memory', icon: Zap },
          { id: 'database', label: 'Database', icon: Database },
          { id: 'conversations', label: 'Conversations', icon: MessageSquare },
          { id: 'apikeys', label: 'API Keys', icon: Key },
          { id: 'system', label: 'System', icon: Server }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Redis Status */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-gray-400">
                <Zap className="w-5 h-5" />
                <span>Redis Memory</span>
              </div>
              <StatusBadge status={memoryStats ? 'healthy' : 'unhealthy'} text={memoryStats ? 'Running' : 'Stopped'} />
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {memoryStats ? formatBytes(memoryStats.used_memory_mb * 1024 * 1024) : '-'}
              </div>
              <div className="text-sm text-gray-500">
                {memoryStats?.total_keys || 0} keys stored
              </div>
              <div className="text-sm text-gray-500">
                {memoryStats?.connected_clients || 0} connected clients
              </div>
            </div>
          </div>

          {/* PostgreSQL Status */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-gray-400">
                <Database className="w-5 h-5" />
                <span>PostgreSQL</span>
              </div>
              <StatusBadge status={dbHealth?.status === 'healthy' ? 'healthy' : 'unhealthy'} />
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {dbHealth?.total_users !== undefined ? dbHealth.total_users : '-'}
              </div>
              <div className="text-sm text-gray-500">
                Total users in database
              </div>
              <div className="text-sm text-gray-500">
                Connection: {dbHealth?.connection || 'unknown'}
              </div>
            </div>
          </div>

          {/* Conversations */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-gray-400">
                <MessageSquare className="w-5 h-5" />
                <span>Conversations</span>
              </div>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                {conversations.length}
              </span>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{conversations.length}</div>
              <div className="text-sm text-gray-500">
                Total conversations stored
              </div>
              <div className="text-sm text-gray-500">
                Persistent in PostgreSQL
              </div>
            </div>
          </div>

          {/* API Keys */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-gray-400">
                <Key className="w-5 h-5" />
                <span>API Keys</span>
              </div>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
                {apiKeys.length}
              </span>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{apiKeys.length}</div>
              <div className="text-sm text-gray-500">
                Encrypted API keys stored
              </div>
              <div className="text-sm text-gray-500 flex items-center gap-1">
                <Lock className="w-3 h-3" />
                Fernet encryption
              </div>
            </div>
          </div>

          {/* Memory Architecture */}
          <div className="col-span-full bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Memory Architecture
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-700/50 p-4 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-400 mb-2">
                  <Zap className="w-4 h-4" />
                  <span className="font-semibold">Short-term (Redis)</span>
                </div>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• Active conversations</li>
                  <li>• Message cache</li>
                  <li>• User sessions</li>
                  <li>• &lt;1ms access time</li>
                  <li>• Auto-expiration (30min)</li>
                </ul>
              </div>
              
              <div className="bg-gray-700/50 p-4 rounded-lg">
                <div className="flex items-center gap-2 text-blue-400 mb-2">
                  <Database className="w-4 h-4" />
                  <span className="font-semibold">Long-term (PostgreSQL)</span>
                </div>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• Conversation history</li>
                  <li>• User profiles</li>
                  <li>• API keys (encrypted)</li>
                  <li>• Action logs</li>
                  <li>• Persistent storage</li>
                </ul>
              </div>
              
              <div className="bg-gray-700/50 p-4 rounded-lg">
                <div className="flex items-center gap-2 text-green-400 mb-2">
                  <Shield className="w-4 h-4" />
                  <span className="font-semibold">Security</span>
                </div>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• Fernet encryption</li>
                  <li>• Rate limiting</li>
                  <li>• Session management</li>
                  <li>• Access control</li>
                  <li>• Audit logging</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Redis Memory Tab */}
      {activeTab === 'memory' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="text-gray-400 mb-2">Memory Usage</div>
              <div className="text-3xl font-bold">{memoryStats ? formatBytes(memoryStats.used_memory_mb * 1024 * 1024) : '-'}</div>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="text-gray-400 mb-2">Total Keys</div>
              <div className="text-3xl font-bold">{memoryStats?.total_keys || 0}</div>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="text-gray-400 mb-2">Uptime</div>
              <div className="text-3xl font-bold">
                {memoryStats?.uptime_seconds 
                  ? `${Math.floor(memoryStats.uptime_seconds / 3600)}h ${Math.floor((memoryStats.uptime_seconds % 3600) / 60)}m`
                  : '-'
                }
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Cache Management</h3>
              <button
                onClick={clearRedisCache}
                className="flex items-center gap-2 px-4 py-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Clear Cache
              </button>
            </div>
            <p className="text-gray-400 text-sm">
              Clearing the cache will force all context to be reloaded from PostgreSQL.
              This is useful for debugging but will temporarily slow down responses.
            </p>
          </div>
        </div>
      )}

      {/* Database Tab */}
      {activeTab === 'database' && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">Database Health</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-gray-400 mb-2">Status</div>
                <StatusBadge status={dbHealth?.status === 'healthy' ? 'healthy' : 'unhealthy'} />
              </div>
              <div>
                <div className="text-gray-400 mb-2">Connection</div>
                <div className="text-lg">{dbHealth?.connection || 'Unknown'}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-2">Total Users</div>
                <div className="text-2xl font-bold">{dbHealth?.total_users !== undefined ? dbHealth.total_users : '-'}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-2">Last Error</div>
                <div className="text-red-400">{dbHealth?.error || 'None'}</div>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">Database Schema</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b border-gray-700">
                    <th className="pb-3">Table</th>
                    <th className="pb-3">Purpose</th>
                    <th className="pb-3">Rows</th>
                  </tr>
                </thead>
                <tbody className="text-gray-400">
                  <tr className="border-b border-gray-800">
                    <td className="py-3 font-mono">users</td>
                    <td>User accounts and preferences</td>
                    <td>{dbHealth?.total_users || '-'}</td>
                  </tr>
                  <tr className="border-b border-gray-800">
                    <td className="py-3 font-mono">conversations</td>
                    <td>Chat conversations</td>
                    <td>{conversations.length}</td>
                  </tr>
                  <tr className="border-b border-gray-800">
                    <td className="py-3 font-mono">messages</td>
                    <td>Individual messages</td>
                    <td>-</td>
                  </tr>
                  <tr className="border-b border-gray-800">
                    <td className="py-3 font-mono">api_keys</td>
                    <td>Encrypted API keys</td>
                    <td>{apiKeys.length}</td>
                  </tr>
                  <tr className="border-b border-gray-800">
                    <td className="py-3 font-mono">actions</td>
                    <td>Action execution logs</td>
                    <td>-</td>
                  </tr>
                  <tr>
                    <td className="py-3 font-mono">system_events</td>
                    <td>System event logs</td>
                    <td>-</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Conversations Tab */}
      {activeTab === 'conversations' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversation List */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Conversations</h3>
              <span className="text-sm text-gray-400">{conversations.length} total</span>
            </div>
            
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => loadConversationMessages(conv.id)}
                  className={`p-4 rounded-lg cursor-pointer transition-colors ${
                    selectedConversation === conv.id
                      ? 'bg-blue-600'
                      : 'bg-gray-700/50 hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{conv.title}</div>
                      <div className="text-sm text-gray-400 flex items-center gap-2 mt-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(conv.updated_at)}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="p-1 hover:bg-red-600/20 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
              
              {conversations.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  No conversations found
                </div>
              )}
            </div>
          </div>

          {/* Conversation Detail */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">
              {selectedConversation ? 'Messages' : 'Select a conversation'}
            </h3>
            
            {selectedConversation ? (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {conversationMessages.map((msg, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-600/20 border-l-4 border-blue-500'
                        : msg.role === 'action'
                        ? 'bg-green-600/20 border-l-4 border-green-500'
                        : 'bg-gray-700/50'
                    }`}
                  >
                    <div className="text-xs text-gray-400 mb-1 uppercase">{msg.role}</div>
                    <div className="text-sm">{msg.content}</div>
                    <div className="text-xs text-gray-500 mt-2">
                      {formatTime(msg.created_at)}
                    </div>
                  </div>
                ))}
                
                {conversationMessages.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    No messages in this conversation
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                Click on a conversation to view messages
              </div>
            )}
          </div>
        </div>
      )}

      {/* API Keys Tab */}
      {activeTab === 'apikeys' && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Encrypted API Keys
            </h3>
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
              {apiKeys.length} keys stored
            </span>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-700">
                  <th className="pb-3">Provider</th>
                  <th className="pb-3">Key ID</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3">Usage Count</th>
                  <th className="pb-3">Last Used</th>
                </tr>
              </thead>
              <tbody className="text-gray-400">
                {apiKeys.map((key, index) => (
                  <tr key={index} className="border-b border-gray-800">
                    <td className="py-3">
                      <span className="px-2 py-1 bg-gray-700 rounded text-xs">
                        {key.provider}
                      </span>
                    </td>
                    <td className="py-3 font-mono text-xs">
                      {key.id}****
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        key.is_active
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {key.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3">{key.usage_count || 0}</td>
                    <td className="py-3">{formatTime(key.last_used)}</td>
                  </tr>
                ))}
                
                {apiKeys.length === 0 && (
                  <tr>
                    <td colSpan="5" className="py-8 text-center">
                      No API keys stored
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="mt-4 p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5" />
              <div className="text-sm text-yellow-200">
                <p className="font-semibold mb-1">Security Notice</p>
                <p>All API keys are encrypted using Fernet encryption before storage. 
                Keys are only decrypted when needed for API calls.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-4">
                <Cpu className="w-5 h-5" />
                <span>CPU</span>
              </div>
              <div className="text-3xl font-bold">
                {systemInfo?.cpu?.usage_percent?.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {systemInfo?.cpu?.count} cores
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-4">
                <HardDrive className="w-5 h-5" />
                <span>Memory</span>
              </div>
              <div className="text-3xl font-bold">
                {systemInfo?.memory?.percent}%
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {systemInfo?.memory?.used_gb?.toFixed(1)} / {systemInfo?.memory?.total_gb?.toFixed(1)} GB
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-4">
                <Terminal className="w-5 h-5" />
                <span>Platform</span>
              </div>
              <div className="text-lg font-semibold">
                {systemInfo?.platform}
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {systemInfo?.uptime}
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">Disk Usage</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {systemInfo?.disks?.map((disk, index) => (
                <div key={index} className="bg-gray-700/50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{disk.device}</span>
                    <span className="text-sm text-gray-400">{disk.mountpoint}</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2 mb-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(disk.used_gb / disk.total_gb) * 100}%` }}
                    />
                  </div>
                  <div className="text-sm text-gray-400">
                    {disk.used_gb.toFixed(1)} / {disk.total_gb.toFixed(1)} GB used
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
