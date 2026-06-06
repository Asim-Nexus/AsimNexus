#!/usr/bin/env python3
"""
Tests for [`core/life_journey.py`](../../core/life_journey.py) — Gap 5: Life Journey Module.

Covers:
  - Enums: LifeStage (6 values), TransitionStatus (5 values)
  - Dataclasses: LifeStageTransition, TransitionRecord, LifeProfile
  - LifeJourneyModule: profiles, transitions, services, criteria, verification
  - Singleton factory pattern
  - Persistence (JSONL round-trip)
  - Edge cases, full lifecycle, module exports
"""

import os
import time
import json
import uuid
import pytest
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from core.life_journey import (
    LifeStage,
    TransitionStatus,
    LifeStageTransition,
    TransitionRecord,
    LifeProfile,
    LifeJourneyModule,
    LIFE_JOURNEY_MACHINE,
    get_life_journey_module,
    reset_life_journey_module,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_system():
    """Reset singleton and clean DB before each test."""
    reset_life_journey_module()
    yield
    reset_life_journey_module()


@pytest.fixture
def module():
    """Fresh LifeJourneyModule instance."""
    return LifeJourneyModule()


@pytest.fixture
def sample_user() -> str:
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def profile(module, sample_user) -> LifeProfile:
    """Create a profile at BIRTH stage."""
    return module.create_profile(sample_user, metadata={"region": "test"})


# ══════════════════════════════════════════════════════════════════════════════
# Test: LifeStage Enum
# ══════════════════════════════════════════════════════════════════════════════

class TestLifeStage:
    """All 6 life stages exist with correct string values."""

    def test_values(self):
        assert LifeStage.BIRTH.value == "birth"
        assert LifeStage.EDUCATION.value == "education"
        assert LifeStage.WORK.value == "work"
        assert LifeStage.FAMILY.value == "family"
        assert LifeStage.RETIREMENT.value == "retirement"
        assert LifeStage.INHERITANCE.value == "inheritance"

    def test_all_stages_defined(self):
        assert len(LifeStage) == 6


# ══════════════════════════════════════════════════════════════════════════════
# Test: TransitionStatus Enum
# ══════════════════════════════════════════════════════════════════════════════

class TestTransitionStatus:
    """All 5 transition statuses exist."""

    def test_values(self):
        assert TransitionStatus.SUCCESS.value == "success"
        assert TransitionStatus.CRITERIA_NOT_MET.value == "criteria_not_met"
        assert TransitionStatus.VERIFICATION_FAILED.value == "verification_failed"
        assert TransitionStatus.INVALID_TRANSITION.value == "invalid_transition"
        assert TransitionStatus.ALREADY_IN_STAGE.value == "already_in_stage"

    def test_all_statuses(self):
        assert len(TransitionStatus) == 5


# ══════════════════════════════════════════════════════════════════════════════
# Test: LifeStageTransition Dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestLifeStageTransition:
    """LifeStageTransition construction and serialization."""

    def test_create_with_defaults(self):
        t = LifeStageTransition(from_stage=LifeStage.BIRTH, to_stage=LifeStage.EDUCATION)
        assert t.from_stage == LifeStage.BIRTH
        assert t.to_stage == LifeStage.EDUCATION
        assert t.criteria == []
        assert t.requires_verification == []
        assert t.services_activated == []

    def test_create_full(self):
        t = LifeStageTransition(
            from_stage=LifeStage.BIRTH,
            to_stage=LifeStage.EDUCATION,
            criteria=["age >= 4"],
            requires_verification=["enrollment"],
            services_activated=["school", "scholarship"],
        )
        assert "age >= 4" in t.criteria
        assert "enrollment" in t.requires_verification
        assert "school" in t.services_activated

    def test_to_dict(self):
        t = LifeStageTransition(
            from_stage=LifeStage.BIRTH,
            to_stage=LifeStage.EDUCATION,
            criteria=["age >= 4"],
            requires_verification=["enrollment"],
            services_activated=["school"],
        )
        d = t.to_dict()
        assert d["from_stage"] == "birth"
        assert d["to_stage"] == "education"
        assert d["criteria"] == ["age >= 4"]
        assert d["requires_verification"] == ["enrollment"]
        assert d["services_activated"] == ["school"]

    def test_to_dict_from_none(self):
        t = LifeStageTransition(from_stage=None, to_stage=LifeStage.BIRTH)
        d = t.to_dict()
        assert d["from_stage"] is None
        assert d["to_stage"] == "birth"


# ══════════════════════════════════════════════════════════════════════════════
# Test: TransitionRecord Dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestTransitionRecord:
    """TransitionRecord construction and serialization."""

    def test_create_with_defaults(self, sample_user):
        r = TransitionRecord(
            id="rec_001",
            user_id=sample_user,
            from_stage=LifeStage.BIRTH,
            to_stage=LifeStage.EDUCATION,
            status=TransitionStatus.SUCCESS,
            criteria_met=["age >= 4"],
            criteria_failed=[],
            verification_provided={},
        )
        assert r.id == "rec_001"
        assert r.user_id == sample_user
        assert r.from_stage == LifeStage.BIRTH
        assert r.to_stage == LifeStage.EDUCATION
        assert r.status == TransitionStatus.SUCCESS
        assert r.notes == ""
        assert isinstance(r.timestamp, float)

    def test_to_dict(self, sample_user):
        r = TransitionRecord(
            id="rec_001",
            user_id=sample_user,
            from_stage=LifeStage.BIRTH,
            to_stage=LifeStage.EDUCATION,
            status=TransitionStatus.SUCCESS,
            criteria_met=["age >= 4"],
            criteria_failed=[],
            verification_provided={"enrollment": "doc_123"},
            notes="First transition",
        )
        d = r.to_dict()
        assert d["id"] == "rec_001"
        assert d["from_stage"] == "birth"
        assert d["to_stage"] == "education"
        assert d["status"] == "success"
        assert d["verification_provided"]["enrollment"] == "doc_123"
        assert d["notes"] == "First transition"

    def test_to_dict_from_stage_none(self, sample_user):
        r = TransitionRecord(
            id="rec_002",
            user_id=sample_user,
            from_stage=None,
            to_stage=LifeStage.BIRTH,
            status=TransitionStatus.SUCCESS,
            criteria_met=[],
            criteria_failed=[],
            verification_provided={},
        )
        d = r.to_dict()
        assert d["from_stage"] is None


# ══════════════════════════════════════════════════════════════════════════════
# Test: LifeProfile Dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestLifeProfile:
    """LifeProfile creation, defaults, serialization."""

    def test_default_stage(self, sample_user):
        p = LifeProfile(user_id=sample_user)
        assert p.user_id == sample_user
        assert p.current_stage == LifeStage.BIRTH
        assert p.services_active == set()
        assert p.services_completed == set()
        assert p.completed_criteria == set()
        assert p.verification_docs == {}

    def test_to_dict(self, sample_user):
        p = LifeProfile(
            user_id=sample_user,
            current_stage=LifeStage.WORK,
            services_active={"job_market", "career_tracking"},
            completed_criteria={"age >= 16", "skill_certification"},
        )
        d = p.to_dict()
        assert d["user_id"] == sample_user
        assert d["current_stage"] == "work"
        assert "job_market" in d["services_active"]
        assert "age >= 16" in d["completed_criteria"]
        assert d["stage_history"] == []

    def test_from_dict(self, sample_user):
        original = LifeProfile(
            user_id=sample_user,
            current_stage=LifeStage.FAMILY,
            services_active={"marriage", "housing"},
            completed_criteria={"age >= 18"},
            verification_docs={"partnership": "doc_001"},
            metadata={"region": "test"},
        )
        d = original.to_dict()
        restored = LifeProfile.from_dict(d)
        assert restored.user_id == sample_user
        assert restored.current_stage == LifeStage.FAMILY
        assert "marriage" in restored.services_active
        assert "age >= 18" in restored.completed_criteria
        assert restored.verification_docs["partnership"] == "doc_001"
        assert restored.metadata["region"] == "test"

    def test_from_dict_with_history(self, sample_user):
        record = TransitionRecord(
            id="rec_001",
            user_id=sample_user,
            from_stage=LifeStage.BIRTH,
            to_stage=LifeStage.EDUCATION,
            status=TransitionStatus.SUCCESS,
            criteria_met=["age >= 4"],
            criteria_failed=[],
            verification_provided={"enrollment": "doc_001"},
        )
        p = LifeProfile(
            user_id=sample_user,
            current_stage=LifeStage.EDUCATION,
            stage_history=[record],
            services_active={"school"},
            completed_criteria={"age >= 4"},
        )
        d = p.to_dict()
        restored = LifeProfile.from_dict(d)
        assert len(restored.stage_history) == 1
        assert restored.stage_history[0].to_stage == LifeStage.EDUCATION
        assert restored.stage_history[0].status == TransitionStatus.SUCCESS


# ══════════════════════════════════════════════════════════════════════════════
# Test: LIFE_JOURNEY_MACHINE
# ══════════════════════════════════════════════════════════════════════════════

class TestLifeJourneyMachine:
    """The state machine has all 6 stages with correct transitions."""

    def test_all_stages_defined(self):
        assert len(LIFE_JOURNEY_MACHINE) == 6

    def test_birth_transition(self):
        t = LIFE_JOURNEY_MACHINE[LifeStage.BIRTH]
        assert t.from_stage is None
        assert t.to_stage == LifeStage.BIRTH
        assert "identity_created" in t.criteria
        assert "guardian_assigned" in t.criteria
        assert "birth_certificate" in t.requires_verification
        assert "identity" in t.services_activated
        assert "healthcare" in t.services_activated

    def test_education_transition(self):
        t = LIFE_JOURNEY_MACHINE[LifeStage.EDUCATION]
        assert t.from_stage == LifeStage.BIRTH
        assert t.to_stage == LifeStage.EDUCATION
        assert "age >= 4" in t.criteria
        assert "enrollment" in t.requires_verification
        assert "school" in t.services_activated

    def test_work_transition(self):
        t = LIFE_JOURNEY_MACHINE[LifeStage.WORK]
        assert t.from_stage == LifeStage.EDUCATION
        assert t.to_stage == LifeStage.WORK
        assert "age >= 16" in t.criteria
        assert "skill_certification" in t.criteria
        assert "employment_contract" in t.requires_verification
        assert "job_market" in t.services_activated

    def test_family_transition(self):
        t = LIFE_JOURNEY_MACHINE[LifeStage.FAMILY]
        assert t.from_stage == LifeStage.WORK
        assert t.to_stage == LifeStage.FAMILY
        assert "age >= 18" in t.criteria
        assert "stable_income" in t.criteria
        assert "marriage" in t.services_activated
        assert "family_mesh" in t.services_activated

    def test_retirement_transition(self):
        t = LIFE_JOURNEY_MACHINE[LifeStage.RETIREMENT]
        assert t.from_stage == LifeStage.FAMILY
        assert t.to_stage == LifeStage.RETIREMENT
        assert "age >= 60" in t.criteria
        assert "retirement_fund" in t.criteria
        assert "pension" in t.services_activated

    def test_inheritance_transition(self):
        t = LIFE_JOURNEY_MACHINE[LifeStage.INHERITANCE]
        assert t.from_stage == LifeStage.RETIREMENT
        assert t.to_stage == LifeStage.INHERITANCE
        assert "will_exists" in t.criteria
        assert "heirs_identified" in t.criteria
        assert "legal_will" in t.requires_verification
        assert "will_execution" in t.services_activated


# ══════════════════════════════════════════════════════════════════════════════
# Test: LifeJourneyModule — Initialization
# ══════════════════════════════════════════════════════════════════════════════

class TestLifeJourneyModuleInit:
    """Module initializes with empty profiles."""

    def test_init_empty(self, module):
        stats = module.get_stats()
        assert stats["total_profiles"] == 0
        assert stats["total_transitions"] == 0
        assert stats["stages_defined"] == 6

    def test_get_current_stage_no_profile(self, module, sample_user):
        assert module.get_current_stage(sample_user) is None

    def test_get_life_stage_info(self, module):
        info = module.get_life_stage_info(LifeStage.BIRTH)
        assert info.to_stage == LifeStage.BIRTH
        assert info.from_stage is None

        info = module.get_life_stage_info(LifeStage.WORK)
        assert info.to_stage == LifeStage.WORK
        assert "age >= 16" in info.criteria


# ══════════════════════════════════════════════════════════════════════════════
# Test: create_profile
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateProfile:
    """Profile creation starts at BIRTH with default services."""

    def test_create_profile(self, module, sample_user):
        p = module.create_profile(sample_user)
        assert p.user_id == sample_user
        assert p.current_stage == LifeStage.BIRTH
        assert "identity" in p.services_active
        assert "healthcare" in p.services_active
        assert "digital_birth_certificate" in p.services_active

    def test_create_profile_with_metadata(self, module, sample_user):
        p = module.create_profile(sample_user, metadata={"region": "asia", "lang": "ne"})
        assert p.metadata["region"] == "asia"
        assert p.metadata["lang"] == "ne"

    def test_create_profile_duplicate(self, module, sample_user):
        module.create_profile(sample_user)
        with pytest.raises(ValueError, match="already has a life profile"):
            module.create_profile(sample_user)

    def test_create_profile_stores_in_module(self, module, sample_user):
        module.create_profile(sample_user)
        assert module.get_current_stage(sample_user) == LifeStage.BIRTH

    def test_create_profile_sets_created_at(self, module, sample_user):
        before = time.time()
        p = module.create_profile(sample_user)
        after = time.time()
        assert before <= p.created_at <= after


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_current_stage
# ══════════════════════════════════════════════════════════════════════════════

class TestGetCurrentStage:
    """Query user's current life stage."""

    def test_returns_stage(self, module, profile, sample_user):
        stage = module.get_current_stage(sample_user)
        assert stage == LifeStage.BIRTH

    def test_returns_none_for_unknown(self, module):
        assert module.get_current_stage("nonexistent_user") is None


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_available_services
# ══════════════════════════════════════════════════════════════════════════════

class TestGetAvailableServices:
    """Services returned match the user's current stage."""

    def test_birth_services(self, module, profile, sample_user):
        services = module.get_available_services(sample_user)
        assert "identity" in services
        assert "healthcare" in services
        assert "digital_birth_certificate" in services
        assert len(services) == 3

    def test_new_user_gets_birth_services(self, module, sample_user):
        """Even without a profile, new users get BIRTH stage defaults."""
        services = module.get_available_services(sample_user)
        assert "identity" in services
        assert "healthcare" in services

    def test_services_update_after_transition(self, module, profile, sample_user):
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "enrolled")
        status, _ = module.transition_stage(sample_user, LifeStage.EDUCATION)

        services = module.get_available_services(sample_user)
        assert status == TransitionStatus.SUCCESS
        assert "identity" not in services  # deactivated
        assert "healthcare" not in services  # deactivated
        assert "school" in services
        assert "scholarship" in services


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_life_profile
# ══════════════════════════════════════════════════════════════════════════════

class TestGetLifeProfile:
    """Retrieve complete LifeProfile."""

    def test_returns_profile(self, module, profile, sample_user):
        p = module.get_life_profile(sample_user)
        assert p is not None
        assert p.user_id == sample_user
        assert p.current_stage == LifeStage.BIRTH

    def test_returns_none_for_unknown(self, module):
        assert module.get_life_profile("nonexistent") is None

    def test_profile_is_mutable(self, module, profile, sample_user):
        p = module.get_life_profile(sample_user)
        assert p is profile  # same object reference


# ══════════════════════════════════════════════════════════════════════════════
# Test: transition_stage
# ══════════════════════════════════════════════════════════════════════════════

class TestTransitionStage:
    """Stage transitions with criteria and verification."""

    def test_no_profile(self, module, sample_user):
        status, msg = module.transition_stage(sample_user, LifeStage.EDUCATION)
        assert status == TransitionStatus.INVALID_TRANSITION
        assert "profile not found" in msg.lower()

    def test_already_in_stage(self, module, profile, sample_user):
        status, msg = module.transition_stage(sample_user, LifeStage.BIRTH)
        assert status == TransitionStatus.ALREADY_IN_STAGE
        assert "already in birth stage" in msg.lower()

    def test_invalid_transition_skip(self, module, profile, sample_user):
        """Cannot go from BIRTH directly to WORK."""
        status, msg = module.transition_stage(sample_user, LifeStage.WORK)
        assert status == TransitionStatus.INVALID_TRANSITION
        assert "Cannot transition from birth to work" in msg

    def test_criteria_not_met(self, module, profile, sample_user):
        """Missing criteria blocks transition."""
        status, msg = module.transition_stage(sample_user, LifeStage.EDUCATION)
        assert status == TransitionStatus.CRITERIA_NOT_MET
        assert "age >= 4" in msg

    def test_verification_failed(self, module, profile, sample_user):
        """Criteria met but missing verification."""
        module.meet_criteria(sample_user, "age >= 4")
        status, msg = module.transition_stage(sample_user, LifeStage.EDUCATION)
        assert status == TransitionStatus.VERIFICATION_FAILED
        assert "enrollment" in msg

    def test_successful_transition(self, module, profile, sample_user):
        """BIRTH -> EDUCATION with criteria and verification."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc_123")
        status, msg = module.transition_stage(
            sample_user, LifeStage.EDUCATION,
            notes="Starting school",
        )
        assert status == TransitionStatus.SUCCESS
        assert "education" in msg.lower()
        assert module.get_current_stage(sample_user) == LifeStage.EDUCATION

    def test_transition_verification_inline(self, module, profile, sample_user):
        """Verification can be passed inline instead of pre-stored."""
        module.meet_criteria(sample_user, "age >= 4")
        status, msg = module.transition_stage(
            sample_user, LifeStage.EDUCATION,
            verification={"enrollment": "doc_456"},
        )
        assert status == TransitionStatus.SUCCESS

    def test_services_deactivated_on_transition(self, module, profile, sample_user):
        """Old stage services moved to completed after transition."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        p = module.get_life_profile(sample_user)
        assert "identity" not in p.services_active
        assert "healthcare" not in p.services_active
        assert "identity" in p.services_completed
        assert "school" in p.services_active

    def test_transition_record_created(self, module, profile, sample_user):
        """Successful transition creates audit trail."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        history = module.get_transition_history(sample_user)
        assert len(history) >= 1
        assert history[0].to_stage == LifeStage.EDUCATION
        assert history[0].status == TransitionStatus.SUCCESS
        assert "age >= 4" in history[0].criteria_met

    def test_failed_transition_records_audit(self, module, profile, sample_user):
        """Failed transitions also create audit records."""
        module.transition_stage(sample_user, LifeStage.EDUCATION)
        history = module.get_transition_history(sample_user)
        assert len(history) >= 1
        assert history[0].status == TransitionStatus.CRITERIA_NOT_MET

    def test_chain_education_to_work(self, module, profile, sample_user):
        """Full chain: BIRTH -> EDUCATION -> WORK."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        module.meet_criteria(sample_user, "age >= 16")
        module.meet_criteria(sample_user, "skill_certification")
        module.add_verification_doc(sample_user, "employment_contract", "doc")
        module.add_verification_doc(sample_user, "tax_registration", "doc")
        status, msg = module.transition_stage(sample_user, LifeStage.WORK)
        assert status == TransitionStatus.SUCCESS
        assert module.get_current_stage(sample_user) == LifeStage.WORK


# ══════════════════════════════════════════════════════════════════════════════
# Test: add_verification_doc
# ══════════════════════════════════════════════════════════════════════════════

class TestAddVerificationDoc:
    """Verification document storage."""

    def test_add_doc(self, module, profile, sample_user):
        result = module.add_verification_doc(sample_user, "birth_certificate",
                                              {"number": "BC-001", "issued": "2024-01-01"})
        assert result is True
        p = module.get_life_profile(sample_user)
        assert p.verification_docs["birth_certificate"]["number"] == "BC-001"

    def test_add_doc_no_profile(self, module, sample_user):
        result = module.add_verification_doc(sample_user, "test", "data")
        assert result is False

    def test_overwrite_doc(self, module, profile, sample_user):
        module.add_verification_doc(sample_user, "test_doc", "v1")
        module.add_verification_doc(sample_user, "test_doc", "v2")
        p = module.get_life_profile(sample_user)
        assert p.verification_docs["test_doc"] == "v2"


# ══════════════════════════════════════════════════════════════════════════════
# Test: meet_criteria
# ══════════════════════════════════════════════════════════════════════════════

class TestMeetCriteria:
    """Criteria completion tracking."""

    def test_meet_criteria(self, module, profile, sample_user):
        result = module.meet_criteria(sample_user, "age >= 4")
        assert result is True
        p = module.get_life_profile(sample_user)
        assert "age >= 4" in p.completed_criteria

    def test_meet_criteria_no_duplicate(self, module, profile, sample_user):
        module.meet_criteria(sample_user, "age >= 4")
        module.meet_criteria(sample_user, "age >= 4")
        p = module.get_life_profile(sample_user)
        assert len(p.completed_criteria) == 1

    def test_meet_criteria_no_profile(self, module, sample_user):
        result = module.meet_criteria(sample_user, "test")
        assert result is False


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_transition_history
# ══════════════════════════════════════════════════════════════════════════════

class TestGetTransitionHistory:
    """Transition history is ordered most-recent-first."""

    def test_empty_history(self, module, sample_user):
        assert module.get_transition_history(sample_user) == []

    def test_history_order(self, module, profile, sample_user):
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        history = module.get_transition_history(sample_user)
        assert len(history) >= 1
        assert history[0].to_stage == LifeStage.EDUCATION

        module.meet_criteria(sample_user, "age >= 16")
        module.meet_criteria(sample_user, "skill_certification")
        module.add_verification_doc(sample_user, "employment_contract", "doc")
        module.add_verification_doc(sample_user, "tax_registration", "doc")
        module.transition_stage(sample_user, LifeStage.WORK)

        history = module.get_transition_history(sample_user)
        assert len(history) >= 2
        # Most recent first
        assert history[0].to_stage == LifeStage.WORK
        assert history[1].to_stage == LifeStage.EDUCATION


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_valid_transitions
# ══════════════════════════════════════════════════════════════════════════════

class TestGetValidTransitions:
    """Valid next stages returned with requirements."""

    def test_new_user_only_birth(self, module, sample_user):
        """Users without a profile can only get BIRTH."""
        valid = module.get_valid_transitions(sample_user)
        assert len(valid) == 1
        assert valid[0]["to_stage"] == "birth"
        assert "identity_created" in valid[0]["criteria"]

    def test_birth_to_education(self, module, profile, sample_user):
        valid = module.get_valid_transitions(sample_user)
        assert len(valid) == 1
        assert valid[0]["to_stage"] == "education"

    def test_after_education(self, module, profile, sample_user):
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        valid = module.get_valid_transitions(sample_user)
        assert len(valid) == 1
        assert valid[0]["to_stage"] == "work"
        assert "age >= 16" in valid[0]["criteria"]
        assert "employment_contract" in valid[0]["requires_verification"]

    def test_middle_stage_valid_transitions(self, module, profile, sample_user):
        """Advance to WORK and check FAMILY is the only valid next."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        module.meet_criteria(sample_user, "age >= 16")
        module.meet_criteria(sample_user, "skill_certification")
        module.add_verification_doc(sample_user, "employment_contract", "doc")
        module.add_verification_doc(sample_user, "tax_registration", "doc")
        module.transition_stage(sample_user, LifeStage.WORK)

        valid = module.get_valid_transitions(sample_user)
        assert len(valid) == 1
        assert valid[0]["to_stage"] == "family"


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_stats
# ══════════════════════════════════════════════════════════════════════════════

class TestGetStats:
    """Module statistics."""

    def test_empty_stats(self, module):
        stats = module.get_stats()
        assert stats["total_profiles"] == 0
        assert stats["total_transitions"] == 0
        assert stats["stages_defined"] == 6
        assert stats["stage_distribution"] == {}

    def test_stats_with_profiles(self, module, sample_user):
        module.create_profile(sample_user)
        stats = module.get_stats()
        assert stats["total_profiles"] == 1
        assert stats["stage_distribution"]["birth"] == 1

    def test_stats_with_transitions(self, module, profile, sample_user):
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        stats = module.get_stats()
        assert stats["total_profiles"] == 1
        assert stats["stage_distribution"]["education"] == 1
        assert stats["total_transitions"] >= 1  # includes failed attempts


# ══════════════════════════════════════════════════════════════════════════════
# Test: Singleton Factory
# ══════════════════════════════════════════════════════════════════════════════

class TestSingletonFactory:
    """Singleton get/reset pattern."""

    def test_singleton_returns_same_instance(self):
        m1 = get_life_journey_module()
        m2 = get_life_journey_module()
        assert m1 is m2

    def test_reset_creates_new_instance(self):
        m1 = get_life_journey_module()
        reset_life_journey_module()
        m2 = get_life_journey_module()
        assert m1 is not m2

    def test_singleton_preserves_state(self):
        m1 = get_life_journey_module()
        m1.create_profile("singleton_user")
        assert m1.get_current_stage("singleton_user") == LifeStage.BIRTH

        m2 = get_life_journey_module()
        assert m2.get_current_stage("singleton_user") == LifeStage.BIRTH

    def test_reset_clears_state(self):
        m1 = get_life_journey_module()
        m1.create_profile("reset_user")
        reset_life_journey_module()
        m2 = get_life_journey_module()
        assert m2.get_current_stage("reset_user") is None


# ══════════════════════════════════════════════════════════════════════════════
# Test: Persistence
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistence:
    """JSONL persistence round-trip."""

    def test_profile_persisted_to_db(self, module, sample_user):
        module.create_profile(sample_user)
        db_path = "data/life_journey.jsonl"
        assert os.path.exists(db_path)
        with open(db_path, encoding="utf-8") as f:
            lines = f.readlines()
        profile_lines = [l for l in lines if '"profile"' in l]
        assert len(profile_lines) >= 1

    def test_transition_persisted(self, module, profile, sample_user):
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        db_path = "data/life_journey.jsonl"
        with open(db_path, encoding="utf-8") as f:
            lines = f.readlines()
        transition_lines = [l for l in lines if '"transition"' in l]
        assert len(transition_lines) >= 1

    def test_load_from_db_on_restart(self, module, profile, sample_user):
        """After reset+reinit, profiles are reloaded from DB."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        # Simulate restart
        new_module = LifeJourneyModule()
        stage = new_module.get_current_stage(sample_user)
        assert stage == LifeStage.EDUCATION
        assert "school" in new_module.get_available_services(sample_user)

    def test_verification_docs_persisted(self, module, profile, sample_user):
        module.add_verification_doc(sample_user, "birth_certificate", {"num": "BC-001"})

        new_module = LifeJourneyModule()
        p = new_module.get_life_profile(sample_user)
        assert p.verification_docs["birth_certificate"]["num"] == "BC-001"


# ══════════════════════════════════════════════════════════════════════════════
# Test: Module Exports
# ══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        from core import life_journey as lj
        for name in lj.__all__:
            assert hasattr(lj, name), f"{name} not found in module"

    def test_all_exports_are_importable(self):
        from core.life_journey import (
            LifeStage,
            TransitionStatus,
            LifeStageTransition,
            TransitionRecord,
            LifeProfile,
            LifeJourneyModule,
            LIFE_JOURNEY_MACHINE,
            get_life_journey_module,
            reset_life_journey_module,
        )
        assert LifeStage is not None
        assert TransitionStatus is not None
        assert LifeStageTransition is not None
        assert TransitionRecord is not None
        assert LifeProfile is not None
        assert LifeJourneyModule is not None
        assert len(LIFE_JOURNEY_MACHINE) == 6
        assert callable(get_life_journey_module)
        assert callable(reset_life_journey_module)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Boundary and unusual conditions."""

    def test_full_lifecycle(self, module, sample_user):
        """BIRTH -> EDUCATION -> WORK -> FAMILY -> RETIREMENT -> INHERITANCE."""
        p = module.create_profile(sample_user)
        assert p.current_stage == LifeStage.BIRTH

        # BIRTH -> EDUCATION
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "enrolled")
        module.transition_stage(sample_user, LifeStage.EDUCATION)
        assert module.get_current_stage(sample_user) == LifeStage.EDUCATION

        # EDUCATION -> WORK
        module.meet_criteria(sample_user, "age >= 16")
        module.meet_criteria(sample_user, "skill_certification")
        module.add_verification_doc(sample_user, "employment_contract", "hired")
        module.add_verification_doc(sample_user, "tax_registration", "registered")
        module.transition_stage(sample_user, LifeStage.WORK)
        assert module.get_current_stage(sample_user) == LifeStage.WORK

        # WORK -> FAMILY
        module.meet_criteria(sample_user, "age >= 18")
        module.meet_criteria(sample_user, "stable_income")
        module.add_verification_doc(sample_user, "partnership_registration", "partnered")
        module.add_verification_doc(sample_user, "financial_stability", "stable")
        module.transition_stage(sample_user, LifeStage.FAMILY)
        assert module.get_current_stage(sample_user) == LifeStage.FAMILY

        # FAMILY -> RETIREMENT
        module.meet_criteria(sample_user, "age >= 60")
        module.meet_criteria(sample_user, "retirement_fund")
        module.add_verification_doc(sample_user, "pension_eligibility", "eligible")
        module.add_verification_doc(sample_user, "health_assessment", "healthy")
        module.transition_stage(sample_user, LifeStage.RETIREMENT)
        assert module.get_current_stage(sample_user) == LifeStage.RETIREMENT

        # RETIREMENT -> INHERITANCE
        module.meet_criteria(sample_user, "will_exists")
        module.meet_criteria(sample_user, "heirs_identified")
        module.add_verification_doc(sample_user, "legal_will", "will_001")
        module.add_verification_doc(sample_user, "asset_inventory", "assets_001")
        module.add_verification_doc(sample_user, "heir_consent", "consent_001")
        module.transition_stage(sample_user, LifeStage.INHERITANCE)
        assert module.get_current_stage(sample_user) == LifeStage.INHERITANCE

        # Verify services accumulated
        p = module.get_life_profile(sample_user)
        assert len(p.services_completed) > 0
        # 5 transitions: BIRTH→EDUCATION→WORK→FAMILY→RETIREMENT→INHERITANCE
        assert len(p.stage_history) >= 5

    def test_invalid_transition_jump(self, module, profile, sample_user):
        """Cannot jump from BIRTH directly to RETIREMENT."""
        status, msg = module.transition_stage(sample_user, LifeStage.RETIREMENT)
        assert status == TransitionStatus.INVALID_TRANSITION

    def test_invalid_transition_backwards(self, module, profile, sample_user):
        """Cannot go backwards from EDUCATION to BIRTH."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        status, msg = module.transition_stage(sample_user, LifeStage.BIRTH)
        assert status == TransitionStatus.INVALID_TRANSITION

    def test_multiple_users_independent(self, module):
        """Multiple users have independent profiles and stages."""
        u1 = "user_alpha"
        u2 = "user_beta"
        u3 = "user_gamma"

        module.create_profile(u1)
        module.create_profile(u2)
        module.create_profile(u3)

        assert module.get_current_stage(u1) == LifeStage.BIRTH
        assert module.get_current_stage(u2) == LifeStage.BIRTH
        assert module.get_current_stage(u3) == LifeStage.BIRTH

        # Advance u1
        module.meet_criteria(u1, "age >= 4")
        module.add_verification_doc(u1, "enrollment", "doc")
        module.transition_stage(u1, LifeStage.EDUCATION)

        assert module.get_current_stage(u1) == LifeStage.EDUCATION
        assert module.get_current_stage(u2) == LifeStage.BIRTH  # unchanged
        assert module.get_current_stage(u3) == LifeStage.BIRTH  # unchanged

    def test_services_accumulate_across_lifecycle(self, module, profile, sample_user):
        """Completed services accumulate; active services change per stage."""
        # BIRTH -> EDUCATION
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(sample_user, LifeStage.EDUCATION)

        p = module.get_life_profile(sample_user)
        assert "identity" in p.services_completed
        assert "healthcare" in p.services_completed
        assert "school" in p.services_active

        # EDUCATION -> WORK
        module.meet_criteria(sample_user, "age >= 16")
        module.meet_criteria(sample_user, "skill_certification")
        module.add_verification_doc(sample_user, "employment_contract", "doc")
        module.add_verification_doc(sample_user, "tax_registration", "doc")
        module.transition_stage(sample_user, LifeStage.WORK)

        p = module.get_life_profile(sample_user)
        assert "school" in p.services_completed
        assert "job_market" in p.services_active
        assert "career_tracking" in p.services_active

    def test_update_timestamp_on_operations(self, module, profile, sample_user):
        """updated_at changes after operations."""
        p = module.get_life_profile(sample_user)
        original_updated = p.updated_at

        time.sleep(0.01)
        module.meet_criteria(sample_user, "age >= 4")
        assert p.updated_at > original_updated

        time.sleep(0.01)
        module.add_verification_doc(sample_user, "enrollment", "doc")
        assert p.updated_at > original_updated

    def test_concurrent_safe(self, module, profile, sample_user):
        """Multiple operations execute without error."""
        import threading

        def add_data(user):
            for i in range(5):
                module.meet_criteria(user, f"criterion_{i}")
                module.add_verification_doc(user, f"doc_{i}", f"data_{i}")

        threads = []
        for i in range(3):
            uid = f"concurrent_user_{i}"
            module.create_profile(uid)
            t = threading.Thread(target=add_data, args=(uid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        stats = module.get_stats()
        assert stats["total_profiles"] >= 3

    def test_reset_cleans_db_file(self, module, sample_user):
        """reset_life_journey_module() deletes the DB file."""
        module.create_profile(sample_user)
        db_path = "data/life_journey.jsonl"
        assert os.path.exists(db_path)

        reset_life_journey_module()
        assert not os.path.exists(db_path)

    def test_notes_included_in_transition(self, module, profile, sample_user):
        """Custom notes are recorded in transition records."""
        module.meet_criteria(sample_user, "age >= 4")
        module.add_verification_doc(sample_user, "enrollment", "doc")
        module.transition_stage(
            sample_user, LifeStage.EDUCATION,
            notes="Started at age 5",
        )
        history = module.get_transition_history(sample_user)
        successful = [r for r in history if r.status == TransitionStatus.SUCCESS]
        assert len(successful) >= 1
        assert successful[0].notes == "Started at age 5"
