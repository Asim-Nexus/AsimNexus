import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Cpu, HardDrive, Zap, TrendingUp } from 'lucide-react';

export default function NeuralPulse() {
  const [pulseData, setPulseData] = useState({
    cpu: 45,
    gpu: 62,
    memory: 68,
    temperature: 58,
    frequency: 2.1
  });
  const [pulseHistory, setPulseHistory] = useState([]);
  const [isPulsing, setIsPulsing] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time neural pulse data
      const newData = {
        cpu: 40 + Math.random() * 30,
        gpu: 55 + Math.random() * 25,
        memory: 60 + Math.random() * 20,
        temperature: 55 + Math.random() * 15,
        frequency: 1.8 + Math.random() * 0.6,
        timestamp: Date.now()
      };

      setPulseData(newData);
      setPulseHistory(prev => [...prev.slice(-29), newData]);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (value, type) => {
    if (type === 'temperature') {
      if (value > 80) return 'text-red-400';
      if (value > 70) return 'text-yellow-400';
      return 'text-green-400';
    }
    if (value > 85) return 'text-red-400';
    if (value > 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getProgressBarColor = (value) => {
    if (value > 85) return 'bg-red-500';
    if (value > 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-6">
      {/* Neural Pulse Visualization */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-green-300 flex items-center gap-3">
            <Activity className="w-8 h-8" />
            Neural Pulse Monitor
          </h2>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isPulsing ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-sm text-gray-400">
              {isPulsing ? 'Active' : 'Idle'}
            </span>
          </div>
        </div>

        {/* Live Waveform */}
        <div className="relative h-32 bg-black rounded-lg overflow-hidden mb-6">
          <svg className="absolute inset-0 w-full h-full">
            <defs>
              <linearGradient id="neuralGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.4" />
              </linearGradient>
            </defs>
            <motion.path
              d={`M 0,64 ${pulseHistory.map((point, i) => 
                `L ${(i / 30) * 100},${64 - (point.cpu / 100) * 50}`
              ).join(' ')}`}
              stroke="url(#neuralGradient)"
              strokeWidth="2"
              fill="none"
              animate={{
                d: `M 0,64 ${pulseHistory.map((point, i) => 
                  `L ${(i / 30) * 100},${64 - (point.cpu / 100) * 50}`
                ).join(' ')}`
              }}
              transition={{ duration: 1 }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              className="text-4xl font-bold text-green-400"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {Math.round(pulseData.cpu)}%
            </motion.div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* CPU */}
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-400" />
                <span className="text-sm font-medium text-gray-300">CPU</span>
              </div>
              <span className={`text-sm font-bold ${getStatusColor(pulseData.cpu)}`}>
                {Math.round(pulseData.cpu)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <motion.div
                className={`h-2 rounded-full ${getProgressBarColor(pulseData.cpu)}`}
                initial={{ width: 0 }}
                animate={{ width: `${pulseData.cpu}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* GPU */}
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <HardDrive className="w-5 h-5 text-green-400" />
                <span className="text-sm font-medium text-gray-300">RTX 2060</span>
              </div>
              <span className={`text-sm font-bold ${getStatusColor(pulseData.gpu)}`}>
                {Math.round(pulseData.gpu)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <motion.div
                className={`h-2 rounded-full ${getProgressBarColor(pulseData.gpu)}`}
                initial={{ width: 0 }}
                animate={{ width: `${pulseData.gpu}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Memory */}
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-400" />
                <span className="text-sm font-medium text-gray-300">Memory</span>
              </div>
              <span className={`text-sm font-bold ${getStatusColor(pulseData.memory)}`}>
                {Math.round(pulseData.memory)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <motion.div
                className={`h-2 rounded-full ${getProgressBarColor(pulseData.memory)}`}
                initial={{ width: 0 }}
                animate={{ width: `${pulseData.memory}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Temperature */}
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-red-400" />
                <span className="text-sm font-medium text-gray-300">Temp</span>
              </div>
              <span className={`text-sm font-bold ${getStatusColor(pulseData.temperature, 'temperature')}`}>
                {Math.round(pulseData.temperature)}°C
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <motion.div
                className={`h-2 rounded-full ${getProgressBarColor(pulseData.temperature, 'temperature')}`}
                initial={{ width: 0 }}
                animate={{ width: `${(pulseData.temperature / 100) * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>

        {/* Neural Frequency */}
        <div className="mt-6 p-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg border border-purple-700/30">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400 mb-1">Neural Frequency</div>
              <div className="text-2xl font-bold text-purple-300">
                {pulseData.frequency.toFixed(2)} GHz
              </div>
            </div>
            <motion.div
              className="w-16 h-16 rounded-full border-2 border-purple-400 flex items-center justify-center"
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Activity className="w-8 h-8 text-purple-400" />
            </motion.div>
          </div>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="bg-gray-900/50 rounded-xl p-6 border border-green-800/30">
        <h3 className="text-xl font-bold text-green-300 mb-4">Performance Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">System Load</div>
            <div className="text-lg font-bold text-green-300">
              {Math.round((pulseData.cpu + pulseData.gpu) / 2)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Optimal Range: 40-70%</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Thermal Status</div>
            <div className={`text-lg font-bold ${getStatusColor(pulseData.temperature, 'temperature')}`}>
              {pulseData.temperature > 80 ? 'Critical' : pulseData.temperature > 70 ? 'Warning' : 'Normal'}
            </div>
            <div className="text-xs text-gray-500 mt-1">Max Safe: 85°C</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Efficiency</div>
            <div className="text-lg font-bold text-blue-300">
              {Math.round(100 - (pulseData.memory - 60))}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Memory Utilization</div>
          </div>
        </div>
      </div>
    </div>
  );
}
