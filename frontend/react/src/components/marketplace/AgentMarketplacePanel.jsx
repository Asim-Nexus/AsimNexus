import React, { useState, useEffect, useCallback } from 'react';
const getStoredToken = () => localStorage.getItem('asim_token');

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const CATEGORIES = ['all', 'tech', 'health', 'education', 'legal', 'finance', 'creative', 'farming', 'community', 'research', 'translation'];

const CAT_ICONS = {
  tech: '💻', health: '🏥', education: '📚', legal: '⚖️', finance: '💰',
  creative: '🎨', farming: '🌾', community: '🤝', research: '🔬',
  translation: '🌐', other: '📌', all: '🌍',
};

const STATUS_COLOR = {
  open: '#10b981', assigned: '#3b82f6', in_progress: '#f59e0b',
  review: '#8b5cf6', completed: '#6b7280', disputed: '#ef4444', cancelled: '#6b7280',
};

function authHeaders() {
  const token = getStoredToken();
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

export default function AgentMarketplacePanel({ user }) {
  const [tab, setTab] = useState('browse'); // browse | post | myJobs | agentProfile
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedCat, setSelectedCat] = useState('all');
  const [selectedJob, setSelectedJob] = useState(null);
  const [msg, setMsg] = useState('');

  const [postForm, setPostForm] = useState({
    title: '', description: '', budget: 'negotiable', budget_currency: 'USD',
    timeline_days: 7, skills: '', category: 'tech',
  });
  const [applyNote, setApplyNote] = useState('');

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const cat = selectedCat === 'all' ? '' : `&category=${selectedCat}`;
      const r = await fetch(`${API}/api/jobs/list?status=open${cat}`, { headers: authHeaders() });
      const d = await r.json();
      setJobs(d.jobs || []);
    } catch { setJobs([]); }
    setLoading(false);
  }, [selectedCat]);

  const fetchStats = async () => {
    try {
      const r = await fetch(`${API}/api/jobs/stats`, { headers: authHeaders() });
      const d = await r.json();
      setStats(d);
    } catch { }
  };

  useEffect(() => { fetchJobs(); fetchStats(); }, [fetchJobs]);

  const postJob = async () => {
    if (!postForm.title.trim()) { setMsg('Title required'); return; }
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/jobs/post`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          ...postForm,
          skills: postForm.skills.split(',').map(s => s.trim()).filter(Boolean),
        }),
      });
      const d = await r.json();
      if (d.job_id) {
        setMsg(`✅ Job posted! ID: ${d.job_id}`);
        setPostForm({ title: '', description: '', budget: 'negotiable', budget_currency: 'USD', timeline_days: 7, skills: '', category: 'tech' });
        fetchJobs();
        setTab('browse');
      } else {
        setMsg(d.error || 'Post failed');
      }
    } catch (e) { setMsg('Error: ' + e.message); }
    setLoading(false);
  };

  const applyJob = async (jobId) => {
    try {
      const r = await fetch(`${API}/api/jobs/${jobId}/apply`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ cover_note: applyNote }),
      });
      const d = await r.json();
      setMsg(d.message || d.error);
      setApplyNote('');
      setSelectedJob(null);
    } catch (e) { setMsg(e.message); }
  };

  const s = {
    wrap: { padding: 24, minHeight: '100vh' },
    header: { marginBottom: 20 },
    title: {
      fontSize: '1.5rem', fontWeight: 700,
      background: 'linear-gradient(45deg, #667eea, #764ba2)',
      WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
    },
    statsRow: { display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 },
    statCard: {
      background: 'var(--theme-card, rgba(255,255,255,0.05))',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 12, padding: '12px 18px', minWidth: 100, textAlign: 'center',
    },
    statNum: { fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-primary, #667eea)' },
    statLabel: { fontSize: '0.7rem', opacity: 0.5 },
    tabs: { display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' },
    tab: (active) => ({
      padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem',
      background: active ? 'rgba(102,126,234,0.2)' : 'transparent',
      border: active ? '1px solid rgba(102,126,234,0.5)' : '1px solid rgba(255,255,255,0.1)',
      color: active ? 'var(--accent-primary, #667eea)' : 'rgba(255,255,255,0.6)',
    }),
    catBar: { display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16 },
    catBtn: (active) => ({
      padding: '4px 12px', borderRadius: 20, cursor: 'pointer', fontSize: '0.75rem',
      background: active ? 'rgba(102,126,234,0.25)' : 'rgba(255,255,255,0.04)',
      border: `1px solid ${active ? 'rgba(102,126,234,0.5)' : 'rgba(255,255,255,0.08)'}`,
      color: active ? 'var(--accent-primary, #667eea)' : 'rgba(255,255,255,0.55)',
    }),
    jobGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 },
    jobCard: {
      background: 'var(--theme-card, rgba(255,255,255,0.04))',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 14, padding: 16, cursor: 'pointer',
      transition: 'all 0.2s',
    },
    jobTitle: { fontWeight: 600, fontSize: '0.95rem', marginBottom: 6 },
    jobMeta: { fontSize: '0.72rem', opacity: 0.55, display: 'flex', gap: 8, flexWrap: 'wrap' },
    statusDot: (status) => ({
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: STATUS_COLOR[status] || '#6b7280', marginRight: 4,
    }),
    formWrap: {
      background: 'var(--theme-card, rgba(255,255,255,0.04))',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 16, padding: 24, maxWidth: 600,
    },
    input: {
      width: '100%', padding: '10px 14px', borderRadius: 8, marginBottom: 12,
      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
      color: 'var(--theme-text, #fff)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
    },
    textarea: {
      width: '100%', minHeight: 80, padding: '10px 14px', borderRadius: 8, marginBottom: 12,
      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
      color: 'var(--theme-text, #fff)', fontSize: '0.9rem', outline: 'none',
      resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit',
    },
    btn: {
      padding: '10px 22px', borderRadius: 8, border: 'none', cursor: 'pointer',
      background: 'linear-gradient(135deg, #667eea, #764ba2)',
      color: '#fff', fontWeight: 600, fontSize: '0.9rem',
    },
    msg: {
      padding: '10px 16px', borderRadius: 8, marginBottom: 14, fontSize: '0.85rem',
      background: 'rgba(102,126,234,0.12)', border: '1px solid rgba(102,126,234,0.3)',
      color: 'var(--theme-text, #fff)',
    },
    overlay: {
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    },
    modal: {
      background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 20, padding: 28, maxWidth: 520, width: '90%', maxHeight: '80vh', overflow: 'auto',
    },
  };

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <div style={s.title}>🌍 Global Agent Marketplace</div>
        <div style={{ fontSize: '0.82rem', opacity: 0.5, marginTop: 4 }}>
          Post jobs, hire global agents, Dharma-protected escrow payments
        </div>
      </div>

      {msg && <div style={s.msg}>{msg} <span style={{ cursor: 'pointer', opacity: 0.5, marginLeft: 8 }} onClick={() => setMsg('')}>✕</span></div>}

      <div style={s.statsRow}>
        {[
          ['Total Jobs', stats.total_jobs || 0],
          ['Open', stats.open_jobs || 0],
          ['Completed', stats.completed_jobs || 0],
          ['Agents', stats.total_agents || 0],
          ['Available', stats.available_agents || 0],
        ].map(([label, val]) => (
          <div key={label} style={s.statCard}>
            <div style={s.statNum}>{val}</div>
            <div style={s.statLabel}>{label}</div>
          </div>
        ))}
      </div>

      <div style={s.tabs}>
        {[['browse', '🔍 Browse Jobs'], ['post', '➕ Post Job'], ['myJobs', '📋 My Jobs']].map(([id, label]) => (
          <button key={id} style={s.tab(tab === id)} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {tab === 'browse' && (
        <>
          <div style={s.catBar}>
            {CATEGORIES.map(cat => (
              <button key={cat} style={s.catBtn(selectedCat === cat)} onClick={() => setSelectedCat(cat)}>
                {CAT_ICONS[cat] || '📌'} {cat}
              </button>
            ))}
          </div>
          {loading ? (
            <div style={{ opacity: 0.5, textAlign: 'center', paddingTop: 40 }}>Loading jobs…</div>
          ) : jobs.length === 0 ? (
            <div style={{ opacity: 0.4, textAlign: 'center', paddingTop: 40 }}>
              No open jobs in this category.<br />
              <button style={{ ...s.btn, marginTop: 16 }} onClick={() => setTab('post')}>Post the First Job</button>
            </div>
          ) : (
            <div style={s.jobGrid}>
              {jobs.map(job => (
                <div key={job.id} style={s.jobCard}
                  onClick={() => setSelectedJob(job)}
                  onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(102,126,234,0.15)'; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span style={{ fontSize: '1.4rem' }}>{CAT_ICONS[job.category] || '📌'}</span>
                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 10, background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}>
                      <span style={s.statusDot(job.status)} />{job.status}
                    </span>
                  </div>
                  <div style={s.jobTitle}>{job.title}</div>
                  <div style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: 8, lineHeight: 1.4 }}>
                    {job.description ? job.description.slice(0, 100) + (job.description.length > 100 ? '…' : '') : ''}
                  </div>
                  <div style={s.jobMeta}>
                    <span>💰 {job.budget} {job.budget_currency}</span>
                    <span>⏱️ {job.timeline_days}d</span>
                    <span>🏷️ {job.category}</span>
                  </div>
                  {job.skills && job.skills.length > 0 && (
                    <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {job.skills.slice(0, 3).map(sk => (
                        <span key={sk} style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(102,126,234,0.1)', fontSize: '0.65rem', color: 'rgba(255,255,255,0.6)' }}>{sk}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'post' && (
        <div style={s.formWrap}>
          <div style={{ fontWeight: 700, marginBottom: 16, fontSize: '1.1rem' }}>Post a New Job</div>
          <input style={s.input} placeholder="Job Title *" value={postForm.title} onChange={e => setPostForm(p => ({ ...p, title: e.target.value }))} />
          <textarea style={s.textarea} placeholder="Description — what do you need?" value={postForm.description} onChange={e => setPostForm(p => ({ ...p, description: e.target.value }))} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <input style={s.input} placeholder="Budget (e.g. 50, negotiable)" value={postForm.budget} onChange={e => setPostForm(p => ({ ...p, budget: e.target.value }))} />
            <select style={{ ...s.input, marginBottom: 0 }} value={postForm.budget_currency} onChange={e => setPostForm(p => ({ ...p, budget_currency: e.target.value }))}>
              {['USD', 'EUR', 'GBP', 'NPR', 'INR', 'BTC', 'ETH'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <input style={s.input} type="number" placeholder="Timeline (days)" value={postForm.timeline_days} onChange={e => setPostForm(p => ({ ...p, timeline_days: +e.target.value }))} />
            <select style={{ ...s.input, marginBottom: 0 }} value={postForm.category} onChange={e => setPostForm(p => ({ ...p, category: e.target.value }))}>
              {CATEGORIES.filter(c => c !== 'all').map(c => <option key={c} value={c}>{CAT_ICONS[c]} {c}</option>)}
            </select>
          </div>
          <input style={s.input} placeholder="Skills (comma-separated: python, design, ...)" value={postForm.skills} onChange={e => setPostForm(p => ({ ...p, skills: e.target.value }))} />
          <button style={s.btn} onClick={postJob} disabled={loading}>
            {loading ? 'Posting…' : '🚀 Post Job'}
          </button>
          <div style={{ fontSize: '0.72rem', opacity: 0.4, marginTop: 10 }}>
            ☯️ All jobs pass Dharma-Chakra veto before being listed.
          </div>
        </div>
      )}

      {tab === 'myJobs' && (
        <div style={{ opacity: 0.6, textAlign: 'center', paddingTop: 40 }}>
          <div style={{ fontSize: '2rem', marginBottom: 10 }}>🔐</div>
          My Jobs panel — shows jobs you posted or applied to.<br />
          <span style={{ fontSize: '0.8rem' }}>Login required for full access.</span>
        </div>
      )}

      {selectedJob && (
        <div style={s.overlay} onClick={() => setSelectedJob(null)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <span style={{ fontSize: '1.4rem' }}>{CAT_ICONS[selectedJob.category] || '📌'}</span>
              <button onClick={() => setSelectedJob(null)} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: 20 }}>✕</button>
            </div>
            <div style={{ fontWeight: 700, fontSize: '1.2rem', marginBottom: 8 }}>{selectedJob.title}</div>
            <div style={{ fontSize: '0.82rem', opacity: 0.6, marginBottom: 12, lineHeight: 1.5 }}>{selectedJob.description}</div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap', fontSize: '0.8rem' }}>
              <span>💰 {selectedJob.budget} {selectedJob.budget_currency}</span>
              <span>⏱️ {selectedJob.timeline_days} days</span>
              <span>🏷️ {selectedJob.category}</span>
            </div>
            {selectedJob.skills?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 6 }}>SKILLS NEEDED</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {selectedJob.skills.map(sk => (
                    <span key={sk} style={{ padding: '3px 10px', borderRadius: 10, background: 'rgba(102,126,234,0.12)', fontSize: '0.75rem', color: 'var(--accent-primary, #667eea)', border: '1px solid rgba(102,126,234,0.25)' }}>{sk}</span>
                  ))}
                </div>
              </div>
            )}
            <div style={{ fontSize: '0.75rem', opacity: 0.5, marginBottom: 10 }}>YOUR COVER NOTE</div>
            <textarea style={{ ...s.textarea, minHeight: 60 }}
              placeholder="Why are you the right person? (optional)"
              value={applyNote} onChange={e => setApplyNote(e.target.value)} />
            <button style={s.btn} onClick={() => applyJob(selectedJob.id)}>
              ✅ Apply for this Job
            </button>
            <div style={{ fontSize: '0.68rem', opacity: 0.35, marginTop: 8 }}>
              ☯️ Dharma-protected · Escrow-ready · Global marketplace
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
