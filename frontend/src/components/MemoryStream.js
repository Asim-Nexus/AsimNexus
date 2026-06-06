/**
 * ASIMNEXUS Memory Stream Component
 * ===================================
 * Real-time vector memory visualization
 */

import React, { useState, useEffect } from 'react';
import { Database, Clock, Tag, Brain } from 'lucide-react';

const MemoryStream = ({ memories }) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredMemories = memories.filter(memory => {
    const matchesFilter = filter === 'all' || memory.type === filter;
    const matchesSearch = searchTerm === '' || 
      memory.content.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getMemoryTypeIcon = (type) => {
    switch (type) {
      case 'neural':
        return <Brain className="w-3 h-3 text-blue-400" />;
      case 'system':
        return <Database className="w-3 h-3 text-green-400" />;
      case 'user':
        return <Tag className="w-3 h-3 text-purple-400" />;
      default:
        return <Database className="w-3 h-3 text-gray-400" />;
    }
  };

  const getMemoryTypeColor = (type) => {
    switch (type) {
      case 'neural':
        return 'border-blue-800 bg-blue-950';
      case 'system':
        return 'border-green-800 bg-green-950';
      case 'user':
        return 'border-purple-800 bg-purple-950';
      default:
        return 'border-gray-800 bg-gray-950';
    }
  };

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Database className="w-6 h-6 mr-2 text-purple-400" />
          <h2 className="text-xl font-bold text-white">Memory Stream</h2>
        </div>
        <div className="text-sm text-slate-400">
          {memories.length} memories
        </div>
      </div>

      {/* Filter Controls */}
      <div className="flex items-center space-x-4 mb-4">
        <div className="flex items-center space-x-2">
          <label className="text-sm text-slate-300">Type:</label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white"
          >
            <option value="all">All</option>
            <option value="neural">Neural</option>
            <option value="system">System</option>
            <option value="user">User</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2 flex-1">
          <label className="text-sm text-slate-300">Search:</label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search memories..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white"
          />
        </div>
      </div>

      {/* Memory Items */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredMemories.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            {memories.length === 0 ? 'No memories yet...' : 'No memories match filters'}
          </div>
        ) : (
          filteredMemories.map((memory, index) => (
            <div
              key={memory.id || index}
              className={`border rounded-lg p-3 transition-all hover:shadow-md ${
                getMemoryTypeColor(memory.type)
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getMemoryTypeIcon(memory.type)}
                  <span className="text-xs font-semibold text-slate-300">
                    {memory.type?.toUpperCase() || 'UNKNOWN'}
                  </span>
                </div>
                <div className="flex items-center text-xs text-slate-500">
                  <Clock className="w-3 h-3 mr-1" />
                  {formatTimestamp(memory.timestamp)}
                </div>
              </div>
              
              <div className="text-sm text-slate-200 mb-2">
                {memory.content}
              </div>
              
              {memory.metadata && (
                <div className="text-xs text-slate-500">
                  {Object.keys(memory.metadata).length > 0 && (
                    <div>
                      <span className="font-semibold">Metadata:</span>
                      <div className="mt-1 space-y-1">
                        {Object.entries(memory.metadata).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span>{key}:</span>
                            <span className="text-slate-400">
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Memory Statistics */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-900 rounded p-2">
            <div className="text-slate-400 mb-1">Total Memories</div>
            <div className="text-lg font-bold text-white">{memories.length}</div>
          </div>
          <div className="bg-slate-900 rounded p-2">
            <div className="text-slate-400 mb-1">Neural Memories</div>
            <div className="text-lg font-bold text-blue-400">
              {memories.filter(m => m.type === 'neural').length}
            </div>
          </div>
          <div className="bg-slate-900 rounded p-2">
            <div className="text-slate-400 mb-1">System Memories</div>
            <div className="text-lg font-bold text-green-400">
              {memories.filter(m => m.type === 'system').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemoryStream;
