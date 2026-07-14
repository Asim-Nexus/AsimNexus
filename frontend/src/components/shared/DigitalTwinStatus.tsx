import React, { useEffect, useState } from 'react';
import api from '../../api/asimnexus';

interface TwinStatus {
    online: boolean;
    twinId?: string;
}

interface DigitalTwinStatusProps {
    mode?: string;
}

const DigitalTwinStatus: React.FC<DigitalTwinStatusProps> = ({ mode }) => {
    const [status, setStatus] = useState<TwinStatus | null>(null);

    useEffect(() => {
        // Poll the backend every 10s for twin status
        const checkStatus = () => {
            api.get('/api/v1/operator/status')
                .then((res: unknown) => {
                    const response = res as { data?: TwinStatus };
                    if (response.data) setStatus(response.data);
                })
                .catch(() => setStatus(null));
        };

        checkStatus();
        const interval = setInterval(checkStatus, 10000);
        return () => clearInterval(interval);
    }, [mode]);

    if (!status) return null;

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            background: 'rgba(15,23,42,0.6)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '12px',
            fontSize: '11px',
            color: '#94a3b8'
        }}>
            <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: status.online ? '#10b981' : '#ef4444',
                boxShadow: status.online ? '0 0 8px rgba(16, 185, 129, 0.5)' : 'none'
            }} />
            <span>{status.online ? `Twin Online (${status.twinId || mode})` : 'Twin Offline'}</span>
        </div>
    );
};

export default DigitalTwinStatus;
