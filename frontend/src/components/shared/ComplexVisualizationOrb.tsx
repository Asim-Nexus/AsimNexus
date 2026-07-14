/**
 * ComplexVisualizationOrb.tsx
 * Production visualization orb with 3 modes: fractal, wave, spectrum
 * Renders real-time animated visualizations using Canvas2D
 */
import { useRef, useEffect, useCallback } from 'react';

interface SystemMetrics {
    health?: number;
    mesh_health?: number;
    [key: string]: unknown;
}

interface VoiceAnalysisData {
    frequencies?: number[];
    pitch?: number;
    command?: string;
    [key: string]: unknown;
}

interface ComplexVisualizationOrbProps {
    mode: string;
    systemMetrics?: SystemMetrics;
    voiceData?: VoiceAnalysisData;
    isRecording?: boolean;
}

const ComplexVisualizationOrb: React.FC<ComplexVisualizationOrbProps> = ({
    mode,
    systemMetrics,
    voiceData,
    isRecording,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animRef = useRef<number>(0);
    const timeRef = useRef<number>(0);

    const health = systemMetrics?.health ?? 0.85;
    const meshHealth = systemMetrics?.mesh_health ?? 0.75;
    const freqs = voiceData?.frequencies ?? [];
    const pitch = voiceData?.pitch ?? 0;

    const drawFractal = useCallback((ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        const cx = w / 2;
        const cy = h / 2;
        const maxR = Math.min(w, h) * 0.42;

        // Clear
        ctx.clearRect(0, 0, w, h);

        // Background glow
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR * 1.2);
        grad.addColorStop(0, `hsla(${(t * 30) % 360}, 70%, 50%, 0.15)`);
        grad.addColorStop(0.5, `hsla(${(t * 30 + 120) % 360}, 60%, 40%, 0.08)`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Fractal tree branches
        const branches = 5 + Math.floor(health * 4);
        for (let i = 0; i < branches; i++) {
            const angle = (i / branches) * Math.PI * 2 + t * 0.3;
            const depth = 3 + Math.floor(meshHealth * 3);
            const hue = (i * 60 + t * 40) % 360;
            const sat = 60 + health * 30;
            const lit = 40 + meshHealth * 30;

            ctx.strokeStyle = `hsla(${hue}, ${sat}%, ${lit}%, ${0.3 + health * 0.4})`;
            ctx.lineWidth = 1.5 + health * 1.5;
            ctx.beginPath();
            ctx.moveTo(cx, cy);

            let x = cx;
            let y = cy;
            let len = maxR * 0.3;
            for (let d = 0; d < depth; d++) {
                const da = angle + (d * 0.5) + Math.sin(t * 2 + i + d) * 0.3;
                x += Math.cos(da) * len;
                y += Math.sin(da) * len;
                ctx.lineTo(x, y);
                len *= 0.65;
            }
            ctx.stroke();

            // Leaf at tip
            if (depth > 2) {
                ctx.beginPath();
                ctx.arc(x, y, 2 + health * 2, 0, Math.PI * 2);
                ctx.fillStyle = `hsla(${(hue + 30) % 360}, 80%, 60%, ${0.4 + health * 0.3})`;
                ctx.fill();
            }
        }

        // Center pulsing orb
        const pulseR = maxR * 0.12 * (0.8 + 0.2 * Math.sin(t * 2));
        const cGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, pulseR);
        cGrad.addColorStop(0, `hsla(${(t * 50) % 360}, 80%, 70%, 0.9)`);
        cGrad.addColorStop(0.6, `hsla(${(t * 50 + 60) % 360}, 70%, 50%, 0.5)`);
        cGrad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = cGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, pulseR, 0, Math.PI * 2);
        ctx.fill();

        // Particle ring
        const particleCount = 12 + Math.floor(health * 12);
        for (let i = 0; i < particleCount; i++) {
            const pa = (i / particleCount) * Math.PI * 2 + t * 0.5;
            const pr = maxR * 0.35 + maxR * 0.15 * Math.sin(t * 1.5 + i);
            const px = cx + Math.cos(pa) * pr;
            const py = cy + Math.sin(pa) * pr;
            const ps = 1.5 + 2 * Math.sin(t * 3 + i * 2);
            ctx.beginPath();
            ctx.arc(px, py, ps, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${(i * 30 + t * 60) % 360}, 80%, 60%, ${0.3 + 0.4 * Math.sin(t + i)})`;
            ctx.fill();
        }
    }, [health, meshHealth]);

    const drawWave = useCallback((ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        const cx = w / 2;
        const cy = h / 2;
        const maxR = Math.min(w, h) * 0.4;

        ctx.clearRect(0, 0, w, h);

        // Background
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR * 1.3);
        grad.addColorStop(0, `rgba(30, 60, 120, ${0.1 + health * 0.1})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Concentric wave rings
        const rings = 4 + Math.floor(meshHealth * 4);
        for (let r = 0; r < rings; r++) {
            const radius = maxR * (0.15 + (r / rings) * 0.7);
            const points = 40 + r * 10;
            const amp = 4 + 6 * Math.sin(t * 1.5 + r * 1.2) + (freqs.length > 0 ? freqs[r % freqs.length] * 10 : 0);

            ctx.beginPath();
            for (let i = 0; i <= points; i++) {
                const a = (i / points) * Math.PI * 2;
                const wave = Math.sin(a * 3 + t * 2 + r) * amp + Math.sin(a * 5 - t * 1.5 + r * 0.5) * amp * 0.5;
                const px = cx + Math.cos(a) * (radius + wave);
                const py = cy + Math.sin(a) * (radius + wave);
                if (i === 0) ctx.moveTo(px, py);
                else ctx.lineTo(px, py);
            }
            ctx.closePath();

            const hue = (r * 40 + t * 30) % 360;
            ctx.strokeStyle = `hsla(${hue}, 70%, ${50 + health * 20}%, ${0.2 + 0.3 * (1 - r / rings)})`;
            ctx.lineWidth = 1.5 + (1 - r / rings) * 2;
            ctx.stroke();

            // Fill with subtle gradient
            const fGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius + amp);
            fGrad.addColorStop(0, `hsla(${hue}, 60%, 50%, 0.02)`);
            fGrad.addColorStop(1, `hsla(${hue}, 60%, 50%, 0)`);
            ctx.fillStyle = fGrad;
            ctx.fill();
        }

        // Center dot
        ctx.beginPath();
        ctx.arc(cx, cy, 2 + pitch * 3, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${(t * 40) % 360}, 80%, 70%, ${0.5 + 0.5 * Math.sin(t * 2)})`;
        ctx.fill();

        // Recording indicator
        if (isRecording) {
            ctx.beginPath();
            ctx.arc(cx, cy, maxR * 0.08, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(239, 68, 68, ${0.3 + 0.3 * Math.sin(t * 4)})`;
            ctx.fill();
        }
    }, [health, meshHealth, freqs, pitch, isRecording]);

    const drawSpectrum = useCallback((ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => {
        const cx = w / 2;
        const cy = h / 2;
        const maxR = Math.min(w, h) * 0.45;

        ctx.clearRect(0, 0, w, h);

        // Background
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR * 1.3);
        grad.addColorStop(0, `rgba(80, 20, 100, ${0.1 + health * 0.1})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Spectrum bars around circle
        const barCount = 24 + Math.floor(health * 16);
        const barWidth = (Math.PI * 2) / barCount * 0.7;
        const innerR = maxR * 0.3;
        const outerR = maxR * 0.85;

        for (let i = 0; i < barCount; i++) {
            const a = (i / barCount) * Math.PI * 2 + t * 0.2;
            const freqVal = freqs.length > 0
                ? freqs[Math.floor((i / barCount) * freqs.length)] ?? 0
                : Math.sin(t * 3 + i * 0.8) * 0.5 + 0.5;
            const barH = freqVal * (outerR - innerR) * 0.8 + (outerR - innerR) * 0.1;
            const r1 = innerR + barH * 0.1;
            const r2 = innerR + barH;

            const hue = (i * (360 / barCount) + t * 50) % 360;
            const sat = 70 + health * 20;
            const lit = 40 + freqVal * 30;

            ctx.beginPath();
            ctx.arc(cx, cy, r1, a - barWidth / 2, a + barWidth / 2);
            ctx.arc(cx, cy, r2, a + barWidth / 2, a - barWidth / 2, true);
            ctx.closePath();
            ctx.fillStyle = `hsla(${hue}, ${sat}%, ${lit}%, ${0.5 + freqVal * 0.3})`;
            ctx.fill();

            // Glow on tall bars
            if (freqVal > 0.6) {
                ctx.shadowColor = `hsla(${hue}, 80%, 60%, 0.3)`;
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }

        // Center ring
        ctx.beginPath();
        ctx.arc(cx, cy, innerR * 0.5, 0, Math.PI * 2);
        ctx.strokeStyle = `hsla(${(t * 40) % 360}, 70%, 60%, ${0.2 + 0.2 * Math.sin(t)})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Recording pulse
        if (isRecording) {
            const pulseR = innerR * 0.3 * (0.8 + 0.2 * Math.sin(t * 3));
            ctx.beginPath();
            ctx.arc(cx, cy, pulseR, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(239, 68, 68, ${0.2 + 0.3 * Math.sin(t * 4)})`;
            ctx.fill();
        }
    }, [health, freqs, isRecording]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const resize = () => {
            const parent = canvas.parentElement;
            if (parent) {
                canvas.width = parent.clientWidth;
                canvas.height = parent.clientHeight;
            }
        };
        resize();
        window.addEventListener('resize', resize);

        const animate = (timestamp: number) => {
            timeRef.current = timestamp / 1000;
            const w = canvas.width;
            const h = canvas.height;
            if (w === 0 || h === 0) {
                animRef.current = requestAnimationFrame(animate);
                return;
            }

            switch (mode) {
                case 'wave':
                    drawWave(ctx, w, h, timeRef.current);
                    break;
                case 'spectrum':
                    drawSpectrum(ctx, w, h, timeRef.current);
                    break;
                case 'fractal':
                default:
                    drawFractal(ctx, w, h, timeRef.current);
                    break;
            }

            animRef.current = requestAnimationFrame(animate);
        };

        animRef.current = requestAnimationFrame(animate);

        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animRef.current);
        };
    }, [mode, drawFractal, drawWave, drawSpectrum]);

    return (
        <canvas
            ref={canvasRef}
            style={{
                width: '100%',
                height: '100%',
                display: 'block',
                pointerEvents: 'none',
            }}
        />
    );
};

export default ComplexVisualizationOrb;
