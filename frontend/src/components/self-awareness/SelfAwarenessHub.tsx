/**
 * SelfAwarenessHub — AsimNexus Self-Awareness Dashboard
 * ======================================================
 * Displays real-time self-knowledge, codebase scan results, build actions,
 * issues, evolution suggestions, health status, gap analysis, and build cycles.
 * Auto-refreshes every 30 seconds.
 */

import React, { useState, useEffect, useCallback } from 'react';

// ── Types ────────────────────────────────────────────────────

interface KnowledgeSummary {
    total_modules: number;
    total_packages: number;
    total_classes: number;
    total_functions: number;
    total_routes: number;
    total_lines: number;
    total_issues: number;
    open_issues: number;
    last_scan: string | null;
    last_updated: string | null;
}

interface ModuleInfo {
    package: string;
    filepath: string;
    classes: number;
    functions: number;
    lines: number;
    has_routes: boolean;
    errors: string[];
}

interface RouteInfo {
    method: string;
    path: string;
    handler: string;
    module: string;
}

interface IssueRecord {
    issue_id: string;
    module: string;
    issue_type: string;
    description: string;
    lineno: number;
    severity: string;
    status: string;
    timestamp: string;
}

interface BuildAction {
    action_id: string;
    action_type: string;
    target_file: string;
    description: string;
    status: string;
    timestamp: string;
}

interface BuildStats {
    total_actions: number;
    success_rate: number;
    actions_by_type: Record<string, number>;
}

// ── Health Types ─────────────────────────────────────────────

interface ComponentHealth {
    status: string;
    [key: string]: unknown;
}

interface HealthData {
    status: string;
    components: Record<string, ComponentHealth>;
}

// ── Gap Types ────────────────────────────────────────────────

interface GapData {
    gap_id: string;
    category: string;
    description: string;
    priority_score: number;
    module: string;
    suggestion: string;
    severity: string;
}

interface GapsResponse {
    gaps: GapData[];
    total_found: number;
    returned: number;
    categories: Record<string, number>;
    summary: Record<string, unknown>;
}

// ── Build Cycle Types ────────────────────────────────────────

interface BuildCycleData {
    cycle_id: string;
    status: string;
    actions_count: number;
    tests_passed: number;
    tests_failed: number;
    deployed: boolean;
    deploy_target: string;
    deploy_url: string;
    smoke_tests_passed: number;
    smoke_tests_total: number;
    started_at: string;
    completed_at: string;
    errors: string[];
}

interface CycleStatusData {
    is_running: boolean;
    last_cycle_id: string;
    last_cycle_status: string;
    total_cycles: number;
    uptime_hours: number;
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

// ── Styling Helpers ──────────────────────────────────────────

const styles = {
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
        background: 'linear-gradient(135deg, #667eea, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
    } as React.CSSProperties,
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
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
        color: '#a78bfa',
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
    button: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(102,126,234,0.3)',
        background: 'rgba(102,126,234,0.1)',
        color: '#a78bfa',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
    } as React.CSSProperties,
    buttonDanger: {
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid rgba(239,68,68,0.3)',
        background: 'rgba(239,68,68,0.1)',
        color: '#ef4444',
        cursor: 'pointer',
        fontSize: '0.82rem',
        fontWeight: 500,
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
    loadingText: {
        opacity: 0.4,
        fontSize: '0.85rem',
        fontStyle: 'italic',
    } as React.CSSProperties,
    progressBar: (percent: number, color: string) => ({
        height: 6,
        borderRadius: 3,
        background: 'rgba(255,255,255,0.06)',
        overflow: 'hidden' as const,
        marginTop: 4,
        width: '100%',
    } as React.CSSProperties),
    progressFill: (percent: number, color: string) => ({
        height: '100%',
        width: `${Math.min(100, Math.max(0, percent))}%`,
        borderRadius: 3,
        background: color,
        transition: 'width 0.5s ease',
    } as React.CSSProperties),
};

// ── Severity Color Map ───────────────────────────────────────

const severityColor: Record<string, string> = {
    critical: '#ef4444',
    error: '#f97316',
    warning: '#eab308',
    info: '#22d3ee',
};

const issueTypeColor: Record<string, string> = {
    bug: '#ef4444',
    bare_except: '#f97316',
    fixme: '#eab308',
    todo: '#22d3ee',
    hack: '#a78bfa',
    optimize: '#34d399',
    improvement: '#60a5fa',
    warning: '#f97316',
};

const gapCategoryColor: Record<string, string> = {
    test_coverage: '#ef4444',
    orphaned_module: '#f97316',
    missing_export: '#eab308',
    naming_inconsistency: '#22d3ee',
    duplicate_functionality: '#a78bfa',
    missing_docstring: '#34d399',
    bare_except: '#f97316',
    todo: '#22d3ee',
    knowledge_issue: '#60a5fa',
    missing_init_export: '#f472b6',
    missing_api_route: '#fbbf24',
    missing_frontend_component: '#94a3b8',
};

const healthStatusColor: Record<string, string> = {
    healthy: '#34d399',
    degraded: '#fbbf24',
    unhealthy: '#ef4444',
};

// ── Component ────────────────────────────────────────────────

const SelfAwarenessHub: React.FC = () => {
    const [summary, setSummary] = useState<KnowledgeSummary | null>(null);
    const [modules, setModules] = useState<ModuleInfo[]>([]);
    const [routes, setRoutes] = useState<RouteInfo[]>([]);
    const [issues, setIssues] = useState<IssueRecord[]>([]);
    const [buildActions, setBuildActions] = useState<BuildAction[]>([]);
    const [buildStats, setBuildStats] = useState<BuildStats | null>(null);
    const [health, setHealth] = useState<HealthData | null>(null);
    const [gaps, setGaps] = useState<GapsResponse | null>(null);
    const [buildCycles, setBuildCycles] = useState<BuildCycleData[]>([]);
    const [cycleStatus, setCycleStatus] = useState<CycleStatusData | null>(null);
    const [scanning, setScanning] = useState(false);
    const [runningCycle, setRunningCycle] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'modules' | 'routes' | 'issues' | 'build' | 'health' | 'gaps' | 'cycles'>('overview');

    // ── Data Fetching ────────────────────────────────────────

    const fetchAll = useCallback(async () => {
        try {
            const [
                summaryData, modulesData, routesData, issuesData,
                historyData, statsData, healthData, gapsData,
                cyclesData, cycleStatusData,
            ] = await Promise.all([
                fetchJSON<{ status: string; data: KnowledgeSummary }>(
                    `${API_BASE}/api/self/knowledge/summary`
                ),
                fetchJSON<{ status: string; data: ModuleInfo[] }>(
                    `${API_BASE}/api/self/knowledge/modules`
                ),
                fetchJSON<{ status: string; data: RouteInfo[] }>(
                    `${API_BASE}/api/self/knowledge/routes`
                ),
                fetchJSON<{ status: string; data: IssueRecord[] }>(
                    `${API_BASE}/api/self/knowledge/issues`
                ),
                fetchJSON<{ status: string; data: BuildAction[] }>(
                    `${API_BASE}/api/self/build/history`
                ),
                fetchJSON<{ status: string; data: BuildStats }>(
                    `${API_BASE}/api/self/build/stats`
                ),
                fetchJSON<{ status: string; data: HealthData }>(
                    `${API_BASE}/api/self/health`
                ),
                fetchJSON<{ status: string; data: GapsResponse }>(
                    `${API_BASE}/api/self/gaps?max_gaps=20`
                ),
                fetchJSON<{ status: string; data: BuildCycleData[] }>(
                    `${API_BASE}/api/self/build/cycles?limit=10`
                ),
                fetchJSON<{ status: string; data: CycleStatusData }>(
                    `${API_BASE}/api/self/build/cycle/status`
                ),
            ]);
            setSummary(summaryData.data || summaryData as unknown as KnowledgeSummary);
            setModules(modulesData.data || []);
            setRoutes(routesData.data || []);
            setIssues(issuesData.data || []);
            setBuildActions(historyData.data || []);
            setBuildStats(statsData.data || null);
            setHealth(healthData.data || null);
            setGaps(gapsData.data || null);
            setBuildCycles(cyclesData.data || []);
            setCycleStatus(cycleStatusData.data || null);
            setError(null);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Failed to fetch self-awareness data';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 30000); // auto-refresh every 30s
        return () => clearInterval(interval);
    }, [fetchAll]);

    // ── Trigger Scan ─────────────────────────────────────────

    const handleScan = async () => {
        setScanning(true);
        setError(null);
        try {
            await postJSON(`${API_BASE}/api/self/scan`, {});
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Scan failed';
            setError(msg);
        } finally {
            setScanning(false);
        }
    };

    // ── Trigger Build Cycle ──────────────────────────────────

    const handleRunCycle = async () => {
        setRunningCycle(true);
        setError(null);
        try {
            await postJSON(`${API_BASE}/api/self/build/run-cycle`, {});
            await fetchAll();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Build cycle failed';
            setError(msg);
        } finally {
            setRunningCycle(false);
        }
    };

    // ── Render Helpers ───────────────────────────────────────

    const renderStatCard = (title: string, value: string | number, label: string, color = '#a78bfa') => (
        <div style={styles.card}>
            <div style={styles.cardTitle}>{title}</div>
            <div style={{ ...styles.statValue, color }}>{value}</div>
            <div style={styles.statLabel}>{label}</div>
        </div>
    );

    const renderOverview = () => (
        <>
            {/* Summary Stats */}
            <div style={styles.grid}>
                {renderStatCard('Modules', summary?.total_modules ?? '—', 'Known Python modules', '#60a5fa')}
                {renderStatCard('Routes', summary?.total_routes ?? '—', 'API endpoints', '#34d399')}
                {renderStatCard('Classes', summary?.total_classes ?? '—', 'Total classes', '#a78bfa')}
                {renderStatCard('Functions', summary?.total_functions ?? '—', 'Total functions', '#f472b6')}
                {renderStatCard('Lines of Code', summary?.total_lines ?? '—', 'Total lines', '#22d3ee')}
                {renderStatCard('Issues', summary?.total_issues ?? '—', `${summary?.open_issues ?? 0} open`, summary && summary.open_issues > 0 ? '#ef4444' : '#34d399')}
                {renderStatCard('Build Actions', buildStats?.total_actions ?? 0, `${((buildStats?.success_rate ?? 0) * 100).toFixed(0)}% success rate`, '#fbbf24')}
                {renderStatCard('Last Scan', summary?.last_scan ? new Date(summary.last_scan).toLocaleTimeString() : 'Never', summary?.last_scan ? new Date(summary.last_scan).toLocaleDateString() : '', '#94a3b8')}
            </div>

            {/* Health Status Summary */}
            {health && (
                <div style={styles.section}>
                    <div style={styles.sectionTitle}>
                        System Health —{' '}
                        <span style={{
                            color: healthStatusColor[health.status] || '#94a3b8',
                            fontWeight: 700,
                        }}>
                            {health.status.toUpperCase()}
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                        {Object.entries(health.components || {}).map(([name, comp]) => (
                            <div key={name} style={{ ...styles.card, minWidth: 160 }}>
                                <div style={styles.cardTitle}>{name.replace(/_/g, ' ')}</div>
                                <div style={{
                                    fontSize: '0.85rem',
                                    fontWeight: 600,
                                    color: healthStatusColor[comp.status as string] || '#94a3b8',
                                }}>
                                    {comp.status as string}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Build Stats Breakdown */}
            {buildStats && buildStats.actions_by_type && Object.keys(buildStats.actions_by_type).length > 0 && (
                <div style={styles.section}>
                    <div style={styles.sectionTitle}>Build Actions by Type</div>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                        {Object.entries(buildStats.actions_by_type).map(([type, count]) => (
                            <div key={type} style={styles.card}>
                                <div style={styles.cardTitle}>{type.replace(/_/g, ' ')}</div>
                                <div style={{ ...styles.statValue, fontSize: '1.2rem' }}>{count}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Gap Summary */}
            {gaps && gaps.total_found > 0 && (
                <div style={styles.section}>
                    <div style={styles.sectionTitle}>
                        Gap Analysis — {gaps.total_found} gaps found
                        {gaps.categories && (
                            <span style={{ fontWeight: 400, opacity: 0.6, fontSize: '0.82rem', marginLeft: 8 }}>
                                ({Object.keys(gaps.categories).length} categories)
                            </span>
                        )}
                    </div>
                    {gaps.categories && (
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {Object.entries(gaps.categories).map(([cat, count]) => (
                                <span key={cat} style={styles.badge(gapCategoryColor[cat] || '#94a3b8')}>
                                    {cat.replace(/_/g, ' ')}: {count as number}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap' }}>
                <button
                    style={styles.button}
                    onClick={handleScan}
                    disabled={scanning}
                >
                    {scanning ? '🔄 Scanning...' : '🔍 Trigger Codebase Scan'}
                </button>
                <button
                    style={{
                        ...styles.button,
                        borderColor: 'rgba(52,211,153,0.3)',
                        background: 'rgba(52,211,153,0.1)',
                        color: '#34d399',
                    }}
                    onClick={handleRunCycle}
                    disabled={runningCycle}
                >
                    {runningCycle ? '🔄 Running Cycle...' : '⚡ Run Build Cycle'}
                </button>
            </div>
        </>
    );

    const renderModules = () => (
        <div style={styles.section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={styles.sectionTitle}>Known Modules ({modules.length})</div>
            </div>
            {modules.length === 0 ? (
                <div style={styles.loadingText}>No modules found. Trigger a scan to discover modules.</div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>Package</th>
                                <th style={styles.th}>File</th>
                                <th style={styles.th}>Classes</th>
                                <th style={styles.th}>Functions</th>
                                <th style={styles.th}>Lines</th>
                                <th style={styles.th}>Routes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {modules.slice(0, 100).map((mod, i) => (
                                <tr key={mod.package || i}>
                                    <td style={styles.td}>
                                        <span style={{ fontWeight: 500 }}>{mod.package}</span>
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.6, fontSize: '0.75rem' }}>
                                        {mod.filepath?.split('/').pop()?.split('\\').pop()}
                                    </td>
                                    <td style={styles.td}>{mod.classes}</td>
                                    <td style={styles.td}>{mod.functions}</td>
                                    <td style={styles.td}>{mod.lines}</td>
                                    <td style={styles.td}>
                                        {mod.has_routes ? (
                                            <span style={styles.badge('#34d399')}>✓</span>
                                        ) : (
                                            <span style={{ opacity: 0.3 }}>—</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );

    const renderRoutes = () => (
        <div style={styles.section}>
            <div style={styles.sectionTitle}>Registered Routes ({routes.length})</div>
            {routes.length === 0 ? (
                <div style={styles.loadingText}>No routes registered yet.</div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>Method</th>
                                <th style={styles.th}>Path</th>
                                <th style={styles.th}>Handler</th>
                                <th style={styles.th}>Module</th>
                            </tr>
                        </thead>
                        <tbody>
                            {routes.map((route, i) => (
                                <tr key={`${route.method}-${route.path}-${i}`}>
                                    <td style={styles.td}>
                                        <span style={{
                                            ...styles.badge(
                                                route.method === 'GET' ? '#34d399' :
                                                    route.method === 'POST' ? '#60a5fa' :
                                                        route.method === 'PUT' ? '#fbbf24' :
                                                            route.method === 'DELETE' ? '#ef4444' : '#94a3b8'
                                            ),
                                            fontFamily: 'monospace',
                                        }}>
                                            {route.method}
                                        </span>
                                    </td>
                                    <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: '0.78rem' }}>
                                        {route.path}
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.7 }}>{route.handler}</td>
                                    <td style={{ ...styles.td, opacity: 0.5, fontSize: '0.75rem' }}>{route.module}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );

    const renderIssues = () => (
        <div style={styles.section}>
            <div style={styles.sectionTitle}>Issues ({issues.length})</div>
            {issues.length === 0 ? (
                <div style={styles.loadingText}>No issues found. The codebase is clean!</div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>Type</th>
                                <th style={styles.th}>Severity</th>
                                <th style={styles.th}>Description</th>
                                <th style={styles.th}>Module</th>
                                <th style={styles.th}>Line</th>
                                <th style={styles.th}>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {issues.map((issue) => (
                                <tr key={issue.issue_id}>
                                    <td style={styles.td}>
                                        <span style={styles.badge(issueTypeColor[issue.issue_type] || '#94a3b8')}>
                                            {issue.issue_type}
                                        </span>
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.badge(severityColor[issue.severity] || '#94a3b8')}>
                                            {issue.severity}
                                        </span>
                                    </td>
                                    <td style={{ ...styles.td, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {issue.description}
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.6, fontSize: '0.75rem' }}>
                                        {issue.module?.split('/').pop()?.split('\\').pop()}
                                    </td>
                                    <td style={styles.td}>{issue.lineno || '—'}</td>
                                    <td style={styles.td}>
                                        <span style={styles.badge(
                                            issue.status === 'open' ? '#ef4444' :
                                                issue.status === 'acknowledged' ? '#fbbf24' :
                                                    issue.status === 'fixed' ? '#34d399' : '#94a3b8'
                                        )}>
                                            {issue.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );

    const renderBuild = () => (
        <div style={styles.section}>
            <div style={styles.sectionTitle}>Build Action History ({buildActions.length})</div>
            {buildActions.length === 0 ? (
                <div style={styles.loadingText}>No build actions recorded yet.</div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>ID</th>
                                <th style={styles.th}>Type</th>
                                <th style={styles.th}>Description</th>
                                <th style={styles.th}>Target</th>
                                <th style={styles.th}>Status</th>
                                <th style={styles.th}>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {buildActions.map((action) => (
                                <tr key={action.action_id}>
                                    <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5 }}>
                                        {action.action_id}
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.badge('#60a5fa')}>
                                            {action.action_type?.replace(/_/g, ' ')}
                                        </span>
                                    </td>
                                    <td style={{ ...styles.td, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {action.description}
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.6, fontSize: '0.75rem' }}>
                                        {action.target_file?.split('/').pop()?.split('\\').pop()}
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.badge(
                                            action.status === 'applied' ? '#34d399' :
                                                action.status === 'rolled_back' ? '#fbbf24' :
                                                    action.status === 'failed' ? '#ef4444' : '#94a3b8'
                                        )}>
                                            {action.status}
                                        </span>
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.4, fontSize: '0.72rem' }}>
                                        {action.timestamp ? new Date(action.timestamp).toLocaleTimeString() : '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );

    // ── Health Tab ───────────────────────────────────────────

    const renderHealth = () => (
        <div style={styles.section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={styles.sectionTitle}>
                    Self-Awareness Health —{' '}
                    <span style={{
                        color: healthStatusColor[health?.status || 'unknown'] || '#94a3b8',
                        fontWeight: 700,
                        fontSize: '1.1rem',
                    }}>
                        {health?.status?.toUpperCase() || 'UNKNOWN'}
                    </span>
                </div>
            </div>

            {!health ? (
                <div style={styles.loadingText}>Health data not available.</div>
            ) : (
                <>
                    {/* Component Cards */}
                    <div style={styles.grid}>
                        {Object.entries(health.components || {}).map(([name, comp]) => (
                            <div key={name} style={styles.card}>
                                <div style={styles.cardTitle}>{name.replace(/_/g, ' ')}</div>
                                <div style={{
                                    fontSize: '1.2rem',
                                    fontWeight: 700,
                                    color: healthStatusColor[comp.status as string] || '#94a3b8',
                                    marginBottom: 8,
                                }}>
                                    {comp.status as string}
                                </div>
                                {Object.entries(comp).filter(([k]) => k !== 'status').map(([key, val]) => (
                                    <div key={key} style={{
                                        fontSize: '0.78rem',
                                        opacity: 0.6,
                                        marginTop: 2,
                                    }}>
                                        {key.replace(/_/g, ' ')}: {String(val)}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>

                    {/* Overall Health Bar */}
                    <div style={styles.card}>
                        <div style={styles.cardTitle}>Overall Health Score</div>
                        <div style={styles.progressBar(100, '#34d399')}>
                            <div style={styles.progressFill(
                                health.status === 'healthy' ? 100 :
                                    health.status === 'degraded' ? 60 : 30,
                                healthStatusColor[health.status] || '#94a3b8'
                            )} />
                        </div>
                        <div style={{ fontSize: '0.78rem', opacity: 0.5, marginTop: 4 }}>
                            {Object.keys(health.components || {}).length} components monitored
                        </div>
                    </div>
                </>
            )}
        </div>
    );

    // ── Gaps Tab ─────────────────────────────────────────────

    const renderGaps = () => (
        <div style={styles.section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={styles.sectionTitle}>
                    Gap Analysis Results
                    {gaps && <span style={{ fontWeight: 400, opacity: 0.6, fontSize: '0.85rem', marginLeft: 8 }}>
                        ({gaps.total_found} total, showing top {gaps.returned})
                    </span>}
                </div>
            </div>

            {/* Category Breakdown */}
            {gaps?.categories && Object.keys(gaps.categories).length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                    {Object.entries(gaps.categories).map(([cat, count]) => (
                        <div key={cat} style={{
                            ...styles.card,
                            padding: '8px 12px',
                            minWidth: 140,
                        }}>
                            <div style={styles.cardTitle}>{cat.replace(/_/g, ' ')}</div>
                            <div style={{
                                fontSize: '1.1rem',
                                fontWeight: 700,
                                color: gapCategoryColor[cat] || '#94a3b8',
                            }}>
                                {count as number}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Gaps Table */}
            {!gaps || gaps.gaps.length === 0 ? (
                <div style={styles.loadingText}>No gaps found. The codebase is well-integrated!</div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>Priority</th>
                                <th style={styles.th}>Category</th>
                                <th style={styles.th}>Description</th>
                                <th style={styles.th}>Module</th>
                                <th style={styles.th}>Severity</th>
                                <th style={styles.th}>Suggestion</th>
                            </tr>
                        </thead>
                        <tbody>
                            {gaps.gaps.map((gap) => (
                                <tr key={gap.gap_id}>
                                    <td style={styles.td}>
                                        <div style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 6,
                                        }}>
                                            <div style={styles.progressBar(100, '#a78bfa')}>
                                                <div style={styles.progressFill(
                                                    (gap.priority_score || 0) * 100,
                                                    gap.priority_score >= 0.7 ? '#ef4444' :
                                                        gap.priority_score >= 0.4 ? '#fbbf24' : '#34d399'
                                                )} />
                                            </div>
                                            <span style={{
                                                fontSize: '0.72rem',
                                                fontWeight: 600,
                                                color: gap.priority_score >= 0.7 ? '#ef4444' :
                                                    gap.priority_score >= 0.4 ? '#fbbf24' : '#34d399',
                                            }}>
                                                {(gap.priority_score * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.badge(gapCategoryColor[gap.category] || '#94a3b8')}>
                                            {gap.category.replace(/_/g, ' ')}
                                        </span>
                                    </td>
                                    <td style={{ ...styles.td, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {gap.description}
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.6, fontSize: '0.75rem' }}>
                                        {gap.module?.split('/').pop()?.split('\\').pop()}
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.badge(severityColor[gap.severity] || '#94a3b8')}>
                                            {gap.severity}
                                        </span>
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.7, fontSize: '0.78rem', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {gap.suggestion}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );

    // ── Cycles Tab ────────────────────────────────────────────

    const renderCycles = () => (
        <div style={styles.section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={styles.sectionTitle}>
                    Build Cycles
                    {cycleStatus && (
                        <span style={{ fontWeight: 400, opacity: 0.6, fontSize: '0.85rem', marginLeft: 8 }}>
                            ({cycleStatus.total_cycles} total{cycleStatus.is_running ? ', RUNNING' : ''})
                        </span>
                    )}
                </div>
            </div>

            {/* Cycle Status Card */}
            {cycleStatus && (
                <div style={{ ...styles.card, marginBottom: 16 }}>
                    <div style={styles.cardTitle}>Cycle Status</div>
                    <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 8 }}>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Running</span>
                            <div style={{
                                fontSize: '1rem',
                                fontWeight: 700,
                                color: cycleStatus.is_running ? '#34d399' : '#94a3b8',
                            }}>
                                {cycleStatus.is_running ? 'Yes' : 'No'}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Last Cycle</span>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#a78bfa' }}>
                                {cycleStatus.last_cycle_id || '—'}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Last Status</span>
                            <div style={{
                                fontSize: '1rem',
                                fontWeight: 700,
                                color: cycleStatus.last_cycle_status === 'completed' ? '#34d399' :
                                    cycleStatus.last_cycle_status === 'failed' ? '#ef4444' : '#fbbf24',
                            }}>
                                {cycleStatus.last_cycle_status || '—'}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>Uptime</span>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#22d3ee' }}>
                                {cycleStatus.uptime_hours?.toFixed(1) || '0'}h
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Cycles Table */}
            {buildCycles.length === 0 ? (
                <div style={styles.loadingText}>No build cycles recorded yet.</div>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}>Cycle ID</th>
                                <th style={styles.th}>Status</th>
                                <th style={styles.th}>Actions</th>
                                <th style={styles.th}>Tests</th>
                                <th style={styles.th}>Deploy</th>
                                <th style={styles.th}>Smoke Tests</th>
                                <th style={styles.th}>Started</th>
                                <th style={styles.th}>Errors</th>
                            </tr>
                        </thead>
                        <tbody>
                            {buildCycles.map((cycle) => (
                                <tr key={cycle.cycle_id}>
                                    <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: '0.7rem', opacity: 0.5 }}>
                                        {cycle.cycle_id}
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.badge(
                                            cycle.status === 'completed' ? '#34d399' :
                                                cycle.status === 'running' ? '#60a5fa' :
                                                    cycle.status === 'failed' ? '#ef4444' : '#fbbf24'
                                        )}>
                                            {cycle.status}
                                        </span>
                                    </td>
                                    <td style={styles.td}>{cycle.actions_count}</td>
                                    <td style={styles.td}>
                                        <span style={{
                                            color: cycle.tests_failed > 0 ? '#ef4444' : '#34d399',
                                            fontWeight: 600,
                                        }}>
                                            ✓{cycle.tests_passed}
                                            {cycle.tests_failed > 0 && ` ✗${cycle.tests_failed}`}
                                        </span>
                                    </td>
                                    <td style={styles.td}>
                                        {cycle.deployed ? (
                                            <span style={styles.badge('#34d399')}>
                                                ✓ {cycle.deploy_target || 'deployed'}
                                            </span>
                                        ) : (
                                            <span style={{ opacity: 0.3 }}>—</span>
                                        )}
                                    </td>
                                    <td style={styles.td}>
                                        {cycle.smoke_tests_total > 0 ? (
                                            <span style={{
                                                color: cycle.smoke_tests_passed === cycle.smoke_tests_total ? '#34d399' : '#ef4444',
                                                fontWeight: 600,
                                            }}>
                                                {cycle.smoke_tests_passed}/{cycle.smoke_tests_total}
                                            </span>
                                        ) : (
                                            <span style={{ opacity: 0.3 }}>—</span>
                                        )}
                                    </td>
                                    <td style={{ ...styles.td, opacity: 0.4, fontSize: '0.72rem' }}>
                                        {cycle.started_at ? new Date(cycle.started_at).toLocaleTimeString() : '—'}
                                    </td>
                                    <td style={styles.td}>
                                        {cycle.errors && cycle.errors.length > 0 ? (
                                            <span style={styles.badge('#ef4444')}>
                                                {cycle.errors.length}
                                            </span>
                                        ) : (
                                            <span style={{ opacity: 0.3 }}>—</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );

    // ── Main Render ───────────────────────────────────────────

    const tabs = [
        { key: 'overview', label: 'Overview', icon: '📊' },
        { key: 'modules', label: 'Modules', icon: '📦' },
        { key: 'routes', label: 'Routes', icon: '🔗' },
        { key: 'issues', label: 'Issues', icon: '🐛' },
        { key: 'build', label: 'Build', icon: '🔨' },
        { key: 'health', label: 'Health', icon: '❤️' },
        { key: 'gaps', label: 'Gaps', icon: '🔍' },
        { key: 'cycles', label: 'Cycles', icon: '🔄' },
    ] as const;

    return (
        <div style={styles.container}>
            <div style={styles.header}>Self-Awareness Dashboard</div>

            {error && <div style={styles.errorBox}>{error}</div>}

            {loading ? (
                <div style={styles.loadingText}>Loading self-awareness data...</div>
            ) : (
                <>
                    {/* Tab Navigation */}
                    <div style={{
                        display: 'flex',
                        gap: 4,
                        marginBottom: 20,
                        borderBottom: '1px solid rgba(255,255,255,0.06)',
                        paddingBottom: 0,
                        flexWrap: 'wrap',
                    }}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key)}
                                style={{
                                    padding: '8px 16px',
                                    border: 'none',
                                    background: 'transparent',
                                    color: activeTab === tab.key ? '#a78bfa' : 'rgba(255,255,255,0.4)',
                                    cursor: 'pointer',
                                    fontSize: '0.82rem',
                                    fontWeight: activeTab === tab.key ? 600 : 400,
                                    borderBottom: activeTab === tab.key ? '2px solid #a78bfa' : '2px solid transparent',
                                    transition: 'all 0.2s ease',
                                    fontFamily: 'inherit',
                                }}
                            >
                                {tab.icon} {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    {activeTab === 'overview' && renderOverview()}
                    {activeTab === 'modules' && renderModules()}
                    {activeTab === 'routes' && renderRoutes()}
                    {activeTab === 'issues' && renderIssues()}
                    {activeTab === 'build' && renderBuild()}
                    {activeTab === 'health' && renderHealth()}
                    {activeTab === 'gaps' && renderGaps()}
                    {activeTab === 'cycles' && renderCycles()}
                </>
            )}
        </div>
    );
};

export default SelfAwarenessHub;
