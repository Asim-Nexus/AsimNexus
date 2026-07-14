import React from 'react';

interface CloneInfo {
    name: string;
    online: boolean;
}

interface CloneStatusProps {
    clones: CloneInfo[];
}

const CloneStatus: React.FC<CloneStatusProps> = ({ clones }) => {
    return (
        <div style={styles.container}>
            <h4 style={styles.title}>15 Founder Clones Status</h4>
            <div style={styles.grid}>
                {clones.map((clone, i) => (
                    <div key={i} style={styles.cloneCard}>
                        <div style={{ ...styles.dot, background: clone.online ? '#10b981' : '#ef4444' }}></div>
                        <span style={styles.name}>{clone.name}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

const styles: Record<string, React.CSSProperties> = {
    container: { padding: '10px', background: '#0f172a', borderRadius: '8px', border: '1px solid #1e293b' },
    title: { margin: '0 0 10px 0', fontSize: '13px', color: '#94a3b8' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '8px' },
    cloneCard: { display: 'flex', alignItems: 'center', gap: '8px', background: '#1e293b', padding: '6px 10px', borderRadius: '4px', border: '1px solid #334155' },
    dot: { width: '8px', height: '8px', borderRadius: '50%' },
    name: { fontSize: '12px', color: '#cbd5e1' }
};

export default CloneStatus;
