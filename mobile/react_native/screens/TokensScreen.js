import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, TextInput, Alert } from 'react-native';
import { tokenAPI } from '../services/economyAPI';

const TokensScreen = () => {
    const [tokens, setTokens] = useState([]);
    const [stats, setStats] = useState(null);
    const [tokenId, setTokenId] = useState('');
    const [selectedToken, setSelectedToken] = useState(null);
    const [ownerId, setOwnerId] = useState('');
    const [holdings, setHoldings] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Register form
    const [regName, setRegName] = useState('');
    const [regSymbol, setRegSymbol] = useState('');
    const [regSupply, setRegSupply] = useState('');

    // Mint/Burn form
    const [tokenAction, setTokenAction] = useState(null); // 'mint' | 'burn' | 'lock' | 'unlock'
    const [actionAmount, setActionAmount] = useState('');
    const [actionTarget, setActionTarget] = useState('');

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const t = await tokenAPI.listTokens();
            if (!t.error) setTokens(t.tokens || t || []);

            const s = await tokenAPI.getTokenStats();
            if (!s.error) setStats(s);
        } catch (err) {
            setError('Failed to load token data');
        }
        setLoading(false);
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    const handleRegister = async () => {
        if (!regName || !regSymbol) {
            Alert.alert('Error', 'Name and Symbol are required');
            return;
        }
        setLoading(true);
        try {
            const res = await tokenAPI.registerToken(regName, regSymbol, 'NRC-20', '', parseFloat(regSupply) || 0);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Token registered: ${res.token_id || res.symbol}`);
            setRegName(''); setRegSymbol(''); setRegSupply('');
            await loadData();
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    const handleTokenAction = async () => {
        if (!tokenId || !actionAmount) return;
        setLoading(true);
        try {
            const amount = parseFloat(actionAmount);
            let res;
            switch (tokenAction) {
                case 'mint':
                    res = await tokenAPI.mint(tokenId, actionTarget || ownerId, amount);
                    break;
                case 'burn':
                    res = await tokenAPI.burn(tokenId, actionTarget || ownerId, amount);
                    break;
                case 'lock':
                    res = await tokenAPI.lockTokens(tokenId, actionTarget || ownerId, amount);
                    break;
                case 'unlock':
                    res = await tokenAPI.unlockTokens(tokenId, actionTarget || ownerId, amount);
                    break;
            }
            if (res?.error) throw new Error(res.error);
            Alert.alert('Success', `${tokenAction} completed`);
            setActionAmount('');
            await loadData();
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    const handleLookupHolding = async () => {
        if (!tokenId || !ownerId) return;
        setLoading(true);
        try {
            const res = await tokenAPI.getOwnerBalance(ownerId, tokenId);
            if (!res.error) {
                setHoldings(res);
            } else {
                const h = await tokenAPI.getOwnerHoldings(ownerId);
                setHoldings({ owner_holdings: h.holdings || h });
            }
        } catch (err) {
            setError('Failed to lookup holdings');
        }
        setLoading(false);
    };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>🪙 Tokens</Text>

            {error && (
                <View style={styles.errorBanner}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {/* Stats */}
            {stats && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Token System Stats</Text>
                    <Text style={styles.detailText}>Total Tokens: {stats.total_tokens || stats.token_count || 0}</Text>
                    <Text style={styles.detailText}>Total Supply: {stats.total_supply || 0}</Text>
                    <Text style={styles.detailText}>Active Holders: {stats.active_holders || stats.holder_count || 0}</Text>
                </View>
            )}

            {/* Register Token */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Register Token</Text>
                <TextInput style={styles.input} placeholder="Token Name" value={regName} onChangeText={setRegName} />
                <TextInput style={styles.input} placeholder="Symbol" value={regSymbol} onChangeText={setRegSymbol} />
                <TextInput style={styles.input} placeholder="Total Supply (optional)" value={regSupply} onChangeText={setRegSupply} keyboardType="decimal-pad" />
                <TouchableOpacity style={styles.button} onPress={handleRegister} disabled={loading}>
                    <Text style={styles.buttonText}>Register</Text>
                </TouchableOpacity>
            </View>

            {/* Token Lookup */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Token Actions</Text>
                <TextInput style={styles.input} placeholder="Token ID" value={tokenId} onChangeText={setTokenId} />
                <TextInput style={styles.input} placeholder="Owner ID" value={ownerId} onChangeText={setOwnerId} />

                <View style={styles.buttonRow}>
                    <TouchableOpacity style={[styles.button, styles.actionBtn]} onPress={() => { setTokenAction('mint'); }} disabled={loading}>
                        <Text style={styles.buttonText}>Mint</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.button, styles.actionBtn, { backgroundColor: '#dc2626' }]} onPress={() => { setTokenAction('burn'); }} disabled={loading}>
                        <Text style={styles.buttonText}>Burn</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.button, styles.actionBtn, { backgroundColor: '#ca8a04' }]} onPress={() => { setTokenAction('lock'); }} disabled={loading}>
                        <Text style={styles.buttonText}>Lock</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.button, styles.actionBtn, { backgroundColor: '#2563eb' }]} onPress={() => { setTokenAction('unlock'); }} disabled={loading}>
                        <Text style={styles.buttonText}>Unlock</Text>
                    </TouchableOpacity>
                </View>

                {tokenAction && (
                    <>
                        <Text style={styles.actionLabel}>Action: {tokenAction.toUpperCase()}</Text>
                        <TextInput style={styles.input} placeholder={`Target Owner ID`} value={actionTarget} onChangeText={setActionTarget} />
                        <TextInput style={styles.input} placeholder="Amount" value={actionAmount} onChangeText={setActionAmount} keyboardType="decimal-pad" />
                        <TouchableOpacity style={[styles.button, styles.confirmBtn]} onPress={handleTokenAction} disabled={loading}>
                            <Text style={styles.buttonText}>Confirm {tokenAction}</Text>
                        </TouchableOpacity>
                    </>
                )}
            </View>

            {/* Holdings */}
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Check Holdings</Text>
                <TouchableOpacity style={[styles.button, { backgroundColor: '#7c3aed' }]} onPress={handleLookupHolding} disabled={loading}>
                    <Text style={styles.buttonText}>Lookup Holdings</Text>
                </TouchableOpacity>
                {holdings && (
                    <>
                        <Text style={styles.balanceText}>
                            Balance: {holdings.balance ?? holdings.available ?? 'N/A'}
                        </Text>
                        {holdings.owner_holdings && holdings.owner_holdings.map((h, i) => (
                            <Text key={i} style={styles.detailText}>
                                {h.token_id || h.symbol}: {h.balance || h.amount}
                            </Text>
                        ))}
                    </>
                )}
            </View>

            {/* Token List */}
            {tokens.length > 0 && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>All Tokens ({tokens.length})</Text>
                    {tokens.map((t, i) => (
                        <TouchableOpacity key={i} style={styles.tokenItem} onPress={() => setTokenId(t.token_id || t.symbol)}>
                            <Text style={styles.tokenName}>{t.name || t.symbol}</Text>
                            <Text style={styles.tokenSymbol}>{t.symbol}</Text>
                            <Text style={styles.tokenSupply}>Supply: {t.total_supply || 0}</Text>
                            <Text style={styles.tokenStatus}>{t.standard || 'NRC-20'}</Text>
                        </TouchableOpacity>
                    ))}
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
    buttonRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' },
    actionBtn: { flex: 1, minWidth: 70, paddingVertical: 10 },
    confirmBtn: { backgroundColor: '#059669' },
    actionLabel: { fontSize: 16, fontWeight: '600', color: '#059669', marginBottom: 8, textAlign: 'center' },
    detailText: { fontSize: 14, color: '#666', marginBottom: 4 },
    balanceText: { fontSize: 20, fontWeight: 'bold', color: '#166534', marginTop: 8 },
    tokenItem: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#eee', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    tokenName: { fontSize: 16, fontWeight: '600', color: '#1a1a2e', flex: 2 },
    tokenSymbol: { fontSize: 14, color: '#8884d8', fontWeight: 'bold', flex: 1 },
    tokenSupply: { fontSize: 12, color: '#666', flex: 1, textAlign: 'right' },
    tokenStatus: { fontSize: 12, color: '#888', flex: 0.8, textAlign: 'right' },
});

export default TokensScreen;
