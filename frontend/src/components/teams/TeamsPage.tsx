import React, { useState, useEffect, useCallback } from 'react';
import { teamsAPI } from '../../api/asimnexus';

interface TeamData {
    id: string;
    name: string;
    description?: string;
    icon?: string;
    member_count?: number;
    member_role?: string;
    [key: string]: unknown;
}

interface MemberData {
    id: string;
    display_name?: string;
    email?: string;
    role: string;
    [key: string]: unknown;
}

interface ApiResponseData {
    success?: boolean;
    team?: TeamData;
    teams?: TeamData[];
    members?: MemberData[];
    display_name?: string;
    detail?: string;
    [key: string]: unknown;
}

const styles: Record<string, React.CSSProperties | ((...args: unknown[]) => React.CSSProperties)> = {
    container: {
        flex: 1, overflow: 'auto', padding: '24px 32px',
    } as React.CSSProperties,
    title: {
        fontSize: '1.4rem', fontWeight: 700, marginBottom: 24,
        background: 'linear-gradient(45deg, #667eea, #a78bfa)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
    } as React.CSSProperties,
    card: {
        background: 'rgba(255,255,255,0.04)', borderRadius: 16,
        border: '1px solid rgba(255,255,255,0.06)',
        padding: 24, backdropFilter: 'blur(12px)',
        marginBottom: 16, cursor: 'pointer', transition: 'all 0.15s',
    } as React.CSSProperties,
    cardHover: {
        background: 'rgba(255,255,255,0.07)',
        border: '1px solid rgba(102,126,234,0.3)',
    } as React.CSSProperties,
    fieldLabel: {
        fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase',
        letterSpacing: 1, opacity: 0.5, marginBottom: 6,
    } as React.CSSProperties,
    input: {
        width: '100%', padding: '10px 14px', borderRadius: 10,
        border: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(0,0,0,0.3)', color: '#fff',
        fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
    } as React.CSSProperties,
    textarea: {
        width: '100%', padding: '10px 14px', borderRadius: 10,
        border: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(0,0,0,0.3)', color: '#fff',
        fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
        minHeight: 60, resize: 'vertical', fontFamily: 'inherit',
    } as React.CSSProperties,
    btn: {
        padding: '10px 24px', borderRadius: 10, cursor: 'pointer',
        fontWeight: 600, fontSize: '0.85rem', border: 'none',
        background: 'linear-gradient(135deg, #667eea, #a78bfa)',
        color: '#fff', transition: 'all 0.15s',
    } as React.CSSProperties,
    btnSecondary: {
        padding: '8px 16px', borderRadius: 8, cursor: 'pointer',
        fontWeight: 500, fontSize: '0.8rem', border: '1px solid rgba(255,255,255,0.15)',
        background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.8)',
    } as React.CSSProperties,
    btnDanger: {
        padding: '6px 14px', borderRadius: 8, cursor: 'pointer',
        fontWeight: 500, fontSize: '0.78rem', border: 'none',
        background: 'rgba(239,68,68,0.15)', color: '#ef4444',
    } as React.CSSProperties,
    select: {
        padding: '6px 10px', borderRadius: 8,
        border: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(0,0,0,0.3)', color: '#fff',
        fontSize: '0.8rem', outline: 'none',
    } as React.CSSProperties,
    badge: (role: unknown) => ({
        display: 'inline-block', padding: '2px 10px', borderRadius: 20,
        fontSize: '0.7rem', fontWeight: 600,
        background: role === 'owner' ? 'rgba(239,68,68,0.2)' :
            role === 'admin' ? 'rgba(102,126,234,0.2)' :
                role === 'member' ? 'rgba(16,185,129,0.2)' :
                    'rgba(255,255,255,0.1)',
        color: role === 'owner' ? '#ef4444' :
            role === 'admin' ? '#667eea' :
                role === 'member' ? '#10b981' : 'rgba(255,255,255,0.5)',
        border: `1px solid ${role === 'owner' ? 'rgba(239,68,68,0.3)' :
            role === 'admin' ? 'rgba(102,126,234,0.3)' :
                role === 'member' ? 'rgba(16,185,129,0.3)' :
                    'rgba(255,255,255,0.1)'
            }`,
    } as React.CSSProperties),
    errMsg: {
        color: '#ef4444', fontSize: '0.82rem', marginTop: 8,
        padding: '8px 12px', borderRadius: 8,
        background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
    } as React.CSSProperties,
    successMsg: {
        color: '#10b981', fontSize: '0.82rem', marginTop: 8,
        padding: '8px 12px', borderRadius: 8,
        background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
    } as React.CSSProperties,
    modalOverlay: {
        position: 'fixed', inset: 0, zIndex: 100,
        background: 'rgba(0,0,0,0.6)', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
    } as React.CSSProperties,
    modal: {
        background: '#1a1a2e', borderRadius: 16, padding: 28,
        width: '90%', maxWidth: 500, maxHeight: '80vh', overflow: 'auto',
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
    } as React.CSSProperties,
    backBtn: {
        display: 'inline-flex', alignItems: 'center', gap: 6,
        cursor: 'pointer', fontSize: '0.85rem', opacity: 0.6,
        marginBottom: 16, transition: 'opacity 0.15s',
    } as React.CSSProperties,
};

// ═══════════════════════════════════════════════════════════════════════════
// TeamDetail — View/Edit team, manage members
// ═══════════════════════════════════════════════════════════════════════════

interface TeamDetailProps {
    teamId: string;
    onBack: () => void;
}

function TeamDetail({ teamId, onBack }: TeamDetailProps) {
    const [team, setTeam] = useState<TeamData | null>(null);
    const [members, setMembers] = useState<MemberData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [editMode, setEditMode] = useState(false);
    const [editName, setEditName] = useState('');
    const [editDesc, setEditDesc] = useState('');
    const [editIcon, setEditIcon] = useState('');
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('member');

    const loadTeam = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const [teamRes, membersRes] = await Promise.all([
                teamsAPI.get(teamId),
                teamsAPI.getMembers(teamId),
            ]);
            const teamData = teamRes.data as unknown as ApiResponseData;
            const membersData = membersRes.data as unknown as ApiResponseData;
            if (teamData?.success) setTeam(teamData.team as TeamData);
            if (membersData?.success) setMembers(membersData.members as MemberData[]);
        } catch (err) {
            setError(((err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Failed to load team');
        } finally {
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => { loadTeam(); }, [loadTeam]);

    const canManage = team && (team.member_role === 'admin' || team.member_role === 'owner');

    const handleEdit = () => {
        setEditName(team?.name || '');
        setEditDesc(team?.description || '');
        setEditIcon(team?.icon || '👥');
        setEditMode(true);
        setError('');
        setSuccess('');
    };

    const handleSaveEdit = async () => {
        setError('');
        setSuccess('');
        try {
            const res = await teamsAPI.update(teamId, { name: editName, description: editDesc, icon: editIcon });
            const resData = res.data as unknown as ApiResponseData;
            if (resData?.success) {
                setTeam(resData.team as TeamData);
                setEditMode(false);
                setSuccess('Team updated successfully');
            }
        } catch (err) {
            setError(((err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Failed to update team');
        }
    };

    const handleInvite = async () => {
        if (!inviteEmail.trim()) return;
        setError('');
        setSuccess('');
        try {
            const res = await teamsAPI.inviteMember(teamId, { email: inviteEmail.trim(), role: inviteRole });
            const resData = res.data as unknown as ApiResponseData;
            if (resData?.success) {
                setSuccess(`Invited ${resData.display_name || inviteEmail} to the team`);
                setInviteEmail('');
                loadTeam(); // Refresh members
            }
        } catch (err) {
            setError(((err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Failed to invite member');
        }
    };

    const handleRemoveMember = async (userId: string, displayName: string) => {
        setError('');
        setSuccess('');
        try {
            const res = await teamsAPI.removeMember(teamId, userId);
            const resData = res.data as unknown as ApiResponseData;
            if (resData?.success) {
                setSuccess(`Removed ${displayName} from the team`);
                loadTeam();
            }
        } catch (err) {
            setError(((err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Failed to remove member');
        }
    };

    const handleChangeRole = async (userId: string, newRole: string) => {
        setError('');
        setSuccess('');
        try {
            const res = await teamsAPI.changeMemberRole(teamId, userId, newRole);
            const resData = res.data as unknown as ApiResponseData;
            if (resData?.success) {
                setSuccess(`Role updated to ${newRole}`);
                loadTeam();
            }
        } catch (err) {
            setError(((err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Failed to change role');
        }
    };

    if (loading) {
        return (
            <div style={styles.container as React.CSSProperties}>
                <div style={styles.backBtn as React.CSSProperties} onClick={onBack}>← Back to Teams</div>
                <div style={{ opacity: 0.5, textAlign: 'center', marginTop: 40 }}>Loading team...</div>
            </div>
        );
    }

    if (!team) {
        return (
            <div style={styles.container as React.CSSProperties}>
                <div style={styles.backBtn as React.CSSProperties} onClick={onBack}>← Back to Teams</div>
                <div style={{ opacity: 0.5, textAlign: 'center', marginTop: 40 }}>Team not found</div>
            </div>
        );
    }

    return (
        <div style={styles.container as React.CSSProperties}>
            <div style={styles.backBtn as React.CSSProperties} onClick={onBack}>← Back to Teams</div>

            {/* Team Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
                <span style={{ fontSize: '2rem' }}>{team.icon || '👥'}</span>
                <div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{team.name}</div>
                    <div style={{ fontSize: '0.78rem', opacity: 0.5 }}>
                        {team.member_count || members.length} member{team.member_count !== 1 ? 's' : ''}
                        {' · '}
                        <span style={(styles.badge as (role: unknown) => React.CSSProperties)(team.member_role)}>{team.member_role}</span>
                    </div>
                </div>
                {canManage && !editMode && (
                    <button style={{ ...(styles.btnSecondary as React.CSSProperties), marginLeft: 'auto' }} onClick={handleEdit}>
                        ✏️ Edit
                    </button>
                )}
            </div>

            {/* Edit Team Form */}
            {editMode && (
                <div style={{ ...(styles.card as React.CSSProperties), cursor: 'default', marginBottom: 20 }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 16 }}>Edit Team</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                            <div style={styles.fieldLabel as React.CSSProperties}>Name</div>
                            <input style={styles.input as React.CSSProperties} value={editName} onChange={e => setEditName(e.target.value)} />
                        </div>
                        <div>
                            <div style={styles.fieldLabel as React.CSSProperties}>Description</div>
                            <textarea style={styles.textarea as React.CSSProperties} value={editDesc} onChange={e => setEditDesc(e.target.value)} />
                        </div>
                        <div>
                            <div style={styles.fieldLabel as React.CSSProperties}>Icon (emoji)</div>
                            <input style={styles.input as React.CSSProperties} value={editIcon} onChange={e => setEditIcon(e.target.value)} maxLength={2} />
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button style={styles.btn as React.CSSProperties} onClick={handleSaveEdit}>Save</button>
                            <button style={styles.btnSecondary as React.CSSProperties} onClick={() => setEditMode(false)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Description */}
            {team.description && (
                <div style={{ ...(styles.card as React.CSSProperties), cursor: 'default', marginBottom: 16, padding: 16 }}>
                    <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>{team.description}</div>
                </div>
            )}

            {/* Invite Member */}
            {canManage && (
                <div style={{ ...(styles.card as React.CSSProperties), cursor: 'default', marginBottom: 16 }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12 }}>Invite Member</div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                        <div style={{ flex: 1 }}>
                            <div style={styles.fieldLabel as React.CSSProperties}>Email Address</div>
                            <input style={styles.input as React.CSSProperties} placeholder="user@example.com"
                                value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} />
                        </div>
                        <div>
                            <div style={styles.fieldLabel as React.CSSProperties}>Role</div>
                            <select style={styles.select as React.CSSProperties} value={inviteRole} onChange={e => setInviteRole(e.target.value)}>
                                <option value="member">Member</option>
                                <option value="admin">Admin</option>
                                <option value="viewer">Viewer</option>
                            </select>
                        </div>
                        <button style={styles.btn as React.CSSProperties} onClick={handleInvite}>Invite</button>
                    </div>
                </div>
            )}

            {/* Members List */}
            <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12, marginTop: 8 }}>
                Members ({members.length})
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {members.map(m => (
                    <div key={m.id} style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        padding: '12px 16px', borderRadius: 12,
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.04)',
                    }}>
                        <div style={{
                            width: 36, height: 36, borderRadius: '50%',
                            background: 'rgba(102,126,234,0.2)', color: '#667eea',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: 700, fontSize: '0.85rem', flexShrink: 0,
                        }}>
                            {(m.display_name || m.email || '?')[0].toUpperCase()}
                        </div>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{m.display_name || m.email}</div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.4 }}>{m.email}</div>
                        </div>
                        <span style={(styles.badge as (role: unknown) => React.CSSProperties)(m.role)}>{m.role}</span>

                        {/* Role changer (admin/owner only, not on owner) */}
                        {canManage && m.role !== 'owner' && (
                            <select style={styles.select as React.CSSProperties}
                                value={m.role}
                                onChange={e => handleChangeRole(m.id, e.target.value)}>
                                <option value="member">member</option>
                                <option value="admin">admin</option>
                                <option value="viewer">viewer</option>
                            </select>
                        )}

                        {/* Remove button (admin/owner only, not on self or owner) */}
                        {canManage && m.role !== 'owner' && (
                            <button style={styles.btnDanger as React.CSSProperties}
                                onClick={() => handleRemoveMember(m.id, m.display_name || m.email || '')}>
                                ✕
                            </button>
                        )}
                    </div>
                ))}
            </div>

            {/* Messages */}
            {error && <div style={styles.errMsg as React.CSSProperties}>{error}</div>}
            {success && <div style={styles.successMsg as React.CSSProperties}>{success}</div>}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════
// TeamsPage — Main list view
// ═══════════════════════════════════════════════════════════════════════════

export default function TeamsPage() {
    const [teams, setTeams] = useState<TeamData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [createName, setCreateName] = useState('');
    const [createDesc, setCreateDesc] = useState('');
    const [createIcon, setCreateIcon] = useState('👥');
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    const loadTeams = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const res = await teamsAPI.list();
            const resData = res.data as unknown as ApiResponseData;
            if (resData?.success) {
                setTeams(resData.teams || []);
            }
        } catch (err) {
            setError('Failed to load teams');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadTeams(); }, [loadTeams]);

    const handleCreateTeam = async () => {
        if (!createName.trim()) return;
        setError('');
        setSuccess('');
        try {
            const res = await teamsAPI.create({ name: createName.trim(), description: createDesc.trim(), icon: createIcon });
            const resData = res.data as unknown as ApiResponseData;
            if (resData?.success) {
                setSuccess(`Team "${createName}" created!`);
                setShowCreate(false);
                setCreateName('');
                setCreateDesc('');
                setCreateIcon('👥');
                loadTeams();
            }
        } catch (err) {
            setError(((err as { response?: { data?: { detail?: string } } }).response?.data?.detail) || 'Failed to create team');
        }
    };

    // If a team is selected, show detail view
    if (selectedTeamId) {
        return <TeamDetail teamId={selectedTeamId} onBack={() => setSelectedTeamId(null)} />;
    }

    return (
        <div style={styles.container as React.CSSProperties}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                <div style={styles.title as React.CSSProperties}>👥 Teams</div>
                <button style={styles.btn as React.CSSProperties} onClick={() => setShowCreate(true)}>
                    + New Team
                </button>
            </div>

            {/* Create Team Dialog */}
            {showCreate && (
                <div style={styles.modalOverlay as React.CSSProperties} onClick={() => setShowCreate(false)}>
                    <div style={styles.modal as React.CSSProperties} onClick={e => e.stopPropagation()}>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20 }}>Create New Team</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                            <div>
                                <div style={styles.fieldLabel as React.CSSProperties}>Team Name</div>
                                <input style={styles.input as React.CSSProperties} placeholder="My Team"
                                    value={createName} onChange={e => setCreateName(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleCreateTeam()} />
                            </div>
                            <div>
                                <div style={styles.fieldLabel as React.CSSProperties}>Description (optional)</div>
                                <textarea style={styles.textarea as React.CSSProperties} placeholder="What's this team for?"
                                    value={createDesc} onChange={e => setCreateDesc(e.target.value)} />
                            </div>
                            <div>
                                <div style={styles.fieldLabel as React.CSSProperties}>Icon (emoji)</div>
                                <input style={styles.input as React.CSSProperties} placeholder="👥"
                                    value={createIcon} onChange={e => setCreateIcon(e.target.value)} maxLength={2} />
                            </div>
                            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                <button style={styles.btn as React.CSSProperties} onClick={handleCreateTeam}>Create Team</button>
                                <button style={styles.btnSecondary as React.CSSProperties} onClick={() => setShowCreate(false)}>Cancel</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div style={{ textAlign: 'center', padding: 40, opacity: 0.5 }}>
                    Loading teams...
                </div>
            )}

            {/* Empty State */}
            {!loading && teams.length === 0 && (
                <div style={{ textAlign: 'center', padding: 60, opacity: 0.4 }}>
                    <div style={{ fontSize: '3rem', marginBottom: 12 }}>👥</div>
                    <div style={{ fontSize: '1rem', marginBottom: 8 }}>No teams yet</div>
                    <div style={{ fontSize: '0.85rem' }}>Create a team to start collaborating</div>
                </div>
            )}

            {/* Team List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {teams.map(team => (
                    <div key={team.id} style={{
                        ...(styles.card as React.CSSProperties),
                        ...(hoveredId === team.id ? (styles.cardHover as React.CSSProperties) : {}),
                    }}
                        onClick={() => setSelectedTeamId(team.id)}
                        onMouseEnter={() => setHoveredId(team.id)}
                        onMouseLeave={() => setHoveredId(null)}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                            <span style={{ fontSize: '1.8rem' }}>{team.icon || '👥'}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: '1rem', fontWeight: 600 }}>{team.name}</div>
                                {team.description && (
                                    <div style={{ fontSize: '0.8rem', opacity: 0.5, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 400 }}>
                                        {team.description}
                                    </div>
                                )}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontSize: '0.78rem', opacity: 0.5 }}>
                                    {team.member_count || 0} member{(team.member_count || 0) !== 1 ? 's' : ''}
                                </span>
                                <span style={(styles.badge as (role: unknown) => React.CSSProperties)(team.member_role || 'member')}>
                                    {team.member_role || 'member'}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Messages */}
            {error && <div style={styles.errMsg as React.CSSProperties}>{error}</div>}
            {success && <div style={styles.successMsg as React.CSSProperties}>{success}</div>}
        </div>
    );
}
