/**
 * AsimNexus Mobile — Identity Screen
 * Blockchain identity, DID, VC, ZKP, e-Residency
 */
import React, { useEffect, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
    Alert,
} from 'react-native';
import { apiService } from '../services/api';
import { IdentityInfo } from '../types';

interface IdentityState {
    identity: IdentityInfo | null;
    nepalStatus: string;
    governmentStatus: string;
    didAddress: string | null;
}

export default function IdentityScreen() {
    const [state, setState] = useState<IdentityState>({
        identity: null,
        nepalStatus: 'loading',
        governmentStatus: 'loading',
        didAddress: null,
    });
    const [refreshing, setRefreshing] = useState(false);
    const [creatingDID, setCreatingDID] = useState(false);

    async function loadData() {
        try {
            const [identityRes, nepalRes, govRes] = await Promise.all([
                apiService.getIdentityStatus().catch(() => ({ data: null })),
                apiService.getNepalStatus().catch(() => ({ data: { status: 'unavailable' } })),
                apiService.getGovernmentStatus().catch(() => ({ data: { status: 'unavailable' } })),
            ]);

            setState({
                identity: identityRes?.data || null,
                nepalStatus: nepalRes?.data?.status || 'unavailable',
                governmentStatus: govRes?.data?.status || 'unavailable',
                didAddress: identityRes?.data?.did || null,
            });
        } catch (error) {
            console.warn('[Identity] Load error:', error);
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

    async function handleCreateDID() {
        setCreatingDID(true);
        try {
            const res = await apiService.createDID();
            if (res.success) {
                setState((prev) => ({ ...prev, didAddress: res.data?.did || 'created' }));
                Alert.alert('Success', 'Your Decentralized Identity (DID) has been created.');
            } else {
                Alert.alert('Error', res.error || 'Failed to create DID.');
            }
        } catch (error: any) {
            Alert.alert('Error', error?.message || 'Failed to create DID.');
        } finally {
            setCreatingDID(false);
        }
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
            <Text style={styles.title}>Digital Identity</Text>
            <Text style={styles.subtitle}>Self-Sovereign Identity & e-Residency</Text>

            {/* DID Card */}
            <View style={styles.card}>
                <Text style={styles.cardIcon}>🆔</Text>
                <Text style={styles.cardTitle}>Decentralized Identity (DID)</Text>
                {state.didAddress ? (
                    <View style={styles.didInfo}>
                        <Text style={styles.didLabel}>Your DID</Text>
                        <Text style={styles.didValue} numberOfLines={1}>
                            {state.didAddress}
                        </Text>
                        <View style={styles.badge}>
                            <Text style={styles.badgeText}>VERIFIED</Text>
                        </View>
                    </View>
                ) : (
                    <View style={styles.didEmpty}>
                        <Text style={styles.didEmptyText}>
                            No DID created yet. Create your self-sovereign identity.
                        </Text>
                        <TouchableOpacity
                            style={[styles.primaryButton, creatingDID && styles.buttonDisabled]}
                            onPress={handleCreateDID}
                            disabled={creatingDID}
                        >
                            <Text style={styles.primaryButtonText}>
                                {creatingDID ? 'Creating...' : 'Create DID'}
                            </Text>
                        </TouchableOpacity>
                    </View>
                )}
            </View>

            {/* Identity Level */}
            {state.identity && (
                <View style={styles.card}>
                    <Text style={styles.cardIcon}>🔐</Text>
                    <Text style={styles.cardTitle}>Identity Level</Text>
                    <View style={styles.levelContainer}>
                        <Text style={styles.levelNumber}>{state.identity.level || 0}</Text>
                        <Text style={styles.levelLabel}>out of 3</Text>
                    </View>
                    <View style={styles.levelBar}>
                        <View
                            style={[
                                styles.levelBarFill,
                                { width: `${((state.identity.level || 0) / 3) * 100}%` },
                            ]}
                        />
                    </View>
                    <Text style={styles.levelHint}>
                        Level 3 enables full biometric + HSM security
                    </Text>
                </View>
            )}

            {/* Nepal Integration */}
            <View style={[styles.statusCard, { borderLeftColor: statusColor(state.nepalStatus) }]}>
                <Text style={styles.statusIcon}>🇳🇵</Text>
                <View style={styles.statusInfo}>
                    <Text style={styles.statusLabel}>Nepal Integration</Text>
                    <Text style={[styles.statusValue, { color: statusColor(state.nepalStatus) }]}>
                        {state.nepalStatus}
                    </Text>
                </View>
            </View>

            {/* Government Integration */}
            <View style={[styles.statusCard, { borderLeftColor: statusColor(state.governmentStatus) }]}>
                <Text style={styles.statusIcon}>🏛️</Text>
                <View style={styles.statusInfo}>
                    <Text style={styles.statusLabel}>Government Services</Text>
                    <Text style={[styles.statusValue, { color: statusColor(state.governmentStatus) }]}>
                        {state.governmentStatus}
                    </Text>
                </View>
            </View>

            {/* Quick Actions */}
            <Text style={styles.sectionTitle}>Identity Services</Text>
            <View style={styles.actionsGrid}>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>📄</Text>
                    <Text style={styles.actionLabel}>Verifiable Credentials</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>🛂</Text>
                    <Text style={styles.actionLabel}>e-Residency</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>🔑</Text>
                    <Text style={styles.actionLabel}>ZKP Proofs</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionIcon}>📋</Text>
                    <Text style={styles.actionLabel}>Audit Log</Text>
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
        padding: 16,
        marginBottom: 12,
    },
    cardIcon: {
        fontSize: 28,
        marginBottom: 8,
    },
    cardTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#f1f5f9',
        marginBottom: 12,
    },
    didInfo: {
        backgroundColor: '#0f172a',
        borderRadius: 8,
        padding: 12,
    },
    didLabel: {
        fontSize: 12,
        color: '#64748b',
        marginBottom: 4,
    },
    didValue: {
        fontSize: 13,
        color: '#10b981',
        fontFamily: 'monospace',
    },
    badge: {
        backgroundColor: '#10b981',
        borderRadius: 4,
        paddingHorizontal: 8,
        paddingVertical: 2,
        alignSelf: 'flex-start',
        marginTop: 8,
    },
    badgeText: {
        fontSize: 10,
        fontWeight: '700',
        color: '#0f172a',
    },
    didEmpty: {
        alignItems: 'center',
        paddingVertical: 12,
    },
    didEmptyText: {
        fontSize: 14,
        color: '#94a3b8',
        textAlign: 'center',
        marginBottom: 16,
        lineHeight: 20,
    },
    primaryButton: {
        backgroundColor: '#10b981',
        borderRadius: 8,
        paddingHorizontal: 24,
        paddingVertical: 12,
    },
    primaryButtonText: {
        fontSize: 15,
        fontWeight: '600',
        color: '#0f172a',
    },
    buttonDisabled: {
        opacity: 0.5,
    },
    levelContainer: {
        flexDirection: 'row',
        alignItems: 'baseline',
        marginBottom: 8,
    },
    levelNumber: {
        fontSize: 36,
        fontWeight: 'bold',
        color: '#10b981',
    },
    levelLabel: {
        fontSize: 14,
        color: '#64748b',
        marginLeft: 4,
    },
    levelBar: {
        height: 6,
        backgroundColor: '#334155',
        borderRadius: 3,
        marginBottom: 8,
        overflow: 'hidden',
    },
    levelBarFill: {
        height: '100%',
        backgroundColor: '#10b981',
        borderRadius: 3,
    },
    levelHint: {
        fontSize: 12,
        color: '#64748b',
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
        fontSize: 13,
        color: '#f1f5f9',
        fontWeight: '500',
        textAlign: 'center',
    },
});
