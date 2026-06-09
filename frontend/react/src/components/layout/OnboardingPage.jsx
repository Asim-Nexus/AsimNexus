/**
 * AsimNexus Onboarding Page
 * Chat-driven step-by-step onboarding with device scan, biometric, role selection,
 * 51%/49% agreement, policies, and Personal Universe creation.
 */
import React, { useState, useEffect, useRef } from 'react';
import { authAPI } from '../../api/asimnexus';

const STEPS = [
  { id: 'welcome', title: 'Welcome to AsimNexus', desc: 'Multiversal Autonomous Operating System' },
  { id: 'language', title: 'Language & Region', desc: 'Choose your preferred language' },
  { id: 'device_scan', title: 'Device Intelligence Scan', desc: 'Auto-detect hardware & software' },
  { id: 'identity', title: 'Identity Verification', desc: 'Biometric + Document + ZKP' },
  { id: 'role', title: 'Role Selection', desc: 'Personal / Company / Community / Government' },
  { id: 'agreement', title: '51% / 49% Partnership', desc: 'Sovereign control & partnership agreement' },
  { id: 'policies', title: 'Policies & Permissions', desc: 'Data, Mesh, Dharma rules' },
  { id: 'universe', title: 'Personal Universe', desc: 'Import data, skills, preferences' },
  { id: 'confirm', title: 'Final 3 Confirmation', desc: 'Review & biometric approve' },
  { id: 'activation', title: 'Activation', desc: 'Your Asim Orb is ready' },
];

const LANGUAGES = [
  { code: 'ne', name: 'नेपाली', flag: '🇳🇵' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
];

const ROLES = [
  { id: 'personal', icon: '👤', label: 'Personal', desc: '100% control of your life & data', color: '#667eea' },
  { id: 'company', icon: '🏢', label: 'Company', desc: '49% Partnership — Enterprise Universe', color: '#3b82f6' },
  { id: 'community', icon: '🏘️', label: 'Community', desc: 'Shared Mesh — Village/Community level', color: '#f59e0b' },
  { id: 'government', icon: '🏛️', label: 'Government', desc: '51% Sovereign — National Layer', color: '#c9a84c' },
];

const POLICIES = [
  { id: 'local_first', label: 'Local-First Data', desc: 'My data stays on my device primarily' },
  { id: 'mesh_share', label: 'Mesh Resource Sharing', desc: 'Share 2-5% compute/storage with mesh' },
  { id: 'dharma_bind', label: 'Dharma-Chakra Bind', desc: 'Accept immutable ethical constitution' },
  { id: 'zkp_verify', label: 'Zero-Knowledge Proof', desc: 'Verify identity without exposing data' },
  { id: 'final3_confirm', label: 'Final 3 Confirmation', desc: 'Biometric approval for critical actions' },
  { id: 'dream_learn', label: 'Dreaming Engine Learn', desc: 'Allow background AI optimization' },
];

function simulateDeviceScan() {
  const hw = [
    { name: 'CPU', value: navigator.hardwareConcurrency ? `${navigator.hardwareConcurrency} cores` : 'Unknown', status: '✅' },
    { name: 'RAM', value: navigator.deviceMemory ? `~${navigator.deviceMemory} GB` : 'Unknown', status: '✅' },
    { name: 'GPU', value: 'WebGL Detected', status: '✅' },
    { name: 'Network', value: navigator.connection?.effectiveType || 'Unknown', status: '✅' },
    { name: 'Screen', value: `${window.screen.width}x${window.screen.height}`, status: '✅' },
    { name: 'OS', value: navigator.platform, status: '✅' },
  ];
  return hw;
}

export default function OnboardingPage({ onComplete }) {
  const [step, setStep] = useState(0);
  const [lang, setLang] = useState('ne');
  const [role, setRole] = useState('personal');
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [scanned, setScanned] = useState(false);
  const [policiesAccepted, setPoliciesAccepted] = useState({});
  const [bioVerified, setBioVerified] = useState(false);
  const [form, setForm] = useState({ displayName: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const timerRef = useRef(null);

  const t = {
    ne: {
      next: 'अगाडि जानुहोस्', back: 'पछाडि जानुहोस्', start: 'सुरु गर्नुहोस्',
      scan: 'स्क्यान गर्नुहोस्', scanning: 'स्क्यान हुँदैछ...', done: 'सकियो',
      welcome: 'AsimNexus मा स्वागत छ', install: 'यो संसारको पहिलो Multiversal Autonomous Operating System हो।',
      selectLang: 'भाषा छान्नुहोस्', selectRole: 'आफ्नो भूमिका छान्नुहोस्',
      agreementTitle: '51% / 49% Partnership Agreement',
      agreementText: 'सरकार ले Sovereign Layer चलाउँदा ५१% नियन्त्रण राख्छ। कम्पनी/कम्युनिटी ले ४९% Partnership मा चलाउँछ। Dharma-Chakra सबैलाई बाँध्छ।',
      accept: 'म स्वीकृत गर्छु', policiesTitle: 'Policies & Permissions',
      identityTitle: 'Biometric + Identity', verifyBio: 'Biometric Verify गर्नुहोस्',
      final3Title: 'Final 3 Confirmation', activate: 'Asim Orb सक्रिय गर्नुहोस्',
    },
    en: {
      next: 'Next', back: 'Back', start: 'Get Started',
      scan: 'Scan Device', scanning: 'Scanning...', done: 'Complete',
      welcome: 'Welcome to AsimNexus', install: 'The world\'s first Multiversal Autonomous Operating System.',
      selectLang: 'Select Language', selectRole: 'Select Your Role',
      agreementTitle: '51% / 49% Partnership Agreement',
      agreementText: 'Government retains 51% Sovereign Control over the National Layer. Companies/Communities operate under 49% Partnership. All bound by Dharma-Chakra.',
      accept: 'I Accept', policiesTitle: 'Policies & Permissions',
      identityTitle: 'Biometric + Identity', verifyBio: 'Verify Biometric',
      final3Title: 'Final 3 Confirmation', activate: 'Activate Asim Orb',
    },
  }[lang];

  useEffect(() => {
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, []);

  const handleScan = () => {
    setScanned(false);
    setLoading(true);
    timerRef.current = setTimeout(() => {
      setDeviceInfo(simulateDeviceScan());
      setScanned(true);
      setLoading(false);
    }, 2000);
  };

  const handleRegister = async () => {
    setLoading(true);
    try {
      const res = await authAPI.register(
        form.displayName, form.email, form.password,
        null, 'NP', null
      );
      if (res.success) { onComplete(res.user, res.token); }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const renderStep = () => {
    const s = STEPS[step];
    switch (s.id) {
      case 'welcome':
        return (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{ fontSize: 72, marginBottom: 20 }}>🌌</div>
            <h1 style={{ fontSize: '2rem', marginBottom: 12, background: 'linear-gradient(135deg,#667eea,#764ba2)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{t.welcome}</h1>
            <p style={{ opacity: 0.7, marginBottom: 30, maxWidth: 400, margin: '0 auto 30px' }}>{t.install}</p>
            <button onClick={() => setStep(1)} style={btnPrimary}>{t.start}</button>
          </div>
        );
      case 'language':
        return (
          <div style={{ padding: 30 }}>
            <h2 style={h2Style}>{t.selectLang}</h2>
            <div style={{ display: 'grid', gap: 12 }}>
              {LANGUAGES.map(l => (
                <button key={l.code} onClick={() => setLang(l.code)} style={{ ...langBtn, ...(lang === l.code ? langBtnActive : {}) }}>
                  <span style={{ fontSize: 28 }}>{l.flag}</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>{l.name}</span>
                </button>
              ))}
            </div>
          </div>
        );
      case 'device_scan':
        return (
          <div style={{ padding: 30 }}>
            <h2 style={h2Style}>🔍 {s.title}</h2>
            {!scanned ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <div style={{ fontSize: 48, marginBottom: 16, animation: loading ? 'spin 2s linear infinite' : 'none' }}>💻</div>
                <button onClick={handleScan} disabled={loading} style={btnPrimary}>
                  {loading ? t.scanning : t.scan}
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {deviceInfo.map((d, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(255,255,255,0.05)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.08)' }}>
                    <span style={{ opacity: 0.6 }}>{d.name}</span>
                    <span style={{ fontWeight: 600, color: '#10b981' }}>{d.status} {d.value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case 'identity':
        return (
          <div style={{ padding: 30 }}>
            <h2 style={h2Style}>🛡️ {t.identityTitle}</h2>
            <div style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
              <Input label="Full Name" value={form.displayName} onChange={v => setForm(f => ({ ...f, displayName: v }))} />
              <Input label="Email" type="email" value={form.email} onChange={v => setForm(f => ({ ...f, email: v }))} />
              <Input label="Password" type="password" value={form.password} onChange={v => setForm(f => ({ ...f, password: v }))} />
            </div>
            <button onClick={() => setBioVerified(!bioVerified)} style={{ ...btnSecondary, width: '100%', marginBottom: 16 }}>
              {bioVerified ? '✅ Biometric Verified (Simulated)' : t.verifyBio}
            </button>
            <p style={{ fontSize: '0.8rem', opacity: 0.5, textAlign: 'center' }}>Zero-Knowledge Proof: Identity verified without exposing raw data.</p>
          </div>
        );
      case 'role':
        return (
          <div style={{ padding: 30 }}>
            <h2 style={h2Style}>{t.selectRole}</h2>
            <div style={{ display: 'grid', gap: 12 }}>
              {ROLES.map(r => (
                <button key={r.id} onClick={() => setRole(r.id)} style={{ ...roleBtn, ...(role === r.id ? { ...roleBtnActive, borderColor: r.color } : {}) }}>
                  <span style={{ fontSize: 32 }}>{r.icon}</span>
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem' }}>{r.label}</div>
                    <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>{r.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        );
      case 'agreement':
        return (
          <div style={{ padding: 30 }}>
            <h2 style={h2Style}>⚖️ {t.agreementTitle}</h2>
            <div style={{ background: 'rgba(255,255,255,0.04)', padding: 20, borderRadius: 14, border: '1px solid rgba(102,126,234,0.2)', marginBottom: 20, maxHeight: 200, overflow: 'auto', fontSize: '0.9rem', lineHeight: 1.6 }}>
              <p><strong>51% / 49% Sovereign Partnership</strong></p>
              <p>{t.agreementText}</p>
              <p style={{ marginTop: 12 }}><strong>Dharma-Chakra Immutable Constitution</strong></p>
              <p>• No centralized monopoly • Human veto always valid • Local-first privacy • 2-5% resource sharing • Zero-knowledge identity</p>
              <p style={{ marginTop: 12 }}><strong>Final 3 Confirmation</strong></p>
              <p>Critical actions require 3 biometric confirmations. AI assists but human decides.</p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', padding: 12, borderRadius: 10, background: agreed ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${agreed ? '#10b981' : 'rgba(255,255,255,0.1)'}` }}>
              <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} style={{ width: 20, height: 20 }} />
              <span style={{ fontWeight: 600 }}>{t.accept}</span>
            </label>
          </div>
        );
      case 'policies':
        return (
          <div style={{ padding: 30 }}>
            <h2 style={h2Style}>📜 {t.policiesTitle}</h2>
            <div style={{ display: 'grid', gap: 10 }}>
              {POLICIES.map(p => (
                <label key={p.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: 12, borderRadius: 10, background: policiesAccepted[p.id] ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)', border: `1px solid ${policiesAccepted[p.id] ? '#10b981' : 'rgba(255,255,255,0.08)'}`, cursor: 'pointer' }}>
                  <input type="checkbox" checked={!!policiesAccepted[p.id]} onChange={e => setPoliciesAccepted(prev => ({ ...prev, [p.id]: e.target.checked }))} style={{ marginTop: 4 }} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{p.label}</div>
                    <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>{p.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        );
      case 'universe':
        return (
          <div style={{ padding: 30, textAlign: 'center' }}>
            <h2 style={h2Style}>🌐 {s.title}</h2>
            <div style={{ fontSize: 64, margin: '20px 0' }}>👤➡️🌌</div>
            <p style={{ opacity: 0.7, marginBottom: 20 }}>Your Personal Universe is being created from your data, skills, and preferences.</p>
            <div style={{ display: 'grid', gap: 8, textAlign: 'left', maxWidth: 320, margin: '0 auto 20px' }}>
              <div style={universeItem}>📁 Documents — Ready</div>
              <div style={universeItem}>🖼️ Photos — Ready</div>
              <div style={universeItem}>🔗 APIs — Ready</div>
              <div style={universeItem}>🧠 Skills — Ready</div>
              <div style={universeItem}>💾 Preferences — Ready</div>
            </div>
          </div>
        );
      case 'confirm':
        return (
          <div style={{ padding: 30, textAlign: 'center' }}>
            <h2 style={h2Style}>🔐 {t.final3Title}</h2>
            <div style={{ display: 'grid', gap: 12, margin: '20px 0' }}>
              {[
                { q: lang === 'ne' ? 'तपाईं AsimNexus को Dharma-Chakra स्वीकार गर्नुहुन्छ?' : 'Do you accept Dharma-Chakra?', a: agreed },
                { q: lang === 'ne' ? 'तपाईंको डाटा Local-First रहन्छ?' : 'Your data stays Local-First?', a: policiesAccepted.local_first },
                { q: lang === 'ne' ? 'Biometric + ZKP ले पहिचान गर्छ?' : 'Biometric + ZKP verifies identity?', a: bioVerified },
              ].map((item, i) => (
                <div key={i} style={{ padding: 14, borderRadius: 10, background: item.a ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${item.a ? '#10b981' : '#ef4444'}` }}>
                  <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>{item.q}</div>
                  <div style={{ fontWeight: 700, color: item.a ? '#10b981' : '#ef4444' }}>{item.a ? '✅ Yes' : '❌ No'}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', opacity: 0.5 }}>Final 3: All must be YES to activate.</p>
          </div>
        );
      case 'activation':
        return (
          <div style={{ padding: 30, textAlign: 'center' }}>
            <h2 style={h2Style}>🚀 {s.title}</h2>
            <div style={{ fontSize: 80, margin: '20px 0', animation: 'pulse 2s infinite' }}>🌌</div>
            <p style={{ opacity: 0.8, marginBottom: 10 }}>Asim Orb is now active on your screen.</p>
            <p style={{ opacity: 0.6, fontSize: '0.9rem', marginBottom: 30 }}>Chat from anywhere. Control everything. Your Universe awaits.</p>
            <button onClick={handleRegister} disabled={loading || !form.email || !form.password} style={btnPrimary}>
              {loading ? 'Activating...' : t.activate}
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  const canProceed = () => {
    const s = STEPS[step];
    if (s.id === 'language') return !!lang;
    if (s.id === 'device_scan') return scanned;
    if (s.id === 'identity') return form.displayName && form.email && form.password && bioVerified;
    if (s.id === 'role') return !!role;
    if (s.id === 'agreement') return agreed;
    if (s.id === 'policies') return Object.values(policiesAccepted).filter(Boolean).length >= 3;
    if (s.id === 'confirm') return agreed && policiesAccepted.local_first && bioVerified;
    return true;
  };

  return (
    <div style={pageStyle}>
      {/* Progress */}
      <div style={{ padding: '20px 30px 0' }}>
        <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
          {STEPS.map((_, i) => (
            <div key={i} style={{ flex: 1, height: 4, borderRadius: 2, background: i <= step ? 'linear-gradient(90deg,#667eea,#764ba2)' : 'rgba(255,255,255,0.1)', transition: 'all 0.3s' }} />
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', opacity: 0.5 }}>
          <span>Step {step + 1} of {STEPS.length}</span>
          <span>{STEPS[step].title}</span>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>{renderStep()}</div>

      {/* Nav */}
      <div style={{ display: 'flex', gap: 12, padding: '20px 30px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        {step > 0 && (
          <button onClick={() => setStep(step - 1)} style={btnSecondary}>{t.back}</button>
        )}
        {step < STEPS.length - 1 ? (
          <button onClick={() => setStep(step + 1)} disabled={!canProceed()} style={{ ...btnPrimary, opacity: canProceed() ? 1 : 0.4 }}>{t.next}</button>
        ) : null}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:0.5;transform:scale(1)} 50%{opacity:1;transform:scale(1.1)} }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
      `}</style>
    </div>
  );
}

// ── Styles ──
const pageStyle = { width: '100%', maxWidth: 520, margin: '0 auto', minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'rgba(10,10,26,0.95)', color: '#fff' };
const h2Style = { fontSize: '1.3rem', marginBottom: 20, fontWeight: 700 };
const btnPrimary = { flex: 1, padding: '14px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg,#667eea,#764ba2)', color: '#fff', fontSize: '1rem', fontWeight: 600, cursor: 'pointer' };
const btnSecondary = { padding: '14px 24px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.05)', color: '#fff', fontSize: '1rem', cursor: 'pointer' };
const langBtn = { display: 'flex', alignItems: 'center', gap: 16, padding: 16, borderRadius: 12, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.03)', color: '#fff', cursor: 'pointer' };
const langBtnActive = { background: 'rgba(102,126,234,0.15)', borderColor: '#667eea' };
const roleBtn = { display: 'flex', alignItems: 'center', gap: 16, padding: 16, borderRadius: 12, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.03)', color: '#fff', cursor: 'pointer' };
const roleBtnActive = { background: 'rgba(255,255,255,0.08)' };
const universeItem = { padding: '10px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.05)', fontSize: '0.9rem' };

function Input({ label, type = 'text', value, onChange }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.8rem', opacity: 0.6, marginBottom: 6 }}>{label}</label>
      <input
        type={type} value={value} onChange={e => onChange(e.target.value)}
        style={{ width: '100%', padding: '12px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: '#fff', fontSize: '1rem', outline: 'none' }}
      />
    </div>
  );
}
