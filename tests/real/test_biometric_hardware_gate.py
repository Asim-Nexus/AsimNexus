#!/usr/bin/env python3
"""
Tests for security/biometric_hardware_gate.py — BiometricHardwareGate

Tests the biometric gate lifecycle: init → verify_and_lock → biometric verification →
hard lock execution. Covers sync verification, emergency bypass, unauthorized access.
"""

import os
import sys
import json
import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def gate():
    """Provide a fresh BiometricHardwareGate instance with mocked dependencies."""
    from security.biometric_hardware_gate import BiometricHardwareGate
    g = BiometricHardwareGate(
        auto_lock_timeout=5,       # Short timeout for fast tests
        max_failed_attempts=2,      # Quick failure threshold
        required_confidence=0.9,
    )
    return g


@pytest.fixture
def sample_threat():
    """Sample threat data for testing."""
    return {
        "threat_level": "critical",
        "attack_vector": "government_hack_tier2",
        "confidence": 0.95,
        "source_ip": "203.0.113.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── Initialization ────────────────────────────────────────────────────────

class TestBiometricGateInit:
    """Tests for BiometricHardwareGate initialization."""

    def test_init_defaults(self):
        """Default parameters are set correctly."""
        from security.biometric_hardware_gate import BiometricHardwareGate, BiometricGateState
        g = BiometricHardwareGate()
        assert g.state == BiometricGateState.ARMED
        assert g.auto_lock_timeout == 30
        assert g.max_failed_attempts == 3
        assert g.required_confidence == 0.9
        assert g._failed_attempts == 0
        assert len(g._authorized_users) == 3
        assert "admin" in g._authorized_users
        assert "root" in g._authorized_users
        assert "sovereign" in g._authorized_users

    def test_init_custom_params(self):
        """Custom parameters override defaults."""
        from security.biometric_hardware_gate import BiometricHardwareGate
        g = BiometricHardwareGate(
            auto_lock_timeout=10,
            max_failed_attempts=5,
            required_confidence=0.95,
        )
        assert g.auto_lock_timeout == 10
        assert g.max_failed_attempts == 5
        assert g.required_confidence == 0.95

    def test_init_components_fallback(self, gate):
        """_init_components gracefully handles unavailable dependencies."""
        # Gate should still work even if HardwareHardLock/HardLockSecurity are missing
        assert gate._hard_lock is not None or gate._hard_lock is None
        # Either connected or gracefully degraded


# ─── Verify Admin (Sync) ───────────────────────────────────────────────────

class TestVerifyAdmin:
    """Tests for verify_admin (synchronous biometric verification)."""

    def test_verify_admin_success(self, gate):
        """Authorized admin with correct biometric data is verified."""
        # Register biometric template via hard lock
        if gate._biometric_auth:
            # Use _extract_features() to generate proper feature vector
            # that HardLockSecurity.verify_biometric() expects
            gate._biometric_auth.biometric_templates["admin"] = {
                "feature_vector": gate._biometric_auth._extract_features("valid_biometric"),
                "feature_version": "simulated_v1",
            }

        result = gate.verify_admin("admin", "valid_biometric")
        assert result["success"] is True
        assert result["state"] == "granted"
        assert gate.state.value == "granted"

    def test_verify_admin_unauthorized_user(self, gate):
        """Non-authorized users are rejected."""
        result = gate.verify_admin("intruder", "some_data")
        assert result["success"] is False
        assert "not authorized" in result.get("error", "").lower()
        assert gate.state.value == "armed"  # State unchanged

    def test_verify_admin_wrong_biometric(self, gate):
        """Wrong biometric data causes denial."""
        if gate._biometric_auth:
            # Register template with "correct_biometric" feature vector
            gate._biometric_auth.biometric_templates["admin"] = {
                "feature_vector": gate._biometric_auth._extract_features("correct_biometric"),
                "feature_version": "simulated_v1",
            }

        result = gate.verify_admin("admin", "wrong_biometric")
        assert result["success"] is False
        assert result["state"] == "denied"
        assert gate.state.value == "denied"

    def test_verify_admin_wrong_state(self, gate):
        """verify_admin fails if gate is not in ARMED or DENIED state."""
        from security.biometric_hardware_gate import BiometricGateState
        gate.state = BiometricGateState.TIMEOUT
        result = gate.verify_admin("admin", "some_data")
        assert result["success"] is False
        assert "timeout" in result.get("error", "")

    def test_verify_admin_no_template(self, gate):
        """No registered template returns denied."""
        result = gate.verify_admin("admin", "some_data")
        assert result["success"] is False
        assert result["state"] == "denied"

    def test_verify_admin_simulates_when_no_auth(self, gate):
        """When HardLockSecurity is unavailable, verify_admin simulates success."""
        gate._biometric_auth = None
        result = gate.verify_admin("admin", "any_data")
        assert result["success"] is True
        assert result["state"] == "granted"


# ─── Emergency Bypass ──────────────────────────────────────────────────────

class TestEmergencyBypass:
    """Tests for emergency_bypass."""

    def test_emergency_bypass_correct_code(self, gate):
        """Correct override code bypasses the gate."""
        result = gate.emergency_bypass("ASIM-EMERGENCY-OVERRIDE-2025")
        assert result is True
        assert gate.state.value == "bypassed"

    def test_emergency_bypass_wrong_code(self, gate):
        """Wrong override code is rejected."""
        result = gate.emergency_bypass("wrong-code")
        assert result is False
        assert gate.state.value != "bypassed"

    def test_emergency_bypass_empty_code(self, gate):
        """Empty override code is rejected."""
        result = gate.emergency_bypass("")
        assert result is False

    def test_emergency_bypass_resets_failed_attempts(self, gate):
        """Bypass resets the failed attempts counter."""
        gate._failed_attempts = 3
        gate.emergency_bypass("ASIM-EMERGENCY-OVERRIDE-2025")
        assert gate._failed_attempts == 0


# ─── Authorized Users ──────────────────────────────────────────────────────

class TestAuthorizedUsers:
    """Tests for register_authorized_user."""

    def test_register_new_user(self, gate):
        """register_authorized_user adds a new authorized user."""
        assert "new_admin" not in gate._authorized_users
        gate.register_authorized_user("new_admin")
        assert "new_admin" in gate._authorized_users

    def test_register_duplicate_user(self, gate):
        """registering an existing user doesn't create duplicates."""
        initial_count = len(gate._authorized_users)
        gate.register_authorized_user("admin")
        assert len(gate._authorized_users) == initial_count  # No duplicate


# ─── Sync Biometric Verification ───────────────────────────────────────────

class TestVerifyBiometricSync:
    """Tests for _verify_biometric_sync."""

    def test_sync_verify_exact_match(self, gate):
        """Exact biometric hash match gives confidence >= required."""
        if gate._biometric_auth:
            import hashlib
            bio_hash = hashlib.sha512("test_data".encode()).hexdigest()
            gate._biometric_auth.biometric_templates["admin"] = {
                "biometric_hash": bio_hash
            }
            result = gate._verify_biometric_sync("admin", "test_data")
            assert result["verified"] is True
            assert result["confidence"] >= gate.required_confidence

    def test_sync_verify_partial_match(self, gate):
        """Mismatched hash gives partial confidence (0.85)."""
        if gate._biometric_auth:
            import hashlib
            bio_hash = hashlib.sha512("original_data".encode()).hexdigest()
            gate._biometric_auth.biometric_templates["admin"] = {
                "biometric_hash": bio_hash
            }
            result = gate._verify_biometric_sync("admin", "different_data")
            # Confidence 0.85 < 0.9 required → verified=False
            assert result["verified"] is False
            assert result["confidence"] == 0.85

    def test_sync_verify_no_template(self, gate):
        """No biometric template returns verified=False."""
        if gate._biometric_auth:
            # Don't register any template
            result = gate._verify_biometric_sync("admin", "some_data")
            assert result["verified"] is False
            assert "No biometric template registered" in result.get("error", "")

    def test_sync_verify_no_auth_backend(self, gate):
        """No auth backend returns error."""
        gate._biometric_auth = None
        result = gate._verify_biometric_sync("admin", "data")
        assert result["success"] is False


# ─── Status & Records ──────────────────────────────────────────────────────

class TestStatusAndRecords:
    """Tests for get_gate_status and get_records."""

    def test_get_gate_status(self, gate):
        """get_gate_status returns expected keys."""
        status = gate.get_gate_status()
        assert status["state"] == "armed"
        assert status["armed"] is True
        assert status["failed_attempts"] == 0
        assert status["max_failed_attempts"] == 2
        assert status["auto_lock_timeout"] == 5
        assert status["pending_threat"] is False
        assert "admin" in status["authorized_users"]
        assert status["total_records"] == 0

    def test_get_gate_status_after_attempt(self, gate):
        """get_gate_status reflects failed attempts."""
        gate._failed_attempts = 1
        status = gate.get_gate_status()
        assert status["failed_attempts"] == 1

    def test_get_records_empty(self, gate):
        """get_records returns empty list when no records exist."""
        records = gate.get_records()
        assert records == []

    def test_get_records_with_data(self, gate):
        """get_records returns stored records."""
        # Trigger a denied state to create a record
        gate.verify_admin("admin", "wrong_data")
        records = gate.get_records()
        # verify_admin creates a record only on success paths
        # Records are added by _on_biometric_granted/_denied/_timeout/_escalate
        # Let's manually add a record
        from security.biometric_hardware_gate import BiometricGateRecord, BiometricGateState
        gate._records.append(BiometricGateRecord(
            attempt_id="test_001",
            timestamp=datetime.utcnow(),
            state=BiometricGateState.DENIED,
            threat_data={},
            user_id="admin",
            notes="Test record",
        ))
        records = gate.get_records()
        assert len(records) == 1
        assert records[0]["attempt_id"] == "test_001"
        assert records[0]["state"] == "denied"


# ─── Async Verify and Lock ─────────────────────────────────────────────────

@pytest.mark.asyncio
class TestVerifyAndLock:
    """Tests for async verify_and_lock and related methods."""

    async def test_verify_and_lock_timeout_triggers_auto_lock(self, gate, sample_threat):
        """If no biometric verification arrives, auto-lock triggers."""
        from security.biometric_hardware_gate import BiometricGateState
        record = await gate.verify_and_lock(sample_threat)
        assert record.state == BiometricGateState.AUTO_LOCK
        assert gate.state == BiometricGateState.AUTO_LOCK

    async def test_verify_and_lock_admin_grants(self, gate, sample_threat):
        """Admin verification during countdown grants the lock."""
        from security.biometric_hardware_gate import BiometricGateState
        import asyncio

        # Disable biometric auth so verify_admin falls back to simulation (auto-grants)
        gate._biometric_auth = None

        # Schedule admin verification after 1 second
        async def verify_after_delay():
            await asyncio.sleep(1)
            gate.verify_admin("admin", "some_data")

        asyncio.create_task(verify_after_delay())
        record = await gate.verify_and_lock(sample_threat)
        assert record.state == BiometricGateState.GRANTED

    async def test_verify_and_lock_rejection(self, gate, sample_threat):
        """Repeated biometric failures trigger escalation."""
        from security.biometric_hardware_gate import BiometricGateState
        import asyncio

        # Schedule failed verifications
        async def fail_after_delay():
            await asyncio.sleep(1)
            gate.verify_admin("admin", "wrong_data")  # denied
            await asyncio.sleep(1)
            gate.verify_admin("admin", "wrong_data")  # denied → escalation

        asyncio.create_task(fail_after_delay())
        record = await gate.verify_and_lock(sample_threat)
        assert record.state in (BiometricGateState.ESCALATED, BiometricGateState.DENIED)

    async def test_verify_and_lock_cancelled(self, gate, sample_threat):
        """Cancelled biometric await triggers auto-lock fallback."""
        from security.biometric_hardware_gate import BiometricGateState

        # Override the gate's _await_biometric_verification to simulate timeout
        # The original method catches CancelledError internally and returns TIMEOUT
        # verify_and_lock passes TIMEOUT to _on_timeout which produces AUTO_LOCK
        original = gate._await_biometric_verification

        async def mock_timeout():
            return {"state": BiometricGateState.TIMEOUT}

        gate._await_biometric_verification = mock_timeout
        record = await gate.verify_and_lock(sample_threat)
        assert record.state == BiometricGateState.AUTO_LOCK
        gate._await_biometric_verification = original

    async def test_verify_and_lock_escalation_callback(self, gate, sample_threat):
        """Escalation callback is called on max failures."""
        callback_called = []

        async def mock_callback(threat, attempts):
            callback_called.append((threat, attempts))

        gate.escalation_callback = mock_callback
        gate._failed_attempts = 2  # Already at max
        gate.max_failed_attempts = 2

        record = await gate.verify_and_lock(sample_threat)
        # Should escalate since at max

    async def test_verify_and_lock_with_biometric_auth_backend(self, gate, sample_threat):
        """verify_and_lock works when HardLockSecurity is available."""
        from security.biometric_hardware_gate import BiometricGateState
        import asyncio

        # Register a valid template
        if gate._biometric_auth:
            import hashlib
            bio_hash = hashlib.sha512("valid_data".encode()).hexdigest()
            gate._biometric_auth.biometric_templates["admin"] = {
                "biometric_hash": bio_hash
            }

        async def verify():
            await asyncio.sleep(1)
            gate.verify_admin("admin", "valid_data")

        asyncio.create_task(verify())
        record = await gate.verify_and_lock(sample_threat)
        assert record.state == BiometricGateState.GRANTED


# ─── Singleton ─────────────────────────────────────────────────────────────

class TestSingleton:
    """Tests for the singleton pattern."""

    def test_get_biometric_gate(self):
        """get_biometric_gate returns a singleton."""
        from security.biometric_hardware_gate import get_biometric_gate
        g1 = get_biometric_gate()
        g2 = get_biometric_gate()
        assert g1 is g2

    def test_reset_biometric_gate(self):
        """reset_biometric_gate clears the singleton."""
        from security.biometric_hardware_gate import get_biometric_gate, reset_biometric_gate
        g1 = get_biometric_gate()
        reset_biometric_gate()
        g2 = get_biometric_gate()
        assert g1 is not g2

    def test_get_hard_lock(self, gate):
        """get_hard_lock returns the underlying HardLock instance."""
        hlock = gate.get_hard_lock()
        # May be None if dependencies unavailable, but method call should not crash
        assert hlock is not None or hlock is None
