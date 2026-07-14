/**
 * VoiceAnalysisService.ts
 * =======================
 * Connects Signal Processing Module to Floating Orb
 * Live voice analysis with FFT spectrum display
 *
 * Features:
 * - Real-time microphone capture
 * - FFT spectrum analysis
 * - Pitch detection
 * - Voice activity detection
 * - Command recognition
 */

interface VoiceAnalysisResult {
    frequencies: number[];
    pitch: number;
    isVoice: boolean;
    energy: number;
    command?: string;
    timestamp?: number;
    [key: string]: unknown;
}

type AnalysisCallback = (analysis: VoiceAnalysisResult) => void;

class VoiceAnalysisService {
    private isInitialized: boolean = false;
    private isRecording: boolean = false;
    private audioContext: AudioContext | null = null;
    private analyser: AnalyserNode | null = null;
    private microphone: MediaStreamAudioSourceNode | null = null;
    private callbacks: AnalysisCallback[] = [];
    private analysisInterval: number | null = null;

    // Analysis results
    private lastAnalysis: VoiceAnalysisResult = {
        frequencies: [],
        pitch: 0,
        isVoice: false,
        energy: 0,
    };

    async init(): Promise<boolean> {
        if (this.isInitialized) return true;

        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000,
                },
            });

            // Create audio context
            const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
            this.audioContext = new AudioCtx({
                sampleRate: 16000,
            });

            // Create analyser node
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;

            // Connect microphone
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.microphone.connect(this.analyser);

            this.isInitialized = true;
            console.log('[VoiceAnalysis] Initialized');
            return true;
        } catch (error) {
            console.error('[VoiceAnalysis] Init failed:', error);
            return false;
        }
    }

    startAnalysis(callback?: AnalysisCallback): boolean {
        if (!this.isInitialized) {
            console.warn('[VoiceAnalysis] Not initialized');
            return false;
        }

        if (this.isRecording) return true;

        this.isRecording = true;
        if (callback) this.callbacks.push(callback);

        const bufferLength = this.analyser!.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        let frameCount = 0;

        // Analysis loop
        const analyze = () => {
            if (!this.isRecording) return;

            // Get frequency data
            this.analyser!.getByteFrequencyData(dataArray);

            // Convert to frequency array (0-8kHz range)
            const frequencies = Array.from(dataArray).map(v => v);

            // Calculate energy
            const energy = frequencies.reduce((a, b) => a + b, 0) / frequencies.length;

            // Detect pitch (simplified)
            let maxVal = 0;
            let maxIdx = 0;
            for (let i = 0; i < frequencies.length; i++) {
                if (frequencies[i] > maxVal) {
                    maxVal = frequencies[i];
                    maxIdx = i;
                }
            }
            // Convert bin to frequency (assuming 16kHz sample rate)
            const pitch = (maxIdx * 16000) / (2 * bufferLength);

            // Voice activity detection
            const isVoice = energy > 30 && pitch > 80 && pitch < 1000;

            // Simple command detection based on pitch patterns
            let command: string | undefined;
            if (isVoice && frameCount % 30 === 0) {
                if (pitch < 150) command = 'low_tone';
                else if (pitch < 300) command = 'mid_tone';
                else command = 'high_tone';
            }

            this.lastAnalysis = {
                frequencies,
                pitch,
                isVoice,
                energy,
                command: command,
                timestamp: Date.now(),
            };

            // Notify callbacks
            this.callbacks.forEach(cb => {
                try {
                    cb(this.lastAnalysis);
                } catch (e) {
                    console.error('[VoiceAnalysis] Callback error:', e);
                }
            });

            frameCount++;
            this.analysisInterval = requestAnimationFrame(analyze);
        };

        analyze();
        console.log('[VoiceAnalysis] Started');
        return true;
    }

    stopAnalysis(): void {
        this.isRecording = false;
        if (this.analysisInterval !== null) {
            cancelAnimationFrame(this.analysisInterval);
            this.analysisInterval = null;
        }
        console.log('[VoiceAnalysis] Stopped');
    }

    getLastAnalysis(): VoiceAnalysisResult {
        return this.lastAnalysis;
    }

    onAnalysis(callback: AnalysisCallback): () => void {
        this.callbacks.push(callback);
        return () => {
            this.callbacks = this.callbacks.filter(cb => cb !== callback);
        };
    }

    destroy(): void {
        this.stopAnalysis();
        if (this.microphone) {
            this.microphone.disconnect();
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        this.callbacks = [];
        this.isInitialized = false;
    }
}

// Singleton instance
const voiceAnalysisService = new VoiceAnalysisService();
export default voiceAnalysisService;
