import React from 'react';

interface Vote {
    role: string;
    choice: 'APPROVE' | 'REJECT';
}

interface CloneVotingCardProps {
    proposal: string;
    votes: Vote[];
}

const CloneVotingCard: React.FC<CloneVotingCardProps> = ({ proposal, votes }) => {
    const totalVotes = votes.length;
    const approved = votes.filter(v => v.choice === 'APPROVE').length;
    const rejected = votes.filter(v => v.choice === 'REJECT').length;

    const progress = (totalVotes / 15) * 100;
    const passed = approved >= 8;

    return (
        <div style={styles.card}>
            <div style={styles.header}>
                <h4 style={styles.title}>🏛️ Constitutional AI Consensus</h4>
                <span style={styles.badge}>{passed ? '✅ Passed (8/15)' : '⏳ Voting in Progress'}</span>
            </div>

            <p style={styles.proposal}><strong>Topic:</strong> {proposal}</p>

            <div style={styles.progressBarBg}>
                <div style={{ ...styles.progressBarFill, width: `${progress}%` }}></div>
            </div>

            <div style={styles.stats}>
                <span>Votes Cast: {totalVotes}/15</span>
                <span style={{ color: '#10b981' }}>Approve: {approved}</span>
                <span style={{ color: '#ef4444' }}>Reject: {rejected}</span>
            </div>

            <div style={styles.voteList}>
                {votes.map((v, i) => (
                    <div key={i} style={styles.voteItem}>
                        <span style={styles.role}>{v.role}</span>
                        <span style={v.choice === 'APPROVE' ? styles.approve : styles.reject}>
                            {v.choice}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};

const styles: Record<string, React.CSSProperties> = {
    card: { background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '15px', color: '#f8fafc', marginBottom: '15px' },
    header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' },
    title: { margin: 0, fontSize: '14px', color: '#e2e8f0' },
    badge: { fontSize: '12px', padding: '4px 8px', background: '#0f172a', borderRadius: '4px', border: '1px solid #475569' },
    proposal: { fontSize: '13px', color: '#94a3b8', margin: '0 0 10px 0' },
    progressBarBg: { height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden', marginBottom: '10px' },
    progressBarFill: { height: '100%', background: '#3b82f6', transition: 'width 0.3s ease' },
    stats: { display: 'flex', gap: '15px', fontSize: '12px', color: '#cbd5e1', marginBottom: '10px' },
    voteList: { display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '120px', overflowY: 'auto', borderTop: '1px solid #334155', paddingTop: '10px' },
    voteItem: { display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '4px', background: '#0f172a', borderRadius: '4px' },
    role: { color: '#94a3b8' },
    approve: { color: '#10b981', fontWeight: 'bold' },
    reject: { color: '#ef4444', fontWeight: 'bold' }
};

export default CloneVotingCard;
