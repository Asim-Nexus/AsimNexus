import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Shield, Users, Terminal, Cpu, HardDrive, Wifi, Zap } from 'lucide-react';
import NeuralPulse from '../components/NeuralPulse';
import DharmaChakra from '../components/DharmaChakra';
import AgentStream from '../components/AgentStream';
import CommandTerminal from '../components/CommandTerminal';
import SovereignHeader from '../components/SovereignHeader';

export default function Home() {
  const [activeTab, setActiveTab] = useState('neural');
  const [systemStatus, setSystemStatus] = useState('online');
  const [heartbeat, setHeartbeat] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws/live');
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('🧠 ASIMNEXUS Neural Core Connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'heartbeat') {
        setHeartbeat(prev => prev + 1);
      }
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      console.log('🔌 Neural Core Disconnected');
    };
    
    return () => ws.close();
  }, []);

  const tabs = [
    { id: 'neural', name: 'Neural Pulse', icon: Activity, component: NeuralPulse },
    { id: 'dharma', name: 'Dharma-Chakra', icon: Shield, component: DharmaChakra },
    { id: 'agents', name: 'Agent Stream', icon: Users, component: AgentStream },
    { id: 'terminal', name: 'Command Terminal', icon: Terminal, component: CommandTerminal }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || NeuralPulse;

  return (
    <>
      <Head>
        <title>ASIMNEXUS - Neural Awakening Dashboard</title>
        <meta name="description" content="ASIMNEXUS Universal Operating System - Live Neural Core Interface" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-black text-green-400 overflow-hidden">
        {/* Animated Background */}
        <div className="fixed inset-0 opacity-20">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-black to-blue-900/20" />
          <div className="absolute inset-0">
            {[...Array(50)].map((_, i) => (
              <div
                key={i}
                className="absolute w-1 h-1 bg-green-400 rounded-full animate-pulse"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 5}s`,
                  animationDuration: `${3 + Math.random() * 4}s`
                }}
              />
            ))}
          </div>
        </div>

        {/* Header */}
        <SovereignHeader 
          systemStatus={systemStatus}
          heartbeat={heartbeat}
          wsConnected={wsConnected}
        />

        {/* Main Content */}
        <div className="relative z-10 container mx-auto px-4 py-6">
          {/* Tab Navigation */}
          <div className="mb-8 flex flex-wrap gap-2 justify-center">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <motion.button
                  key={tab.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300
                    ${activeTab === tab.id 
                      ? 'bg-green-500/20 border border-green-400 text-green-300 shadow-lg shadow-green-500/25' 
                      : 'bg-gray-900/50 border border-gray-700 text-gray-400 hover:border-green-600 hover:text-green-300'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.name}</span>
                  {activeTab === tab.id && (
                    <motion.div
                      className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-green-400 rounded-full"
                      animate={{ scale: [1, 1.5, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  )}
                </motion.button>
              );
            })}
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="w-full"
            >
              <ActiveComponent />
            </motion.div>
          </AnimatePresence>

          {/* System Status Bar */}
          <div className="fixed bottom-0 left-0 right-0 bg-black/90 backdrop-blur-lg border-t border-green-800/30">
            <div className="container mx-auto px-4 py-3">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-green-400" />
                    <span className="text-green-300">Neural Core: Active</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4 text-blue-400" />
                    <span className="text-blue-300">RTX 2060: Optimal</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <span className="text-yellow-300">Power: Balanced</span>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`} />
                    <span className="text-gray-400">
                      {wsConnected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                  <div className="text-gray-500">
                    Heartbeat: {heartbeat}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
