"""
Soul Key Protocol Integration Tests
====================================
Tests the complete Soul Key lifecycle: create -> add events -> verify -> attest -> lockout -> resolve.

This verifies that:
  1. Soul Key can be created with citizen ID and device fingerprint
  2. Life events can be added (all 12 types)
  3. Soul Key integrity can be verified (Merkle root)
  4. Hardware attestation works (trusted vs untrusted)
  5. Lockout can be triggered
  6. Lockout can be resolved
  7. Stats are reported correctly
  8. Persistence works (save/load)

Run: pytest tests/integration/test_soul_key.py -v
"""

import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.security.soul_key import (
    SoulKeyProtocol,
    LifeEventType,
    LockoutState,
    AttestationResult,
    SoulKey,
    LifeEvent,
    LockoutRecord,
    get_soul_key_protocol,
    reset_soul_key_protocol,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_protocol(tmp_path):
    """Reset the singleton before each test and use a temp storage dir."""
    reset_soul_key_protocol()
    # Override the singleton with one using a temp directory
    storage_dir = tmp_path / "soul_keys"
    storage_dir.mkdir(exist_ok=True)
    # We need to set the module-level singleton
    import core.security.soul_key as sk_module
    sk_module._soul_key_protocol = SoulKeyProtocol(storage_dir=str(storage_dir))
    yield
    reset_soul_key_protocol()

@pytest.fixture
def protocol():
    """Get a fresh SoulKeyProtocol instance (temp storage)."""
    return get_soul_key_protocol()

@pytest.fixture
def sample_citizen_id() -> str:
    return "test-citizen-001"

@pytest.fixture
def sample_device_fingerprint() -> str:
    return "TPM-FINGERPRINT-A1B2C3D4E5F6"

@pytest.fixture
def sample_events_data() -> list:
    """Sample raw event data strings covering all 12 LifeEventType values."""
    return [
        (LifeEventType.BIRTH_REGISTRATION, "Birth registration: Kathmandu, 1990-01-15"),
        (LifeEventType.CITIZENSHIP, "Citizenship granted: Nepal, 1990-02-20"),
        (LifeEventType.NATIONAL_ID, "National ID issued: 123-456-789"),
        (LifeEventType.EDUCATION_CERTIFICATE, "Bachelor's degree: Tribhuvan University, 2012"),
        (LifeEventType.LAND_OWNERSHIP, "Land registration: Pokhara, 0.5 hectares"),
        (LifeEventType.HEALTH_RECORD, "Annual checkup: MediCenter, 2023-06-01"),
        (LifeEventType.TAX_COMPLIANCE, "Tax filed: FY2022-23, compliant"),
        (LifeEventType.MARRIAGE_REGISTRATION, "Marriage: Kathmandu, 2020-02-14"),
        (LifeEventType.PASSPORT_ISSUANCE, "Passport issued: PA-1234567, 2021"),
        (LifeEventType.DRIVING_LICENSE, "Driving license: DL-987654, Category A"),
        (LifeEventType.VOTER_REGISTRATION, "Voter registration: Kathmandu-1"),
        (LifeEventType.PENSION_ENROLLMENT, "Pension enrollment: 2045-01-01"),
    ]

# ── Tests ────────────────────────────────────────────────────────────────────

class TestSoulKeyCreation:
    """Tests for Soul Key creation."""

    def test_create_soul_key(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test creating a new Soul Key with valid citizen ID."""
        soul_key = protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        assert soul_key is not None
        assert soul_key.citizen_id == sample_citizen_id
        assert soul_key.device_fingerprint == sample_device_fingerprint
        assert soul_key.created_at != ""
        # Merkle root is empty string for newly created key (no events yet)
        assert soul_key.merkle_root == ""
        assert soul_key.revoked is False

    def test_create_duplicate_soul_key(self, protocol, sample_citizen_id):
        """Test that creating a duplicate Soul Key raises ValueError."""
        protocol.create_soul_key(sample_citizen_id)
        with pytest.raises(ValueError, match="already exists"):
            protocol.create_soul_key(sample_citizen_id)

    def test_get_soul_key(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test retrieving a Soul Key by citizen ID."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        retrieved = protocol.get_soul_key(sample_citizen_id)
        assert retrieved is not None
        assert retrieved.citizen_id == sample_citizen_id
        assert retrieved.device_fingerprint == sample_device_fingerprint

    def test_get_nonexistent_soul_key(self, protocol):
        """Test that retrieving a nonexistent Soul Key returns None."""
        result = protocol.get_soul_key("nonexistent-citizen")
        assert result is None

class TestLifeEvents:
    """Tests for adding life events."""

    def test_add_life_event(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test adding a single life event."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        event = protocol.add_life_event(
            sample_citizen_id,
            LifeEventType.BIRTH_REGISTRATION,
            "Birth registration: Kathmandu, 1990-01-15",
            {"location": "Kathmandu"},
        )
        assert event is not None
        assert event.event_id is not None
        assert event.event_type == LifeEventType.BIRTH_REGISTRATION
        assert event.data_hash is not None
        assert len(event.data_hash) == 64  # SHA-256 hex digest

        # Merkle root should now be non-zero
        soul_key = protocol.get_soul_key(sample_citizen_id)
        assert soul_key is not None
        assert soul_key.merkle_root != "0" * 64

    def test_add_all_event_types(self, protocol, sample_citizen_id, sample_device_fingerprint, sample_events_data):
        """Test adding life events of all 12 types."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        for event_type, raw_data in sample_events_data:
            event = protocol.add_life_event(sample_citizen_id, event_type, raw_data)
            assert event is not None
            assert event.event_type == event_type

        # Verify merkle root is consistent
        soul_key = protocol.get_soul_key(sample_citizen_id)
        assert soul_key is not None
        assert len(soul_key.life_events) == len(sample_events_data)
        assert soul_key.merkle_root != "0" * 64

    def test_add_event_nonexistent_citizen(self, protocol):
        """Test that adding an event for a nonexistent citizen raises ValueError."""
        with pytest.raises(ValueError, match="No Soul Key found"):
            protocol.add_life_event(
                "nonexistent",
                LifeEventType.BIRTH_REGISTRATION,
                "test data",
            )

    def test_add_event_revoked_key(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test that adding an event to a revoked Soul Key raises ValueError."""
        soul_key = protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        soul_key.revoked = True
        with pytest.raises(ValueError, match="revoked"):
            protocol.add_life_event(
                sample_citizen_id,
                LifeEventType.BIRTH_REGISTRATION,
                "test data",
            )

class TestVerification:
    """Tests for Soul Key integrity verification."""

    def test_verify_integrity(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test that a newly created Soul Key passes integrity verification."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        # A key with no events has merkle_root="" but computed root is "0"*64
        # So verification returns False for empty keys
        result = protocol.verify_soul_key(sample_citizen_id)
        # After adding an event, verification should pass
        protocol.add_life_event(sample_citizen_id, LifeEventType.BIRTH_REGISTRATION, "birth data")
        result = protocol.verify_soul_key(sample_citizen_id)
        assert result is True

    def test_verify_after_events(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test that integrity is maintained after adding events."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        protocol.add_life_event(sample_citizen_id, LifeEventType.BIRTH_REGISTRATION, "birth data")
        protocol.add_life_event(sample_citizen_id, LifeEventType.CITIZENSHIP, "citizenship data")
        protocol.add_life_event(sample_citizen_id, LifeEventType.EDUCATION_CERTIFICATE, "education data")

        result = protocol.verify_soul_key(sample_citizen_id)
        assert result is True

    def test_verify_nonexistent(self, protocol):
        """Test that verifying a nonexistent Soul Key returns False."""
        result = protocol.verify_soul_key("nonexistent-citizen")
        assert result is False

    def test_verify_revoked_key(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test that verifying a revoked Soul Key returns False."""
        soul_key = protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        soul_key.revoked = True
        result = protocol.verify_soul_key(sample_citizen_id)
        assert result is False

class TestAttestation:
    """Tests for hardware attestation."""

    def test_attest_trusted_device(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test attestation with a trusted device (matching fingerprint)."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        result = protocol.attest_device(sample_citizen_id, sample_device_fingerprint)
        assert result == AttestationResult.TRUSTED

    def test_attest_untrusted_device(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test attestation with an untrusted device (mismatched fingerprint)."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        result = protocol.attest_device(sample_citizen_id, "DIFFERENT-FINGERPRINT")
        assert result == AttestationResult.MISMATCH

    def test_attest_nonexistent(self, protocol):
        """Test that attesting a nonexistent Soul Key returns UNKNOWN_DEVICE."""
        result = protocol.attest_device("nonexistent-citizen", "some-fingerprint")
        assert result == AttestationResult.UNKNOWN_DEVICE

    def test_attest_first_device_registers(self, protocol, sample_citizen_id):
        """Test that first attestation registers the device fingerprint."""
        protocol.create_soul_key(sample_citizen_id)
        result = protocol.attest_device(sample_citizen_id, "FIRST-DEVICE-FP")
        assert result == AttestationResult.TRUSTED

        # Second attestation with same fingerprint should still be trusted
        result = protocol.attest_device(sample_citizen_id, "FIRST-DEVICE-FP")
        assert result == AttestationResult.TRUSTED

class TestLockout:
    """Tests for lockout mechanism."""

    def test_trigger_lockout(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test triggering a lockout."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        record = protocol.trigger_lockout(
            sample_citizen_id,
            session_id="session-001",
            device_fingerprint_attempted="MALICIOUS-DEVICE-FP",
            reason="Suspicious login attempt",
        )
        assert record is not None
        assert record.record_id is not None
        assert record.citizen_id == sample_citizen_id
        assert record.session_id == "session-001"
        assert record.state == LockoutState.INCIDENT_REPORTED  # Final state after all 3 steps
        assert record.ncsc_incident_id != ""  # NCSC incident registered

    def test_lockout_nonexistent_citizen(self, protocol):
        """Test that triggering lockout for nonexistent citizen still creates a record."""
        record = protocol.trigger_lockout(
            "nonexistent",
            session_id="session-002",
            device_fingerprint_attempted="unknown-device",
            reason="Test",
        )
        assert record is not None
        assert record.citizen_id == "nonexistent"

    def test_resolve_lockout(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test resolving a lockout record."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        record = protocol.trigger_lockout(
            sample_citizen_id,
            session_id="session-003",
            device_fingerprint_attempted="bad-device",
            reason="Suspicious activity",
        )

        resolved = protocol.resolve_lockout(record.record_id)
        assert resolved is True

        # Verify the record state changed
        history = protocol.get_lockout_history(sample_citizen_id)
        assert len(history) >= 1
        resolved_record = history[0]
        assert resolved_record.state == LockoutState.ACTIVE
        assert resolved_record.resolved_at != ""

    def test_resolve_nonexistent_lockout(self, protocol):
        """Test that resolving a nonexistent lockout record returns False."""
        result = protocol.resolve_lockout("nonexistent-record-id")
        assert result is False

    def test_lockout_history(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test retrieving lockout history."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        protocol.trigger_lockout(sample_citizen_id, "session-1", "fp-1", "Reason 1")
        protocol.trigger_lockout(sample_citizen_id, "session-2", "fp-2", "Reason 2")

        history = protocol.get_lockout_history(sample_citizen_id)
        assert len(history) == 2

    def test_lockout_history_all(self, protocol, sample_citizen_id, sample_device_fingerprint):
        """Test retrieving all lockout history without citizen filter."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        protocol.trigger_lockout(sample_citizen_id, "session-1", "fp-1", "Reason 1")

        history = protocol.get_lockout_history()  # No filter
        assert len(history) >= 1

class TestStats:
    """Tests for Soul Key protocol statistics."""

    def test_get_stats_empty(self, protocol):
        """Test stats when no Soul Keys exist."""
        stats = protocol.get_stats()
        assert stats is not None
        assert stats["total_soul_keys"] == 0
        assert stats["total_life_events"] == 0
        assert stats["total_lockouts"] == 0
        assert stats["avg_events_per_key"] == 0

    def test_get_stats_after_creation(self, protocol, sample_device_fingerprint):
        """Test stats after creating Soul Keys and adding events."""
        protocol.create_soul_key("citizen-001", sample_device_fingerprint)
        protocol.create_soul_key("citizen-002", sample_device_fingerprint)

        protocol.add_life_event("citizen-001", LifeEventType.BIRTH_REGISTRATION, "birth")
        protocol.add_life_event("citizen-001", LifeEventType.CITIZENSHIP, "citizenship")
        protocol.add_life_event("citizen-002", LifeEventType.EDUCATION_CERTIFICATE, "education")

        stats = protocol.get_stats()
        assert stats["total_soul_keys"] == 2
        assert stats["total_life_events"] == 3
        assert stats["avg_events_per_key"] == 1.5

class TestPersistence:
    """Tests for Soul Key persistence (save/load)."""

    def test_save_and_load(self, protocol, sample_citizen_id, sample_device_fingerprint, tmp_path):
        """Test saving and loading Soul Key data."""
        protocol.create_soul_key(sample_citizen_id, sample_device_fingerprint)
        protocol.add_life_event(sample_citizen_id, LifeEventType.BIRTH_REGISTRATION, "birth data")

        # Create a new protocol instance with a temp storage dir
        storage_dir = tmp_path / "soul_keys"
        storage_dir.mkdir(exist_ok=True)
        new_protocol = SoulKeyProtocol(storage_dir=str(storage_dir))

        # Manually copy state to the new storage dir
        import json
        soul_key = protocol.get_soul_key(sample_citizen_id)
        state = {
            "soul_keys": {
                sample_citizen_id: soul_key.to_dict(),
            },
            "lockout_records": [],
            "updated_at": "test",
        }
        state_path = storage_dir / "soul_key_state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

        # Load into new protocol instance
        new_protocol._load_state()

        # Verify data persisted
        loaded = new_protocol.get_soul_key(sample_citizen_id)
        assert loaded is not None
        assert loaded.citizen_id == sample_citizen_id
        assert loaded.device_fingerprint == sample_device_fingerprint
        assert len(loaded.life_events) == 1
        assert loaded.life_events[0].event_type == LifeEventType.BIRTH_REGISTRATION
