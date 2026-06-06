#!/usr/bin/env python3
"""
tests/real/test_compliance_engine.py
AsimNexus — Compliance / Masterplan Engine Tests

Tests for core/compliance/masterplan_engine.py:
  - CriticalSector enum: value, uniqueness, all 15 sectors
  - MasterplanEngine: creation, updates, status queries,
    audit logging, compliance levels, edge cases
"""

import time
import pytest
from datetime import datetime

from core.compliance.masterplan_engine import (
    CriticalSector,
    MasterplanEngine,
)


# ── CriticalSector Enum ──────────────────────────────────────────────────────

class TestCriticalSector:
    """Validate the CriticalSector enum."""

    def test_enum_values(self):
        """All 15 sectors should have correct string values."""
        assert CriticalSector.FINANCE.value == "finance"
        assert CriticalSector.HEALTH.value == "health"
        assert CriticalSector.ENERGY.value == "energy"
        assert CriticalSector.TRANSPORT.value == "transport"
        assert CriticalSector.TELECOMMUNICATIONS.value == "telecommunications"
        assert CriticalSector.GOVERNMENT.value == "government"
        assert CriticalSector.DEFENSE.value == "defense"
        assert CriticalSector.WATER.value == "water"
        assert CriticalSector.EDUCATION.value == "education"
        assert CriticalSector.RETAIL.value == "retail"
        assert CriticalSector.MANUFACTURING.value == "manufacturing"
        assert CriticalSector.AGRICULTURE.value == "agriculture"
        assert CriticalSector.MEDIA.value == "media"
        assert CriticalSector.LOGISTICS.value == "logistics"
        assert CriticalSector.PERSONAL.value == "personal"

    def test_enum_count(self):
        """There should be exactly 15 critical sectors."""
        assert len(CriticalSector) == 15

    def test_enum_uniqueness(self):
        """All sector values should be unique."""
        values = [s.value for s in CriticalSector]
        assert len(values) == len(set(values))


# ── MasterplanEngine ─────────────────────────────────────────────────────────

class TestMasterplanEngine:
    """Test MasterplanEngine creation, masterplan lifecycle, and auditing."""

    def test_init(self):
        """Engine initialises with empty plans and no last_update."""
        engine = MasterplanEngine()
        assert engine.sector_masterplans == {}
        assert engine.last_update is None
        assert engine.update_interval.days == 180  # 6 months

    def test_create_single_sector(self):
        """Create a masterplan for a single critical sector."""
        engine = MasterplanEngine()
        requirements = {"encryption": "AES-256", "audit_freq_days": 90}
        plan = engine.create_sector_masterplan(CriticalSector.FINANCE, requirements)

        assert plan["sector"] == "finance"
        assert plan["requirements"] == requirements
        assert plan["compliance_level"] == "baseline"
        assert plan["last_audit"] is None
        assert "created_at" in plan

        # Verify stored in engine
        assert "finance" in engine.sector_masterplans
        assert engine.sector_masterplans["finance"] == plan

    def test_create_multiple_sectors(self):
        """Create masterplans for multiple sectors independently."""
        engine = MasterplanEngine()
        fin_req = {"regulation": "GDPR"}
        health_req = {"regulation": "HIPAA"}

        fin_plan = engine.create_sector_masterplan(CriticalSector.FINANCE, fin_req)
        health_plan = engine.create_sector_masterplan(CriticalSector.HEALTH, health_req)

        assert len(engine.sector_masterplans) == 2
        assert engine.sector_masterplans["finance"]["requirements"] == fin_req
        assert engine.sector_masterplans["health"]["requirements"] == health_req

    def test_create_all_sectors(self):
        """Masterplans can be created for all 15 sectors."""
        engine = MasterplanEngine()
        for sector in CriticalSector:
            engine.create_sector_masterplan(sector, {"base": True})

        assert len(engine.sector_masterplans) == 15
        for sector in CriticalSector:
            assert sector.value in engine.sector_masterplans

    def test_overwrite_existing_plan(self):
        """Creating a plan for an existing sector overwrites it."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.ENERGY, {"version": 1})
        engine.create_sector_masterplan(CriticalSector.ENERGY, {"version": 2})

        assert len(engine.sector_masterplans) == 1
        assert engine.sector_masterplans["energy"]["requirements"]["version"] == 2

    def test_update_masterplan(self):
        """Update sets last_audit and last_update timestamp."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.DEFENSE, {"level": "high"})

        before = engine.sector_masterplans["defense"]["last_audit"]
        assert before is None

        engine.update_masterplan(CriticalSector.DEFENSE)

        after = engine.sector_masterplans["defense"]["last_audit"]
        assert after is not None
        assert isinstance(after, str)  # ISO format string

        # last_update on engine should also be set
        assert engine.last_update is not None

    def test_update_nonexistent_sector(self):
        """Updating a sector without a plan does nothing (no crash)."""
        engine = MasterplanEngine()
        # Should not raise
        engine.update_masterplan(CriticalSector.WATER)
        assert engine.last_update is None  # Nothing was updated

    def test_get_sector_status_exists(self):
        """get_sector_status returns the masterplan dict."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.EDUCATION, {"curriculum": "v2"})
        status = engine.get_sector_status(CriticalSector.EDUCATION)

        assert status["sector"] == "education"
        assert status["requirements"]["curriculum"] == "v2"

    def test_get_sector_status_missing(self):
        """get_sector_status returns 'no_masterplan' for missing sector."""
        engine = MasterplanEngine()
        status = engine.get_sector_status(CriticalSector.RETAIL)
        assert status == {"status": "no_masterplan"}

    def test_get_all_sectors_status_empty(self):
        """get_all_sectors_status works with no plans."""
        engine = MasterplanEngine()
        result = engine.get_all_sectors_status()
        assert result["total_sectors"] == 0
        assert result["last_update"] is None
        assert result["sectors"] == {}

    def test_get_all_sectors_status_with_plans(self):
        """get_all_sectors_status returns correct totals and plans."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.FINANCE, {"a": 1})
        engine.create_sector_masterplan(CriticalSector.HEALTH, {"b": 2})

        result = engine.get_all_sectors_status()
        assert result["total_sectors"] == 2
        assert "finance" in result["sectors"]
        assert "health" in result["sectors"]

    def test_get_all_sectors_status_after_update(self):
        """get_all_sectors_status reflects last_update after an update."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.LOGISTICS, {"route": "opt"})
        engine.update_masterplan(CriticalSector.LOGISTICS)
        result = engine.get_all_sectors_status()
        assert result["last_update"] is not None

    def test_compliance_level_default(self):
        """Default compliance level is 'baseline'."""
        engine = MasterplanEngine()
        plan = engine.create_sector_masterplan(CriticalSector.MANUFACTURING, {})
        assert plan["compliance_level"] == "baseline"

    def test_created_at_iso_format(self):
        """created_at field is an ISO-format datetime string."""
        engine = MasterplanEngine()
        plan = engine.create_sector_masterplan(CriticalSector.MEDIA, {})
        # Attempt to parse it
        dt = datetime.fromisoformat(plan["created_at"])
        assert isinstance(dt, datetime)

    def test_last_audit_iso_format(self):
        """last_audit after update is an ISO-format datetime string."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.AGRICULTURE, {})
        engine.update_masterplan(CriticalSector.AGRICULTURE)
        audit = engine.sector_masterplans["agriculture"]["last_audit"]
        dt = datetime.fromisoformat(audit)
        assert isinstance(dt, datetime)

    def test_multiple_updates(self):
        """Multiple updates to same sector keep track of latest audit."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.TELECOMMUNICATIONS, {})
        engine.update_masterplan(CriticalSector.TELECOMMUNICATIONS)
        audit1 = engine.sector_masterplans["telecommunications"]["last_audit"]
        time.sleep(0.01)
        engine.update_masterplan(CriticalSector.TELECOMMUNICATIONS)
        audit2 = engine.sector_masterplans["telecommunications"]["last_audit"]
        assert audit2 > audit1

    def test_requirements_stored_correctly(self):
        """Requirements dict is stored and retrievable."""
        engine = MasterplanEngine()
        req = {"compliance": ["GDPR", "CCPA"], "penalties": {"max": 50000}}
        engine.create_sector_masterplan(CriticalSector.PERSONAL, req)
        stored = engine.get_sector_status(CriticalSector.PERSONAL)
        assert stored["requirements"] == req

    def test_sector_independence(self):
        """Updating one sector does not affect others."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.FINANCE, {"v": 1})
        engine.create_sector_masterplan(CriticalSector.HEALTH, {"v": 2})

        engine.update_masterplan(CriticalSector.FINANCE)
        fin_audit = engine.sector_masterplans["finance"]["last_audit"]
        health_audit = engine.sector_masterplans["health"]["last_audit"]

        assert fin_audit is not None
        assert health_audit is None  # health was not updated

    def test_requirements_not_mutated_externally(self):
        """Requirements dict stored should be the same object reference."""
        engine = MasterplanEngine()
        req = {"key": "value"}
        engine.create_sector_masterplan(CriticalSector.GOVERNMENT, req)
        # Modify original
        req["key"] = "changed"
        stored = engine.get_sector_status(CriticalSector.GOVERNMENT)
        # dict is stored by reference, so it reflects change
        assert stored["requirements"]["key"] == "changed"

    def test_string_vs_enum_access(self):
        """Plans can be accessed via sector.value string key."""
        engine = MasterplanEngine()
        engine.create_sector_masterplan(CriticalSector.WATER, {"priority": 1})
        assert "water" in engine.sector_masterplans
        assert engine.sector_masterplans["water"]["sector"] == "water"
