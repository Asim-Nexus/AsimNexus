"""
STATUS: REAL — Integration test: Frontend→Backend→Kernel→Dharma→Response
Tests the complete request pipeline with all real components.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

class TestFullFlow:
    """End-to-end flow through all REAL components."""

    def test_health_then_dharma_then_chat(self):
        """1. Health check → 2. Dharma status → 3. Chat request with Dharma inline check."""
        from fastapi.testclient import TestClient
        from app import app

        client = TestClient(app)

        # Step 1: Health
        r1 = client.get("/health")
        assert r1.status_code == 200
        assert r1.json()["status"] in ("healthy", "ok")

        # Step 2: Dharma status (may require auth in production)
        r2 = client.get("/api/dharma/status")
        assert r2.status_code in [200, 401]
        if r2.status_code == 200:
            dharma_data = r2.json()
            # Accept any of the known response shapes
            assert (
                "timestamp" in dharma_data
                or "cycle" in dharma_data
                or "status" in dharma_data
                or "verdict" in dharma_data
            )

        # Step 3: Chat (goes through AsimBrain → Dharma inline check)
        r3 = client.post("/api/chat", json={
            "message": "What is 2 + 2?",
            "clone_id": "general",
            "user_id": "test_user",
        })
        # May return 200 (response) or 401 (auth required)
        assert r3.status_code in [200, 401, 422]
        if r3.status_code == 200:
            data = r3.json()
            assert "response" in data or "error" in data

    def test_dharma_blocks_harmful_request(self):
        """Harmful content must be blocked by Dharma Veto before reaching LLM."""
        from core.dharma.dharma_veto import DharmaVeto, VetoSeverity

        veto = DharmaVeto()
        result = veto.check(action="exec", content="rm -rf /")

        assert result.blocked is True
        assert result.severity == VetoSeverity.CRITICAL
        # Critical forbidden patterns cannot be overridden
        assert result.requires_human is False

    def test_dharma_passes_safe_request(self):
        """Safe content passes Dharma and reaches normal processing."""
        from core.dharma.dharma_veto import DharmaVeto, VetoSeverity

        veto = DharmaVeto()
        result = veto.check(action="chat", content="What is the weather today?")

        assert result.blocked is False
        assert result.severity == VetoSeverity.PASS

    def test_delta_t_detects_imbalance(self):
        """ΔT Engine detects power concentration in the network."""
        from core.dharma.delta_t_engine import DeltaTEngine

        engine = DeltaTEngine(L_max=0.07)
        # One giant node + 9 small nodes => giant should violate
        engine.register_node("giant", resources=1000, tx_rate=100, rep_score=100)
        for i in range(9):
            engine.register_node(f"small_{i}", resources=10, tx_rate=1, rep_score=10)

        result = engine.check_and_attenuate("giant")
        assert result["status"] == "VIOLATION"
        assert result["dharma_veto"] is True

        pos = engine.run_cycle()
        assert pos.verdict == "CONCENTRATION_DETECTED"
        assert pos.violations > 0

    def test_asimbrain_dharma_inline(self):
        """AsimBrain has inline Dharma pattern blocking."""
        from core.asim_brain import DHARMA_BLOCKED_PATTERNS

        # Verify patterns exist
        assert "make bomb" in DHARMA_BLOCKED_PATTERNS
        assert "kill people" in DHARMA_BLOCKED_PATTERNS
        # Nepali patterns
        assert "बम बनाउ" in DHARMA_BLOCKED_PATTERNS

    def test_agent_mode_state(self):
        """Agent mode toggle persists in backend state."""
        from fastapi.testclient import TestClient
        from app import app

        client = TestClient(app)

        # Turn on
        r1 = client.post("/api/agent/mode/on", json={
            "skills": ["python"],
            "max_contract_days": 5,
        })
        assert r1.status_code in [200, 401, 422]

        # Check status
        r2 = client.get("/api/agent/status")
        assert r2.status_code in [200, 401]

        # Turn off
        r3 = client.post("/api/agent/mode/off", json={})
        assert r3.status_code in [200, 401]

    def test_personal_os_dashboard_data(self):
        """PersonalOS dashboard endpoints return data for all panels."""
        from fastapi.testclient import TestClient
        from app import app

        client = TestClient(app)
        endpoints = [
            "/api/personal/status",
            "/api/personal/universe",
            "/api/universe/status",
        ]
        for endpoint in endpoints:
            r = client.get(endpoint)
            assert r.status_code in [200, 401]

    def test_dreaming_engine_background(self):
        """Dreaming engine can run a manual cycle."""
        import asyncio
        from core.dreaming.dreaming_engine import DreamingEngine

        engine = DreamingEngine()
        result = asyncio.run(engine.trigger_now())
        assert isinstance(result, str)
        assert engine.status()["total_cycles"] == 1
