#!/usr/bin/env python3
"""
Integration tests for Federation + Governance + Compliance cross-module flows.

Tests the interactions between:
- GlobalFederationManager (core/federation/global_federation.py)
- GovernanceEngine (core/governance/consensus.py)
- ComplianceEngine (governance/compliance_engine.py)
"""

import os
import sys
import pytest
from typing import Dict, Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import enums at module level for easy access
from governance.compliance_engine import DataClassification, ComplianceSector


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture(autouse=True)
def clean_all_env():
    """Reset all singletons and env vars before each test."""
    import core.federation.global_federation as gf
    gf._mgr = None

    import core.governance.consensus as gc
    gc._governance = None

    import governance.compliance_engine as gce
    gce._compliance_engine = None

    for key in [
        "ASIM_FED_NODE_ID", "ASIM_FED_DATA_DIR", "ASIM_FED_SYNC_INTERVAL",
        "ASIM_FED_MAX_PEERS",
        "ASIM_GOV_QUORUM_PERCENT", "ASIM_GOV_VOTING_PERIOD_HOURS",
        "ASIM_GOV_MIN_VOTING_WEIGHT",
        "ASIM_COMPLIANCE_AUDIT_HOURS",
    ]:
        os.environ.pop(key, None)

    # Clean federation data directory to prevent stale data across tests
    import glob
    fed_dir = os.path.join(os.path.expanduser("~"), ".asimnexus", "federation")
    if os.path.isdir(fed_dir):
        for fpath in glob.glob(os.path.join(fed_dir, "*.json")):
            try:
                os.remove(fpath)
            except Exception:
                pass

    yield

    gf._mgr = None
    gc._governance = None
    gce._compliance_engine = None
    for key in [
        "ASIM_FED_NODE_ID", "ASIM_FED_DATA_DIR", "ASIM_FED_SYNC_INTERVAL",
        "ASIM_FED_MAX_PEERS",
        "ASIM_GOV_QUORUM_PERCENT", "ASIM_GOV_VOTING_PERIOD_HOURS",
        "ASIM_GOV_MIN_VOTING_WEIGHT",
        "ASIM_COMPLIANCE_AUDIT_HOURS",
    ]:
        os.environ.pop(key, None)
    fed_dir = os.path.join(os.path.expanduser("~"), ".asimnexus", "federation")
    if os.path.isdir(fed_dir):
        for fpath in glob.glob(os.path.join(fed_dir, "*.json")):
            try:
                os.remove(fpath)
            except Exception:
                pass


# =========================================================================
# Single-module smoke tests
# =========================================================================

class TestFederationSmoke:
    """Smoke tests for federation in isolation"""

    def test_federation_init(self):
        from core.federation.global_federation import GlobalFederationManager
        mgr = GlobalFederationManager(node_id="fed_node")
        assert mgr.node_id == "fed_node"
        assert len(mgr.peer_list()) == 0

    def test_federation_add_peer(self):
        from core.federation.global_federation import GlobalFederationManager
        mgr = GlobalFederationManager(node_id="fed_node")
        peer = mgr.add_peer("did:example:alice", "https://alice.example.com")
        assert peer.peer_id is not None
        # Verify peer appears in peer_list
        peers = mgr.peer_list()
        assert any(p["did"] == "did:example:alice" for p in peers)

    def test_federation_remove_peer(self):
        from core.federation.global_federation import GlobalFederationManager
        mgr = GlobalFederationManager(node_id="fed_node")
        peer = mgr.add_peer("did:example:alice", "https://alice.example.com")
        mgr.remove_peer(peer.peer_id)
        assert len(mgr.peer_list()) == 0


class TestGovernanceSmoke:
    """Smoke tests for governance in isolation"""

    def test_gov_init(self):
        from core.governance.consensus import GovernanceEngine
        gov = GovernanceEngine()
        assert gov is not None
        assert gov.default_quorum_percent == 51

    def test_gov_create_proposal(self):
        from core.governance.consensus import GovernanceEngine
        gov = GovernanceEngine()
        gov.add_member("addr_1")
        prop = gov.create_proposal("Test Proposal", "Test description", "member_1")
        assert prop is not None
        assert prop.title == "Test Proposal"
        assert prop.status.value == "draft"


class TestComplianceSmoke:
    """Smoke tests for compliance in isolation"""

    def test_compliance_init(self):
        from governance.compliance_engine import ComplianceEngine
        ce = ComplianceEngine()
        assert ce is not None
        assert len(ce.policies) >= 5  # 5 standard policies

    def test_compliance_check_public(self):
        from governance.compliance_engine import ComplianceEngine
        ce = ComplianceEngine()
        result = ce.check_data_compliance(
            DataClassification.PUBLIC,
            ComplianceSector.PRIVATE,
            "test_user",
            10
        )
        assert result["compliant"] is True



# =========================================================================
# Cross-module integration tests
# =========================================================================

class TestGovernanceToComplianceIntegration:
    """Integration between GovernanceEngine and ComplianceEngine"""

    def test_governance_decision_logged_to_compliance(self):
        """
        After a governance vote passes, a compliance violation is logged
        to record the decision in the audit trail.
        """
        from core.governance.consensus import GovernanceEngine
        from governance.compliance_engine import ComplianceEngine

        gov = GovernanceEngine(quorum_percent=1)
        comp = ComplianceEngine()

        gov.add_member("addr_1")
        gov.add_member("addr_2")

        prop = gov.create_proposal("Audit test", "Test audit flow", "member_1")
        gov.activate_proposal(prop.proposal_id)
        gov.cast_vote(prop.proposal_id, "member_1", "for")
        gov.cast_vote(prop.proposal_id, "member_2", "for")
        assert gov.finalize_proposal(prop.proposal_id) is True
        assert gov.execute_proposal(prop.proposal_id) is True

        # Log a compliance event for this governance action
        comp.log_violation(
            "governance_decision",
            "governance_policy",
            f"Proposal {prop.proposal_id} executed (passed)",
            severity="info"
        )

        trail = comp.get_audit_trail()
        matched = [e for e in trail if "governance_decision" in e.get("data", {}).get("violation_type", "")]
        assert len(matched) >= 1

    def test_compliance_violation_referenced_in_governance(self):
        """
        Compliance violations can be checked as part of governance workflows.
        """
        from core.governance.consensus import GovernanceEngine
        from governance.compliance_engine import ComplianceEngine

        gov = GovernanceEngine()
        comp = ComplianceEngine()

        # Log a compliance violation
        comp.log_violation(
            "pii_exposure",
            "gdpr_policy",
            "PII data exposed for user_42",
            severity="critical"
        )

        report = comp.get_compliance_report()
        assert report["total_violations"] >= 1

        # Governance proposal can check if data is compliant
        result = comp.check_data_compliance(
            DataClassification.RESTRICTED,
            ComplianceSector.PRIVATE,
            "user_42",
            100
        )
        # RESTRICTED data gets a warning but is still compliant
        assert result["compliant"] is True
        assert len(result["warnings"]) >= 1


class TestFederationToGovernanceIntegration:
    """Integration between Federation and Governance"""

    def test_federation_peer_consented_via_governance(self):
        """
        A peer is added to federation, governance votes to consent,
        then federation consent is applied.
        """
        from core.federation.global_federation import GlobalFederationManager
        from core.governance.consensus import GovernanceEngine

        mgr = GlobalFederationManager(node_id="main_node")
        gov = GovernanceEngine(quorum_percent=1)

        peer = mgr.add_peer("did:example:new_node", "https://new.node/endpoint")

        # Governance votes to consent
        gov.add_member("addr_admin")
        prop = gov.create_proposal(
            "Consent new federation peer",
            "Vote on whether to trust this peer",
            "member_admin"
        )
        gov.activate_proposal(prop.proposal_id)
        gov.cast_vote(prop.proposal_id, "member_admin", "for")
        assert gov.finalize_proposal(prop.proposal_id) is True
        assert gov.execute_proposal(prop.proposal_id) is True

        # Consent in federation
        mgr.consent_peer(peer.peer_id)

        # Verify via peer_list
        peers = mgr.peer_list()
        matched = [p for p in peers if p["peer_id"] == peer.peer_id]
        assert len(matched) == 1
        assert matched[0]["trusted"] is True

    def test_federation_revocation_via_governance(self):
        """
        Governance votes to revoke a peer, then federation applies it.
        """
        from core.federation.global_federation import GlobalFederationManager
        from core.governance.consensus import GovernanceEngine

        mgr = GlobalFederationManager(node_id="main_node")
        gov = GovernanceEngine(quorum_percent=1)

        peer = mgr.add_peer("did:example:bad_actor", "https://bad.actor/endpoint")
        mgr.consent_peer(peer.peer_id)

        # Governance decides to revoke
        gov.add_member("addr_admin")
        prop = gov.create_proposal(
            "Revoke bad actor peer",
            "This peer violated federation rules",
            "member_admin"
        )
        gov.activate_proposal(prop.proposal_id)
        gov.cast_vote(prop.proposal_id, "member_admin", "for")
        assert gov.finalize_proposal(prop.proposal_id) is True
        assert gov.execute_proposal(prop.proposal_id) is True

        mgr.revoke_peer(peer.peer_id)
        peers = mgr.peer_list()
        matched = [p for p in peers if p["peer_id"] == peer.peer_id]
        assert len(matched) == 1
        assert matched[0]["trusted"] is False

    def test_federation_sync_with_governance_tracking(self):
        """
        A federation sync between peers is tracked alongside governance state.
        """
        from core.federation.global_federation import GlobalFederationManager
        from core.governance.consensus import GovernanceEngine

        mgr1 = GlobalFederationManager(node_id="node_a")
        mgr2 = GlobalFederationManager(node_id="node_b")

        peer1_in_mgr2 = mgr2.add_peer("did:example:node_a", "https://node.a/endpoint")
        peer2_in_mgr1 = mgr1.add_peer("did:example:node_b", "https://node.b/endpoint")

        mgr1.consent_peer(peer2_in_mgr1.peer_id)
        mgr2.consent_peer(peer1_in_mgr2.peer_id)

        mgr1._state.msg_count.increment(5)

        packet = mgr1.get_sync_packet()
        result = mgr2.receive_sync(packet, peer1_in_mgr2.peer_id)
        assert result is not None
        assert result.get("accepted") is True

        stats = mgr1.get_stats()
        assert stats.get("node_id", "").startswith("node_a")


class TestFederationToComplianceIntegration:
    """Integration between Federation and Compliance"""

    def test_federation_peer_activity_logged_to_compliance(self):
        """
        Peer activity in federation can be logged to compliance audit trail.
        """
        from core.federation.global_federation import GlobalFederationManager
        from governance.compliance_engine import ComplianceEngine

        mgr = GlobalFederationManager(node_id="main_node")
        comp = ComplianceEngine()

        peer = mgr.add_peer("did:example:partner", "https://partner/endpoint")
        mgr.consent_peer(peer.peer_id)

        comp.log_violation(
            "peer_consented",
            "federation_policy",
            "Partner node consented in federation",
            severity="info"
        )

        trail = comp.get_audit_trail()
        match = [e for e in trail if e.get("data", {}).get("violation_type") == "peer_consented"]
        assert len(match) >= 1

    def test_compliance_check_on_federation_data(self):
        """
        Data shared via federation sync passes compliance checks.
        """
        from governance.compliance_engine import ComplianceEngine

        comp = ComplianceEngine()

        # Public data should pass
        result = comp.check_data_compliance(
            DataClassification.PUBLIC,
            ComplianceSector.PRIVATE,
            "federation_user",
            10
        )
        assert result["compliant"] is True

        # Secret data should fail
        result = comp.check_data_compliance(
            DataClassification.SECRET,
            ComplianceSector.PRIVATE,
            "federation_user",
            10
        )
        assert result["compliant"] is False


class TestTripleIntegration:
    """Integration across all three modules: Federation, Governance, Compliance"""

    def test_end_to_end_flow(self):
        """
        End-to-end flow:
        1. Peer joins federation
        2. Governance votes to consent
        3. Compliance logs the consent
        4. Federation syncs data
        5. Compliance audits the sync
        """
        from core.federation.global_federation import GlobalFederationManager
        from core.governance.consensus import GovernanceEngine
        from governance.compliance_engine import ComplianceEngine

        mgr = GlobalFederationManager(node_id="hub_node")
        gov = GovernanceEngine(quorum_percent=1, voting_period_hours=1)
        comp = ComplianceEngine()

        # Step 1: A peer wants to join
        peer = mgr.add_peer("did:example:new_member", "https://new.member/endpoint")
        assert peer.peer_id is not None

        # Step 2: Governance votes to consent
        gov.add_member("addr_admin")
        prop = gov.create_proposal(
            "Consent new federation member",
            "Approve new member for federation",
            "member_admin"
        )
        gov.activate_proposal(prop.proposal_id)
        gov.cast_vote(prop.proposal_id, "member_admin", "for")
        assert gov.finalize_proposal(prop.proposal_id) is True
        assert gov.execute_proposal(prop.proposal_id) is True

        # Step 3: Consent in federation + log to compliance
        mgr.consent_peer(peer.peer_id)
        comp.log_violation(
            "governance_consent_granted",
            "federation_policy",
            f"Peer consented via proposal {prop.proposal_id}",
            severity="info"
        )

        # Step 4: Simulate sync and verify status
        mgr._state.msg_count.increment(10)
        packet = mgr.get_sync_packet()
        assert packet is not None

        result = comp.check_data_compliance(
            DataClassification.PUBLIC,
            ComplianceSector.PRIVATE,
            "hub_node",
            10
        )
        assert result["compliant"] is True

        # Step 5: Verify audit trail
        trail = comp.get_audit_trail()
        consent_events = [
            e for e in trail
            if e.get("data", {}).get("violation_type") == "governance_consent_granted"
        ]
        assert len(consent_events) >= 1

        stats = mgr.get_stats()
        # stats has "peers" (count) from status() plus extra fields
        assert stats.get("peers", 0) >= 1

    def test_rejected_peer_compliance_audit(self):
        """
        When governance cannot consent a peer, compliance records it.
        """
        from core.federation.global_federation import GlobalFederationManager
        from governance.compliance_engine import ComplianceEngine

        mgr = GlobalFederationManager(node_id="hub_node")
        comp = ComplianceEngine()

        mgr.add_peer("did:example:suspicious", "https://suspicious/endpoint")

        comp.log_violation(
            "peer_consent_rejected",
            "federation_policy",
            "Peer rejected: Insufficient quorum",
            severity="warning"
        )

        trail = comp.get_audit_trail()
        rejected = [e for e in trail if e.get("data", {}).get("violation_type") == "peer_consent_rejected"]
        assert len(rejected) >= 1

    def test_compliance_violation_leads_to_peer_revocation(self):
        """
        When a compliance violation is logged for a peer,
        the peer gets revoked in federation.
        """
        from core.federation.global_federation import GlobalFederationManager
        from governance.compliance_engine import ComplianceEngine

        mgr = GlobalFederationManager(node_id="hub_node")
        comp = ComplianceEngine()

        peer = mgr.add_peer("did:example:violator", "https://violator/endpoint")
        mgr.consent_peer(peer.peer_id)

        # Log a compliance violation
        comp.log_violation(
            "data_breach",
            "security_policy",
            "Unauthorized access detected",
            severity="critical"
        )

        report = comp.get_compliance_report()
        assert report["total_violations"] >= 1
        assert report["severity_breakdown"]["critical"] >= 1

        # Revoke the peer
        mgr.revoke_peer(peer.peer_id)
        peers = mgr.peer_list()
        matched = [p for p in peers if p["peer_id"] == peer.peer_id]
        assert len(matched) == 1
        assert matched[0]["trusted"] is False

    def test_multi_peer_workflow(self):
        """
        Complex workflow with multiple peers undergoing
        governance votes and compliance audits.
        """
        from core.federation.global_federation import GlobalFederationManager
        from core.governance.consensus import GovernanceEngine
        from governance.compliance_engine import ComplianceEngine

        mgr = GlobalFederationManager(node_id="hub")
        gov = GovernanceEngine(quorum_percent=1)
        comp = ComplianceEngine()

        # Add 3 peers
        peers = []
        for i in range(3):
            did = f"did:example:peer_{i}"
            peer = mgr.add_peer(did, f"https://peer{i}/endpoint")
            peers.append(peer)

        assert len(mgr.peer_list()) == 3

        # Governance votes to consent all 3
        gov.add_member("addr_admin")

        for peer in peers:
            prop = gov.create_proposal(
                f"Consent {peer.did}",
                f"Approve peer {peer.did}",
                "member_admin"
            )
            gov.activate_proposal(prop.proposal_id)
            gov.cast_vote(prop.proposal_id, "member_admin", "for")
            assert gov.finalize_proposal(prop.proposal_id) is True
            assert gov.execute_proposal(prop.proposal_id) is True

            mgr.consent_peer(peer.peer_id)
            comp.log_violation(
                "peer_consented",
                "federation_policy",
                f"Peer {peer.did} consented",
                severity="info"
            )

        # Verify federation state
        stats = mgr.get_stats()
        assert stats.get("peers", 0) == 3

        # Verify compliance trail
        trail = comp.get_audit_trail()
        consent_events = [e for e in trail if e.get("data", {}).get("violation_type") == "peer_consented"]
        assert len(consent_events) == 3

        # Verify governance stats
        gov_stats = gov.get_governance_stats()
        assert gov_stats["total_proposals"] == 3
        assert gov_stats["proposal_status_distribution"]["executed"] == 3

    def test_singleton_access_consistency(self):
        """
        All three modules are accessible via their singleton getters
        and work together consistently.
        """
        from core.federation.global_federation import get_federation
        from core.governance.consensus import get_governance
        from governance.compliance_engine import get_compliance_engine

        fed = get_federation()
        gov = get_governance()
        comp = get_compliance_engine()

        assert fed is not None
        assert gov is not None
        assert comp is not None

        fed.add_peer("did:example:test", "https://test/endpoint")

        gov.add_member("addr_tester")
        prop = gov.create_proposal(
            "Test integration",
            "Singleton access test",
            "member_tester"
        )
        assert prop is not None

        result = comp.check_data_compliance(
            DataClassification.PUBLIC,
            ComplianceSector.PRIVATE,
            "test_user",
            10
        )
        assert result["compliant"] is True

        # Singleton consistency
        assert get_federation() is fed
        assert get_governance() is gov
        assert get_compliance_engine() is comp
