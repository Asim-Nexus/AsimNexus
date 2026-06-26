import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, TextInput, Alert } from 'react-native';
import {
    healthAPI,
    proposalsAPI,
    votingAPI,
    vetoAPI,
    constitutionAPI,
    auditAPI,
    councilAPI,
    bridgeAPI,
    foundersAPI,
    statsAPI,
} from '../services/governanceAPI';

const TABS = [
    'Overview', 'Proposals', 'Voting', 'Veto',
    'Constitution', 'Audit', 'Council', 'Bridge',
];

const GovernanceScreen = () => {
    const [activeTab, setActiveTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Overview
    const [health, setHealth] = useState(null);
    const [govStats, setGovStats] = useState(null);

    // Proposals
    const [proposals, setProposals] = useState([]);
    const [propTitle, setPropTitle] = useState('');
    const [propDesc, setPropDesc] = useState('');
    const [propProposer, setPropProposer] = useState('');
    const [propUrgency, setPropUrgency] = useState('normal');
    const [propSector, setPropSector] = useState('public');

    // Voting
    const [votePropId, setVotePropId] = useState('');
    const [voteVoter, setVoteVoter] = useState('');
    const [voteDecision, setVoteDecision] = useState('for');
    const [voteWeight, setVoteWeight] = useState('1.0');
    const [voteRationale, setVoteRationale] = useState('');
    const [tally, setTally] = useState(null);
    const [tallyPropId, setTallyPropId] = useState('');

    // Veto
    const [vetoBy, setVetoBy] = useState('');
    const [vetoReason, setVetoReason] = useState('');
    const [vetoAction, setVetoAction] = useState('');
    const [vetoPropId, setVetoPropId] = useState('');
    const [vetoStatus, setVetoStatus] = useState(null);

    // Constitution
    const [constHash, setConstHash] = useState('');
    const [constSealer, setConstSealer] = useState('');
    const [constJurisdiction, setConstJurisdiction] = useState('global');
    const [constVerifyHash, setConstVerifyHash] = useState('');
    const [constVerifyResult, setConstVerifyResult] = useState(null);
    const [constLatest, setConstLatest] = useState(null);
    const [constStats, setConstStats] = useState(null);

    // Audit
    const [auditAction, setAuditAction] = useState('');
    const [auditActor, setAuditActor] = useState('');
    const [auditEntries, setAuditEntries] = useState([]);
    const [auditChainResult, setAuditChainResult] = useState(null);
    const [auditStats, setAuditStats] = useState(null);

    // Council
    const [councilStatus, setCouncilStatus] = useState(null);
    const [councilName, setCouncilName] = useState('');
    const [councilType, setCouncilType] = useState('legal_expert');
    const [councilCountry, setCouncilCountry] = useState('global');
    const [councilExpertise, setCouncilExpertise] = useState('');

    // Bridge
    const [bridgeTitle, setBridgeTitle] = useState('');
    const [bridgeDesc, setBridgeDesc] = useState('');
    const [bridgeSector, setBridgeSector] = useState('public');
    const [bridgeUrgency, setBridgeUrgency] = useState('normal');
    const [bridgeResult, setBridgeResult] = useState(null);
    const [bridgeHistory, setBridgeHistory] = useState([]);

    const showError = (msg) => {
        setError(msg);
        setTimeout(() => setError(null), 5000);
    };

    // ─── Overview ────────────────────────────────────────────────────────

    const loadOverview = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [h, s] = await Promise.all([
                healthAPI.health(),
                statsAPI.get(),
            ]);
            if (h.error) throw new Error(h.error);
            setHealth(h);
            setGovStats(s);
        } catch (err) {
            showError(err.message || 'Failed to load overview');
        }
        setLoading(false);
    }, []);

    // ─── Proposals ───────────────────────────────────────────────────────

    const handleCreateProposal = async () => {
        if (!propTitle.trim() || !propDesc.trim() || !propProposer.trim()) {
            Alert.alert('Error', 'Title, description, and proposer are required');
            return;
        }
        setLoading(true);
        try {
            const res = await proposalsAPI.create(propTitle.trim(), propDesc.trim(), propProposer.trim(), null, propUrgency, propSector);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Proposal created: ${res.proposal_id}`);
            setPropTitle('');
            setPropDesc('');
            await handleListProposals();
        } catch (err) {
            showError(err.message || 'Failed to create proposal');
        }
        setLoading(false);
    };

    const handleListProposals = async () => {
        setLoading(true);
        try {
            const res = await proposalsAPI.list();
            if (res.error) throw new Error(res.error);
            setProposals(res.proposals || []);
        } catch (err) {
            showError(err.message || 'Failed to list proposals');
        }
        setLoading(false);
    };

    // ─── Voting ──────────────────────────────────────────────────────────

    const handleCastVote = async () => {
        if (!votePropId.trim() || !voteVoter.trim()) {
            Alert.alert('Error', 'Proposal ID and voter address are required');
            return;
        }
        setLoading(true);
        try {
            const res = await votingAPI.castVote(votePropId.trim(), voteVoter.trim(), voteDecision, parseFloat(voteWeight) || 1.0, voteRationale);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Vote cast: ${res.decision}`);
        } catch (err) {
            showError(err.message || 'Failed to cast vote');
        }
        setLoading(false);
    };

    const handleGetTally = async () => {
        if (!tallyPropId.trim()) return;
        setLoading(true);
        try {
            const res = await votingAPI.getTally(tallyPropId.trim());
            if (res.error) throw new Error(res.error);
            setTally(res);
        } catch (err) {
            showError(err.message || 'Failed to get tally');
        }
        setLoading(false);
    };

    // ─── Veto ────────────────────────────────────────────────────────────

    const handleExerciseVeto = async () => {
        if (!vetoBy.trim() || !vetoReason.trim() || !vetoAction.trim()) {
            Alert.alert('Error', 'Exercised by, reason, and action are required');
            return;
        }
        setLoading(true);
        try {
            const res = await vetoAPI.exercise(vetoBy.trim(), vetoReason.trim(), vetoAction.trim(), vetoPropId.trim());
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', 'Veto recorded');
            await handleRefreshVetoStatus();
        } catch (err) {
            showError(err.message || 'Failed to exercise veto');
        }
        setLoading(false);
    };

    const handleRefreshVetoStatus = async () => {
        setLoading(true);
        try {
            const res = await vetoAPI.status();
            if (res.error) throw new Error(res.error);
            setVetoStatus(res);
        } catch (err) {
            showError(err.message || 'Failed to get veto status');
        }
        setLoading(false);
    };

    // ─── Constitution ────────────────────────────────────────────────────

    const handleSealConstitution = async () => {
        if (!constHash.trim()) {
            Alert.alert('Error', 'Constitution hash is required');
            return;
        }
        setLoading(true);
        try {
            const res = await constitutionAPI.seal(constHash.trim(), constSealer.trim() || 'system', constJurisdiction);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', 'Constitution sealed');
            setConstHash('');
        } catch (err) {
            showError(err.message || 'Failed to seal constitution');
        }
        setLoading(false);
    };

    const handleVerifyConstitution = async () => {
        if (!constVerifyHash.trim()) return;
        setLoading(true);
        try {
            const res = await constitutionAPI.verify(constVerifyHash.trim());
            if (res.error) throw new Error(res.error);
            setConstVerifyResult(res);
        } catch (err) {
            showError(err.message || 'Failed to verify constitution');
        }
        setLoading(false);
    };

    const handleLatestConstitution = async () => {
        setLoading(true);
        try {
            const res = await constitutionAPI.latest();
            if (res.error) throw new Error(res.error);
            setConstLatest(res);
            const s = await constitutionAPI.stats();
            if (!s.error) setConstStats(s);
        } catch (err) {
            showError(err.message || 'Failed to get latest constitution');
        }
        setLoading(false);
    };

    // ─── Audit ───────────────────────────────────────────────────────────

    const handleAuditQuery = async () => {
        setLoading(true);
        try {
            const filters = {};
            if (auditAction.trim()) filters.action = auditAction.trim();
            if (auditActor.trim()) filters.actor = auditActor.trim();
            const res = await auditAPI.query(filters);
            if (res.error) throw new Error(res.error);
            setAuditEntries(res.entries || []);
        } catch (err) {
            showError(err.message || 'Failed to query audit');
        }
        setLoading(false);
    };

    const handleVerifyAuditChain = async () => {
        setLoading(true);
        try {
            const res = await auditAPI.verifyChain();
            if (res.error) throw new Error(res.error);
            setAuditChainResult(res);
        } catch (err) {
            showError(err.message || 'Failed to verify audit chain');
        }
        setLoading(false);
    };

    const handleAuditStats = async () => {
        setLoading(true);
        try {
            const res = await auditAPI.stats();
            if (res.error) throw new Error(res.error);
            setAuditStats(res);
        } catch (err) {
            showError(err.message || 'Failed to get audit stats');
        }
        setLoading(false);
    };

    // ─── Council ─────────────────────────────────────────────────────────

    const handleCouncilStatus = async () => {
        setLoading(true);
        try {
            const res = await councilAPI.status();
            if (res.error) throw new Error(res.error);
            setCouncilStatus(res);
        } catch (err) {
            showError(err.message || 'Failed to get council status');
        }
        setLoading(false);
    };

    const handleAddCouncilMember = async () => {
        if (!councilName.trim()) {
            Alert.alert('Error', 'Name is required');
            return;
        }
        setLoading(true);
        try {
            const expertise = councilExpertise.trim() ? councilExpertise.trim().split(',').map(s => s.trim()) : [];
            const res = await councilAPI.addMember(councilName.trim(), councilType, councilCountry.trim() || 'global', expertise);
            if (res.error) throw new Error(res.error);
            Alert.alert('Success', `Member added: ${res.member_id}`);
            setCouncilName('');
            await handleCouncilStatus();
        } catch (err) {
            showError(err.message || 'Failed to add council member');
        }
        setLoading(false);
    };

    // ─── Bridge ──────────────────────────────────────────────────────────

    const handleBridgeDecide = async () => {
        if (!bridgeTitle.trim() || !bridgeDesc.trim()) {
            Alert.alert('Error', 'Title and description are required');
            return;
        }
        setLoading(true);
        try {
            const res = await bridgeAPI.decide(bridgeTitle.trim(), bridgeDesc.trim(), bridgeSector, bridgeUrgency);
            if (res.error) throw new Error(res.error);
            setBridgeResult(res);
            Alert.alert('Success', 'Decision submitted to bridge');
            setBridgeTitle('');
            setBridgeDesc('');
            await handleBridgeHistory();
        } catch (err) {
            showError(err.message || 'Failed to submit bridge decision');
        }
        setLoading(false);
    };

    const handleBridgeHistory = async () => {
        setLoading(true);
        try {
            const res = await bridgeAPI.history(10);
            if (res.error) throw new Error(res.error);
            setBridgeHistory(res.history || []);
        } catch (err) {
            showError(err.message || 'Failed to get bridge history');
        }
        setLoading(false);
    };

    // ─── Tab Change ──────────────────────────────────────────────────────

    useEffect(() => {
        setError(null);
        if (activeTab === 0) loadOverview();
        else if (activeTab === 1) handleListProposals();
        else if (activeTab === 3) handleRefreshVetoStatus();
        else if (activeTab === 5) { handleAuditStats(); handleVerifyAuditChain(); }
        else if (activeTab === 6) handleCouncilStatus();
        else if (activeTab === 7) handleBridgeHistory();
    }, [activeTab]);

    // ─── Render: Tab Navigation ─────────────────────────────────────────

    const renderTabNav = () => (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabBar}>
            {TABS.map((tab, i) => (
                <TouchableOpacity
                    key={tab}
                    style={[styles.tabItem, activeTab === i && styles.tabItemActive]}
                    onPress={() => setActiveTab(i)}
                >
                    <Text style={[styles.tabText, activeTab === i && styles.tabTextActive]}>{tab}</Text>
                </TouchableOpacity>
            ))}
        </ScrollView>
    );

    // ─── Render: Overview ───────────────────────────────────────────────

    const renderOverview = () => {
        if (loading && !health) {
            return <ActivityIndicator size="large" color="#8884d8" style={{ marginTop: 40 }} />;
        }
        return (
            <View>
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Health Status</Text>
                    <Text style={styles.value}>
                        Status: <Text style={{ color: health?.status === 'healthy' ? '#166534' : '#dc2626', fontWeight: 'bold' }}>
                            {health?.status || 'Unknown'}
                        </Text>
                    </Text>
                    <Text style={styles.value}>Modules: {(health?.modules || []).join(', ') || 'None'}</Text>
                    {health?.issues && health.issues.length > 0 && (
                        <Text style={{ color: '#dc2626', marginTop: 8 }}>
                            Issues: {health.issues.join(', ')}
                        </Text>
                    )}
                </View>

                {govStats && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Governance Stats</Text>
                        <View style={styles.statsRow}>
                            <View style={styles.statBox}>
                                <Text style={styles.statNumber}>{govStats.proposals?.total || 0}</Text>
                                <Text style={styles.statLabel}>Proposals</Text>
                            </View>
                            <View style={styles.statBox}>
                                <Text style={styles.statNumber}>{govStats.council?.total_members || 0}</Text>
                                <Text style={styles.statLabel}>Council</Text>
                            </View>
                            <View style={styles.statBox}>
                                <Text style={styles.statNumber}>{govStats.audit?.total_entries || 0}</Text>
                                <Text style={styles.statLabel}>Audit</Text>
                            </View>
                        </View>
                        <View style={styles.statsRow}>
                            <View style={styles.statBox}>
                                <Text style={styles.statNumber}>{govStats.constitution?.anchors_count || 0}</Text>
                                <Text style={styles.statLabel}>Anchors</Text>
                            </View>
                            <View style={styles.statBox}>
                                <Text style={styles.statNumber}>{govStats.bridge?.total_decisions || 0}</Text>
                                <Text style={styles.statLabel}>Bridge</Text>
                            </View>
                            <View style={styles.statBox}>
                                <Text style={styles.statNumber}>{govStats.veto?.total || 0}</Text>
                                <Text style={styles.statLabel}>Vetoes</Text>
                            </View>
                        </View>
                    </View>
                )}
                <TouchableOpacity style={styles.refreshBtn} onPress={loadOverview}>
                    <Text style={styles.refreshBtnText}>Refresh</Text>
                </TouchableOpacity>
            </View>
        );
    };

    // ─── Render: Proposals ──────────────────────────────────────────────

    const renderProposals = () => (
        <View>
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Create Proposal</Text>
                <TextInput style={styles.input} placeholder="Title" placeholderTextColor="#999" value={propTitle} onChangeText={setPropTitle} />
                <TextInput style={[styles.input, styles.textArea]} placeholder="Description" placeholderTextColor="#999" value={propDesc} onChangeText={setPropDesc} multiline numberOfLines={3} />
                <TextInput style={styles.input} placeholder="Proposer ID" placeholderTextColor="#999" value={propProposer} onChangeText={setPropProposer} />
                <View style={styles.pickerRow}>
                    <TouchableOpacity style={[styles.pickerBtn, propUrgency === 'normal' && styles.pickerBtnActive]} onPress={() => setPropUrgency('normal')}>
                        <Text style={[styles.pickerText, propUrgency === 'normal' && styles.pickerTextActive]}>Normal</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.pickerBtn, propUrgency === 'high' && styles.pickerBtnActive]} onPress={() => setPropUrgency('high')}>
                        <Text style={[styles.pickerText, propUrgency === 'high' && styles.pickerTextActive]}>High</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.pickerBtn, propUrgency === 'critical' && styles.pickerBtnActive]} onPress={() => setPropUrgency('critical')}>
                        <Text style={[styles.pickerText, propUrgency === 'critical' && styles.pickerTextActive]}>Critical</Text>
                    </TouchableOpacity>
                </View>
                <TextInput style={styles.input} placeholder="Sector (public, technology, healthcare...)" placeholderTextColor="#999" value={propSector} onChangeText={setPropSector} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleCreateProposal} disabled={loading}>
                    <Text style={styles.actionBtnText}>Create Proposal</Text>
                </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.refreshBtn} onPress={handleListProposals}>
                <Text style={styles.refreshBtnText}>Refresh Proposals</Text>
            </TouchableOpacity>

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Proposals ({proposals.length})</Text>
                {proposals.length === 0 ? (
                    <Text style={styles.emptyText}>No proposals yet</Text>
                ) : (
                    proposals.map((p, i) => (
                        <View key={p.proposal_id || i} style={styles.listItem}>
                            <Text style={styles.itemTitle}>{p.title || 'Untitled'}</Text>
                            <Text style={styles.itemSub}>ID: {p.proposal_id} | State: {p.state}</Text>
                            <Text style={styles.itemSub}>Proposer: {p.proposer} | Votes: {p.vote_count || 0}</Text>
                        </View>
                    ))
                )}
            </View>
        </View>
    );

    // ─── Render: Voting ─────────────────────────────────────────────────

    const renderVoting = () => (
        <View>
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Cast Vote</Text>
                <TextInput style={styles.input} placeholder="Proposal ID" placeholderTextColor="#999" value={votePropId} onChangeText={setVotePropId} />
                <TextInput style={styles.input} placeholder="Voter Address" placeholderTextColor="#999" value={voteVoter} onChangeText={setVoteVoter} />
                <View style={styles.pickerRow}>
                    {['for', 'against', 'abstain'].map(d => (
                        <TouchableOpacity key={d} style={[styles.pickerBtn, voteDecision === d && styles.pickerBtnActive]} onPress={() => setVoteDecision(d)}>
                            <Text style={[styles.pickerText, voteDecision === d && styles.pickerTextActive]}>{d.charAt(0).toUpperCase() + d.slice(1)}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
                <TextInput style={styles.input} placeholder="Weight (default: 1.0)" placeholderTextColor="#999" value={voteWeight} onChangeText={setVoteWeight} keyboardType="decimal-pad" />
                <TextInput style={[styles.input, styles.textArea]} placeholder="Rationale (optional)" placeholderTextColor="#999" value={voteRationale} onChangeText={setVoteRationale} multiline numberOfLines={2} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleCastVote} disabled={loading}>
                    <Text style={styles.actionBtnText}>Cast Vote</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Vote Tally</Text>
                <TextInput style={styles.input} placeholder="Proposal ID" placeholderTextColor="#999" value={tallyPropId} onChangeText={setTallyPropId} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleGetTally} disabled={loading}>
                    <Text style={styles.actionBtnText}>Get Tally</Text>
                </TouchableOpacity>
                {tally && (
                    <View style={{ marginTop: 12 }}>
                        <Text style={styles.value}>For: {tally.for ?? tally.votes_for ?? 0}</Text>
                        <Text style={styles.value}>Against: {tally.against ?? tally.votes_against ?? 0}</Text>
                        <Text style={styles.value}>Abstain: {tally.abstain ?? 0}</Text>
                        <Text style={styles.value}>Approval: {tally.approval_pct ?? 0}%</Text>
                    </View>
                )}
            </View>
        </View>
    );

    // ─── Render: Veto ───────────────────────────────────────────────────

    const renderVeto = () => (
        <View>
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Exercise Veto</Text>
                <TextInput style={styles.input} placeholder="Exercised By" placeholderTextColor="#999" value={vetoBy} onChangeText={setVetoBy} />
                <TextInput style={styles.input} placeholder="Reason" placeholderTextColor="#999" value={vetoReason} onChangeText={setVetoReason} />
                <TextInput style={styles.input} placeholder="Action Vetoed" placeholderTextColor="#999" value={vetoAction} onChangeText={setVetoAction} />
                <TextInput style={styles.input} placeholder="Proposal ID (optional)" placeholderTextColor="#999" value={vetoPropId} onChangeText={setVetoPropId} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleExerciseVeto} disabled={loading}>
                    <Text style={styles.actionBtnText}>Exercise Veto</Text>
                </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.refreshBtn} onPress={handleRefreshVetoStatus}>
                <Text style={styles.refreshBtnText}>Refresh Veto Status</Text>
            </TouchableOpacity>

            {vetoStatus && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Veto Status</Text>
                    <Text style={styles.value}>Active: {vetoStatus.veto_power_active ? '✅ Yes' : '❌ No'}</Text>
                    <Text style={styles.value}>Recent Vetoes: {vetoStatus.recent_vetoes || 0}</Text>
                    {(vetoStatus.veto_records || []).map((v, i) => (
                        <View key={v.veto_id || i} style={styles.listItem}>
                            <Text style={styles.itemTitle}>By: {v.exercised_by}</Text>
                            <Text style={styles.itemSub}>Action: {v.action_vetoed}</Text>
                            <Text style={styles.itemSub}>Reason: {v.reason}</Text>
                            {v.abuse_detected && <Text style={{ color: '#dc2626', fontWeight: 'bold' }}>⚠ Abuse Detected</Text>}
                        </View>
                    ))}
                </View>
            )}
        </View>
    );

    // ─── Render: Constitution ───────────────────────────────────────────

    const renderConstitution = () => (
        <View>
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Seal Constitution</Text>
                <TextInput style={styles.input} placeholder="Constitution Hash" placeholderTextColor="#999" value={constHash} onChangeText={setConstHash} />
                <TextInput style={styles.input} placeholder="Sealed By (optional)" placeholderTextColor="#999" value={constSealer} onChangeText={setConstSealer} />
                <TextInput style={styles.input} placeholder="Jurisdiction (default: global)" placeholderTextColor="#999" value={constJurisdiction} onChangeText={setConstJurisdiction} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleSealConstitution} disabled={loading}>
                    <Text style={styles.actionBtnText}>Seal</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Verify Constitution</Text>
                <TextInput style={styles.input} placeholder="Hash to Verify" placeholderTextColor="#999" value={constVerifyHash} onChangeText={setConstVerifyHash} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleVerifyConstitution} disabled={loading}>
                    <Text style={styles.actionBtnText}>Verify</Text>
                </TouchableOpacity>
                {constVerifyResult && (
                    <View style={{ marginTop: 12 }}>
                        <Text style={styles.value}>Verified: {constVerifyResult.verified ? '✅ Yes' : '❌ No'}</Text>
                    </View>
                )}
            </View>

            <TouchableOpacity style={styles.refreshBtn} onPress={handleLatestConstitution}>
                <Text style={styles.refreshBtnText}>Latest Anchor & Stats</Text>
            </TouchableOpacity>

            {constLatest && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Latest Anchor</Text>
                    <Text style={styles.value}>{JSON.stringify(constLatest.latest_anchor || constLatest)}</Text>
                </View>
            )}
            {constStats && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Constitution Stats</Text>
                    <Text style={styles.value}>Anchors: {constStats.anchors_count || 0}</Text>
                    <Text style={styles.value}>Chain Integrity: {constStats.chain_integrity || 'unknown'}</Text>
                </View>
            )}
        </View>
    );

    // ─── Render: Audit ──────────────────────────────────────────────────

    const renderAudit = () => (
        <View>
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Query Audit Trail</Text>
                <TextInput style={styles.input} placeholder="Filter by Action (optional)" placeholderTextColor="#999" value={auditAction} onChangeText={setAuditAction} />
                <TextInput style={styles.input} placeholder="Filter by Actor (optional)" placeholderTextColor="#999" value={auditActor} onChangeText={setAuditActor} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleAuditQuery} disabled={loading}>
                    <Text style={styles.actionBtnText}>Query</Text>
                </TouchableOpacity>
                {auditEntries.length > 0 && (
                    <View style={{ marginTop: 12 }}>
                        <Text style={styles.cardTitle}>Entries ({auditEntries.length})</Text>
                        {auditEntries.slice(0, 10).map((e, i) => (
                            <View key={e.entry_id || i} style={styles.listItem}>
                                <Text style={styles.itemTitle}>{e.action || 'Unknown'}</Text>
                                <Text style={styles.itemSub}>Actor: {e.actor || e.auditor || 'N/A'}</Text>
                                <Text style={styles.itemSub}>Resource: {e.resource || 'N/A'}</Text>
                            </View>
                        ))}
                    </View>
                )}
            </View>

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Chain Integrity</Text>
                <TouchableOpacity style={styles.actionBtn} onPress={handleVerifyAuditChain} disabled={loading}>
                    <Text style={styles.actionBtnText}>Verify Chain</Text>
                </TouchableOpacity>
                {auditChainResult && (
                    <View style={{ marginTop: 8 }}>
                        <Text style={styles.value}>Status: {auditChainResult.status || 'Checked'}</Text>
                        <Text style={styles.value}>Total: {auditChainResult.total_entries || 0}</Text>
                    </View>
                )}
            </View>

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Audit Stats</Text>
                <TouchableOpacity style={styles.actionBtn} onPress={handleAuditStats} disabled={loading}>
                    <Text style={styles.actionBtnText}>Get Stats</Text>
                </TouchableOpacity>
                {auditStats && (
                    <View style={{ marginTop: 8 }}>
                        {Object.entries(auditStats).map(([k, v]) => (
                            <Text key={k} style={styles.value}>{k}: {JSON.stringify(v)}</Text>
                        ))}
                    </View>
                )}
            </View>
        </View>
    );

    // ─── Render: Council ────────────────────────────────────────────────

    const renderCouncil = () => (
        <View>
            <TouchableOpacity style={styles.refreshBtn} onPress={handleCouncilStatus}>
                <Text style={styles.refreshBtnText}>Refresh Council Status</Text>
            </TouchableOpacity>

            {councilStatus && (
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Council Status</Text>
                    <Text style={styles.value}>Total Members: {councilStatus.total_members || councilStatus.council_members?.length || 0}</Text>
                    <Text style={styles.value}>Active Members: {councilStatus.active_members || 0}</Text>
                    {(councilStatus.council_members || []).map((m, i) => (
                        <View key={m.member_id || i} style={styles.listItem}>
                            <Text style={styles.itemTitle}>{m.name || 'Unknown'}</Text>
                            <Text style={styles.itemSub}>Type: {m.member_type || 'N/A'}</Text>
                            <Text style={styles.itemSub}>Country: {m.country || 'global'}</Text>
                            <Text style={styles.itemSub}>Active: {m.active ? '✅' : '❌'}</Text>
                        </View>
                    ))}
                </View>
            )}

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Add Council Member</Text>
                <TextInput style={styles.input} placeholder="Name" placeholderTextColor="#999" value={councilName} onChangeText={setCouncilName} />
                <View style={styles.pickerRow}>
                    {['legal_expert', 'constitutional_expert', 'technical_expert', 'ethics_expert', 'government_representative'].map(t => (
                        <TouchableOpacity key={t} style={[styles.pickerBtn, councilType === t && styles.pickerBtnActive]} onPress={() => setCouncilType(t)}>
                            <Text style={[styles.pickerText, councilType === t && styles.pickerTextActive]} numberOfLines={1}>{t.replace(/_/g, ' ')}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
                <TextInput style={styles.input} placeholder="Country (default: global)" placeholderTextColor="#999" value={councilCountry} onChangeText={setCouncilCountry} />
                <TextInput style={styles.input} placeholder="Expertise (comma-separated)" placeholderTextColor="#999" value={councilExpertise} onChangeText={setCouncilExpertise} />
                <TouchableOpacity style={styles.actionBtn} onPress={handleAddCouncilMember} disabled={loading}>
                    <Text style={styles.actionBtnText}>Add Member</Text>
                </TouchableOpacity>
            </View>
        </View>
    );

    // ─── Render: Bridge ─────────────────────────────────────────────────

    const renderBridge = () => (
        <View>
            <View style={styles.card}>
                <Text style={styles.cardTitle}>Submit Governance Decision</Text>
                <TextInput style={styles.input} placeholder="Title" placeholderTextColor="#999" value={bridgeTitle} onChangeText={setBridgeTitle} />
                <TextInput style={[styles.input, styles.textArea]} placeholder="Description" placeholderTextColor="#999" value={bridgeDesc} onChangeText={setBridgeDesc} multiline numberOfLines={3} />
                <TextInput style={styles.input} placeholder="Sector (public, technology...)" placeholderTextColor="#999" value={bridgeSector} onChangeText={setBridgeSector} />
                <View style={styles.pickerRow}>
                    {['normal', 'high', 'critical'].map(u => (
                        <TouchableOpacity key={u} style={[styles.pickerBtn, bridgeUrgency === u && styles.pickerBtnActive]} onPress={() => setBridgeUrgency(u)}>
                            <Text style={[styles.pickerText, bridgeUrgency === u && styles.pickerTextActive]}>{u.charAt(0).toUpperCase() + u.slice(1)}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
                <TouchableOpacity style={styles.actionBtn} onPress={handleBridgeDecide} disabled={loading}>
                    <Text style={styles.actionBtnText}>Submit Decision</Text>
                </TouchableOpacity>
                {bridgeResult && (
                    <View style={{ marginTop: 12 }}>
                        <Text style={styles.value}>Status: {bridgeResult.status}</Text>
                        <Text style={styles.value}>Result: {JSON.stringify(bridgeResult.bridge_result || {})}</Text>
                    </View>
                )}
            </View>

            <TouchableOpacity style={styles.refreshBtn} onPress={handleBridgeHistory}>
                <Text style={styles.refreshBtnText}>Refresh History</Text>
            </TouchableOpacity>

            <View style={styles.card}>
                <Text style={styles.cardTitle}>Bridge History ({bridgeHistory.length})</Text>
                {bridgeHistory.length === 0 ? (
                    <Text style={styles.emptyText}>No history yet</Text>
                ) : (
                    bridgeHistory.map((h, i) => (
                        <View key={h.id || i} style={styles.listItem}>
                            <Text style={styles.itemTitle}>{h.title || h.decision_title || 'Decision'}</Text>
                            <Text style={styles.itemSub}>Sector: {h.sector || 'N/A'} | Status: {h.status || h.result || 'N/A'}</Text>
                            <Text style={styles.itemSub}>Urgency: {h.urgency || 'N/A'}</Text>
                        </View>
                    ))
                )}
            </View>
        </View>
    );

    // ─── Main Render ────────────────────────────────────────────────────

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>⚖️ Governance Dashboard</Text>

            {error && (
                <View style={styles.errorBanner}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {renderTabNav()}

            {loading && <ActivityIndicator size="small" color="#8884d8" style={{ marginVertical: 12 }} />}

            <View style={styles.tabContent}>
                {activeTab === 0 && renderOverview()}
                {activeTab === 1 && renderProposals()}
                {activeTab === 2 && renderVoting()}
                {activeTab === 3 && renderVeto()}
                {activeTab === 4 && renderConstitution()}
                {activeTab === 5 && renderAudit()}
                {activeTab === 6 && renderCouncil()}
                {activeTab === 7 && renderBridge()}
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        padding: 16,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 16,
        color: '#1a1a2e',
    },
    errorBanner: {
        backgroundColor: '#fef2f2',
        borderColor: '#fecaca',
        borderWidth: 1,
        padding: 12,
        borderRadius: 12,
        marginBottom: 12,
    },
    errorText: {
        fontSize: 14,
        color: '#991b1b',
    },
    // ─── Tab Bar ────────────────────────────────────────────────────────
    tabBar: {
        flexDirection: 'row',
        marginBottom: 12,
    },
    tabItem: {
        paddingVertical: 8,
        paddingHorizontal: 16,
        borderRadius: 20,
        backgroundColor: '#e5e5e5',
        marginRight: 8,
    },
    tabItemActive: {
        backgroundColor: '#8884d8',
    },
    tabText: {
        fontSize: 13,
        fontWeight: '600',
        color: '#666',
    },
    tabTextActive: {
        color: '#fff',
    },
    tabContent: {
        minHeight: 300,
    },
    // ─── Cards ──────────────────────────────────────────────────────────
    card: {
        backgroundColor: 'white',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.08,
        shadowRadius: 3,
        elevation: 2,
    },
    cardTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#1a1a2e',
        marginBottom: 12,
    },
    // ─── Stats ──────────────────────────────────────────────────────────
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 8,
    },
    statBox: {
        alignItems: 'center',
        flex: 1,
    },
    statNumber: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#8884d8',
    },
    statLabel: {
        fontSize: 12,
        color: '#666',
        marginTop: 2,
    },
    // ─── Inputs ─────────────────────────────────────────────────────────
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        paddingHorizontal: 12,
        paddingVertical: 10,
        fontSize: 15,
        color: '#1a1a2e',
        backgroundColor: '#fafafa',
        marginBottom: 10,
    },
    textArea: {
        minHeight: 60,
        textAlignVertical: 'top',
    },
    // ─── Pickers ────────────────────────────────────────────────────────
    pickerRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginBottom: 10,
    },
    pickerBtn: {
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 16,
        backgroundColor: '#e5e5e5',
        marginRight: 6,
        marginBottom: 6,
    },
    pickerBtnActive: {
        backgroundColor: '#8884d8',
    },
    pickerText: {
        fontSize: 12,
        fontWeight: '600',
        color: '#666',
    },
    pickerTextActive: {
        color: '#fff',
    },
    // ─── Buttons ────────────────────────────────────────────────────────
    actionBtn: {
        backgroundColor: '#8884d8',
        paddingVertical: 12,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 4,
    },
    actionBtnText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 15,
    },
    refreshBtn: {
        backgroundColor: '#1a1a2e',
        paddingVertical: 10,
        borderRadius: 8,
        alignItems: 'center',
        marginBottom: 16,
    },
    refreshBtnText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 14,
    },
    // ─── Values ─────────────────────────────────────────────────────────
    value: {
        fontSize: 14,
        color: '#333',
        marginBottom: 4,
    },
    emptyText: {
        fontSize: 14,
        color: '#999',
        fontStyle: 'italic',
    },
    // ─── List Items ─────────────────────────────────────────────────────
    listItem: {
        backgroundColor: '#f9f9f9',
        borderRadius: 8,
        padding: 10,
        marginBottom: 8,
        borderLeftWidth: 3,
        borderLeftColor: '#8884d8',
    },
    itemTitle: {
        fontSize: 15,
        fontWeight: 'bold',
        color: '#1a1a2e',
    },
    itemSub: {
        fontSize: 12,
        color: '#666',
        marginTop: 2,
    },
});

export default GovernanceScreen;
