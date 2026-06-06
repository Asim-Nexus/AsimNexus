/**
 * ASIMNEXUS Sovereign Interface
 * ===============================
 * Digital Entity Control Dashboard
 * React Frontend with Sovereign Theme
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Activity, Shield, Database, Terminal, Brain, Cpu, HardDrive, Wifi } from 'lucide-react';
import './App.css';

// Import Components
import NeuralPulse from './components/NeuralPulse';
import DharmaChakra from './components/DharmaChakra';
import MemoryStream from './components/MemoryStream';
import CommandTerminal from './components/CommandTerminal';
import SystemStatus from './components/SystemStatus';
import SovereignHeader from './components/SovereignHeader';

function App() {
  const [systemStatus, setSystemStatus] = useState({
    neural_gateway: 'offline',
    safety_system: 'offline',
    kill_switch: 'offline',
    heartbeat: 0,
    cpu_usage: 0,
    memory_usage: 0,
    gpu_usage: 0,
    connected: false
  });

  const [memories, setMemories] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [wsConnection, setWsConnection] = useState(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('🧠 Connected to ASIMNEXUS Neural Core');
      setSystemStatus(prev => ({ ...prev, connected: true }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onclose = () => {
      console.log('🔌 Disconnected from ASIMNEXUS');
      setSystemStatus(prev => ({ ...prev, connected: false }));
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket Error:', error);
      setSystemStatus(prev => ({ ...prev, connected: false }));
    };

    setWsConnection(ws);

    // Cleanup
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'system_update':
        setSystemStatus(data.data);
        break;
      case 'heartbeat':
        setSystemStatus(prev => ({
          ...prev,
          heartbeat: prev.heartbeat + 1
        }));
        break;
      case 'memory_update':
        setMemories(data.data.memories || []);
        break;
      case 'policy_update':
        setPolicies(data.data.policies || []);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  // Fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // System Status
        const statusResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/system/status`);
        const statusData = await statusResponse.json();
        if (!statusData.error) {
          setSystemStatus(prev => ({ ...prev, ...statusData }));
        }

        // Memory Stream
        const memoryResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/memory/stream`);
        const memoryData = await memoryResponse.json();
        if (!memoryData.error) {
          setMemories(memoryData.memories || []);
        }

        // Safety Policies
        const policiesResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/safety/policies`);
        const policiesData = await policiesResponse.json();
        if (!policiesData.error) {
          setPolicies(policiesData.policies || []);
        }

      } catch (error) {
        console.error('❌ Failed to fetch initial data:', error);
      }
    };

    fetchInitialData();
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Sovereign Header */}
        <SovereignHeader systemStatus={systemStatus} />
        
        {/* Main Dashboard */}
        <main className="container mx-auto px-4 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            
            {/* Neural Pulse Monitor */}
            <div className="xl:col-span-2">
              <NeuralPulse systemStatus={systemStatus} />
            </div>

            {/* Dharma-Chakra Status */}
            <div>
              <DharmaChakra policies={policies} systemStatus={systemStatus} />
            </div>

            {/* Memory Stream */}
            <div>
              <MemoryStream memories={memories} />
            </div>

            {/* Command Terminal */}
            <div className="xl:col-span-2 lg:col-span-1">
              <CommandTerminal wsConnection={wsConnection} />
            </div>

            {/* System Status Panel */}
            <div>
              <SystemStatus systemStatus={systemStatus} />
            </div>

          </div>
        </main>

        {/* Connection Status */}
        <div className="fixed bottom-4 right-4 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 shadow-lg">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${systemStatus.connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
            <span className="text-sm text-slate-300">
              {systemStatus.connected ? 'Connected to Neural Core' : 'Disconnected'}
            </span>
          </div>
        </div>

      </div>
    </Router>
  );
}

export default App;
