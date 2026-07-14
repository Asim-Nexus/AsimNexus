// components/chat/ActionChip.tsx
// Quick-action suggestion pills shown below the input bar

import React from 'react';

interface ChipColor {
    bg: string;
    border: string;
    text: string;
}

interface ActionChipProps {
    label: string;
    onClick: (label: string) => void;
    mode?: 'citizen' | 'company' | 'government';
    icon?: string;
}

const CHIP_COLORS: Record<string, ChipColor> = {
    citizen: { bg: 'rgba(139,92,246,0.15)', border: '#8b5cf644', text: '#c4b5fd' },
    company: { bg: 'rgba(59,130,246,0.15)', border: '#3b82f644', text: '#93c5fd' },
    government: { bg: 'rgba(16,185,129,0.15)', border: '#10b98144', text: '#6ee7b7' },
};

const ActionChip: React.FC<ActionChipProps> = ({ label, onClick, mode = 'citizen', icon }) => {
    const colors = CHIP_COLORS[mode] || CHIP_COLORS.citizen;

    return (
        <button
            onClick={() => onClick(label)}
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '999px',
                border: `1px solid ${colors.border}`,
                background: colors.bg,
                color: colors.text,
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s ease',
                outline: 'none',
                backdropFilter: 'blur(8px)',
            }}
            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = `0 4px 14px ${colors.border}`;
            }}
            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
            }}
        >
            {icon && <span style={{ fontSize: '15px' }}>{icon}</span>}
            {label}
        </button>
    );
};

export default ActionChip;
