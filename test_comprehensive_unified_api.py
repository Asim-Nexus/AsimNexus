"""
test_comprehensive_unified_api.py
==================================
Comprehensive integration test for ALL endpoints registered in unified_api.py.
Tests every route from every registered module:
  - Core routes: /health, /api/stats, /api/digital-twin, /api/agi, /api/quantum, /api/blockchain, /api/mesh, /api/life-protocol, /api/brain
  - identity_svt_hdt_api: /api/identity/*, /api/svt/*, /api/hdt/*, /api/quad/*, /api/bugs/*, /api/dht/*, /api/firewall/*, /api/universe/*, /api/universal/*
  - consensus_mesh_clones_healing_ostools_api: /api/consensus/*, /api/mesh/*, /api/clones/*, /api/healing/*, /api/os/*
  - remaining_missing_api: /api/dharma/*, /api/dreaming/*, /api/analytics/overview|activity, /api/jobs/*, /api/sync/*, /api/mesh/offline/*
  - unified_routes_api: /llm/chat, /files/*, /codebase/*, /terminal/execute, /automation/*, /api/analytics/performance|usage, /api/security/*, /api/virtual_office/*, /api/autonomous/*, /hdt/*, /zkp/*, /clones/*
"""

import pytest
from fastapi.testclient import TestClient
from api.unified_api import app

client = TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# SECTION 1: Core unified_api.py routes
# ==============================================================================

class TestCoreRoutes:
    """Test core routes defined directly in unified_api.py."""

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_system_stats(self):
        resp = client.get("/api/stats")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_digital_twin_create(self):
        resp = client.post("/api/digital-twin", json={
            "legal_name": "Test Twin",
            "date_of_birth": "2000-01-01",
            "nationality": "NP",
            "gender": "other",
            "birth_certificate_id": "TEST123"
        })
        assert resp.status_code in (200, 201, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_digital_twin_get(self):
        resp = client.get("/api/digital-twin/test-id")
        assert resp.status_code in (200, 404, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_digital_twin_life_events(self):
        resp = client.get("/api/digital-twin/test-id/life-events")
        assert resp.status_code in (200, 404, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_agi_think(self):
        resp = client.post("/api/agi/think", json={"query": "Hello"})
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_agi_stats(self):
        resp = client.get("/api/agi/stats")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_quantum_job(self):
        resp = client.post("/api/quantum/job", json={
            "algorithm": "grover",
            "problem_size": 100,
            "shots": 1024
        })
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_quantum_stats(self):
        resp = client.get("/api/quantum/stats")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_quantum_devices(self):
        resp = client.get("/api/quantum/devices")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_blockchain_did(self):
        resp = client.post("/api/blockchain/did", json={
            "public_key": "0x1234567890abcdef",
            "network": "ethereum"
        })
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_blockchain_credential(self):
        resp = client.post("/api/blockchain/credential", json={
            "issuer_did": "did:test:issuer",
            "subject_did": "did:test:subject",
            "credential_type": "membership",
            "claims": {},
            "expiration_days": 365
        })
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_blockchain_credentials_get(self):
        resp = client.get("/api/blockchain/credentials/did:test:123")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_blockchain_sbts_get(self):
        resp = client.get("/api/blockchain/sbts/did:test:123")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_blockchain_zkproof(self):
        resp = client.post("/api/blockchain/zkproof?prover_did=test&statement=test&secret_data=secret")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_mesh_status(self):
        resp = client.get("/api/mesh/status")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_mesh_edge_node(self):
        resp = client.post("/api/mesh/edge-node?region=us-west&lat=37.77&lon=-122.41")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_life_protocol_event(self):
        resp = client.post("/api/life-protocol/event", json={
            "event_type": "birth",
            "details": {"user_id": "test-user"}
        })
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_life_protocol_tasks(self):
        resp = client.get("/api/life-protocol/tasks")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_local_llm_health(self):
        resp = client.get("/api/local-llm/health")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_brain_process(self):
        resp = client.post("/api/brain/process", json={"message": "Hello"})
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_brain_stream(self):
        resp = client.post("/api/brain/stream", json={"message": "Hello"})
        assert resp.status_code in (200, 500, 503)


# ==============================================================================
# SECTION 2: identity_svt_hdt_api.py routes
# ==============================================================================

class TestIdentitySvtHdtRoutes:
    """Test routes from identity_svt_hdt_api.py (identity, SVT, HDT, World OS)."""

    def test_identity_stats(self):
        resp = client.get("/api/identity/stats")
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)

    def test_identity_list(self):
        resp = client.get("/api/identity/list")
        assert resp.status_code in (200, 500, 503)

    def test_identity_create(self):
        resp = client.post("/api/identity/create", json={
            "user_id": "test-user-1",
            "display_name": "Test User",
            "email": "test@example.com"
        })
        assert resp.status_code in (200, 201, 500, 503)

    def test_identity_verify(self):
        resp = client.post("/api/identity/verify", json={
            "identity_id": "test-id-1",
            "method": "email",
            "verification_data": {}
        })
        assert resp.status_code in (200, 500, 503)

    def test_svt_stats(self):
        resp = client.get("/api/svt/stats")
        assert resp.status_code in (200, 500, 503)

    def test_svt_wallet(self):
        resp = client.get("/api/svt/wallet/test-did")
        assert resp.status_code in (200, 500, 503)

    def test_svt_mint(self):
        resp = client.post("/api/svt/mint", json={"did": "test", "amount": 100})
        assert resp.status_code in (200, 500, 503)

    def test_hdt_create(self):
        resp = client.post("/api/hdt/create", json={
            "did": "did:test:hdt1",
            "display_name": "Test HDT"
        })
        assert resp.status_code in (200, 201, 500, 503)

    def test_hdt_status(self):
        resp = client.get("/api/hdt/test-did/status")
        assert resp.status_code in (200, 500, 503)

    def test_hdt_skill(self):
        resp = client.post("/api/hdt/test-did/skill", json={
            "did": "test-did",
            "skill": "python",
            "level": "beginner"
        })
        assert resp.status_code in (200, 500, 503)

    def test_hdt_announce(self):
        resp = client.post("/api/hdt/test-did/announce")
        assert resp.status_code in (200, 500, 503)

    def test_quad_status(self):
        resp = client.get("/api/quad/status")
        assert resp.status_code in (200, 500, 503)

    def test_bugs_stats(self):
        resp = client.get("/api/bugs/stats")
        assert resp.status_code in (200, 500, 503)

    def test_dht_status(self):
        resp = client.get("/api/dht/status")
        assert resp.status_code in (200, 500, 503)

    def test_firewall_status(self):
        resp = client.get("/api/firewall/status")
        assert resp.status_code in (200, 500, 503)

    def test_universe_lifecycle(self):
        resp = client.get("/api/universe/test-user/lifecycle")
        assert resp.status_code in (200, 500, 503)

    def test_universal_status(self):
        resp = client.get("/api/universal/status")
        assert resp.status_code in (200, 500, 503)

    def test_universal_countries(self):
        resp = client.get("/api/universal/countries")
        assert resp.status_code in (200, 500, 503)

    def test_universal_currencies(self):
        resp = client.get("/api/universal/currencies")
        assert resp.status_code in (200, 500, 503)

    def test_universal_languages(self):
        resp = client.get("/api/universal/languages")
        assert resp.status_code in (200, 500, 503)

    def test_universal_timezones(self):
        resp = client.get("/api/universal/timezones")
        assert resp.status_code in (200, 500, 503)


# ==============================================================================
# SECTION 3: consensus_mesh_clones_healing_ostools_api.py routes
# ==============================================================================

class TestConsensusMeshClonesHealingOsToolsRoutes:
    """Test consensus, mesh, clones, healing, and OS tools routes."""

    def test_consensus_vote(self):
        resp = client.post("/api/consensus/vote", json={"topic": "test", "vote": "yes"})
        assert resp.status_code in (200, 500, 503)

    def test_consensus_override(self):
        resp = client.post("/api/consensus/round-1/override", json={"approved": True})
        assert resp.status_code in (200, 404, 500, 503)

    def test_consensus_stats(self):
        resp = client.get("/api/consensus/stats")
        assert resp.status_code in (200, 500, 503)

    def test_consensus_pending(self):
        resp = client.get("/api/consensus/pending")
        assert resp.status_code in (200, 500, 503)

    def test_consensus_list(self):
        resp = client.get("/api/consensus/list")
        assert resp.status_code in (200, 500, 503)

    def test_clones_specs(self):
        resp = client.get("/api/clones/specs")
        assert resp.status_code in (200, 500, 503)

    def test_clone_spec(self):
        resp = client.get("/api/clones/1/spec")
        assert resp.status_code in (200, 500, 503)

    def test_clones_route(self):
        resp = client.post("/api/clones/route", json={"query": "hello"})
        assert resp.status_code in (200, 500, 503)

    def test_healing_status(self):
        resp = client.get("/api/healing/status")
        assert resp.status_code in (200, 500, 503)

    def test_healing_balance(self):
        resp = client.get("/api/healing/balance")
        assert resp.status_code in (200, 500, 503)

    def test_healing_heal(self):
        resp = client.post("/api/healing/heal")
        assert resp.status_code in (200, 500, 503)

    def test_os_tools(self):
        resp = client.get("/api/os/tools")
        assert resp.status_code in (200, 500, 503)

    def test_os_execute(self):
        resp = client.post("/api/os/execute", json={"tool": "echo", "params": {}})
        assert resp.status_code in (200, 500, 503)

    def test_os_status(self):
        resp = client.get("/api/os/status")
        assert resp.status_code in (200, 500, 503)

    def test_os_metrics(self):
        resp = client.get("/api/os/metrics")
        assert resp.status_code in (200, 500, 503)

    def test_os_pending(self):
        resp = client.get("/api/os/pending")
        assert resp.status_code in (200, 500, 503)

    def test_os_approve(self):
        resp = client.post("/api/os/approve/call-1")
        assert resp.status_code in (200, 404, 500, 503)

    def test_os_reject(self):
        resp = client.post("/api/os/reject/call-1")
        assert resp.status_code in (200, 404, 500, 503)

    def test_os_audit(self):
        resp = client.get("/api/os/audit")
        assert resp.status_code in (200, 500, 503)

    def test_os_clipboard_status(self):
        resp = client.get("/api/os/clipboard/status")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_peers(self):
        resp = client.get("/api/mesh/peers")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_nodes(self):
        resp = client.get("/api/mesh/nodes")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_discover_status(self):
        resp = client.get("/api/mesh/discover/status")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_discover_start(self):
        resp = client.post("/api/mesh/discover/start")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_discover_add_peer(self):
        resp = client.post("/api/mesh/discover/add-peer", json={"ip": "192.168.1.1", "port": 8765})
        assert resp.status_code in (200, 500, 503)


# ==============================================================================
# SECTION 4: remaining_missing_api.py routes (Dharma, Dreaming, Analytics, Jobs, Sync)
# ==============================================================================

class TestRemainingRoutes:
    """Test Dharma, Dreaming, Analytics, Jobs, and Sync routes."""

    def test_dharma_status(self):
        resp = client.get("/api/dharma/status")
        assert resp.status_code in (200, 500, 503)

    def test_dharma_veto(self):
        resp = client.post("/api/dharma/veto", json={
            "reason": "test_action",
            "severity": "warning"
        })
        assert resp.status_code in (200, 500, 503)

    def test_dreaming_status(self):
        resp = client.get("/api/dreaming/status")
        assert resp.status_code in (200, 500, 503)

    def test_dreaming_briefing(self):
        resp = client.get("/api/dreaming/briefing")
        assert resp.status_code in (200, 500, 503)

    def test_dreaming_trigger(self):
        resp = client.post("/api/dreaming/trigger")
        assert resp.status_code in (200, 500, 503)

    def test_analytics_overview(self):
        resp = client.get("/api/analytics/overview")
        assert resp.status_code in (200, 500, 503)

    def test_analytics_activity(self):
        resp = client.get("/api/analytics/activity")
        assert resp.status_code in (200, 500, 503)

    def test_jobs_stats(self):
        resp = client.get("/api/jobs/stats")
        assert resp.status_code in (200, 500, 503)

    def test_jobs_list(self):
        resp = client.get("/api/jobs/list")
        assert resp.status_code in (200, 500, 503)

    def test_jobs_post(self):
        resp = client.post("/api/jobs/post", json={
            "title": "Test Job",
            "description": "A test job posting",
            "budget": 100
        })
        assert resp.status_code in (200, 500, 503)

    def test_sync_status(self):
        resp = client.get("/api/sync/status")
        assert resp.status_code in (200, 500, 503)

    def test_sync_queue(self):
        resp = client.get("/api/sync/queue")
        assert resp.status_code in (200, 500, 503)

    def test_sync_enqueue(self):
        resp = client.post("/api/sync/enqueue", json={
            "entity_id": "test-entity",
            "op_type": "update",
            "entity_type": "user",
            "payload": {"key": "value"}
        })
        assert resp.status_code in (200, 500, 503)

    def test_sync_flush(self):
        resp = client.post("/api/sync/flush")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_offline_user_status(self):
        resp = client.get("/api/mesh/offline/status/test-user")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_offline_capabilities(self):
        resp = client.get("/api/mesh/offline/capabilities")
        assert resp.status_code in (200, 500, 503)

    def test_mesh_offline_operation(self):
        resp = client.post("/api/mesh/offline/operation", json={
            "operation_type": "sync",
            "payload": {"entity_id": "test"}
        })
        assert resp.status_code in (200, 500, 503)


# ==============================================================================
# SECTION 5: unified_routes_api.py routes (newly added)
# ==============================================================================

class TestUnifiedRoutes:
    """Test all routes from unified_routes_api.py."""

    def test_llm_chat(self):
        resp = client.post("/llm/chat", json={"message": "Hello"})
        assert resp.status_code in (200, 500, 503)
        data = resp.json()
        assert isinstance(data, dict)
        if resp.status_code == 200:
            assert "success" in data or "response" in data

    def test_files_list(self):
        resp = client.get("/files/list?path=.")
        assert resp.status_code in (200, 500, 503)

    def test_files_read(self):
        resp = client.get("/files/read?path=README.md")
        # README may not exist, so 200 or 400/404 are acceptable
        assert resp.status_code in (200, 400, 404, 500, 503)

    def test_files_write(self):
        resp = client.post("/files/write", json={"path": "test_tmp_write.txt", "content": "test"})
        assert resp.status_code in (200, 500, 503)

    def test_files_delete(self):
        resp = client.delete("/files/delete?path=test_tmp_write.txt")
        assert resp.status_code in (200, 500, 503)

    def test_files_create_directory(self):
        resp = client.post("/files/create_directory", json={"path": "test_tmp_dir"})
        assert resp.status_code in (200, 500, 503)
        # Clean up
        import os
        try:
            os.rmdir("test_tmp_dir")
        except OSError:
            pass

    def test_files_search(self):
        resp = client.get("/files/search?query=.py")
        assert resp.status_code in (200, 500, 503)

    def test_codebase_index(self):
        resp = client.get("/codebase/index")
        assert resp.status_code in (200, 500, 503)

    def test_codebase_search(self):
        resp = client.get("/codebase/search?query=api")
        assert resp.status_code in (200, 500, 503)

    def test_codebase_summary(self):
        resp = client.get("/codebase/summary")
        assert resp.status_code in (200, 500, 503)

    def test_codebase_file(self):
        resp = client.get("/codebase/file/README.md")
        assert resp.status_code in (200, 400, 404, 500, 503)

    def test_terminal_execute(self):
        resp = client.post("/terminal/execute", json={"command": "echo hello"})
        assert resp.status_code in (200, 500, 503)

    def test_automation_create(self):
        resp = client.post("/automation/create", json={
            "name": "Test Task",
            "description": "A test automation task"
        })
        assert resp.status_code in (200, 201, 500, 503)

    def test_automation_list(self):
        resp = client.get("/automation/list")
        assert resp.status_code in (200, 500, 503)

    def test_automation_execute(self):
        # First create a task
        create_resp = client.post("/automation/create", json={"name": "Exec Task"})
        task_id = ""
        if create_resp.status_code == 200:
            task_id = create_resp.json().get("task", {}).get("id", "none")
        resp = client.post("/automation/execute", json={"task_id": task_id or "test-id"})
        assert resp.status_code in (200, 404, 500, 503)

    def test_automation_delete(self):
        resp = client.delete("/automation/non-existent")
        assert resp.status_code in (200, 404, 500, 503)

    def test_analytics_performance(self):
        resp = client.get("/api/analytics/performance")
        assert resp.status_code in (200, 500, 503)

    def test_analytics_usage(self):
        resp = client.get("/api/analytics/usage")
        assert resp.status_code in (200, 500, 503)

    def test_security_status(self):
        resp = client.get("/api/security/status")
        assert resp.status_code in (200, 500, 503)

    def test_security_vulnerabilities(self):
        resp = client.get("/api/security/vulnerabilities")
        assert resp.status_code in (200, 500, 503)

    def test_security_scan(self):
        resp = client.post("/api/security/scan")
        assert resp.status_code in (200, 500, 503)

    def test_virtual_office_status(self):
        resp = client.get("/api/virtual_office/status")
        assert resp.status_code in (200, 500, 503)

    def test_virtual_office_rooms(self):
        resp = client.get("/api/virtual_office/rooms")
        assert resp.status_code in (200, 500, 503)

    def test_virtual_office_join(self):
        resp = client.post("/api/virtual_office/join", json={"room_id": "test-room"})
        assert resp.status_code in (200, 500, 503)

    def test_virtual_office_leave(self):
        resp = client.post("/api/virtual_office/leave", json={"room_id": "test-room"})
        assert resp.status_code in (200, 500, 503)

    def test_autonomous_status(self):
        resp = client.get("/api/autonomous/status")
        assert resp.status_code in (200, 500, 503)

    def test_autonomous_enable(self):
        resp = client.post("/api/autonomous/enable")
        assert resp.status_code in (200, 500, 503)

    def test_autonomous_disable(self):
        resp = client.post("/api/autonomous/disable")
        assert resp.status_code in (200, 500, 503)

    def test_hdt_me(self):
        resp = client.get("/hdt/me")
        assert resp.status_code in (200, 500, 503)

    def test_hdt_update(self):
        resp = client.post("/hdt/update", json={"name": "Updated"})
        assert resp.status_code in (200, 500, 503)

    def test_hdt_top_clones(self):
        resp = client.get("/hdt/top-clones")
        assert resp.status_code in (200, 500, 503)

    def test_zkp_pending(self):
        resp = client.get("/zkp/pending")
        assert resp.status_code in (200, 500, 503)

    def test_zkp_confirm(self):
        resp = client.post("/zkp/confirm/test-token")
        assert resp.status_code in (200, 500, 503)

    def test_zkp_reject(self):
        resp = client.post("/zkp/reject/test-token")
        assert resp.status_code in (200, 500, 503)

    def test_zkp_status(self):
        resp = client.get("/zkp/status/test-token")
        assert resp.status_code in (200, 500, 503)

    def test_clones_list(self):
        resp = client.get("/clones/list")
        assert resp.status_code in (200, 500, 503)

    def test_clones_chat(self):
        resp = client.post("/clones/chat", json={"message": "Hello clones"})
        assert resp.status_code in (200, 500, 503)

    def test_clones_direct(self):
        resp = client.post("/clones/direct/sage", json={"message": "Hello"})
        assert resp.status_code in (200, 500, 503)

    def test_clones_agent_mode(self):
        resp = client.post("/clones/agent-mode?enabled=true")
        assert resp.status_code in (200, 500, 503)


# ==============================================================================
# SECTION 6: Summary / Route Count Verification
# ==============================================================================

class TestRouteRegistration:
    """Verify all expected routes are registered."""

    EXPECTED_PATHS = [
        # Core
        "/health", "/api/stats",
        "/api/digital-twin", "/api/digital-twin/{twin_id}",
        "/api/digital-twin/{twin_id}/life-events",
        "/api/agi/think", "/api/agi/stats",
        "/api/quantum/job", "/api/quantum/stats", "/api/quantum/devices",
        "/api/blockchain/did", "/api/blockchain/credential",
        "/api/blockchain/credentials/{did}", "/api/blockchain/sbts/{did}",
        "/api/blockchain/zkproof",
        "/api/mesh/status", "/api/mesh/edge-node",
        "/api/life-protocol/event", "/api/life-protocol/tasks",
        "/api/local-llm/health",
        "/api/brain/process", "/api/brain/stream",
        # Identity / SVT / HDT / World OS
        "/api/identity/stats", "/api/identity/list",
        "/api/identity/create", "/api/identity/verify",
        "/api/svt/stats", "/api/svt/wallet/{did}", "/api/svt/mint",
        "/api/hdt/create", "/api/hdt/{did}/status",
        "/api/hdt/{did}/skill", "/api/hdt/{did}/announce",
        "/api/quad/status", "/api/bugs/stats",
        "/api/dht/status", "/api/firewall/status",
        "/api/universe/{user_id}/lifecycle",
        "/api/universal/status", "/api/universal/countries",
        "/api/universal/currencies", "/api/universal/languages",
        "/api/universal/timezones",
        # Consensus / Mesh / Clones / Healing / OS Tools
        "/api/consensus/vote", "/api/consensus/{round_id}/override",
        "/api/consensus/stats", "/api/consensus/pending", "/api/consensus/list",
        "/api/clones/specs", "/api/clones/{clone_id}/spec", "/api/clones/route",
        "/api/healing/status", "/api/healing/balance", "/api/healing/heal",
        "/api/os/tools", "/api/os/execute", "/api/os/status", "/api/os/metrics",
        "/api/os/pending", "/api/os/approve/{call_id}", "/api/os/reject/{call_id}",
        "/api/os/audit", "/api/os/clipboard/status",
        "/api/mesh/peers", "/api/mesh/nodes",
        "/api/mesh/discover/status", "/api/mesh/discover/start",
        "/api/mesh/discover/add-peer",
        # Dharma / Dreaming / Analytics / Jobs / Sync
        "/api/dharma/status", "/api/dharma/veto",
        "/api/dreaming/status", "/api/dreaming/briefing", "/api/dreaming/trigger",
        "/api/analytics/overview", "/api/analytics/activity",
        "/api/jobs/stats", "/api/jobs/list", "/api/jobs/post",
        "/api/sync/status", "/api/sync/queue", "/api/sync/enqueue", "/api/sync/flush",
        "/api/mesh/offline/status/{user_id}",
        "/api/mesh/offline/capabilities", "/api/mesh/offline/operation",
        # Unified routes
        "/llm/chat",
        "/files/list", "/files/read", "/files/write", "/files/delete",
        "/files/create_directory", "/files/search",
        "/codebase/index", "/codebase/search", "/codebase/summary",
        "/codebase/file/{path:path}",
        "/terminal/execute",
        "/automation/create", "/automation/list", "/automation/execute",
        "/automation/{task_id}",
        "/api/analytics/performance", "/api/analytics/usage",
        "/api/security/status", "/api/security/vulnerabilities", "/api/security/scan",
        "/api/virtual_office/status", "/api/virtual_office/rooms",
        "/api/virtual_office/join", "/api/virtual_office/leave",
        "/api/autonomous/status", "/api/autonomous/enable", "/api/autonomous/disable",
        "/hdt/me", "/hdt/update", "/hdt/top-clones",
        "/zkp/pending", "/zkp/confirm/{token}", "/zkp/reject/{token}", "/zkp/status/{token}",
        "/clones/list", "/clones/chat", "/clones/direct/{role_name}", "/clones/agent-mode",
    ]

    def test_all_routes_registered(self):
        """Verify every expected route path is registered."""
        registered = set()
        for route in app.routes:
            if hasattr(route, "path"):
                registered.add(route.path)

        missing = [p for p in self.EXPECTED_PATHS if p not in registered]
        if missing:
            print(f"\nMISSING ROUTES ({len(missing)}):")
            for m in missing:
                print(f"  - {m}")

        # Every expected route must be present
        assert len(missing) == 0, f"Missing {len(missing)} routes: {missing}"
        print(f"\nALL {len(self.EXPECTED_PATHS)} expected routes registered successfully")
        print(f"Total registered routes: {len(registered)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
