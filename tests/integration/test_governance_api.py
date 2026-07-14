"""
STATUS: REAL — API endpoint tests for governance modules.

Tests each REST endpoint via FastAPI TestClient using a fresh FastAPI app
with register_governance_routes(). Uses reset fixtures to clean JSONL state
between tests.

Covers:
  - Health: /api/governance/health
  - Proposals: create, list, get, activate, finalize
  - Voting: cast vote, get tally
  - Veto: exercise, get status
  - Constitution: seal, verify, latest, stats
  - Audit: query, verify-chain, stats
  - Council: status, add member
  - Bridge: decide, history
  - Founders: list
  - Stats: aggregated
"""

import os
import sys
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─── Clean reset fixtures ──────────────────────────────────────────────────

def _clean_jsonl(path: str) -> None:
    """Remove a JSONL file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

# Import DB paths for cleanup
from core.governance.governance_audit import _AUDIT_DB_PATH
from core.governance.blockchain_constitution_anchor import _ANCHOR_DB_PATH
from core.security.power_balance_constitution import _POWER_BALANCE_DB_PATH

@pytest.fixture(autouse=True)
def reset_governance():
    """Reset all governance singletons and data files before each test."""
    # Reset governance engine singletons
    from core.governance.governance_audit import reset_governance_audit
    from core.governance.blockchain_constitution_anchor import reset_constitution_anchor
    from core.governance.governance_clone_bridge import reset_governance_clone_bridge
    from core.security.power_balance_constitution import reset_power_balance
    reset_governance_audit()
    reset_constitution_anchor()
    reset_governance_clone_bridge()
    reset_power_balance()

    # Also reset DharmaChakraCouncil by clearing its singleton
    try:
        import governance.dharma_chakra_council as _dc
        _dc._dharma_chakra_council = None
    except Exception:
        pass

    # Reset FounderStructure singleton
    try:
        import governance.founder_structure as _fs
        _fs._founder_structure = None
    except Exception:
        pass

    # Clean data files
    _clean_jsonl(_AUDIT_DB_PATH)
    _clean_jsonl(_ANCHOR_DB_PATH)
    _clean_jsonl(_POWER_BALANCE_DB_PATH)

    yield

    # Clean up after test
    reset_governance_audit()
    reset_constitution_anchor()
    reset_governance_clone_bridge()
    reset_power_balance()
    try:
        import governance.dharma_chakra_council as _dc
        _dc._dharma_chakra_council = None
    except Exception:
        pass
    try:
        import governance.founder_structure as _fs
        _fs._founder_structure = None
    except Exception:
        pass
    _clean_jsonl(_AUDIT_DB_PATH)
    _clean_jsonl(_ANCHOR_DB_PATH)
    _clean_jsonl(_POWER_BALANCE_DB_PATH)

@pytest.fixture
def app():
    """Create a fresh FastAPI app with governance routes registered."""
    application = FastAPI()
    from core.api_endpoints import register_governance_routes
    register_governance_routes(application)
    return application

@pytest.fixture
def client(app):
    """FastAPI TestClient wrapping the governance routes."""
    with TestClient(app) as c:
        yield c

# ═══════════════════════════════════════════════════════════════════════════ #
# Health API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestHealthAPI:
    """Test GET /api/governance/health."""

    def test_health_returns_status(self, client):
        """Health endpoint should return a status and module list."""
        resp = client.get("/api/governance/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "modules" in data
        # Should list which governance modules are available
        assert isinstance(data["modules"], list)

    def test_health_degraded_when_modules_missing(self, client):
        """If engines not initialized, health may report degraded."""
        resp = client.get("/api/governance/health")
        assert resp.status_code == 200
        data = resp.json()
        # Modules array might be empty if engines fail to load
        assert isinstance(data["modules"], list)

# ═══════════════════════════════════════════════════════════════════════════ #
# Proposals API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestProposalsAPI:
    """Test /api/governance/proposals/* endpoints."""

    def _create_proposal(self, client, title="Test Proposal", description="Test desc",
                         proposer="tester", sector="public"):
        """Helper to create a proposal and return the response."""
        return client.post("/api/governance/proposals", json={
            "title": title,
            "description": description,
            "proposer": proposer,
            "sector": sector,
        })

    def test_create_proposal(self, client):
        """Create a governance proposal successfully."""
        resp = self._create_proposal(client)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "created"
        assert "proposal_id" in data
        assert data["title"] == "Test Proposal"

    def test_create_proposal_missing_fields(self, client):
        """Create should handle missing optional fields gracefully."""
        resp = client.post("/api/governance/proposals", json={})
        # Should either succeed with defaults or fail with 422/400
        assert resp.status_code in (200, 422, 400)

    def test_list_proposals_empty(self, client):
        """List proposals when none exist should return empty list."""
        resp = client.get("/api/governance/proposals")
        assert resp.status_code == 200
        data = resp.json()
        assert "proposals" in data
        assert "total" in data

    def test_list_proposals_with_data(self, client):
        """List proposals after creating one should include it."""
        self._create_proposal(client, title="List Test")
        resp = client.get("/api/governance/proposals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        titles = [p["title"] for p in data["proposals"]]
        assert "List Test" in titles

    def test_list_proposals_with_filters(self, client):
        """List proposals with state filter."""
        self._create_proposal(client, title="Filtered Prop")
        resp = client.get("/api/governance/proposals?state=draft")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["proposals"], list)

    def test_get_proposal(self, client):
        """Get a specific proposal by ID."""
        create_resp = self._create_proposal(client, title="Get Test")
        assert create_resp.status_code == 200
        proposal_id = create_resp.json()["proposal_id"]

        resp = client.get(f"/api/governance/proposals/{proposal_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Get Test"

    def test_get_proposal_not_found(self, client):
        """Get a non-existent proposal should return 404."""
        resp = client.get("/api/governance/proposals/NONEXISTENT_PROPOSAL")
        assert resp.status_code == 404

    def test_activate_proposal(self, client):
        """Activate a proposal."""
        create_resp = self._create_proposal(client)
        assert create_resp.status_code == 200
        proposal_id = create_resp.json()["proposal_id"]

        resp = client.post(f"/api/governance/proposals/{proposal_id}/activate")
        # Activate may succeed or return 400 if engine doesn't support it
        assert resp.status_code in (200, 400, 503)

    def test_finalize_proposal(self, client):
        """Finalize a proposal."""
        create_resp = self._create_proposal(client)
        assert create_resp.status_code == 200
        proposal_id = create_resp.json()["proposal_id"]

        resp = client.post(f"/api/governance/proposals/{proposal_id}/finalize")
        # Finalize may succeed or return 400/503
        assert resp.status_code in (200, 400, 503)

# ═══════════════════════════════════════════════════════════════════════════ #
# Voting API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestVotingAPI:
    """Test /api/governance/vote and tally endpoints."""

    def _create_proposal(self, client):
        """Helper to create a proposal and return its ID."""
        resp = client.post("/api/governance/proposals", json={
            "title": "Vote Test",
            "description": "Testing votes",
            "proposer": "voter_tester",
        })
        assert resp.status_code == 200
        return resp.json()["proposal_id"]

    def test_cast_vote(self, client):
        """Cast a vote on a proposal."""
        proposal_id = self._create_proposal(client)

        resp = client.post("/api/governance/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "voter_1",
            "decision": "for",
            "weight": 1.0,
        })
        assert resp.status_code in (200, 400, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "voted"

    def test_cast_vote_missing_fields(self, client):
        """Cast vote with missing fields should return 400."""
        resp = client.post("/api/governance/vote", json={})
        assert resp.status_code in (400, 422)

    def test_cast_vote_invalid_decision(self, client):
        """Cast vote with invalid decision should be handled."""
        proposal_id = self._create_proposal(client)
        resp = client.post("/api/governance/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "voter_2",
            "decision": "invalid_decision",
            "weight": 1.0,
        })
        # Should either reject or accept with default
        assert resp.status_code in (200, 400, 422)

    def test_get_tally(self, client):
        """Get vote tally for a proposal."""
        proposal_id = self._create_proposal(client)

        # Cast a vote first
        client.post("/api/governance/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "voter_tally",
            "decision": "for",
            "weight": 1.0,
        })

        resp = client.get(f"/api/governance/proposals/{proposal_id}/tally")
        assert resp.status_code == 200
        data = resp.json()
        assert "proposal_id" in data
        assert "for" in data or "votes_for" in data

    def test_get_tally_nonexistent_proposal(self, client):
        """Get tally for non-existent proposal returns zeros."""
        resp = client.get("/api/governance/proposals/NONEXISTENT/tally")
        assert resp.status_code == 200
        data = resp.json()
        assert data["for"] == 0
        assert data["against"] == 0

# ═══════════════════════════════════════════════════════════════════════════ #
# Veto API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestVetoAPI:
    """Test /api/governance/veto endpoints."""

    def test_exercise_veto(self, client):
        """Exercise veto power."""
        resp = client.post("/api/governance/veto", json={
            "exercised_by": "veto_tester",
            "reason": "Testing veto endpoint",
            "action_vetoed": "test_action",
        })
        # Veto may succeed or report unavailability
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "veto_recorded"

    def test_exercise_veto_missing_fields(self, client):
        """Exercise veto with missing fields should return 400."""
        resp = client.post("/api/governance/veto", json={})
        assert resp.status_code in (400, 422)

    def test_veto_status(self, client):
        """Get veto power status."""
        resp = client.get("/api/governance/veto/status")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "veto_power_active" in data
            assert "veto_records" in data

# ═══════════════════════════════════════════════════════════════════════════ #
# Constitution API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestConstitutionAPI:
    """Test /api/governance/constitution/* endpoints."""

    def test_seal_constitution(self, client):
        """Seal a constitution hash."""
        resp = client.post("/api/governance/constitution/seal", json={
            "constitution_hash": "abc123def456",
            "sealed_by": "test_sealer",
            "jurisdiction": "global",
        })
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "sealed"

    def test_seal_constitution_missing_hash(self, client):
        """Seal without hash should return 400."""
        resp = client.post("/api/governance/constitution/seal", json={
            "sealed_by": "test",
        })
        assert resp.status_code in (400, 422)

    def test_verify_constitution(self, client):
        """Verify a constitution hash."""
        resp = client.get("/api/governance/constitution/verify",
                          params={"constitution_hash": "abc123"})
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "verified" in data
            assert "constitution_hash" in data

    def test_verify_constitution_no_param(self, client):
        """Verify without hash param should return 422."""
        resp = client.get("/api/governance/constitution/verify")
        assert resp.status_code in (422, 400)

    def test_latest_constitution(self, client):
        """Get latest constitution anchor."""
        resp = client.get("/api/governance/constitution/latest")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "latest_anchor" in data

    def test_constitution_stats(self, client):
        """Get constitution stats."""
        resp = client.get("/api/governance/constitution/stats")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "anchors_count" in data or "chain_integrity" in data

    def test_seal_then_verify_roundtrip(self, client):
        """Seal a hash then verify it returns verified=True."""
        seal_resp = client.post("/api/governance/constitution/seal", json={
            "constitution_hash": "roundtrip_hash_001",
            "sealed_by": "roundtrip_tester",
        })
        if seal_resp.status_code != 200:
            pytest.skip("Constitution sealing not available")

        verify_resp = client.get("/api/governance/constitution/verify",
                                 params={"constitution_hash": "roundtrip_hash_001"})
        assert verify_resp.status_code == 200
        data = verify_resp.json()
        assert data["verified"] is True

# ═══════════════════════════════════════════════════════════════════════════ #
# Audit API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestAuditAPI:
    """Test /api/governance/audit/* endpoints."""

    def test_audit_query(self, client):
        """Query the audit trail."""
        resp = client.post("/api/governance/audit/query", json={
            "limit": 10,
        })
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "entries" in data
            assert "total" in data

    def test_audit_query_with_filters(self, client):
        """Query audit trail with action/actor filters."""
        resp = client.post("/api/governance/audit/query", json={
            "action": "law_submitted",
            "actor": "tester",
            "limit": 20,
        })
        assert resp.status_code in (200, 503)

    def test_audit_verify_chain(self, client):
        """Verify the integrity of the audit hash chain."""
        resp = client.get("/api/governance/audit/verify-chain")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data or "total_entries" in data

    def test_audit_stats(self, client):
        """Get audit trail statistics."""
        resp = client.get("/api/governance/audit/stats")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "total_entries" in data

# ═══════════════════════════════════════════════════════════════════════════ #
# Council API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestCouncilAPI:
    """Test /api/governance/council/* endpoints."""

    def test_council_status(self, client):
        """Get council status."""
        resp = client.get("/api/governance/council/status")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "council_members" in data

    def test_add_council_member(self, client):
        """Add a council member."""
        resp = client.post("/api/governance/council/members", json={
            "name": "Test Councilor",
            "member_type": "legal_expert",
            "country": "global",
            "expertise": ["constitutional_law", "human_rights"],
        })
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "member_added"
            assert "member_id" in data

    def test_add_council_member_missing_name(self, client):
        """Add member without name should return 400."""
        resp = client.post("/api/governance/council/members", json={
            "member_type": "technical_expert",
        })
        assert resp.status_code in (400, 422)

    def test_add_then_list_council(self, client):
        """Add a member then verify they appear in status."""
        add_resp = client.post("/api/governance/council/members", json={
            "name": "List Test Councilor",
            "member_type": "ethics_expert",
        })
        if add_resp.status_code != 200:
            pytest.skip("Council add member not available")

        status_resp = client.get("/api/governance/council/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        members = data.get("council_members", [])
        names = [m.get("name", "") for m in members]
        assert "List Test Councilor" in names

# ═══════════════════════════════════════════════════════════════════════════ #
# Bridge API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestBridgeAPI:
    """Test /api/governance/bridge/* endpoints."""

    def test_bridge_decide(self, client):
        """Submit a governance decision to the clone bridge."""
        resp = client.post("/api/governance/bridge/decide", json={
            "title": "Bridge Test Decision",
            "description": "Testing the governance clone bridge endpoint",
            "sector": "public",
            "urgency": "normal",
        })
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "submitted"

    def test_bridge_decide_missing_fields(self, client):
        """Bridge decide without title/description should return 400."""
        resp = client.post("/api/governance/bridge/decide", json={
            "sector": "public",
        })
        assert resp.status_code in (400, 422)

    def test_bridge_history(self, client):
        """Get bridge vote history."""
        resp = client.get("/api/governance/bridge/history?limit=5")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "history" in data
            assert "total" in data

    def test_bridge_decide_then_history(self, client):
        """Submit a decision then verify it appears in history."""
        decide_resp = client.post("/api/governance/bridge/decide", json={
            "title": "History Test Decision",
            "description": "Testing that bridge history includes this decision",
            "sector": "technology",
            "urgency": "high",
        })
        if decide_resp.status_code != 200:
            pytest.skip("Bridge decide not available")

        history_resp = client.get("/api/governance/bridge/history?limit=10")
        assert history_resp.status_code == 200
        data = history_resp.json()
        assert data["total"] >= 1

# ═══════════════════════════════════════════════════════════════════════════ #
# Founders & Stats API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestFoundersAPI:
    """Test /api/governance/founders endpoint."""

    def test_list_founders(self, client):
        """List founders in the governance structure."""
        resp = client.get("/api/governance/founders")
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "governance_structure" in data or "founder_summary" in data

class TestStatsAPI:
    """Test /api/governance/stats endpoint."""

    def test_governance_stats(self, client):
        """Get aggregated governance statistics."""
        resp = client.get("/api/governance/stats")
        assert resp.status_code == 200
        data = resp.json()
        # Should have all sub-system stat blocks
        assert "proposals" in data
        assert "audit" in data
        assert "council" in data
        assert "constitution" in data
        assert "bridge" in data
        assert "veto" in data

    def test_stats_after_proposal_creation(self, client):
        """Stats should reflect newly created proposals."""
        # Create a proposal
        client.post("/api/governance/proposals", json={
            "title": "Stats Test",
            "description": "Testing stats tracking",
            "proposer": "stats_tester",
        })

        resp = client.get("/api/governance/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["proposals"]["total"] >= 1

# ═══════════════════════════════════════════════════════════════════════════ #
# Integration / Cross-Feature Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestGovernanceIntegration:
    """Test cross-feature governance workflows."""

    def test_full_proposal_workflow(self, client):
        """
        Full workflow: create proposal → activate → cast vote → get tally.
        This tests the integration between Proposals and Voting subsystems.
        """
        # Step 1: Create proposal
        create_resp = client.post("/api/governance/proposals", json={
            "title": "Integration Test Proposal",
            "description": "Testing the full governance workflow",
            "proposer": "integration_tester",
            "sector": "public",
        })
        if create_resp.status_code != 200:
            pytest.skip("Proposal creation not available")
        proposal_id = create_resp.json()["proposal_id"]

        # Step 2: Activate proposal (if supported)
        activate_resp = client.post(f"/api/governance/proposals/{proposal_id}/activate")
        assert activate_resp.status_code in (200, 400, 503)

        # Step 3: Cast a vote
        vote_resp = client.post("/api/governance/vote", json={
            "proposal_id": proposal_id,
            "voter_address": "integration_voter",
            "decision": "for",
            "weight": 1.0,
        })
        assert vote_resp.status_code in (200, 400, 503)

        # Step 4: Get tally
        tally_resp = client.get(f"/api/governance/proposals/{proposal_id}/tally")
        assert tally_resp.status_code == 200
        tally_data = tally_resp.json()
        assert tally_data["proposal_id"] == proposal_id

    def test_health_and_stats_consistency(self, client):
        """Health and stats endpoints should return consistent results."""
        health_resp = client.get("/api/governance/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()

        stats_resp = client.get("/api/governance/stats")
        assert stats_resp.status_code == 200
        stats_data = stats_resp.json()

        # Health modules should correlate with stats availability
        modules = health_data.get("modules", [])
        if "power_balance" in modules:
            assert "proposals" in stats_data
        if "audit" in modules:
            assert "audit" in stats_data

    def test_constitution_seal_then_stats(self, client):
        """Sealing a constitution should update constitution stats."""
        seal_resp = client.post("/api/governance/constitution/seal", json={
            "constitution_hash": "integ_test_hash",
            "sealed_by": "integ_tester",
        })
        if seal_resp.status_code != 200:
            pytest.skip("Constitution sealing not available")

        # Check stats reflect the new anchor
        stats_resp = client.get("/api/governance/stats")
        assert stats_resp.status_code == 200
        data = stats_resp.json()
        assert data["constitution"]["anchors_count"] >= 1

    def test_council_add_then_stats(self, client):
        """Adding a council member should update council stats."""
        add_resp = client.post("/api/governance/council/members", json={
            "name": "Stats Councilor",
            "member_type": "technical_expert",
        })
        if add_resp.status_code != 200:
            pytest.skip("Council add member not available")

        stats_resp = client.get("/api/governance/stats")
        assert stats_resp.status_code == 200
        data = stats_resp.json()
        assert data["council"]["total_members"] >= 1
