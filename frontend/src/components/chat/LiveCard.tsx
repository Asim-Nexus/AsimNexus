// components/chat/LiveCard.tsx
// Step-by-step execution progress card shown during orchestrator processing

import React from 'react';

interface Step {
    id?: string;
    name?: string;
    action?: string;
    detail?: string;
    status: 'pending' | 'running' | 'done' | 'failed' | 'vetoed' | 'consensus';
}

interface StepRowProps {
    step: Step;
    index: number;
}

interface LiveCardProps {
    steps?: Step[];
    auditId?: string;
    isVisible?: boolean;
}

const STATUS_ICON: Record<string, { icon: string; color: string }> = {
    pending: { icon: '⏳', color: '#94a3b8' },
    running: { icon: '⚡', color: '#f59e0b' },
    done: { icon: '✅', color: '#22c55e' },
    failed: { icon: '❌', color: '#ef4444' },
    vetoed: { icon: '🛡️', color: '#a78bfa' },
    consensus: { icon: '🤝', color: '#38bdf8' },
};

function StepRow({ step, index }: StepRowProps) {
    const meta = STATUS_ICON[step.status] || STATUS_ICON.pending;
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                padding: '8px 12px',
                borderRadius: '10px',
                background: step.status === 'running'
                    ? 'rgba(245,158,11,0.08)'
                    : 'rgba(255,255,255,0.03)',
                transition: 'background 0.3s ease',
                animation: step.status === 'running' ? 'pulse-bg 1.5s ease-in-out infinite' : 'none',
            }}
        >
            <span style={{ fontSize: '16px', lineHeight: 1.4 }}>{meta.icon}</span>
            <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>
                    Step {index + 1}: {step.name || step.action || 'Processing…'}
                </div>
                {step.detail && (
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: 2 }}>{step.detail}</div>
                )}
            </div>
            <span style={{ fontSize: '11px', fontWeight: 700, color: meta.color, textTransform: 'uppercase' }}>
                {step.status}
            </span>
        </div>
    );
}

const LiveCard: React.FC<LiveCardProps> = ({ steps = [], auditId, isVisible }) => {
    if (!isVisible || steps.length === 0) return null;

    return (
        <div
            style={{
                margin: '8px 0',
                padding: '14px',
                borderRadius: '16px',
                background: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid rgba(139,92,246,0.25)',
                backdropFilter: 'blur(16px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                animation: 'fade-in 0.3s ease',
            }}
        >
            <div style={{
                fontSize: '12px',
                fontWeight: 700,
                color: '#8b5cf6',
                marginBottom: 10,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                display: 'flex',
                justifyContent: 'space-between',
            }}>
                <span>⚙️ Orchestrator Live View</span>
                {auditId && (
                    <span style={{ color: '#475569', fontWeight: 400, fontSize: '10px', letterSpacing: '0.04em' }}>
                        audit: {auditId.slice(0, 12)}…
                    </span>
                )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {steps.map((step, i) => (
                    <StepRow key={step.id || i} step={step} index={i} />
                ))}
            </div>

            <style>{`
        @keyframes pulse-bg {
          0%, 100% { background: rgba(245,158,11,0.08); }
          50% { background: rgba(245,158,11,0.18); }
        }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </div>
    );
};

export default LiveCard;
