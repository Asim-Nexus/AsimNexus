/**
 * MCPServiceBrowser.tsx
 * MCP server management and tool browser.
 *
 * Shows server list with connection status, tool browser,
 * tool detail view with parameter schema, and quick "Try it" invoke.
 */
import { useState, useEffect, useCallback } from 'react';
import { mcpAPI } from '../../api';
import './odysseus.css';

const BUILT_IN_SERVERS = [
    'asim-memory',
    'asim-mesh',
    'asim-files',
    'asim-dharma',
    'asim-clones',
];

const STATUS_ICONS: Record<string, string> = {
    connected: '🟢',
    connecting: '🟡',
    disconnected: '🔴',
    error: '⚠️',
};

interface MCPServer {
    name: string;
    status: string;
    tool_count?: number;
    tools?: MCPTool[];
    [key: string]: unknown;
}

interface MCPTool {
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
    input_schema?: Record<string, unknown>;
    [key: string]: unknown;
}

interface ServerCardProps {
    server: MCPServer;
    onConnect: (name: string) => void;
    onDisconnect: (name: string) => void;
    onSelectTool: (server: MCPServer) => void;
}

function ServerCard({ server, onConnect, onDisconnect, onSelectTool }: ServerCardProps) {
    const statusIcon = STATUS_ICONS[server.status] || '🔴';

    return (
        <div
            className={`odysseus-server-card ${server.status === 'connected' ? 'connected' : ''}`}
        >
            <div className="odysseus-server-card-header">
                <span className="odysseus-server-status-icon">{statusIcon}</span>
                <span className="odysseus-server-name">{server.name}</span>
            </div>
            <div className="odysseus-server-meta">
                <span className="odysseus-server-status-text">{server.status || 'disconnected'}</span>
                {server.tool_count !== undefined && (
                    <span className="odysseus-server-tool-count">
                        {server.tool_count} tools
                    </span>
                )}
            </div>
            <div className="odysseus-server-actions">
                {server.status === 'connected' ? (
                    <button
                        className="odysseus-server-btn disconnect"
                        onClick={() => onDisconnect(server.name)}
                    >
                        Disconnect
                    </button>
                ) : (
                    <button
                        className="odysseus-server-btn connect"
                        onClick={() => onConnect(server.name)}
                    >
                        Connect
                    </button>
                )}
                {server.tools && server.tools.length > 0 && (
                    <button
                        className="odysseus-server-btn browse"
                        onClick={() => onSelectTool(server)}
                    >
                        Browse Tools
                    </button>
                )}
            </div>
        </div>
    );
}

interface ToolDetailProps {
    tool: MCPTool;
    onTryIt: (tool: MCPTool) => void;
    onClose: () => void;
}

function ToolDetail({ tool, onTryIt, onClose }: ToolDetailProps) {
    return (
        <div className="odysseus-tool-detail">
            <div className="odysseus-tool-detail-header">
                <span className="odysseus-tool-detail-name">🔧 {tool.name}</span>
                <div className="odysseus-tool-detail-actions">
                    <button
                        className="odysseus-tool-try-btn"
                        onClick={() => onTryIt(tool)}
                    >
                        Try it
                    </button>
                    <button className="odysseus-tool-close-btn" onClick={onClose}>
                        ✕
                    </button>
                </div>
            </div>
            {tool.description && (
                <div className="odysseus-tool-detail-desc">{tool.description}</div>
            )}
            <div className="odysseus-tool-detail-section">
                <div className="odysseus-tool-detail-section-title">Parameters Schema</div>
                <pre className="odysseus-code-block">
                    {JSON.stringify(tool.parameters || tool.input_schema || {}, null, 2)}
                </pre>
            </div>
        </div>
    );
}

interface MCPServiceBrowserProps {
    user?: Record<string, unknown>;
}

export default function MCPServiceBrowser({ user: _user }: MCPServiceBrowserProps) {
    const [servers, setServers] = useState<MCPServer[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedServer, setSelectedServer] = useState<MCPServer | null>(null);
    const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
    const [allTools, setAllTools] = useState<MCPTool[]>([]);
    const [toolsLoading, setToolsLoading] = useState(false);
    const [tryResult, setTryResult] = useState<{ success: boolean; data?: unknown; error?: string } | null>(null);
    const [tryLoading, setTryLoading] = useState(false);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await mcpAPI.status();
            const data = res.data as Record<string, unknown>;
            // Merge built-in server list with status response
            const serverStatuses = (data?.servers || data || {}) as Record<string, Record<string, unknown>>;
            const merged: MCPServer[] = BUILT_IN_SERVERS.map((name) => ({
                name,
                status: (serverStatuses[name]?.status as string) || 'disconnected',
                tool_count: (serverStatuses[name]?.tool_count as number) || 0,
                tools: (serverStatuses[name]?.tools as MCPTool[]) || [],
                ...serverStatuses[name],
            }));
            setServers(merged);
            setError(null);
        } catch (err) {
            // If backend not available, show built-in servers as disconnected
            setServers(
                BUILT_IN_SERVERS.map((name) => ({
                    name,
                    status: 'disconnected',
                    tool_count: 0,
                }))
            );
            setError('Could not fetch MCP status. Backend may be unavailable.');
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchTools = useCallback(async () => {
        setToolsLoading(true);
        try {
            const res = await mcpAPI.tools();
            const data = res.data as Record<string, unknown>;
            const toolList = (data?.tools || data || []) as unknown;
            setAllTools(Array.isArray(toolList) ? (toolList as MCPTool[]) : []);
        } catch {
            setAllTools([]);
        } finally {
            setToolsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStatus();
        fetchTools();
    }, [fetchStatus, fetchTools]);

    const handleConnect = useCallback(async (serverName: string) => {
        setServers((prev) =>
            prev.map((s) =>
                s.name === serverName ? { ...s, status: 'connecting' } : s
            )
        );
        // Connect is implicit via /api/mcp/call — status refresh will show connected if reachable
        try {
            await mcpAPI.call('ping', {}, serverName);
            setServers((prev) =>
                prev.map((s) =>
                    s.name === serverName ? { ...s, status: 'connected' } : s
                )
            );
        } catch {
            setServers((prev) =>
                prev.map((s) =>
                    s.name === serverName ? { ...s, status: 'error' } : s
                )
            );
        }
    }, []);

    const handleDisconnect = useCallback(async (serverName: string) => {
        setServers((prev) =>
            prev.map((s) =>
                s.name === serverName ? { ...s, status: 'disconnected' } : s
            )
        );
    }, []);

    const handleSelectTool = useCallback(
        (server: MCPServer) => {
            setSelectedServer(server);
            setSelectedTool(null);
            setTryResult(null);
        },
        []
    );

    const handleTryIt = useCallback(async (tool: MCPTool) => {
        if (!selectedServer) return;
        setTryLoading(true);
        setTryResult(null);
        try {
            const res = await mcpAPI.call(tool.name, {}, selectedServer.name);
            setTryResult({
                success: true,
                data: res.data,
            });
        } catch (err) {
            const e = err as { response?: { data?: { detail?: string } }; message?: string };
            setTryResult({
                success: false,
                error: e.response?.data?.detail || e.message || 'Tool call failed',
            });
        } finally {
            setTryLoading(false);
        }
    }, [selectedServer]);

    if (loading) {
        return (
            <div className="odysseus-loading-container">
                <div className="odysseus-loading-spinner" />
                <span>Loading MCP servers...</span>
            </div>
        );
    }

    return (
        <div className="odysseus-mcp-browser">
            {/* ── Error Banner ── */}
            {error && (
                <div className="odysseus-error-banner">
                    ⚠️ {error}
                    <button className="odysseus-retry-btn" onClick={fetchStatus}>
                        Retry
                    </button>
                </div>
            )}

            <div className="odysseus-mcp-layout">
                {/* ── Server List ── */}
                <div className="odysseus-server-list">
                    <h3 className="odysseus-section-title">🖥️ MCP Servers</h3>
                    {servers.length === 0 ? (
                        <div className="odysseus-empty-state">
                            No MCP servers available
                        </div>
                    ) : (
                        servers.map((server) => (
                            <ServerCard
                                key={server.name}
                                server={server}
                                onConnect={handleConnect}
                                onDisconnect={handleDisconnect}
                                onSelectTool={handleSelectTool}
                            />
                        ))
                    )}
                </div>

                {/* ── Tool Browser / Detail ── */}
                <div className="odysseus-tool-browser">
                    {selectedServer ? (
                        <>
                            <h3 className="odysseus-section-title">
                                🔧 {selectedServer.name} — Tools
                            </h3>
                            {selectedServer.tools && selectedServer.tools.length > 0 ? (
                                <div className="odysseus-tool-list">
                                    {selectedServer.tools.map((tool, i) => (
                                        <div
                                            key={tool.name || i}
                                            className={`odysseus-tool-item ${selectedTool?.name === tool.name ? 'active' : ''
                                                }`}
                                            onClick={() => setSelectedTool(tool)}
                                        >
                                            <span className="odysseus-tool-item-icon">🔧</span>
                                            <span className="odysseus-tool-item-name">{tool.name}</span>
                                            {tool.description && (
                                                <span className="odysseus-tool-item-desc">
                                                    {tool.description.slice(0, 60)}
                                                    {tool.description.length > 60 ? '...' : ''}
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="odysseus-empty-state">
                                    {toolsLoading ? (
                                        <div className="odysseus-loading-container">
                                            <div className="odysseus-loading-spinner" />
                                            <span>Loading tools...</span>
                                        </div>
                                    ) : (
                                        'No tools available for this server'
                                    )}
                                </div>
                            )}

                            {/* Tool Detail */}
                            {selectedTool && (
                                <ToolDetail
                                    tool={selectedTool}
                                    onTryIt={handleTryIt}
                                    onClose={() => setSelectedTool(null)}
                                />
                            )}

                            {/* Try Result */}
                            {tryResult && (
                                <div
                                    className={`odysseus-try-result ${tryResult.success ? 'success' : 'error'
                                        }`}
                                >
                                    <div className="odysseus-try-result-header">
                                        {tryResult.success ? '✅ Result' : '❌ Error'}
                                    </div>
                                    <pre className="odysseus-code-block">
                                        {JSON.stringify(tryResult.success ? tryResult.data : tryResult.error, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {tryLoading && (
                                <div className="odysseus-loading-container">
                                    <div className="odysseus-loading-spinner" />
                                    <span>Executing tool...</span>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="odysseus-empty-state odysseus-mcp-empty">
                            <div className="odysseus-empty-icon">🖥️</div>
                            <div className="odysseus-empty-text">
                                Select a server to browse its tools
                            </div>
                            <div className="odysseus-empty-hint">
                                {allTools.length > 0
                                    ? `${allTools.length} tools available across all servers`
                                    : 'Connect to a server to see available tools'}
                            </div>
                            {allTools.length > 0 && (
                                <div className="odysseus-all-tools-summary">
                                    <h4>All Available Tools</h4>
                                    <div className="odysseus-all-tools-list">
                                        {allTools.slice(0, 20).map((t, i) => (
                                            <span key={i} className="odysseus-all-tool-tag">
                                                🔧 {t.name || String(t)}
                                            </span>
                                        ))}
                                        {allTools.length > 20 && (
                                            <span className="odysseus-all-tool-tag more">
                                                +{allTools.length - 20} more
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
