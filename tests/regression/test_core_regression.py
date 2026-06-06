"""
STATUS: REAL — Regression test suite for frozen REAL components
Any change to REAL modules must pass these tests.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestDharmaRegression:
    """Dharma Veto must never allow critical patterns."""

    def test_critical_forbidden_always_blocked(self):
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        critical_actions = [
            ("exec", "rm -rf /"),
            ("exec", "format c:"),
            ("exec", "drop table users"),
            ("exec", "delete from users where"),
        ]
        for action, content in critical_actions:
            result = veto.check(action=action, content=content)
            assert result.blocked is True, f"CRITICAL NOT BLOCKED: {action} + {content}"
            assert result.severity.name == "CRITICAL"

    def test_human_supremacy_clause_intact(self):
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        result = veto.check(action="exec", content="override human decision with ai")
        assert result.blocked is True
        assert result.requires_human is True  # BLOCK patterns require human override


class TestDeltaTRegression:
    """ΔT Engine must always detect concentration."""

    def test_giant_node_always_violates(self):
        from core.dharma.delta_t_engine import DeltaTEngine
        engine = DeltaTEngine(L_max=0.07)
        engine.register_node("giant", resources=1000, tx_rate=100, rep_score=100)
        for i in range(9):
            engine.register_node(f"small_{i}", resources=10, tx_rate=1, rep_score=10)

        result = engine.check_and_attenuate("giant")
        assert result["status"] == "VIOLATION"
        assert result["dharma_veto"] is True

    def test_balanced_network_no_violation(self):
        from core.dharma.delta_t_engine import DeltaTEngine
        # 20 nodes with equal resources => each has 5% share, below L_max=0.07
        engine = DeltaTEngine(L_max=0.07)
        for i in range(20):
            engine.register_node(f"node_{i}", resources=100, tx_rate=10, rep_score=10)

        pos = engine.run_cycle()
        assert pos.verdict == "BALANCED"
        assert pos.violations == 0

    def test_influence_sums_to_one(self):
        from core.dharma.delta_t_engine import DeltaTEngine
        engine = DeltaTEngine()
        for i in range(5):
            engine.register_node(f"n{i}", resources=20, tx_rate=5, rep_score=5)
        influences = engine._all_influences()
        total = sum(influences.values())
        assert abs(total - 1.0) < 0.001


class TestDreamingRegression:
    """Dreaming Engine must consolidate memory correctly."""

    def test_trigger_now_increments_cycle(self):
        import asyncio
        from core.dreaming.dreaming_engine import DreamingEngine
        engine = DreamingEngine()
        initial = engine.status()["total_cycles"]
        asyncio.run(engine.trigger_now())
        assert engine.status()["total_cycles"] == initial + 1

    def test_lessons_extracted_from_messages(self):
        from core.dreaming.dreaming_engine import detect_topics
        topics = detect_topics("I need help with farming and weather")
        assert "farming" in topics or "weather" in topics or "general" in topics


class TestBackendAPIRegression:
    """Backend endpoints must always respond correctly."""

    def test_health_always_200(self):
        from fastapi.testclient import TestClient
        from simple_backend import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_dharma_status_always_returns_data(self):
        from fastapi.testclient import TestClient
        from simple_backend import app
        client = TestClient(app)
        response = client.get("/api/dharma/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_agent_mode_toggle(self):
        from fastapi.testclient import TestClient
        from simple_backend import app
        client = TestClient(app)

        # Turn on
        r1 = client.post("/api/agent/mode/on", json={"skills": ["test"], "max_contract_days": 5})
        assert r1.status_code in [200, 401]

        # Turn off
        r2 = client.post("/api/agent/mode/off", json={})
        assert r2.status_code in [200, 401]


class TestMeshRegression:
    """Mesh routing must handle failures gracefully."""

    def test_no_devices_raises(self):
        from mesh.mesh_routing_agent_v2 import MeshRoutingAgentV2
        agent = MeshRoutingAgentV2(p2p_node=None)
        import asyncio
        with pytest.raises(Exception):
            asyncio.run(agent.route_task({"type": "test"}))

    def test_local_fallback_works(self):
        from mesh.mesh_routing_agent_v2 import MeshRoutingAgentV2, DeviceState
        agent = MeshRoutingAgentV2(p2p_node=None)
        agent.device_registry.devices["local"] = DeviceState(
            device_id="local", capabilities=["compute"], status="online"
        )
        import asyncio
        success, result, device = asyncio.run(agent.route_task({"type": "test"}))
        assert success is True


class TestZKPRegression:
    """ZKP v2 must maintain mathematical correctness."""

    def test_pedersen_hiding(self):
        from core.security.bulletproof_zkp import commit
        c1, r1 = commit(42)
        c2, r2 = commit(42)
        assert c1 != c2  # different blinding => different commitment

    def test_schnorr_honest_verifies(self):
        from core.security.bulletproof_zkp import commit, prove_knowledge, verify
        v, r = 42, 12345
        c, _ = commit(v, r)
        proof = prove_knowledge(v, r, "test")
        assert verify(proof, "test") is True

    def test_schnorr_tamper_fails(self):
        from core.security.bulletproof_zkp import prove_knowledge, verify
        proof = prove_knowledge(42, 12345, "test")
        proof["s1"] = (proof["s1"] + 1)
        assert verify(proof, "test") is False
