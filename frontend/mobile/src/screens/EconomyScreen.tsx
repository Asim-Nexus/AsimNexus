/**
 * AsimNexus Mobile — Economy Screen
 * Digital economy dashboard: wallet, finance, RBE, DePIN
 */
import React, { useEffect, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
    ActivityIndicator,
    Platform,
} from 'react-native';
import { apiService } from '../services/api';
import { WalletInfo } from '../types';

interface EconomyState {
    wallet: WalletInfo | null;
    financeStatus: string;
    rbeStatus: string;
    depinStatus: string;
}

export default function EconomyScreen() {
    const [state, setState] = useState<EconomyState>({
        wallet: null,
        financeStatus: 'loading',
        rbeStatus: 'loading',
        depinStatus: 'loading',
    });
    const [refreshing, setRefreshing] = useState(false);
    const [walletExpanded, setWalletExpanded] = useState(false);

    async function loadData() {
        try {
            const [walletRes, financeRes] = await Promise.all([
                apiService.getWallet('me').catch(() => null),
                apiService.getFinanceStatus().catch(() => ({ data: { status: 'unavailable' } })),
            ]);

            setState({
                wallet: walletRes?.data || null,
                financeStatus: financeRes?.data?.status || 'unavailable',
                rbeStatus: 'checking',
                depinStatus: 'checking',
            });
        } catch (error) {
            console.warn('[Economy] Load error:', error);
        }
    }

    useEffect(() => {
        loadData();
    }, []);

    async function onRefresh() {
        setRefreshing(true);
        await loadData();
        setRefreshing(false);
    }

    const statusColor = (status: string) => {
        switch (status) {
            case 'active': case 'ok': case 'healthy': return '#10b981';
            case 'degraded': case 'warning': return '#f59e0b';
            case 'unavailable': case 'error': return '#ef4444';
            default: return '#64748b';
        }
    };

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            <Text style={styles.title}>Digital Economy</Text>
            <Text style={styles.subtitle}>AsimNexus Economic Engine</Text>

            {/* Wallet Card */}
            <View style={styles.card}>
                <TouchableOpacity
                    style={styles.cardHeader}
                    onPress={() => setWalletExpanded(!walletExpanded)}
                >
                    <Text style={styles.cardIcon}>💳</Text>
                    <View style={styles.cardHeaderText}>
                        <Text style={styles.cardTitle}>Wallet</Text>
                        <Text style={styles.cardSubtitle}>
                            {state.wallet
                                ? `${state.wallet.balance} ${state.wallet.currency}`
                                : 'Connect to view balance'}
                        </Text>
                    </View>
                    <Text style={styles.expandIcon}>{walletExpanded ? '▲' : '▼'}</Text>
                </TouchableOpacity>

                {walletExpanded && state.wallet && (
                    <View style={styles.cardBody}>
                        <View style={styles.row}>
                            <Text style={styles.rowLabel}>Balance</Text>
                            <Text style={styles.rowValue}>
                                {state.wallet.balance} {state.wallet.currency}
                            </Text>
                        </View>
                        {state.wallet.address && (
                            <View style={styles.row}>
                                <Text style={styles.rowLabel}>Address</Text>
                                <Text style={[styles.rowValue, styles.mono]}>
                                    {state.wallet.address.slice(0, 16)}...
                                </Text>
                            </View>
                        )}
                    </View>
                )}
            </View>

            {/* Finance Status */}
            <View style={[styles.statusCard, { borderLeftColor: statusColor(state.financeStatus) }]}>
                <Text style={styles.statusIcon}>💰</Text>
                <View style={styles.statusInfo}>
                    <Text style={styles.statusLabel}>Finance System</Text>
                    <Text style={[styles.statusValue, { color: statusColor(state.financeStatus) }]}>
                        {state.financeStatus}
                    </Text>
                </View>
            </View>

            {/* RBE Status */}
            <View style={[styles.statusCard, { borderLeftColor: statusColor(state.rbeStatus) }]}>
                <Text style={styles.statusIcon}>♻️</Text>
                <View style={styles.statusInfo}>
                    <Text style={styles.statusLabel}>Resource-Based Economy</Text>
                    <Text style={[styles.statusValue, { color: statusColor(state.rbeStatus) }]}>
                        {state.rbeStatus}
                    </Text>
                </View>
            </View>

            {/* DePIN Status */}
            <View style={[styles.statusCard, { borderLeftColor: statusColor(state.depinStatus) }]}>
                <Text style={styles.statusIcon}>📡</Text>
                <View style={styles.statusInfo}>
                    <Text style={styles.statusLabel}>DePIN Network</Text>
                    <Text style={[styles.statusValue, { color: statusColor(state.depinStatus) }]}>
                        {state.depinStatus}
                    </Text>
                </View>
            </View>

            {/* Quick Actions */}
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <View style={styles.actionsGrid}>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>💸</Text>
                    <Text style={styles.actionLabel}>Send</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>📥</Text>
                    <Text style={styles.actionLabel}>Receive</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>📊</Text>
                    <Text style={styles.actionLabel}>History</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>⚙️</Text>
                    <Text style={styles.actionLabel}>Settings</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a',
        padding: 16,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#f1f5f9',
        marginBottom: 4,
    },
    subtitle: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 24,
    },
    card: {
        backgroundColor: '#1e293b',
        borderRadius: 12,
        marginBottom: 12,
        overflow: 'hidden',
    },
    cardHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
    },
    cardHeaderText: {
        flex: 1,
        marginLeft: 12,
    },
    cardTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#f1f5f9',
    },
    cardSubtitle: {
        fontSize: 13,
        color: '#94a3b8',
        marginTop: 2,
    },
    cardIcon: {
        fontSize: 28,
    },
    expandIcon: {
        fontSize: 12,
        color: '#64748b',
    },
    cardBody: {
        borderTopWidth: 1,
        borderTopColor: '#334155',
        padding: 16,
    },
    row: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    rowLabel: {
        fontSize: 14,
        color: '#94a3b8',
    },
    rowValue: {
        fontSize: 14,
        fontWeight: '600',
        color: '#f1f5f9',
    },
    mono: {
        fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
        fontSize: 12,
    },
    statusCard: {
        backgroundColor: '#1e293b',
        borderRadius: 12,
        padding: 16,
        borderLeftWidth: 4,
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
    },
    statusIcon: {
        fontSize: 24,
        marginRight: 12,
    },
    statusInfo: {
        flex: 1,
    },
    statusLabel: {
        fontSize: 14,
        color: '#94a3b8',
    },
    statusValue: {
        fontSize: 16,
        fontWeight: '600',
        textTransform: 'capitalize',
        marginTop: 2,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#f1f5f9',
        marginTop: 12,
        marginBottom: 12,
    },
    actionsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 12,
    },
    actionButton: {
        backgroundColor: '#1e293b',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        width: '47%',
    },
    actionIcon: {
        fontSize: 28,
        marginBottom: 8,
    },
    actionLabel: {
        fontSize: 14,
        color: '#f1f5f9',
        fontWeight: '500',
    },
});
