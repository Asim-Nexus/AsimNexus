/**
 * AsimNexus Mobile — Agent Mode Screen
 * 5/15/30 day agent contracts, mode toggle, status monitoring
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

interface AgentStatus {
    mode?: string;
    active_contracts?: number;
    status?: string;
}

const CONTRACT_DURATIONS = [
    { days: 5, label: 'Trial', desc: 'Short-term exploration', color: '#8b5cf6' },
    { days: 15, label: 'Standard', desc: 'Medium-term projects', color: '#3b82f6' },
    { days: 30, label: 'Extended', desc: 'Long-term operations', color: '#10b981' },
];

export default function AgentModeScreen() {
    const [status, setStatus] = useState<AgentStatus | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [agentMode, setAgentMode] = useState(false);
    const [selectedDuration, setSelectedDuration] = useState<number | null>(null);

    async function loadStatus() {
        try {
            const res = await apiService.getGovernmentStatus().catch(() => ({ data: { data: null } }));
            const data = res?.data?.data || res?.data;
            setStatus(data as AgentStatus);
            setAgentMode(data?.mode === 'agent' || false);
        } catch (error) {
            console.warn('[AgentMode] Load error:', error);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadStatus();
    }, []);

    async function onRefresh() {
        setRefreshing(true);
        await loadStatus();
        setRefreshing(false);
    }

    async function toggleAgentMode() {
        try {
            if (agentMode) {
                // Deactivate
                setAgentMode(false);
            } else {
                // Activate with selected duration
                setAgentMode(true);
            }
        } catch (error) {
            console.warn('[AgentMode] Toggle error:', error);
        }
    }

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#8b5cf6" />
                <Text style={styles.loadingText}>Loading agent status...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            <Text style={styles.greeting}>🤖 Agent Mode</Text>
            <Text style={styles.subtitle}>5 · 15 · 30 Day Autonomous Contracts</Text>

            {/* Status Card */}
            <View style={styles.statusCard}>
                <View style={styles.statusRow}>
                    <Text style={styles.statusLabel}>Agent Mode</Text>
                    <View style={[styles.statusBadge, agentMode ? styles.activeBadge : styles.inactiveBadge]}>
                        <Text style={[styles.statusBadgeText, agentMode ? styles.activeBadgeText : styles.inactiveBadgeText]}>
                            {agentMode ? 'ACTIVE' : 'INACTIVE'}
                        </Text>
                    </View>
                </View>
                <View style={styles.statusRow}>
                    <Text style={styles.statusLabel}>Active Contracts</Text>
                    <Text style={styles.statusValue}>{status?.active_contracts || 0}</Text>
                </View>
                <View style={styles.statusRow}>
                    <Text style={styles.statusLabel}>System Status</Text>
                    <Text style={styles.statusValue}>{status?.status || 'unknown'}</Text>
                </View>
            </View>

            {/* Duration Selector */}
            <Text style={styles.sectionTitle}>⏱️ Contract Duration</Text>
            <Text style={styles.sectionDesc}>
                Choose how long your agent should operate autonomously.
                Longer durations unlock more capabilities.
            </Text>
            {CONTRACT_DURATIONS.map(d => (
                <TouchableOpacity
                    key={d.days}
                    style={[
                        styles.durationCard,
                        selectedDuration === d.days && { borderColor: d.color, backgroundColor: `${d.color}15` },
                    ]}
                    onPress={() => setSelectedDuration(d.days)}
                >
                    <View style={styles.durationHeader}>
                        <Text style={[styles.durationDays, { color: d.color }]}>{d.days}</Text>
                        <Text style={styles.durationUnit}>days</Text>
                    </View>
                    <View style={styles.durationInfo}>
                        <Text style={styles.durationLabel}>{d.label}</Text>
                        <Text style={styles.durationDesc}>{d.desc}</Text>
                    </View>
                    <View style={[styles.durationRadio, selectedDuration === d.days && { backgroundColor: d.color }]}>
                        {selectedDuration === d.days && <View style={styles.durationRadioInner} />}
                    </View>
                </TouchableOpacity>
            ))}

            {/* Activate Button */}
            <TouchableOpacity
                style={[styles.activateButton, { backgroundColor: agentMode ? '#ef4444' : '#8b5cf6' }]}
                onPress={toggleAgentMode}
            >
                <Text style={styles.activateButtonText}>
                    {agentMode ? '🔴 Deactivate Agent Mode' : '🟢 Activate Agent Mode'}
                </Text>
            </TouchableOpacity>

            {/* Info */}
            <View style={styles.infoCard}>
                <Text style={styles.infoTitle}>ℹ️ About Agent Mode</Text>
                <Text style={styles.infoText}>
                    Agent mode allows AI agents to operate autonomously within defined contracts.
                    The 51% Government layer provides oversight, while the 49% Enterprise layer
                    enables commercial operations. Users maintain 100% sovereignty.
                </Text>
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
    statusCard: {
        backgroundColor: 'rgba(30,41,59,0.6)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 20,
    },
    statusRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    statusLabel: {
        color: '#94a3b8',
        fontSize: 14,
    },
    statusValue: {
        color: '#e2e8f0',
        fontSize: 14,
        fontWeight: '600',
    },
    statusBadge: {
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 12,
    },
    activeBadge: {
        backgroundColor: 'rgba(16,185,129,0.2)',
    },
    inactiveBadge: {
        backgroundColor: 'rgba(100,116,139,0.2)',
    },
    statusBadgeText: {
        fontSize: 12,
        fontWeight: '700',
    },
    activeBadgeText: {
        color: '#10b981',
    },
    inactiveBadgeText: {
        color: '#64748b',
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#e2e8f0',
        marginBottom: 8,
    },
    sectionDesc: {
        fontSize: 13,
        color: '#64748b',
        marginBottom: 16,
        lineHeight: 20,
    },
    durationCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(30,41,59,0.4)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.06)',
    },
    durationHeader: {
        alignItems: 'center',
        marginRight: 16,
        width: 50,
    },
    durationDays: {
        fontSize: 28,
        fontWeight: '800',
    },
    durationUnit: {
        fontSize: 11,
        color: '#64748b',
        marginTop: -2,
    },
    durationInfo: {
        flex: 1,
    },
    durationLabel: {
        color: '#e2e8f0',
        fontSize: 16,
        fontWeight: '600',
    },
    durationDesc: {
        color: '#64748b',
        fontSize: 12,
        marginTop: 2,
    },
    durationRadio: {
        width: 22,
        height: 22,
        borderRadius: 11,
        borderWidth: 2,
        borderColor: '#475569',
        justifyContent: 'center',
        alignItems: 'center',
    },
    durationRadioInner: {
        width: 10,
        height: 10,
        borderRadius: 5,
        backgroundColor: '#fff',
    },
    activateButton: {
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        marginTop: 8,
        marginBottom: 20,
    },
    activateButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '700',
    },
    infoCard: {
        backgroundColor: 'rgba(139,92,246,0.1)',
        borderRadius: 12,
        padding: 16,
        borderWidth: 1,
        borderColor: 'rgba(139,92,246,0.2)',
        marginBottom: 20,
    },
    infoTitle: {
        color: '#c4b5fd',
        fontSize: 14,
        fontWeight: '600',
        marginBottom: 8,
    },
    infoText: {
        color: '#a78bfa',
        fontSize: 13,
        lineHeight: 20,
    },
});
