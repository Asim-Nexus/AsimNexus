import React, { useState, useEffect } from 'react';
import { marketplaceAPI } from '../../api/asimnexus';

const CATEGORIES = ['All', 'Electronics', 'Clothing', 'Home', 'Books', 'Services', 'Digital', 'Other'];
const CAT_ICONS: Record<string, string> = {
    Electronics: '🔌', Clothing: '👕', Home: '🏠', Books: '📚',
    Services: '🔧', Digital: '💾', Other: '📦',
};
const STATUS_COLOR: Record<string, string> = {
    available: '#10b981', sold: '#667eea', reserved: '#f59e0b', cancelled: '#ef4444',
};
const DELIVERY_ICONS: Record<string, string> = {
    physical: '📦', digital: '💾', service: '🔧',
};

interface MarketplaceEnginePanelProps {
    user?: Record<string, unknown>;
}

interface ListingData {
    id?: string;
    title?: string;
    description?: string;
    price?: number;
    category?: string;
    status?: string;
    delivery_type?: string;
    seller?: string;
    created_at?: string;
}

interface CartItem {
    id?: string;
    listing_id?: string;
    title?: string;
    price?: number;
    seller?: string;
}

interface OrderData {
    id?: string;
    listing_title?: string;
    amount?: number;
    status?: string;
    buyer?: string;
    created_at?: string;
}

interface StatsData {
    total_listings?: number;
    active_listings?: number;
    total_orders?: number;
    total_revenue?: number;
}

const sf = (fn: unknown, ...args: unknown[]): React.CSSProperties => {
    return typeof fn === 'function' ? (fn as (...a: unknown[]) => React.CSSProperties)(...args) : fn as React.CSSProperties;
};

export default function MarketplaceEnginePanel({ user }: MarketplaceEnginePanelProps) {
    const [tab, setTab] = useState<'browse' | 'sell' | 'cart' | 'orders' | 'myListings'>('browse');
    const [listings, setListings] = useState<ListingData[]>([]);
    const [myListings] = useState<ListingData[]>([]);
    const [cart, setCart] = useState<CartItem[]>([]);
    const [orders, setOrders] = useState<OrderData[]>([]);
    const [stats, setStats] = useState<StatsData | null>(null);
    const [category, setCategory] = useState('All');
    const [msg, setMsg] = useState('');
    const [postForm, setPostForm] = useState({
        title: '', description: '', price: '', category: 'Electronics', delivery_type: 'physical',
    });

    const userId = (user?.id as string) || 'default';

    const fetchStats = async () => {
        try {
            const r = await marketplaceAPI.getEngineStats() as unknown as { data?: StatsData };
            if (r.data) setStats(r.data);
        } catch { /* ignore */ }
    };

    useEffect(() => {
        fetchStats();
        marketplaceAPI.listListings({}).then((r: unknown) => {
            const res = r as { data?: { listings?: ListingData[] } };
            if (res.data?.listings) setListings(res.data.listings);
        }).catch(() => { });
        marketplaceAPI.getCart(userId).then((r: unknown) => {
            const res = r as { data?: { items?: CartItem[] } };
            if (res.data?.items) setCart(res.data.items);
        }).catch(() => { });
        marketplaceAPI.listOrders({ user_id: userId }).then((r: unknown) => {
            const res = r as { data?: { orders?: OrderData[] } };
            if (res.data?.orders) setOrders(res.data.orders);
        }).catch(() => { });
    }, [userId]);

    const postListing = async () => {
        if (!postForm.title.trim()) { setMsg('Title required'); return; }
        setMsg('');
        try {
            const r = await marketplaceAPI.createListing({
                title: postForm.title, description: postForm.description,
                price: parseFloat(postForm.price) || 0, category: postForm.category,
                delivery_type: postForm.delivery_type,
            }, userId) as unknown as { data?: { success?: boolean } };
            if (r.data?.success) {
                setMsg('Listing created!');
                setPostForm({ title: '', description: '', price: '', category: 'Electronics', delivery_type: 'physical' });
                fetchStats();
            }
        } catch { setMsg('Failed to create listing'); }
    };

    const addToCart = async (listingId: string) => {
        try {
            await marketplaceAPI.addToCart(userId, listingId);
            setMsg('Added to cart!');
        } catch { setMsg('Failed to add'); }
    };

    const removeFromCart = async (listingId: string) => {
        try {
            await marketplaceAPI.removeFromCart(userId, listingId);
            const r = await marketplaceAPI.getCart(userId) as unknown as { data?: { items?: CartItem[] } };
            if (r.data?.items) setCart(r.data.items);
        } catch { setMsg('Failed to remove'); }
    };

    const checkout = async () => {
        try {
            const r = await marketplaceAPI.checkout(userId, {}) as unknown as { data?: { success?: boolean } };
            if (r.data?.success) {
                setMsg('Checkout complete!');
                setCart([]);
            }
        } catch { setMsg('Checkout failed'); }
    };

    const completeOrder = async (orderId: string) => {
        try {
            await marketplaceAPI.completeOrder(orderId, userId);
            setMsg('Order completed!');
        } catch { setMsg('Failed to complete order'); }
    };

    const filteredListings = category === 'All' ? listings : listings.filter(l => l.category === category);

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
            padding: '8px 14px', borderRadius: 8, cursor: 'pointer', fontSize: '0.78rem',
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
        card: {
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
            background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#10b981',
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
            <div style={s.title as React.CSSProperties}>🏪 Digital Marketplace</div>

            {/* Stats */}
            {stats && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#667eea' }}>{stats.total_listings ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Total Listings</div>
                    </div>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#10b981' }}>{stats.active_listings ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Active</div>
                    </div>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#f59e0b' }}>{stats.total_orders ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Orders</div>
                    </div>
                    <div style={s.statCard as React.CSSProperties}>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#a78bfa' }}>${stats.total_revenue ?? 0}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.5 }}>Revenue</div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
                {(['browse', 'sell', 'cart', 'orders', 'myListings'] as const).map(t => (
                    <button key={t} onClick={() => setTab(t)} style={sf(s.tab, tab === t)}>
                        {t === 'browse' ? '📋 Browse' : t === 'sell' ? '💰 Sell' : t === 'cart' ? `🛒 Cart (${cart.length})` : t === 'orders' ? '📦 Orders' : '📂 My Listings'}
                    </button>
                ))}
            </div>

            {/* Browse Tab */}
            {tab === 'browse' && (
                <div>
                    <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
                        {CATEGORIES.map(c => (
                            <button key={c} onClick={() => setCategory(c)} style={sf(s.catBtn, category === c)}>
                                {CAT_ICONS[c] || ''} {c}
                            </button>
                        ))}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {filteredListings.map(item => (
                            <div key={item.id} style={s.card as React.CSSProperties}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{item.title}</div>
                                        <div style={{ fontSize: '0.78rem', opacity: 0.6, marginBottom: 6 }}>
                                            {CAT_ICONS[item.category || '']} {item.category} · ${item.price}
                                            {' '}{DELIVERY_ICONS[item.delivery_type || ''] || ''}
                                        </div>
                                        <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>
                                            {item.seller} · {item.created_at?.slice(0, 10)}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                                        <span style={{ fontSize: '0.72rem', display: 'flex', alignItems: 'center' }}>
                                            <span style={sf(s.statusDot, item.status)} />{item.status}
                                        </span>
                                        {item.status === 'available' && (
                                            <button onClick={() => { if (item.id) addToCart(item.id); }}
                                                style={{
                                                    padding: '6px 14px', borderRadius: 8, cursor: 'pointer',
                                                    border: '1px solid rgba(16,185,129,0.3)',
                                                    background: 'rgba(16,185,129,0.1)', color: '#10b981',
                                                    fontSize: '0.75rem', fontWeight: 600,
                                                }}>
                                                Add to Cart
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Sell Tab */}
            {tab === 'sell' && (
                <div style={s.formWrap as React.CSSProperties}>
                    <input style={s.input as React.CSSProperties} placeholder="Title"
                        value={postForm.title} onChange={e => setPostForm(p => ({ ...p, title: e.target.value }))} />
                    <textarea style={s.textarea as React.CSSProperties} placeholder="Description"
                        value={postForm.description} onChange={e => setPostForm(p => ({ ...p, description: e.target.value }))} />
                    <div style={{ display: 'flex', gap: 10 }}>
                        <select style={{ ...s.input as React.CSSProperties, flex: 1 }}
                            value={postForm.category} onChange={e => setPostForm(p => ({ ...p, category: e.target.value }))}>
                            {CATEGORIES.filter(c => c !== 'All').map(c => (
                                <option key={c} value={c}>{CAT_ICONS[c]} {c}</option>
                            ))}
                        </select>
                        <select style={{ ...s.input as React.CSSProperties, flex: 1 }}
                            value={postForm.delivery_type} onChange={e => setPostForm(p => ({ ...p, delivery_type: e.target.value }))}>
                            <option value="physical">📦 Physical</option>
                            <option value="digital">💾 Digital</option>
                            <option value="service">🔧 Service</option>
                        </select>
                    </div>
                    <input style={s.input as React.CSSProperties} placeholder="Price ($)" type="number"
                        value={postForm.price} onChange={e => setPostForm(p => ({ ...p, price: e.target.value }))} />
                    <button style={s.btn as React.CSSProperties} onClick={postListing}>Create Listing</button>
                    {msg && <div style={s.msg as React.CSSProperties}>{msg}</div>}
                </div>
            )}

            {/* Cart Tab */}
            {tab === 'cart' && (
                <div>
                    {cart.length === 0 ? (
                        <div style={{ opacity: 0.5, textAlign: 'center', padding: 20 }}>Cart is empty</div>
                    ) : (
                        <>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {cart.map(item => (
                                    <div key={item.id || item.listing_id} style={s.card as React.CSSProperties}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <div>
                                                <div style={{ fontWeight: 600 }}>{item.title}</div>
                                                <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>${item.price} · {item.seller}</div>
                                            </div>
                                            <button onClick={() => { if (item.listing_id) removeFromCart(item.listing_id); }}
                                                style={{
                                                    padding: '6px 12px', borderRadius: 8, cursor: 'pointer',
                                                    border: '1px solid rgba(239,68,68,0.3)',
                                                    background: 'rgba(239,68,68,0.1)', color: '#ef4444',
                                                    fontSize: '0.72rem',
                                                }}>
                                                Remove
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <button onClick={checkout} style={{
                                ...s.btn as React.CSSProperties, marginTop: 16, width: '100%',
                                background: 'linear-gradient(135deg, #10b981, #34d399)',
                            }}>
                                Checkout (${cart.reduce((sum, item) => sum + (item.price || 0), 0).toFixed(2)})
                            </button>
                        </>
                    )}
                </div>
            )}

            {/* Orders Tab */}
            {tab === 'orders' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {orders.map(order => (
                        <div key={order.id} style={s.card as React.CSSProperties}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>{order.listing_title}</div>
                                    <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                        ${order.amount} · {order.created_at?.slice(0, 10)}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <span style={{ fontSize: '0.72rem', opacity: 0.6 }}>{order.status}</span>
                                    {order.status === 'pending' && (
                                        <button onClick={() => { if (order.id) completeOrder(order.id); }}
                                            style={{
                                                padding: '6px 14px', borderRadius: 8, cursor: 'pointer',
                                                border: '1px solid rgba(16,185,129,0.3)',
                                                background: 'rgba(16,185,129,0.1)', color: '#10b981',
                                                fontSize: '0.72rem', fontWeight: 600,
                                            }}>
                                            Complete
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* My Listings Tab */}
            {tab === 'myListings' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {myListings.map(item => (
                        <div key={item.id} style={s.card as React.CSSProperties}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>{item.title}</div>
                                    <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                                        {item.category} · ${item.price}
                                    </div>
                                </div>
                                <span style={{ fontSize: '0.72rem', display: 'flex', alignItems: 'center' }}>
                                    <span style={sf(s.statusDot, item.status)} />{item.status}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
