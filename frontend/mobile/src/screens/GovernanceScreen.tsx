/**
 * AsimNexus Mobile — Governance Screen
 * 51% Government / 49% Enterprise / 100% User
 * Power balance, policies, veto, stakeholder actions
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
    ActivityIndicator,
} from 'react-native';
import { apiService } from '../services/api';

interface GovernanceData {
    balance?: Record<string, unknown>;
    policies?: unknown[];
    stats?: Record<string, unknown>;
}

export default function GovernanceScreen() {
    const [data, setData] = useState<GovernanceData | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [activeTab, setActiveTab] = useState<'balance' | 'policies' | 'stats'>('balance');
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            const [balanceRes, statsRes] = await Promise.all([
                apiService.getGovernmentStatus().catch(() => ({ data: { data: { error: 'unavailable' } } })),
                apiService.getConsensusStatus().catch(() => ({ data: { data: { error: 'unavailable' } } })),
            ]);
            setData({
                balance: balanceRes?.data?.data || balanceRes?.data,
                stats: statsRes?.data?.data || statsRes?.data,
            });
        } catch (error) {
            console.warn('[Governance] Load error:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    async function onRefresh() {
        setRefreshing(true);
        await loadData();
        setRefreshing(false);
    }

    const renderBalance = () => (
        <View>
            <Text style={styles.sectionTitle}>🏛️ Power Balance (51/49)</Text>
            <View style={styles.balanceBar}>
                <View style={[styles.balanceSegment, { flex: 51, backgroundColor: '#10b981' }]}>
                    <Text style={styles.balanceText}>51% Gov</Text>
                </View>
                <View style={[styles.balanceSegment, { flex: 49, backgroundColor: '#3b82f6' }]}>
                    <Text style={styles.balanceText}>49% Ent</Text>
                </View>
            </View>
            <View style={styles.balanceLegend}>
                <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: '#10b981' }]} />
                    <Text style={styles.legendText}>Government (51% Public Control)</Text>
                </View>
                <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: '#3b82f6' }]} />
                    <Text style={styles.legendText}>Enterprise (49% Private Sector)</Text>
                </View>
                <View style={styles.legendItem}>
                    <View style={[styles.legendDot, { backgroundColor: '#8b5cf6' }]} />
                    <Text style={styles.legendText}>User (100% Sovereignty)</Text>
                </View>
            </View>
            {data?.balance && (
                <View style={styles.dataCard}>
                    <Text style={styles.dataTitle}>Balance Data</Text>
                    <Text style={styles.dataContent}>{JSON.stringify(data.balance, null, 2)}</Text>
                </View>
            )}
        </View>
    );

    const renderPolicies = () => (
        <View>
            <Text style={styles.sectionTitle}>📋 Governance Policies</Text>
            <View style={styles.actionCard}>
                <Text style={styles.actionTitle}>Quick Actions</Text>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionButtonText}>📜 View Pending Policies</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionButtonText}>⚖️ Issue Veto</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionButtonText}>🚨 Declare Emergency</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionButtonText}>🕉️ Dharma Check</Text>
                </TouchableOpacity>
            </View>
            <View style={styles.infoCard}>
                <Text style={styles.infoText}>
                    Full governance controls are available on the web dashboard at /governance.
                    Mobile provides status monitoring and quick actions.
                </Text>
            </View>
        </View>
    );

    const renderStats = () => (
        <View>
            <Text style={styles.sectionTitle}>📊 Governance Stats</Text>
            {data?.stats ? (
                <View style={styles.dataCard}>
                    <Text style={styles.dataContent}>{JSON.stringify(data.stats, null, 2)}</Text>
                </View>
            ) : (
                <View style={styles.infoCard}>
                    <Text style={styles.infoText}>Governance statistics unavailable.</Text>
                </View>
            )}
        </View>
    );

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#10b981" />
                <Text style={styles.loadingText}>Loading governance data...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            <Text style={styles.greeting}>🏛️ Governance</Text>
            <Text style={styles.subtitle}>51% Government · 49% Enterprise · 100% User</Text>

            {/* Tab Selector */}
            <View style={styles.tabRow}>
                {(['balance', 'policies', 'stats'] as const).map(tab => (
                    <TouchableOpacity
                        key={tab}
                        style={[styles.tab, activeTab === tab && styles.activeTab]}
                        onPress={() => setActiveTab(tab)}
                    >
                        <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
                            {tab === 'balance' ? '⚖️ Balance' : tab === 'policies' ? '📋 Policies' : '📊 Stats'}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            <View style={styles.content}>
                {activeTab === 'balance' && renderBalance()}
                {activeTab === 'policies' && renderPolicies()}
                {activeTab === 'stats' && renderStats()}
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
    loadingContainer: {
        flex: 1,
        backgroundColor: '#0f172a',
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        color: '#94a3b8',
        marginTop: 12,
        fontSize: 14,
    },
    greeting: {
        fontSize: 24,
        fontWeight: '700',
        color: '#f1f5f9',
        marginBottom: 4,
    },
    subtitle: {
        fontSize: 13,
        color: '#64748b',
        marginBottom: 20,
    },
    tabRow: {
        flexDirection: 'row',
        backgroundColor: 'rgba(30,41,59,0.6)',
        borderRadius: 12,
        padding: 4,
        marginBottom: 16,
    },
    tab: {
        flex: 1,
        paddingVertical: 10,
        alignItems: 'center',
        borderRadius: 10,
    },
    activeTab: {
        backgroundColor: 'rgba(16,185,129,0.2)',
    },
    tabText: {
        color: '#64748b',
        fontSize: 13,
        fontWeight: '600',
    },
    activeTabText: {
        color: '#10b981',
    },
    content: {
        flex: 1,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#e2e8f0',
        marginBottom: 16,
    },
    balanceBar: {
        flexDirection: 'row',
        height: 40,
        borderRadius: 20,
        overflow: 'hidden',
        marginBottom: 16,
    },
    balanceSegment: {
        justifyContent: 'center',
        alignItems: 'center',
    },
    balanceText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '700',
    },
    balanceLegend: {
        marginBottom: 20,
    },
    legendItem: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    legendDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginRight: 10,
    },
    legendText: {
        color: '#94a3b8',
        fontSize: 13,
    },
    dataCard: {
        backgroundColor: 'rgba(30,41,59,0.6)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
    },
    dataTitle: {
        color: '#e2e8f0',
        fontSize: 14,
        fontWeight: '600',
        marginBottom: 8,
    },
    dataContent: {
        color: '#94a3b8',
        fontSize: 12,
        fontFamily: 'monospace',
    },
    actionCard: {
        backgroundColor: 'rgba(30,41,59,0.6)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
    },
    actionTitle: {
        color: '#e2e8f0',
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 12,
    },
    actionButton: {
        backgroundColor: 'rgba(16,185,129,0.1)',
        borderRadius: 10,
        padding: 14,
        marginBottom: 8,
        borderWidth: 1,
        borderColor: 'rgba(16,185,129,0.2)',
    },
    actionButtonText: {
        color: '#e2e8f0',
        fontSize: 14,
        fontWeight: '500',
    },
    infoCard: {
        backgroundColor: 'rgba(234,179,8,0.1)',
        borderRadius: 12,
        padding: 16,
        borderWidth: 1,
        borderColor: 'rgba(234,179,8,0.2)',
    },
    infoText: {
        color: '#fbbf24',
        fontSize: 13,
        lineHeight: 20,
    },
});
