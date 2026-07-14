/**
 * Nepal Payment Gateway — connectIPS, eSewa, Khalti Integration
 * Real payment UI backed by core/nepal/banking_integrations.py
 *
 * Supports:
 *   - eSewa (Digital Wallet)
 *   - Khalti (Digital Wallet)
 *   - ConnectIPS (NCHL Bank Transfer)
 *   - NIBL Ace Pay, Prabhu Pay, FonePay
 *   - Nepal tax breakdown (13% VAT, 1% TDS)
 *   - Transaction history & status
 */
import React, { useState, useEffect, useCallback } from 'react';
import { financeAPI } from '../../api/asimnexus';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ProviderInfo {
    key: string;
    name: string;
    type: string;
    currencies: string[];
    status: string;
    fee_pct: number;
}

interface TaxBreakdown {
    vat_rate: number;
    vat_label: string;
    tds_rate: number;
    tds_label: string;
    service_charge_rate: number;
    service_charge_label: string;
    country: string;
    reference?: string;
}

interface BankingStatus {
    country: string;
    providers_available: number;
    total_providers: number;
    providers: string[];
    currencies_supported: string[];
    tpm_secured: boolean;
    ledger_sync: boolean;
    saga_integrated: boolean;
    pending_transactions: number;
    completed_transactions: number;
    status: string;
}

interface PaymentResult {
    success: boolean;
    provider: string;
    provider_name: string;
    transaction_id: string;
    amount: number;
    currency: string;
    fee: number;
    total: number;
    status: string;
    request_id: string;
    idempotency_key: string;
    timestamp: number;
}

// ── Styles ────────────────────────────────────────────────────────────────────

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    padding: 16,
};

const INPUT: React.CSSProperties = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: '10px 14px',
    color: '#e2e8f0',
    fontSize: '0.85rem',
    width: '100%',
    outline: 'none',
    boxSizing: 'border-box' as const,
};

const BTN_PRIMARY: React.CSSProperties = {
    background: 'linear-gradient(135deg, #c9a84c, #a8882e)',
    border: 'none',
    borderRadius: 8,
    padding: '10px 24px',
    color: '#0a0a1a',
    fontWeight: 700,
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'all 0.15s',
};

const BTN_SECONDARY: React.CSSProperties = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    padding: '10px 24px',
    color: '#e2e8f0',
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'all 0.15s',
};

const BADGE_BASE: React.CSSProperties = {
    display: 'inline-block',
    padding: '2px 10px',
    borderRadius: 20,
    fontSize: '0.68rem',
    fontWeight: 600,
};

const SECTION_HEADER: React.CSSProperties = {
    fontSize: '0.85rem',
    fontWeight: 700,
    color: '#c9a84c',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
};

// ── Provider Icons ────────────────────────────────────────────────────────────

const PROVIDER_ICONS: Record<string, string> = {
    esewa: '💳',
    khalti: '🔵',
    connectips: '🏦',
    nibl_acepay: '🏛️',
    prabhu_pay: '💜',
    fonepay: '📱',
};

const PROVIDER_COLORS: Record<string, string> = {
    esewa: '#10b981',
    khalti: '#3b82f6',
    connectips: '#f59e0b',
    nibl_acepay: '#8b5cf6',
    prabhu_pay: '#ec4899',
    fonepay: '#06b6d4',
};

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
    const color = status === 'active' || status === 'completed' || status === 'success'
        ? '#10b981'
        : status === 'pending' || status === 'processing'
            ? '#f59e0b'
            : '#ef4444';
    return (
        <span style={{ ...BADGE_BASE, background: `${color}22`, color, border: `1px solid ${color}44` }}>
            {status}
        </span>
    );
}

function ProviderCard({ provider, selected, onSelect }: { provider: ProviderInfo; selected: boolean; onSelect: () => void }) {
    const icon = PROVIDER_ICONS[provider.key] || '🏦';
    const color = PROVIDER_COLORS[provider.key] || '#c9a84c';
    return (
        <div
            onClick={onSelect}
            style={{
                ...CARD,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                border: `1px solid ${selected ? `${color}66` : 'rgba(255,255,255,0.08)'}`,
                background: selected ? `${color}11` : 'rgba(255,255,255,0.04)',
                transition: 'all 0.15s',
                flex: '1 1 180px',
                minWidth: 160,
            }}
            onMouseEnter={e => { if (!selected) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.08)'; }}
            onMouseLeave={e => { if (!selected) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)'; }}
        >
            <span style={{ fontSize: '1.5rem' }}>{icon}</span>
            <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{provider.name}</div>
                <div style={{ fontSize: '0.65rem', opacity: 0.5, textTransform: 'capitalize' }}>
                    {provider.type.replace('_', ' ')} · {provider.fee_pct}% fee
                </div>
            </div>
            {selected && <span style={{ color, fontSize: '1.1rem' }}>✓</span>}
        </div>
    );
}

// ── Main Component ────────────────────────────────────────────────────────────

interface NepalPaymentGatewayProps {
    user?: Record<string, unknown>;
}

export default function NepalPaymentGateway({ user }: NepalPaymentGatewayProps) {
    const [providers, setProviders] = useState<ProviderInfo[]>([]);
    const [taxBreakdown, setTaxBreakdown] = useState<TaxBreakdown | null>(null);
    const [bankingStatus, setBankingStatus] = useState<BankingStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Payment form state
    const [selectedProvider, setSelectedProvider] = useState<string>('');
    const [amount, setAmount] = useState<string>('1000');
    const [description, setDescription] = useState<string>('Payment via AsimNexus');
    const [processing, setProcessing] = useState(false);
    const [paymentResult, setPaymentResult] = useState<PaymentResult | null>(null);

    // Transaction history
    const [activeTab, setActiveTab] = useState<'pay' | 'history' | 'status'>('pay');

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [provRes, taxRes, statusRes] = await Promise.allSettled([
                financeAPI.getNepalProviders(),
                financeAPI.getNepalTaxBreakdown(),
                financeAPI.getNepalBankingStatus(),
            ]);

            if (provRes.status === 'fulfilled') {
                const d = provRes.value.data as unknown as Record<string, unknown>;
                const list = (d?.data as Record<string, unknown>)?.providers as ProviderInfo[] || [];
                setProviders(list);
                if (list.length > 0 && !selectedProvider) {
                    setSelectedProvider(list[0].key);
                }
            }
            if (taxRes.status === 'fulfilled') {
                const d = taxRes.value.data as unknown as Record<string, unknown>;
                setTaxBreakdown(d?.data as TaxBreakdown);
            }
            if (statusRes.status === 'fulfilled') {
                const d = statusRes.value.data as unknown as Record<string, unknown>;
                setBankingStatus(d?.data as BankingStatus);
            }
        } catch (err) {
            console.warn('[NepalPaymentGateway] Error loading data:', err);
            setError('Failed to load payment gateway data');
        } finally {
            setLoading(false);
        }
    }, [selectedProvider]);

    useEffect(() => { loadData(); }, []);

    const handlePay = async () => {
        if (!selectedProvider || !amount || parseFloat(amount) <= 0) return;
        setProcessing(true);
        setPaymentResult(null);
        setError(null);
        try {
            const res = await financeAPI.initiateNepalPayment({
                provider: selectedProvider,
                amount: parseFloat(amount),
                currency: 'NPR',
                user_id: (user?.id as string) || 'anonymous',
                description: description || `Payment via ${selectedProvider}`,
            });
            const d = res.data as unknown as Record<string, unknown>;
            const result = d?.data as PaymentResult;
            setPaymentResult(result);
            if (result?.success) {
                // Refresh status after payment
                const statusRes = await financeAPI.getNepalBankingStatus();
                const sd = statusRes.data as unknown as Record<string, unknown>;
                setBankingStatus(sd?.data as BankingStatus);
            }
        } catch (err) {
            console.warn('[NepalPaymentGateway] Payment error:', err);
            setError('Payment failed. Please try again.');
        } finally {
            setProcessing(false);
        }
    };

    const selectedProviderInfo = providers.find(p => p.key === selectedProvider);

    // Calculate tax breakdown for the entered amount
    const numAmount = parseFloat(amount) || 0;
    const vatAmount = taxBreakdown ? Math.round(numAmount * taxBreakdown.vat_rate * 100) / 100 : 0;
    const tdsAmount = taxBreakdown ? Math.round(numAmount * taxBreakdown.tds_rate * 100) / 100 : 0;
    const serviceCharge = taxBreakdown ? Math.round(numAmount * taxBreakdown.service_charge_rate * 100) / 100 : 0;
    const feeAmount = selectedProviderInfo ? Math.round(numAmount * (selectedProviderInfo.fee_pct / 100) * 100) / 100 : 0;
    const totalAmount = numAmount + feeAmount + vatAmount + serviceCharge;

    if (loading) {
        return (
            <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>🇳🇵</div>
                <div>Loading Nepal Payment Gateway...</div>
            </div>
        );
    }

    return (
        <div style={{ padding: 16, maxWidth: 900, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#c9a84c' }}>
                        💳 Nepal Payment Gateway
                    </div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: 2 }}>
                        connectIPS · eSewa · Khalti — Nepal Rastra Bank Compliant
                    </div>
                </div>
                {bankingStatus && <StatusBadge status={bankingStatus.status} />}
            </div>

            {error && (
                <div style={{ ...CARD, border: '1px solid #ef444444', background: '#ef444411', color: '#ef4444', marginBottom: 16, fontSize: '0.82rem' }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
                {[
                    { id: 'pay' as const, label: 'Pay', icon: '💳' },
                    { id: 'history' as const, label: 'History', icon: '📋' },
                    { id: 'status' as const, label: 'Status', icon: '📊' },
                ].map(tab => (
                    <div
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            padding: '8px 16px',
                            borderRadius: 8,
                            cursor: 'pointer',
                            fontSize: '0.78rem',
                            background: activeTab === tab.id ? 'rgba(201,168,76,0.15)' : 'rgba(255,255,255,0.04)',
                            border: `1px solid ${activeTab === tab.id ? '#c9a84c44' : 'rgba(255,255,255,0.06)'}`,
                            color: activeTab === tab.id ? '#c9a84c' : 'rgba(255,255,255,0.6)',
                            transition: 'all 0.15s',
                        }}
                    >
                        {tab.icon} {tab.label}
                    </div>
                ))}
            </div>

            {/* ── Pay Tab ── */}
            {activeTab === 'pay' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {/* Provider Selection */}
                    <div style={SECTION_HEADER}>🏦 Select Payment Provider</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        {providers.map(p => (
                            <ProviderCard
                                key={p.key}
                                provider={p}
                                selected={selectedProvider === p.key}
                                onSelect={() => setSelectedProvider(p.key)}
                            />
                        ))}
                    </div>

                    {/* Payment Form */}
                    <div style={SECTION_HEADER}>📝 Payment Details</div>
                    <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                            <div style={{ flex: '1 1 200px' }}>
                                <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Amount (NPR)</div>
                                <input
                                    type="number"
                                    value={amount}
                                    onChange={e => setAmount(e.target.value)}
                                    placeholder="Enter amount in NPR"
                                    style={INPUT}
                                    min="1"
                                />
                            </div>
                            <div style={{ flex: '1 1 200px' }}>
                                <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Currency</div>
                                <div style={{ ...INPUT, opacity: 0.6, cursor: 'not-allowed' }}>
                                    🇳🇵 NPR (Nepalese Rupee)
                                </div>
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 4 }}>Description</div>
                            <input
                                type="text"
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                placeholder="Payment description"
                                style={INPUT}
                            />
                        </div>
                    </div>

                    {/* Fee & Tax Breakdown */}
                    {numAmount > 0 && (
                        <div style={SECTION_HEADER}>🧾 Fee & Tax Breakdown</div>
                    )}
                    {numAmount > 0 && (
                        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                <span style={{ opacity: 0.6 }}>Base Amount</span>
                                <span>🇳🇵 NPR {numAmount.toFixed(2)}</span>
                            </div>
                            {selectedProviderInfo && selectedProviderInfo.fee_pct > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                    <span style={{ opacity: 0.6 }}>Provider Fee ({selectedProviderInfo.fee_pct}%)</span>
                                    <span style={{ color: '#f59e0b' }}>🇳🇵 NPR {feeAmount.toFixed(2)}</span>
                                </div>
                            )}
                            {taxBreakdown && (
                                <>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                        <span style={{ opacity: 0.6 }}>{taxBreakdown.vat_label}</span>
                                        <span style={{ color: '#ef4444' }}>🇳🇵 NPR {vatAmount.toFixed(2)}</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                        <span style={{ opacity: 0.6 }}>{taxBreakdown.tds_label}</span>
                                        <span style={{ color: '#ef4444' }}>🇳🇵 NPR {tdsAmount.toFixed(2)}</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                        <span style={{ opacity: 0.6 }}>{taxBreakdown.service_charge_label}</span>
                                        <span style={{ color: '#f59e0b' }}>🇳🇵 NPR {serviceCharge.toFixed(2)}</span>
                                    </div>
                                </>
                            )}
                            <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 8, display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem', fontWeight: 700 }}>
                                <span>Total Charge</span>
                                <span style={{ color: '#c9a84c' }}>🇳🇵 NPR {totalAmount.toFixed(2)}</span>
                            </div>
                        </div>
                    )}

                    {/* Pay Button */}
                    <button
                        onClick={handlePay}
                        disabled={processing || !selectedProvider || !amount || parseFloat(amount) <= 0}
                        style={{
                            ...BTN_PRIMARY,
                            opacity: processing || !selectedProvider || !amount || parseFloat(amount) <= 0 ? 0.5 : 1,
                            width: '100%',
                            padding: '14px 24px',
                            fontSize: '1rem',
                        }}
                    >
                        {processing ? (
                            <span>⏳ Processing Payment...</span>
                        ) : (
                            <span>💳 Pay NPR {numAmount.toFixed(2)} via {selectedProviderInfo?.name || selectedProvider}</span>
                        )}
                    </button>

                    {/* Payment Result */}
                    {paymentResult && (
                        <div style={{
                            ...CARD,
                            border: `1px solid ${paymentResult.success ? '#10b98144' : '#ef444444'}`,
                            background: paymentResult.success ? '#10b98111' : '#ef444411',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                <span style={{ fontSize: '1.2rem' }}>{paymentResult.success ? '✅' : '❌'}</span>
                                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: paymentResult.success ? '#10b981' : '#ef4444' }}>
                                    {paymentResult.success ? 'Payment Successful!' : 'Payment Failed'}
                                </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: '0.78rem', opacity: 0.8 }}>
                                <div>Transaction ID: <span style={{ fontFamily: 'monospace', color: '#c9a84c' }}>{paymentResult.transaction_id}</span></div>
                                <div>Provider: {paymentResult.provider_name} ({paymentResult.provider})</div>
                                <div>Amount: 🇳🇵 NPR {paymentResult.amount.toFixed(2)}</div>
                                <div>Fee: 🇳🇵 NPR {paymentResult.fee.toFixed(2)}</div>
                                <div>Total Charged: 🇳🇵 NPR {paymentResult.total.toFixed(2)}</div>
                                <div>Status: <StatusBadge status={paymentResult.status} /></div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── History Tab ── */}
            {activeTab === 'history' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={SECTION_HEADER}>📋 Recent Transactions</div>
                    {bankingStatus && bankingStatus.completed_transactions > 0 ? (
                        <div style={{ ...CARD, fontSize: '0.82rem', opacity: 0.7 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontWeight: 600, color: '#c9a84c' }}>
                                <span>Total Completed: {bankingStatus.completed_transactions}</span>
                                <span>Pending: {bankingStatus.pending_transactions}</span>
                            </div>
                            <div style={{ fontSize: '0.75rem' }}>
                                Transaction history is available via the backend ledger.
                                Use the Finance Ledger panel for full transaction details.
                            </div>
                        </div>
                    ) : (
                        <div style={{ ...CARD, textAlign: 'center', color: '#94a3b8', padding: 24 }}>
                            <div style={{ fontSize: '2rem', marginBottom: 8 }}>📭</div>
                            <div>No transactions yet. Make your first payment above!</div>
                        </div>
                    )}

                    {/* Quick Stats */}
                    <div style={SECTION_HEADER}>📊 Payment Stats</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                        <div style={{ ...CARD, flex: '1 1 140px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#10b981' }}>
                                {bankingStatus?.completed_transactions ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>Completed</div>
                        </div>
                        <div style={{ ...CARD, flex: '1 1 140px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>
                                {bankingStatus?.pending_transactions ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>Pending</div>
                        </div>
                        <div style={{ ...CARD, flex: '1 1 140px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#3b82f6' }}>
                                {bankingStatus?.providers_available ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>Active Providers</div>
                        </div>
                        <div style={{ ...CARD, flex: '1 1 140px', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#c9a84c' }}>
                                {bankingStatus?.total_providers ?? 0}
                            </div>
                            <div style={{ fontSize: '0.68rem', opacity: 0.5 }}>Total Providers</div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Status Tab ── */}
            {activeTab === 'status' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={SECTION_HEADER}>📊 System Status</div>

                    {/* Banking Status */}
                    {bankingStatus && (
                        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>🇳🇵 Nepal Banking Integration</span>
                                <StatusBadge status={bankingStatus.status} />
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.78rem' }}>
                                <div><span style={{ opacity: 0.5 }}>Country:</span> {bankingStatus.country}</div>
                                <div><span style={{ opacity: 0.5 }}>Currencies:</span> {bankingStatus.currencies_supported.join(', ')}</div>
                                <div>
                                    <span style={{ opacity: 0.5 }}>TPM Secured:</span>{' '}
                                    <span style={{ color: bankingStatus.tpm_secured ? '#10b981' : '#f59e0b' }}>
                                        {bankingStatus.tpm_secured ? '✅ Yes' : '⚠️ No'}
                                    </span>
                                </div>
                                <div>
                                    <span style={{ opacity: 0.5 }}>Ledger Sync:</span>{' '}
                                    <span style={{ color: bankingStatus.ledger_sync ? '#10b981' : '#ef4444' }}>
                                        {bankingStatus.ledger_sync ? '✅ Active' : '❌ Inactive'}
                                    </span>
                                </div>
                                <div>
                                    <span style={{ opacity: 0.5 }}>Saga Integration:</span>{' '}
                                    <span style={{ color: bankingStatus.saga_integrated ? '#10b981' : '#94a3b8' }}>
                                        {bankingStatus.saga_integrated ? '✅ Active' : '⚪ Not Available'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Tax Breakdown */}
                    {taxBreakdown && (
                        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#c9a84c' }}>
                                🧾 Nepal Tax Rates (IT Act 2063)
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.78rem' }}>
                                <div><span style={{ opacity: 0.5 }}>VAT:</span> {taxBreakdown.vat_label}</div>
                                <div><span style={{ opacity: 0.5 }}>TDS:</span> {taxBreakdown.tds_label}</div>
                                <div><span style={{ opacity: 0.5 }}>Service Charge:</span> {taxBreakdown.service_charge_label}</div>
                                <div><span style={{ opacity: 0.5 }}>Reference:</span> {taxBreakdown.reference}</div>
                            </div>
                        </div>
                    )}

                    {/* Provider List */}
                    <div style={SECTION_HEADER}>🏦 Available Providers</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {providers.map(p => {
                            const icon = PROVIDER_ICONS[p.key] || '🏦';
                            return (
                                <div key={p.key} style={{ ...CARD, display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span style={{ fontSize: '1.3rem' }}>{icon}</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{p.name}</div>
                                        <div style={{ fontSize: '0.68rem', opacity: 0.5, textTransform: 'capitalize' }}>
                                            {p.type.replace('_', ' ')} · {p.fee_pct}% fee · {p.currencies.join(', ')}
                                        </div>
                                    </div>
                                    <StatusBadge status={p.status} />
                                </div>
                            );
                        })}
                    </div>

                    {/* Refresh Button */}
                    <button onClick={loadData} style={{ ...BTN_SECONDARY, alignSelf: 'flex-start' }}>
                        🔄 Refresh Status
                    </button>
                </div>
            )}
        </div>
    );
}
