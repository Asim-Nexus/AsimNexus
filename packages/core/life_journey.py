#!/usr/bin/env python3
"""
STATUS: NEW — Gap 5 Implementation
ASIMNEXUS Life Journey Module
==============================
Tracks human life journey through 6 stages (Birth → Education → Work →
Family → Retirement → Inheritance). Provides stage-specific services,
transition verification, and multi-party coordination.

Integrates with:
  - [`auth/identity_provider.py`](../auth/identity_provider.py) — Identity creation at Birth stage
  - [`core/agent_contract.py`](agent_contract.py) — Contracts for Work/Family stages
  - [`security/immutable_constitution.py`](../security/immutable_constitution.py) — Rights protection
  - [`simple_backend.py`](../simple_backend.py) — Job market endpoints for Work stage
"""

import os
import time
import json
import uuid
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple

logger = logging.getLogger("AsimNexus.Core.LifeJourney")

# ─── Environment Configuration ────────────────────────────────────────────────
_LIFE_DB_PATH = os.getenv("ASIM_LIFE_DB_PATH", "data/life_journey.jsonl")


class LifeStage(str, Enum):
    """The six stages of a human life journey."""
    BIRTH = "birth"
    EDUCATION = "education"
    WORK = "work"
    FAMILY = "family"
    RETIREMENT = "retirement"
    INHERITANCE = "inheritance"


class TransitionStatus(str, Enum):
    """Result status of a stage transition attempt."""
    SUCCESS = "success"
    CRITERIA_NOT_MET = "criteria_not_met"
    VERIFICATION_FAILED = "verification_failed"
    INVALID_TRANSITION = "invalid_transition"
    ALREADY_IN_STAGE = "already_in_stage"


@dataclass
class LifeStageTransition:
    """
    Defines the rules for transitioning between life stages.

    Attributes:
        from_stage: The source stage (None for BIRTH).
        to_stage: The target stage.
        criteria: Conditions that must be true to transition.
        requires_verification: Documents/evidence needed.
        services_activated: Services that become available after transition.
    """
    from_stage: Optional[LifeStage]
    to_stage: LifeStage
    criteria: List[str] = field(default_factory=list)
    requires_verification: List[str] = field(default_factory=list)
    services_activated: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_stage": self.from_stage.value if self.from_stage else None,
            "to_stage": self.to_stage.value,
            "criteria": self.criteria,
            "requires_verification": self.requires_verification,
            "services_activated": self.services_activated,
        }


@dataclass
class TransitionRecord:
    """Record of a stage transition event."""
    id: str
    user_id: str
    from_stage: Optional[LifeStage]
    to_stage: LifeStage
    status: TransitionStatus
    criteria_met: List[str]
    criteria_failed: List[str]
    verification_provided: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "from_stage": self.from_stage.value if self.from_stage else None,
            "to_stage": self.to_stage.value,
            "status": self.status.value,
            "criteria_met": self.criteria_met,
            "criteria_failed": self.criteria_failed,
            "verification_provided": self.verification_provided,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }


# ─── Life Journey State Machine ──────────────────────────────────────────────
# Defines the valid transitions between life stages and their requirements.

LIFE_JOURNEY_MACHINE: Dict[LifeStage, LifeStageTransition] = {
    LifeStage.BIRTH: LifeStageTransition(
        from_stage=None,
        to_stage=LifeStage.BIRTH,
        criteria=["identity_created", "guardian_assigned"],
        requires_verification=["birth_certificate"],
        services_activated=[
            "identity", "healthcare", "digital_birth_certificate",
        ],
    ),
    LifeStage.EDUCATION: LifeStageTransition(
        from_stage=LifeStage.BIRTH,
        to_stage=LifeStage.EDUCATION,
        criteria=["age >= 4"],
        requires_verification=["enrollment"],
        services_activated=[
            "school", "scholarship", "learning_materials",
            "skill_assessment",
        ],
    ),
    LifeStage.WORK: LifeStageTransition(
        from_stage=LifeStage.EDUCATION,
        to_stage=LifeStage.WORK,
        criteria=["age >= 16", "skill_certification"],
        requires_verification=["employment_contract", "tax_registration"],
        services_activated=[
            "job_market", "career_tracking", "skill_development",
            "tax_management", "professional_network",
        ],
    ),
    LifeStage.FAMILY: LifeStageTransition(
        from_stage=LifeStage.WORK,
        to_stage=LifeStage.FAMILY,
        criteria=["age >= 18", "stable_income"],
        requires_verification=["partnership_registration",
                                "financial_stability"],
        services_activated=[
            "marriage", "child_registration", "family_mesh",
            "housing", "family_healthcare",
        ],
    ),
    LifeStage.RETIREMENT: LifeStageTransition(
        from_stage=LifeStage.FAMILY,
        to_stage=LifeStage.RETIREMENT,
        criteria=["age >= 60", "retirement_fund"],
        requires_verification=["pension_eligibility", "health_assessment"],
        services_activated=[
            "pension", "healthcare_senior", "succession_planning",
            "community_services",
        ],
    ),
    LifeStage.INHERITANCE: LifeStageTransition(
        from_stage=LifeStage.RETIREMENT,
        to_stage=LifeStage.INHERITANCE,
        criteria=["will_exists", "heirs_identified"],
        requires_verification=["legal_will", "asset_inventory",
                                "heir_consent"],
        services_activated=[
            "will_execution", "asset_transfer", "legacy_management",
            "memorial",
        ],
    ),
}

# Reverse mapping: which transitions are valid to reach a stage
_VALID_TRANSITIONS: Dict[LifeStage, List[LifeStage]] = {
    LifeStage.BIRTH: [],
    LifeStage.EDUCATION: [LifeStage.BIRTH],
    LifeStage.WORK: [LifeStage.EDUCATION],
    LifeStage.FAMILY: [LifeStage.WORK],
    LifeStage.RETIREMENT: [LifeStage.FAMILY],
    LifeStage.INHERITANCE: [LifeStage.RETIREMENT],
}


@dataclass
class LifeProfile:
    """
    A user's complete life journey profile.

    Attributes:
        user_id: Unique user identifier.
        current_stage: The user's current life stage.
        stage_history: List of past stage transitions.
        services_active: Currently active services.
        services_completed: Services used in the past.
        completed_criteria: List of criteria that have been met.
        verification_docs: Verification documents provided.
        metadata: Additional user-specific data.
        created_at: When the profile was created.
        updated_at: Last profile update timestamp.
    """
    user_id: str
    current_stage: LifeStage = LifeStage.BIRTH
    stage_history: List[TransitionRecord] = field(default_factory=list)
    services_active: Set[str] = field(default_factory=set)
    services_completed: Set[str] = field(default_factory=set)
    completed_criteria: Set[str] = field(default_factory=set)
    verification_docs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "current_stage": self.current_stage.value,
            "stage_history": [r.to_dict() for r in self.stage_history],
            "services_active": list(self.services_active),
            "services_completed": list(self.services_completed),
            "completed_criteria": list(self.completed_criteria),
            "verification_docs": self.verification_docs,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifeProfile":
        data = dict(data)
        data["current_stage"] = LifeStage(data["current_stage"])
        data["services_active"] = set(data.get("services_active", []))
        data["services_completed"] = set(data.get("services_completed", []))
        data["completed_criteria"] = set(data.get("completed_criteria", []))
        data["stage_history"] = [
            TransitionRecord(
                id=h["id"],
                user_id=h["user_id"],
                from_stage=LifeStage(h["from_stage"]) if h.get("from_stage") else None,
                to_stage=LifeStage(h["to_stage"]),
                status=TransitionStatus(h["status"]),
                criteria_met=h.get("criteria_met", []),
                criteria_failed=h.get("criteria_failed", []),
                verification_provided=h.get("verification_provided", {}),
                timestamp=h.get("timestamp", 0.0),
                notes=h.get("notes", ""),
            )
            for h in data.get("stage_history", [])
        ]
        return cls(**data)


class LifeJourneyModule:
    """
    Life journey state machine tracking the 6 stages of human life.

    Provides:
      - Stage transitions with criteria verification
      - Service activation/deactivation per stage
      - Life profile management
      - Transition audit trail
      - Multi-party coordination hooks

    Key methods:
        [`get_current_stage()`](:TBD) — get user's current life stage
        [`transition_stage()`](:TBD) — attempt stage transition
        [`get_available_services()`](:TBD) — services at current stage
        [`get_life_profile()`](:TBD) — complete life profile
        [`add_verification_doc()`](:TBD) — store verification documents
        [`meet_criteria()`](:TBD) — mark criteria as completed
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._profiles: Dict[str, LifeProfile] = {}
        self._load_from_db()

        logger.info(
            f"🌱 LifeJourneyModule initialized — "
            f"{len(self._profiles)} profiles loaded"
        )

    # ─── Core API ────────────────────────────────────────────────────────────

    def get_current_stage(self, user_id: str) -> Optional[LifeStage]:
        """
        Get the current life stage for a user.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The user's current LifeStage, or None if profile doesn't exist.
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            return profile.current_stage if profile else None

    def get_life_stage_info(self, stage: LifeStage) -> LifeStageTransition:
        """
        Get the transition definition for a life stage.

        Args:
            stage: The life stage to query.

        Returns:
            The LifeStageTransition definition for that stage.
        """
        return LIFE_JOURNEY_MACHINE[stage]

    def transition_stage(self, user_id: str, to_stage: LifeStage,
                         verification: Optional[Dict[str, Any]] = None,
                         notes: str = "") -> Tuple[TransitionStatus, str]:
        """
        Attempt to transition a user to the next life stage.

        Validates:
          1. The transition is valid (from_stage → to_stage exists)
          2. All criteria are met
          3. Required verification is provided

        Args:
            user_id: The user to transition.
            to_stage: The target life stage.
            verification: Dict of verification documents provided.
            notes: Optional notes about the transition.

        Returns:
            Tuple of (TransitionStatus, message).
        """
        verification = verification or {}
        with self._lock:
            profile = self._profiles.get(user_id)

            if not profile:
                return (TransitionStatus.INVALID_TRANSITION,
                        "User profile not found. Create one first.")

            if profile.current_stage == to_stage:
                return (TransitionStatus.ALREADY_IN_STAGE,
                        f"Already in {to_stage.value} stage.")

            # Check valid transition path
            valid_from = _VALID_TRANSITIONS.get(to_stage, [])
            if profile.current_stage not in valid_from:
                return (TransitionStatus.INVALID_TRANSITION,
                        f"Cannot transition from {profile.current_stage.value} "
                        f"to {to_stage.value}.")

            transition_def = LIFE_JOURNEY_MACHINE[to_stage]

            # Check criteria
            criteria_met: List[str] = []
            criteria_failed: List[str] = []
            for criterion in transition_def.criteria:
                if criterion in profile.completed_criteria:
                    criteria_met.append(criterion)
                else:
                    criteria_failed.append(criterion)

            if criteria_failed:
                record = TransitionRecord(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    from_stage=profile.current_stage,
                    to_stage=to_stage,
                    status=TransitionStatus.CRITERIA_NOT_MET,
                    criteria_met=criteria_met,
                    criteria_failed=criteria_failed,
                    verification_provided=verification,
                    notes=notes,
                )
                profile.stage_history.append(record)
                profile.updated_at = time.time()
                self._persist_transition(user_id, record)
                return (TransitionStatus.CRITERIA_NOT_MET,
                        f"Criteria not met: {', '.join(criteria_failed)}")

            # Check verification
            missing_verification: List[str] = []
            for required in transition_def.requires_verification:
                if required not in verification and required not in profile.verification_docs:
                    missing_verification.append(required)

            if missing_verification:
                record = TransitionRecord(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    from_stage=profile.current_stage,
                    to_stage=to_stage,
                    status=TransitionStatus.VERIFICATION_FAILED,
                    criteria_met=criteria_met,
                    criteria_failed=[],
                    verification_provided=verification,
                    notes=notes,
                )
                profile.stage_history.append(record)
                profile.updated_at = time.time()
                self._persist_transition(user_id, record)
                return (TransitionStatus.VERIFICATION_FAILED,
                        f"Missing verification: {', '.join(missing_verification)}")

            # Perform transition
            old_stage = profile.current_stage
            profile.current_stage = to_stage

            # Deactivate old stage services (move to completed)
            old_transition = LIFE_JOURNEY_MACHINE.get(old_stage)
            if old_transition:
                for service in old_transition.services_activated:
                    profile.services_active.discard(service)
                    profile.services_completed.add(service)

            # Activate new stage services
            for service in transition_def.services_activated:
                profile.services_active.add(service)

            # Store verification docs
            profile.verification_docs.update(verification)

            record = TransitionRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                from_stage=old_stage,
                to_stage=to_stage,
                status=TransitionStatus.SUCCESS,
                criteria_met=criteria_met,
                criteria_failed=[],
                verification_provided=verification,
                notes=notes,
            )
            profile.stage_history.append(record)
            profile.updated_at = time.time()
            self._persist_profile(profile)
            self._persist_transition(user_id, record)

            logger.info(
                f"🔄 Life stage transition: {user_id[:8]}... "
                f"{old_stage.value} → {to_stage.value}"
            )
            return (TransitionStatus.SUCCESS,
                    f"Transitioned to {to_stage.value} stage.")

    def get_available_services(self, user_id: str) -> List[str]:
        """
        Get services available at the user's current stage.

        Args:
            user_id: The user to query.

        Returns:
            List of service identifiers available at the current stage.
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            if not profile:
                # New users get BIRTH stage services
                return list(LIFE_JOURNEY_MACHINE[LifeStage.BIRTH].services_activated)
            return list(profile.services_active)

    def get_life_profile(self, user_id: str) -> Optional[LifeProfile]:
        """
        Get the complete life journey profile for a user.

        Args:
            user_id: The user to query.

        Returns:
            LifeProfile if it exists, None otherwise.
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            if profile:
                return profile
            return None

    def create_profile(self, user_id: str,
                       metadata: Optional[Dict[str, Any]] = None) -> LifeProfile:
        """
        Create a new life journey profile for a user.

        Starts at BIRTH stage with default services.

        Args:
            user_id: The user's unique identifier.
            metadata: Optional initial metadata.

        Returns:
            The newly created LifeProfile.

        Raises:
            ValueError: If user already has a profile.
        """
        with self._lock:
            if user_id in self._profiles:
                raise ValueError(f"User {user_id[:8]}... already has a life profile.")

            birth_def = LIFE_JOURNEY_MACHINE[LifeStage.BIRTH]
            profile = LifeProfile(
                user_id=user_id,
                current_stage=LifeStage.BIRTH,
                services_active=set(birth_def.services_activated),
                metadata=metadata or {},
            )
            self._profiles[user_id] = profile
            self._persist_profile(profile)

            logger.info(f"🌟 Life profile created for {user_id[:8]}...")
            return profile

    def add_verification_doc(self, user_id: str,
                             doc_type: str,
                             doc_data: Any) -> bool:
        """
        Store a verification document for a user.

        Args:
            user_id: The user.
            doc_type: Document type (e.g., "birth_certificate").
            doc_data: Document data (dict, string, etc.).

        Returns:
            True if document was stored successfully.
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            if not profile:
                return False
            profile.verification_docs[doc_type] = doc_data
            profile.updated_at = time.time()
            self._persist_profile(profile)
            return True

    def meet_criteria(self, user_id: str, criterion: str) -> bool:
        """
        Mark a criterion as completed for a user.

        Args:
            user_id: The user.
            criterion: The criterion identifier (e.g., "age >= 16").

        Returns:
            True if criterion was added successfully.
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            if not profile:
                return False
            if criterion not in profile.completed_criteria:
                profile.completed_criteria.add(criterion)
                profile.updated_at = time.time()
                self._persist_profile(profile)
            return True

    def get_transition_history(self, user_id: str) -> List[TransitionRecord]:
        """
        Get the transition history for a user.

        Args:
            user_id: The user to query.

        Returns:
            List of TransitionRecords, most recent first.
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            if not profile:
                return []
            return list(reversed(profile.stage_history))

    def get_valid_transitions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get valid next stages for a user, with their requirements.

        Args:
            user_id: The user to query.

        Returns:
            List of dicts with "to_stage", "criteria", "requires_verification".
        """
        with self._lock:
            profile = self._profiles.get(user_id)
            if not profile:
                # Only BIRTH is valid for new users
                birth_def = LIFE_JOURNEY_MACHINE[LifeStage.BIRTH]
                return [{
                    "to_stage": LifeStage.BIRTH.value,
                    "criteria": birth_def.criteria,
                    "requires_verification": birth_def.requires_verification,
                    "services_activated": birth_def.services_activated,
                }]

            current = profile.current_stage
            valid: List[Dict[str, Any]] = []

            for stage, transition in LIFE_JOURNEY_MACHINE.items():
                valid_from = _VALID_TRANSITIONS.get(stage, [])
                if current in valid_from:
                    valid.append({
                        "to_stage": stage.value,
                        "criteria": transition.criteria,
                        "requires_verification": transition.requires_verification,
                        "services_activated": transition.services_activated,
                    })

            return valid

    def get_stats(self) -> Dict[str, Any]:
        """Get life journey module statistics."""
        with self._lock:
            stage_counts: Dict[str, int] = {}
            for profile in self._profiles.values():
                stage = profile.current_stage.value
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

            total_transitions = sum(
                len(p.stage_history) for p in self._profiles.values()
            )

            return {
                "total_profiles": len(self._profiles),
                "stage_distribution": stage_counts,
                "total_transitions": total_transitions,
                "stages_defined": len(LIFE_JOURNEY_MACHINE),
            }

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _persist_profile(self, profile: LifeProfile) -> None:
        """Append profile state to JSONL."""
        try:
            os.makedirs(os.path.dirname(_LIFE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "profile",
                "user_id": profile.user_id,
                "data": profile.to_dict(),
                "timestamp": time.time(),
            }
            with open(_LIFE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist life profile: {e}")

    def _persist_transition(self, user_id: str,
                            record: TransitionRecord) -> None:
        """Append transition record to JSONL."""
        try:
            os.makedirs(os.path.dirname(_LIFE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "transition",
                "user_id": user_id,
                "data": record.to_dict(),
                "timestamp": time.time(),
            }
            with open(_LIFE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist transition: {e}")

    def _load_from_db(self) -> None:
        """Load profiles from persistent storage."""
        try:
            path = _LIFE_DB_PATH
            if not os.path.exists(path):
                return

            latest_profiles: Dict[str, LifeProfile] = {}

            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("_type") == "profile":
                            uid = entry["user_id"]
                            profile = LifeProfile.from_dict(entry["data"])
                            latest_profiles[uid] = profile
                    except (json.JSONDecodeError, KeyError):
                        continue

            self._profiles = latest_profiles
            logger.info(
                f"📂 Loaded {len(latest_profiles)} life profiles from DB"
            )
        except Exception as e:
            logger.warning(f"Failed to load life profiles: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_life_journey_instance: Optional[LifeJourneyModule] = None
_life_journey_lock = threading.Lock()


def get_life_journey_module() -> LifeJourneyModule:
    """
    Get or create the singleton LifeJourneyModule instance.

    Usage:
        ```python
        ljm = get_life_journey_module()
        stage = ljm.get_current_stage("user_001")
        services = ljm.get_available_services("user_001")
        ```
    """
    global _life_journey_instance
    if _life_journey_instance is None:
        with _life_journey_lock:
            if _life_journey_instance is None:
                _life_journey_instance = LifeJourneyModule()
    return _life_journey_instance


def reset_life_journey_module() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _life_journey_instance
    with _life_journey_lock:
        _life_journey_instance = None
    try:
        from pathlib import Path
        p = Path(_LIFE_DB_PATH)
        if p.exists():
            p.unlink()
    except Exception:
        pass


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "LifeStage",
    "TransitionStatus",
    "LifeStageTransition",
    "TransitionRecord",
    "LifeProfile",
    "LifeJourneyModule",
    "LIFE_JOURNEY_MACHINE",
    "get_life_journey_module",
    "reset_life_journey_module",
]
