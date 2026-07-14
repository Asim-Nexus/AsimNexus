/**
 * AsimNexus Mobile — Dashboard Screen
 */
import React, { useEffect, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
} from 'react-native';
import { apiService } from '../services/api';

interface DashboardData {
    health: string;
    finance: string;
    government: string;
    mesh: string;
    consensus: string;
}

export default function DashboardScreen() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    async function loadData() {
        try {
            const [health, finance, gov, mesh, consensus] = await Promise.all([
                apiService.healthCheck(),
                apiService.getFinanceStatus().catch(() => ({ data: { status: 'unavailable' } })),
                apiService.getGovernmentStatus().catch(() => ({ data: { status: 'unavailable' } })),
                apiService.getMeshStatus().catch(() => ({ data: { status: 'unavailable' } })),
                apiService.getConsensusStatus().catch(() => ({ data: { status: 'unavailable' } })),
            ]);

            setData({
                health: health?.data?.status || 'unknown',
                finance: finance?.data?.status || 'unavailable',
                government: gov?.data?.status || 'unavailable',
                mesh: mesh?.data?.status || 'unavailable',
                consensus: consensus?.data?.status || 'unavailable',
            });
        } catch (error) {
            console.warn('[Dashboard] Load error:', error);
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
            <Text style={styles.greeting}>Welcome to AsimNexus</Text>
            <Text style={styles.subtitle}>Universal AI Operating System</Text>

            <View style={styles.grid}>
                <View style={[styles.card, { borderLeftColor: statusColor(data?.health || '') }]}>
                    <Text style={styles.cardIcon}>💚</Text>
                    <Text style={styles.cardLabel}>System</Text>
                    <Text style={[styles.cardValue, { color: statusColor(data?.health || '') }]}>
                        {data?.health || '...'}
                    </Text>
                </View>

                <View style={[styles.card, { borderLeftColor: statusColor(data?.finance || '') }]}>
                    <Text style={styles.cardIcon}>💰</Text>
                    <Text style={styles.cardLabel}>Finance</Text>
                    <Text style={[styles.cardValue, { color: statusColor(data?.finance || '') }]}>
                        {data?.finance || '...'}
                    </Text>
                </View>

                <View style={[styles.card, { borderLeftColor: statusColor(data?.government || '') }]}>
                    <Text style={styles.cardIcon}>🏛️</Text>
                    <Text style={styles.cardLabel}>Government</Text>
                    <Text style={[styles.cardValue, { color: statusColor(data?.government || '') }]}>
                        {data?.government || '...'}
                    </Text>
                </View>

                <View style={[styles.card, { borderLeftColor: statusColor(data?.mesh || '') }]}>
                    <Text style={styles.cardIcon}>🌐</Text>
                    <Text style={styles.cardLabel}>Mesh</Text>
                    <Text style={[styles.cardValue, { color: statusColor(data?.mesh || '') }]}>
                        {data?.mesh || '...'}
                    </Text>
                </View>

                <View style={[styles.card, { borderLeftColor: statusColor(data?.consensus || '') }]}>
                    <Text style={styles.cardIcon}>🗳️</Text>
                    <Text style={styles.cardLabel}>Consensus</Text>
                    <Text style={[styles.cardValue, { color: statusColor(data?.consensus || '') }]}>
                        {data?.consensus || '...'}
                    </Text>
                </View>
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
    greeting: {
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
    grid: {
        gap: 12,
    },
    card: {
        backgroundColor: '#1e293b',
        borderRadius: 12,
        padding: 16,
        borderLeftWidth: 4,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    cardIcon: {
        fontSize: 28,
    },
    cardLabel: {
        fontSize: 14,
        color: '#94a3b8',
        flex: 1,
    },
    cardValue: {
        fontSize: 16,
        fontWeight: '600',
        textTransform: 'capitalize',
    },
});
