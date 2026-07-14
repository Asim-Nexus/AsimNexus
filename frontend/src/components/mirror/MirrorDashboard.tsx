// STATUS: NEW — Mirror Dashboard
// React component for AsimNexus Digital Twin Mirror integration
import React, { useState, useEffect } from 'react';
import { mirrorAPI } from '../../api/asimnexus';
import './MirrorDashboard.css';

interface MirrorStateData {
    consciousness_score?: number;
    subconscious_depth?: number;
    lora_adapted?: boolean;
}

interface MirrorDashboardProps {
    userId?: string;
}

export default function MirrorDashboard({ userId = 'default' }: MirrorDashboardProps) {
    const [mirrorState, setMirrorState] = useState<MirrorStateData | null>(null);
    const [dailyReport, setDailyReport] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    // Load mirror state on mount
    useEffect(() => {
        loadMirrorState();
        loadDailyReport();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userId]);

    const loadMirrorState = async () => {
        try {
            const state = await mirrorAPI.getState(userId);
            setMirrorState(state.data as MirrorStateData);
        } catch (e) {
            console.error('Failed to load mirror state:', e);
        }
    };

    const loadDailyReport = async () => {
        try {
            const report = await mirrorAPI.getDaily(userId);
            setDailyReport(report.data as unknown as Record<string, unknown>);
        } catch (e) {
            console.error('Failed to load daily report:', e);
        }
    };

    const handleReflect = async () => {
        setLoading(true);
        try {
            const result = await mirrorAPI.reflect(userId, message);
            const data = result.data as { success?: boolean };
            if (data?.success) {
                setMessage('');
                loadMirrorState();
            }
        } catch (e) {
            console.error('Reflect error:', e);
        }
        setLoading(false);
    };

    const handleDream = async () => {
        setLoading(true);
        try {
            const result = await mirrorAPI.dream(userId);
            console.log('Dream result:', result.data);
        } catch (e) {
            console.error('Dream error:', e);
        }
        setLoading(false);
    };

    return (
        <div className="mirror-dashboard">
            <h2>🌌 Digital Twin Mirror</h2>

            <div className="mirror-stats">
                {mirrorState && (
                    <>
                        <div className="stat-card">
                            <span className="label">Consciousness Score</span>
                            <span className="value">{mirrorState.consciousness_score || 'N/A'}</span>
                        </div>
                        <div className="stat-card">
                            <span className="label">Subconscious Depth</span>
                            <span className="value">{mirrorState.subconscious_depth || 'N/A'}</span>
                        </div>
                        <div className="stat-card">
                            <span className="label">LoRA Adapted</span>
                            <span className="value">{mirrorState.lora_adapted ? 'Yes' : 'No'}</span>
                        </div>
                    </>
                )}
            </div>

            <div className="mirror-actions">
                <textarea
                    value={message}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
                    placeholder="सोच्नुहोस्... (Reflect your thoughts)"
                    className="mirror-input"
                />
                <button
                    onClick={handleReflect}
                    disabled={loading || !message}
                    className="mirror-btn"
                >
                    चिन्तन गर्नुहोस् (Reflect)
                </button>

                <button
                    onClick={handleDream}
                    disabled={loading}
                    className="dream-btn"
                >
                    सपना देख्नुहोस् (Dream)
                </button>
            </div>

            {dailyReport && (
                <div className="daily-report">
                    <h3>दैनिक रिपोर्ट (Daily Report)</h3>
                    <pre>{JSON.stringify(dailyReport, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}
