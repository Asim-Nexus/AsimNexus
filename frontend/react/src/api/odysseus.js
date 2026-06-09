/**
 * ODYSSEUS API — Agent Loop, Tool Execution & MCP Service Integration
 *
 * Follows the same axios pattern as asimnexus.js.
 * All endpoints assume backend routes served by simple_backend.py.
 *
 * ── Agent Loop ─────────────────  POST /api/agent/*
 * ── Tool Execution ─────────────  POST /api/tools/*
 * ── MCP Service ────────────────  GET|POST /api/mcp/*
 */

import axios from 'axios';

const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    timeout: 30000,
});

// Bearer token interceptor (identical to asimnexus.js pattern)
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('asimnexus_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ────────────────────────────────────────────────────────────────
// AGENT LOOP API
// Backend: POST /api/agent/run, POST /api/agent/cancel
//          GET  /api/agent/status/{session_id}, GET /api/agent/sessions
//          GET  /api/agent/stats
// ────────────────────────────────────────────────────────────────

export const agentAPI = {
    /** POST /api/agent/run — execute agent loop (AUTO/GUIDE/PLAN/OBSERVE) */
    run: (userInput, mode = 'AUTO', cloneId = null, systemPrompt = null) =>
        api.post('/api/agent/run', {
            user_input: userInput,
            mode,
            clone_id: cloneId,
            system_prompt: systemPrompt,
        }),

    /** POST /api/agent/cancel — cancel an active session */
    cancel: (sessionId) => api.post('/api/agent/cancel', { session_id: sessionId }),

    /** GET /api/agent/status/{sessionId} — get session status */
    status: (sessionId) => api.get(`/api/agent/status/${sessionId}`),

    /** GET /api/agent/sessions — list all agent sessions */
    sessions: () => api.get('/api/agent/sessions'),

    /** GET /api/agent/stats — agent loop statistics */
    stats: () => api.get('/api/agent/stats'),
};

// ────────────────────────────────────────────────────────────────
// TOOL EXECUTION API
// Backend: GET /api/tools/list, POST /api/tools/execute
//          POST /api/tools/approve, POST /api/tools/reject
//          GET /api/tools/pending, GET /api/tools/audit
// ────────────────────────────────────────────────────────────────

export const toolsAPI = {
    /** GET /api/tools/list — list all available tools */
    list: () => api.get('/api/tools/list'),

    /** POST /api/tools/execute — execute a tool */
    execute: (toolName, args, sessionId = null) =>
        api.post('/api/tools/execute', {
            tool_name: toolName,
            arguments: args,
            session_id: sessionId,
        }),

    /** POST /api/tools/approve — approve a pending tool execution */
    approve: (executionId) => api.post('/api/tools/approve', { execution_id: executionId }),

    /** POST /api/tools/reject — reject a pending tool execution */
    reject: (executionId) => api.post('/api/tools/reject', { execution_id: executionId }),

    /** GET /api/tools/pending — get pending tool approvals */
    pending: () => api.get('/api/tools/pending'),

    /** GET /api/tools/audit — get tool execution audit log */
    audit: (limit = 30) => api.get('/api/tools/audit', { params: { limit } }),
};

// ────────────────────────────────────────────────────────────────
// MCP SERVICE API
// Backend: GET /api/mcp/tools, POST /api/mcp/call
//          POST /api/mcp/approve/{call_id}, POST /api/mcp/reject/{call_id}
//          GET /api/mcp/pending, GET /api/mcp/audit, GET /api/mcp/status
// ────────────────────────────────────────────────────────────────

export const mcpAPI = {
    /** GET /api/mcp/tools — list all MCP tools */
    tools: () => api.get('/api/mcp/tools'),

    /** POST /api/mcp/call — call an MCP tool (backend expects tool_name + parameters) */
    call: (toolName, params = {}, context = '') =>
        api.post('/api/mcp/call', {
            tool_name: toolName,
            parameters: params,
            context,
        }),

    /** POST /api/mcp/approve/{callId} — approve pending MCP call */
    approve: (callId) => api.post(`/api/mcp/approve/${callId}`),

    /** POST /api/mcp/reject/{callId} — reject pending MCP call */
    reject: (callId) => api.post(`/api/mcp/reject/${callId}`),

    /** GET /api/mcp/pending — list pending MCP approvals */
    pending: () => api.get('/api/mcp/pending'),

    /** GET /api/mcp/audit — MCP audit log */
    audit: (limit = 30) => api.get('/api/mcp/audit', { params: { limit } }),

    /** GET /api/mcp/status — MCP server connection status */
    status: () => api.get('/api/mcp/status'),
};

// ────────────────────────────────────────────────────────────────
// ODYSSEUS AGGREGATOR — Convenience export
// ────────────────────────────────────────────────────────────────

export const odysseusAPI = {
    agent: agentAPI,
    tools: toolsAPI,
    mcp: mcpAPI,
};

export default api;
