/**
 * MirrorEvolutionHub — AsimNexus Mirror, Dreaming & Evolution Dashboard
 * ======================================================================
 * Integrated UI for the Digital Twin Mirror Module, Dreaming Engine,
 * and Evolution Engine — reflection, contradiction detection, dream cycles,
 * evolution suggestions, and consciousness monitoring.
 *
 * Reference:
 *   - routes/mirror.py — Mirror REST API (10 routes)
 *   - routes/dreaming.py — Dreaming REST API (9 routes)
 *   - routes/evolution.py — Evolution REST API (8 routes)
 *   - core/mirror/ — MirrorModule, ConsciousnessLayer, MirrorLoRA
 *   - core/dreaming/ — DreamingEngine, BugTriageEngine
 *   - core/evolution/ — EvolutionEngine
 */

import React, { useState, useEffect, useCallback } from 'react';

// ── Types ────────────────────────────────────────────────────

interface MirrorReflection {
    reflection_id: string;
    user_id: string;
    intent: string;
    contradictions: string[];
    balance_impact: number;
    response: string;
    timestamp: string;
}

interface ContradictionPattern {
    pattern: string;
    count: number;
    examples: string[];
}

interface EvolutionSuggestion {
    suggestion_id: string;
    title: string;
    description: string;
    category: string;
    status: string;
    priority: number;
    created_at: string;
}

interface EvolutionEvent {
    event_id: string;
    event_type: string;
    description: string;
    timestamp: string;
}

interface EvolutionStats {
    total_suggestions: number;
    approved: number;
    rejected: number;
    implemented: number;
    pending: number;
    categories: Record<string, number>;
}

interface DreamCycle {
    cycle_id: string;
    started_at: string;
    ended_at: string | null;
    messages_processed: number;
    lessons_extracted: number;
    memories_pruned: number;
    briefing: string;
    status: string;
}

interface DreamLesson {
    topic: string;
    summary: string;
    confidence: number;
    created_at: string;
}

interface DreamPatterns {
    patterns: Record<string, number>;
}

interface DreamStatus {
    is_running: boolean;
    total_cycles: number;
    last_cycle: string | null;
    uptime_hours: number;
    cycles: DreamCycle[];
}

interface ConsciousnessState {
    thoughts: Array<{
        thought_id: string;
        thought_type: string;
        content: string;
        timestamp: string;
    }>;
    principles: string[];
    thought_count: number;
}

interface BugTriageStats {
    total_reports: number;
    by_severity: Record<string, number>;
    by_status: Record<string, number>;
    recent_reports: Array<Record<string, unknown>>;
}

// ── API Helpers ──────────────────────────────────────────────

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function fetchJSON<T>(url: string): Promise<T> {
    const token = localStorage.getItem('asimnexus_token');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return res.json();
}

async function postJSON<T>(url: string, body: unknown): Promise<T> {
    const token = localStorage.getItem('asimnexus_token');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return res.json();
}

// ── Styling ──────────────────────────────────────────────────

const s = {
    container: {
        flex: 1,
        overflow: 'auto',
        padding: '20px 24px',
        color: '#e0e0e0',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    } as React.CSSProperties,
    header: {
        fontSize: '1.4rem',
        fontWeight: 700,
        marginBottom: 20,
        background: 'linear-gradient(135deg, #22d3ee, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
    } as React.CSSProperties,
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 16,
        marginBottom: 24,
    } as React.CSSProperties,
    card: {
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 12,
        padding: '16px 20px',
        border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(8px)',
    } as React.CSSProperties,
    cardTitle: {
        fontSize: '0.75rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        opacity: 0.5,
        marginBottom: 8,
    } as React.CSSProperties,
    statValue: {
        fontSize: '1.8rem',
        fontWeight: 700,
        color: '#22d3ee',
    } as React.CSSProperties,
    statLabel: {
        fontSize: '0.78rem',
        opacity: 0.6,
        marginTop: 2,
    } as React.CSSProperties,
    section: {
        marginBottom: 24,
    } as React.CSSProperties,
    sectionTitle: {
        fontSize: '1rem',
        fontWeight: 600,
        marginBottom: 12,
        opacity: 0.8,
    } as React.CSSProperties,
    table: {
        width: '100%',
        borderCollapse: 'collapse' as const,
        fontSize: '0.82rem',
    } as React.CSSProperties,
    th: {
        textAlign: 'left' as const,
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        fontWeight: 600,
        opacity: 0.5,
        fontSize: '0.72rem',
        textTransform: 'uppercase' as const,
        letterSpacing: '0.05em',
    } as React.CSSProperties,
    td: {
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
    } as React.CSSProperties,
    badge: (color: string) => ({
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 10,
        fontSize: '0.7rem',
        fontWeight: 600,
        background: `${color}22`,
        color: color,
        border: `1px solid ${color}44`,
    } as React.CSSProperties),
    btn: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(34,211,238,0.3)',
        background: 'rgba(34,211,238,0.1)',
        color: '#22d3ee',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    btnDanger: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(239,68,68,0.3)',
        background: 'rgba(239,68,68,0.1)',
        color: '#ef4444',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    btnSuccess: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(52,211,153,0.3)',
        background: 'rgba(52,211,153,0.1)',
        color: '#34d399',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    input: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        width: '100%',
        outline: 'none',
        boxSizing: 'border-box' as const,
    } as React.CSSProperties,
    textarea: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        width: '100%',
        outline: 'none',
        boxSizing: 'border-box' as const,
        minHeight: 60,
        fontFamily: 'monospace',
        resize: 'vertical' as const,
    } as React.CSSProperties,
    errorBox: {
        padding: 12,
        borderRadius: 8,
        background: 'rgba(239,68,68,0.1)',
        border: '1px solid rgba(239,68,68,0.2)',
        color: '#ef4444',
        fontSize: '0.82rem',
        marginBottom: 16,
    } as React.CSSProperties,
    successBox: {
        padding: 12,
        borderRadius: 8,
        background: 'rgba(52,211,153,0.1)',
        border: '1px solid rgba(52,211,153,0.2)',
        color: '#34d399',
        fontSize: '0.82rem',
        marginBottom: 16,
    } as React.CSSProperties,
    loadingText: {
        opacity: 0.4,
        fontSize: '0.85rem',
        fontStyle: 'italic',
    } as React.CSSProperties,
    formRow: {
        display: 'flex',
        gap: 12,
        marginBottom: 12,
        alignItems: 'flex-end',
        flexWrap: 'wrap' as const,
    } as React.CSSProperties,
    formGroup: {
        flex: 1,
        minWidth: 200,
    } as React.CSSProperties,
    label: {
        fontSize: '0.75rem',
        fontWeight: 600,
        opacity: 0.5,
        marginBottom: 4,
        display: 'block',
    } as React.CSSProperties,
    select: {
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 8,
        padding: '8px 12px',
        color: '#fff',
        fontSize: '0.82rem',
        width: '100%',
        outline: 'none',
        boxSizing: 'border-box' as const,
    } as React.CSSProperties,
};

// ── Color Maps ───────────────────────────────────────────────

const suggestionStatusColor: Record<string, string> = {
    pending: '#fbbf24',
    approved: '#34d399',
    rejected: '#ef4444',
    implemented: '#60a5fa',
};

const suggestionCategoryColor: Record<string, string> = {
    performance: '#34d399',
    security: '#ef4444',
    feature: '#a78bfa',
    refactor: '#fbbf24',
    docs: '#22d3ee',
    test: '#f472b6',
};

const thoughtTypeColor: Record<string, string> = {
    observation: '#22d3ee',
    reflection: '#a78bfa',
    intention: '#34d399',
    principle: '#fbbf24',
    question: '#60a5fa',
    insight: '#f472b6',
};

// ── Component ────────────────────────────────────────────────

const MirrorEvolutionHub: React.FC = () => {
    // ── State ──────────────────────────────────────────────
    const [userId, setUserId] = useState('default');
    const [reflections, setReflections] = useState<MirrorReflection[]>([]);
    const [contradictions, setContradictions] = useState<ContradictionPattern[]>([]);
    const [contradictionRate, setContradictionRate] = useState(0);
    const [requiresReview, setRequiresReview] = useState(false);
    const [dailyReport, setDailyReport] = useState<Record<string, unknown> | null>(null);
    const [consciousness, setConsciousness] = useState<ConsciousnessState | null>(null);
    const [evoSuggestions, setEvoSuggestions] = useState<EvolutionSuggestion[]>([]);
    const [evoEvents, setEvoEvents] = useState<EvolutionEvent[]>([]);
    const [evoStats, setEvoStats] = useState<EvolutionStats | null>(null);
    const [dreamStatus, setDreamStatus] = useState<DreamStatus | null>(null);
    const [dreamLessons, setDreamLessons] = useState<DreamLesson[]>([]);
    const [dreamPatterns, setDreamPatterns] = useState<DreamPatterns | null>(null);
    const [bugTriageStats, setBugTriageStats] = useState<BugTriageStats | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'mirror' | 'consciousness' | 'dreaming' | 'evolution'>('overview');

    // ── Reflect Form ───────────────────────────────────────
    const [reflectIntent, setReflectIntent] = useState('');
    const [reflectDetails, setReflectDetails] = useState('{}');

    // ── Thought Form ───────────────────────────────────────
    const [thoughtType, setThoughtType] = useState('observation');
    const [thoughtContent, setThoughtContent] = useState('');

    // ── Data Fetching ──────────────────────────────────────

    const fetchAll = useCallback(async () => {
        try {
            const [
                reflectionsRes, contradictionsRes, reportRes,
                evoSuggestionsRes, evoEventsRes, evoStatsRes,
                dreamStatusRes, dreamLessonsRes, dreamPatternsRes,
                consciousnessRes, bugTriageRes,
            ] = await Promise.all([
                fetchJSON<{ status: string; data: { reflections: MirrorReflection[] } }>(
                    `${API_BASE}/api/mirror/reflections?user_id=${userId}&limit=20`
                ),
                fetchJSON<{ status: string; data: { patterns: ContradictionPattern[]; contradiction_rate: number; requires_review: boolean } }>(
                    `${API_BASE}/api/mirror/contradictions?user_id=${userId}`
                ),
                fetchJSON<{ status: string; data: Record<string, unknown> }>(
                    `${API_BASE}/api/mirror/daily-report?user_id=${userId}`
                ),
                fetchJSON<{ status: string; data: { suggestions: EvolutionSuggestion[] } }>(
                    `${API_BASE}/api/evolution/suggestions?limit=20`
                ),
                fetchJSON<{ status: string; data: { events: EvolutionEvent[] } }>(
                    `${API_BASE}/api/evolution/events?limit=20`
                ),
                fetchJSON<{ status: string; data: EvolutionStats }>(
                    `${API_BASE}/api/evolution/stats`
                ),
                fetchJSON<{ status: string; data: DreamStatus }>(
                    `${API_BASE}/api/dreaming/status`
                ),
                fetchJSON<{ status: string; data: { lessons: DreamLesson[] } }>(
                    `${API_BASE}/api/dreaming/lessons?limit=10`
                ),
                fetchJSON<{ status: string; data: DreamPatterns }>(
                    `${API_BASE}/api/dreaming/patterns`
                ),
                fetchJSON<{ status: string; data: ConsciousnessState }>(
                    `${API_BASE}/api/mirror/consciousness?user_id=${userId}`
                ),
                fetchJSON<{ status: string; data: BugTriageStats }>(
                    `${API_BASE}/api/dreaming/bug-triage/stats`
                ),
            ]);

            setReflections(reflectionsRes.data?.reflections || []);
            setContradictions(contradictionsRes.data?.patterns || []);
            setContradictionRate(contradictionsRes.data?.contradiction_rate || 0);
            setRequiresReview(contradictionsRes.data?.requires_review || false);
            setDailyReport(reportRes.data || null);
            setEvoSuggestions(evoSuggestionsRes.data?.suggestions || []);
            setEvoEvents(evoEventsRes.data?.events || []);
            setEvoStats(evoStatsRes.data || null);
            setDreamStatus(dreamStatusRes.data || null);
            setDreamLessons(dreamLessonsRes.data?.lessons || []);
            setDreamPatterns(dreamPatternsRes.data || null);
            setConsciousness(consciousnessRes.data || null);
            setBugTriageStats(bugTriageRes.data || null);
            setError(null);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to fetch data';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [userId]);

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 30000);
        return () => clearInterval(interval);
    }, [fetchAll]);

    // ── Actions ────────────────────────────────────────────

    const handleReflect = async () => {
        if (!reflectIntent) {
            setError('Intent is required');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            const res = await postJSON<{ status: string; data: MirrorReflection }>(
                `${API_BASE}/api/mirror/reflect`,
                {
                    user_id: userId,
                    action: {
                        intent: reflectIntent,
                        details: JSON.parse(reflectDetails || '{}'),
                    },
                }
            );
            setSuccess(`Reflection created: ${res.data.reflection_id}`);
            setReflectIntent('');
            setReflectDetails('{}');
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Reflection failed';
            setError(msg);
        }
    };

    const handleAddThought = async () => {
        if (!thoughtContent) {
            setError('Content is required');
            return;
        }
        setError(null);
        setSuccess(null);
        try {
            await postJSON(
                `${API_BASE}/api/mirror/consciousness/thought`,
                {
                    user_id: userId,
                    thought_type: thoughtType,
                    content: thoughtContent,
                }
            );
            setSuccess('Thought added to consciousness');
            setThoughtContent('');
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to add thought';
            setError(msg);
        }
    };

    const handleNightlyDream = async () => {
        setError(null);
        setSuccess(null);
        try {
            const res = await postJSON<{ status: string; data: { count: number } }>(
                `${API_BASE}/api/mirror/nightly-dream`,
                { user_id: userId }
            );
            setSuccess(`Nightly dream complete: ${res.data.count} suggestions generated`);
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Nightly dream failed';
            setError(msg);
        }
    };

    const handleTriggerDreamCycle = async () => {
        setError(null);
        setSuccess(null);
        try {
            await postJSON(`${API_BASE}/api/dreaming/cycle/trigger`, {});
            setSuccess('Dream cycle triggered');
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to trigger dream cycle';
            setError(msg);
        }
    };

    const handleApproveSuggestion = async (suggestionId: string) => {
        setError(null);
        setSuccess(null);
        try {
            await postJSON(
                `${API_BASE}/api/evolution/suggestions/${suggestionId}/approve`,
                {}
            );
            setSuccess(`Suggestion ${suggestionId} approved`);
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to approve';
            setError(msg);
        }
    };

    const handleRejectSuggestion = async (suggestionId: string) => {
        setError(null);
        setSuccess(null);
        try {
            await postJSON(
                `${API_BASE}/api/evolution/suggestions/${suggestionId}/reject`,
                { reason: 'Rejected via dashboard' }
            );
            setSuccess(`Suggestion ${suggestionId} rejected`);
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to reject';
            setError(msg);
        }
    };

    const handleAutoFineTune = async () => {
        setError(null);
        setSuccess(null);
        try {
            const res = await postJSON<{ status: string; data: Record<string, unknown> }>(
                `${API_BASE}/api/mirror/auto-fine-tune`,
                { user_id: userId }
            );
            setSuccess(`Fine-tuning complete: ${JSON.stringify(res.data)}`);
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Fine-tuning failed';
            setError(msg);
        }
    };

    // ── Render Helpers ─────────────────────────────────────

    const renderStatCard = (title: string, value: string | number, label: string, color = '#22d3ee') => (
        <div style={s.card}>
            <div style={s.cardTitle}>{title}</div>
            <div style={{ ...s.statValue, color }}>{value}</div>
            <div style={s.statLabel}>{label}</div>
        </div>
    );

    // ── Overview Tab ───────────────────────────────────────

    const renderOverview = () => (
        <>
            <div style={s.grid}>
                {renderStatCard('Reflections', reflections.length, 'Recent mirror reflections', '#22d3ee')}
                {renderStatCard('Contradiction Rate', `${(contradictionRate * 100).toFixed(0)}%`, 'Current rate', contradictionRate > 0.5 ? '#ef4444' : '#34d399')}
                {renderStatCard('Evolution Suggestions', evoSuggestions.length, 'Total pending/active', '#a78bfa')}
                {renderStatCard('Dream Cycles', dreamStatus?.total_cycles ?? 0, 'Total cycles run', '#f472b6')}
                {renderStatCard('Dream Lessons', dreamLessons.length, 'Recent lessons', '#60a5fa')}
                {renderStatCard('Consciousness', consciousness?.thought_count ?? 0, 'Thoughts recorded', '#fbbf24')}
            </div>

            {/* Quick Actions */}
            <div style={s.section}>
                <div style={s.sectionTitle}>Quick Actions</div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <button style={s.btn} onClick={() => setActiveTab('mirror')}>
                        🪞 Mirror Actions
                    </button>
                    <button style={s.btn} onClick={() => setActiveTab('consciousness')}>
                        🧠 Consciousness
                    </button>
                    <button style={s.btn} onClick={() => setActiveTab('dreaming')}>
                        💭 Dreaming Engine
                    </button>
                    <button style={s.btn} onClick={() => setActiveTab('evolution')}>
                        🧬 Evolution Engine
                    </button>
                </div>
            </div>

            {/* User ID Input */}
            <div style={s.card}>
                <div style={s.cardTitle}>User Configuration</div>
                <div style={s.formRow}>
                    <div style={s.formGroup}>
                        <label style={s.label}>User ID</label>
                        <input
                            style={s.input}
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            placeholder="default"
                        />
                    </div>
                </div>
            </div>

            {/* Daily Report Summary */}
            {dailyReport && (
                <div style={s.card}>
                    <div style={s.cardTitle}>Daily Report Summary</div>
                    <pre style={{ fontSize: '0.78rem', opacity: 0.7, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {JSON.stringify(dailyReport, null, 2).slice(0, 1000)}
                    </pre>
                </div>
            )}
        </>
    );

    // ── Mirror Tab ─────────────────────────────────────────

    const renderMirror = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Mirror Module — Digital Twin Reflection</div>

            {/* Reflect Form */}
            <div style={s.card}>
                <div style={s.cardTitle}>New Reflection</div>
                <div style={s.formRow}>
                    <div style={s.formGroup}>
                        <label style={s.label}>Intent</label>
                        <input
                            style={s.input}
                            placeholder="e.g., submit_tax_return"
                            value={reflectIntent}
                            onChange={(e) => setReflectIntent(e.target.value)}
                        />
                    </div>
                </div>
                <div style={s.formRow}>
                    <div style={s.formGroup}>
                        <label style={s.label}>Details (JSON)</label>
                        <textarea
                            style={s.textarea}
                            placeholder='{"amount": 50000, "currency": "NPR"}'
                            value={reflectDetails}
                            onChange={(e) => setReflectDetails(e.target.value)}
                        />
                    </div>
                </div>
                <button style={s.btn} onClick={handleReflect}>
                    🪞 Reflect
                </button>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
                <button style={s.btn} onClick={handleNightlyDream}>
                    🌙 Run Nightly Dream
                </button>
                <button style={s.btn} onClick={handleAutoFineTune}>
                    🎯 Auto Fine-Tune
                </button>
            </div>

            {/* Contradictions */}
            {contradictions.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>
                        Contradiction Patterns
                        {requiresReview && <span style={s.badge('#ef4444')}>REQUIRES REVIEW</span>}
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Pattern</th>
                                    <th style={s.th}>Count</th>
                                    <th style={s.th}>Examples</th>
                                </tr>
                            </thead>
                            <tbody>
                                {contradictions.map((c, i) => (
                                    <tr key={i}>
                                        <td style={s.td}>{c.pattern}</td>
                                        <td style={s.td}>{c.count}</td>
                                        <td style={{ ...s.td, opacity: 0.6, fontSize: '0.75rem' }}>
                                            {(c.examples || []).slice(0, 2).join(', ')}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Recent Reflections */}
            {reflections.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>Recent Reflections ({reflections.length})</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>ID</th>
                                    <th style={s.th}>Intent</th>
                                    <th style={s.th}>Contradictions</th>
                                    <th style={s.th}>Balance</th>
                                    <th style={s.th}>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reflections.map((r) => (
                                    <tr key={r.reflection_id}>
                                        <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5 }}>
                                            {r.reflection_id}
                                        </td>
                                        <td style={s.td}>{r.intent}</td>
                                        <td style={s.td}>
                                            {r.contradictions?.length > 0 ? (
                                                <span style={s.badge('#ef4444')}>{r.contradictions.length}</span>
                                            ) : (
                                                <span style={{ opacity: 0.3 }}>—</span>
                                            )}
                                        </td>
                                        <td style={s.td}>
                                            <span style={{
                                                color: r.balance_impact >= 0 ? '#34d399' : '#ef4444',
                                                fontWeight: 600,
                                            }}>
                                                {r.balance_impact >= 0 ? '+' : ''}{r.balance_impact?.toFixed(2)}
                                            </span>
                                        </td>
                                        <td style={{ ...s.td, opacity: 0.4, fontSize: '0.72rem' }}>
                                            {r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );

    // ── Consciousness Tab ──────────────────────────────────

    const renderConsciousness = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Consciousness Layer</div>

            {/* Add Thought */}
            <div style={s.card}>
                <div style={s.cardTitle}>Add Thought</div>
                <div style={s.formRow}>
                    <div style={s.formGroup}>
                        <label style={s.label}>Thought Type</label>
                        <select
                            style={s.select}
                            value={thoughtType}
                            onChange={(e) => setThoughtType(e.target.value)}
                        >
                            {Object.keys(thoughtTypeColor).map((t) => (
                                <option key={t} value={t}>{t}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <div style={s.formRow}>
                    <div style={s.formGroup}>
                        <label style={s.label}>Content</label>
                        <textarea
                            style={s.textarea}
                            placeholder="Enter thought content..."
                            value={thoughtContent}
                            onChange={(e) => setThoughtContent(e.target.value)}
                        />
                    </div>
                </div>
                <button style={s.btn} onClick={handleAddThought}>
                    ➕ Add Thought
                </button>
            </div>

            {/* Principles */}
            {consciousness?.principles && consciousness.principles.length > 0 && (
                <div style={{ ...s.card, marginTop: 16 }}>
                    <div style={s.cardTitle}>Guiding Principles</div>
                    <ul style={{ margin: 0, paddingLeft: 20, opacity: 0.7, fontSize: '0.82rem' }}>
                        {consciousness.principles.map((p, i) => (
                            <li key={i} style={{ marginBottom: 4 }}>{p}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Thoughts */}
            {consciousness?.thoughts && consciousness.thoughts.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>Thoughts ({consciousness.thought_count})</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Type</th>
                                    <th style={s.th}>Content</th>
                                    <th style={s.th}>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {consciousness.thoughts.map((t) => (
                                    <tr key={t.thought_id}>
                                        <td style={s.td}>
                                            <span style={s.badge(thoughtTypeColor[t.thought_type] || '#94a3b8')}>
                                                {t.thought_type}
                                            </span>
                                        </td>
                                        <td style={{ ...s.td, maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {t.content}
                                        </td>
                                        <td style={{ ...s.td, opacity: 0.4, fontSize: '0.72rem' }}>
                                            {t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );

    // ── Dreaming Tab ───────────────────────────────────────

    const renderDreaming = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Dreaming Engine — Memory Consolidation</div>

            {/* Status & Actions */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                <button style={s.btn} onClick={handleTriggerDreamCycle}>
                    💤 Trigger Dream Cycle
                </button>
            </div>

            {/* Dream Status */}
            {dreamStatus && (
                <div style={s.card}>
                    <div style={s.cardTitle}>Engine Status</div>
                    <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Running</span>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: dreamStatus.is_running ? '#34d399' : '#94a3b8' }}>
                                {dreamStatus.is_running ? 'Yes' : 'No'}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Total Cycles</span>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f472b6' }}>
                                {dreamStatus.total_cycles}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Uptime</span>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#22d3ee' }}>
                                {dreamStatus.uptime_hours?.toFixed(1) || '0'}h
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Patterns */}
            {dreamPatterns?.patterns && Object.keys(dreamPatterns.patterns).length > 0 && (
                <div style={{ ...s.card, marginTop: 16 }}>
                    <div style={s.cardTitle}>Detected Patterns</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {Object.entries(dreamPatterns.patterns).map(([key, val]) => (
                            <span key={key} style={s.badge                            <span key={key} style={s.badge('#a78bfa')}>
                                {key}: {(val as number).toFixed(2)}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Lessons */}
            {dreamLessons.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>Recent Lessons ({dreamLessons.length})</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Topic</th>
                                    <th style={s.th}>Summary</th>
                                    <th style={s.th}>Confidence</th>
                                    <th style={s.th}>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {dreamLessons.map((lesson, i) => (
                                    <tr key={i}>
                                        <td style={s.td}>
                                            <span style={s.badge('#60a5fa')}>{lesson.topic}</span>
                                        </td>
                                        <td style={{ ...s.td, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {lesson.summary}
                                        </td>
                                        <td style={s.td}>
                                            <span style={{
                                                color: lesson.confidence > 0.7 ? '#34d399' : lesson.confidence > 0.4 ? '#fbbf24' : '#ef4444',
                                                fontWeight: 600,
                                            }}>
                                                {(lesson.confidence * 100).toFixed(0)}%
                                            </span>
                                        </td>
                                        <td style={{ ...s.td, opacity: 0.4, fontSize: '0.72rem' }}>
                                            {lesson.created_at ? new Date(lesson.created_at).toLocaleString() : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Bug Triage Stats */}
            {bugTriageStats && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>Bug Triage</div>
                    <div style={s.grid}>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Total Reports</div>
                            <div style={{ ...s.statValue, color: '#f472b6' }}>{bugTriageStats.total_reports}</div>
                        </div>
                        {Object.entries(bugTriageStats.by_severity || {}).map(([sev, count]) => (
                            <div key={sev} style={s.card}>
                                <div style={s.cardTitle}>{sev}</div>
                                <div style={{ ...s.statValue, color: sev === 'critical' ? '#ef4444' : sev === 'high' ? '#fbbf24' : '#22d3ee', fontSize: '1.2rem' }}>
                                    {count}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    // ── Evolution Tab ──────────────────────────────────────

    const renderEvolution = () => (
        <div style={s.section}>
            <div style={s.sectionTitle}>Evolution Engine — Autonomous Code Evolution</div>

            {/* Stats Cards */}
            {evoStats && (
                <div style={s.grid}>
                    <div style={s.card}>
                        <div style={s.cardTitle}>Total</div>
                        <div style={{ ...s.statValue, color: '#a78bfa' }}>{evoStats.total_suggestions}</div>
                    </div>
                    <div style={s.card}>
                        <div style={s.cardTitle}>Approved</div>
                        <div style={{ ...s.statValue, color: '#34d399' }}>{evoStats.approved}</div>
                    </div>
                    <div style={s.card}>
                        <div style={s.cardTitle}>Rejected</div>
                        <div style={{ ...s.statValue, color: '#ef4444' }}>{evoStats.rejected}</div>
                    </div>
                    <div style={s.card}>
                        <div style={s.cardTitle}>Implemented</div>
                        <div style={{ ...s.statValue, color: '#60a5fa' }}>{evoStats.implemented}</div>
                    </div>
                    <div style={s.card}>
                        <div style={s.cardTitle}>Pending</div>
                        <div style={{ ...s.statValue, color: '#fbbf24' }}>{evoStats.pending}</div>
                    </div>
                </div>
            )}

            {/* Category Breakdown */}
            {evoStats?.categories && Object.keys(evoStats.categories).length > 0 && (
                <div style={{ ...s.card, marginBottom: 16 }}>
                    <div style={s.cardTitle}>Categories</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {Object.entries(evoStats.categories).map(([cat, count]) => (
                            <span key={cat} style={s.badge(suggestionCategoryColor[cat] || '#94a3b8')}>
                                {cat}: {count}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Suggestions Table */}
            {evoSuggestions.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>Suggestions ({evoSuggestions.length})</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Title</th>
                                    <th style={s.th}>Category</th>
                                    <th style={s.th}>Status</th>
                                    <th style={s.th}>Priority</th>
                                    <th style={s.th}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {evoSuggestions.map((sug) => (
                                    <tr key={sug.suggestion_id}>
                                        <td style={{ ...s.td, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {sug.title}
                                        </td>
                                        <td style={s.td}>
                                            <span style={s.badge(suggestionCategoryColor[sug.category] || '#94a3b8')}>
                                                {sug.category}
                                            </span>
                                        </td>
                                        <td style={s.td}>
                                            <span style={s.badge(suggestionStatusColor[sug.status] || '#94a3b8')}>
                                                {sug.status}
                                            </span>
                                        </td>
                                        <td style={s.td}>
                                            <span style={{ fontWeight: 600, color: sug.priority > 7 ? '#ef4444' : sug.priority > 4 ? '#fbbf24' : '#94a3b8' }}>
                                                {sug.priority}
                                            </span>
                                        </td>
                                        <td style={s.td}>
                                            {sug.status === 'pending' && (
                                                <div style={{ display: 'flex', gap: 6 }}>
                                                    <button
                                                        style={{ ...s.btnSuccess, padding: '4px 10px', fontSize: '0.72rem' }}
                                                        onClick={() => handleApproveSuggestion(sug.suggestion_id)}
                                                    >
                                                        ✓ Approve
                                                    </button>
                                                    <button
                                                        style={{ ...s.btnDanger, padding: '4px 10px', fontSize: '0.72rem' }}
                                                        onClick={() => handleRejectSuggestion(sug.suggestion_id)}
                                                    >
                                                        ✗ Reject
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Events Table */}
            {evoEvents.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    <div style={s.sectionTitle}>Recent Events ({evoEvents.length})</div>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={s.table}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Type</th>
                                    <th style={s.th}>Description</th>
                                    <th style={s.th}>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {evoEvents.map((evt) => (
                                    <tr key={evt.event_id}>
                                        <td style={s.td}>
                                            <span style={s.badge('#a78bfa')}>{evt.event_type}</span>
                                        </td>
                                        <td style={{ ...s.td, maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {evt.description}
                                        </td>
                                        <td style={{ ...s.td, opacity: 0.4, fontSize: '0.72rem' }}>
                                            {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* No Data */}
            {evoSuggestions.length === 0 && evoEvents.length === 0 && (
                <div style={{ ...s.card, opacity: 0.5, textAlign: 'center', padding: 40 }}>
                    No evolution data available yet. Run a nightly dream or trigger a dream cycle to generate suggestions.
                </div>
            )}
        </div>
    );

    // ── Main Render ────────────────────────────────────────

    const tabs: { key: typeof activeTab; label: string; icon: string }[] = [
        { key: 'overview', label: 'Overview', icon: '📊' },
        { key: 'mirror', label: 'Mirror', icon: '🪞' },
        { key: 'consciousness', label: 'Consciousness', icon: '🧠' },
        { key: 'dreaming', label: 'Dreaming', icon: '💭' },
        { key: 'evolution', label: 'Evolution', icon: '🧬' },
    ];

    return (
        <div style={s.container}>
            {/* Header */}
            <div style={s.header}>
                🪞 Mirror · 💭 Dreaming · 🧬 Evolution
            </div>

            {/* Messages */}
            {error && <div style={s.errorBox}>{error}</div>}
            {success && <div style={s.successBox}>{success}</div>}

            {/* Loading */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: 60 }}>
                    <div style={s.loadingText}>Loading Mirror, Dreaming & Evolution data...</div>
                </div>
            ) : (
                <>
                    {/* Tab Navigation */}
                    <div style={{
                        display: 'flex',
                        gap: 4,
                        marginBottom: 20,
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                        paddingBottom: 0,
                    }}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key)}
                                style={{
                                    padding: '10px 18px',
                                    border: 'none',
                                    background: activeTab === tab.key
                                        ? 'rgba(34,211,238,0.12)'
                                        : 'transparent',
                                    color: activeTab === tab.key ? '#22d3ee' : 'rgba(255,255,255,0.5)',
                                    cursor: 'pointer',
                                    fontSize: '0.85rem',
                                    fontWeight: activeTab === tab.key ? 600 : 400,
                                    borderBottom: activeTab === tab.key
                                        ? '2px solid #22d3ee'
                                        : '2px solid transparent',
                                    transition: 'all 0.15s ease',
                                    borderRadius: '8px 8px 0 0',
                                }}
                            >
                                {tab.icon} {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    {activeTab === 'overview' && renderOverview()}
                    {activeTab === 'mirror' && renderMirror()}
                    {activeTab === 'consciousness' && renderConsciousness()}
                    {activeTab === 'dreaming' && renderDreaming()}
                    {activeTab === 'evolution' && renderEvolution()}
                </>
            )}
        </div>
    );
};

export default MirrorEvolutionHub;
