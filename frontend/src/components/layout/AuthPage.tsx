/**
 * AsimNexus Auth Page — Register & Login
 * Every person creates their own Personal OS here.
 */
import React, { useState } from 'react';
import { authAPI } from '../../api/asimnexus';

interface Country {
    code: string;
    name: string;
}

const COUNTRIES: Country[] = [
    { code: 'NP', name: 'Nepal 🇳🇵' },
    { code: 'IN', name: 'India 🇮🇳' },
    { code: 'US', name: 'USA 🇺🇸' },
    { code: 'GB', name: 'UK 🇬🇧' },
    { code: 'DE', name: 'Germany 🇩🇪' },
    { code: 'JP', name: 'Japan 🇯🇵' },
    { code: 'CN', name: 'China 🇨🇳' },
    { code: 'BR', name: 'Brazil 🇧🇷' },
    { code: 'NG', name: 'Nigeria 🇳🇬' },
    { code: 'XX', name: 'Other 🌍' },
];

interface AuthForm {
    displayName: string;
    email: string;
    password: string;
    confirmPassword: string;
    phone: string;
    countryCode: string;
    nationalId: string;
}

interface AuthPageProps {
    onAuthSuccess: (user: Record<string, unknown>, token: string) => void;
}

interface InputProps {
    label: string;
    type?: string;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    required?: boolean;
}

function Input({ label, type = 'text', value, onChange, placeholder, required }: InputProps) {
    return (
        <div style={styles.field}>
            <label style={styles.label}>{label}</label>
            <input style={styles.input} type={type} value={value} placeholder={placeholder}
                required={required} onChange={e => onChange(e.target.value)} />
        </div>
    );
}

export default function AuthPage({ onAuthSuccess }: AuthPageProps) {
    const [mode, setMode] = useState<'login' | 'register'>('login');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [form, setForm] = useState<AuthForm>({
        displayName: '', email: '', password: '', confirmPassword: '',
        phone: '', countryCode: 'NP', nationalId: '',
    });

    const set = (k: keyof AuthForm, v: string) => setForm(f => ({ ...f, [k]: v }));

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(''); setLoading(true);
        try {
            const res = await authAPI.login(form.email, form.password) as unknown as { success: boolean; user: Record<string, unknown>; token: string; error?: string };
            if (res.success) { onAuthSuccess(res.user, res.token); }
            else { setError(res.error || 'Login failed'); }
        } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr.response?.data?.detail || 'Cannot connect to backend');
        }
        setLoading(false);
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (form.password !== form.confirmPassword) {
            setError('Passwords do not match'); return;
        }
        setLoading(true);
        try {
            const res = await authAPI.register(
                form.displayName, form.email, form.password,
                form.phone || null, form.countryCode, form.nationalId || null
            ) as unknown as { success: boolean; user: Record<string, unknown>; token: string; error?: string };
            if (res.success) { onAuthSuccess(res.user, res.token); }
            else { setError(res.error || 'Registration failed'); }
        } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr.response?.data?.detail || 'Cannot connect to backend');
        }
        setLoading(false);
    };

    return (
        <div style={styles.overlay}>
            <div style={styles.card}>
                {/* Header */}
                <div style={styles.header}>
                    <img src="/asim-logo.png" alt="AsimNexus Logo" style={styles.logoImage} />
                    <h1 style={styles.title}>AsimNexus</h1>
                    <p style={styles.subtitle}>Your Personal World OS</p>
                </div>

                {/* Tab Switch */}
                <div style={styles.tabs}>
                    <button style={{ ...styles.tab, ...(mode === 'login' ? styles.tabActive : {}) }}
                        onClick={() => { setMode('login'); setError(''); }}>Login</button>
                    <button style={{ ...styles.tab, ...(mode === 'register' ? styles.tabActive : {}) }}
                        onClick={() => { setMode('register'); setError(''); }}>Create Account</button>
                </div>

                {error && <div style={styles.error}>{error}</div>}

                {/* Login Form */}
                {mode === 'login' && (
                    <form onSubmit={handleLogin} style={styles.form}>
                        <Input label="Email" type="email" value={form.email}
                            onChange={v => set('email', v)} placeholder="you@email.com" />
                        <Input label="Password" type="password" value={form.password}
                            onChange={v => set('password', v)} placeholder="••••••••" />
                        <button type="submit" style={styles.btn} disabled={loading}>
                            {loading ? 'Logging in...' : 'Login to Your OS'}
                        </button>
                        <p style={styles.hint}>New here? <span style={styles.link}
                            onClick={() => setMode('register')}>Create your Personal OS →</span></p>
                    </form>
                )}

                {/* Register Form */}
                {mode === 'register' && (
                    <form onSubmit={handleRegister} style={styles.form}>
                        <Input label="Your Name" value={form.displayName}
                            onChange={v => set('displayName', v)} placeholder="Ram Bahadur" required />
                        <Input label="Email" type="email" value={form.email}
                            onChange={v => set('email', v)} placeholder="you@email.com" required />
                        <Input label="Phone (optional)" type="tel" value={form.phone}
                            onChange={v => set('phone', v)} placeholder="+977-9800000000" />
                        <div style={styles.field}>
                            <label style={styles.label}>Country</label>
                            <select style={styles.select} value={form.countryCode}
                                onChange={e => set('countryCode', e.target.value)}>
                                {COUNTRIES.map(c => (
                                    <option key={c.code} value={c.code}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                        <Input label="National ID (optional — ZKP hashed)" value={form.nationalId}
                            onChange={v => set('nationalId', v)} placeholder="Never stored raw — privacy protected" />
                        <Input label="Password" type="password" value={form.password}
                            onChange={v => set('password', v)} placeholder="Min 8 characters" required />
                        <Input label="Confirm Password" type="password" value={form.confirmPassword}
                            onChange={v => set('confirmPassword', v)} placeholder="Repeat password" required />
                        <div style={styles.privacyNote}>
                            🔒 Your data stays on your device. National ID is SHA-256 hashed — never stored raw.
                        </div>
                        <button type="submit" style={styles.btn} disabled={loading}>
                            {loading ? 'Creating your OS...' : '🚀 Create My Personal OS'}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    overlay: {
        minHeight: '100vh', display: 'flex', alignItems: 'center',
        justifyContent: 'center', background: 'transparent',
        padding: '20px',
    },
    card: {
        background: 'rgba(26, 26, 46, 0.1)', backdropFilter: 'blur(3px)',
        WebkitBackdropFilter: 'blur(3px)',
        border: '1px solid rgba(102,126,234,0.3)', borderRadius: '24px',
        padding: '40px', width: '100%', maxWidth: '480px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    },
    header: { textAlign: 'center', marginBottom: '28px' },
    logoImage: { width: '100px', height: '100px', objectFit: 'contain', marginBottom: '16px', borderRadius: '50%', background: 'rgba(26, 26, 46, 0.3)', padding: '12px' },
    title: { color: '#fff', fontSize: '28px', fontWeight: '700', margin: '0 0 6px' },
    subtitle: { color: 'rgba(255,255,255,0.5)', fontSize: '14px', margin: 0 },
    tabs: {
        display: 'flex', gap: '8px', marginBottom: '24px', background: 'rgba(0,0,0,0.3)',
        borderRadius: '10px', padding: '4px'
    },
    tab: {
        flex: 1, padding: '10px', borderRadius: '8px', border: 'none',
        cursor: 'pointer', fontSize: '14px', fontWeight: '600',
        background: 'transparent', color: 'rgba(255,255,255,0.5)', transition: 'all 0.2s'
    },
    tabActive: { background: 'linear-gradient(135deg, #667eea, #764ba2)', color: '#fff' },
    form: { display: 'flex', flexDirection: 'column', gap: '16px' },
    field: { display: 'flex', flexDirection: 'column', gap: '6px' },
    label: { color: 'rgba(255,255,255,0.7)', fontSize: '13px', fontWeight: '500' },
    input: {
        background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
        borderRadius: '10px', padding: '12px 14px', color: '#fff', fontSize: '14px',
        outline: 'none', width: '100%', boxSizing: 'border-box',
    },
    select: {
        background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
        borderRadius: '10px', padding: '12px 14px', color: '#fff', fontSize: '14px',
        outline: 'none', width: '100%',
    },
    btn: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: '#fff', border: 'none', borderRadius: '12px',
        padding: '14px', fontSize: '15px', fontWeight: '700',
        cursor: 'pointer', marginTop: '8px', transition: 'opacity 0.2s',
    },
    error: {
        background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)',
        borderRadius: '10px', padding: '12px', color: '#fca5a5',
        fontSize: '13px', marginBottom: '8px', textAlign: 'center',
    },
    privacyNote: {
        background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)',
        borderRadius: '8px', padding: '10px', color: 'rgba(134,239,172,0.9)',
        fontSize: '12px',
    },
    hint: { textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '13px', margin: '4px 0 0' },
    link: { color: '#667eea', cursor: 'pointer', fontWeight: '600' },
};
