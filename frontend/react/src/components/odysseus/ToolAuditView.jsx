/**
 * ToolAuditView.jsx
 * Audit log viewer for tool executions.
 *
 * Table with columns: time, tool name, user, status, duration.
 * Filterable by tool name, user, status.
 * Expandable rows showing full arguments and result.
 * Pagination (20 per page).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { toolsAPI } from '../../api/odysseus';
import './odysseus.css';

const PAGE_SIZE = 20;

const STATUS_ICONS = {
    completed: '✅',
    approved: '✅',
    running: '⏳',
    pending: '⏳',
    failed: '❌',
    rejected: '🚫',
    cancelled: '🚫',
    error: '❌',
};

function formatTime(ts) {
    if (!ts) return '—';
    return new Date(ts).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

function AuditRow({ entry }) {
    const [expanded, setExpanded] = useState(false);

    const statusIcon = STATUS_ICONS[entry.status] || '❓';
    const duration = entry.duration || entry.execution_time || null;

    return (
        <>
            <tr
                className="odysseus-audit-row"
                onClick={() => setExpanded(!expanded)}
            >
                <td className="odysseus-audit-cell time">{formatTime(entry.timestamp || entry.ts)}</td>
                <td className="odysseus-audit-cell tool-name">
                    <code>{entry.tool_name || entry.tool || 'Unknown'}</code>
                </td>
                <td className="odysseus-audit-cell user">{entry.user || entry.user_id || '—'}</td>
                <td className="odysseus-audit-cell status">{statusIcon} {entry.status}</td>
                <td className="odysseus-audit-cell duration">
                    {duration ? `${duration}ms` : '—'}
                </td>
            </tr>
            {expanded && (
                <tr className="odysseus-audit-expanded">
                    <td colSpan={5}>
                        <div className="odysseus-audit-detail">
                            <div className="odysseus-audit-detail-section">
                                <div className="odysseus-detail-label">Arguments</div>
                                <pre className="odysseus-code-block">
                                    {JSON.stringify(entry.arguments || entry.args || {}, null, 2)}
                                </pre>
                            </div>
                            <div className="odysseus-audit-detail-section">
                                <div className="odysseus-detail-label">Result</div>
                                <pre className="odysseus-code-block">
                                    {entry.result
                                        ? typeof entry.result === 'string'
                                            ? entry.result
                                            : JSON.stringify(entry.result, null, 2)
                                        : 'No result'}
                                </pre>
                            </div>
                            {entry.error && (
                                <div className="odysseus-audit-detail-section">
                                    <div className="odysseus-detail-label error">Error</div>
                                    <pre className="odysseus-code-block error">
                                        {entry.error}
                                    </pre>
                                </div>
                            )}
                        </div>
                    </td>
                </tr>
            )}
        </>
    );
}

export default function ToolAuditView({ user }) {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(0);
    const [filters, setFilters] = useState({
        toolName: '',
        user: '',
        status: '',
    });

    const totalPages = Math.max(1, Math.ceil(entries.length / PAGE_SIZE));
    const paginatedEntries = entries.slice(
        page * PAGE_SIZE,
        (page + 1) * PAGE_SIZE
    );

    const fetchAudit = useCallback(async () => {
        setLoading(true);
        try {
            const res = await toolsAPI.audit(100);
            const data = res.data;
            const rawEntries = data?.entries || data?.audit || data || [];
            setEntries(Array.isArray(rawEntries) ? rawEntries : []);
            setError(null);
        } catch (err) {
            setEntries([]);
            setError('Failed to fetch audit log');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAudit();
    }, [fetchAudit]);

    // Filter entries
    const filteredEntries = entries.filter((e) => {
        if (filters.toolName) {
            const tn = (e.tool_name || e.tool || '').toLowerCase();
            if (!tn.includes(filters.toolName.toLowerCase())) return false;
        }
        if (filters.user) {
            const u = (e.user || e.user_id || '').toLowerCase();
            if (!u.includes(filters.user.toLowerCase())) return false;
        }
        if (filters.status) {
            if ((e.status || '').toLowerCase() !== filters.status.toLowerCase()) return false;
        }
        return true;
    });

    const filteredPages = Math.max(1, Math.ceil(filteredEntries.length / PAGE_SIZE));
    const filteredPaginated = filteredEntries.slice(
        page * PAGE_SIZE,
        (page + 1) * PAGE_SIZE
    );

    const handleFilterChange = (key, value) => {
        setFilters((prev) => ({ ...prev, [key]: value }));
        setPage(0);
    };

    // Extract unique statuses for filter dropdown
    const uniqueStatuses = [...new Set(entries.map((e) => e.status || 'unknown'))];

    if (loading && entries.length === 0) {
        return (
            <div className="odysseus-loading-container">
                <div className="odysseus-loading-spinner" />
                <span>Loading audit log...</span>
            </div>
        );
    }

    return (
        <div className="odysseus-audit-view">
            {/* Header */}
            <div className="odysseus-panel-header">
                <h3 className="odysseus-panel-title">📋 Tool Execution Audit</h3>
                <button className="odysseus-refresh-btn" onClick={fetchAudit}>
                    ↻ Refresh
                </button>
            </div>

            {/* Error */}
            {error && (
                <div className="odysseus-error-banner">
                    ⚠️ {error}
                    <button className="odysseus-retry-btn" onClick={fetchAudit}>
                        Retry
                    </button>
                </div>
            )}

            {/* Filters */}
            <div className="odysseus-audit-filters">
                <input
                    className="odysseus-filter-input"
                    placeholder="🔍 Filter by tool name..."
                    value={filters.toolName}
                    onChange={(e) => handleFilterChange('toolName', e.target.value)}
                />
                <input
                    className="odysseus-filter-input"
                    placeholder="👤 Filter by user..."
                    value={filters.user}
                    onChange={(e) => handleFilterChange('user', e.target.value)}
                />
                <select
                    className="odysseus-filter-select"
                    value={filters.status}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                >
                    <option value="">All statuses</option>
                    {uniqueStatuses.map((s) => (
                        <option key={s} value={s}>
                            {STATUS_ICONS[s] || '❓'} {s}
                        </option>
                    ))}
                </select>
            </div>

            {/* Table */}
            {filteredEntries.length === 0 ? (
                <div className="odysseus-empty-state">
                    <div className="odysseus-empty-icon">📋</div>
                    <div className="odysseus-empty-text">
                        {entries.length === 0
                            ? 'No audit entries yet'
                            : 'No entries match your filters'}
                    </div>
                    <div className="odysseus-empty-hint">
                        Tool executions will appear here as they are run
                    </div>
                </div>
            ) : (
                <div className="odysseus-audit-table-wrapper">
                    <table className="odysseus-audit-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Tool</th>
                                <th>User</th>
                                <th>Status</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredPaginated.map((entry, i) => (
                                <AuditRow key={entry.execution_id || entry.id || i} entry={entry} />
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Pagination */}
            {filteredEntries.length > PAGE_SIZE && (
                <div className="odysseus-pagination">
                    <button
                        className="odysseus-page-btn"
                        disabled={page === 0}
                        onClick={() => setPage((p) => Math.max(0, p - 1))}
                    >
                        ◀ Prev
                    </button>
                    <span className="odysseus-page-info">
                        Page {page + 1} of {filteredPages}
                    </span>
                    <button
                        className="odysseus-page-btn"
                        disabled={page >= filteredPages - 1}
                        onClick={() => setPage((p) => p + 1)}
                    >
                        Next ▶
                    </button>
                </div>
            )}
        </div>
    );
}
