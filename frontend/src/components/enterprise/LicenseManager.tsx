/**
 * LicenseManager — Enterprise License Management
 *
 * Manages enterprise licenses: register new licenses, view existing ones,
 * deactivate licenses, and monitor license usage across organizations.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { enterpriseAPI } from '../../api/asimnexus';

interface License {
    license_id: string;
    organization: string;
    tier: string;
    jurisdiction: string;
    max_users: number;
    max_agents: number;
    features: string[];
    active: boolean;
    created_at: string;
    expires_at?: string;
}

interface EnterpriseStats {
    total_licenses: number;
    active_licenses: number;
    total_compliance_checks: number;
    compliance_breakdown?: Record<string, number>;
    organizations?: string[];
}

interface LicenseManagerProps {
    user?: Record<string, unknown>;
    stats?: EnterpriseStats | null;
    loading?: boolean;
}

const TIER_COLORS: Record<string, string> = {
    free: '#64748b',
    starter: '#3b82f6',
    business: '#f59e0b',
    enterprise: '#8b5cf6',
    government: '#10b981',
};

const TIER_FEATURES: Record<string, string[]> = {
    free: ['basic'],
    starter: ['basic', 'analytics'],
    business: ['basic', 'analytics', 'api_access', 'multi_user'],
    enterprise: ['basic', 'analytics', 'api_access', 'multi_user', 'custom_integrations', 'priority_support'],
    government: ['basic', 'analytics', 'api_access', 'multi_user', 'custom_integrations', 'priority_support', 'compliance'],
};

export default function LicenseManager({ user: _user, stats, loading: parentLoading }: LicenseManagerProps) {
    const [licenses, setLicenses] = useState<License[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [showRegisterForm, setShowRegisterForm] = useState(false);

    // Register form state
    const [orgName, setOrgName] = useState('');
    const [tier, setTier] = useState('starter');
    const [jurisdiction, setJurisdiction] = useState('np');
    const [maxUsers, setMaxUsers] = useState(10);
    const [maxAgents, setMaxAgents] = useState(5);

    const loadLicenses = useCallback(async () => {
        try {
            const res = await enterpriseAPI.getLicenses();
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            const data = (responseData?.data || responseData) as Record<string, unknown>;
            setLicenses((data?.licenses || []) as License[]);
        } catch {
            setLicenses([]);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadLicenses();
        const interval = setInterval(loadLicenses, 30000);
        return () => clearInterval(interval);
    }, [loadLicenses]);

    const handleRegister = async () => {
        if (!orgName.trim()) return;
        setActionLoading('register');
        setMessage(null);
        try {
            const res = await enterpriseAPI.registerLicense({
                organization: orgName,
                tier,
                jurisdiction,
                max_users: maxUsers,
                max_agents: maxAgents,
                features: TIER_FEATURES[tier] || ['basic'],
            });
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: `License registered for ${orgName} ✓` });
                setOrgName('');
                setShowRegisterForm(false);
                loadLicenses();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Registration failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to register license';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const handleDeactivate = async (licenseId: string) => {
        setActionLoading(`deactivate-${licenseId}`);
        setMessage(null);
        try {
            const res = await enterpriseAPI.deactivateLicense(licenseId);
            const responseData = (res?.data || res) as unknown as Record<string, unknown>;
            if (responseData?.status === 'ok' || responseData?.success) {
                setMessage({ type: 'success', text: 'License deactivated ✓' });
                loadLicenses();
            } else {
                setMessage({ type: 'error', text: String(responseData?.detail || responseData?.message || 'Deactivation failed') });
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to deactivate license';
            setMessage({ type: 'error', text: errorMsg });
        }
        setActionLoading(null);
    };

    const displayLoading = parentLoading !== undefined ? parentLoading : loading;

    if (displayLoading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingPulse}>🔑 Loading licenses...</div>
            </div>
        );
    }

    const activeCount = stats?.active_licenses ?? licenses.filter(l => l.active).length;
    const totalCount = stats?.total_licenses ?? licenses.length;

    return (
        <div style={styles.container}>
            {/* Summary Bar */}
            <div style={styles.summaryBar}>
                <div style={styles.summaryItem}>
                    <span style={styles.summaryValue}>{totalCount}</span>
                    <span style={styles.summaryLabel}>Total Licenses</span>
                </div>
                <div style={styles.summaryItem}>
                    <span style={{ ...styles.summaryValue, color: '#10b981' }}>{activeCount}</span>
                    <span style={styles.summaryLabel}>Active</span>
                </div>
                <div style={styles.summaryItem}>
                    <span style={{ ...styles.summaryValue, color: '#64748b' }}>{totalCount - activeCount}</span>
                    <span style={styles.summaryLabel}>Inactive</span>
                </div>
                <button
                    style={styles.registerButton}
                    onClick={() => setShowRegisterForm(!showRegisterForm)}
                >
                    {showRegisterForm ? '✕ Cancel' : '➕ Register License'}
                </button>
            </div>

            {/* Message Banner */}
            {message && (
                <div style={{
                    ...styles.messageBanner,
                    background: message.type === 'success' ? '#052e16' : '#7f1d1d',
                    borderColor: message.type === 'success' ? '#16a34a' : '#dc2626',
                    color: message.type === 'success' ? '#86efac' : '#fca5a5',
                } as React.CSSProperties}>
                    {message.text}
                    <button style={styles.messageClose} onClick={() => setMessage(null)}>✕</button>
                </div>
            )}

            {/* Register Form */}
            {showRegisterForm && (
                <div style={styles.formCard}>
                    <h4 style={styles.formTitle}>Register New License</h4>
                    <input
                        style={styles.formInput}
                        placeholder="Organization Name"
                        value={orgName}
                        onChange={(e) => setOrgName(e.target.value)}
                    />
                    <div style={styles.formRow}>
                        <select
                            style={{ ...styles.formSelect, flex: 1 }}
                            value={tier}
                            onChange={(e) => setTier(e.target.value)}
                        >
                            <option value="free">Free</option>
                            <option value="starter">Starter</option>
                            <option value="business">Business</option>
                            <option value="enterprise">Enterprise</option>
                            <option value="government">Government</option>
                        </select>
                        <select
                            style={{ ...styles.formSelect, flex: 1 }}
                            value={jurisdiction}
                            onChange={(e) => setJurisdiction(e.target.value)}
                        >
                            <option value="np">Nepal (NP)</option>
                            <option value="in">India (IN)</option>
                            <option value="us">United States (US)</option>
                            <option value="eu">European Union (EU)</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div style={styles.formRow}>
                        <div style={styles.formField}>
                            <label style={styles.formLabel}>Max Users</label>
                            <input
                                style={styles.formInput}
                                type="number"
                                value={maxUsers}
                                onChange={(e) => setMaxUsers(parseInt(e.target.value) || 1)}
                                min={1}
                            />
                        </div>
                        <div style={styles.formField}>
                            <label style={styles.formLabel}>Max Agents</label>
                            <input
                                style={styles.formInput}
                                type="number"
                                value={maxAgents}
                                onChange={(e) => setMaxAgents(parseInt(e.target.value) || 1)}
                                min={1}
                            />
                        </div>
                    </div>
                    <div style={styles.featureTags}>
                        {(TIER_FEATURES[tier] || ['basic']).map((f) => (
                            <span key={f} style={styles.featureTag}>{f}</span>
                        ))}
                    </div>
                    <button
                        style={{
                            ...styles.submitButton,
                            opacity: orgName.trim() ? 1 : 0.5,
                        } as React.CSSProperties}
                        onClick={handleRegister}
                        disabled={!orgName.trim() || actionLoading === 'register'}
                    >
                        {actionLoading === 'register' ? '⏳ Registering...' : '📝 Register License'}
                    </button>
                </div>
            )}

            {/* License List */}
            <h4 style={styles.listTitle}>
                Licenses ({licenses.length})
            </h4>
            <div style={styles.licenseList}>
                {licenses.length === 0 ? (
                    <div style={styles.emptyState}>No licenses registered yet</div>
                ) : (
                    licenses.map((license) => (
                        <div key={license.license_id} style={{
                            ...styles.licenseCard,
                            borderLeftColor: license.active ? TIER_COLORS[license.tier] || '#3b82f6' : '#64748b',
                            opacity: license.active ? 1 : 0.6,
                        } as React.CSSProperties}>
                            <div style={styles.licenseHeader}>
                                <div style={styles.licenseHeaderLeft}>
                                    <span style={styles.licenseOrg}>{license.organization}</span>
                                    <span style={{
                                        ...styles.tierBadge,
                                        background: TIER_COLORS[license.tier] || '#64748b',
                                    } as React.CSSProperties}>
                                        {license.tier.toUpperCase()}
                                    </span>
                                </div>
                                <span style={{
                                    ...styles.activeBadge,
                                    color: license.active ? '#10b981' : '#ef4444',
                                    borderColor: license.active ? '#10b981' : '#ef4444',
                                } as React.CSSProperties}>
                                    {license.active ? 'ACTIVE' : 'INACTIVE'}
                                </span>
                            </div>
                            <div style={styles.licenseMeta}>
                                <span>Jurisdiction: {license.jurisdiction.toUpperCase()}</span>
                                <span>Users: {license.max_users}</span>
                                <span>Agents: {license.max_agents}</span>
                            </div>
                            <div style={styles.featureRow}>
                                {license.features.map((f) => (
                                    <span key={f} style={styles.featureChip}>{f}</span>
                                ))}
                            </div>
                            <div style={styles.licenseFooter}>
                                <span style={styles.licenseDate}>
                                    Created: {new Date(license.created_at).toLocaleDateString()}
                                </span>
                                {license.active && (
                                    <button
                                        style={styles.deactivateButton}
                                        onClick={() => handleDeactivate(license.license_id)}
                                        disabled={actionLoading === `deactivate-${license.license_id}`}
                                    >
                                        {actionLoading === `deactivate-${license.license_id}` ? '...' : 'Deactivate'}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div style={styles.footer}>
                <span>49% Private Sector — Enterprise Licensing</span>
                <span style={styles.footerBrand}>AsimNexus 🏢 Digital Nepal</span>
            </div>
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        padding: '20px',
        color: '#e2e8f0',
        maxHeight: 'calc(100vh - 200px)',
        overflowY: 'auto',
    },
    loadingPulse: {
        textAlign: 'center',
        padding: '40px',
        color: '#94a3b8',
        fontSize: '16px',
        animation: 'pulse 1.5s ease-in-out infinite',
    },
    summaryBar: {
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        marginBottom: 16,
        flexWrap: 'wrap',
    },
    summaryItem: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
    },
    summaryValue: {
        fontSize: 24,
        fontWeight: 800,
        color: '#f1f5f9',
    },
    summaryLabel: {
        fontSize: 11,
        color: '#64748b',
    },
    registerButton: {
        marginLeft: 'auto',
        background: '#1e3a5f',
        color: '#93c5fd',
        border: '1px solid #3b82f6',
        borderRadius: 6,
        padding: '6px 14px',
        fontSize: 12,
        fontWeight: 600,
        cursor: 'pointer',
    },
    messageBanner: {
        border: '1px solid',
        borderRadius: 8,
        padding: '10px 14px',
        fontSize: 13,
        marginBottom: 12,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    messageClose: {
        background: 'none',
        border: 'none',
        color: 'inherit',
        cursor: 'pointer',
        fontSize: 14,
        padding: '0 4px',
    },
    formCard: {
        background: '#1e293b',
        border: '1px solid #f59e0b',
        borderRadius: 10,
        padding: 16,
        marginBottom: 16,
    },
    formTitle: {
        margin: '0 0 12px 0',
        fontSize: 14,
        color: '#e2e8f0',
        fontWeight: 600,
    },
    formInput: {
        width: '100%',
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 12px',
        color: '#e2e8f0',
        fontSize: 13,
        marginBottom: 8,
        outline: 'none',
        boxSizing: 'border-box' as const,
    },
    formRow: {
        display: 'flex',
        gap: 8,
        marginBottom: 8,
    },
    formField: {
        flex: 1,
    },
    formLabel: {
        display: 'block',
        fontSize: 11,
        color: '#94a3b8',
        marginBottom: 4,
    },
    formSelect: {
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: 6,
        padding: '8px 12px',
        color: '#e2e8f0',
        fontSize: 13,
        outline: 'none',
    },
    featureTags: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: 4,
        marginBottom: 12,
    },
    featureTag: {
        fontSize: 10,
        background: '#1e3a5f',
        color: '#93c5fd',
        padding: '2px 8px',
        borderRadius: 4,
    },
    submitButton: {
        width: '100%',
        background: '#f59e0b',
        color: '#1e293b',
        border: 'none',
        borderRadius: 6,
        padding: '8px 16px',
        fontSize: 13,
        fontWeight: 600,
        cursor: 'pointer',
    },
    listTitle: {
        margin: '16px 0 10px 0',
        fontSize: 14,
        color: '#cbd5e1',
        fontWeight: 600,
    },
    licenseList: {
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        marginBottom: 16,
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#64748b',
        fontSize: 14,
    },
    licenseCard: {
        background: '#1e293b',
        border: '1px solid #334155',
        borderLeft: '4px solid',
        borderRadius: 8,
        padding: 12,
    },
    licenseHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
    },
    licenseHeaderLeft: {
        display: 'flex',
        gap: 8,
        alignItems: 'center',
    },
    licenseOrg: {
        fontSize: 14,
        fontWeight: 600,
        color: '#e2e8f0',
    },
    tierBadge: {
        fontSize: 10,
        fontWeight: 700,
        color: '#fff',
        padding: '2px 8px',
        borderRadius: 4,
    },
    activeBadge: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid',
    },
    licenseMeta: {
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#64748b',
        marginBottom: 6,
    },
    featureRow: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: 4,
        marginBottom: 6,
    },
    featureChip: {
        fontSize: 10,
        background: '#0f172a',
        color: '#94a3b8',
        padding: '2px 8px',
        borderRadius: 4,
        border: '1px solid #334155',
    },
    licenseFooter: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    licenseDate: {
        fontSize: 10,
        color: '#64748b',
    },
    deactivateButton: {
        background: '#7f1d1d',
        color: '#fca5a5',
        border: '1px solid #dc2626',
        borderRadius: 4,
        padding: '3px 10px',
        fontSize: 11,
        fontWeight: 600,
        cursor: 'pointer',
    },
    footer: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 10,
        color: '#475569',
        borderTop: '1px solid #1e293b',
        paddingTop: 10,
    },
    footerBrand: {
        color: '#7c3aed',
        fontWeight: 600,
    },
};
