/**
 * ComplexVisualizationOrb.jsx
 * ============================
 * Asim Orb with Complex Number Visualizations:
 * - Live Fractal Background (Mandelbrot/Julia)
 * - Wave Propagation Display
 * - FFT Spectrum Analyzer
 * - Quantum State Visualizer
 * 
 * i² = -1 powering beautiful visual math
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Activity, Zap, Radio, Eye, Mic, BarChart3 } from 'lucide-react';

const ComplexVisualizationOrb = ({ 
  mode = 'fractal', 
  systemMetrics = {},
  voiceData = null,
  isRecording = false,
  className = ''
}) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [frame, setFrame] = useState(0);
  const [pulsePhase, setPulsePhase] = useState(0);

  // Pulse animation for orb
  useEffect(() => {
    const interval = setInterval(() => {
      setPulsePhase(p => (p + 2) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Fractal rendering
  const renderFractal = useCallback((ctx, width, height, time) => {
    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;

    // Health-based coloring
    const health = systemMetrics.health || 0.7;
    const iterations = 50 + Math.floor(health * 100);
    
    // Zoom based on system state
    const zoom = 1 + (1 - health) * 3;
    const xMin = -2.5 / zoom, xMax = 1.0 / zoom;
    const yMin = -1.25 / zoom, yMax = 1.25 / zoom;

    for (let y = 0; y < height; y += 2) {
      for (let x = 0; x < width; x += 2) {
        const cx = xMin + (x / width) * (xMax - xMin);
        const cy = yMin + (y / height) * (yMax - yMin);

        // Mandelbrot: z² + c
        let zx = 0, zy = 0;
        let i = 0;
        while (zx * zx + zy * zy < 4 && i < iterations) {
          const temp = zx * zx - zy * zy + cx;
          zy = 2 * zx * zy + cy;
          zx = temp;
          i++;
        }

        // Color mapping based on escape time
        const r = i < iterations ? Math.min(255, i * 8) : 0;
        const g = i < iterations ? Math.min(255, i * 4) : 0;
        const b = i < iterations ? Math.min(255, i * 12 + 100) : 0;

        // Fill 2x2 block
        for (let dy = 0; dy < 2 && y + dy < height; dy++) {
          for (let dx = 0; dx < 2 && x + dx < width; dx++) {
            const idx = ((y + dy) * width + (x + dx)) * 4;
            data[idx] = r;
            data[idx + 1] = g;
            data[idx + 2] = b;
            data[idx + 3] = 200; // Alpha
          }
        }
      }
    }

    ctx.putImageData(imageData, 0, 0);
  }, [systemMetrics]);

  // Wave propagation rendering
  const renderWaves = useCallback((ctx, width, height, time) => {
    const centerX = width / 2;
    const centerY = height / 2;
    
    // Clear with dark background
    ctx.fillStyle = 'rgba(10, 10, 26, 0.3)';
    ctx.fillRect(0, 0, width, height);

    // Draw interference pattern: ψ = A·e^(i(kr-ωt))
    const numWaves = 3;
    const meshHealth = systemMetrics.mesh_health || 0.85;
    const amplitude = 30 * meshHealth;
    
    for (let w = 0; w < numWaves; w++) {
      ctx.beginPath();
      ctx.strokeStyle = `hsla(${200 + w * 40}, 70%, 60%, ${0.3 + meshHealth * 0.4})`;
      ctx.lineWidth = 2;

      for (let angle = 0; angle < Math.PI * 2; angle += 0.1) {
        const r = 50 + w * 40;
        const x = centerX + Math.cos(angle) * r;
        const y = centerY + Math.sin(angle) * r;
        
        // Wave oscillation
        const wave = Math.sin(angle * 8 + time * 0.005 + w * 2) * amplitude;
        const radius = r + wave;
        
        const px = centerX + Math.cos(angle) * radius;
        const py = centerY + Math.sin(angle) * radius;
        
        if (angle === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw node positions
    const nodes = [
      { x: 0.3, y: 0.3 },
      { x: 0.7, y: 0.3 },
      { x: 0.5, y: 0.7 }
    ];

    nodes.forEach((node, i) => {
      const nx = node.x * width;
      const ny = node.y * height;
      
      // Node glow
      const gradient = ctx.createRadialGradient(nx, ny, 0, nx, ny, 20);
      gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
      gradient.addColorStop(1, 'rgba(102, 126, 234, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(nx, ny, 20, 0, Math.PI * 2);
      ctx.fill();
      
      // Node center
      ctx.fillStyle = '#fff';
      ctx.beginPath();
      ctx.arc(nx, ny, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [systemMetrics]);

  // FFT Spectrum rendering
  const renderSpectrum = useCallback((ctx, width, height, time) => {
    if (!voiceData || !isRecording) {
      // Idle animation
      ctx.fillStyle = 'rgba(10, 10, 26, 0.5)';
      ctx.fillRect(0, 0, width, height);
      
      // Draw idle bars
      const bars = 16;
      const barWidth = width / bars;
      
      for (let i = 0; i < bars; i++) {
        const h = 10 + Math.sin(time * 0.01 + i * 0.5) * 5;
        const hue = 200 + i * 10;
        ctx.fillStyle = `hsla(${hue}, 70%, 60%, 0.3)`;
        ctx.fillRect(i * barWidth, height - h, barWidth - 2, h);
      }
      return;
    }

    // Real FFT visualization
    ctx.fillStyle = 'rgba(10, 10, 26, 0.3)';
    ctx.fillRect(0, 0, width, height);

    const bins = 32;
    const binWidth = width / bins;
    
    // Use voiceData frequencies or generate from time
    const frequencies = voiceData.frequencies || 
      Array.from({ length: bins }, (_, i) => 
        Math.abs(Math.sin(time * 0.02 + i * 0.3)) * 
        Math.exp(-i * 0.1) * 100
      );

    frequencies.forEach((freq, i) => {
      const barHeight = Math.min(height - 10, freq * height / 200);
      const hue = 120 + (freq / 200) * 100; // Green to red
      
      // Gradient bar
      const gradient = ctx.createLinearGradient(0, height, 0, height - barHeight);
      gradient.addColorStop(0, `hsla(${hue}, 70%, 50%, 0.8)`);
      gradient.addColorStop(1, `hsla(${hue}, 70%, 70%, 0.4)`);
      
      ctx.fillStyle = gradient;
      ctx.fillRect(i * binWidth, height - barHeight, binWidth - 1, barHeight);
    });

    // Peak frequency indicator
    const peakIdx = frequencies.indexOf(Math.max(...frequencies));
    const peakFreq = Math.round(peakIdx * 22050 / bins); // Assuming 44.1kHz
    
    ctx.fillStyle = '#fff';
    ctx.font = '10px monospace';
    ctx.fillText(`${peakFreq} Hz`, 5, 15);
  }, [voiceData, isRecording]);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let time = 0;

    const animate = () => {
      time += 1;
      setFrame(time);

      const width = canvas.width;
      const height = canvas.height;

      switch (mode) {
        case 'fractal':
          if (time % 5 === 0) renderFractal(ctx, width, height, time);
          break;
        case 'wave':
          renderWaves(ctx, width, height, time);
          break;
        case 'spectrum':
          renderSpectrum(ctx, width, height, time);
          break;
        default:
          renderFractal(ctx, width, height, time);
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [mode, renderFractal, renderWaves, renderSpectrum]);

  const glowIntensity = 0.5 + Math.sin(pulsePhase * Math.PI / 180) * 0.3;

  return (
    <div className={`complex-visualization-orb ${className}`} style={{
      position: 'relative',
      width: '100%',
      height: 120,
      borderRadius: 12,
      overflow: 'hidden',
      background: 'rgba(10, 10, 26, 0.8)',
      border: `2px solid rgba(102, 126, 234, ${glowIntensity})`,
    }}>
      {/* Canvas for complex visualization */}
      <canvas
        ref={canvasRef}
        width={360}
        height={120}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
        }}
      />

      {/* Overlay UI */}
      <div style={{
        position: 'absolute',
        top: 8,
        left: 8,
        display: 'flex',
        gap: 8,
        alignItems: 'center',
      }}>
        {mode === 'fractal' && <Zap size={14} color="#667eea" />}
        {mode === 'wave' && <Radio size={14} color="#667eea" />}
        {mode === 'spectrum' && <BarChart3 size={14} color="#667eea" />}
        <span style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.7)',
          textTransform: 'uppercase',
          letterSpacing: 1,
        }}>
          {mode}
        </span>
        {isRecording && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 10,
            color: '#ef4444',
            animation: 'pulse 1s infinite',
          }}>
            <Mic size={10} /> REC
          </span>
        )}
      </div>

      {/* System metrics overlay */}
      <div style={{
        position: 'absolute',
        bottom: 8,
        right: 8,
        display: 'flex',
        gap: 12,
        fontSize: 10,
        color: 'rgba(255,255,255,0.6)',
      }}>
        {systemMetrics.health && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Activity size={10} />
            {(systemMetrics.health * 100).toFixed(0)}%
          </span>
        )}
        {systemMetrics.mesh_health && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Radio size={10} />
            {(systemMetrics.mesh_health * 100).toFixed(0)}%
          </span>
        )}
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Eye size={10} />
          {frame}
        </span>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

export default ComplexVisualizationOrb;
