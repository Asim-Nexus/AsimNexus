import React, { useState, useEffect } from 'react';
import { lifecycleAPI } from '../../api/asimnexus';

/**
 * Six life stages defining the AsimNexus human journey.
 * Each stage has icon, color, milestones, and a brief description.
 */

interface Milestone {
    id: string;
    label: string;
    icon: string;
}

interface LifeStage {
    id: string;
    icon: string;
    label: string;
    subtitle: string;
    color: string;
    bg: string;
    milestones: Milestone[];
}

interface LifecycleData {
    activity_count?: number;
    active_layers?: number;
    age_days?: number;
    created_at?: string;
    user_id?: string;
    mesh_nodes?: number;
    connection_network_size?: number;
    privacy_score?: number;
    total_layers?: number;
    current_state?: string;
}

interface Metric {
    label: string;
    value: string | number;
    icon: string;
}

interface LifeJourneyProps {
    user: { id?: string } | null;
}

const LIFE_STAGES: LifeStage[] = [
    {
        id: 'birth',
        icon: '🌱',
        label: 'Birth',
        subtitle: 'Genesis of your Digital Universe',
        color: '#10b981',
        bg: '#001a04',
        milestones: [
            { id: 'b1', label: 'Universe Created', icon: '✨' },
            { id: 'b2', label: 'Identity Registered', icon: '🆔' },
            { id: 'b3', label: 'First Connection', icon: '🔗' },
            { id: 'b4', label: 'Persona Defined', icon: '👤' },
        ],
    },
    {
        id: 'education',
        icon: '📖',
        label: 'Education',
        subtitle: 'Learning & Skill Acquisition',
        color: '#3b82f6',
        bg: '#00102e',
        milestones: [
            { id: 'e1', label: 'First Chat', icon: '💬' },
            { id: 'e2', label: 'Knowledge Base', icon: '📚' },
            { id: 'e3', label: 'Clone Introductions', icon: '🤖' },
            { id: 'e4', label: 'System Familiarity', icon: '🎓' },
        ],
    },
    {
        id: 'work',
        icon: '💼',
        label: 'Work',
        subtitle: 'Contributions & Economic Activity',
        color: '#f59e0b',
        bg: '#1a1200',
        milestones: [
            { id: 'w1', label: 'First Contract', icon: '📜' },
            { id: 'w2', label: 'Marketplace Active', icon: '🏪' },
            { id: 'w3', label: 'Job Completed', icon: '✅' },
            { id: 'w4', label: 'Value Created', icon: '💰' },
        ],
    },
    {
        id: 'family',
        icon: '👨‍👩‍👧‍👦',
        label: 'Family',
        subtitle: 'Relationships & Community',
        color: '#ec4899',
        bg: '#1a0010',
        milestones: [
            { id: 'f1', label: 'Peers Connected', icon: '🤝' },
            { id: 'f2', label: 'Mesh Network', icon: '🌐' },
            { id: 'f3', label: 'Community Joined', icon: '🏘️' },
            { id: 'f4', label: 'Collaboration', icon: '🤲' },
        ],
    },
    {
        id: 'retirement',
        icon: '🏖️',
        label: 'Retirement',
        subtitle: 'Wisdom & Legacy Mode',
        color: '#a855f7',
        bg: '#0f001a',
        milestones: [
            { id: 'r1', label: 'Sage Status', icon: '🧙' },
            { id: 'r2', label: 'Legacy Data', icon: '📦' },
            { id: 'r3', label: 'Mentorship', icon: '🎯' },
            { id: 'r4', label: 'Passive Mode', icon: '🌅' },
        ],
    },
    {
        id: 'inheritance',
        icon: '🔄',
        label: 'Inheritance',
        subtitle: 'Transfer & Continuation',
        color: '#22c55e',
        bg: '#001a04',
        milestones: [
            { id: 'i1', label: 'Data Export', icon: '💾' },
            { id: 'i2', label: 'Successor Designated', icon: '📋' },
            { id: 'i3', label: 'Assets Transferred', icon: '📤' },
            { id: 'i4', label: 'Continuity Plan', icon: '♻️' },
        ],
    },
];

export default function LifeJourney({ user }: LifeJourneyProps) {
    const [lifecycleData, setLifecycleData] = useState<LifecycleData | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeStage, setActiveStage] = useState<LifeStage | null>(null);
    const [completedMilestones, setCompletedMilestones] = useState<Record<string, boolean>>({});

    useEffect(() => {
        if (!user?.id) {
            setLoading(false);
            return;
        }
        lifecycleAPI.getLifecycle(user.id)
            .then((r) => {
                const responseData = (r as unknown as { data?: LifecycleData })?.data || {} as LifecycleData;
                setLifecycleData(responseData);
                // Derive completed milestones from backend data
                deriveMilestones(responseData);
            })
            .catch(() => { /* ignore */ })
            .finally(() => setLoading(false));
    }, [user]);

    function deriveMilestones(data: LifecycleData): void {
        const completed: Record<string, boolean> = {};
        const ac = data?.activity_count || 0;
        const layers = data?.active_layers || 0;
        const age = data?.age_days || 0;

        // Birth milestones
        if (data?.created_at) {
            completed.b1 = true;
            completed.b2 = !!data?.user_id;
            completed.b3 = (data?.mesh_nodes || 0) > 0 || age > 0;
            completed.b4 = true;
        }

        // Education milestones
        completed.e1 = ac > 0;
        completed.e2 = ac > 5;
        completed.e3 = layers > 1;
        completed.e4 = age > 7;

        // Work milestones
        completed.w1 = ac > 10;
        completed.w2 = layers > 2;
        completed.w3 = ac > 25;
        completed.w4 = age > 30;

        // Family milestones
        completed.f1 = (data?.mesh_nodes || 0) > 0;
        completed.f2 = (data?.mesh_nodes || 0) > 1;
        completed.f3 = (data?.connection_network_size || 0) > 0;

        // Retirement (longevity-based)
        completed.r1 = age > 60;
        completed.r2 = age > 90;
        completed.r3 = age > 120;

        // Inheritance
        completed.i1 = !!data?.privacy_score;
        completed.i2 = age > 180;

        setCompletedMilestones(completed);
    }

    function stageProgress(stage: LifeStage): number {
        const total = stage.milestones.length;
        const done = stage.milestones.filter(m => completedMilestones[m.id]).length;
        return total > 0 ? (done / total) * 100 : 0;
    }

    function totalProgress(): number {
        const all = LIFE_STAGES.flatMap(s => s.milestones);
        const total = all.length;
        const done = all.filter(m => completedMilestones[m.id]).length;
        return total > 0 ? Math.round((done / total) * 100) : 0;
    }

    const metrics: Metric[] = lifecycleData ? [
        { label: 'Universe Age', value: `${lifecycleData.age_days || 0} days`, icon: '⏳' },
        { label: 'Active Layers', value: `${lifecycleData.active_layers || 0} / ${lifecycleData.total_layers || 5}`, icon: '🧩' },
        { label: 'Activities', value: lifecycleData.activity_count || 0, icon: '📊' },
        { label: 'Mesh Nodes', value: lifecycleData.mesh_nodes || 0, icon: '🔗' },
        { label: 'Privacy Score', value: lifecycleData.privacy_score != null ? `${Math.round(lifecycleData.privacy_score * 100)}%` : '—', icon: '🛡️' },
        { label: 'Current State', value: lifecycleData.current_state || '—', icon: '📍' },
    ] : [];

    if (loading) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.loadingSpinner} />
                <p style={{ color: '#9ca3af', marginTop: 12 }}>Loading Life Journey...</p>
            </div>
        );
    }

    return (
        <div style={styles.page}>
            {/* Header */}
            <div style={styles.header}>
                <div>
                    <h1 style={styles.title}>🧬 Life Journey</h1>
                    <p style={styles.subtitle}>Your AsimNexus lifecycle — from birth to inheritance</p>
                </div>
                <div style={styles.progressRing}>
                    <svg width="56" height="56" viewBox="0 0 56 56">
                        <circle cx="28" cy="28" r="24" fill="none" stroke="#1f2937" strokeWidth="4" />
                        <circle cx="28" cy="28" r="24" fill="none" stroke="#7c3aed"
                            strokeWidth="4" strokeDasharray={`${(totalProgress() / 100) * 151} 151`}
                            strokeLinecap="round" transform="rotate(-90 28 28)" />
                    </svg>
                    <div style={styles.progressText}>{totalProgress()}%</div>
                </div>
            </div>

            {/* Metrics Bar */}
            {metrics.length > 0 && (
                <div style={styles.metricsBar}>
                    {metrics.map((m, i) => (
                        <div key={i} style={styles.metricCard}>
                            <span style={{ fontSize: 18 }}>{m.icon}</span>
                            <div>
                                <div style={styles.metricValue}>{typeof m.value === 'number' ? m.value.toLocaleString() : m.value}</div>
                                <div style={styles.metricLabel}>{m.label}</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Timeline */}
            <div style={styles.timeline}>
                {LIFE_STAGES.map((stage, idx) => {
                    const progress = stageProgress(stage);
                    const isActive = activeStage?.id === stage.id;
                    return (
                        <div key={stage.id} style={styles.stageWrapper}>
                            {/* Connector line */}
                            {idx > 0 && <div style={styles.connector} />}

                            {/* Stage Card */}
                            <div
                                onClick={() => setActiveStage(isActive ? null : stage)}
                                style={{
                                    ...styles.stageCard,
                                    borderColor: isActive ? stage.color : '#1f2937',
                                    background: isActive ? stage.bg : '#111827',
                                    boxShadow: isActive ? `0 0 24px ${stage.color}33` : 'none',
                                }}
                            >
                                {/* Stage Header */}
                                <div style={styles.stageHeader}>
                                    <span style={{ fontSize: 32 }}>{stage.icon}</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ ...styles.stageLabel, color: stage.color }}>{stage.label}</div>
                                        <div style={styles.stageSubtitle}>{stage.subtitle}</div>
                                    </div>
                                    <div style={styles.stageProgressBadge}>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: stage.color }}>
                                            {Math.round(progress)}%
                                        </div>
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div style={styles.progressBarBg}>
                                    <div style={{
                                        ...styles.progressBarFill,
                                        width: `${progress}%`,
                                        background: stage.color,
                                    }} />
                                </div>

                                {/* Milestones (shown when expanded) */}
                                {isActive && (
                                    <div style={styles.milestones}>
                                        {stage.milestones.map(m => {
                                            const done = !!completedMilestones[m.id];
                                            return (
                                                <div key={m.id} style={{
                                                    ...styles.milestone,
                                                    opacity: done ? 1 : 0.5,
                                                }}>
                                                    <span style={{ fontSize: 16 }}>{done ? '✅' : m.icon}</span>
                                                    <span style={{
                                                        flex: 1,
                                                        fontSize: 13,
                                                        color: done ? '#d1d5db' : '#6b7280',
                                                        textDecoration: done ? 'none' : 'none',
                                                    }}>
                                                        {m.label}
                                                    </span>
                                                    {done && <span style={{ color: '#10b981', fontSize: 12 }}>✓</span>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    page: {
        minHeight: '100vh',
        background: '#030712',
        color: '#f9fafb',
        fontFamily: 'Inter, sans-serif',
        padding: '24px 20px',
    },
    loadingContainer: {
        minHeight: '100vh',
        background: '#030712',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
    },
    loadingSpinner: {
        width: 40,
        height: 40,
        border: '3px solid #1f2937',
        borderTopColor: '#7c3aed',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
    },
    title: {
        margin: 0,
        fontSize: 26,
        fontWeight: 800,
        background: 'linear-gradient(90deg,#7c3aed,#06b6d4)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
    },
    subtitle: {
        margin: '4px 0 0',
        color: '#6b7280',
        fontSize: 13,
    },
    progressRing: {
        position: 'relative',
        width: 56,
        height: 56,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
    progressText: {
        position: 'absolute',
        fontSize: 12,
        fontWeight: 700,
        color: '#c084fc',
    },
    metricsBar: {
        display: 'flex',
        gap: 10,
        marginBottom: 28,
        flexWrap: 'wrap',
    },
    metricCard: {
        background: '#111827',
        border: '1px solid #1f2937',
        borderRadius: 10,
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        flex: '1 0 140px',
    },
    metricValue: {
        fontSize: 15,
        fontWeight: 700,
        color: '#f9fafb',
        lineHeight: 1.2,
    },
    metricLabel: {
        fontSize: 11,
        color: '#6b7280',
    },
    timeline: {
        display: 'flex',
        flexDirection: 'column',
        gap: 0,
        maxWidth: 700,
        margin: '0 auto',
    },
    stageWrapper: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative',
    },
    connector: {
        width: 2,
        height: 24,
        background: 'linear-gradient(180deg, #374151, #1f2937)',
    },
    stageCard: {
        width: '100%',
        border: '1px solid #1f2937',
        borderRadius: 14,
        padding: '16px 18px',
        cursor: 'pointer',
        transition: 'all 0.25s ease',
    },
    stageHeader: {
        display: 'flex',
        alignItems: 'center',
        gap: 14,
    },
    stageLabel: {
        fontSize: 17,
        fontWeight: 700,
    },
    stageSubtitle: {
        fontSize: 12,
        color: '#6b7280',
        marginTop: 1,
    },
    stageProgressBadge: {
        background: '#1f2937',
        borderRadius: 20,
        padding: '4px 10px',
    },
    progressBarBg: {
        marginTop: 12,
        height: 4,
        background: '#1f2937',
        borderRadius: 2,
        overflow: 'hidden',
    },
    progressBarFill: {
        height: '100%',
        borderRadius: 2,
        transition: 'width 0.6s ease',
    },
    milestones: {
        marginTop: 14,
        borderTop: '1px solid #1f2937',
        paddingTop: 12,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
    },
    milestone: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '4px 0',
    },
};
