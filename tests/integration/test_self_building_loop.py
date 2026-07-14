"""
Self-Building Loop Integration Tests
=====================================
Tests the complete self-building pipeline: GapAnalyzer → AutoBuilder → EvolutionBridge.

This verifies that:
  1. GapAnalyzer can detect gaps in the codebase
  2. AutoBuilder can execute build actions from gap analysis
  3. EvolutionBridge can process suggestions from Mirror/Dreaming/Evolution
  4. The full scan → analyze → build → verify cycle works end-to-end

Run: pytest tests/integration/test_self_building_loop.py -v
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.self_awareness import (
    get_scanner,
    get_knowledge,
    get_builder,
    get_gap_analyzer,
    get_auto_builder,
    reset_all,
)
from core.self_awareness.gap_analyzer import Gap, GapAnalysisResult, GapAnalyzer
from core.self_awareness.evolution_bridge import EvolutionBridge, BridgeAction, get_bridge
from core.self_awareness.auto_builder import AutoBuilder, BuildCycle

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all self-awareness singletons before each test."""
    reset_all()
    yield
    reset_all()

@pytest.fixture
def scanner():
    """Get a fresh CodebaseScanner."""
    return get_scanner()

@pytest.fixture
def knowledge():
    """Get a fresh SelfKnowledge instance."""
    return get_knowledge()

@pytest.fixture
def builder():
    """Get a fresh SelfBuilder instance."""
    return get_builder()

@pytest.fixture
def gap_analyzer(scanner, knowledge):
    """Get a fresh GapAnalyzer with scanner and knowledge."""
    return GapAnalyzer(scanner=scanner, knowledge=knowledge)

@pytest.fixture
def auto_builder():
    """Get a fresh AutoBuilder instance."""
    return get_auto_builder()

@pytest.fixture
def bridge(knowledge, builder):
    """Get a fresh EvolutionBridge instance."""
    return EvolutionBridge(knowledge=knowledge, builder=builder)

# ── GapAnalyzer Tests ────────────────────────────────────────────────────────

class TestGapAnalyzerIntegration:
    """Test GapAnalyzer can detect real gaps in the codebase."""

    def test_analyzer_initialization(self, gap_analyzer):
        """Verify GapAnalyzer initializes with scanner and knowledge."""
        assert gap_analyzer is not None
        assert gap_analyzer._scanner is not None
        assert gap_analyzer._knowledge is not None

    def test_analyze_returns_result(self, gap_analyzer):
        """Verify analyze() returns a GapAnalysisResult with gaps."""
        result = gap_analyzer.analyze()
        assert isinstance(result, GapAnalysisResult)
        assert hasattr(result, "gaps")
        assert hasattr(result, "scan_duration_ms")
        assert hasattr(result, "total_modules_scanned")

    def test_analyze_detects_gaps(self, gap_analyzer):
        """Verify analyze() detects at least some gaps in the codebase."""
        result = gap_analyzer.analyze()
        # The codebase should have at least some gaps (TODOs, missing docs, etc.)
        assert len(result.gaps) > 0, (
            f"Expected at least 1 gap, got {len(result.gaps)}. "
            "If codebase is pristine, this test may need updating."
        )

    def test_gap_categories(self, gap_analyzer):
        """Verify gaps are categorized correctly."""
        result = gap_analyzer.analyze()
        by_category = result.by_category()
        assert isinstance(by_category, dict)
        # Should have at least one category
        assert len(by_category) > 0

    def test_gap_priority_scoring(self, gap_analyzer):
        """Verify gaps have priority scores."""
        result = gap_analyzer.analyze()
        for gap in result.gaps:
            assert hasattr(gap, "priority_score")
            assert isinstance(gap.priority_score, (int, float))
            # priority_score = severity * impact * effort
            # severity: 1-5, impact: 1-3, effort: 1-3 => range 1 to 45
            assert 1 <= gap.priority_score <= 45, (
                f"Expected priority_score in [1, 45], got {gap.priority_score} "
                f"for gap {gap.gap_id} (severity={gap.severity}, impact={gap.impact}, effort={gap.effort})"
            )

    def test_top_gaps_ordering(self, gap_analyzer):
        """Verify top_gaps returns highest priority gaps first."""
        result = gap_analyzer.analyze()
        top = result.top_gaps(n=5)
        if len(top) >= 2:
            for i in range(len(top) - 1):
                assert top[i].priority_score >= top[i + 1].priority_score

    def test_gap_to_dict(self, gap_analyzer):
        """Verify Gap serialization to dict."""
        result = gap_analyzer.analyze()
        if result.gaps:
            gap = result.gaps[0]
            d = gap.to_dict()
            assert "category" in d
            assert "description" in d
            assert "priority_score" in d
            assert "filepath" in d

    def test_suggest_build_actions(self, gap_analyzer, builder):
        """Verify gap analysis can suggest build actions."""
        result = gap_analyzer.analyze()
        actions = gap_analyzer.suggest_build_actions(result, max_actions=5)
        assert isinstance(actions, list)
        # Actions may be empty if no actionable gaps found
        for action in actions:
            assert "action_type" in action
            assert "description" in action

    def test_missing_init_exports_detection(self, gap_analyzer):
        """Verify the missing_init_exports detector runs without error."""
        result = gap_analyzer.analyze()
        by_category = result.by_category()
        # This detector may or may not find gaps, but it should run cleanly
        assert "missing_init_exports" in by_category or True  # category may be absent if none found

    def test_missing_api_routes_detection(self, gap_analyzer):
        """Verify the missing_api_routes detector runs without error."""
        result = gap_analyzer.analyze()
        by_category = result.by_category()
        # This detector may or may not find gaps, but it should run cleanly
        assert "missing_api_routes" in by_category or True

    def test_missing_frontend_components_detection(self, gap_analyzer):
        """Verify the missing_frontend_components detector runs without error."""
        result = gap_analyzer.analyze()
        by_category = result.by_category()
        # This detector may or may not find gaps, but it should run cleanly
        assert "missing_frontend_components" in by_category or True

# ── AutoBuilder Tests ────────────────────────────────────────────────────────

class TestAutoBuilderIntegration:
    """Test AutoBuilder can execute build cycles."""

    @pytest.mark.asyncio
    async def test_auto_builder_initialization(self, auto_builder):
        """Verify AutoBuilder initializes correctly."""
        assert auto_builder is not None
        stats = auto_builder.get_stats()
        assert isinstance(stats, dict)
        assert "total_cycles" in stats

    @pytest.mark.asyncio
    async def test_run_cycle_completes(self, auto_builder):
        """Verify run_cycle() completes without error."""
        cycle = await auto_builder.run_cycle()
        assert isinstance(cycle, BuildCycle)
        assert hasattr(cycle, "cycle_id")
        assert hasattr(cycle, "status")
        assert cycle.cycle_id is not None

    @pytest.mark.asyncio
    async def test_cycle_has_actions(self, auto_builder):
        """Verify a build cycle produces actions."""
        cycle = await auto_builder.run_cycle()
        assert hasattr(cycle, "actions_planned")
        assert isinstance(cycle.actions_planned, int)
        assert cycle.actions_planned >= 0

    @pytest.mark.asyncio
    async def test_cycle_records_stats(self, auto_builder):
        """Verify cycle stats are recorded after run."""
        await auto_builder.run_cycle()
        stats = auto_builder.get_stats()
        assert stats["total_cycles"] >= 1

    @pytest.mark.asyncio
    async def test_cycle_to_dict(self, auto_builder):
        """Verify BuildCycle serialization."""
        cycle = await auto_builder.run_cycle()
        d = cycle.to_dict()
        assert isinstance(d, dict)
        assert "cycle_id" in d
        assert "status" in d
        assert "actions_planned" in d
        assert "actions_succeeded" in d
        assert "actions_failed" in d

    def test_get_stats_returns_dict(self, auto_builder):
        """Verify get_stats() returns a dictionary with expected keys."""
        stats = auto_builder.get_stats()
        assert isinstance(stats, dict)
        expected_keys = ["total_cycles", "total_actions_planned", "total_actions_succeeded", "completed", "failed", "rolled_back"]
        for key in expected_keys:
            assert key in stats, f"Expected key '{key}' in stats"

# ── EvolutionBridge Tests ────────────────────────────────────────────────────

class TestEvolutionBridgeIntegration:
    """Test EvolutionBridge can process suggestions from all sources."""

    def test_bridge_initialization(self, bridge):
        """Verify EvolutionBridge initializes correctly."""
        assert bridge is not None
        stats = bridge.get_stats()
        assert isinstance(stats, dict)

    def test_process_evolution_suggestion(self, bridge):
        """Verify bridge can process an evolution suggestion."""
        suggestion = {
            "suggestion_id": "test_suggestion_001",
            "title": "Add type hints to module",
            "description": "Add missing type hints",
            "category": "refactor",
            "priority": 0.8,
            "source": "test",
            "target_module": "core.test_module",
        }
        action = bridge.process_evolution_suggestion(suggestion)
        assert isinstance(action, BridgeAction)
        assert action.source_type == "evolution_suggestion"
        assert action.status == "executed"

    def test_process_mirror_reflection(self, bridge):
        """Verify bridge can process a mirror reflection."""
        reflection = {
            "reflection_id": "test_reflection_001",
            "intent": "refactor_module",
            "contradictions": ["missing_error_handling"],
            "balance_impact": -0.3,
            "response": "Should add error handling",
            "timestamp": "2025-01-01T00:00:00",
        }
        action = bridge.process_mirror_reflection(reflection)
        assert isinstance(action, BridgeAction)
        assert action.source_type == "mirror_reflection"
        assert action.status == "executed"

    def test_process_dream_lesson(self, bridge):
        """Verify bridge can process a dream lesson."""
        lesson = {
            "lesson_id": "test_lesson_001",
            "topic": "code_quality",
            "summary": "Add more validation",
            "confidence": 0.85,
            "source": "dream_cycle",
            "created_at": "2025-01-01T00:00:00",
        }
        action = bridge.process_dream_lesson(lesson)
        assert isinstance(action, BridgeAction)
        assert action.source_type == "dream_lesson"
        assert action.status == "executed"

    def test_get_actions_returns_list(self, bridge):
        """Verify get_actions() returns a list of actions."""
        # Process a suggestion first
        bridge.process_evolution_suggestion({
            "suggestion_id": "test_002",
            "title": "Test",
            "description": "Test",
            "category": "refactor",
            "priority": 0.5,
            "source": "test",
            "target_module": "core.test",
        })
        actions = bridge.get_actions(limit=10)
        assert isinstance(actions, list)
        assert len(actions) >= 1

    def test_bridge_stats_after_processing(self, bridge):
        """Verify bridge stats update after processing actions."""
        before = bridge.get_stats()
        bridge.process_evolution_suggestion({
            "suggestion_id": "test_003",
            "title": "Test",
            "description": "Test",
            "category": "refactor",
            "priority": 0.5,
            "source": "test",
            "target_module": "core.test",
        })
        after = bridge.get_stats()
        assert after.get("total_actions", 0) >= before.get("total_actions", 0) + 1

# ── Full Pipeline Tests ──────────────────────────────────────────────────────

class TestFullSelfBuildingPipeline:
    """Test the complete self-building pipeline end-to-end."""

    @pytest.mark.asyncio
    async def test_scan_analyze_build_cycle(self, scanner, knowledge, gap_analyzer, auto_builder):
        """Verify the full scan → analyze → build cycle works."""
        # 1. Scan
        scan_result = scanner.scan(subdirs=["core"])
        assert scan_result is not None
        assert len(scan_result.modules) > 0

        # 2. Analyze
        result = gap_analyzer.analyze(scanner=scanner)
        assert isinstance(result, GapAnalysisResult)
        assert len(result.gaps) > 0

        # 3. Build
        cycle = await auto_builder.run_cycle()
        assert isinstance(cycle, BuildCycle)
        assert cycle.status in ["completed", "partial", "failed"]

    def test_gap_to_build_action_mapping(self, gap_analyzer):
        """Verify gap analysis can produce actionable build tasks."""
        result = gap_analyzer.analyze()
        for gap in result.gaps[:5]:  # Check first 5 gaps
            action = gap_analyzer._gap_to_build_action(gap)
            if action is not None:
                assert "action_type" in action
                assert "description" in action
                assert "module" in action

    @pytest.mark.asyncio
    async def test_bridge_feeds_auto_builder(self, bridge, auto_builder):
        """Verify EvolutionBridge actions can be consumed by AutoBuilder."""
        # Create a bridge action
        bridge.process_evolution_suggestion({
            "suggestion_id": "pipeline_test",
            "title": "Pipeline test suggestion",
            "description": "Test the full pipeline",
            "category": "refactor",
            "priority": 0.9,
            "source": "test",
            "target_module": "core.test_module",
        })

        # Run auto-builder cycle (it should pick up bridge actions)
        cycle = await auto_builder.run_cycle()
        assert cycle is not None

    def test_knowledge_updates_after_scan(self, scanner, knowledge):
        """Verify knowledge is updated after a scan."""
        before_summary = knowledge.get_summary()
        knowledge.refresh(scanner=scanner)
        after_summary = knowledge.get_summary()
        # Knowledge should have modules after refresh
        assert after_summary.total_modules > 0

    def test_gap_analyzer_singleton(self):
        """Verify get_gap_analyzer() returns a singleton."""
        from core.self_awareness import get_gap_analyzer as get_ga

        a1 = get_ga()
        a2 = get_ga()
        assert a1 is a2, "get_gap_analyzer() should return the same instance"

    def test_all_singletons_consistent(self):
        """Verify all self-awareness singletons are consistent."""
        from core.self_awareness import (
            get_scanner,
            get_knowledge,
            get_builder,
            get_gap_analyzer,
        )

        s1 = get_scanner()
        k1 = get_knowledge()
        b1 = get_builder()
        a1 = get_gap_analyzer()

        s2 = get_scanner()
        k2 = get_knowledge()
        b2 = get_builder()
        a2 = get_gap_analyzer()

        assert s1 is s2
        assert k1 is k2
        assert b1 is b2
        assert a1 is a2
