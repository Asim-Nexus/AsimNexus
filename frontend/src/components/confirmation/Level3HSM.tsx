import React, { useState } from 'react';

interface Intent {
    action: string;
    sub_action: string;
}

interface Level3HSMProps {
    onConfirm: (data: { level: number; method: string; token: string }) => void;
    onCancel: () => void;
    intent: Intent;
}

const Level3HSM: React.FC<Level3HSMProps> = ({ onConfirm, onCancel, intent }) => {
    const [status, setStatus] = useState<'waiting' | 'touching' | 'verified'>('waiting');

    const handleSimulateTouch = () => {
        setStatus('touching');
        setTimeout(() => {
            setStatus('verified');
            setTimeout(() => {
                onConfirm({ level: 3, method: 'hsm', token: 'yubikey_signed_blob' });
            }, 1000);
        }, 1500);
    };

    return (
        <div style={styles.container}>
            <h3 style={styles.title}>🔐 Security Level 3 (HSM)</h3>
            <p style={styles.text}>Action: {intent.action} / {intent.sub_action}</p>
            <p style={styles.text}>
                This is a critical government/constitutional action. <br />
                Please insert your Hardware Security Module (YubiKey) and touch the sensor.
            </p>

            <div style={styles.hsmBox} onClick={status === 'waiting' ? handleSimulateTouch : undefined}>
                {status === 'waiting' && <span style={styles.pulsing}>👉 Touch your security key</span>}
                {status === 'touching' && <span style={{ color: '#fbbf24' }}>⏳ Verifying cryptography...</span>}
                {status === 'verified' && <span style={{ color: '#10b981' }}>✅ Signature Verified</span>}
            </div>

            <div style={styles.actions}>
                <button type="button" onClick={onCancel} style={styles.btnCancel}>Cancel</button>
            </div>
        </div>
    );
};

const styles: Record<string, React.CSSProperties> = {
    container: { background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid rgba(220, 38, 38, 0.5)', color: '#fff' },
    title: { margin: '0 0 10px 0', fontSize: '16px', color: '#f87171' },
    text: { margin: '0 0 15px 0', fontSize: '13px', color: '#94a3b8' },
    hsmBox: {
        height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#0f172a', border: '2px dashed #475569', borderRadius: '8px', cursor: 'pointer',
        marginBottom: '15px',
    },
    pulsing: {
        animation: 'pulse 1.5s infinite', color: '#38bdf8',
    },
    actions: { display: 'flex', justifyContent: 'flex-end', gap: '10px' },
    btnCancel: { padding: '8px 16px', background: 'transparent', border: '1px solid #475569', color: '#cbd5e1', borderRadius: '6px', cursor: 'pointer' },
};

export default Level3HSM;
