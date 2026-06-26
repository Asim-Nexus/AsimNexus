import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, TextInput, Alert } from 'react-native';
import { escrowAPI } from '../services/economyAPI';

const EscrowScreen = () => {
    const [buyerId, setBuyerId] = useState('');
    const [sellerId, setSellerId] = useState('');
    const [amount, setAmount] = useState('');
    const [escrowId, setEscrowId] = useState('');
    const [escrow, setEscrow] = useState(null);
    const [userEscrows, setUserEscrows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState(null);
    const [activeTab, setActiveTab] = useState('create');

    const handleCreate = async () => {
        if (!buyerId || !sellerId || !amount) {
            Alert.alert('Error', 'Buyer ID, Seller ID, and Amount are required');
            return;
        }
        setLoading(true);
        try {
            const res = await escrowAPI.createEscrow(buyerId, sellerId, parseFloat(amount));
            if (res.error) throw new Error(res.error);
            setEscrowId(res.escrow_id || res.escrow?.escrow_id);
            Alert.alert('Success', `Escrow created: ${res.escrow_id || res.escrow?.escrow_id}`);
            await loadStats();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleAction = async (action) => {
        if (!escrowId) { Alert.alert('Error', 'Escrow ID required'); return; }
        setLoading(true);
        try {
            let res;
            switch (action) {
                case 'fund':
                    res = await escrowAPI.fundEscrow(escrowId, buyerId);
                    break;
                case 'release':
                    res = await escrowAPI.releaseToSeller(escrowId, sellerId);
                    break;
                case 'refund':
                    res = await escrowAPI.refundToBuyer(escrowId, sellerId);
                    break;
                case 'dispute':
                    res = await escrowAPI.raiseDispute(escrowId, buyerId, 'Dispute raised via mobile');
                    break;
            }
            if (res?.error) throw new Error(res.error);
            Alert.alert('Success', `${action} completed`);
            await loadEscrow();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const loadEscrow = async () => {
        if (!escrowId) return;
        setLoading(true);
        try {
            const res = await escrowAPI.getEscrow(escrowId);
            if (res.error) throw new Error(res.error);
            setEscrow(res.escrow || res);
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const loadUserEscrows = async () => {
        const uid = buyerId || sellerId;
        if (!uid) { Alert.alert('Error', 'Enter a Buyer or Seller ID first'); return; }
        setLoading(true);
        try {
            const res = await escrowAPI.getEscrowsForUser(uid);
            if (res.error) throw new Error(res.error);
            setUserEscrows(res.escrows || res || []);
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const loadStats = async () => {
        try {
            const res = await escrowAPI.getEscrowStats();
            if (!res.error) setStats(res);
        } catch (_) { }
    };

    const tabs = ['create', 'manage', 'lookup', 'stats'];
    const tabLabels = { create: 'Create', manage: 'Manage', lookup: 'Lookup', stats: 'Stats' };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>🤝 Escrow</Text>

            {error && (
                <View style={styles.errorBanner}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {/* Tab Bar */}
            <View style={styles.tabRow}>
                {tabs.map((t) => (
                    <TouchableOpacity key={t} style={[styles.tab, activeTab === t && styles.activeTab]} onPress={() => setActiveTab(t)}>
                        <Text style={[styles.tabText, activeTab === t && styles.activeTabText]}>{tabLabels[t]}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            {activeTab === 'create' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Create Escrow</Text>
                    <TextInput style={styles.input} placeholder="Buyer ID" value={buyerId} onChangeText={setBuyerId} />
                    <TextInput style={styles.input} placeholder="Seller ID" value={sellerId} onChangeText={setSellerId} />
                    <TextInput style={styles.input} placeholder="Amount" value={amount} onChangeText={setAmount} keyboardType="decimal-pad" />
                    <TouchableOpacity style={styles.button} onPress={handleCreate} disabled={loading}>
                        <Text style={styles.buttonText}>Create Escrow</Text>
                    </TouchableOpacity>
                </View>
            )}

            {activeTab === 'manage' && (
                <>
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Escrow Actions</Text>
                        <TextInput style={styles.input} placeholder="Escrow ID" value={escrowId} onChangeText={setEscrowId} />
                        <View style={styles.buttonRow}>
                            <TouchableOpacity style={[styles.button, { backgroundColor: '#166534' }]} onPress={() => handleAction('fund')} disabled={loading}>
                                <Text style={styles.buttonText}>Fund</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={[styles.button, { backgroundColor: '#2563eb' }]} onPress={() => handleAction('release')} disabled={loading}>
                                <Text style={styles.buttonText}>Release</Text>
                            </TouchableOpacity>
                        </View>
                        <View style={styles.buttonRow}>
                            <TouchableOpacity style={[styles.button, { backgroundColor: '#ca8a04' }]} onPress={() => handleAction('refund')} disabled={loading}>
                                <Text style={styles.buttonText}>Refund</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={[styles.button, { backgroundColor: '#dc2626' }]} onPress={() => handleAction('dispute')} disabled={loading}>
                                <Text style={styles.buttonText}>Dispute</Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                    {escrow && (
                        <View style={styles.card}>
                            <Text style={styles.cardTitle}>Escrow Details</Text>
                            <Text style={styles.detailText}>ID: {escrow.escrow_id || escrow.id}</Text>
                            <Text style={styles.detailText}>Status: {escrow.status}</Text>
                            <Text style={styles.detailText}>Buyer: {escrow.buyer_id}</Text>
                            <Text style={styles.detailText}>Seller: {escrow.seller_id}</Text>
                            <Text style={styles.balanceText}>Amount: {escrow.amount} {escrow.token_type || 'nexus'}</Text>
                        </View>
                    )}
                </>
            )}

            {activeTab === 'lookup' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Lookup Escrows</Text>
                    <TouchableOpacity style={styles.button} onPress={loadUserEscrows} disabled={loading}>
                        <Text style={styles.buttonText}>Get My Escrows</Text>
                    </TouchableOpacity>
                    {userEscrows.length > 0 && userEscrows.map((e, i) => (
                        <TouchableOpacity key={i} style={styles.escrowItem} onPress={() => { setEscrowId(e.escrow_id || e.id); loadEscrow(); }}>
                            <Text style={styles.escrowId}>ID: {(e.escrow_id || e.id || '').slice(0, 16)}...</Text>
                            <Text style={styles.escrowStatus}>{e.status}</Text>
                            <Text style={styles.escrowAmount}>{e.amount}</Text>
                        </TouchableOpacity>
                    ))}
                    {userEscrows.length === 0 && <Text style={styles.detailText}>No escrows found</Text>}
                </View>
            )}

            {activeTab === 'stats' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Escrow Stats</Text>
                    <TouchableOpacity style={styles.button} onPress={loadStats} disabled={loading}>
                        <Text style={styles.buttonText}>Refresh Stats</Text>
                    </TouchableOpacity>
                    {stats && (
                        <>
                            <Text style={styles.detailText}>Total Escrows: {stats.total_escrows || 0}</Text>
                            <Text style={styles.detailText}>Active: {stats.active_escrows || 0}</Text>
                            <Text style={styles.detailText}>Completed: {stats.completed_escrows || 0}</Text>
                            <Text style={styles.detailText}>Disputed: {stats.disputed_escrows || 0}</Text>
                            <Text style={styles.detailText}>Total Volume: {stats.total_volume || 0}</Text>
                        </>
                    )}
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
    buttonRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 10, marginBottom: 8 },
    detailText: { fontSize: 14, color: '#666', marginBottom: 4 },
    balanceText: { fontSize: 20, fontWeight: 'bold', color: '#166534', marginTop: 8 },
    escrowItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#eee' },
    escrowId: { fontSize: 14, color: '#1a1a2e', flex: 2 },
    escrowStatus: { fontSize: 14, fontWeight: '600', color: '#8884d8', flex: 1, textAlign: 'center' },
    escrowAmount: { fontSize: 14, fontWeight: 'bold', color: '#166534', flex: 1, textAlign: 'right' },
});

export default EscrowScreen;
