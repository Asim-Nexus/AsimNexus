import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Shield, Wifi, Zap, Cpu, HardDrive } from 'lucide-react';

export default function SovereignHeader({ systemStatus, heartbeat, wsConnected }) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 45,
    memory: 68,
    gpu: 62,
    temperature: 58
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const metricsTimer = setInterval(() => {
      setSystemMetrics({
        cpu: 40 + Math.random() * 30,
        memory: 60 + Math.random() * 20,
        gpu: 50 + Math.random() * 30,
        temperature: 55 + Math.random() * 15
      });
    }, 2000);

    return () => clearInterval(metricsTimer);
  }, []);

  return (
    <div className="relative z-20">
      {/* Animated Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-purple-900/20 via-transparent to-blue-900/20" />
      
      <div className="relative container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Left Side - Title and Status */}
          <div className="flex items-center gap-6">
            {/* Main Title */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
              <motion.div
                className="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center"
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <Activity className="w-6 h-6 text-white" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold text-green-300">ASIMNEXUS</h1>
                <div className="text-xs text-gray-400">Neural Core Interface</div>
              </div>
            </motion.div>

            {/* Status Indicators */}
            <div className="flex items-center gap-4">
              <motion.div
                className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-900/30 border border-green-700"
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Shield className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-300">Safety Engaged</span>
              </motion.div>
              
              <motion.div
                className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/30 border border-blue-700"
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
              >
                <Cpu className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-blue-300">Neural Active</span>
              </motion.div>
            </div>
          </div>

          {/* Center - Time and Heartbeat */}
          <div className="flex flex-col items-center">
            <motion.div
              className="text-3xl font-bold text-green-300 tabular-nums"
              animate={{ opacity: [0.8, 1, 0.8] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              {currentTime.toLocaleTimeString()}
            </motion.div>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-1">
                <Activity className="w-3 h-3" />
                <span>Heartbeat: {heartbeat}</span>
              </div>
              <div className="flex items-center gap-1">
                <Wifi className={`w-3 h-3 ${wsConnected ? 'text-green-400' : 'text-red-400'}`} />
                <span className={wsConnected ? 'text-green-400' : 'text-red-400'}>
                  {wsConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          {/* Right Side - System Metrics */}
          <div className="flex items-center gap-6">
            {/* CPU */}
            <motion.div
              className="flex items-center gap-2"
              whileHover={{ scale: 1.1 }}
            >
              <Cpu className="w-5 h-5 text-blue-400" />
              <div className="text-right">
                <div className="text-sm font-bold text-blue-300">
                  {Math.round(systemMetrics.cpu)}%
                </div>
                <div className="text-xs text-gray-500">CPU</div>
              </div>
            </motion.div>

            {/* GPU */}
            <motion.div
              className="flex items-center gap-2"
              whileHover={{ scale: 1.1 }}
            >
              <HardDrive className="w-5 h-5 text-green-400" />
              <div className="text-right">
                <div className="text-sm font-bold text-green-300">
                  {Math.round(systemMetrics.gpu)}%
                </div>
                <div className="text-xs text-gray-500">RTX 2060</div>
              </div>
            </motion.div>

            {/* Memory */}
            <motion.div
              className="flex items-center gap-2"
              whileHover={{ scale: 1.1 }}
            >
              <Zap className="w-5 h-5 text-yellow-400" />
              <div className="text-right">
                <div className="text-sm font-bold text-yellow-300">
                  {Math.round(systemMetrics.memory)}%
                </div>
                <div className="text-xs text-gray-500">Memory</div>
              </div>
            </motion.div>

            {/* Temperature */}
            <motion.div
              className="flex items-center gap-2"
              whileHover={{ scale: 1.1 }}
            >
              <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                systemMetrics.temperature > 80 ? 'bg-red-500' :
                systemMetrics.temperature > 70 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}>
                <div className="w-2 h-2 bg-white rounded-full" />
              </div>
              <div className="text-right">
                <div className={`text-sm font-bold ${
                  systemMetrics.temperature > 80 ? 'text-red-300' :
                  systemMetrics.temperature > 70 ? 'text-yellow-300' :
                  'text-green-300'
                }`}>
                  {Math.round(systemMetrics.temperature)}°C
                </div>
                <div className="text-xs text-gray-500">Temp</div>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4 h-1 bg-gray-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-green-500 via-blue-500 to-purple-500"
            initial={{ width: 0 }}
            animate={{ width: `${(systemMetrics.cpu + systemMetrics.gpu) / 2}%` }}
            transition={{ duration: 1 }}
          />
        </div>
      </div>
    </div>
  );
}
