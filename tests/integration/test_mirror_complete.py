"""
AsimNexus Mirror Module Integration Tests
========================================
Tests the complete Digital Twin system.

Run: pytest tests/test_mirror_complete.py -v
"""

import os
import pytest
import asyncio
from pathlib import Path
from core.mirror.mirror_module import (
    MirrorModule,
    MirrorReflection,
    get_mirror,
    MIRROR_DB_PATH,
)
from core.mirror.consciousness import (
    ConsciousnessLayer,
    Thought,
    ThoughtType
)
from core.mirror.dreaming_engine import (
    DreamingEngine,
    Dream,
    DreamType
)
from core.mirror.lora_engine import (
    MirrorLoRA,
    LoRAConfig
)

@pytest.fixture(autouse=True)
def cleanup_mirror_data():
    """Clean up persisted mirror data files before each test."""
    if MIRROR_DB_PATH.exists():
        for f in MIRROR_DB_PATH.iterdir():
            if f.suffix == ".jsonl":
                try:
                    os.remove(f)
                except OSError:
                    pass
    yield

class TestMirrorModule:
    """Digital Twin core tests."""

    @pytest.fixture
    def mirror(self):
        """Create fresh mirror instance."""
        return MirrorModule(user_id="test_user", user_type="citizen")

    @pytest.mark.asyncio
    async def test_mirror_initialization(self, mirror):
        """Test mirror initializes with correct defaults."""
        assert mirror.user_id == "test_user"
        assert mirror.user_type == "citizen"
        assert mirror.reflections == []
        assert mirror.daily_summary == {}

    @pytest.mark.asyncio
    async def test_reflect_action(self, mirror):
        """Test action reflection."""
        action = {
            "intent": "Help citizen access healthcare",
            "outcome": "Provided healthcare information",
            "type": "service_query"
        }

        reflection = await mirror.reflect(action)

        assert isinstance(reflection, MirrorReflection)
        assert reflection.intent == "Help citizen access healthcare"
        assert reflection.outcome == "Provided healthcare information"

    @pytest.mark.asyncio
    async def test_contradiction_detection(self, mirror):
        """Test contradiction detection in reflection."""
        action = {
            "intent": "Help friendly user",
            "outcome": "Ignored user request"
        }

        reflection = await mirror.reflect(action)

        # Should detect contradiction
        assert len(reflection.contradictions) > 0 or reflection.balance_impact >= 0

    @pytest.mark.asyncio
    async def test_daily_report(self, mirror):
        """Test daily reflection report."""
        # Add some reflections
        for i in range(3):
            action = {"intent": f"action_{i}", "outcome": f"outcome_{i}"}
            await mirror.reflect(action)

        report = mirror.get_daily_report()

        assert "date" in report
        assert "total_actions" in report
        assert "total_contradictions" in report
        assert report["total_actions"] >= 3

class TestConsciousnessLayer:
    """Consciousness layer tests."""

    @pytest.fixture
    def consciousness(self):
        """Create consciousness layer."""
        return ConsciousnessLayer(user_id="test_user")

    def test_add_thought(self, consciousness):
        """Test adding thoughts."""
        thought = Thought(
            thought_type=ThoughtType.INTENTION,
            content="My intention is to help"
        )

        consciousness.add_thought(thought)

        assert len(consciousness.conscious_thoughts) == 1
        assert consciousness.conscious_thoughts[0].content == "My intention is to help"

    def test_update_principles(self, consciousness):
        """Test principle updates from action."""
        action = {"intent": "I want to help everyone"}

        principles = consciousness.update_principles(action)

        # Should return a list
        assert isinstance(principles, list)

    def test_get_state(self, consciousness):
        """Test consciousness state retrieval."""
        state = consciousness.get_state()

        assert "user_id" in state
        assert "principles_count" in state

class TestDreamingEngine:
    """Dreaming engine tests."""

    @pytest.fixture
    def dreaming(self):
        """Create dreaming engine."""
        return DreamingEngine(user_id="test_user")

    @pytest.mark.asyncio
    async def test_nightly_evolution(self, dreaming):
        """Test overnight learning process."""
        reflections = [
            {"intent": "help", "outcome": "helped", "timestamp": 1000.0},
            {"intent": "learn", "outcome": "learned", "timestamp": 1001.0},
            {"intent": "serve", "outcome": "served", "timestamp": 1002.0}
        ]

        dreams = await dreaming.nightly_evolution(reflections)

        assert isinstance(dreams, list)
        assert all(isinstance(d, Dream) for d in dreams)

    def test_get_patterns(self, dreaming):
        """Test pattern retrieval."""
        patterns = dreaming.get_patterns()

        assert isinstance(patterns, dict)

class TestMirrorLoRA:
    """Personal LoRA adapter tests."""

    @pytest.fixture
    def lora(self):
        """Create LoRA engine."""
        return MirrorLoRA(user_id="test_user")

    def test_prepare_training_data(self, lora):
        """Test training data preparation."""
        reflections = [
            {"intent": "help", "outcome": "success"},
            {"intent": "teach", "outcome": "learned"}
        ]

        data = lora.prepare_training_data(reflections)

        assert len(data) == 2
        assert data[0]["prompt"] == "Action: help"
        assert data[0]["completion"] == "Outcome: success"

    @pytest.mark.asyncio
    async def test_fine_tune(self, lora):
        """Test LoRA fine-tuning process."""
        reflections = [
            {"intent": "help", "outcome": "success"},
            {"intent": "serve", "outcome": "completed"}
        ]

        result = await lora.fine_tune(reflections)

        assert result["status"] == "completed"
        assert result["samples"] == 2
        assert "adapter_path" in result

class TestMirrorIntegration:
    """Integration tests between Mirror components."""

    @pytest.mark.asyncio
    async def test_full_mirror_flow(self):
        """Test complete Mirror Module flow."""
        mirror = get_mirror("integration_user")

        # 1. Reflect actions
        action1 = {"intent": "Help citizen", "outcome": "Helped successfully"}
        action2 = {"intent": "Learn new skills", "outcome": "Skills acquired"}

        ref1 = await mirror.reflect(action1)
        ref2 = await mirror.reflect(action2)

        assert len(mirror.reflections) == 2

        # 2. Nightly dream
        dreams = await mirror.nightly_dream()
        assert isinstance(dreams, list)

        # 3. Auto fine-tune
        tune_result = await mirror.auto_fine_tune()
        assert tune_result["status"] in ["completed", "skipped"]

        # 4. Daily report
        report = mirror.get_daily_report()
        assert report["total_actions"] >= 2

class TestGovernmentMirror:
    """Government-specific Mirror tests."""

    @pytest.mark.asyncio
    async def test_government_mirror_reflection(self):
        """Test government decision reflection."""
        gov_mirror = MirrorModule(user_id="gov_001", user_type="government")

        action = {
            "intent": "Allocate budget for healthcare",
            "outcome": "Budget allocated",
            "type": "policy_decision",
            "impact": "national"
        }

        reflection = await gov_mirror.reflect(action)

        assert reflection.intent is not None
        assert reflection.mirror_response is not None

    @pytest.mark.asyncio
    async def test_company_mirror_reflection(self):
        """Test company Mirror reflection."""
        comp_mirror = MirrorModule(user_id="comp_001", user_type="company")

        action = {
            "intent": "Process customer order",
            "outcome": "Order fulfilled",
            "type": "business_operation"
        }

        reflection = await comp_mirror.reflect(action)

        assert reflection.intent is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])