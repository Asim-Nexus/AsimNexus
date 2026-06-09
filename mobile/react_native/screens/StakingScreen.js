import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, TextInput, Alert } from 'react-native';
import { stakingAPI } from '../services/economyAPI';

const StakingScreen = () => {
    const [validators, setValidators] = useState([]);
    const [stats, setStats] = useState(null);
    const [stakerId, setStakerId] = useState('');
    const [amount, setAmount] = useState('');
    const [validatorId, setValidatorId] = useState('');
    const [stakeId, setStakeId] = useState('');
    const [stakeInfo, setStakeInfo] = useState(null);

    // Register validator form
    const [valName, setValName] = useState('');
    const [valOwner, setValOwner] = useState('');
    const [valDesc, setValDesc] = useState('');
    const [valCommission, setValCommission] = useState('10');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('stake');

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const v = await stakingAPI.listValidators();
            if (!v.error) setValidators(v.validators || v || []);

            const s = await stakingAPI.getStakingStats();
            if (!s.error) setStats(s);

            const ts = await stakingAPI.getTotalStaked();
            if (ts && !ts.error && stats) setStats(prev => ({ ...prev, total_staked: ts.total_staked || ts.amount || 0 }));
        } catch (_) { }
        setLoading(false);
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    const handleStake = async () => {
        if (!stakerId || !amount || !validatorId) {
            Alert.alert('Error', 'Staker ID, Amount, and Validator ID required');
            return;
        }
        setLoading(true);
        try {
            const res = await stakingAPI.stake(stakerId, parseFloat(amount), validatorId);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Staked ${amount}`);
            setAmount('');
            await loadData();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleUnstake = async () => {
        if (!stakeId || !stakerId) {
            Alert.alert('Error', 'Stake ID and Staker ID required');
            return;
        }
        setLoading(true);
        try {
            const res = await stakingAPI.unstake(stakeId, stakerId);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', 'Unstake initiated');
            await loadData();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleClaim = async () => {
        if (!stakeId || !stakerId) {
            Alert.alert('Error', 'Stake ID and Staker ID required');
            return;
        }
        setLoading(true);
        try {
            const res = await stakingAPI.claimUnstaked(stakeId, stakerId);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', 'Rewards claimed');
            await loadData();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleRegisterValidator = async () => {
        if (!valName || !valOwner) {
            Alert.alert('Error', 'Name and Owner ID required');
            return;
        }
        setLoading(true);
        try {
            const commission = parseFloat(valCommission) / 100;
            const res = await stakingAPI.registerValidator(valName, valOwner, valDesc, commission);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Validator registered: ${res.validator_id || res.id}`);
            setValName(''); setValOwner(''); setValDesc(''); setValCommission('10');
            await loadData();
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const handleGetStakeInfo = async () => {
        if (!stakeId) { Alert.alert('Error', 'Stake ID required'); return; }
        setLoading(true);
        try {
            const res = await stakingAPI.getStake(stakeId);
            if (res.error) throw new Error(res.error);
            setStakeInfo(res.stake || res);
        } catch (err) { setError(err.message); }
        setLoading(false);
    };

    const tabs = ['stake', 'validators', 'rewards', 'stats'];
    const tabLabels = { stake: 'Stake', validators: 'Validators', rewards: 'Rewards', stats: 'Stats' };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>🔒 Staking</Text>

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

            {activeTab === 'stake' && (
                <>
                    {/* Stake Form */}
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Stake Tokens</Text>
                        <TextInput style={styles.input} placeholder="Your ID (Staker)" value={stakerId} onChangeText={setStakerId} />
                        <TextInput style={styles.input} placeholder="Validator ID" value={validatorId} onChangeText={setValidatorId} />
                        <TextInput style={styles.input} placeholder="Amount" value={amount} onChangeText={setAmount} keyboardType="decimal-pad" />
                        <TouchableOpacity style={[styles.button, { backgroundColor: '#059669' }]} onPress={handleStake} disabled={loading}>
                            <Text style={styles.buttonText}>Stake</Text>
                        </TouchableOpacity>
                    </View>

                    {/* Unstake Form */}
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Unstake / Claim</Text>
                        <TextInput style={styles.input} placeholder="Stake ID" value={stakeId} onChangeText={setStakeId} />
                        <TextInput style={styles.input} placeholder="Your ID" value={stakerId} onChangeText={setStakerId} />
                        <View style={styles.buttonRow}>
                            <TouchableOpacity style={[styles.button, { flex: 1, backgroundColor: '#ca8a04' }]} onPress={handleUnstake} disabled={loading}>
                                <Text style={styles.buttonText}>Unstake</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={[styles.button, { flex: 1, backgroundColor: '#2563eb' }]} onPress={handleClaim} disabled={loading}>
                                <Text style={styles.buttonText}>Claim</Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                    {/* Stake Info */}
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Stake Info</Text>
                        <TextInput style={styles.input} placeholder="Stake ID" value={stakeId} onChangeText={setStakeId} />
                        <TouchableOpacity style={styles.button} onPress={handleGetStakeInfo} disabled={loading}>
                            <Text style={styles.buttonText}>Get Stake Info</Text>
                        </TouchableOpacity>
                        {stakeInfo && (
                            <>
                                <Text style={styles.detailText}>ID: {stakeInfo.stake_id || stakeInfo.id}</Text>
                                <Text style={styles.detailText}>Staker: {stakeInfo.staker_id}</Text>
                                <Text style={styles.detailText}>Validator: {stakeInfo.validator_id}</Text>
                                <Text style={styles.balanceText}>Amount: {stakeInfo.amount} {stakeInfo.token_type || 'nexus'}</Text>
                                <Text style={styles.detailText}>Status: {stakeInfo.status}</Text>
                                {stakeInfo.pending_rewards > 0 && (
                                    <Text style={[styles.detailText, { color: '#059669', fontWeight: 'bold' }]}>
                                        Pending Rewards: {stakeInfo.pending_rewards}
                                    </Text>
                                )}
                            </>
                        )}
                    </View>
                </>
            )}

            {activeTab === 'validators' && (
                <>
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Register Validator</Text>
                        <TextInput style={styles.input} placeholder="Validator Name" value={valName} onChangeText={setValName} />
                        <TextInput style={styles.input} placeholder="Owner ID" value={valOwner} onChangeText={setValOwner} />
                        <TextInput style={styles.input} placeholder="Description" value={valDesc} onChangeText={setValDesc} />
                        <TextInput style={styles.input} placeholder="Commission % (default 10)" value={valCommission} onChangeText={setValCommission} keyboardType="decimal-pad" />
                        <TouchableOpacity style={[styles.button, { backgroundColor: '#7c3aed' }]} onPress={handleRegisterValidator} disabled={loading}>
                            <Text style={styles.buttonText}>Register</Text>
                        </TouchableOpacity>
                    </View>

                    {validators.length > 0 && (
                        <View style={styles.card}>
                            <Text style={styles.cardTitle}>Validators ({validators.length})</Text>
                            {validators.map((v, i) => (
                                <TouchableOpacity key={i} style={styles.valItem} onPress={() => setValidatorId(v.validator_id || v.id)}>
                                    <View>
                                        <Text style={styles.valName}>{v.name}</Text>
                                        <Text style={styles.valDetail}>Owner: {(v.owner_id || '').slice(0, 12)}...</Text>
                                    </View>
                                    <View style={{ alignItems: 'flex-end' }}>
                                        <Text style={styles.valCommission}>{((v.commission || 0) * 100).toFixed(0)}%</Text>
                                        <Text style={[styles.valStatus, v.status === 'active' && { color: '#166534' }]}>{v.status}</Text>
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </View>
                    )}
                </>
            )}

            {activeTab === 'rewards' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Rewards & Actions</Text>
                    <TouchableOpacity style={styles.button} onPress={async () => {
                        try {
                            const res = await stakingAPI.distributeRewards();
                            if (!res.error) Alert.alert('Success', 'Rewards distributed');
                        } catch (err) { setError(err.message); }
                    }} disabled={loading}>
                        <Text style={styles.buttonText}>Distribute All Rewards</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.button, { backgroundColor: '#ca8a04' }]} onPress={async () => {
                        try {
                            const res = await stakingAPI.unlockMaturedStakes();
                            if (!res.error) Alert.alert('Success', `Unlocked ${res.unlocked || 0} stakes`);
                        } catch (err) { setError(err.message); }
                    }} disabled={loading}>
                        <Text style={styles.buttonText}>Unlock Matured Stakes</Text>
                    </TouchableOpacity>
                    <TextInput style={styles.input} placeholder="Your ID for rewards history" value={stakerId} onChangeText={setStakerId} />
                    <TouchableOpacity style={[styles.button, { backgroundColor: '#2563eb' }]} onPress={async () => {
                        if (!stakerId) { Alert.alert('Error', 'Enter your ID'); return; }
                        try {
                            const res = await stakingAPI.getRewardsHistory(stakerId);
                            if (!res.error) {
                                const rewards = res.rewards || res || [];
                                Alert.alert('Rewards', rewards.length > 0
                                    ? `Last ${rewards.length} rewards\nTotal: ${rewards.reduce((s, r) => s + (r.amount || 0), 0)}`
                                    : 'No rewards found');
                            }
                        } catch (err) { setError(err.message); }
                    }} disabled={loading}>
                        <Text style={styles.buttonText}>My Rewards</Text>
                    </TouchableOpacity>
                </View>
            )}

            {activeTab === 'stats' && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Staking Stats</Text>
                    <TouchableOpacity style={styles.button} onPress={loadData} disabled={loading}>
                        <Text style={styles.buttonText}>Refresh</Text>
                    </TouchableOpacity>
                    {stats && (
                        <>
                            <Text style={styles.detailText}>Total Staked: {stats.total_staked || 0}</Text>
                            <Text style={styles.detailText}>Active Validators: {stats.active_validators || stats.validator_count || 0}</Text>
                            <Text style={styles.detailText}>Total Stakers: {stats.total_stakers || stats.staker_count || 0}</Text>
                            <Text style={styles.detailText}>APR: {stats.apr || stats.avg_apr || 'N/A'}%</Text>
                            <Text style={styles.detailText}>Total Rewards Distributed: {stats.total_rewards_distributed || 0}</Text>
                        </>
                    )}
                    {!stats && <Text style={styles.detailText}>No stats loaded — tap Refresh</Text>}
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
    buttonRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
    detailText: { fontSize: 14, color: '#666', marginBottom: 4 },
    balanceText: { fontSize: 20, fontWeight: 'bold', color: '#166534', marginTop: 8 },
    valItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#eee' },
    valName: { fontSize: 16, fontWeight: '600', color: '#1a1a2e' },
    valDetail: { fontSize: 12, color: '#999', marginTop: 2 },
    valCommission: { fontSize: 16, fontWeight: 'bold', color: '#8884d8' },
    valStatus: { fontSize: 12, color: '#ca8a04', marginTop: 2 },
});

export default StakingScreen;
