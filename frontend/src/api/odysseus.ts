/**
 * Odysseus Agent/Tool/MCP API Module
 * ====================================
 * TypeScript re-implementation of the old odysseus.js API.
 * Uses the shared axios instance from asimnexus.ts.
 *
 * Backend routes (all exist in app.py):
 *   - /api/agent/*       → routes/chat.py (agent run/cancel/sessions/stats/status)
 *   - /api/mcp/*         → routes/mcp.py (tools/call/approve/reject/pending/audit/status)
 *   - /api/tools/*       → routes/mcp.py (approve/reject/audit)
 */

import api from './asimnexus';

// ═══════════════════════════════════════════════════════════════════
// AGENT API
// ═══════════════════════════════════════════════════════════════════

export const agentAPI = {
    /** List active agent sessions */
    sessions: () => api.get('/api/agent/sessions'),

    /** Get agent stats */
    stats: () => api.get('/api/agent/stats'),

    /** Get status of a specific session */
    status: (sessionId: string) => api.get(`/api/agent/status/${sessionId}`),

    /** Run an agent with a message and mode */
    run: (message: string, mode: string = 'AUTO') =>
        api.post('/api/agent/run', { message, mode }),

    /** Cancel an active session */
    cancel: (sessionId: string) =>
        api.post('/api/agent/cancel', { session_id: sessionId }),
};

// ═══════════════════════════════════════════════════════════════════
// TOOLS API (veto/approval integration)
// ═══════════════════════════════════════════════════════════════════

export const toolsAPI = {
    /** Approve a pending tool execution */
    approve: (executionId: string) =>
        api.post(`/api/mcp/approve/${executionId}`, { user_id: 'web_user' }),

    /** Reject a pending tool execution */
    reject: (executionId: string) =>
        api.post(`/api/mcp/reject/${executionId}`, { user_id: 'web_user' }),

    /** Get audit log */
    audit: (limit: number = 30) => api.get(`/api/mcp/audit?limit=${limit}`),
};

// ═══════════════════════════════════════════════════════════════════
// MCP API (Dharma-Gated MCP Server)
// ═══════════════════════════════════════════════════════════════════

export const mcpAPI = {
    /** Get MCP server status */
    status: () => api.get('/api/mcp/status'),

    /** List registered MCP tools */
    tools: () => api.get('/api/mcp/tools'),

    /** Call an MCP tool */
    call: (toolName: string, parameters: Record<string, unknown> = {}, _serverName?: string) =>
        api.post('/api/mcp/call', {
            tool_name: toolName,
            parameters,
            user_id: 'web_user',
        }),

    /** List pending Final-3 approvals */
    pending: () => api.get('/api/mcp/pending'),

    /** Approve a pending call */
    approve: (callId: string) =>
        api.post(`/api/mcp/approve/${callId}`, { user_id: 'web_user' }),

    /** Reject a pending call */
    reject: (callId: string) =>
        api.post(`/api/mcp/reject/${callId}`, { user_id: 'web_user' }),

    /** Get audit log */
    audit: (limit: number = 30) => api.get(`/api/mcp/audit?limit=${limit}`),
};

// ═══════════════════════════════════════════════════════════════════
// ODYSSEUS API (legacy — kept for backward compat)
// ═══════════════════════════════════════════════════════════════════

export const odysseusAPI = {
    agent: agentAPI,
    tools: toolsAPI,
    mcp: mcpAPI,
};
