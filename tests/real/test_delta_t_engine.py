"""
STATUS: REAL — Tests for DeltaT Engine v2
Tests: Gini coefficient, PoS, attenuation, cap enforcement
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.dharma.delta_t_engine import DeltaTEngine, NodeState, PoSReport


class TestDeltaTEngine:
    """Test suite for DeltaT Engine anti-concentration system."""

    def test_register_node(self):
        """Node registration with raw values."""
        engine = DeltaTEngine()
        engine.register_node("node_a", resources=100, tx_rate=10, rep_score=50)
        assert "node_a" in engine.nodes
        assert engine.nodes["node_a"].resources == 100

    def test_calculate_influence_sums_to_one(self):
        """All node influences must sum to 1.0."""
        engine = DeltaTEngine()
        engine.register_node("a", resources=100, tx_rate=10, rep_score=50)
        engine.register_node("b", resources=100, tx_rate=10, rep_score=50)
        influences = [engine.calculate_influence(nid) for nid in engine.nodes]
        assert abs(sum(influences) - 1.0) < 1e-6

    def test_violation_attenuation(self):
        """Node over L_max gets attenuated."""
        engine = DeltaTEngine(L_max=0.07)
        # 10 equal nodes -> fair share = 10%, which exceeds L_max=7%
        for i in range(10):
            engine.register_node(f"node_{i}", resources=100, tx_rate=10, rep_score=50)
        result = engine.check_and_attenuate("node_0")
        # Since fair share is 10% > 7%, it should be violation
        assert result["status"] == "VIOLATION"
        assert result["dharma_veto"] is True
        assert result["attenuation_factor"] < 1.0

    def test_balanced_within_cap(self):
        """Node under L_max stays balanced."""
        engine = DeltaTEngine(L_max=0.07)
        # 20 equal nodes -> fair share = 5%, under 7%
        for i in range(20):
            engine.register_node(f"node_{i}", resources=100, tx_rate=10, rep_score=50)
        result = engine.check_and_attenuate("node_0")
        assert result["status"] == "BALANCED"
        assert result["dharma_veto"] is False

    def test_pos_perfect_equality(self):
        """Equal nodes -> symmetry=1.0, gini=0.0."""
        engine = DeltaTEngine()
        for i in range(20):
            engine.register_node(f"node_{i}", resources=100, tx_rate=10, rep_score=50)
        pos = engine.run_cycle()
        assert pos.symmetry_score == 1.0
        assert pos.gini_coefficient == 0.0
        assert pos.verdict == "BALANCED"

    def test_pos_concentration_detected(self):
        """One big node -> low symmetry, high gini."""
        engine = DeltaTEngine()
        # 9 small nodes + 1 giant
        for i in range(9):
            engine.register_node(f"small_{i}", resources=10, tx_rate=1, rep_score=10)
        engine.register_node("giant", resources=1000, tx_rate=100, rep_score=100)
        pos = engine.run_cycle()
        assert pos.symmetry_score < 0.90
        assert pos.gini_coefficient > 0.0
        assert pos.verdict == "CONCENTRATION_DETECTED"
        assert pos.violations > 0

    def test_persistent_penalty(self):
        """Rep score decreases after violation."""
        engine = DeltaTEngine(L_max=0.07)
        engine.register_node("a", resources=100, tx_rate=10, rep_score=100)
        for i in range(5):
            engine.register_node(f"small_{i}", resources=10, tx_rate=1, rep_score=10)
        before = engine.nodes["a"].rep_score
        engine.check_and_attenuate("a")
        after = engine.nodes["a"].rep_score
        assert after < before

    def test_invalid_weights_raises(self):
        """Alpha+beta+gamma must equal 1.0."""
        with pytest.raises(ValueError):
            DeltaTEngine(alpha=0.5, beta=0.5, gamma=0.5)

    def test_invalid_lmax_raises(self):
        """L_max must be 0.05-0.15."""
        with pytest.raises(ValueError):
            DeltaTEngine(L_max=0.50)

    def test_network_summary_has_all_nodes(self):
        """Summary returns all node data."""
        engine = DeltaTEngine()
        engine.register_node("a", resources=100, tx_rate=10, rep_score=50)
        summary = engine.network_summary()
        assert "nodes" in summary
        assert "a" in summary["nodes"]
        assert summary["nodes"]["a"]["resources"] == 100


class TestPoSReport:
    """Test Proof of Symmetry reports."""

    def test_balanced_verdict(self):
        report = PoSReport(cycle=1, node_count=5, symmetry_score=0.95, gini_coefficient=0.05, violations=0, l_max=0.07)
        assert report.verdict == "BALANCED"

    def test_mild_concentration_verdict(self):
        report = PoSReport(cycle=1, node_count=5, symmetry_score=0.80, gini_coefficient=0.20, violations=1, l_max=0.07)
        assert report.verdict == "MILD_CONCENTRATION"

    def test_concentration_verdict(self):
        report = PoSReport(cycle=1, node_count=5, symmetry_score=0.50, gini_coefficient=0.50, violations=3, l_max=0.07)
        assert report.verdict == "CONCENTRATION_DETECTED"
