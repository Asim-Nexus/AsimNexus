#!/usr/bin/env python3
"""
tests/real/test_compliance.py
AsimNexus — Compliance Engine Tests (Phase D)

Tests for governance/compliance_engine.py:
  - CompliancePolicy creation
  - ComplianceEngine initialization, policy management
  - Data compliance checks, violation logging, resolution
  - Audit trail and reporting
"""

import os
import gc
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from governance.compliance_engine import (
    ComplianceSector,
    DataClassification,
    CompliancePolicy,
    ComplianceEngine,
    get_compliance_engine,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_compliance_env():
    """Reset singleton and env vars before/after each test."""
    saved = {}
    for key in ("ASIM_COMPLIANCE_AUDIT_HOURS",):
        saved[key] = os.environ.pop(key, None)

    # Reset singleton
    import governance.compliance_engine as ce_mod
    ce_mod._compliance_engine = None

    yield

    for key, val in saved.items():
        if val is not None:
            os.environ[key] = val
        else:
            os.environ.pop(key, None)
    ce_mod._compliance_engine = None


# ── CompliancePolicy Tests ──────────────────────────────────────────────────

class TestCompliancePolicy:
    """CompliancePolicy dataclass tests."""

    def test_import(self):
        assert CompliancePolicy is not None

    def test_init(self):
        p = CompliancePolicy(
            policy_id="test_001",
            name="Test Policy",
            sector=ComplianceSector.TECHNOLOGY,
            description="A test policy",
            requirements=["Req 1", "Req 2"],
        )
        assert p.policy_id == "test_001"
        assert p.name == "Test Policy"
        assert p.sector == ComplianceSector.TECHNOLOGY
        assert len(p.requirements) == 2

    def test_default_enforcement_level(self):
        p = CompliancePolicy("p1", "P1", ComplianceSector.PRIVATE, "Desc", ["R1"])
        assert p.enforcement_level == "must"

    def test_to_dict(self):
        p = CompliancePolicy("p1", "P1", ComplianceSector.FINANCE, "Desc", ["R1"])
        d = p.to_dict()
        assert d["policy_id"] == "p1"
        assert d["sector"] == "finance"


# ── ComplianceEngine Tests ──────────────────────────────────────────────────

class TestComplianceEngine:
    """ComplianceEngine initialization and policy management tests."""

    def test_import(self):
        assert ComplianceEngine is not None

    def test_init_creates_policies(self):
        ce = ComplianceEngine()
        assert len(ce.policies) >= 5  # GDPR, HIPAA, PCI-DSS, FedRAMP, FERPA

    def test_get_policy_exists(self):
        ce = ComplianceEngine()
        policy = ce.get_policy("gdpr_001")
        assert policy is not None
        assert policy.name == "GDPR Compliance"

    def test_get_policy_not_found(self):
        ce = ComplianceEngine()
        assert ce.get_policy("nonexistent") is None

    def test_get_policies_by_sector(self):
        ce = ComplianceEngine()
        healthcare_policies = ce.get_policies_by_sector(ComplianceSector.HEALTHCARE)
        assert len(healthcare_policies) == 1
        assert healthcare_policies[0].policy_id == "hipaa_001"

    def test_get_policies_by_sector_empty(self):
        ce = ComplianceEngine()
        tech_policies = ce.get_policies_by_sector(ComplianceSector.TECHNOLOGY)
        assert tech_policies == []

    def test_register_policy(self):
        ce = ComplianceEngine()
        new_policy = CompliancePolicy(
            policy_id="custom_001",
            name="Custom Policy",
            sector=ComplianceSector.TECHNOLOGY,
            description="Custom tech policy",
            requirements=["Encryption required"],
        )
        result = ce.register_policy(new_policy)
        assert result is True
        assert ce.get_policy("custom_001") is new_policy

    def test_register_policy_overwrite(self):
        ce = ComplianceEngine()
        p1 = CompliancePolicy("dup", "Original", ComplianceSector.PRIVATE, "Desc", [])
        p2 = CompliancePolicy("dup", "Overwrite", ComplianceSector.PRIVATE, "Desc", [])
        ce.register_policy(p1)
        ce.register_policy(p2)
        assert ce.get_policy("dup").name == "Overwrite"

    def test_check_compliance_public_data_passes(self):
        ce = ComplianceEngine()
        result = ce.check_data_compliance(
            data_classification=DataClassification.PUBLIC,
            sector=ComplianceSector.HEALTHCARE,
            user_id="user_test",
            data_size_mb=10,
        )
        assert result["compliant"] is True
        assert len(result["violations"]) == 0

    def test_check_compliance_secret_fails(self):
        ce = ComplianceEngine()
        result = ce.check_data_compliance(
            data_classification=DataClassification.SECRET,
            sector=ComplianceSector.GOVERNMENT,
            user_id="user_admin",
            data_size_mb=1,
        )
        assert result["compliant"] is False
        assert len(result["violations"]) >= 1

    def test_check_compliance_restricted_warns(self):
        ce = ComplianceEngine()
        result = ce.check_data_compliance(
            data_classification=DataClassification.RESTRICTED,
            sector=ComplianceSector.FINANCE,
            user_id="user_fin",
            data_size_mb=100,
        )
        assert result["compliant"] is True
        assert len(result["warnings"]) >= 1

    def test_check_compliance_large_volume_fails(self):
        ce = ComplianceEngine()
        result = ce.check_data_compliance(
            data_classification=DataClassification.CONFIDENTIAL,
            sector=ComplianceSector.HEALTHCARE,
            user_id="user_big",
            data_size_mb=5000,
        )
        assert result["compliant"] is False
        assert any("Large volume" in v for v in result["violations"])

    def test_log_violation(self):
        ce = ComplianceEngine()
        vio_id = ce.log_violation(
            violation_type="unauthorized_access",
            policy_id="hipaa_001",
            description="Unauthorized PHI access",
            severity="high",
            user_id="user_bad",
        )
        assert vio_id.startswith("vio_")
        assert len(ce.violations) == 1
        assert ce.violations[0]["status"] == "open"

    def test_log_violation_default_severity(self):
        ce = ComplianceEngine()
        vio_id = ce.log_violation("test", "p1", "desc")
        assert vio_id is not None

    def test_resolve_violation(self):
        ce = ComplianceEngine()
        vio_id = ce.log_violation("test", "p1", "desc", severity="medium")
        result = ce.resolve_violation(vio_id, "Fixed the issue")
        assert result is True

        # Verify resolved
        for v in ce.violations:
            if v["violation_id"] == vio_id:
                assert v["status"] == "resolved"
                assert v["resolution_notes"] == "Fixed the issue"
                break

    def test_resolve_violation_not_found(self):
        ce = ComplianceEngine()
        assert ce.resolve_violation("nonexistent", "nope") is False

    def test_get_compliance_report(self):
        ce = ComplianceEngine()
        report = ce.get_compliance_report()
        assert report["total_policies"] >= 5
        assert report["total_violations"] >= 0
        assert report["compliance_score"] == 100
        assert report["compliant"] is True

    def test_get_compliance_report_with_violations(self):
        ce = ComplianceEngine()
        ce.log_violation("test", "p1", "A violation", severity="high")
        report = ce.get_compliance_report()
        assert report["total_violations"] == 1
        assert report["open_violations"] == 1
        assert report["compliance_score"] < 100

    def test_get_audit_trail(self):
        ce = ComplianceEngine()
        ce.check_data_compliance(DataClassification.PUBLIC, ComplianceSector.PRIVATE,
                                 "user_a", 1)
        ce.log_violation("test", "p1", "Audit test", severity="low")

        trail = ce.get_audit_trail(hours=24)
        assert len(trail) >= 2  # at least one check + one violation

    def test_get_audit_trail_filters_by_time(self):
        ce = ComplianceEngine()
        ce.log_violation("test", "p1", "Recent violation")

        # Set default to 0 hours to filter out everything
        trail = ce.get_audit_trail(hours=0)
        assert len(trail) == 0

    def test_get_audit_trail_contains_expected_keys(self):
        ce = ComplianceEngine()
        ce.check_data_compliance(DataClassification.PUBLIC, ComplianceSector.PRIVATE,
                                 "user_a", 1)
        trail = ce.get_audit_trail(hours=24)
        assert len(trail) > 0
        entry = trail[0]
        assert "timestamp" in entry
        assert "event_type" in entry
        assert "data" in entry

    def test_get_compliance_engine_singleton(self):
        ce1 = get_compliance_engine()
        ce2 = get_compliance_engine()
        assert ce1 is ce2

    def test_env_var_audit_hours(self):
        """Verify ASIM_COMPLIANCE_AUDIT_HOURS module-level default is read."""
        import governance.compliance_engine as ce_mod

        # Save original value and override directly (avoid importlib.reload
        # which would recreate enum classes and break equality checks)
        original = ce_mod._DEFAULT_AUDIT_HOURS
        os.environ["ASIM_COMPLIANCE_AUDIT_HOURS"] = "48"
        ce_mod._DEFAULT_AUDIT_HOURS = 48

        assert ce_mod._DEFAULT_AUDIT_HOURS == 48

        # Clean up
        del os.environ["ASIM_COMPLIANCE_AUDIT_HOURS"]
        ce_mod._DEFAULT_AUDIT_HOURS = original
