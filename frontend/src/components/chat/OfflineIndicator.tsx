// components/chat/OfflineIndicator.tsx
// Pulsing offline/online badge shown in the chat header

import React from 'react';

interface OfflineIndicatorProps {
    isOnline: boolean;
    queueLength?: number;
}

const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({ isOnline, queueLength = 0 }) => {
    return (
        <div
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 12px',
                borderRadius: '999px',
                fontSize: '12px',
                fontWeight: 600,
                letterSpacing: '0.03em',
                background: isOnline
                    ? 'rgba(34, 197, 94, 0.15)'
                    : 'rgba(239, 68, 68, 0.15)',
                color: isOnline ? '#22c55e' : '#ef4444',
                border: `1px solid ${isOnline ? '#22c55e44' : '#ef444444'}`,
                transition: 'all 0.4s ease',
                userSelect: 'none',
            }}
        >
            <span
                style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: isOnline ? '#22c55e' : '#ef4444',
                    display: 'inline-block',
                    animation: isOnline ? 'none' : 'pulse-dot 1.4s ease-in-out infinite',
                    boxShadow: isOnline
                        ? '0 0 6px #22c55e'
                        : '0 0 6px #ef4444',
                }}
            />
            {isOnline ? 'Online' : `Offline${queueLength > 0 ? ` · ${queueLength} queued` : ''}`}

            <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.7); }
        }
      `}</style>
        </div>
    );
};

export default OfflineIndicator;
