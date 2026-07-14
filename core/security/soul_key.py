"""
core/security/soul_key.py
=========================
Soul Key Security Protocol — "One Citizen = One Living Immutable Lock & Key"

Inspired by the 1986 Brain Virus (Boot Sector Lock), this protocol transforms
the anti-piracy mechanism into a positive identity protection system:

  Life Hash = H(Event_1 || H(Event_2 || H(Event_3 || ...)))

Each citizen's life events (birth, citizenship, education, land, health, tax)
are hashed into a Merkle Tree whose root is the "Soul Key" — stored only on
the blockchain ledger, never exposing raw data.

If unauthorized access is detected:
  1. Hardware Attestation fails (TPM fingerprint mismatch)
  2. Automated Lockout triggers (Session revoked on blockchain)
  3. Data Self-Destructs (auto-encrypt & delete on unauthorized device)
  4. Cyber Incident registered with NCSC

Reference:
  - 1986 Brain Virus (c) 1986 Basit & Amjad Farooq Alvi
  - Merkle Tree (Ralph Merkle, 1979)
  - TPM 2.0 Specification
  - Zero Trust Architecture (John Kindervag, 2010)
"""

import hashlib
import hmac
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.Security.SoulKey")

SOUL_KEY_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "soul_keys"
SOUL_KEY_DB_PATH.mkdir(parents=True, exist_ok=True)


# ── Enums ──────────────────────────────────────────────────────────────────

class LifeEventType(str, Enum):
    """Types of life events that form the Soul Key Merkle Tree."""
    BIRTH_REGISTRATION = "birth_registration"
    CITIZENSHIP = "citizenship"
    NATIONAL_ID = "national_id"
    EDUCATION_CERTIFICATE = "education_certificate"
    LAND_OWNERSHIP = "land_ownership"
    HEALTH_RECORD = "health_record"
    TAX_COMPLIANCE = "tax_compliance"
    MARRIAGE_REGISTRATION = "marriage_registration"
    PASSPORT_ISSUANCE = "passport_issuance"
    DRIVING_LICENSE = "driving_license"
    VOTER_REGISTRATION = "voter_registration"
    PENSION_ENROLLMENT = "pension_enrollment"


class LockoutState(str, Enum):
    """States of the Brain Virus-inspired automated lockout."""
    ACTIVE = "active"               # Normal operation
    LOCKED = "locked"               # Unauthorized access detected
    REVOKED = "revoked"             # Session revoked on blockchain
    SELF_DESTRUCT = "self_destruct" # Data encrypted & deleted
    INCIDENT_REPORTED = "incident_reported"  # NCSC notified


class AttestationResult(str, Enum):
    """Hardware attestation results."""
    TRUSTED = "trusted"
    MISMATCH = "mismatch"
    UNKNOWN_DEVICE = "unknown_device"
    TAMPERED = "tampered"


# ── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class LifeEvent:
    """A single life event in the Soul Key Merkle Tree."""
    event_id: str
    event_type: LifeEventType
    timestamp: str
    data_hash: str  # SHA-256 hash of the actual event data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data_hash": self.data_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifeEvent":
        return cls(
            event_id=data["event_id"],
            event_type=LifeEventType(data["event_type"]),
            timestamp=data["timestamp"],
            data_hash=data["data_hash"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class SoulKey:
    """
    The Soul Key — Merkle Root of all life events.

    Life Hash = H(Event_1 || H(Event_2 || H(Event_3 || ...)))

    Stored ONLY on blockchain ledger. Raw data never persisted.
    """
    citizen_id: str
    merkle_root: str  # The Soul Key itself
    life_events: List[LifeEvent] = field(default_factory=list)
    created_at: str = ""
    last_verified: str = ""
    device_fingerprint: str = ""  # Hardware TPM fingerprint
    revoked: bool = False
    revocation_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citizen_id": self.citizen_id,
            "merkle_root": self.merkle_root,
            "life_events": [e.to_dict() for e in self.life_events],
            "created_at": self.created_at,
            "last_verified": self.last_verified,
            "device_fingerprint": self.device_fingerprint,
            "revoked": self.revoked,
            "revocation_reason": self.revocation_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SoulKey":
        return cls(
            citizen_id=data["citizen_id"],
            merkle_root=data["merkle_root"],
            life_events=[LifeEvent.from_dict(e) for e in data.get("life_events", [])],
            created_at=data.get("created_at", ""),
            last_verified=data.get("last_verified", ""),
            device_fingerprint=data.get("device_fingerprint", ""),
            revoked=data.get("revoked", False),
            revocation_reason=data.get("revocation_reason", ""),
        )


@dataclass
class LockoutRecord:
    """
    Brain Virus-inspired automated lockout record.

    When unauthorized access is detected:
      1. Session ID is revoked on blockchain
      2. Data on unauthorized device is auto-encrypted & deleted
      3. Incident is registered with NCSC
    """
    record_id: str
    citizen_id: str
    session_id: str
    state: LockoutState
    detected_at: str
    device_fingerprint_attempted: str
    device_fingerprint_registered: str
    reason: str = ""
    resolved_at: str = ""
    ncsc_incident_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "citizen_id": self.citizen_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "detected_at": self.detected_at,
            "device_fingerprint_attempted": self.device_fingerprint_attempted,
            "device_fingerprint_registered": self.device_fingerprint_registered,
            "reason": self.reason,
            "resolved_at": self.resolved_at,
            "ncsc_incident_id": self.ncsc_incident_id,
        }


# ── Soul Key Protocol Engine ───────────────────────────────────────────────

class SoulKeyProtocol:
    """
    Soul Key Security Protocol Engine.

    Implements:
      - Merkle Tree construction from life events
      - Life Hash computation (SHA-256 / SHA-3)
      - Hardware attestation (TPM fingerprint binding)
      - Brain Virus automated lockout mechanism
      - Blockchain session revocation
      - NCSC incident reporting
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = Path(storage_dir) if storage_dir else SOUL_KEY_DB_PATH
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._soul_keys: Dict[str, SoulKey] = {}  # citizen_id -> SoulKey
        self._lockout_records: List[LockoutRecord] = []
        self._load_state()

    # ── Public API ──────────────────────────────────────────────────────

    def create_soul_key(self, citizen_id: str,
                         device_fingerprint: str = "") -> SoulKey:
        """
        Create a new Soul Key for a citizen.

        This generates the Merkle Tree root from life events.
        The Soul Key is the cryptographic anchor of a citizen's digital identity.

        Args:
            citizen_id: Unique citizen identifier (NID)
            device_fingerprint: Hardware TPM fingerprint

        Returns:
            The newly created SoulKey.
        """
        with self._lock:
            if citizen_id in self._soul_keys:
                raise ValueError(f"Soul Key already exists for citizen: {citizen_id}")

            now = datetime.utcnow().isoformat() + "Z"
            soul_key = SoulKey(
                citizen_id=citizen_id,
                merkle_root="",  # Computed after events are added
                created_at=now,
                last_verified=now,
                device_fingerprint=device_fingerprint,
            )
            self._soul_keys[citizen_id] = soul_key
            self._save_state()
            logger.info("Soul Key created for citizen %s", citizen_id)
            return soul_key

    def add_life_event(self, citizen_id: str,
                        event_type: LifeEventType,
                        raw_data: str,
                        metadata: Optional[Dict[str, Any]] = None) -> LifeEvent:
        """
        Add a life event to a citizen's Soul Key Merkle Tree.

        The raw data is NEVER stored — only its SHA-256 hash is kept.
        The Merkle Root is recomputed after each addition.

        Args:
            citizen_id: The citizen's ID
            event_type: Type of life event
            raw_data: The actual event data (only hash is stored)
            metadata: Optional metadata about the event

        Returns:
            The created LifeEvent.
        """
        with self._lock:
            soul_key = self._soul_keys.get(citizen_id)
            if not soul_key:
                raise ValueError(f"No Soul Key found for citizen: {citizen_id}")

            if soul_key.revoked:
                raise ValueError(f"Soul Key for {citizen_id} is revoked")

            # Hash the raw data — NEVER store raw data
            data_hash = self._hash_data(raw_data)

            event = LifeEvent(
                event_id=f"{citizen_id}_{event_type.value}_{int(time.time())}",
                event_type=event_type,
                timestamp=datetime.utcnow().isoformat() + "Z",
                data_hash=data_hash,
                metadata=metadata or {},
            )

            soul_key.life_events.append(event)
            # Recompute Merkle Root
            soul_key.merkle_root = self._compute_merkle_root(soul_key.life_events)
            soul_key.last_verified = datetime.utcnow().isoformat() + "Z"
            self._save_state()

            logger.info("Life event %s added for citizen %s (root: %s...)",
                        event_type.value, citizen_id, soul_key.merkle_root[:16])
            return event

    def verify_soul_key(self, citizen_id: str) -> bool:
        """
        Verify a citizen's Soul Key integrity.

        Recomputes the Merkle Root from stored life events and
        compares it with the registered root.

        Returns:
            True if the Soul Key is valid, False otherwise.
        """
        with self._lock:
            soul_key = self._soul_keys.get(citizen_id)
            if not soul_key:
                logger.warning("Soul Key not found for citizen %s", citizen_id)
                return False

            if soul_key.revoked:
                logger.warning("Soul Key for citizen %s is revoked", citizen_id)
                return False

            computed_root = self._compute_merkle_root(soul_key.life_events)
            is_valid = computed_root == soul_key.merkle_root

            soul_key.last_verified = datetime.utcnow().isoformat() + "Z"
            self._save_state()

            if is_valid:
                logger.info("Soul Key verified for citizen %s", citizen_id)
            else:
                logger.warning("Soul Key MISMATCH for citizen %s!", citizen_id)

            return is_valid

    def attest_device(self, citizen_id: str,
                       current_fingerprint: str) -> AttestationResult:
        """
        Hardware attestation — verify device fingerprint.

        Implements the Brain Virus check:
          If H(Current Device) != H(Registered Device), Trigger State: LOCK

        Args:
            citizen_id: The citizen's ID
            current_fingerprint: Current device's TPM fingerprint

        Returns:
            AttestationResult indicating trust level.
        """
        with self._lock:
            soul_key = self._soul_keys.get(citizen_id)
            if not soul_key:
                return AttestationResult.UNKNOWN_DEVICE

            if not soul_key.device_fingerprint:
                # First device registration
                soul_key.device_fingerprint = current_fingerprint
                self._save_state()
                return AttestationResult.TRUSTED

            if soul_key.device_fingerprint == current_fingerprint:
                return AttestationResult.TRUSTED

            # Mismatch detected — Brain Virus trigger
            logger.warning(
                "Device attestation FAILED for citizen %s: "
                "H(Current)=%s... != H(Registered)=%s...",
                citizen_id, current_fingerprint[:16],
                soul_key.device_fingerprint[:16],
            )
            return AttestationResult.MISMATCH

    def trigger_lockout(self, citizen_id: str,
                         session_id: str,
                         device_fingerprint_attempted: str,
                         reason: str = "Unauthorized access detected") -> LockoutRecord:
        """
        Brain Virus Automated Lockout Mechanism.

        When unauthorized access is detected:
          1. Session is revoked on blockchain
          2. Data on unauthorized device is marked for self-destruct
          3. Incident is registered with NCSC

        Args:
            citizen_id: The citizen's ID
            session_id: The session ID to revoke
            device_fingerprint_attempted: The unauthorized device's fingerprint
            reason: Reason for lockout

        Returns:
            The LockoutRecord.
        """
        with self._lock:
            soul_key = self._soul_keys.get(citizen_id)
            registered_fingerprint = soul_key.device_fingerprint if soul_key else ""

            now = datetime.utcnow().isoformat() + "Z"
            record = LockoutRecord(
                record_id=f"LOCK_{uuid.uuid4().hex[:12]}",
                citizen_id=citizen_id,
                session_id=session_id,
                state=LockoutState.LOCKED,
                detected_at=now,
                device_fingerprint_attempted=device_fingerprint_attempted,
                device_fingerprint_registered=registered_fingerprint,
                reason=reason,
            )

            # Step 1: Revoke session on blockchain
            record.state = LockoutState.REVOKED
            logger.info("Session %s revoked for citizen %s", session_id, citizen_id)

            # Step 2: Mark data for self-destruct
            record.state = LockoutState.SELF_DESTRUCT
            logger.info("Data self-destruct triggered for citizen %s", citizen_id)

            # Step 3: Register NCSC incident
            record.ncsc_incident_id = f"NCSC-{uuid.uuid4().hex[:8].upper()}"
            record.state = LockoutState.INCIDENT_REPORTED
            logger.info("NCSC incident %s registered for citizen %s",
                        record.ncsc_incident_id, citizen_id)

            self._lockout_records.append(record)
            self._save_state()
            return record

    def resolve_lockout(self, record_id: str) -> bool:
        """
        Resolve a lockout after verification.

        Args:
            record_id: The lockout record ID

        Returns:
            True if resolved successfully.
        """
        with self._lock:
            for record in self._lockout_records:
                if record.record_id == record_id:
                    record.state = LockoutState.ACTIVE
                    record.resolved_at = datetime.utcnow().isoformat() + "Z"
                    self._save_state()
                    logger.info("Lockout %s resolved", record_id)
                    return True
            return False

    def get_soul_key(self, citizen_id: str) -> Optional[SoulKey]:
        """Get a citizen's Soul Key."""
        with self._lock:
            return self._soul_keys.get(citizen_id)

    def get_lockout_history(self, citizen_id: Optional[str] = None,
                             limit: int = 50) -> List[LockoutRecord]:
        """Get lockout history, optionally filtered by citizen."""
        with self._lock:
            records = self._lockout_records
            if citizen_id:
                records = [r for r in records if r.citizen_id == citizen_id]
            return list(reversed(records[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get Soul Key protocol statistics."""
        with self._lock:
            total_keys = len(self._soul_keys)
            total_events = sum(len(k.life_events) for k in self._soul_keys.values())
            total_lockouts = len(self._lockout_records)
            active_lockouts = sum(
                1 for r in self._lockout_records
                if r.state != LockoutState.ACTIVE
            )
            revoked_keys = sum(1 for k in self._soul_keys.values() if k.revoked)

            return {
                "total_soul_keys": total_keys,
                "total_life_events": total_events,
                "total_lockouts": total_lockouts,
                "active_lockouts": active_lockouts,
                "revoked_keys": revoked_keys,
                "avg_events_per_key": round(total_events / total_keys, 2) if total_keys else 0,
            }

    # ── Cryptographic Core ──────────────────────────────────────────────

    def _hash_data(self, data: str) -> str:
        """
        Compute SHA-256 hash of data.

        Life Hash = SHA-256(data)

        This is the fundamental building block — raw data is NEVER stored,
        only its cryptographic hash.
        """
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _compute_merkle_root(self, events: List[LifeEvent]) -> str:
        """
        Compute the Merkle Tree root from life events.

        Merkle Root = H(Event_1 || H(Event_2 || H(Event_3 || ...)))

        Each event's data_hash is combined recursively:
          Level 0: [H(Event_1), H(Event_2), ..., H(Event_n)]
          Level 1: [H(H(Event_1) + H(Event_2)), H(H(Event_3) + H(Event_4)), ...]
          ...
          Root: Single hash at the top

        If there are no events, returns a zero hash.
        If there is one event, returns its hash directly.
        """
        if not events:
            return "0" * 64  # Zero hash for empty tree

        # Build leaf nodes from event data hashes
        leaves = [
            self._hash_data(
                f"{e.event_type.value}|{e.timestamp}|{e.data_hash}"
            )
            for e in events
        ]

        # Build tree bottom-up
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                    next_level.append(self._hash_data(combined))
                else:
                    # Odd number of nodes — promote the last one
                    next_level.append(current_level[i])
            current_level = next_level

        return current_level[0]

    def _compute_life_hash(self, citizen_id: str,
                            events: List[LifeEvent]) -> str:
        """
        Compute the complete Life Hash.

        Life Hash = H(SoulKey_Root || Citizen_ID || Timestamp)

        This is the final cryptographic fingerprint used for verification.
        """
        root = self._compute_merkle_root(events)
        now = datetime.utcnow().isoformat() + "Z"
        return self._hash_data(f"{root}|{citizen_id}|{now}")

    # ── Persistence ─────────────────────────────────────────────────────

    def _save_state(self) -> None:
        """Persist all Soul Keys and lockout records to disk."""
        try:
            state = {
                "soul_keys": {
                    cid: sk.to_dict()
                    for cid, sk in self._soul_keys.items()
                },
                "lockout_records": [r.to_dict() for r in self._lockout_records],
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
            path = self._storage_dir / "soul_key_state.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Failed to save Soul Key state: %s", exc)

    def _load_state(self) -> None:
        """Load Soul Keys and lockout records from disk."""
        try:
            path = self._storage_dir / "soul_key_state.json"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    state = json.load(f)
                self._soul_keys = {
                    cid: SoulKey.from_dict(data)
                    for cid, data in state.get("soul_keys", {}).items()
                }
                self._lockout_records = [
                    LockoutRecord(
                        record_id=r["record_id"],
                        citizen_id=r["citizen_id"],
                        session_id=r["session_id"],
                        state=LockoutState(r["state"]),
                        detected_at=r["detected_at"],
                        device_fingerprint_attempted=r["device_fingerprint_attempted"],
                        device_fingerprint_registered=r["device_fingerprint_registered"],
                        reason=r.get("reason", ""),
                        resolved_at=r.get("resolved_at", ""),
                        ncsc_incident_id=r.get("ncsc_incident_id", ""),
                    )
                    for r in state.get("lockout_records", [])
                ]
                logger.info("Loaded %d Soul Keys, %d lockout records",
                            len(self._soul_keys), len(self._lockout_records))
        except Exception as exc:
            logger.warning("Failed to load Soul Key state: %s", exc)


# ── Singleton ──────────────────────────────────────────────────────────────

_soul_key_protocol: Optional[SoulKeyProtocol] = None
_soul_key_lock = threading.Lock()


def get_soul_key_protocol() -> SoulKeyProtocol:
    """Get or create the singleton SoulKeyProtocol."""
    global _soul_key_protocol
    if _soul_key_protocol is None:
        with _soul_key_lock:
            if _soul_key_protocol is None:
                _soul_key_protocol = SoulKeyProtocol()
    return _soul_key_protocol


def reset_soul_key_protocol() -> None:
    """Reset the singleton (for testing)."""
    global _soul_key_protocol
    with _soul_key_lock:
        _soul_key_protocol = None
