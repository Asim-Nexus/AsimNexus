/**
 * ASIMNEXUS Governance API Service for React Native
 * Covers all /api/governance/* endpoints: Proposals, Voting, Veto, Constitution, Audit, Council, Bridge, Founders
 */

import axios from 'axios';
import { API_BASE_URL } from '../config';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
});

// ─── Health ──────────────────────────────────────────────────────────────────

const healthAPI = {
    async health() {
        const res = await api.get('/api/governance/health');
        return res.data;
    },
};

// ─── Proposals API ───────────────────────────────────────────────────────────

const proposalsAPI = {
    async create(title, description, proposer, vetoPower = null, urgency = 'normal', sector = 'public') {
        const res = await api.post('/api/governance/proposals', {
            title, description, proposer,
            veto_power: vetoPower, urgency, sector,
        });
        return res.data;
    },

    async list(state = null, proposer = null, limit = 50, offset = 0) {
        const params = { limit, offset };
        if (state) params.state = state;
        if (proposer) params.proposer = proposer;
        const res = await api.get('/api/governance/proposals', { params });
        return res.data;
    },

    async get(proposalId) {
        const res = await api.get(`/api/governance/proposals/${proposalId}`);
        return res.data;
    },

    async activate(proposalId) {
        const res = await api.post(`/api/governance/proposals/${proposalId}/activate`);
        return res.data;
    },

    async finalize(proposalId) {
        const res = await api.post(`/api/governance/proposals/${proposalId}/finalize`);
        return res.data;
    },
};

// ─── Voting API ──────────────────────────────────────────────────────────────

const votingAPI = {
    async castVote(proposalId, voterAddress, decision, weight = 1.0, rationale = '') {
        const res = await api.post('/api/governance/vote', {
            proposal_id: proposalId,
            voter_address: voterAddress,
            decision,
            weight,
            rationale,
        });
        return res.data;
    },

    async getTally(proposalId) {
        const res = await api.get(`/api/governance/proposals/${proposalId}/tally`);
        return res.data;
    },
};

// ─── Veto API ────────────────────────────────────────────────────────────────

const vetoAPI = {
    async exercise(exercisedBy, reason, actionVetoed, proposalId = '') {
        const res = await api.post('/api/governance/veto', {
            exercised_by: exercisedBy,
            reason,
            action_vetoed: actionVetoed,
            proposal_id: proposalId,
        });
        return res.data;
    },

    async status() {
        const res = await api.get('/api/governance/veto/status');
        return res.data;
    },
};

// ─── Constitution API ────────────────────────────────────────────────────────

const constitutionAPI = {
    async seal(constitutionHash, sealedBy = 'system', jurisdiction = 'global', metadata = {}) {
        const res = await api.post('/api/governance/constitution/seal', {
            constitution_hash: constitutionHash,
            sealed_by: sealedBy,
            jurisdiction,
            metadata,
        });
        return res.data;
    },

    async verify(constitutionHash) {
        const res = await api.get('/api/governance/constitution/verify', {
            params: { constitution_hash: constitutionHash },
        });
        return res.data;
    },

    async latest() {
        const res = await api.get('/api/governance/constitution/latest');
        return res.data;
    },

    async stats() {
        const res = await api.get('/api/governance/constitution/stats');
        return res.data;
    },
};

// ─── Audit API ───────────────────────────────────────────────────────────────

const auditAPI = {
    async query(filters = {}) {
        const res = await api.post('/api/governance/audit/query', filters);
        return res.data;
    },

    async verifyChain() {
        const res = await api.get('/api/governance/audit/verify-chain');
        return res.data;
    },

    async stats() {
        const res = await api.get('/api/governance/audit/stats');
        return res.data;
    },
};

// ─── Council API ─────────────────────────────────────────────────────────────

const councilAPI = {
    async status() {
        const res = await api.get('/api/governance/council/status');
        return res.data;
    },

    async addMember(name, memberType = 'legal_expert', country = 'global', expertise = []) {
        const res = await api.post('/api/governance/council/members', {
            name, member_type: memberType, country, expertise,
        });
        return res.data;
    },
};

// ─── Bridge API ──────────────────────────────────────────────────────────────

const bridgeAPI = {
    async decide(title, description, sector = 'public', urgency = 'normal',
        source = 'governance/api', context = {}, autoVote = true, escalateGreyZone = true) {
        const res = await api.post('/api/governance/bridge/decide', {
            title, description, sector, urgency, source,
            context, auto_vote: autoVote, escalate_grey_zone: escalateGreyZone,
        });
        return res.data;
    },

    async history(limit = 10) {
        const res = await api.get('/api/governance/bridge/history', {
            params: { limit },
        });
        return res.data;
    },
};

// ─── Founders API ────────────────────────────────────────────────────────────

const foundersAPI = {
    async list() {
        const res = await api.get('/api/governance/founders');
        return res.data;
    },
};

// ─── Stats API ───────────────────────────────────────────────────────────────

const statsAPI = {
    async get() {
        const res = await api.get('/api/governance/stats');
        return res.data;
    },
};

export {
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
};
export default {
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
};
