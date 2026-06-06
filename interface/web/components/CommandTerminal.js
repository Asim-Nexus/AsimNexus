import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Send, Cpu, Zap, Shield, Activity } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';

export default function CommandTerminal() {
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState([
    {
      id: 1,
      type: 'system',
      command: 'system.status',
      output: '🧠 ASIMNEXUS Neural Core Status: ONLINE\n📊 CPU: 45% | GPU: 62% | Memory: 68%\n🔥 Temperature: 58°C | Performance: BALANCED',
      timestamp: '2024-01-10T17:30:00Z'
    },
    {
      id: 2,
      type: 'agent',
      command: 'agent.list',
      output: '🤖 Active Agents (8/8):\n• SystemOptimizer - Cleaning temp files (75%)\n• ScreenAnalyst - OCR processing (45%)\n• SandboxExecutor - Monitoring (0%)\n• RTXStressAdaptor - GPU monitoring (100%)\n• Orchestrator - Coordinating (100%)\n• MCPConnector - API sync (60%)\n• GovernanceLayer - Policy enforcement (100%)\n• FinanceEngine - Budget monitoring (85%)',
      timestamp: '2024-01-10T17:28:00Z'
    },
    {
      id: 3,
      type: 'windows',
      command: 'dir C:\\Users',
      output: ' Volume in drive C is Windows\n Volume Serial Number is XXXX-XXXX\n\n Directory of C:\\Users\n\n2024-01-10  17:25    <DIR>          Administrator\n2024-01-10  16:45    <DIR>          Default\n2024-01-10  15:30    <DIR>          Public\n               0 File(s)              0 bytes\n               3 Dir(s)  45,678,912,000 bytes free',
      timestamp: '2024-01-10T17:25:00Z'
    }
  ]);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const terminalRef = useRef(null);
  const inputRef = useRef(null);

  const commands = [
    'system.status',
    'system.optimize',
    'system.restart',
    'agent.list',
    'agent.start <name>',
    'agent.stop <name>',
    'agent.logs <name>',
    'neural.pulse',
    'neural.frequency <ghz>',
    'gpu.status',
    'gpu.mode <performance|balanced|powersave>',
    'dharma.status',
    'dharma.policy <list|enable|disable>',
    'sandbox.execute <file>',
    'sandbox.status',
    'ocr.capture',
    'ocr.analyze <file>',
    'help',
    'clear'
  ];

  useEffect(() => {
    // Auto-scroll to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [history]);

  useEffect(() => {
    // Filter suggestions based on current command
    if (command.length > 0) {
      const filtered = commands.filter(cmd => 
        cmd.toLowerCase().startsWith(command.toLowerCase())
      );
      setSuggestions(filtered);
      setSelectedSuggestion(0);
    } else {
      setSuggestions([]);
    }
  }, [command]);

  const executeCommand = async (cmd) => {
    if (!cmd.trim()) return;

    setIsProcessing(true);
    
    // Add command to history
    const newEntry = {
      id: Date.now(),
      type: 'user',
      command: cmd,
      output: '',
      timestamp: new Date().toISOString()
    };

    setHistory(prev => [...prev, newEntry]);

    // Simulate command execution
    setTimeout(() => {
      const output = processCommand(cmd);
      
      setHistory(prev => prev.map(entry => 
        entry.id === newEntry.id 
          ? { ...entry, output, type: 'system' }
          : entry
      ));
      
      setIsProcessing(false);
      setCommand('');
      setSuggestions([]);
    }, 1000 + Math.random() * 1000);
  };

  const processCommand = (cmd) => {
    const parts = cmd.trim().split(' ');
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    switch (command) {
      case 'system.status':
        return `🧠 ASIMNEXUS Neural Core Status: ${Math.random() > 0.3 ? 'ONLINE' : 'OPTIMIZING'}
📊 CPU: ${Math.round(40 + Math.random() * 30)}% | GPU: ${Math.round(50 + Math.random() * 30)}% | Memory: ${Math.round(60 + Math.random() * 20)}%
🔥 Temperature: ${Math.round(55 + Math.random() * 15)}°C | Performance: ${['BALANCED', 'PERFORMANCE', 'POWERSAVE'][Math.floor(Math.random() * 3)]}
⏰ Uptime: ${Math.floor(Math.random() * 24)}h ${Math.floor(Math.random() * 60)}m`;

      case 'agent.list':
        const agentCount = 8;
        const activeCount = Math.floor(5 + Math.random() * 3);
        return `🤖 Active Agents (${activeCount}/${agentCount}):\n${generateAgentList()}`;

      case 'neural.pulse':
        return `📈 Neural Pulse Data:\nFrequency: ${(1.8 + Math.random() * 0.6).toFixed(2)} GHz\nAmplitude: ${Math.round(20 + Math.random() * 30)}%\nStability: ${Math.round(85 + Math.random() * 10)}%\nPhase: ${['ALPHA', 'BETA', 'GAMMA', 'DELTA'][Math.floor(Math.random() * 4)]}`;

      case 'gpu.status':
        return `🎮 RTX 2060 Status:\nTemperature: ${Math.round(55 + Math.random() * 15)}°C\nUtilization: ${Math.round(50 + Math.random() * 30)}%\nMemory: ${Math.round(2 + Math.random() * 4)}GB / 6GB\nFan Speed: ${Math.round(40 + Math.random() * 40)}%\nPower Mode: ${['PERFORMANCE', 'BALANCED', 'POWERSAVE'][Math.floor(Math.random() * 3)]}`;

      case 'dharma.status':
        return `🛡️ Dharma-Chakra Status:\nSystem Integrity: ${Math.round(95 + Math.random() * 4)}%\nActive Policies: ${Math.floor(3 + Math.random() * 2)}\nViolations (24h): ${Math.floor(Math.random() * 3)}\nResponse Time: ${Math.round(10 + Math.random() * 20)}ms`;

      case 'ocr.capture':
        return `📸 Screen Capture Initiated:\nResolution: ${Math.floor(1920)}x${Math.floor(1080)}\nFormat: PNG\nText Regions Found: ${Math.floor(2 + Math.random() * 5)}\nProcessing Time: ${Math.round(100 + Math.random() * 500)}ms`;

      case 'help':
        return `📚 ASIMNEXUS Command Reference:\n\n${commands.map(cmd => `  ${cmd}`).join('\n')}\n\n💡 Use Tab for autocomplete, ↑↓ for history`;

      case 'clear':
        setHistory([]);
        return 'Terminal cleared.';

      default:
        if (cmd.startsWith('dir ') || cmd.startsWith('ls ')) {
          return `📁 Directory listing for ${cmd.substring(4) || 'current directory'}:\n\n${generateDirectoryListing()}`;
        }
        return `❌ Unknown command: ${cmd}\n💡 Type 'help' for available commands`;
    }
  };

  const generateAgentList = () => {
    const agents = [
      'SystemOptimizer - System maintenance',
      'ScreenAnalyst - Vision processing',
      'SandboxExecutor - Security isolation',
      'RTXStressAdaptor - GPU management',
      'Orchestrator - Task coordination',
      'MCPConnector - API integration',
      'GovernanceLayer - Policy enforcement',
      'FinanceEngine - Budget monitoring'
    ];
    
    return agents.map(agent => `• ${agent} (${['Active', 'Idle', 'Processing'][Math.floor(Math.random() * 3)]})`).join('\n');
  };

  const generateDirectoryListing = () => {
    const files = ['Documents', 'Downloads', 'Pictures', 'Videos', 'Music', 'Desktop', 'temp', 'system'];
    const dirs = files.filter(() => Math.random() > 0.3).map(f => 
      `2024-01-10  ${Math.floor(10 + Math.random() * 8)}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}    <DIR>          ${f}`
    );
    
    return dirs.join('\n') + `\n               ${dirs.length} Dir(s)  ${Math.round(Math.random() * 100000000000)} bytes free`;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (command.trim() && !isProcessing) {
      executeCommand(command);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      if (suggestions.length > 0) {
        setCommand(suggestions[selectedSuggestion]);
        setSuggestions([]);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const userCommands = history.filter(h => h.type === 'user').map(h => h.command);
      if (userCommands.length > 0) {
        const currentIndex = userCommands.indexOf(command);
        const newIndex = currentIndex > 0 ? currentIndex - 1 : userCommands.length - 1;
        setCommand(userCommands[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const userCommands = history.filter(h => h.type === 'user').map(h => h.command);
      if (userCommands.length > 0) {
        const currentIndex = userCommands.indexOf(command);
        const newIndex = currentIndex < userCommands.length - 1 ? currentIndex + 1 : 0;
        setCommand(userCommands[newIndex]);
      }
    }
  };

  const getCommandIcon = (type) => {
    switch (type) {
      case 'system': return <Terminal className="w-4 h-4 text-green-400" />;
      case 'agent': return <Activity className="w-4 h-4 text-blue-400" />;
      case 'windows': return <Cpu className="w-4 h-4 text-yellow-400" />;
      case 'gpu': return <Zap className="w-4 h-4 text-purple-400" />;
      case 'dharma': return <Shield className="w-4 h-4 text-red-400" />;
      default: return <Terminal className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Terminal Header */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-green-300 flex items-center gap-3">
            <Terminal className="w-8 h-8" />
            Command Terminal
          </h2>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              History: {history.length} commands
            </div>
            <div className={`w-3 h-3 rounded-full ${isProcessing ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`} />
          </div>
        </div>

        {/* Terminal Output */}
        <div 
          ref={terminalRef}
          className="bg-black rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm mb-4 border border-gray-700"
          onClick={() => inputRef.current?.focus()}
        >
          <AnimatePresence>
            {history.map((entry) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-3"
              >
                {/* User Command */}
                {entry.type === 'user' && (
                  <div className="flex items-start gap-2 mb-1">
                    <span className="text-green-400">❯</span>
                    <span className="text-gray-300">{entry.command}</span>
                  </div>
                )}
                
                {/* Command Output */}
                {entry.output && (
                  <div className="ml-4">
                    <div className="flex items-center gap-2 mb-2">
                      {getCommandIcon(entry.type)}
                      <span className="text-gray-500 text-xs">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-gray-200 whitespace-pre-wrap">
                      {entry.output}
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Processing Indicator */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-yellow-400"
            >
              <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
              Processing command...
            </motion.div>
          )}
        </div>

        {/* Command Input */}
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-center gap-2 bg-gray-800 rounded-lg border border-gray-700 p-3">
            <span className="text-green-400">❯</span>
            <input
              ref={inputRef}
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isProcessing}
              placeholder="Enter command... (Tab for autocomplete, ↑↓ for history)"
              className="flex-1 bg-transparent text-gray-300 placeholder-gray-500 outline-none font-mono"
              autoComplete="off"
            />
            <motion.button
              type="submit"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              disabled={isProcessing || !command.trim()}
              className="p-2 bg-green-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </motion.button>
          </div>

          {/* Suggestions Dropdown */}
          <AnimatePresence>
            {suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute bottom-full left-0 right-0 mb-2 bg-gray-800 border border-gray-700 rounded-lg overflow-hidden z-10"
              >
                {suggestions.map((suggestion, index) => (
                  <div
                    key={suggestion}
                    className={`
                      px-4 py-2 font-mono text-sm cursor-pointer transition-colors
                      ${index === selectedSuggestion 
                        ? 'bg-green-900/50 text-green-300' 
                        : 'text-gray-300 hover:bg-gray-700'
                      }
                    `}
                    >
                    {suggestion}
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </form>

        {/* Quick Commands */}
        <div className="mt-4 flex flex-wrap gap-2">
          {[
            'system.status',
            'agent.list', 
            'neural.pulse',
            'gpu.status',
            'dharma.status',
            'help'
          ].map((cmd) => (
            <motion.button
              key={cmd}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setCommand(cmd)}
              className="px-3 py-1 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 hover:border-green-600 hover:text-green-300 transition-all duration-300"
            >
              {cmd}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Command Reference */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <h3 className="text-xl font-bold text-green-300 mb-4">Command Reference</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { cmd: 'system.status', desc: 'Show system status' },
            { cmd: 'system.optimize', desc: 'Optimize system performance' },
            { cmd: 'agent.list', desc: 'List all agents' },
            { cmd: 'agent.start <name>', desc: 'Start specific agent' },
            { cmd: 'agent.stop <name>', desc: 'Stop specific agent' },
            { cmd: 'neural.pulse', desc: 'Show neural pulse data' },
            { cmd: 'gpu.status', desc: 'Show GPU status' },
            { cmd: 'gpu.mode <mode>', desc: 'Set GPU performance mode' },
            { cmd: 'dharma.status', desc: 'Show safety system status' },
            { cmd: 'ocr.capture', desc: 'Capture and analyze screen' },
            { cmd: 'sandbox.execute <file>', desc: 'Execute file in sandbox' },
            { cmd: 'help', desc: 'Show command reference' }
          ].map((item) => (
            <div key={item.cmd} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
              <div className="font-mono text-xs text-green-400 mb-1">{item.cmd}</div>
              <div className="text-xs text-gray-400">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
