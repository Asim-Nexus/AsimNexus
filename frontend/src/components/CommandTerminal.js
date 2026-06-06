/**
 * ASIMNEXUS Command Terminal Component
 * =====================================
 * Real-time command interface with WebSocket integration
 */

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Send, Play, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const CommandTerminal = ({ wsConnection }) => {
  const [command, setCommand] = useState('');
  const [commandHistory, setCommandHistory] = useState([]);
  const [output, setOutput] = useState([
    { type: 'system', message: 'ASIMNEXUS Command Terminal Ready', timestamp: new Date() },
    { type: 'system', message: 'Type "help" for available commands', timestamp: new Date() }
  ]);
  const [isExecuting, setIsExecuting] = useState(false);
  const terminalRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const availableCommands = [
    { cmd: 'help', description: 'Show available commands' },
    { cmd: 'status', description: 'Get system status' },
    { cmd: 'memory list', description: 'List recent memories' },
    { cmd: 'safety check', description: 'Run safety system check' },
    { cmd: 'neural scan', description: 'Scan neural network' },
    { cmd: 'hardware test', description: 'Run hardware diagnostics' },
    { cmd: 'identity verify', description: 'Verify CEO identity' },
    { cmd: 'cloud deploy', description: 'Deploy to cloud' },
    { cmd: 'govt request', description: 'Make government API request' },
    { cmd: 'clear', description: 'Clear terminal' }
  ];

  const executeCommand = async (cmd) => {
    if (!cmd.trim()) return;
    
    setIsExecuting(true);
    
    // Add command to history
    setCommandHistory(prev => [...prev, cmd]);
    
    // Add command to output
    const commandOutput = {
      type: 'command',
      message: `$ ${cmd}`,
      timestamp: new Date()
    };
    setOutput(prev => [...prev, commandOutput]);

    try {
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        // Send command via WebSocket
        wsConnection.send(JSON.stringify({
          type: 'command',
          command: cmd,
          timestamp: new Date().toISOString()
        }));
      } else {
        // Fallback to HTTP API
        const response = await fetch('http://localhost:8000/api/command/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: cmd, parameters: {} })
        });
        
        const result = await response.json();
        
        const responseOutput = {
          type: result.success ? 'success' : 'error',
          message: result.message || result.error || 'Command processed',
          timestamp: new Date(),
          details: result
        };
        setOutput(prev => [...prev, responseOutput]);
      }
    } catch (error) {
      const errorOutput = {
        type: 'error',
        message: `Command failed: ${error.message}`,
        timestamp: new Date()
      };
      setOutput(prev => [...prev, errorOutput]);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    executeCommand(command);
    setCommand('');
  };

  const clearTerminal = () => {
    setOutput([
      { type: 'system', message: 'Terminal cleared', timestamp: new Date() }
    ]);
  };

  const getOutputIcon = (type) => {
    switch (type) {
      case 'command':
        return <Terminal className="w-3 h-3 text-blue-400" />;
      case 'success':
        return <CheckCircle className="w-3 h-3 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-3 h-3 text-red-400" />;
      case 'system':
        return <Clock className="w-3 h-3 text-yellow-400" />;
      default:
        return <Terminal className="w-3 h-3 text-gray-400" />;
    }
  };

  const getOutputColor = (type) => {
    switch (type) {
      case 'command':
        return 'text-blue-300';
      case 'success':
        return 'text-green-300';
      case 'error':
        return 'text-red-300';
      case 'system':
        return 'text-yellow-300';
      default:
        return 'text-gray-300';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        setCommand(commandHistory[commandHistory.length - 1]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (commandHistory.length > 1) {
        setCommand(commandHistory[commandHistory.length - 2]);
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      // Auto-complete logic here
      const matches = availableCommands.filter(cmd => 
        cmd.cmd.startsWith(command.toLowerCase())
      );
      if (matches.length === 1) {
        setCommand(matches[0].cmd);
      }
    }
  };

  // Handle WebSocket messages
  useEffect(() => {
    if (!wsConnection) return;

    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'command_result') {
        const responseOutput = {
          type: data.success ? 'success' : 'error',
          message: data.message || data.error || 'Command processed',
          timestamp: new Date(),
          details: data
        };
        setOutput(prev => [...prev, responseOutput]);
      }
    };

    wsConnection.addEventListener('message', handleMessage);

    return () => {
      wsConnection.removeEventListener('message', handleMessage);
    };
  }, [wsConnection]);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Terminal className="w-6 h-6 mr-2 text-green-400" />
          <h2 className="text-xl font-bold text-white">Command Terminal</h2>
        </div>
        <button
          onClick={clearTerminal}
          className="px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-300 transition-colors"
        >
          Clear
        </button>
      </div>

      {/* Terminal Output */}
      <div 
        ref={terminalRef}
        className="bg-black rounded p-3 h-64 overflow-y-auto mb-4 font-mono text-sm"
      >
        {output.map((line, index) => (
          <div key={index} className="mb-2 flex items-start">
            <div className="mr-2 text-slate-500 flex-shrink-0">
              {getOutputIcon(line.type)}
            </div>
            <div className="flex-1">
              <span className={`text-xs text-slate-400 mr-2`}>
                {line.timestamp.toLocaleTimeString()}
              </span>
              <span className={getOutputColor(line.type)}>
                {line.message}
              </span>
              {line.details && (
                <div className="mt-1 text-xs text-slate-500">
                  {JSON.stringify(line.details, null, 2)}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isExecuting && (
          <div className="flex items-center text-yellow-300">
            <div className="mr-2">⚡</div>
            <span>Executing command...</span>
          </div>
        )}
      </div>

      {/* Command Input */}
      <form onSubmit={handleSubmit} className="flex items-center space-x-2">
        <div className="flex-1 flex items-center bg-slate-900 rounded border border-slate-700">
          <span className="text-green-400 px-2 py-1">$</span>
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter ASIMNEXUS command..."
            className="flex-1 bg-transparent text-white px-2 py-1 focus:outline-none"
            disabled={isExecuting}
            autoComplete="off"
          />
        </div>
        <button
          type="submit"
          disabled={isExecuting || !command.trim()}
          className="px-4 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-white flex items-center transition-colors"
        >
          {isExecuting ? (
            <div className="animate-spin w-4 h-4 mr-1">⚡</div>
          ) : (
            <Send className="w-4 h-4 mr-1" />
          )}
          Execute
        </button>
      </form>

      {/* Quick Commands */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="text-sm font-semibold text-slate-300 mb-2">Quick Commands:</div>
        <div className="grid grid-cols-2 gap-2">
          {availableCommands.slice(0, 6).map((cmd) => (
            <button
              key={cmd.cmd}
              onClick={() => setCommand(cmd.cmd)}
              className="text-left px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-300 transition-colors"
            >
              {cmd.cmd}
            </button>
          ))}
        </div>
      </div>

      {/* Command Help */}
      {command === 'help' && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="text-sm font-semibold text-slate-300 mb-2">Available Commands:</div>
          <div className="space-y-1">
            {availableCommands.map((cmd) => (
              <div key={cmd.cmd} className="text-xs text-slate-400">
                <span className="text-blue-400 font-mono">{cmd.cmd}</span>
                <span className="ml-2">- {cmd.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CommandTerminal;
