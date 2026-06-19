import React, { useState, useEffect, useCallback } from 'react';
const getStoredToken = () => localStorage.getItem('asimnexus_token');

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const CATEGORIES = ['all', 'digital_asset', 'service', 'ai_model', 'data', 'compute', 'domain', 'subscription', 'template', 'api_access', 'training', 'consulting'];

const CAT_ICONS = {
  digital_asset: '📄', service: '🔧', ai_model: '🧠', data: '📊',
  compute: '⚡', domain: '🌐', subscription: '🔄', template: '📋',
  api_access: '🔌', training: '🎓', consulting: '💼', other: '📌', all: '🌍',
};

const STATUS_COLOR = {
  active: '#10b981', paused: '#f59e0b', sold: '#3b82f6',
  cancelled: '#6b7280', archived: '#6b7280',
};

const DELIVERY_ICONS = { digital: '💾', physical: '📦', service: '🤝' };

function authHeaders() {
  const token = getStoredToken();
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

export default function MarketplaceEnginePanel({ user }) {
  const [tab, setTab] = useState('browse');
  const [listings, setListings] = useState([]);
  const [cart, setCart] = useState(null);
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedCat, setSelectedCat] = useState('all');
  const [selectedListing, setSelectedListing] = useState(null);
  const [msg, setMsg] = useState('');

  const [postForm, setPostForm] = useState({
    title: '', description: '', category: 'digital_asset', price: 0,
    currency: 'SVT', quantity: 1, tags: '', delivery_type: 'digital',
  });

  const userId = user?.id || user?.user_id || 'user_demo';

  const fetchListings = useCallback(async () => {
    setLoading(true);
    try {
      const params = { status: 'active', limit: 50 };
      if (selectedCat !== 'all') params.category = selectedCat;
      const r = await fetch(`${API}/api/marketplace/listings?${new URLSearchParams(params)}`, { headers: authHeaders() });
      const d = await r.json();
      setListings(d.listings || []);
    } catch { setListings([]); }
    setLoading(false);
  }, [selectedCat]);

  const fetchCart = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/marketplace/cart/${userId}`, { headers: authHeaders() });
      if (r.ok) {
        const d = await r.json();
        setCart(d);
      }
    } catch {}
  }, [userId]);

  const fetchOrders = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/marketplace/orders?user_id=${userId}&limit=20`, { headers: authHeaders() });
      if (r.ok) {
        const d = await r.json();
        setOrders(d.orders || []);
      }
    } catch {}
  }, [userId]);

  const fetchStats = async () => {
    try {
      const r = await fetch(`${API}/api/marketplace/stats`, { headers: authHeaders() });
      if (r.ok) {
        const d = await r.json();
        setStats(d);
      }
    } catch {}
  };

  useEffect(() => { fetchListings(); fetchStats(); }, [fetchListings]);
  useEffect(() => { if (tab === 'cart') fetchCart(); if (tab === 'orders') fetchOrders(); }, [tab, fetchCart, fetchOrders]);

  const postListing = async () => {
    if (!postForm.title.trim() || postForm.price <= 0) {
      setMsg('Title and price required');
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/marketplace/listings?seller_id=${userId}`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          ...postForm,
          tags: postForm.tags.split(',').map(s => s.trim()).filter(Boolean),
        }),
      });
      const d = await r.json();
      if (d.success) {
        setMsg(`✅ Listing created! ID: ${d.listing_id}`);
        setPostForm({ title: '', description: '', category: 'digital_asset', price: 0, currency: 'SVT', quantity: 1, tags: '', delivery_type: 'digital' });
        fetchListings();
        setTab('browse');
      } else {
        setMsg(d.error || 'Create failed');
      }
    } catch (e) { setMsg('Error: ' + e.message); }
    setLoading(false);
  };

  const addToCart = async (listingId) => {
    try {
      const r = await fetch(`${API}/api/marketplace/cart/${userId}/add`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ listing_id: listingId, quantity: 1 }),
      });
      const d = await r.json();
      setMsg(d.success ? '✅ Added to cart!' : d.error);
      if (d.success) fetchCart();
    } catch (e) { setMsg(e.message); }
  };

  const removeFromCart = async (listingId) => {
    try {
      const r = await fetch(`${API}/api/marketplace/cart/${userId}/remove?listing_id=${listingId}`, {
        method: 'POST', headers: authHeaders(),
      });
      const d = await r.json();
      if (d.success) fetchCart();
    } catch {}
  };

  const checkout = async () => {
    try {
      const r = await fetch(`${API}/api/marketplace/cart/${userId}/checkout`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ payment_method: 'svt' }),
      });
      const d = await r.json();
      if (d.success) {
        setMsg(`✅ Checkout complete! ${d.total_orders} order(s) created.`);
        setCart(null);
        fetchOrders();
        setTab('orders');
      } else {
        setMsg(d.error || 'Checkout failed');
      }
    } catch (e) { setMsg(e.message); }
  };

  const completeOrder = async (orderId) => {
    try {
      const r = await fetch(`${API}/api/marketplace/orders/${orderId}/complete?buyer_id=${userId}`, {
        method: 'POST', headers: authHeaders(),
      });
      const d = await r.json();
      setMsg(d.success ? '✅ Order completed!' : d.error);
      if (d.success) fetchOrders();
    } catch (e) { setMsg(e.message); }
  };

  const s = {
    wrap: { padding: 24, minHeight: '100vh' },
    header: { marginBottom: 20 },
    title: { fontSize: '1.5rem', fontWeight: 700,
      background: 'linear-gradient(45deg, #10b981, #3b82f6)',
      WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
    statsRow: { display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 },
    statCard: { background: 'var(--theme-card, rgba(255,255,255,0.05))',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '12px 18px', minWidth: 100, textAlign: 'center' },
    statNum: { fontSize: '1.6rem', fontWeight: 700, color: '#10b981' },
    statLabel: { fontSize: '0.7rem', opacity: 0.5 },
    tabs: { display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' },
    tab: (active) => ({ padding: '8px 18px', borderRadius: 8, cursor: 'pointer', fontSize: '0.85rem',
      background: active ? 'rgba(16,185,129,0.2)' : 'transparent',
      border: active ? '1px solid rgba(16,185,129,0.5)' : '1px solid rgba(255,255,255,0.1)',
      color: active ? '#10b981' : 'rgba(255,255,255,0.6)' }),
    catBar: { display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16 },
    catBtn: (active) => ({ padding: '4px 12px', borderRadius: 20, cursor: 'pointer', fontSize: '0.75rem',
      background: active ? 'rgba(16,185,129,0.25)' : 'rgba(255,255,255,0.04)',
      border: `1px solid ${active ? 'rgba(16,185,129,0.5)' : 'rgba(255,255,255,0.08)'}`,
      color: active ? '#10b981' : 'rgba(255,255,255,0.55)' }),
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 },
    card: { background: 'var(--theme-card, rgba(255,255,255,0.04))',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: 16, cursor: 'pointer',
      transition: 'all 0.2s' },
    cardTitle: { fontWeight: 600, fontSize: '0.95rem', marginBottom: 6 },
    meta: { fontSize: '0.72rem', opacity: 0.55, display: 'flex', gap: 8, flexWrap: 'wrap' },
    statusDot: (status) => ({ display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: STATUS_COLOR[status] || '#6b7280', marginRight: 4 }),
    formWrap: { background: 'var(--theme-card, rgba(255,255,255,0.04))',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 24, maxWidth: 600 },
    input: { width: '100%', padding: '10px 14px', borderRadius: 8, marginBottom: 12,
      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
      color: 'var(--theme-text, #fff)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' },
    textarea: { width: '100%', minHeight: 80, padding: '10px 14px', borderRadius: 8, marginBottom: 12,
      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
      color: 'var(--theme-text, #fff)', fontSize: '0.9rem', outline: 'none',
      resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit' },
    btn: { padding: '10px 22px', borderRadius: 8, border: 'none', cursor: 'pointer',
      background: 'linear-gradient(135deg, #10b981, #3b82f6)', color: '#fff', fontWeight: 600, fontSize: '0.9rem' },
    msg: { padding: '10px 16px', borderRadius: 8, marginBottom: 14, fontSize: '0.85rem',
      background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', color: 'var(--theme-text, #fff)' },
    overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' },
    modal: { background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 20, padding: 28, maxWidth: 520, width: '90%', maxHeight: '80vh', overflow: 'auto' },
  };

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <div style={s.title}>🏪 Digital Marketplace</div>
        <div style={{ fontSize: '0.82rem', opacity: 0.5, marginTop: 4 }}>
          Buy & sell digital assets, AI models, data, services — Dharma-protected
        </div>
      </div>

      {msg && <div style={s.msg}>{msg} <span style={{ cursor: 'pointer', opacity: 0.5, marginLeft: 8 }} onClick={() => setMsg('')}>✕</span></div>}

      <div style={s.statsRow}>
        {[
          ['Listings', stats.active_listings || 0],
          ['Sold', stats.sold_items || 0],
          ['Revenue', `${stats.total_revenue || 0}`],
          ['Orders', stats.completed_orders || 0],
          ['Sellers', stats.total_sellers || 0],
          ...(cart ? [['Cart', `${cart.item_count || 0} items`]] : []),
        ].map(([label, val]) => (
          <div key={label} style={s.statCard}>
            <div style={s.statNum}>{val}</div>
            <div style={s.statLabel}>{label}</div>
          </div>
        ))}
      </div>

      <div style={s.tabs}>
        {[
          ['browse', '🔍 Browse'],
          ['sell', '💰 Sell'],
          ['cart', '🛒 Cart' + (cart?.item_count ? ` (${cart.item_count})` : '')],
          ['orders', '📋 Orders'],
          ['myListings', '📦 My Listings'],
        ].map(([id, label]) => (
          <button key={id} style={s.tab(tab === id)} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {tab === 'browse' && (
        <>
          <div style={s.catBar}>
            {CATEGORIES.map(cat => (
              <button key={cat} style={s.catBtn(selectedCat === cat)} onClick={() => setSelectedCat(cat)}>
                {CAT_ICONS[cat] || '📌'} {cat.replace('_', ' ')}
              </button>
            ))}
          </div>
          {loading ? (
            <div style={{ opacity: 0.5, textAlign: 'center', paddingTop: 40 }}>Loading listings…</div>
          ) : listings.length === 0 ? (
            <div style={{ opacity: 0.4, textAlign: 'center', paddingTop: 40 }}>
              No active listings in this category.<br />
              <button style={{ ...s.btn, marginTop: 16 }} onClick={() => setTab('sell')}>Create the First Listing</button>
            </div>
          ) : (
            <div style={s.grid}>
              {listings.map(lst => (
                <div key={lst.listing_id} style={s.card}
                  onClick={() => setSelectedListing(lst)}
                  onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(16,185,129,0.15)'; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span style={{ fontSize: '1.4rem' }}>{CAT_ICONS[lst.category] || '📌'}</span>
                    <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: 8, background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}>
                      {DELIVERY_ICONS[lst.delivery_type] || '📌'} {lst.delivery_type}
                    </span>
                  </div>
                  <div style={s.cardTitle}>{lst.title}</div>
                  <div style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: 8, lineHeight: 1.4 }}>
                    {lst.description ? lst.description.slice(0, 100) + (lst.description.length > 100 ? '…' : '') : ''}
                  </div>
                  <div style={s.meta}>
                    <span style={{ fontWeight: 700, color: '#10b981' }}>{lst.price} {lst.currency}</span>
                    <span>📦 {lst.quantity} left</span>
                    <span>⭐ {(lst.rating_avg || 0).toFixed(1)} ({lst.rating_count || 0})</span>
                  </div>
                  {lst.tags && lst.tags.length > 0 && (
                    <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {lst.tags.slice(0, 3).map(t => (
                        <span key={t} style={{ padding: '2px 8px', borderRadius: 10, background: 'rgba(16,185,129,0.1)', fontSize: '0.65rem', color: 'rgba(255,255,255,0.6)' }}>{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'sell' && (
        <div style={s.formWrap}>
          <div style={{ fontWeight: 700, marginBottom: 16, fontSize: '1.1rem' }}>Create a Listing</div>
          <input style={s.input} placeholder="Title *" value={postForm.title} onChange={e => setPostForm(p => ({ ...p, title: e.target.value }))} />
          <textarea style={s.textarea} placeholder="Description — what are you selling?" value={postForm.description} onChange={e => setPostForm(p => ({ ...p, description: e.target.value }))} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <input style={s.input} type="number" placeholder="Price *" value={postForm.price || ''} onChange={e => setPostForm(p => ({ ...p, price: parseFloat(e.target.value) || 0 }))} />
            <select style={{ ...s.input, marginBottom: 0 }} value={postForm.currency} onChange={e => setPostForm(p => ({ ...p, currency: e.target.value }))}>
              {['SVT', 'NPR', 'USD', 'EUR', 'NexusCredits'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <input style={s.input} type="number" placeholder="Quantity" value={postForm.quantity} onChange={e => setPostForm(p => ({ ...p, quantity: +e.target.value }))} />
            <select style={{ ...s.input, marginBottom: 0 }} value={postForm.category} onChange={e => setPostForm(p => ({ ...p, category: e.target.value }))}>
              {CATEGORIES.filter(c => c !== 'all').map(c => <option key={c} value={c}>{CAT_ICONS[c]} {c.replace('_', ' ')}</option>)}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <select style={{ ...s.input, marginBottom: 0 }} value={postForm.delivery_type} onChange={e => setPostForm(p => ({ ...p, delivery_type: e.target.value }))}>
              <option value="digital">💾 Digital</option>
              <option value="service">🤝 Service</option>
            </select>
          </div>
          <input style={s.input} placeholder="Tags (comma-separated: ai, data, ...)" value={postForm.tags} onChange={e => setPostForm(p => ({ ...p, tags: e.target.value }))} />
          <button style={s.btn} onClick={postListing} disabled={loading}>
            {loading ? 'Creating…' : '🚀 List Item'}
          </button>
          <div style={{ fontSize: '0.72rem', opacity: 0.4, marginTop: 10 }}>
            ☯️ All listings pass Dharma-Chakra veto before being published.
          </div>
        </div>
      )}

      {tab === 'cart' && (
        <div style={s.formWrap}>
          <div style={{ fontWeight: 700, marginBottom: 16, fontSize: '1.1rem' }}>🛒 Shopping Cart</div>
          {!cart || !cart.items || cart.items.length === 0 ? (
            <div style={{ opacity: 0.5, textAlign: 'center', padding: 30 }}>
              Your cart is empty.<br />
              <button style={{ ...s.btn, marginTop: 12 }} onClick={() => setTab('browse')}>Browse Listings</button>
            </div>
          ) : (
            <>
              {cart.items.map(item => (
                <div key={item.listing_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.listing?.title || item.listing_id}</div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                      {item.quantity} x {item.listing?.price || 0} {item.listing?.currency || ''}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#10b981' }}>
                      {(item.quantity * (item.listing?.price || 0)).toFixed(2)} {item.listing?.currency || ''}
                    </span>
                    <button onClick={() => removeFromCart(item.listing_id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1rem' }}>✕</button>
                  </div>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>Total: {cart.total?.toFixed(2) || 0}</span>
                <button style={{ ...s.btn }} onClick={checkout}>✅ Checkout</button>
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'orders' && (
        <div>
          {orders.length === 0 ? (
            <div style={{ opacity: 0.5, textAlign: 'center', paddingTop: 40 }}>No orders yet.</div>
          ) : (
            <div style={{ display: 'grid', gap: 12 }}>
              {orders.map(order => (
                <div key={order.order_id} style={{ ...s.formWrap, maxWidth: '100%', padding: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                        Order {order.order_id.slice(0, 12)}…
                      </div>
                      <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: 4 }}>
                        {order.quantity} x {order.unit_price} {order.currency} = {order.total_price} {order.currency}
                      </div>
                      <div style={{ fontSize: '0.7rem', opacity: 0.4, marginTop: 2 }}>
                        {order.created_at?.slice(0, 10) || ''}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: '0.7rem', fontWeight: 600,
                        background: order.status === 'completed' ? 'rgba(16,185,129,0.2)' :
                          order.status === 'disputed' ? 'rgba(239,68,68,0.2)' :
                          order.status === 'fulfilled' ? 'rgba(59,130,246,0.2)' :
                          order.status === 'paid' ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.1)',
                        color: order.status === 'completed' ? '#10b981' :
                          order.status === 'disputed' ? '#ef4444' :
                          order.status === 'fulfilled' ? '#3b82f6' :
                          order.status === 'paid' ? '#f59e0b' : 'rgba(255,255,255,0.6)' }}>
                        {order.status.replace('_', ' ')}
                      </span>
                      {order.status === 'fulfilled' && order.buyer_id === userId && (
                        <div><button style={{ ...s.btn, padding: '4px 12px', fontSize: '0.75rem', marginTop: 8 }} onClick={() => completeOrder(order.order_id)}>✓ Complete</button></div>
                      )}
                    </div>
                  </div>
                  {order.dispute_reason && (
                    <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#ef4444', background: 'rgba(239,68,68,0.08)', padding: '6px 10px', borderRadius: 6 }}>
                      Dispute: {order.dispute_reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'myListings' && (
        <div>
          {(() => {
            const myListings = listings.filter(l => l.seller_id === userId);
            if (myListings.length === 0) {
              return <div style={{ opacity: 0.5, textAlign: 'center', paddingTop: 40 }}>You haven't created any listings yet.<br />
                <button style={{ ...s.btn, marginTop: 12 }} onClick={() => setTab('sell')}>Create a Listing</button></div>;
            }
            return (
              <div style={s.grid}>
                {myListings.map(lst => (
                  <div key={lst.listing_id} style={s.card}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontSize: '1.2rem' }}>{CAT_ICONS[lst.category] || '📌'}</span>
                      <span style={s.statusDot(lst.status)} />
                    </div>
                    <div style={s.cardTitle}>{lst.title}</div>
                    <div style={s.meta}>
                      <span>{lst.price} {lst.currency}</span>
                      <span>📦 {lst.quantity}</span>
                      <span style={{
                        color: lst.status === 'active' ? '#10b981' : lst.status === 'paused' ? '#f59e0b' : '#6b7280',
                        textTransform: 'capitalize' }}>{lst.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            );
          })()}
        </div>
      )}

      {selectedListing && (
        <div style={s.overlay} onClick={() => setSelectedListing(null)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <span style={{ fontSize: '1.4rem' }}>{CAT_ICONS[selectedListing.category] || '📌'}</span>
              <button onClick={() => setSelectedListing(null)} style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: 20 }}>✕</button>
            </div>
            <div style={{ fontWeight: 700, fontSize: '1.2rem', marginBottom: 8 }}>{selectedListing.title}</div>
            <div style={{ fontSize: '0.82rem', opacity: 0.6, marginBottom: 12, lineHeight: 1.5 }}>{selectedListing.description}</div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap', fontSize: '0.8rem' }}>
              <span style={{ fontWeight: 700, color: '#10b981', fontSize: '1.1rem' }}>{selectedListing.price} {selectedListing.currency}</span>
              <span>📦 {selectedListing.quantity} available</span>
              <span>⭐ {(selectedListing.rating_avg || 0).toFixed(1)} ({selectedListing.rating_count || 0} reviews)</span>
              <span>{DELIVERY_ICONS[selectedListing.delivery_type] || '📌'} {selectedListing.delivery_type}</span>
            </div>
            {selectedListing.tags?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: '0.72rem', opacity: 0.5, marginBottom: 6 }}>TAGS</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {selectedListing.tags.map(t => (
                    <span key={t} style={{ padding: '3px 10px', borderRadius: 10, background: 'rgba(16,185,129,0.12)', fontSize: '0.75rem', color: '#10b981', border: '1px solid rgba(16,185,129,0.25)' }}>{t}</span>
                  ))}
                </div>
              </div>
            )}
            {selectedListing.seller_id !== userId && selectedListing.status === 'active' && (
              <button style={s.btn} onClick={() => { addToCart(selectedListing.listing_id); setSelectedListing(null); }}>
                🛒 Add to Cart
              </button>
            )}
            <div style={{ fontSize: '0.68rem', opacity: 0.35, marginTop: 8 }}>
              ☯️ Dharma-protected · Escrow-ready · ASIMNEXUS Marketplace
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
