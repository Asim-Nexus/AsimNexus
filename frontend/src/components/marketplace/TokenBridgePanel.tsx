import React, { useState, useEffect } from 'react';
import { bridgeAPI } from '../../api/asimnexus';

interface TokenBridgePanelProps {
    user?: Record<string, unknown>;
}

interface PoolData {
    pool_id: string;
    chain: string;
    token_symbol: string;
    token_address?: string;
    balance: number;
    locked_amount: number;
    fee_rate: number;
    [key: string]: unknown;
}

interface TxData {
    tx_id: string;
    status: string;
    from_chain: string;
    to_chain: string;
    amount: number;
    asset: string;
    fee: string;
    [key: string]: unknown;
}

interface StatsResponse {
    total_transactions?: number;
    total_volume_bridged?: number;
    total_fees_collected?: number;
    total_pools?: number;
    total_liquidity?: number;
    [key: string]: unknown;
}

const TokenBridgePanel: React.FC<TokenBridgePanelProps> = ({ user: _user }) => {
    const [stats, setStats] = useState<StatsResponse | null>(null);
    const [pools, setPools] = useState<PoolData[]>([]);
    const [txs, setTxs] = useState<TxData[]>([]);
    const [tab, setTab] = useState<string>('dashboard');
    const [loading, setLoading] = useState<boolean>(false);
    const [msg, setMsg] = useState<string>('');

    const [bridgeForm, setBridgeForm] = useState({
        from_chain: 'nexus', to_chain: 'ethereum', asset: 'NEX',
        amount: 100, sender: '', recipient: '',
    });
    const [poolForm, setPoolForm] = useState({
        chain: 'nexus', token_symbol: 'NEX', initial_balance: 10000,
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            const [sR, pR, tR] = await Promise.all([
                bridgeAPI.getStats(),
                bridgeAPI.listPools(),
                bridgeAPI.listTransactions({ limit: 10 }),
            ]);
            const statsRes = sR as unknown as { data?: StatsResponse };
            const poolsRes = pR as unknown as { data?: { pools?: PoolData[] } };
            const txsRes = tR as unknown as { data?: { transactions?: TxData[] } };
            setStats(statsRes.data || null);
            setPools(poolsRes.data?.pools || []);
            setTxs(txsRes.data?.transactions || []);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }; message?: string };
            setMsg(err.response?.data?.detail || err.message || 'Error');
        }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const initiateBridge = async () => {
        setLoading(true);
        try {
            const r = await bridgeAPI.initiate(
                bridgeForm.from_chain, bridgeForm.to_chain,
                bridgeForm.asset, bridgeForm.amount,
                bridgeForm.sender, bridgeForm.recipient
            );
            const d = r as unknown as { data?: { success?: boolean; tx_id?: string; detail?: string } };
            const data = d.data || {};
            setMsg(data.success ? `✅ Bridge initiated: ${data.tx_id}` : (data.detail || 'Error'));
            if (data.success) fetchData();
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }; message?: string };
            setMsg(err.response?.data?.detail || err.message || 'Error');
        }
        setLoading(false);
    };

    const createPool = async () => {
        setLoading(true);
        try {
            const r = await bridgeAPI.createPool(poolForm.chain, poolForm.token_symbol, poolForm.initial_balance);
            const d = r as unknown as { data?: { success?: boolean; detail?: string } };
            const data = d.data || {};
            setMsg(data.success ? `✅ Pool created` : (data.detail || 'Error'));
            if (data.success) fetchData();
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }; message?: string };
            setMsg(err.response?.data?.detail || err.message || 'Error');
        }
        setLoading(false);
    };

    const s: Record<string, React.CSSProperties | ((active: boolean) => React.CSSProperties)> = {
        wrap: { padding: 24 },
        header: { marginBottom: 20 },
        title: {
            fontSize: '1.5rem', fontWeight: 700,
            background: 'linear-gradient(45deg, #06b6d4, #8b5cf6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        } as React.CSSProperties,
        tabs: { display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' },
        tab: (active: boolean): React.CSSProperties => ({
            padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem',
            background: active ? 'rgba(6,182,212,0.2)' : 'transparent',
            border: active ? '1px solid rgba(6,182,212,0.5)' : '1px solid rgba(255,255,255,0.1)',
            color: active ? '#06b6d4' : 'rgba(255,255,255,0.6)',
        }),
        statsRow: { display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 },
        statCard: {
            background: 'var(--theme-card, rgba(255,255,255,0.05))',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 12, padding: '12px 18px', minWidth: 100, textAlign: 'center',
        },
        statNum: { fontSize: '1.4rem', fontWeight: 700, color: '#06b6d4' },
        statLabel: { fontSize: '0.7rem', opacity: 0.5 },
        input: {
            width: '100%', padding: '10px 14px', borderRadius: 8, marginBottom: 12,
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'var(--theme-text, #fff)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
        },
        btn: {
            padding: '8px 18px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: 'linear-gradient(135deg, #06b6d4, #8b5cf6)',
            color: '#fff', fontWeight: 600, fontSize: '0.85rem', marginRight: 8, marginBottom: 8,
        },
        card: {
            background: 'var(--theme-card, rgba(255,255,255,0.04))',
            border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: 16, marginBottom: 14,
        },
        msg: {
            padding: '10px 16px', borderRadius: 8, marginBottom: 14, fontSize: '0.85rem',
            background: 'rgba(6,182,212,0.12)', border: '1px solid rgba(6,182,212,0.3)',
        },
        grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 14 },
    };

    return (
        <div style={s.wrap as React.CSSProperties}>
            <div style={s.header as React.CSSProperties}>
                <div style={s.title as React.CSSProperties}>🌉 Cross-Chain Token Bridge</div>
                <div style={{ fontSize: '0.82rem', opacity: 0.5, marginTop: 4 }}>
                    Bridge NEX tokens between chains (Nexus, Ethereum, Solana, Bitcoin, ...)
                </div>
            </div>

            {msg && <div style={s.msg as React.CSSProperties}>{msg} <span style={{ cursor: 'pointer', marginLeft: 8 }} onClick={() => setMsg('')}>✕</span></div>}

            {stats && (
                <div style={s.statsRow as React.CSSProperties}>
                    {([
                        ['Transactions', stats.total_transactions],
                        ['Volume', stats.total_volume_bridged],
                        ['Fees', stats.total_fees_collected],
                        ['Pools', stats.total_pools],
                        ['Liquidity', stats.total_liquidity],
                    ] as [string, number | undefined][]).map(([l, v]) => (
                        <div key={l} style={s.statCard as React.CSSProperties}>
                            <div style={s.statNum as React.CSSProperties}>{typeof v === 'number' ? v.toLocaleString() : v}</div>
                            <div style={s.statLabel as React.CSSProperties}>{l}</div>
                        </div>
                    ))}
                </div>
            )}

            <div style={s.tabs as React.CSSProperties}>
                {[['dashboard', '📊 Dashboard'], ['bridge', '🌉 Bridge Tokens'], ['pools', '🏊 Pools'], ['txs', '📋 Transactions']].map(([id, label]) => (
                    <button key={id} style={(s.tab as (active: boolean) => React.CSSProperties)(tab === id)} onClick={() => { setTab(id); fetchData(); }}>{label}</button>
                ))}
            </div>

            {tab === 'dashboard' && (
                <div>
                    <button style={s.btn as React.CSSProperties} onClick={fetchData}>🔄 Refresh</button>
                    <div style={s.grid as React.CSSProperties}>
                        {pools.map(p => (
                            <div key={p.pool_id} style={s.card as React.CSSProperties}>
                                <div style={{ fontWeight: 600, marginBottom: 8 }}>{p.chain.toUpperCase()} — {p.token_symbol}</div>
                                <div style={{ fontSize: '0.82rem' }}>
                                    <div>Balance: <strong>{p.balance}</strong></div>
                                    <div>Locked: <strong>{p.locked_amount}</strong></div>
                                    <div>Fee Rate: <strong>{(p.fee_rate * 100).toFixed(2)}%</strong></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {tab === 'bridge' && (
                <div style={{ maxWidth: 500 }}>
                    <div style={s.card as React.CSSProperties}>
                        <div style={{ fontWeight: 600, marginBottom: 12 }}>Initiate Bridge Transfer</div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                            <select style={s.input as React.CSSProperties} value={bridgeForm.from_chain}
                                onChange={e => setBridgeForm(f => ({ ...f, from_chain: e.target.value }))}>
                                {['nexus', 'ethereum', 'solana', 'bitcoin', 'polygon', 'bsc'].map(c => <option key={c}>{c}</option>)}
                            </select>
                            <select style={s.input as React.CSSProperties} value={bridgeForm.to_chain}
                                onChange={e => setBridgeForm(f => ({ ...f, to_chain: e.target.value }))}>
                                {['nexus', 'ethereum', 'solana', 'bitcoin', 'polygon', 'bsc'].map(c => <option key={c}>{c}</option>)}
                            </select>
                        </div>
                        <input style={s.input as React.CSSProperties} placeholder="Asset (NEX, USDC, ...)" value={bridgeForm.asset}
                            onChange={e => setBridgeForm(f => ({ ...f, asset: e.target.value }))} />
                        <input style={s.input as React.CSSProperties} type="number" placeholder="Amount" value={bridgeForm.amount}
                            onChange={e => setBridgeForm(f => ({ ...f, amount: +e.target.value }))} />
                        <input style={s.input as React.CSSProperties} placeholder="Sender address" value={bridgeForm.sender}
                            onChange={e => setBridgeForm(f => ({ ...f, sender: e.target.value }))} />
                        <input style={s.input as React.CSSProperties} placeholder="Recipient address" value={bridgeForm.recipient}
                            onChange={e => setBridgeForm(f => ({ ...f, recipient: e.target.value }))} />
                        <button style={s.btn as React.CSSProperties} onClick={initiateBridge} disabled={loading}>
                            {loading ? 'Processing…' : '🌉 Bridge Tokens'}
                        </button>
                    </div>
                </div>
            )}

            {tab === 'pools' && (
                <div>
                    <div style={{ maxWidth: 400, marginBottom: 20 }}>
                        <div style={s.card as React.CSSProperties}>
                            <div style={{ fontWeight: 600, marginBottom: 12 }}>Create Liquidity Pool</div>
                            <select style={s.input as React.CSSProperties} value={poolForm.chain}
                                onChange={e => setPoolForm(f => ({ ...f, chain: e.target.value }))}>
                                {['nexus', 'ethereum', 'solana', 'bitcoin', 'polygon', 'bsc'].map(c => <option key={c}>{c}</option>)}
                            </select>
                            <input style={s.input as React.CSSProperties} placeholder="Token Symbol" value={poolForm.token_symbol}
                                onChange={e => setPoolForm(f => ({ ...f, token_symbol: e.target.value }))} />
                            <input style={s.input as React.CSSProperties} type="number" placeholder="Initial Balance" value={poolForm.initial_balance}
                                onChange={e => setPoolForm(f => ({ ...f, initial_balance: +e.target.value }))} />
                            <button style={s.btn as React.CSSProperties} onClick={createPool} disabled={loading}>🏊 Create Pool</button>
                        </div>
                    </div>
                    <div style={{ fontWeight: 600, marginBottom: 12 }}>Existing Pools</div>
                    {pools.length === 0 ? (
                        <div style={{ opacity: 0.4, textAlign: 'center', padding: 20 }}>No pools created yet</div>
                    ) : (
                        <div style={s.grid as React.CSSProperties}>
                            {pools.map(p => (
                                <div key={p.pool_id} style={s.card as React.CSSProperties}>
                                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{p.chain.toUpperCase()}</div>
                                    <div style={{ fontSize: '0.82rem', opacity: 0.7 }}>{p.token_symbol} — {p.token_address}</div>
                                    <div style={{ marginTop: 8, fontSize: '0.85rem' }}>
                                        Balance: <strong>{p.balance.toLocaleString()}</strong> | Locked: <strong>{p.locked_amount.toLocaleString()}</strong>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {tab === 'txs' && (
                <div>
                    <div style={{ fontWeight: 600, marginBottom: 12 }}>Recent Bridge Transactions</div>
                    {txs.length === 0 ? (
                        <div style={{ opacity: 0.4, textAlign: 'center', padding: 20 }}>No transactions yet</div>
                    ) : (
                        txs.map(tx => (
                            <div key={tx.tx_id} style={s.card as React.CSSProperties}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{tx.tx_id?.slice(0, 20)}…</span>
                                    <span style={{
                                        padding: '2px 8px', borderRadius: 8, fontSize: '0.7rem',
                                        background: tx.status === 'released' ? 'rgba(16,185,129,0.2)' :
                                            tx.status === 'failed' ? 'rgba(239,68,68,0.2)' : 'rgba(251,191,36,0.2)',
                                        color: tx.status === 'released' ? '#10b981' :
                                            tx.status === 'failed' ? '#ef4444' : '#f59e0b',
                                    }}>{tx.status}</span>
                                </div>
                                <div style={{ fontSize: '0.78rem', opacity: 0.7 }}>
                                    {tx.from_chain} → {tx.to_chain} | {tx.amount} {tx.asset} | Fee: {tx.fee}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

export default TokenBridgePanel;
