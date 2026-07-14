/**
 * Nepali Language Selector — Language preference for Nepal governance
 * Supports Nepali (नेपाली), English, Hindi, and other regional languages.
 * Now backed by the i18n system with full translation dictionaries.
 */
import React from 'react';
import { useI18n, LANGUAGES, LanguageCode } from '../../i18n';

interface NepaliLanguageSelectorProps {
    currentLanguage?: string;
    onLanguageChange?: (code: string) => void;
}

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    padding: 16,
};

export default function NepaliLanguageSelector({ currentLanguage, onLanguageChange }: NepaliLanguageSelectorProps) {
    const { t, locale, setLocale } = useI18n();
    const [showAll, setShowAll] = React.useState(false);

    const selected = (currentLanguage as LanguageCode) || locale;
    const displayed = showAll ? LANGUAGES : LANGUAGES.slice(0, 3);

    const handleSelect = (code: LanguageCode) => {
        setLocale(code);
        if (onLanguageChange) onLanguageChange(code);
    };

    return (
        <div style={{ padding: 16, maxWidth: 500, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#8b5cf6', marginBottom: 4 }}>
                🌐 {t('language.title')}
            </div>
            <div style={{ fontSize: '0.75rem', opacity: 0.5, marginBottom: 16 }}>
                {t('language.subtitle')}
            </div>

            {/* Current Selection */}
            <div style={CARD}>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    {t('language.current')}
                </div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: 12,
                    background: 'rgba(139,92,246,0.1)',
                    borderRadius: 8,
                    border: '1px solid rgba(139,92,246,0.3)',
                }}>
                    <span style={{ fontSize: '1.5rem' }}>
                        {LANGUAGES.find(l => l.code === selected)?.flag || '🌐'}
                    </span>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                            {LANGUAGES.find(l => l.code === selected)?.name || 'English'}
                        </div>
                        <div style={{ fontSize: '0.78rem', opacity: 0.6 }}>
                            {LANGUAGES.find(l => l.code === selected)?.nativeName || 'English'}
                        </div>
                    </div>
                </div>
            </div>

            {/* Language Grid */}
            <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    {t('language.available')}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {displayed.map(lang => (
                        <div
                            key={lang.code}
                            onClick={() => handleSelect(lang.code)}
                            style={{
                                ...CARD,
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                border: `1px solid ${selected === lang.code ? '#8b5cf666' : 'rgba(255,255,255,0.08)'}`,
                                background: selected === lang.code ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.04)',
                                transition: 'all 0.15s',
                            }}
                            onMouseEnter={e => { if (selected !== lang.code) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.08)'; }}
                            onMouseLeave={e => { if (selected !== lang.code) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'; }}
                        >
                            <span style={{ fontSize: '1.3rem' }}>{lang.flag}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{lang.name}</div>
                                <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>{lang.nativeName}</div>
                            </div>
                            {selected === lang.code && (
                                <span style={{ color: '#8b5cf6', fontSize: '1.1rem' }}>✓</span>
                            )}
                        </div>
                    ))}
                </div>

                {LANGUAGES.length > 3 && (
                    <div
                        onClick={() => setShowAll(!showAll)}
                        style={{
                            textAlign: 'center',
                            padding: '8px',
                            marginTop: 8,
                            cursor: 'pointer',
                            color: '#8b5cf6',
                            fontSize: '0.78rem',
                            opacity: 0.7,
                        }}
                    >
                        {showAll
                            ? t('language.show_less')
                            : t('language.show_all', { count: LANGUAGES.length })
                        }
                    </div>
                )}
            </div>

            {/* Language Info */}
            <div style={{ ...CARD, marginTop: 16 }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#94a3b8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    ℹ️ {t('language.info_title')}
                </div>
                <div style={{ fontSize: '0.75rem', opacity: 0.7, lineHeight: 1.6 }}>
                    {t('language.info_desc')}
                </div>
            </div>
        </div>
    );
}
