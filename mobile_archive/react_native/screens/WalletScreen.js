import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, TextInput, Alert } from 'react-native';
import { walletAPI } from '../services/economyAPI';

const WalletScreen = () => {
    const [wallet, setWallet] = useState(null);
    const [balance, setBalance] = useState(null);
    const [stats, setStats] = useState(null);
    const [ownerId, setOwnerId] = useState('');
    const [walletId, setWalletId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeAction, setActiveAction] = useState(null); // 'create' | 'lookup' | null
    const [amount, setAmount] = useState('');
    const [toWalletId, setToWalletId] = useState('');

    const loadWalletData = useCallback(async (wId) => {
        if (!wId) return;
        setLoading(true);
        setError(null);
        try {
            const w = await walletAPI.getWallet(wId);
            if (w.error) throw new Error(w.error);
            setWallet(w.wallet || w);
            setWalletId(wId);

            const bal = await walletAPI.getBalance(wId);
            if (!bal.error) setBalance(bal);

            const s = await walletAPI.getWalletStats();
            if (!s.error) setStats(s);
        } catch (err) {
            setError(err.message || 'Failed to load wallet');
        }
        setLoading(false);
    }, []);

    const handleCreateWallet = async () => {
        if (!ownerId.trim()) {
            Alert.alert('Error', 'Please enter an Owner ID');
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const res = await walletAPI.createWallet(ownerId.trim());
            if (res.error) throw new Error(res.error);
            setWallet(res.wallet);
            setWalletId(res.wallet_id || res.wallet?.wallet_id);
            Alert.alert('Success', `Wallet created: ${res.wallet_id || res.wallet?.wallet_id}`);
            await loadWalletData(res.wallet_id || res.wallet?.wallet_id);
        } catch (err) {
            setError(err.message || 'Failed to create wallet');
        }
        setLoading(false);
    };

    const handleDeposit = async () => {
        if (!walletId || !amount) return;
        setLoading(true);
        try {
            const res = await walletAPI.deposit(walletId, parseFloat(amount));
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Deposited ${amount}`);
            setAmount('');
            await loadWalletData(walletId);
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    const handleWithdraw = async () => {
        if (!walletId || !amount) return;
        setLoading(true);
        try {
            const res = await walletAPI.withdraw(walletId, parseFloat(amount));
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Withdrew ${amount}`);
            setAmount('');
            await loadWalletData(walletId);
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    const handleTransfer = async () => {
        if (!walletId || !amount || !toWalletId) return;
        setLoading(true);
        try {
            const res = await walletAPI.transfer(walletId, toWalletId, parseFloat(amount));
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Transferred ${amount} to ${toWalletId}`);
            setAmount('');
            setToWalletId('');
            await loadWalletData(walletId);
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>💼 Wallet</Text>

            {error && (
                <View style={styles.errorBanner}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {/* Create Wallet */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Create Wallet</Text>
                <TextInput style={styles.input} placeholder="Owner ID" value={ownerId} onChangeText={setOwnerId} />
                <TouchableOpacity style={styles.button} onPress={handleCreateWallet} disabled={loading}>
                    <Text style={styles.buttonText}>{loading ? 'Creating...' : 'Create Wallet'}</Text>
                </TouchableOpacity>
            </View>

            {/* Lookup Wallet */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Lookup Wallet</Text>
                <TextInput style={styles.input} placeholder="Wallet ID" value={walletId} onChangeText={setWalletId} />
                <TouchableOpacity style={styles.button} onPress={() => loadWalletData(walletId)} disabled={loading}>
                    <Text style={styles.buttonText}>{loading ? 'Loading...' : 'Load Wallet'}</Text>
                </TouchableOpacity>
            </View>

            {/* Wallet Info */}
            {wallet && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Wallet Details</Text>
                    <Text style={styles.detailText}>ID: {wallet.wallet_id || wallet.walletId || 'N/A'}</Text>
                    <Text style={styles.detailText}>Owner: {wallet.owner_id || wallet.ownerId || 'N/A'}</Text>
                    <Text style={styles.detailText}>Status: {wallet.status || 'N/A'}</Text>
                    {balance && (
                        <>
                            <Text style={styles.balanceText}>
                                Balance: {balance.balance?.available ?? balance.available ?? 0} {balance.token_type || 'nexus'}
                            </Text>
                            {balance.locked > 0 && (
                                <Text style={styles.detailText}>Locked: {balance.locked}</Text>
                            )}
                        </>
                    )}
                </View>
            )}

            {/* Transactions */}
            {walletId && (
                <>
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Deposit / Withdraw</Text>
                        <TextInput style={styles.input} placeholder="Amount" value={amount} onChangeText={setAmount} keyboardType="decimal-pad" />
                        <View style={styles.buttonRow}>
                            <TouchableOpacity style={[styles.button, styles.depositBtn]} onPress={handleDeposit} disabled={loading}>
                                <Text style={styles.buttonText}>Deposit</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={[styles.button, styles.withdrawBtn]} onPress={handleWithdraw} disabled={loading}>
                                <Text style={styles.buttonText}>Withdraw</Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Transfer</Text>
                        <TextInput style={styles.input} placeholder="To Wallet ID" value={toWalletId} onChangeText={setToWalletId} />
                        <TextInput style={styles.input} placeholder="Amount" value={amount} onChangeText={setAmount} keyboardType="decimal-pad" />
                        <TouchableOpacity style={[styles.button, styles.transferBtn]} onPress={handleTransfer} disabled={loading}>
                            <Text style={styles.buttonText}>Transfer</Text>
                        </TouchableOpacity>
                    </View>
                </>
            )}

            {/* Stats */}
            {stats && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Wallet System Stats</Text>
                    <Text style={styles.detailText}>Total Wallets: {stats.total_wallets || stats.wallet_count || 0}</Text>
                    <Text style={styles.detailText}>Active: {stats.active_wallets || stats.active || 0}</Text>
                    <Text style={styles.detailText}>Total Supply: {stats.total_supply || 0}</Text>
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
    card: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginBottom: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
    cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 12, color: '#1a1a2e' },
    input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, fontSize: 16, marginBottom: 12, color: '#333' },
    button: { backgroundColor: '#8884d8', paddingVertical: 12, borderRadius: 8, alignItems: 'center', marginBottom: 8 },
    buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
    buttonRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
    depositBtn: { flex: 1, backgroundColor: '#166534' },
    withdrawBtn: { flex: 1, backgroundColor: '#dc2626' },
    transferBtn: { backgroundColor: '#2563eb' },
    detailText: { fontSize: 14, color: '#666', marginBottom: 4 },
    balanceText: { fontSize: 20, fontWeight: 'bold', color: '#166534', marginTop: 8 },
});

export default WalletScreen;
