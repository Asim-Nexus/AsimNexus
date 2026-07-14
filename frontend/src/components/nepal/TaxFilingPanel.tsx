/**
 * Tax Filing Panel — Calculate and prepare tax returns
 * Supports Nepal-specific tax rules with multi-country support.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { governmentAPI } from '../../api/asimnexus';

interface TaxCountry {
    code: string;
    name: string;
    currency: string;
}

interface TaxCalculation {
    gross_income: number;
    total_deductions: number;
    taxable_income: number;
    tax_amount: number;
    effective_rate: number;
    currency: string;
    breakdown: Record<string, number>;
}

interface TaxReturn {
    return_id: string;
    status: string;
    tax_year: number;
    total_tax: number;
    currency: string;
    filing_date: string;
}

interface TaxFilingPanelProps {
    user?: Record<string, unknown>;
}

const CARD: React.CSSProperties = {
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    padding: 16,
};

const INPUT: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: 8,
    border: '1px solid rgba(255,255,255,0.1)',
    background: 'rgba(0,0,0,0.3)',
    color: '#e8e8e8',
    fontSize: '0.82rem',
    outline: 'none',
    boxSizing: 'border-box',
};

const LABEL: React.CSSProperties = {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: '#94a3b8',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
};

export default function TaxFilingPanel({ user: _user }: TaxFilingPanelProps) {
    const [activeTab, setActiveTab] = useState<'calculate' | 'prepare' | 'history'>('calculate');
    const [countries, setCountries] = useState<TaxCountry[]>([]);
    const [selectedCountry, setSelectedCountry] = useState('NP');
    const [income, setIncome] = useState(50000);
    const [taxYear, setTaxYear] = useState(2024);
    const [filingStatus, setFilingStatus] = useState('single');
    const [deductions, setDeductions] = useState('');
    const [calculating, setCalculating] = useState(false);
    const [preparing, setPreparing] = useState(false);
    const [calculation, setCalculation] = useState<TaxCalculation | null>(null);
    const [taxReturn, setTaxReturn] = useState<TaxReturn | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const loadCountries = useCallback(async () => {
        try {
            const res = await governmentAPI.getTaxCountries();
            const d = res.data as unknown as Record<string, unknown>;
            const data = d?.data as Record<string, unknown>;
            setCountries(data?.countries as TaxCountry[] || []);
        } catch (err) {
            console.warn('[TaxFiling] Error loading countries:', err);
        }
    }, []);

    useEffect(() => { loadCountries(); }, [loadCountries]);

    const handleCalculate = async () => {
        setCalculating(true);
        setError(null);
        setCalculation(null);
        try {
            const parsedDeductions = deductions
                ? deductions.split(',').map(d => {
                    const [name, amount] = d.trim().split(':');
                    return { name: name?.trim() || 'Deduction', amount: parseFloat(amount) || 0 };
                })
                : [];

            const res = await governmentAPI.calculateTax({
                user_id: 'current',
                country: selectedCountry,
                income,
                deductions: parsedDeductions,
                tax_year: taxYear,
            });
            const d = res.data as unknown as Record<string, unknown>;
            const data = d?.data as TaxCalculation;
            if (data) {
                setCalculation(data);
            } else {
                setError('Failed to calculate tax');
            }
        } catch (err) {
            setError('Calculation failed. Please try again.');
            console.warn('[TaxFiling] Calculate error:', err);
        } finally {
            setCalculating(false);
        }
    };

    const handlePrepareReturn = async () => {
        setPreparing(true);
        setError(null);
        setSuccess(null);
        try {
            const parsedDeductions = deductions
                ? deductions.split(',').map(d => {
                    const [name, amount] = d.trim().split(':');
                    return { name: name?.trim() || 'Deduction', amount: parseFloat(amount) || 0 };
                })
                : [];

            const res = await governmentAPI.prepareTaxReturn({
                user_id: 'current',
                country: selectedCountry,
                income,
                deductions: parsedDeductions,
                tax_year: taxYear,
                filing_status: filingStatus,
            });
            const d = res.data as unknown as Record<string, unknown>;
            const data = d?.data as TaxReturn;
            if (data) {
                setTaxReturn(data);
                setSuccess(`Tax return #${data.return_id} prepared successfully!`);
            } else {
                setError('Failed to prepare tax return');
            }
        } catch (err) {
            setError('Failed to prepare return. Please try again.');
            console.warn('[TaxFiling] Prepare error:', err);
        } finally {
            setPreparing(false);
        }
    };

    const tabs = [
        { id: 'calculate' as const, label: 'Calculate', icon: '🧮' },
        { id: 'prepare' as const, label: 'Prepare Return', icon: '📝' },
        { id: 'history' as const, label: 'History', icon: '📊' },
    ];

    return (
        <div style={{ padding: 16, maxWidth: 700, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b', marginBottom: 4 }}>
                💰 Tax Services
            </div>
            <div style={{ fontSize: '0.75rem', opacity: 0.5, marginBottom: 16 }}>
                Calculate tax liability and prepare returns
            </div>

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
                {tabs.map(tab => (
                    <div
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            padding: '8px 16px',
                            borderRadius: 8,
                            cursor: 'pointer',
                            fontSize: '0.78rem',
                            background: activeTab === tab.id ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                            border: `1px solid ${activeTab === tab.id ? '#f59e0b44' : 'rgba(255,255,255,0.06)'}`,
                            color: activeTab === tab.id ? '#f59e0b' : 'rgba(255,255,255,0.6)',
                        }}
                    >
                        {tab.icon} {tab.label}
                    </div>
                ))}
            </div>

            {/* Calculate Tab */}
            {activeTab === 'calculate' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={CARD}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div>
                                <div style={LABEL}>Country</div>
                                <select value={selectedCountry} onChange={e => setSelectedCountry(e.target.value)} style={INPUT}>
                                    {countries.map(c => (
                                        <option key={c.code} value={c.code}>{c.name} ({c.currency})</option>
                                    ))}
                                    {countries.length === 0 && <option value="NP">🇳🇵 Nepal (NPR)</option>}
                                </select>
                            </div>
                            <div>
                                <div style={LABEL}>Annual Income ({countries.find(c => c.code === selectedCountry)?.currency || 'NPR'})</div>
                                <input type="number" style={INPUT} value={income} onChange={e => setIncome(Number(e.target.value))} />
                            </div>
                            <div>
                                <div style={LABEL}>Tax Year</div>
                                <select value={taxYear} onChange={e => setTaxYear(Number(e.target.value))} style={INPUT}>
                                    <option value={2024}>2024</option>
                                    <option value={2025}>2025</option>
                                    <option value={2026}>2026</option>
                                </select>
                            </div>
                            <div>
                                <div style={LABEL}>Deductions (optional)</div>
                                <input style={INPUT} value={deductions} onChange={e => setDeductions(e.target.value)}
                                    placeholder="e.g., provident_fund:50000, insurance:25000" />
                                <div style={{ fontSize: '0.65rem', opacity: 0.4, marginTop: 4 }}>
                                    Format: name:amount, name:amount (comma-separated)
                                </div>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleCalculate}
                        disabled={calculating || !income}
                        style={{
                            padding: '12px 24px',
                            borderRadius: 8,
                            border: 'none',
                            background: calculating ? 'rgba(245,158,11,0.5)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                            color: 'white',
                            cursor: calculating || !income ? 'not-allowed' : 'pointer',
                            fontSize: '0.85rem',
                            fontWeight: 600,
                        }}
                    >
                        {calculating ? 'Calculating...' : '🧮 Calculate Tax'}
                    </button>

                    {error && (
                        <div style={{ padding: 12, background: 'rgba(239,68,68,0.1)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '0.78rem' }}>
                            {error}
                        </div>
                    )}

                    {calculation && (
                        <div style={CARD}>
                            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#f59e0b', marginBottom: 12 }}>
                                📊 Tax Calculation Result
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.78rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.5 }}>Gross Income</span>
                                    <strong>{calculation.currency} {calculation.gross_income?.toLocaleString()}</strong>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.5 }}>Total Deductions</span>
                                    <strong style={{ color: '#10b981' }}>- {calculation.currency} {calculation.total_deductions?.toLocaleString()}</strong>
                                </div>
                                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.5 }}>Taxable Income</span>
                                    <strong>{calculation.currency} {calculation.taxable_income?.toLocaleString()}</strong>
                                </div>
                                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.5 }}>Tax Amount</span>
                                    <strong style={{ color: '#ef4444', fontSize: '1rem' }}>{calculation.currency} {calculation.tax_amount?.toLocaleString()}</strong>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.5 }}>Effective Rate</span>
                                    <strong>{(calculation.effective_rate * 100)?.toFixed(2)}%</strong>
                                </div>
                            </div>
                            {calculation.breakdown && Object.keys(calculation.breakdown).length > 0 && (
                                <div style={{ marginTop: 12 }}>
                                    <div style={{ fontSize: '0.68rem', opacity: 0.5, marginBottom: 4 }}>Breakdown:</div>
                                    {Object.entries(calculation.breakdown).map(([key, val]) => (
                                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', padding: '2px 0' }}>
                                            <span style={{ opacity: 0.6 }}>{key}</span>
                                            <span>{calculation.currency} {val?.toLocaleString()}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Prepare Return Tab */}
            {activeTab === 'prepare' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={CARD}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div>
                                <div style={LABEL}>Country</div>
                                <select value={selectedCountry} onChange={e => setSelectedCountry(e.target.value)} style={INPUT}>
                                    {countries.map(c => (
                                        <option key={c.code} value={c.code}>{c.name}</option>
                                    ))}
                                    {countries.length === 0 && <option value="NP">🇳🇵 Nepal</option>}
                                </select>
                            </div>
                            <div>
                                <div style={LABEL}>Annual Income</div>
                                <input type="number" style={INPUT} value={income} onChange={e => setIncome(Number(e.target.value))} />
                            </div>
                            <div>
                                <div style={LABEL}>Tax Year</div>
                                <select value={taxYear} onChange={e => setTaxYear(Number(e.target.value))} style={INPUT}>
                                    <option value={2024}>2024</option>
                                    <option value={2025}>2025</option>
                                    <option value={2026}>2026</option>
                                </select>
                            </div>
                            <div>
                                <div style={LABEL}>Filing Status</div>
                                <select value={filingStatus} onChange={e => setFilingStatus(e.target.value)} style={INPUT}>
                                    <option value="single">Single</option>
                                    <option value="married_joint">Married (Joint)</option>
                                    <option value="married_separate">Married (Separate)</option>
                                    <option value="head_of_household">Head of Household</option>
                                </select>
                            </div>
                            <div>
                                <div style={LABEL}>Deductions (optional)</div>
                                <input style={INPUT} value={deductions} onChange={e => setDeductions(e.target.value)}
                                    placeholder="e.g., provident_fund:50000, insurance:25000" />
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handlePrepareReturn}
                        disabled={preparing || !income}
                        style={{
                            padding: '12px 24px',
                            borderRadius: 8,
                            border: 'none',
                            background: preparing ? 'rgba(16,185,129,0.5)' : 'linear-gradient(135deg, #10b981, #059669)',
                            color: 'white',
                            cursor: preparing || !income ? 'not-allowed' : 'pointer',
                            fontSize: '0.85rem',
                            fontWeight: 600,
                        }}
                    >
                        {preparing ? 'Preparing...' : '📝 Prepare Tax Return'}
                    </button>

                    {error && (
                        <div style={{ padding: 12, background: 'rgba(239,68,68,0.1)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '0.78rem' }}>
                            {error}
                        </div>
                    )}

                    {success && (
                        <div style={{ padding: 12, background: 'rgba(16,185,129,0.1)', borderRadius: 8, border: '1px solid rgba(16,185,129,0.3)', color: '#10b981', fontSize: '0.78rem' }}>
                            {success}
                        </div>
                    )}

                    {taxReturn && (
                        <div style={CARD}>
                            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#10b981', marginBottom: 12 }}>
                                ✅ Tax Return Prepared
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.78rem' }}>
                                <div><span style={{ opacity: 0.5 }}>Return ID:</span> <strong>{taxReturn.return_id}</strong></div>
                                <div><span style={{ opacity: 0.5 }}>Status:</span> <strong style={{ color: '#10b981' }}>{taxReturn.status}</strong></div>
                                <div><span style={{ opacity: 0.5 }}>Tax Year:</span> <strong>{taxReturn.tax_year}</strong></div>
                                <div><span style={{ opacity: 0.5 }}>Total Tax:</span> <strong>{taxReturn.currency} {taxReturn.total_tax?.toLocaleString()}</strong></div>
                                <div><span style={{ opacity: 0.5 }}>Filing Date:</span> <strong>{taxReturn.filing_date}</strong></div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
                <div style={CARD}>
                    <div style={{ textAlign: 'center', padding: 24 }}>
                        <div style={{ fontSize: '2rem', marginBottom: 8 }}>📊</div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Tax filing history will appear here</div>
                        <div style={{ fontSize: '0.72rem', opacity: 0.4, marginTop: 4 }}>
                            Use "Prepare Return" to file your first tax return
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
