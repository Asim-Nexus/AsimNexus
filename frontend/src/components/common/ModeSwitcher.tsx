// components/common/ModeSwitcher.tsx
// Toggles between Citizen / Company / Government modes with animated pill indicator

import React from 'react';

interface Mode {
    id: string;
    label: string;
    icon: string;
    color: string;
}

interface ModeSwitcherProps {
    mode?: string;
    onModeChange?: (mode: string) => void;
}

const MODES: Mode[] = [
    { id: 'citizen', label: 'Citizen', icon: '\u{1F3E0}', color: '#8b5cf6' },
    { id: 'company', label: 'Company', icon: '\u{1F3E2}', color: '#3b82f6' },
    { id: 'government', label: 'Government', icon: '\u{1F3DB}\uFE0F', color: '#10b981' },
];

const ModeSwitcher: React.FC<ModeSwitcherProps> = ({ mode = 'citizen', onModeChange = () => { } }) => {
    return (
        <div
            role="tablist"
            aria-label="Operation Mode"
            style={{
                display: 'inline-flex',
                background: 'rgba(15,23,42,0.7)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '999px',
                padding: '4px',
                gap: '2px',
                backdropFilter: 'blur(12px)',
            }}
        >
            {MODES.map(m => {
                const active = mode === m.id;
                return (
                    <button
                        key={m.id}
                        role="tab"
                        aria-selected={active}
                        onClick={() => onModeChange(m.id)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '6px 16px',
                            borderRadius: '999px',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '13px',
                            fontWeight: active ? 700 : 500,
                            color: active ? '#fff' : '#64748b',
                            background: active
                                ? `linear-gradient(135deg, ${m.color}cc, ${m.color}88)`
                                : 'transparent',
                            boxShadow: active ? `0 2px 12px ${m.color}55` : 'none',
                            transition: 'all 0.25s ease',
                            outline: 'none',
                            whiteSpace: 'nowrap',
                        }}
                    >
                        <span>{m.icon}</span>
                        <span>{m.label}</span>
                    </button>
                );
            })}
        </div>
    );
};

export default ModeSwitcher;
