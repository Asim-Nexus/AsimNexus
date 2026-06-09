import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, TextInput, Alert, FlatList } from 'react-native';
import { marketplaceAPI } from '../services/economyAPI';

const MarketplaceScreen = () => {
    const [listings, setListings] = useState([]);
    const [stats, setStats] = useState(null);
    const [sellerId, setSellerId] = useState('');
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [price, setPrice] = useState('');
    const [category, setCategory] = useState('general');
    const [query, setQuery] = useState('');
    const [listingId, setListingId] = useState('');
    const [selectedListing, setSelectedListing] = useState(null);
    const [buyerId, setBuyerId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('browse');

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const res = await marketplaceAPI.searchListings('', null, null, null, 'active');
            if (!res.error) setListings(res.listings || res.results || res || []);
            const s = await marketplaceAPI.getMarketplaceStats();
            if (!s.error) setStats(s);
        } catch (_) { }
        setLoading(false);
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    const handleCreate = async () => {
        if (!sellerId || !title || !price) {
            Alert.alert('Error', 'Seller ID, Title, and Price required');
            return;
        }
        setLoading(true);
        try {
            const res = await marketplaceAPI.createListing(sellerId, title, description, parseFloat(price), category);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Listing created: ${res.listing_id || res.id}`);
            setTitle(''); setDescription(''); setPrice(''); setCategory('general');
            await loadData();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleSearch = async () => {
        setLoading(true);
        try {
            const res = await marketplaceAPI.searchListings(query);
            if (!res.error) setListings(res.listings || res.results || res || []);
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleOrder = async () => {
        if (!listingId || !buyerId) {
            Alert.alert('Error', 'Listing ID and Buyer ID required');
            return;
        }
        setLoading(true);
        try {
            const res = await marketplaceAPI.createOrder(listingId, buyerId, 1);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Order created: ${res.order_id || res.id}`);
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const tabs = ['browse', 'create', 'order'];
    const tabLabels = { browse: 'Browse', create: 'Sell', order: 'Buy' };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>🏪 Marketplace</Text>

            {error && (
                <View style={styles.errorBanner}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            <View style={styles.tabRow}>
                {tabs.map((t) => (
                    <TouchableOpacity key={t} style={[styles.tab, activeTab === t && styles.activeTab]} onPress={() => setActiveTab(t)}>
                        <Text style={[styles.tabText, activeTab === t && styles.activeTabText]}>{tabLabels[t]}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            {activeTab === 'browse' && (
                <>
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Search Listings</Text>
                        <TextInput style={styles.input} placeholder="Search query..." value={query} onChangeText={setQuery} />
                        <TouchableOpacity style={styles.button} onPress={handleSearch} disabled={loading}>
                            <Text style={styles.buttonText}>Search</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={[styles.button, { backgroundColor: '#7c3aed' }]} onPress={loadData} disabled={loading}>
                            <Text style={styles.buttonText}>Refresh All</Text>
                        </TouchableOpacity>
                    </View>

                    {listings.length > 0 && (
                        <View style={styles.card}>
                            <Text style={styles.cardTitle}>Active Listings ({listings.length})</Text>
                            {listings.map((l, i) => (
                                <TouchableOpacity key={i} style={styles.listingItem} onPress={() => { setListingId(l.listing_id || l.id); setSelectedListing(l); }}>
                                    <View style={{ flex: 1 }}>
                                        <Text style={styles.listingTitle}>{l.title}</Text>
                                        <Text style={styles.listingDesc} numberOfLines={2}>{l.description}</Text>
                                        <Text style={styles.listingSeller}>Seller: {(l.seller_id || '').slice(0, 12)}...</Text>
                                    </View>
                                    <View style={{ alignItems: 'flex-end' }}>
                                        <Text style={styles.listingPrice}>{l.price} {l.token_type || 'nexus'}</Text>
                                        <Text style={styles.listingCategory}>{l.category}</Text>
                                        <Text style={[styles.listingStatus, l.status === 'active' && { color: '#166534' }]}>{l.status}</Text>
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </View>
                    )}
                </>
            )}

            {activeTab === 'create' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Create Listing</Text>
                    <TextInput style={styles.input} placeholder="Seller ID" value={sellerId} onChangeText={setSellerId} />
                    <TextInput style={styles.input} placeholder="Title" value={title} onChangeText={setTitle} />
                    <TextInput style={styles.input} placeholder="Description" value={description} onChangeText={setDescription} multiline />
                    <TextInput style={styles.input} placeholder="Price" value={price} onChangeText={setPrice} keyboardType="decimal-pad" />
                    <TextInput style={styles.input} placeholder="Category (general)" value={category} onChangeText={setCategory} />
                    <TouchableOpacity style={styles.button} onPress={handleCreate} disabled={loading}>
                        <Text style={styles.buttonText}>Create Listing</Text>
                    </TouchableOpacity>
                </View>
            )}

            {activeTab === 'order' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Create Order</Text>
                    <TextInput style={styles.input} placeholder="Listing ID" value={listingId} onChangeText={setListingId} />
                    <TextInput style={styles.input} placeholder="Buyer ID" value={buyerId} onChangeText={setBuyerId} />
                    <TouchableOpacity style={[styles.button, { backgroundColor: '#059669' }]} onPress={handleOrder} disabled={loading}>
                        <Text style={styles.buttonText}>Place Order</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.button, { backgroundColor: '#7c3aed', marginTop: 10 }]} onPress={async () => {
                        if (!buyerId) { Alert.alert('Error', 'Enter Buyer ID first'); return; }
                        try {
                            const res = await marketplaceAPI.getOrdersForUser(buyerId, 'buyer');
                            if (!res.error) Alert.alert('My Orders', JSON.stringify(res.orders || res, null, 2).slice(0, 500));
                        } catch (err) { setError(err.message); }
                    }} disabled={loading}>
                        <Text style={styles.buttonText}>My Orders</Text>
                    </TouchableOpacity>
                </View>
            )}

            {stats && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Marketplace Stats</Text>
                    <Text style={styles.detailText}>Total Listings: {stats.total_listings || 0}</Text>
                    <Text style={styles.detailText}>Active Orders: {stats.active_orders || 0}</Text>
                    <Text style={styles.detailText}>Total Volume: {stats.total_volume || 0}</Text>
                    <Text style={styles.detailText}>Avg Rating: {stats.avg_rating || 'N/A'}</Text>
                </View>
            )}

            {loading && <ActivityIndicator size="large" color="#8884d8" style={{ margin: 20 }} />}
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5', padding: 20 },
    title: { fontSize: 28, fontWeight: 'bold', marginBottom: 20, color: '#1a1a2e' },
    errorBanner: { backgroundColor: '#fef2f2', borderColor: '#fecaca', borderWidth: 1, padding: 16, borderRadius: 12, marginBottom: 15 },
    errorText: { fontSize: 14, color: '#991b1b' },
    tabRow: { flexDirection: 'row', marginBottom: 15, gap: 8 },
    tab: { flex: 1, paddingVertical: 10, borderRadius: 8, backgroundColor: '#e5e7eb', alignItems: 'center' },
    activeTab: { backgroundColor: '#8884d8' },
    tabText: { fontSize: 14, fontWeight: '600', color: '#666' },
    activeTabText: { color: '#fff' },
    card: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginBottom: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
    cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 12, color: '#1a1a2e' },
    input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, fontSize: 16, marginBottom: 12, color: '#333' },
    button: { backgroundColor: '#8884d8', paddingVertical: 12, borderRadius: 8, alignItems: 'center', marginBottom: 8 },
    buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
    detailText: { fontSize: 14, color: '#666', marginBottom: 4 },
    listingItem: { flexDirection: 'row', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#eee' },
    listingTitle: { fontSize: 16, fontWeight: '600', color: '#1a1a2e' },
    listingDesc: { fontSize: 13, color: '#666', marginTop: 2 },
    listingSeller: { fontSize: 11, color: '#999', marginTop: 2 },
    listingPrice: { fontSize: 16, fontWeight: 'bold', color: '#166534' },
    listingCategory: { fontSize: 11, color: '#8884d8', marginTop: 2 },
    listingStatus: { fontSize: 12, color: '#ca8a04', marginTop: 2 },
});

export default MarketplaceScreen;
