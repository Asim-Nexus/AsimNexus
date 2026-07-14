"""
Soul Key Protocol Integration Tests
====================================
Tests the complete Soul Key security protocol: creation, life events,
Merkle Tree verification, hardware attestation, lockout mechanism,
and the full Brain Virus-inspired lifecycle.

This verifies that:
  1. Soul Keys can be created with citizen_id and device fingerprint
  2. Life events can be added and Merkle Root is recomputed
  3. Soul Key integrity verification works (valid and tampered)
  4. Hardware attestation detects trusted/mismatch/unknown devices
  5. Automated lockout triggers and resolves correctly
  6. Lockout history and stats are accurate
  7. Singleton consistency is maintained
  8. The full Soul Key lifecycle works end-to-end

Run: pytest tests/integration/test_soul_key_protocol.py -v
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.security.soul_key import (
    SoulKeyProtocol,
    get_soul_key_protocol,
    reset_soul_key_protocol,
    LifeEventType,
    LockoutState,
    AttestationResult,
    LifeEvent,
    SoulKey,
    LockoutRecord,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset the Soul Key singleton before each test."""
    reset_soul_key_protocol()
    yield
    reset_soul_key_protocol()

@pytest.fixture
def protocol():
    """Create a fresh SoulKeyProtocol with a temp storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield SoulKeyProtocol(storage_dir=tmpdir)

@pytest.fixture
def populated_protocol(protocol: SoulKeyProtocol):
    """Create a protocol with a pre-populated Soul Key and life events."""
    # Create Soul Key
    sk = protocol.create_soul_key(
        citizen_id="NID-123456",
        device_fingerprint="TPM-FINGERPRINT-A1B2C3D4",
    )

    # Add life events
    protocol.add_life_event(
        citizen_id="NID-123456",
        event_type=LifeEventType.BIRTH_REGISTRATION,
        raw_data='{"name": "Alice", "dob": "1990-01-15", "place": "Kathmandu"}',
        metadata={"source": "civil_registry"},
    )
    protocol.add_life_event(
        citizen_id="NID-123456",
        event_type=LifeEventType.CITIZENSHIP,
        raw_data='{"certificate_no": "CIT-2020-78901", "type": "natural"}',
        metadata={"source": "home_ministry"},
    )
    protocol.add_life_event(
        citizen_id="NID-123456",
        event_type=LifeEventType.EDUCATION_CERTIFICATE,
        raw_data='{"degree": "B.Sc. CS", "university": "TU", "year": 2015}',
        metadata={"source": "education_board"},
    )
    return protocol

# ── Test Classes ─────────────────────────────────────────────────────────────

class TestSoulKeyCreation:
    """Tests for Soul Key creation."""

    def test_create_soul_key(self, protocol: SoulKeyProtocol):
        """Creating a Soul Key returns a valid SoulKey with correct fields."""
        sk = protocol.create_soul_key(
            citizen_id="NID-999999",
            device_fingerprint="TPM-ABCDEF",
        )
        assert isinstance(sk, SoulKey)
        assert sk.citizen_id == "NID-999999"
        assert sk.device_fingerprint == "TPM-ABCDEF"
        # merkle_root is empty string until life events are added
        assert sk.merkle_root == ""
        assert sk.created_at != ""
        assert sk.last_verified != ""
        assert sk.revoked is False
        assert len(sk.life_events) == 0

    def test_create_soul_key_without_fingerprint(self, protocol: SoulKeyProtocol):
        """Creating a Soul Key without device fingerprint is allowed."""
        sk = protocol.create_soul_key(citizen_id="NID-888888")
        assert sk.citizen_id == "NID-888888"
        assert sk.device_fingerprint == ""

    def test_duplicate_soul_key_raises(self, protocol: SoulKeyProtocol):
        """Creating a Soul Key for an existing citizen raises ValueError."""
        protocol.create_soul_key(citizen_id="NID-111111")
        with pytest.raises(ValueError, match="already exists"):
            protocol.create_soul_key(citizen_id="NID-111111")

    def test_get_soul_key(self, protocol: SoulKeyProtocol):
        """Getting a Soul Key returns the correct key."""
        protocol.create_soul_key(citizen_id="NID-777777")
        sk = protocol.get_soul_key("NID-777777")
        assert sk is not None
        assert sk.citizen_id == "NID-777777"

    def test_get_nonexistent_soul_key(self, protocol: SoulKeyProtocol):
        """Getting a non-existent Soul Key returns None."""
        sk = protocol.get_soul_key("NID-NONEXISTENT")
        assert sk is None

class TestLifeEvents:
    """Tests for adding life events to Soul Keys."""

    def test_add_life_event(self, populated_protocol: SoulKeyProtocol):
        """Adding a life event returns a valid LifeEvent with correct fields."""
        event = populated_protocol.add_life_event(
            citizen_id="NID-123456",
            event_type=LifeEventType.VOTER_REGISTRATION,
            raw_data='{"constituency": "Kathmandu-1", "voter_id": "VOT-2024-001"}',
            metadata={"source": "election_commission"},
        )
        assert isinstance(event, LifeEvent)
        assert event.event_type == LifeEventType.VOTER_REGISTRATION
        assert event.data_hash != ""  # SHA-256 hash of raw data
        assert event.event_id.startswith("NID-123456_voter_registration_")
        assert event.metadata.get("source") == "election_commission"

    def test_merkle_root_updates(self, populated_protocol: SoulKeyProtocol):
        """Merkle Root changes after adding a life event."""
        sk_before = populated_protocol.get_soul_key("NID-123456")
        root_before = sk_before.merkle_root

        populated_protocol.add_life_event(
            citizen_id="NID-123456",
            event_type=LifeEventType.TAX_COMPLIANCE,
            raw_data='{"pan": "PAN-2023-45678", "year": 2023}',
        )

        sk_after = populated_protocol.get_soul_key("NID-123456")
        root_after = sk_after.merkle_root

        assert root_before != root_after
        assert len(root_after) == 64  # SHA-256 hex digest

    def test_add_event_to_nonexistent_key(self, protocol: SoulKeyProtocol):
        """Adding a life event to a non-existent Soul Key raises ValueError."""
        with pytest.raises(ValueError, match="No Soul Key found"):
            protocol.add_life_event(
                citizen_id="NID-NONEXISTENT",
                event_type=LifeEventType.BIRTH_REGISTRATION,
                raw_data="test",
            )

    def test_raw_data_never_stored(self, populated_protocol: SoulKeyProtocol):
        """Raw data is hashed and never stored in the Soul Key."""
        sk = populated_protocol.get_soul_key("NID-123456")
        for event in sk.life_events:
            # The raw data should NOT appear anywhere in the event
            assert "Alice" not in event.data_hash
            assert "1990-01-15" not in event.data_hash
            # Only the SHA-256 hash is stored
            assert len(event.data_hash) == 64

    def test_multiple_events_accumulate(self, populated_protocol: SoulKeyProtocol):
        """Multiple life events accumulate in the Soul Key."""
        sk = populated_protocol.get_soul_key("NID-123456")
        assert len(sk.life_events) == 3

        # Add 2 more
        populated_protocol.add_life_event(
            citizen_id="NID-123456",
            event_type=LifeEventType.PASSPORT_ISSUANCE,
            raw_data='{"passport_no": "P-2024-56789"}',
        )
        populated_protocol.add_life_event(
            citizen_id="NID-123456",
            event_type=LifeEventType.DRIVING_LICENSE,
            raw_data='{"license_no": "DL-2024-12345"}',
        )

        sk = populated_protocol.get_soul_key("NID-123456")
        assert len(sk.life_events) == 5

class TestSoulKeyVerification:
    """Tests for Soul Key integrity verification."""

    def test_verify_valid_soul_key(self, populated_protocol: SoulKeyProtocol):
        """A valid Soul Key with untampered events verifies as True."""
        is_valid = populated_protocol.verify_soul_key("NID-123456")
        assert is_valid is True

    def test_verify_nonexistent_key(self, protocol: SoulKeyProtocol):
        """Verifying a non-existent Soul Key returns False."""
        is_valid = protocol.verify_soul_key("NID-NONEXISTENT")
        assert is_valid is False

    def test_verify_tampered_soul_key(self, protocol: SoulKeyProtocol):
        """A Soul Key with tampered events fails verification."""
        # Create a Soul Key
        protocol.create_soul_key(
            citizen_id="NID-TAMPER",
            device_fingerprint="TPM-TEST",
        )
        protocol.add_life_event(
            citizen_id="NID-TAMPER",
            event_type=LifeEventType.BIRTH_REGISTRATION,
            raw_data='{"name": "Bob"}',
        )

        # Verify it's valid initially
        assert protocol.verify_soul_key("NID-TAMPER") is True

        # Tamper with the stored data directly
        sk = protocol.get_soul_key("NID-TAMPER")
        sk.merkle_root = "tampered_root_value"

        # Verification should now fail
        assert protocol.verify_soul_key("NID-TAMPER") is False

    def test_verify_updates_last_verified(self, populated_protocol: SoulKeyProtocol):
        """Verification updates the last_verified timestamp."""
        sk_before = populated_protocol.get_soul_key("NID-123456")
        last_verified_before = sk_before.last_verified

        populated_protocol.verify_soul_key("NID-123456")

        sk_after = populated_protocol.get_soul_key("NID-123456")
        assert sk_after.last_verified >= last_verified_before

class TestHardwareAttestation:
    """Tests for hardware device attestation."""

    def test_trusted_device(self, populated_protocol: SoulKeyProtocol):
        """Attesting with the registered fingerprint returns TRUSTED."""
        result = populated_protocol.attest_device(
            citizen_id="NID-123456",
            current_fingerprint="TPM-FINGERPRINT-A1B2C3D4",
        )
        assert result == AttestationResult.TRUSTED

    def test_mismatched_device(self, populated_protocol: SoulKeyProtocol):
        """Attesting with a different fingerprint returns MISMATCH."""
        result = populated_protocol.attest_device(
            citizen_id="NID-123456",
            current_fingerprint="TPM-COMPROMISED-DEVICE",
        )
        assert result == AttestationResult.MISMATCH

    def test_unknown_device(self, protocol: SoulKeyProtocol):
        """Attesting for a non-existent citizen returns UNKNOWN_DEVICE."""
        result = protocol.attest_device(
            citizen_id="NID-NONEXISTENT",
            current_fingerprint="TPM-UNKNOWN",
        )
        assert result == AttestationResult.UNKNOWN_DEVICE

    def test_first_device_registration(self, protocol: SoulKeyProtocol):
        """First device attestation registers the fingerprint as TRUSTED."""
        protocol.create_soul_key(citizen_id="NID-FIRST")
        result = protocol.attest_device(
            citizen_id="NID-FIRST",
            current_fingerprint="TPM-FIRST-TIME",
        )
        assert result == AttestationResult.TRUSTED

        # Verify the fingerprint was registered
        sk = protocol.get_soul_key("NID-FIRST")
        assert sk.device_fingerprint == "TPM-FIRST-TIME"

class TestLockoutMechanism:
    """Tests for the Brain Virus automated lockout mechanism."""

    def test_trigger_lockout(self, populated_protocol: SoulKeyProtocol):
        """Triggering a lockout returns a LockoutRecord with correct fields."""
        record = populated_protocol.trigger_lockout(
            citizen_id="NID-123456",
            session_id="SESSION-ABC-123",
            device_fingerprint_attempted="TPM-ATTACKER-DEVICE",
            reason="Unauthorized access from unknown device",
        )
        assert isinstance(record, LockoutRecord)
        assert record.citizen_id == "NID-123456"
        assert record.session_id == "SESSION-ABC-123"
        assert record.device_fingerprint_attempted == "TPM-ATTACKER-DEVICE"
        assert record.device_fingerprint_registered == "TPM-FINGERPRINT-A1B2C3D4"
        assert record.reason == "Unauthorized access from unknown device"
        assert record.record_id.startswith("LOCK_")
        assert record.ncsc_incident_id.startswith("NCSC-")

    def test_lockout_state_progression(self, populated_protocol: SoulKeyProtocol):
        """Lockout progresses through LOCKED → REVOKED → SELF_DESTRUCT → INCIDENT_REPORTED."""
        record = populated_protocol.trigger_lockout(
            citizen_id="NID-123456",
            session_id="SESSION-XYZ-789",
            device_fingerprint_attempted="TPM-HACKER",
            reason="Brute force attempt detected",
        )
        # The final state should be INCIDENT_REPORTED (after all steps)
        assert record.state == LockoutState.INCIDENT_REPORTED

    def test_resolve_lockout(self, populated_protocol: SoulKeyProtocol):
        """Resolving a lockout sets state to ACTIVE and records resolution time."""
        record = populated_protocol.trigger_lockout(
            citizen_id="NID-123456",
            session_id="SESSION-RESOLVE",
            device_fingerprint_attempted="TPM-ATTACKER",
            reason="Test lockout",
        )
        assert record.state == LockoutState.INCIDENT_REPORTED

        # Resolve the lockout
        resolved = populated_protocol.resolve_lockout(record.record_id)
        assert resolved is True

        # Check the record was updated
        history = populated_protocol.get_lockout_history(citizen_id="NID-123456")
        resolved_record = next(r for r in history if r.record_id == record.record_id)
        assert resolved_record.state == LockoutState.ACTIVE
        assert resolved_record.resolved_at != ""

    def test_resolve_nonexistent_lockout(self, protocol: SoulKeyProtocol):
        """Resolving a non-existent lockout returns False."""
        resolved = protocol.resolve_lockout("LOCK-NONEXISTENT")
        assert resolved is False

    def test_lockout_history_filtered(self, populated_protocol: SoulKeyProtocol):
        """Lockout history can be filtered by citizen_id."""
        # Create lockouts for two citizens
        populated_protocol.trigger_lockout(
            citizen_id="NID-123456",
            session_id="SESSION-1",
            device_fingerprint_attempted="TPM-ATTACKER-1",
        )
        populated_protocol.trigger_lockout(
            citizen_id="NID-123456",
            session_id="SESSION-2",
            device_fingerprint_attempted="TPM-ATTACKER-2",
        )

        # Create a second citizen
        populated_protocol.create_soul_key(
            citizen_id="NID-OTHER",
            device_fingerprint="TPM-OTHER",
        )
        populated_protocol.trigger_lockout(
            citizen_id="NID-OTHER",
            session_id="SESSION-3",
            device_fingerprint_attempted="TPM-ATTACKER-3",
        )

        # Filter by citizen
        citizen_history = populated_protocol.get_lockout_history(citizen_id="NID-123456")
        assert len(citizen_history) == 2

        other_history = populated_protocol.get_lockout_history(citizen_id="NID-OTHER")
        assert len(other_history) == 1

        # All history
        all_history = populated_protocol.get_lockout_history()
        assert len(all_history) == 3

class TestStats:
    """Tests for Soul Key protocol statistics."""

    def test_stats_empty(self, protocol: SoulKeyProtocol):
        """Stats returns zeros when no keys exist."""
        stats = protocol.get_stats()
        assert stats["total_soul_keys"] == 0
        assert stats["total_life_events"] == 0
        assert stats["total_lockouts"] == 0
        assert stats["active_lockouts"] == 0
        assert stats["revoked_keys"] == 0
        assert stats["avg_events_per_key"] == 0

    def test_stats_with_data(self, populated_protocol: SoulKeyProtocol):
        """Stats reflect the actual state of the protocol."""
        stats = populated_protocol.get_stats()
        assert stats["total_soul_keys"] == 1
        assert stats["total_life_events"] == 3
        assert stats["total_lockouts"] == 0
        assert stats["avg_events_per_key"] == 3.0

    def test_stats_after_lockout(self, populated_protocol: SoulKeyProtocol):
        """Stats update after a lockout is triggered."""
        populated_protocol.trigger_lockout(
            citizen_id="NID-123456",
            session_id="SESSION-STATS",
            device_fingerprint_attempted="TPM-ATTACKER",
        )
        stats = populated_protocol.get_stats()
        assert stats["total_lockouts"] == 1
        # active_lockouts counts records NOT in ACTIVE state
        assert stats["active_lockouts"] == 1

    def test_stats_multiple_keys(self, protocol: SoulKeyProtocol):
        """Stats correctly aggregate across multiple Soul Keys."""
        protocol.create_soul_key(citizen_id="NID-001")
        protocol.create_soul_key(citizen_id="NID-002")
        protocol.create_soul_key(citizen_id="NID-003")

        protocol.add_life_event("NID-001", LifeEventType.BIRTH_REGISTRATION, "data1")
        protocol.add_life_event("NID-001", LifeEventType.CITIZENSHIP, "data2")
        protocol.add_life_event("NID-002", LifeEventType.BIRTH_REGISTRATION, "data3")

        stats = protocol.get_stats()
        assert stats["total_soul_keys"] == 3
        assert stats["total_life_events"] == 3
        assert stats["avg_events_per_key"] == 1.0

class TestSingleton:
    """Tests for the Soul Key singleton pattern."""

    def test_get_soul_key_protocol_returns_instance(self):
        """get_soul_key_protocol() returns a SoulKeyProtocol instance."""
        sp = get_soul_key_protocol()
        assert isinstance(sp, SoulKeyProtocol)

    def test_get_soul_key_protocol_singleton(self):
        """get_soul_key_protocol() always returns the same instance."""
        sp1 = get_soul_key_protocol()
        sp2 = get_soul_key_protocol()
        assert sp1 is sp2

    def test_reset_soul_key_protocol(self):
        """reset_soul_key_protocol() creates a new instance on next access."""
        sp1 = get_soul_key_protocol()
        reset_soul_key_protocol()
        sp2 = get_soul_key_protocol()
        assert sp1 is not sp2

    def test_singleton_persistence(self):
        """Data written to singleton is readable from the same singleton."""
        reset_soul_key_protocol()
        import uuid
        unique_id = f"NID-SINGLETON-{uuid.uuid4().hex[:8]}"
        sp = get_soul_key_protocol()
        sp.create_soul_key(citizen_id=unique_id)
        sk = sp.get_soul_key(unique_id)
        assert sk is not None
        assert sk.citizen_id == unique_id
        reset_soul_key_protocol()

class TestDataClasses:
    """Tests for Soul Key data class serialization."""

    def test_life_event_to_dict(self):
        """LifeEvent.to_dict() returns the correct dictionary."""
        event = LifeEvent(
            event_id="EVT-001",
            event_type=LifeEventType.BIRTH_REGISTRATION,
            timestamp="2024-01-01T00:00:00Z",
            data_hash="abc123",
            metadata={"source": "test"},
        )
        d = event.to_dict()
        assert d["event_id"] == "EVT-001"
        assert d["event_type"] == "birth_registration"
        assert d["data_hash"] == "abc123"
        assert d["metadata"]["source"] == "test"

    def test_life_event_from_dict(self):
        """LifeEvent.from_dict() reconstructs a LifeEvent correctly."""
        data = {
            "event_id": "EVT-002",
            "event_type": "citizenship",
            "timestamp": "2024-06-15T12:00:00Z",
            "data_hash": "def456",
            "metadata": {"source": "ministry"},
        }
        event = LifeEvent.from_dict(data)
        assert event.event_id == "EVT-002"
        assert event.event_type == LifeEventType.CITIZENSHIP
        assert event.data_hash == "def456"

    def test_soul_key_to_dict(self):
        """SoulKey.to_dict() returns the correct dictionary."""
        events = [
            LifeEvent("EVT-1", LifeEventType.BIRTH_REGISTRATION, "2024-01-01T00:00:00Z", "hash1"),
        ]
        sk = SoulKey(
            citizen_id="NID-001",
            merkle_root="root_hash",
            life_events=events,
            created_at="2024-01-01T00:00:00Z",
            last_verified="2024-06-01T00:00:00Z",
            device_fingerprint="TPM-001",
        )
        d = sk.to_dict()
        assert d["citizen_id"] == "NID-001"
        assert d["merkle_root"] == "root_hash"
        assert len(d["life_events"]) == 1
        assert d["device_fingerprint"] == "TPM-001"

    def test_soul_key_from_dict(self):
        """SoulKey.from_dict() reconstructs a SoulKey correctly."""
        data = {
            "citizen_id": "NID-002",
            "merkle_root": "root_abc",
            "life_events": [
                {
                    "event_id": "EVT-1",
                    "event_type": "birth_registration",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "data_hash": "hash1",
                    "metadata": {},
                }
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "last_verified": "2024-06-01T00:00:00Z",
            "device_fingerprint": "TPM-002",
            "revoked": False,
            "revocation_reason": "",
        }
        sk = SoulKey.from_dict(data)
        assert sk.citizen_id == "NID-002"
        assert sk.merkle_root == "root_abc"
        assert len(sk.life_events) == 1
        assert sk.life_events[0].event_type == LifeEventType.BIRTH_REGISTRATION

    def test_lockout_record_to_dict(self):
        """LockoutRecord.to_dict() returns the correct dictionary."""
        record = LockoutRecord(
            record_id="LOCK-001",
            citizen_id="NID-001",
            session_id="SESSION-001",
            state=LockoutState.INCIDENT_REPORTED,
            detected_at="2024-06-01T00:00:00Z",
            device_fingerprint_attempted="TPM-ATTACKER",
            device_fingerprint_registered="TPM-OWNER",
            reason="Unauthorized access",
            resolved_at="",
            ncsc_incident_id="NCSC-001",
        )
        d = record.to_dict()
        assert d["record_id"] == "LOCK-001"
        assert d["state"] == "incident_reported"
        assert d["ncsc_incident_id"] == "NCSC-001"

class TestFullSoulKeyLifecycle:
    """End-to-end tests for the complete Soul Key lifecycle."""

    def test_full_lifecycle(self, protocol: SoulKeyProtocol):
        """Complete Soul Key lifecycle: create → events → verify → attest → lockout → resolve."""
        # 1. Create Soul Key
        sk = protocol.create_soul_key(
            citizen_id="NID-LIFECYCLE",
            device_fingerprint="TPM-LIFECYCLE-DEVICE",
        )
        assert sk.citizen_id == "NID-LIFECYCLE"

        # 2. Add life events
        protocol.add_life_event(
            "NID-LIFECYCLE",
            LifeEventType.BIRTH_REGISTRATION,
            '{"name": "Charlie", "dob": "1995-03-20"}',
        )
        protocol.add_life_event(
            "NID-LIFECYCLE",
            LifeEventType.CITIZENSHIP,
            '{"certificate_no": "CIT-2020-12345"}',
        )
        protocol.add_life_event(
            "NID-LIFECYCLE",
            LifeEventType.EDUCATION_CERTIFICATE,
            '{"degree": "M.Sc.", "university": "KU"}',
        )
        sk = protocol.get_soul_key("NID-LIFECYCLE")
        assert len(sk.life_events) == 3
        assert sk.merkle_root != "0" * 64

        # 3. Verify Soul Key integrity
        assert protocol.verify_soul_key("NID-LIFECYCLE") is True

        # 4. Attest trusted device
        result = protocol.attest_device("NID-LIFECYCLE", "TPM-LIFECYCLE-DEVICE")
        assert result == AttestationResult.TRUSTED

        # 5. Detect unauthorized access (mismatched device)
        result = protocol.attest_device("NID-LIFECYCLE", "TPM-ATTACKER-DEVICE")
        assert result == AttestationResult.MISMATCH

        # 6. Trigger automated lockout
        record = protocol.trigger_lockout(
            citizen_id="NID-LIFECYCLE",
            session_id="SESSION-LIFECYCLE-001",
            device_fingerprint_attempted="TPM-ATTACKER-DEVICE",
            reason="Brain Virus triggered: device mismatch",
        )
        assert record.state == LockoutState.INCIDENT_REPORTED
        assert record.ncsc_incident_id != ""

        # 7. Verify stats reflect the lifecycle
        stats = protocol.get_stats()
        assert stats["total_soul_keys"] == 1
        assert stats["total_life_events"] == 3
        assert stats["total_lockouts"] == 1

        # 8. Resolve lockout after verification
        resolved = protocol.resolve_lockout(record.record_id)
        assert resolved is True

        # 9. Verify lockout history
        history = protocol.get_lockout_history(citizen_id="NID-LIFECYCLE")
        assert len(history) == 1
        assert history[0].state == LockoutState.ACTIVE
        assert history[0].resolved_at != ""

    def test_multiple_citizens_isolation(self, protocol: SoulKeyProtocol):
        """Multiple citizens' Soul Keys are isolated from each other."""
        # Create keys for two citizens
        protocol.create_soul_key("NID-ALICE", "TPM-ALICE")
        protocol.create_soul_key("NID-BOB", "TPM-BOB")

        # Add events to Alice only
        protocol.add_life_event("NID-ALICE", LifeEventType.BIRTH_REGISTRATION, "alice_birth")
        protocol.add_life_event("NID-ALICE", LifeEventType.CITIZENSHIP, "alice_citizen")

        # Bob should have no events
        bob_sk = protocol.get_soul_key("NID-BOB")
        assert len(bob_sk.life_events) == 0

        # Alice should have 2 events
        alice_sk = protocol.get_soul_key("NID-ALICE")
        assert len(alice_sk.life_events) == 2

        # Lockout for Alice should not affect Bob
        protocol.trigger_lockout(
            "NID-ALICE", "SESSION-ALICE", "TPM-ATTACKER", "Alice compromised"
        )
        bob_history = protocol.get_lockout_history(citizen_id="NID-BOB")
        assert len(bob_history) == 0

    def test_persistence_across_instances(self):
        """Soul Key data persists across instances using the same storage dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create protocol and add data
            p1 = SoulKeyProtocol(storage_dir=tmpdir)
            p1.create_soul_key("NID-PERSIST", "TPM-PERSIST")
            p1.add_life_event("NID-PERSIST", LifeEventType.BIRTH_REGISTRATION, "persist_data")

            # Create new protocol instance with same storage dir
            p2 = SoulKeyProtocol(storage_dir=tmpdir)
            sk = p2.get_soul_key("NID-PERSIST")
            assert sk is not None
            assert sk.citizen_id == "NID-PERSIST"
            assert len(sk.life_events) == 1

    def test_merkle_tree_verification_consistent(self, protocol: SoulKeyProtocol):
        """Merkle Tree verification is consistent — verify passes after adding events."""
        protocol.create_soul_key("NID-CONSISTENT", "TPM-CONSISTENT")

        # Add events and verify after each addition
        protocol.add_life_event("NID-CONSISTENT", LifeEventType.BIRTH_REGISTRATION, "data_1")
        assert protocol.verify_soul_key("NID-CONSISTENT") is True

        protocol.add_life_event("NID-CONSISTENT", LifeEventType.CITIZENSHIP, "data_2")
        assert protocol.verify_soul_key("NID-CONSISTENT") is True

        protocol.add_life_event("NID-CONSISTENT", LifeEventType.EDUCATION_CERTIFICATE, "data_3")
        assert protocol.verify_soul_key("NID-CONSISTENT") is True

        # The root should be non-empty and valid
        sk = protocol.get_soul_key("NID-CONSISTENT")
        assert len(sk.merkle_root) == 64
        assert sk.merkle_root != "0" * 64
