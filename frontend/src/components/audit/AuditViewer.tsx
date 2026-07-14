import React, { useEffect, useState } from 'react';
import api from '../../api/asimnexus';

interface AuditLog {
    timestamp: number;
    user_id: string;
    intent: Record<string, unknown>;
    plan: Record<string, unknown>;
    results?: Array<{
        agent: string;
        status: string;
        message?: string;
    }>;
}

interface AuditViewerProps {
    auditId: string | null;
    onClose: () => void;
}

const AuditViewer: React.FC<AuditViewerProps> = ({ auditId, onClose }) => {
    const [log, setLog] = useState<AuditLog | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!auditId) return;
        setLoading(true);
        api.get(`/api/v1/audit/${auditId}`)
            .then((res: unknown) => {
                const response = res as { data?: AuditLog };
                setLog(response.data || null);
                setError(null);
            })
            .catch((err: unknown) => {
                const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
                setError(axiosErr.response?.data?.detail || axiosErr.message || 'Audit log not found');
            })
            .finally(() => {
                setLoading(false);
            });
    }, [auditId]);

    if (!auditId) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999
        }}>
            <div style={{
                background: '#1e293b',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '16px',
                width: '90%',
                maxWidth: '600px',
                maxHeight: '80vh',
                overflowY: 'auto',
                padding: '24px',
                color: '#e2e8f0',
                fontFamily: "'Inter', sans-serif"
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h3 style={{ margin: 0 }}>Immutable Audit Log</h3>
                    <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '18px' }}>✕</button>
                </div>

                {loading && <div>Loading audit data...</div>}
                {error && <div style={{ color: '#ef4444' }}>{error}</div>}

                {log && (
                    <div>
                        <div style={{ marginBottom: '16px', fontSize: '14px', color: '#cbd5e1' }}>
                            <strong>Audit ID:</strong> {auditId} <br />
                            <strong>Timestamp:</strong> {new Date(log.timestamp * 1000).toLocaleString()} <br />
                            <strong>User ID:</strong> {log.user_id}
                        </div>

                        <h4>Intent</h4>
                        <pre style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', fontSize: '12px', overflowX: 'auto' }}>
                            {JSON.stringify(log.intent, null, 2)}
                        </pre>

                        <h4>Plan</h4>
                        <pre style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', fontSize: '12px', overflowX: 'auto' }}>
                            {JSON.stringify(log.plan, null, 2)}
                        </pre>

                        <h4>Execution Results</h4>
                        {log.results && log.results.map((res, i) => (
                            <div key={i} style={{
                                background: 'rgba(255,255,255,0.05)',
                                padding: '12px',
                                borderRadius: '8px',
                                marginBottom: '8px',
                                fontSize: '13px'
                            }}>
                                <div style={{ fontWeight: 'bold', color: res.status === 'success' ? '#10b981' : '#ef4444' }}>
                                    {res.agent} - {res.status}
                                </div>
                                {res.message && <div>{res.message}</div>}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AuditViewer;
