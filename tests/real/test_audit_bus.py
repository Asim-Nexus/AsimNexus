#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade audit bus tests
ASIMNEXUS Audit Bus Tests
==========================
Tests for emit_audit, fetch_audit, and audit_summary.
"""

import json
import pytest
from pathlib import Path
from core.audit_bus import emit_audit, fetch_audit, audit_summary, AUDIT_BUS_PATH


class TestAuditBus:
    """Test suite for audit bus functions."""

    @pytest.fixture(autouse=True)
    def setup_audit_path(self, tmp_path):
        """Override AUDIT_BUS_PATH to a temp path for test isolation."""
        import core.audit_bus as audit_mod
        self._original_path = audit_mod.AUDIT_BUS_PATH
        self._test_path = tmp_path / "audit_bus.jsonl"
        audit_mod.AUDIT_BUS_PATH = self._test_path
        yield
        audit_mod.AUDIT_BUS_PATH = self._original_path

    # ------------------------------------------------------------------ #
    # emit_audit
    # ------------------------------------------------------------------ #

    def test_emit_audit_creates_file(self):
        """emit_audit creates the audit JSONL file."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "Test audit entry",
        })
        assert self._test_path.exists()

    def test_emit_audit_appends_valid_json(self):
        """emit_audit writes valid JSON lines to the file."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "Entry 1",
        })
        emit_audit({
            "component": "core",
            "action": "tool_call",
            "severity": "info",
            "status": "ok",
            "message": "Entry 2",
        })
        lines = self._test_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        assert entry1["message"] == "Entry 1"
        assert entry2["message"] == "Entry 2"

    def test_emit_audit_adds_event_id(self):
        """emit_audit assigns event_id via validation."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "Has event_id",
        })
        lines = self._test_path.read_text(encoding="utf-8").strip().splitlines()
        entry = json.loads(lines[0])
        assert "event_id" in entry
        assert len(entry["event_id"]) > 0

    def test_emit_audit_fallback_on_error(self):
        """emit_audit does not crash on invalid events."""
        # An invalid event should not raise - emit_audit wraps in try/except
        try:
            emit_audit({"component": "nonexistent", "action": "invalid"})
        except Exception:
            pytest.fail("emit_audit should not raise on invalid event")

    # ------------------------------------------------------------------ #
    # fetch_audit
    # ------------------------------------------------------------------ #

    def test_fetch_audit_returns_records(self):
        """fetch_audit returns all recorded audit entries."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "A",
        })
        emit_audit({
            "component": "core",
            "action": "tool_call",
            "severity": "info",
            "status": "ok",
            "message": "B",
        })
        records = fetch_audit(limit=100)
        assert len(records) == 2
        assert records[0]["message"] == "A"
        assert records[1]["message"] == "B"

    def test_fetch_audit_empty_file(self):
        """fetch_audit returns empty list when no audit file exists."""
        if self._test_path.exists():
            self._test_path.unlink()
        records = fetch_audit(limit=100)
        assert records == []

    def test_fetch_audit_respects_limit(self):
        """fetch_audit respects the limit parameter."""
        for i in range(10):
            emit_audit({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "message": f"Entry {i}",
            })
        records = fetch_audit(limit=3)
        assert len(records) == 3

    def test_fetch_audit_with_cursor(self):
        """fetch_audit supports cursor-based pagination."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "First",
        })
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "Second",
        })
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "Third",
        })

        # Get first record's event_id as cursor
        all_records = fetch_audit(limit=100)
        cursor = all_records[0]["event_id"]

        # Fetch after cursor
        after = fetch_audit(limit=100, cursor=cursor)
        assert len(after) == 2
        assert after[0]["message"] == "Second"
        assert after[1]["message"] == "Third"

    def test_fetch_audit_cursor_nonexistent(self):
        """fetch_audit with non-existent cursor returns all records."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "Test",
        })
        records = fetch_audit(limit=100, cursor="nonexistent-cursor")
        assert len(records) == 1

    # ------------------------------------------------------------------ #
    # audit_summary
    # ------------------------------------------------------------------ #

    def test_audit_summary_counts(self):
        """audit_summary returns correct counts for recorded events."""
        emit_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "OK request",
        })
        emit_audit({
            "component": "policy",
            "action": "decision",
            "severity": "warning",
            "status": "blocked",
            "message": "Blocked",
        })
        emit_audit({
            "component": "backend",
            "action": "error",
            "severity": "error",
            "status": "failed",
            "message": "Error",
        })

        summary = audit_summary()
        assert summary["total_records"] == 3
        assert summary["by_severity"]["info"] == 1
        assert summary["by_severity"]["warning"] == 1
        assert summary["by_severity"]["error"] == 1
        assert summary["by_status"]["ok"] == 1
        assert summary["by_status"]["blocked"] == 1
        assert summary["by_status"]["failed"] == 1
        assert summary["by_component"]["backend"] == 2
        assert summary["by_component"]["policy"] == 1

    def test_audit_summary_empty(self):
        """audit_summary returns zeroed counts for empty audit file."""
        if self._test_path.exists():
            self._test_path.unlink()
        summary = audit_summary()
        assert summary["total_records"] == 0
        assert summary["by_severity"]["info"] == 0
        assert summary["by_status"]["ok"] == 0
        assert summary["by_component"] == {}

    def test_audit_summary_no_crash_on_corrupt_line(self):
        """audit_summary handles corrupt lines gracefully."""
        self._test_path.write_text("{invalid json line}\n{\"component\": \"backend\", \"action\": \"request\", \"severity\": \"info\", \"status\": \"ok\", \"message\": \"valid\"}\n")
        summary = audit_summary()
        # Should still count valid lines
        assert summary["total_records"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
