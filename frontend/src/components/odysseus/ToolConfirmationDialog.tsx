/**
 * ToolConfirmationDialog.tsx
 * Modal dialog for approving/rejecting tool executions (veto integration).
 *
 * Shows: tool name, arguments (JSON), security level badge,
 * user/clone context, approve/reject with confirmation for dangerous ops.
 */
import { useState, useEffect, useCallback } from 'react';
import { toolsAPI } from '../../api';
import './odysseus.css';

interface SecurityLevelMeta {
    icon: string;
    label: string;
    color: string;
}

const SECURITY_LEVELS: Record<string, SecurityLevelMeta> = {
    dangerous: { icon: '🔴', label: 'Dangerous', color: '#ef4444' },
    sensitive: { icon: '🟡', label: 'Sensitive', color: '#f59e0b' },
    secure: { icon: '🟢', label: 'Secure', color: '#10b981' },
};

interface ConfirmOverlayProps {
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
}

function ConfirmOverlay({ message, onConfirm, onCancel }: ConfirmOverlayProps) {
    return (
        <div className="odysseus-confirm-overlay">
            <div className="odysseus-confirm-box">
                <div className="odysseus-confirm-icon">⚠️</div>
                <div className="odysseus-confirm-text">{message}</div>
                <div className="odysseus-confirm-actions">
                    <button className="odysseus-btn-danger" onClick={onConfirm}>
                        Yes, proceed
                    </button>
                    <button className="odysseus-btn-ghost" onClick={onCancel}>
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}

interface ToolConfirmationDialogProps {
    open: boolean;
    onClose?: () => void;
    execution?: Record<string, unknown> | null;
    onApproved?: (execution: Record<string, unknown>) => void;
    onRejected?: (execution: Record<string, unknown>) => void;
    onRememberChoice?: (toolName: string, choice: string) => void;
}

export default function ToolConfirmationDialog({
    open,
    onClose,
    execution,
    onApproved,
    onRejected,
    onRememberChoice,
}: ToolConfirmationDialogProps) {
    const [processing, setProcessing] = useState(false);
    const [confirmDangerous, setConfirmDangerous] = useState(false);
    const [rememberChoice, setRememberChoice] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Reset state when dialog opens with new execution
    useEffect(() => {
        if (open) {
            setProcessing(false);
            setConfirmDangerous(false);
            setRememberChoice(false);
            setError(null);
        }
    }, [open, execution?.execution_id]);

    const handleApprove = useCallback(async () => {
        if (!execution) return;

        const securityLevel = (execution.security_level as string) || 'secure';
        if (securityLevel === 'dangerous' && !confirmDangerous) {
            setConfirmDangerous(true);
            return;
        }

        setProcessing(true);
        setError(null);
        try {
            await toolsAPI.approve(execution.execution_id as string);
            if (rememberChoice && onRememberChoice) {
                onRememberChoice(execution.tool_name as string, 'approve');
            }
            if (onApproved) onApproved(execution);
            if (onClose) onClose();
        } catch (err) {
            const e = err as { response?: { data?: { detail?: string } }; message?: string };
            setError(e.response?.data?.detail || e.message || 'Failed to approve');
        } finally {
            setProcessing(false);
        }
    }, [execution, confirmDangerous, rememberChoice, onApproved, onClose, onRememberChoice]);

    const handleReject = useCallback(async () => {
        if (!execution) return;

        setProcessing(true);
        setError(null);
        try {
            await toolsAPI.reject(execution.execution_id as string);
            if (rememberChoice && onRememberChoice) {
                onRememberChoice(execution.tool_name as string, 'reject');
            }
            if (onRejected) onRejected(execution);
            if (onClose) onClose();
        } catch (err) {
            const e = err as { response?: { data?: { detail?: string } }; message?: string };
            setError(e.response?.data?.detail || e.message || 'Failed to reject');
        } finally {
            setProcessing(false);
        }
    }, [execution, rememberChoice, onRejected, onClose, onRememberChoice]);

    if (!open || !execution) return null;

    const securityLevel = (execution.security_level as string) || 'secure';
    const secMeta = SECURITY_LEVELS[securityLevel] || SECURITY_LEVELS.secure;

    return (
        <div className="odysseus-dialog-wrapper">
            <div className="odysseus-dialog-overlay" onClick={processing ? undefined : onClose} />
            <div className="odysseus-dialog">
                <div className="odysseus-dialog-header">
                    <span className="odysseus-dialog-title">🔧 Tool Execution Required</span>
                    <button
                        className="odysseus-dialog-close"
                        onClick={onClose}
                        disabled={processing}
                    >
                        ✕
                    </button>
                </div>

                <div className="odysseus-dialog-body">
                    <>
                        {/* Security Level Badge */}
                        <div
                            className="odysseus-security-badge"
                            style={{
                                background: `${secMeta.color}18`,
                                borderColor: `${secMeta.color}44`,
                                color: secMeta.color,
                            }}
                        >
                            {secMeta.icon} {secMeta.label}
                        </div>

                        {/* Tool Name */}
                        <div className="odysseus-dialog-field">
                            <label>Tool</label>
                            <div className="odysseus-dialog-value">
                                <code>{String((execution as Record<string, unknown>).tool_name ?? 'Unknown')}</code>
                            </div>
                        </div>

                        {/* Arguments */}
                        <div className="odysseus-dialog-field">
                            <label>Arguments</label>
                            <pre className="odysseus-dialog-json">
                                {JSON.stringify(execution.arguments || execution.args || {}, null, 2)}
                            </pre>
                        </div>

                        {/* Context */}
                        {(execution.user_context || execution.clone_context) && (
                            <div className="odysseus-dialog-field">
                                <label>Context</label>
                                <div className="odysseus-dialog-value">
                                    {Boolean((execution as Record<string, unknown>).user_context) && (
                                        <div className="odysseus-context-tag">👤 {String((execution as Record<string, unknown>).user_context)}</div>
                                    )}
                                    {Boolean((execution as Record<string, unknown>).clone_context) && (
                                        <div className="odysseus-context-tag">🧬 {String((execution as Record<string, unknown>).clone_context)}</div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Remember Choice */}
                        <label className="odysseus-remember-label">
                            <input
                                type="checkbox"
                                checked={rememberChoice}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRememberChoice(e.target.checked)}
                                disabled={processing}
                            />
                            <span>Remember my choice for this session</span>
                        </label>

                        {/* Error */}
                        {error && (
                            <div className="odysseus-dialog-error">
                                ⚠️ {error}
                            </div>
                        )}

                        {/* Confirmation overlay for dangerous */}
                        {confirmDangerous && (
                            <ConfirmOverlay
                                message={`This is a ${secMeta.label.toLowerCase()} operation. Are you sure you want to proceed?`}
                                onConfirm={() => {
                                    setConfirmDangerous(false);
                                    handleApprove();
                                }}
                                onCancel={() => setConfirmDangerous(false)}
                            />
                        )}
                    </>
                </div>

                <div className="odysseus-dialog-footer">
                    <button
                        className="odysseus-btn-reject"
                        onClick={handleReject}
                        disabled={processing}
                    >
                        {processing ? '⏳' : '✕'} Reject
                    </button>
                    <button
                        className="odysseus-btn-approve"
                        onClick={handleApprove}
                        disabled={processing}
                    >
                        {processing ? '⏳' : '✓'} Approve
                    </button>
                </div>
            </div>
        </div>
    );
}
