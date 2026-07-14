import React, { useState, useEffect } from 'react';
import { jobsAPI } from '../../api/asimnexus';

const CATEGORIES = ['All', 'Development', 'Design', 'Writing', 'Data', 'Marketing', 'Support', 'Other'];
const CAT_ICONS: Record<string, string> = {
    Development: '💻', Design: '🎨', Writing: '✍️', Data: '📊',
    Marketing: '📢', Support: '🎧', Other: '🔧',
};
const STATUS_COLOR: Record<string, string> = {
    open: '#10b981', in_progress: '#f59e0b', completed: '#667eea', cancelled: '#ef4444',
};

interface AgentMarketplacePanelProps {
    user?: Record<string, unknown>;
}

interface JobData {
    id?: string;
    title?: string;
    description?: string;
    category?: string;
    budget?: number;
    status?: string;
    client?: string;
    created_at?: string;
}

interface StatsData {
    total_jobs?: number;
    open_jobs?: number;
    active_contracts?: number;
    total_spent?: number;
}

// Helper to call a style function safely
const sf = (fn: unknown, ...args: unknown[]): React.CSSProperties => {
    return typeof fn === 'function' ? (fn as (...a: unknown[]) => React.CSSProperties)(...args) : fn as React.CSSProperties;
};

export default function AgentMarketplacePanel({ user: _user }: AgentMarketplacePanelProps) {
    const [tab, setTab] = useState<'browse' | 'post' | 'myJobs'>('browse');
    const [jobs, setJobs] = useState<JobData[]>([]);
    const [myJobs, setMyJobs] = useState<JobData[]>([]);
    const [stats, setStats] = useState<StatsData | null>(null);
    const [category, setCategory] = useState('All');
    const [selectedJob, setSelectedJob] = useState<JobData | null>(null);
    const [applyLoading, setApplyLoading] = useState<string | null>(null);
    const [msg, setMsg] = useState('');
    const [postForm, setPostForm] = useState({
        title: '', description: '', category: 'Development', budget: '',
    });

    const fetchStats = async () => {
        try {
            const r = await jobsAPI.getStats() as unknown as { data?: StatsData };
            if (r.data) setStats(r.data);
        } catch { /* ignore */ }
    };

    useEffect(() => {
        fetchStats();
        jobsAPI.list().then((r: unknown) => {
            const res = r as { data?: { success?: boolean; jobs?: JobData[] } };
            if (res.data?.success) setJobs(res.data.jobs || []);
        }).catch(() => { });
        jobsAPI.list().then((r: unknown) => {
            const res = r as { data?: { success?: boolean; jobs?: JobData[] } };
            if (res.data?.success) setMyJobs(res.data.jobs || []);
        }).catch(() => { });
    }, []);

    const postJob = async () => {
        if (!postForm.title.trim()) { setMsg('Title is required'); return; }
        setMsg('');
        try {
            const r = await jobsAPI.post({
                title: postForm.title, description: postForm.description,
                category: postForm.category, budget: parseFloat(postForm.budget) || 0,
            }) as unknown as { data?: { success?: boolean } };
            if (r.data?.success) {
                setMsg('Job posted successfully!');
                setPostForm({ title: '', description: '', category: 'Development', budget: '' });
                fetchStats();
            }
        } catch { setMsg('Failed to post job'); }
    };

    const applyJob = async (jobId: string) => {
        setApplyLoading(jobId);
        try {
            await jobsAPI.apply(jobId);
            setMsg('Application submitted!');
        } catch { setMsg('Failed to apply'); }
        setApplyLoading(null);
    };

    const filteredJobs = category === 'All' ? jobs : jobs.filter(j => j.category === category);

    const s: Record<string, React.CSSProperties | ((...args: unknown[]) => React.CSSProperties)> = {
        title: {
            fontSize: '1.2rem', fontWeight: 700, marginBottom: 16,
            background: 'linear-gradient(135deg, #667eea, #a78bfa)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        },
        statCard: {
            background: 'rgba(255,255,255,0.04)', borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.06)', padding: '14px 18px', flex: 1,
        },
        tab: (active: unknown) => ({
            padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontSize: '0.82rem',
            fontWeight: active ? 700 : 400, border: 'none',
            background: active ? 'rgba(102,126,234,0.2)' : 'rgba(255,255,255,0.04)',
            color: active ? '#667eea' : 'rgba(255,255,255,0.6)',
        }) as React.CSSProperties,
        catBtn: (active: unknown) => ({
            padding: '4px 12px', borderRadius: 16, cursor: 'pointer', fontSize: '0.72rem',
            border: `1px solid ${active ? '#667eea' : 'rgba(255,255,255,0.1)'}`,
            background: active ? '#667eea22' : 'transparent',
            color: active ? '#667eea' : 'rgba(255,255,255,0.6)',
        }) as React.CSSProperties,
        jobCard: {
            background: 'rgba(255,255,255,0.03)', borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.06)', padding: 16,
        },
        statusDot: (status: unknown) => ({
            display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
            background: STATUS_COLOR[String(status)] || '#888', marginRight: 6,
        }) as React.CSSProperties,
        formWrap: {
            display: 'flex', flexDirection: 'column' as const, gap: 12,
        },
        input: {
            padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(0,0,0,0.3)', color: '#fff', fontSize: '0.85rem', outline: 'none',
        },
        textarea: {
            padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(0,0,0,0.3)', color: '#fff', fontSize: '0.85rem', outline: 'none',
            minHeight: 80, resize: 'vertical' as const, fontFamily: 'inherit',
        },
        btn: {
            padding: '10px 20px', borderRadius: 8, cursor: 'pointer', fontWeight: 600,
            border: 'none', background: 'linear-gradient(135deg, #667eea, #a78bfa)',
            color: '#fff', fontSize: '0.85rem',
        },
        msg: {
            padding: '8px 14px', borderRadius: 8, fontSize: '0.8rem',
            background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
            color: '#10b981',
        },
        overlay: {
            position: 'fixed' as const, inset: 0, zIndex: 100,
            background: 'rgba(0,0,0,0.6)', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
        },
        modal: {
            background: '#1a1a2e', borderRadius: 16, padding: 28,
            width: '90%', maxWidth: 500, maxHeight: '80vh', overflow: 'auto',
            border: '1px solid rgba(255,255,255,0.08)',
        },
    };

    return (
        <div style={{ color: '#fff', fontFamily: 'inherit' }}>
            <div style={s.title as React.CSSProperties}>🤖 Agent Marketplace</div>

            {/* Stats */}
            {stats && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#667eea' }}>{stats.total_jobs ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Total Jobs</div>
                    </div>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#10b981' }}>{stats.open_jobs ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Open</div>
                    </div>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f59e0b' }}>{stats.active_contracts ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Active Contracts</div>
                    </div>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#a78bfa' }}>${stats.total_spent ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Total Spent</div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                {(['browse', 'post', 'myJobs'] as const).map(t => (
                    <button key={t} onClick={() => setTab(t)}
                        style={sf(s.tab, tab === t)}>
                        {t === 'browse' ? '📋 Browse' : t === 'post' ? '📝 Post Job' : '📂 My Jobs'}
                    </button>
                ))}
            </div>

            {/* Browse Tab */}
            {tab === 'browse' && (
                <div>
                    <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
                        {CATEGORIES.map(c => (
                            <button key={c} onClick={() => setCategory(c)}
                                style={sf(s.catBtn, category === c)}>
                                {CAT_ICONS[c] || ''} {c}
                            </button>
                        ))}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {filteredJobs.map(job => (
                            <div key={job.id} style={s.jobCard as React.CSSProperties}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{job.title}</div>
                                        <div style={{ fontSize: '0.78rem', opacity: 0.6, marginBottom: 6 }}>
                                            {CAT_ICONS[job.category || ''] || ''} {job.category} · ${job.budget}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                            {job.client} · {job.created_at?.slice(0, 10)}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                                        <span style={{ fontSize: '0.72rem', display: 'flex', alignItems: 'center' }}>
                                            <span style={sf(s.statusDot, job.status)} />
                                            {job.status}
                                        </span>
                                        <button onClick={() => setSelectedJob(job)}
                                            style={{
                                                padding: '6px 14px', borderRadius: 8, cursor: 'pointer',
                                                border: '1px solid rgba(102,126,234,0.3)',
                                                background: 'rgba(102,126,234,0.1)', color: '#667eea',
                                                fontSize: '0.75rem', fontWeight: 600,
                                            }}>
                                            View & Apply
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Post Tab */}
            {tab === 'post' && (
                <div style={s.formWrap as React.CSSProperties}>
                    <input style={s.input as React.CSSProperties} placeholder="Job Title"
                        value={postForm.title} onChange={e => setPostForm(p => ({ ...p, title: e.target.value }))} />
                    <textarea style={s.textarea as React.CSSProperties} placeholder="Description"
                        value={postForm.description} onChange={e => setPostForm(p => ({ ...p, description: e.target.value }))} />
                    <select style={s.input as React.CSSProperties}
                        value={postForm.category} onChange={e => setPostForm(p => ({ ...p, category: e.target.value }))}>
                        {CATEGORIES.filter(c => c !== 'All').map(c => (
                            <option key={c} value={c}>{CAT_ICONS[c]} {c}</option>
                        ))}
                    </select>
                    <input style={s.input as React.CSSProperties} placeholder="Budget ($)"
                        type="number" value={postForm.budget}
                        onChange={e => setPostForm(p => ({ ...p, budget: e.target.value }))} />
                    <button style={s.btn as React.CSSProperties} onClick={postJob}>Post Job</button>
                    {msg && <div style={s.msg as React.CSSProperties}>{msg}</div>}
                </div>
            )}

            {/* My Jobs Tab */}
            {tab === 'myJobs' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {myJobs.map(job => (
                        <div key={job.id} style={s.jobCard as React.CSSProperties}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>{job.title}</div>
                                    <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                        {job.category} · ${job.budget}
                                    </div>
                                </div>
                                <span style={{ fontSize: '0.72rem', display: 'flex', alignItems: 'center' }}>
                                    <span style={sf(s.statusDot, job.status)} />
                                    {job.status}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Job Detail Modal */}
            {selectedJob && (
                <div style={s.overlay as React.CSSProperties} onClick={() => setSelectedJob(null)}>
                    <div style={s.modal as React.CSSProperties} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                            <div>
                                <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{selectedJob.title}</div>
                                <div style={{ fontSize: '0.78rem', opacity: 0.5, marginTop: 4 }}>
                                    {CAT_ICONS[selectedJob.category || '']} {selectedJob.category} · ${selectedJob.budget}
                                </div>
                            </div>
                            <button onClick={() => setSelectedJob(null)}
                                style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1.2rem' }}>
                                ✕
                            </button>
                        </div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.7, marginBottom: 16, lineHeight: 1.5 }}>
                            {selectedJob.description || 'No description provided.'}
                        </div>
                        <div style={{ fontSize: '0.78rem', opacity: 0.5, marginBottom: 16 }}>
                            Client: {selectedJob.client} · Posted: {selectedJob.created_at?.slice(0, 10)}
                        </div>
                        <button onClick={() => { if (selectedJob.id) applyJob(selectedJob.id); }}
                            disabled={applyLoading === selectedJob.id}
                            style={{
                                padding: '10px 24px', borderRadius: 8, cursor: 'pointer', fontWeight: 600,
                                border: 'none', background: 'linear-gradient(135deg, #10b981, #34d399)',
                                color: '#fff', fontSize: '0.85rem', width: '100%',
                            }}>
                            {applyLoading === selectedJob.id ? '⏳ Applying...' : '📩 Apply for this Job'}
                        </button>
                        {msg && <div style={{ ...s.msg as React.CSSProperties, marginTop: 12 }}>{msg}</div>}
                    </div>
                </div>
            )}
        </div>
    );
}
