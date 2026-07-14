/**
 * AsimNexus Mobile — Nepal Screen
 * Digital Nepal integration: ministries, provinces, e-Residency, tax
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
} from 'react-native';
import { apiService } from '../services/api';

interface NepalData {
    status?: string;
    ministries?: number;
    provinces?: number;
    districts?: number;
}

export default function NepalScreen() {
    const [data, setData] = useState<NepalData | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'eresidency' | 'tax'>('overview');

    async function loadData() {
        try {
            const [nepalRes, govRes] = await Promise.all([
                apiService.getNepalStatus().catch(() => ({ data: { data: null } })),
                apiService.getGovernmentStatus().catch(() => ({ data: { data: null } })),
            ]);
            const nepalData = nepalRes?.data?.data || nepalRes?.data;
            setData(nepalData as NepalData);
        } catch (error) {
            console.warn('[Nepal] Load error:', error);
        } finally {
            setLoading(false);
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

    const renderOverview = () => (
        <View>
            <Text style={styles.sectionTitle}>🇳🇵 Digital Nepal</Text>

            {/* Stats Grid */}
            <View style={styles.statsGrid}>
                <View style={styles.statCard}>
                    <Text style={styles.statIcon}>🏛️</Text>
                    <Text style={styles.statValue}>{data?.ministries || '—'}</Text>
                    <Text style={styles.statLabel}>Ministries</Text>
                </View>
                <View style={styles.statCard}>
                    <Text style={styles.statIcon}>🗺️</Text>
                    <Text style={styles.statValue}>{data?.provinces || '—'}</Text>
                    <Text style={styles.statLabel}>Provinces</Text>
                </View>
                <View style={styles.statCard}>
                    <Text style={styles.statIcon}>📍</Text>
                    <Text style={styles.statValue}>{data?.districts || '—'}</Text>
                    <Text style={styles.statLabel}>Districts</Text>
                </View>
                <View style={styles.statCard}>
                    <Text style={styles.statIcon}>✅</Text>
                    <Text style={[styles.statValue, { color: data?.status === 'active' ? '#10b981' : '#f59e0b' }]}>
                        {data?.status || '—'}
                    </Text>
                    <Text style={styles.statLabel}>Status</Text>
                </View>
            </View>

            {/* Connectors */}
            <Text style={styles.sectionTitle}>🔌 Nepal Connectors</Text>
            <View style={styles.connectorGrid}>
                {[
                    { icon: '🏦', label: 'Banks', key: 'banks' },
                    { icon: '📡', label: 'ISPs', key: 'isps' },
                    { icon: '🎓', label: 'Universities', key: 'universities' },
                    { icon: '🏫', label: 'Schools', key: 'schools' },
                    { icon: '🏥', label: 'Hospitals', key: 'hospitals' },
                    { icon: '🏘️', label: 'Palikas', key: 'palikas' },
                    { icon: '🏨', label: 'Hotels', key: 'hotels' },
                ].map(conn => (
                    <View key={conn.key} style={styles.connectorCard}>
                        <Text style={styles.connectorIcon}>{conn.icon}</Text>
                        <Text style={styles.connectorLabel}>{conn.label}</Text>
                    </View>
                ))}
            </View>
        </View>
    );

    const renderEResidency = () => (
        <View>
            <Text style={styles.sectionTitle}>🆔 e-Residency</Text>
            <View style={styles.infoCard}>
                <Text style={styles.infoTitle}>Digital Residency Program</Text>
                <Text style={styles.infoText}>
                    Nepal's e-Residency program allows global citizens to establish digital residency,
                    access government services, and participate in Nepal's digital economy.
                </Text>
            </View>

            <View style={styles.stepCard}>
                <Text style={styles.stepNumber}>1</Text>
                <View style={styles.stepContent}>
                    <Text style={styles.stepTitle}>Select Program</Text>
                    <Text style={styles.stepDesc}>Choose from available e-Residency programs</Text>
                </View>
            </View>
            <View style={styles.stepCard}>
                <Text style={styles.stepNumber}>2</Text>
                <View style={styles.stepContent}>
                    <Text style={styles.stepTitle}>Personal Information</Text>
                    <Text style={styles.stepDesc}>Provide your identity details and documents</Text>
                </View>
            </View>
            <View style={styles.stepCard}>
                <Text style={styles.stepNumber}>3</Text>
                <View style={styles.stepContent}>
                    <Text style={styles.stepTitle}>Verification</Text>
                    <Text style={styles.stepDesc}>Verify your identity through digital channels</Text>
                </View>
            </View>
            <View style={styles.stepCard}>
                <Text style={styles.stepNumber}>4</Text>
                <View style={styles.stepContent}>
                    <Text style={styles.stepTitle}>Approval</Text>
                    <Text style={styles.stepDesc}>Receive your digital residency certificate</Text>
                </View>
            </View>

            <TouchableOpacity style={styles.applyButton}>
                <Text style={styles.applyButtonText}>Apply for e-Residency</Text>
            </TouchableOpacity>
        </View>
    );

    const renderTax = () => (
        <View>
            <Text style={styles.sectionTitle}>💰 Tax Filing</Text>
            <View style={styles.infoCard}>
                <Text style={styles.infoTitle}>Nepal Tax Services</Text>
                <Text style={styles.infoText}>
                    File taxes, calculate liabilities, and manage your tax profile
                    through Nepal's digital tax system.
                </Text>
            </View>

            <View style={styles.actionCard}>
                <TouchableOpacity style={styles.taxAction}>
                    <Text style={styles.taxActionIcon}>🧮</Text>
                    <Text style={styles.taxActionText}>Calculate Tax</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.taxAction}>
                    <Text style={styles.taxActionIcon}>📄</Text>
                    <Text style={styles.taxActionText}>Prepare Return</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.taxAction}>
                    <Text style={styles.taxActionIcon}>📋</Text>
                    <Text style={styles.taxActionText}>View History</Text>
                </TouchableOpacity>
            </View>
        </View>
    );

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#10b981" />
                <Text style={styles.loadingText}>Loading Nepal data...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            <Text style={styles.greeting}>🇳🇵 Digital Nepal</Text>
            <Text style={styles.subtitle}>Government Services & Integration</Text>

            {/* Tab Selector */}
            <View style={styles.tabRow}>
                {(['overview', 'eresidency', 'tax'] as const).map(tab => (
                    <TouchableOpacity
                        key={tab}
                        style={[styles.tab, activeTab === tab && styles.activeTab]}
                        onPress={() => setActiveTab(tab)}
                    >
                        <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
                            {tab === 'overview' ? '🇳🇵 Overview' : tab === 'eresidency' ? '🆔 e-Residency' : '💰 Tax'}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            <View style={styles.content}>
                {activeTab === 'overview' && renderOverview()}
                {activeTab === 'eresidency' && renderEResidency()}
                {activeTab === 'tax' && renderTax()}
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
    statsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
        marginBottom: 24,
    },
    statCard: {
        width: '47%',
        backgroundColor: 'rgba(30,41,59,0.6)',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
    },
    statIcon: {
        fontSize: 24,
        marginBottom: 8,
    },
    statValue: {
        fontSize: 22,
        fontWeight: '800',
        color: '#e2e8f0',
    },
    statLabel: {
        fontSize: 12,
        color: '#64748b',
        marginTop: 4,
    },
    connectorGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
        marginBottom: 24,
    },
    connectorCard: {
        width: '29%',
        backgroundColor: 'rgba(30,41,59,0.4)',
        borderRadius: 10,
        padding: 12,
        alignItems: 'center',
    },
    connectorIcon: {
        fontSize: 22,
        marginBottom: 6,
    },
    connectorLabel: {
        fontSize: 11,
        color: '#94a3b8',
    },
    infoCard: {
        backgroundColor: 'rgba(16,185,129,0.1)',
        borderRadius: 12,
        padding: 16,
        borderWidth: 1,
        borderColor: 'rgba(16,185,129,0.2)',
        marginBottom: 16,
    },
    infoTitle: {
        color: '#6ee7b7',
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 8,
    },
    infoText: {
        color: '#a7f3d0',
        fontSize: 13,
        lineHeight: 20,
    },
    stepCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(30,41,59,0.4)',
        borderRadius: 12,
        padding: 14,
        marginBottom: 10,
    },
    stepNumber: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: 'rgba(16,185,129,0.2)',
        color: '#10b981',
        fontSize: 16,
        fontWeight: '800',
        textAlign: 'center',
        lineHeight: 32,
        marginRight: 14,
    },
    stepContent: {
        flex: 1,
    },
    stepTitle: {
        color: '#e2e8f0',
        fontSize: 15,
        fontWeight: '600',
    },
    stepDesc: {
        color: '#64748b',
        fontSize: 12,
        marginTop: 2,
    },
    applyButton: {
        backgroundColor: '#10b981',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        marginTop: 8,
        marginBottom: 20,
    },
    applyButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '700',
    },
    actionCard: {
        backgroundColor: 'rgba(30,41,59,0.6)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 20,
    },
    taxAction: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255,255,255,0.04)',
        borderRadius: 10,
        padding: 14,
        marginBottom: 8,
    },
    taxActionIcon: {
        fontSize: 20,
        marginRight: 12,
    },
    taxActionText: {
        color: '#e2e8f0',
        fontSize: 15,
        fontWeight: '500',
    },
});