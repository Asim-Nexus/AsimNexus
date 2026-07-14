/**
 * AsimNexus I18nProvider
 * Lightweight i18n context for Nepal governance multi-language support
 * Languages: English (en), Nepali (ne), Hindi (hi)
 */
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { translations, LANGUAGES, LanguageCode, TranslationDict } from './translations';

// ── Types ─────────────────────────────────────────────────────────────────────

interface I18nContextValue {
    /** Current language code */
    locale: LanguageCode;
    /** Set current language */
    setLocale: (code: LanguageCode) => void;
    /** Translate a dot-separated key (e.g. 'app.name', 'identity.title') */
    t: (key: string, params?: Record<string, string | number>) => string;
    /** Get all available languages */
    languages: typeof LANGUAGES;
    /** Get current language metadata */
    currentLanguage: typeof LANGUAGES[0] | undefined;
}

// ── Context ───────────────────────────────────────────────────────────────────

const I18nContext = createContext<I18nContextValue | null>(null);

// ── Helper: deep get with dot notation ────────────────────────────────────────

function deepGet(obj: TranslationDict, path: string): string | TranslationDict | undefined {
    const keys = path.split('.');
    let current: TranslationDict | string | undefined = obj;
    for (const key of keys) {
        if (typeof current === 'object' && current !== null && key in current) {
            current = (current as TranslationDict)[key];
        } else {
            return undefined;
        }
    }
    return current;
}

// ── Helper: simple interpolation ──────────────────────────────────────────────

function interpolate(template: string, params?: Record<string, string | number>): string {
    if (!params) return template;
    return template.replace(/\{(\w+)\}/g, (_, key) => {
        const val = params[key];
        return val !== undefined ? String(val) : `{${key}}`;
    });
}

// ── Provider ──────────────────────────────────────────────────────────────────

interface I18nProviderProps {
    children: ReactNode;
    defaultLocale?: LanguageCode;
}

export function I18nProvider({ children, defaultLocale = 'en' }: I18nProviderProps) {
    const [locale, setLocaleState] = useState<LanguageCode>(() => {
        // Try to restore saved preference
        const saved = localStorage.getItem('asimnexus_locale') as LanguageCode | null;
        if (saved && (saved === 'en' || saved === 'ne' || saved === 'hi')) {
            return saved;
        }
        return defaultLocale;
    });

    const setLocale = useCallback((code: LanguageCode) => {
        setLocaleState(code);
        localStorage.setItem('asimnexus_locale', code);
    }, []);

    const t = useCallback((key: string, params?: Record<string, string | number>): string => {
        const dict = translations[locale];
        const result = deepGet(dict, key);
        if (typeof result === 'string') {
            return interpolate(result, params);
        }
        // Fallback to English
        const enResult = deepGet(translations.en, key);
        if (typeof enResult === 'string') {
            return interpolate(enResult, params);
        }
        // Last resort: return the key itself
        return key;
    }, [locale]);

    const currentLanguage = LANGUAGES.find(l => l.code === locale);

    return (
        <I18nContext.Provider value={{
            locale,
            setLocale,
            t,
            languages: LANGUAGES,
            currentLanguage,
        }}>
            {children}
        </I18nContext.Provider>
    );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useI18n(): I18nContextValue {
    const context = useContext(I18nContext);
    if (!context) {
        throw new Error('useI18n must be used within an I18nProvider');
    }
    return context;
}
