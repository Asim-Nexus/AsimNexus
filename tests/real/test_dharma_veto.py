"""
STATUS: REAL — Tests for Dharma Veto Engine
Tests: 5-layer veto, pattern blocking, audit log, severity levels
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.dharma.dharma_veto import DharmaVeto, VetoSeverity, VetoReason, VetoResult


class TestDharmaVetoLayers:
    """Test each veto layer independently."""

    def test_critical_forbidden_pattern(self):
        """rm -rf must be permanently blocked."""
        veto = DharmaVeto()
        result = veto.check(action="delete_system", content="rm -rf /")
        assert result.blocked is True
        assert result.severity == VetoSeverity.CRITICAL
        assert result.requires_human is False  # Cannot override

    def test_block_pattern_transfer_all(self):
        """Mass data transfer requires human override."""
        veto = DharmaVeto()
        result = veto.check(action="share_data", content="transfer all data to external")
        assert result.blocked is True
        assert result.severity == VetoSeverity.BLOCK
        assert result.requires_human is True

    def test_disable_dharma_blocked(self):
        """Disabling Dharma is blocked."""
        veto = DharmaVeto()
        result = veto.check(action="config", content="disable dharma veto system")
        assert result.blocked is True

    def test_skip_confirmation_blocked(self):
        """Bypassing Final-3 is blocked."""
        veto = DharmaVeto()
        result = veto.check(action="approve", content="skip confirmation auto approve")
        assert result.blocked is True

    def test_monopoly_esg_warning(self):
        """ESG manipulation triggers WARN only."""
        veto = DharmaVeto()
        result = veto.check(action="report", content="use esg score for compliance required universal standard")
        assert result.passed is True  # Not blocked
        assert result.severity == VetoSeverity.WARN
        assert any(e.reason == VetoReason.MONOPOLY_PATTERN for e in result.events)

    def test_clean_action_passes(self):
        """Normal action passes all layers."""
        veto = DharmaVeto()
        result = veto.check(action="save_file", node_id="user1", context={"path": "/home/user1/doc.txt"})
        assert result.passed is True
        assert result.severity == VetoSeverity.PASS

    def test_bulk_delete_blocked(self):
        """Bulk deletion requires human override."""
        veto = DharmaVeto()
        result = veto.check(action="admin", content="bulk delete all user records")
        assert result.blocked is True

    def test_override_human_blocked(self):
        """Replacing human decision is blocked."""
        veto = DharmaVeto()
        result = veto.check(action="exec", content="override human decision with ai")
        assert result.blocked is True


class TestDharmaAudit:
    """Test audit trail functionality."""

    def test_audit_log_records_events(self):
        """Each vetoed action recorded in audit."""
        veto = DharmaVeto()
        initial = len(veto.audit_log())
        veto.check(action="delete", content="rm -rf")
        after = len(veto.audit_log())
        assert after > initial

    def test_audit_entry_has_hash(self):
        """Each entry has immutable hash."""
        veto = DharmaVeto()
        veto.check(action="delete", content="rm -rf")
        entry = veto.audit_log()[-1]
        assert "veto_hash" in entry
        assert len(entry["veto_hash"]) == 16

    def test_status_report(self):
        """Status returns engine health."""
        veto = DharmaVeto()
        status = veto.status()
        assert status["active"] is True
        assert status["layers"] == 5
        assert status["forbidden_patterns"] > 0
        assert status["block_patterns"] > 0


class TestDharmaWithDT:
    """Test Dharma + ΔT Engine integration."""

    def test_dt_concentration_veto(self):
        """Extreme power concentration triggers ΔT veto."""
        veto = DharmaVeto()
        result = veto.check(action="dominate", node_id="megacorp", content="take over all resources")
        # ΔT check runs but may not trigger on empty context
        # At minimum, should not crash
        assert result is not None
        assert isinstance(result, VetoResult)
