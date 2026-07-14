import React, { useState } from 'react';

interface Intent {
    action: string;
    sub_action: string;
}

interface Level2MFAProps {
    onConfirm: (data: { level: number; method: string; token: string }) => void;
    onCancel: () => void;
    intent: Intent;
}

const Level2MFA: React.FC<Level2MFAProps> = ({ onConfirm, onCancel, intent }) => {
    const [totp, setTotp] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (totp.length === 6) {
            onConfirm({ level: 2, method: 'totp', token: totp });
        }
    };

    return (
        <div style={styles.container}>
            <h3 style={styles.title}>🛡️ Security Level 2 (MFA)</h3>
            <p style={styles.text}>Action: {intent.action} / {intent.sub_action}</p>
            <p style={styles.text}>Enter the code from your Authenticator app.</p>
            <form onSubmit={handleSubmit} style={styles.form}>
                <input
                    type="text"
                    value={totp}
                    onChange={(e) => setTotp(e.target.value.replace(/\D/g, '').substring(0, 6))}
                    placeholder="000 000"
                    style={styles.input}
                    autoFocus
                />
                <div style={styles.actions}>
                    <button type="button" onClick={onCancel} style={styles.btnCancel}>Cancel</button>
                    <button type="submit" disabled={totp.length !== 6} style={styles.btnConfirm}>Verify MFA</button>
                </div>
            </form>
        </div>
    );
};

const styles: Record<string, React.CSSProperties> = {
    container: { background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' },
    title: { margin: '0 0 10px 0', fontSize: '16px', color: '#818cf8' },
    text: { margin: '0 0 15px 0', fontSize: '13px', color: '#94a3b8' },
    form: { display: 'flex', flexDirection: 'column', gap: '15px' },
    input: { padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#fff', fontSize: '16px', letterSpacing: '4px', textAlign: 'center' },
    actions: { display: 'flex', justifyContent: 'flex-end', gap: '10px' },
    btnCancel: { padding: '8px 16px', background: 'transparent', border: '1px solid #475569', color: '#cbd5e1', borderRadius: '6px', cursor: 'pointer' },
    btnConfirm: { padding: '8px 16px', background: '#6366f1', border: 'none', color: '#fff', borderRadius: '6px', cursor: 'pointer' },
};

export default Level2MFA;
