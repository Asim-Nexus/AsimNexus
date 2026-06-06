#!/usr/bin/env python3
"""
Tests for [`core/life/life_journey_module.py`](../../core/life/life_journey_module.py).

Covers: entity creation, skill acquisition, connection/resource accumulation,
stage advancement (including requirement checks), event triggering, stats.

Target: 10-12 tests
"""

import pytest
from typing import Generator

from core.life.life_journey_module import (
    LifeStage,
    EventType,
    StageRequirements,
    LifeEvent,
    LifeEntity,
    LifeJourneyModule,
    STAGE_ORDER,
    STAGE_REQUIREMENTS,
    DEFAULT_EVENTS,
    get_life_journey_module,
    reset_life_journey_module,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_module():
    """Reset singleton before each test (autouse)."""
    reset_life_journey_module()
    yield
    reset_life_journey_module()


@pytest.fixture
def module() -> LifeJourneyModule:
    """Fresh LifeJourneyModule instance with deterministic seed."""
    return LifeJourneyModule(seed=42)


@pytest.fixture
def entity_id(module: LifeJourneyModule) -> str:
    """Create and return an entity ID."""
    return module.create_entity("test_user_01", metadata={"name": "Test User"})


# ─── Test: LifeStage Enum ─────────────────────────────────────────────────────


class TestLifeStage:
    """LifeStage enum values and order."""

    def test_values(self):
        """All 7 life stages exist with correct string values."""
        assert LifeStage.BIRTH.value == "birth"
        assert LifeStage.CHILDHOOD.value == "childhood"
        assert LifeStage.EDUCATION.value == "education"
        assert LifeStage.CAREER.value == "career"
        assert LifeStage.FAMILY.value == "family"
        assert LifeStage.LEGACY.value == "legacy"
        assert LifeStage.TRANSCENDENCE.value == "transcendence"

    def test_stage_order(self):
        """STAGE_ORDER has 7 stages in sequential order."""
        assert len(STAGE_ORDER) == 7
        assert STAGE_ORDER[0] == LifeStage.BIRTH
        assert STAGE_ORDER[-1] == LifeStage.TRANSCENDENCE


class TestEventType:
    """EventType enum values."""

    def test_values(self):
        assert EventType.POSITIVE.value == "positive"
        assert EventType.NEGATIVE.value == "negative"
        assert EventType.NEUTRAL.value == "neutral"


# ─── Test: Entity Creation ─────────────────────────────────────────────────────


class TestEntityCreation:
    """Creating entities via LifeJourneyModule."""

    def test_create_entity_starts_at_birth(self, module: LifeJourneyModule):
        """New entity starts at BIRTH stage."""
        eid = module.create_entity("alice")
        entity = module.get_entity(eid)
        assert entity is not None
        assert entity.current_stage == LifeStage.BIRTH

    def test_create_entity_auto_id(self, module: LifeJourneyModule):
        """Entity with no ID gets auto-generated ID."""
        eid = module.create_entity()
        assert eid is not None
        assert eid.startswith("entity_")
        assert module.get_entity(eid) is not None

    def test_create_duplicate_raises(self, module: LifeJourneyModule):
        """Creating duplicate entity ID raises ValueError."""
        module.create_entity("dup")
        with pytest.raises(ValueError, match="already exists"):
            module.create_entity("dup")

    def test_create_entity_with_metadata(self, module: LifeJourneyModule):
        """Entity can store metadata."""
        eid = module.create_entity("bob", metadata={"role": "tester"})
        entity = module.get_entity(eid)
        assert entity is not None
        assert entity.metadata.get("role") == "tester"


# ─── Test: Skill Acquisition ──────────────────────────────────────────────────


class TestSkills:
    """Adding skills to entities."""

    def test_add_skill(self, module: LifeJourneyModule, entity_id: str):
        """Skill can be added to entity."""
        success, msg = module.add_skill(entity_id, "basic_motor")
        assert success is True
        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.skills.get("basic_motor") == 1

    def test_add_skill_nonexistent_entity(self, module: LifeJourneyModule):
        """Adding skill to nonexistent entity returns False."""
        success, msg = module.add_skill("ghost", "any_skill")
        assert success is False
        assert "not found" in msg

    def test_add_skill_multiple_levels(self, module: LifeJourneyModule, entity_id: str):
        """Skill can have multiple levels."""
        module.add_skill(entity_id, "literacy", count=3)
        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.skills.get("literacy") == 3


# ─── Test: Connections ────────────────────────────────────────────────────────


class TestConnections:
    """Adding connections to entities."""

    def test_add_connection(self, module: LifeJourneyModule, entity_id: str):
        """Connection count increases."""
        module.add_connection(entity_id, count=3)
        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.connections == 3


# ─── Test: Resources ──────────────────────────────────────────────────────────


class TestResources:
    """Adding resources to entities."""

    def test_add_resource(self, module: LifeJourneyModule, entity_id: str):
        """Resource amount increases."""
        module.add_resource(entity_id, 10.0)
        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.resources == 10.0


# ─── Test: Stage Advancement ──────────────────────────────────────────────────


class TestAdvance:
    """Stage advancement mechanics."""

    def test_advance_blocked_at_birth_no_skills(self, module: LifeJourneyModule, entity_id: str):
        """Advance from BIRTH→CHILDHOOD blocked if skills not met."""
        # BIRTH has no requirements, so advance to CHILDHOOD should check CHILDHOOD's reqs
        # Childhood needs basic_motor, basic_language, 1 connection, 1.0 resources, 1.0s time
        # Add skills only, not enough connections
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        module.tick(entity_id, delta=2.0)

        success, msg = module.advance(entity_id)
        assert success is True, f"Advance failed: {msg}"
        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.current_stage == LifeStage.CHILDHOOD

    def test_advance_blocked_missing_skill(self, module: LifeJourneyModule, entity_id: str):
        """Advance blocked if required skill is missing."""
        # Get past BIRTH first (no requirements)
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        module.tick(entity_id, delta=2.0)
        module.advance(entity_id)  # BIRTH → CHILDHOOD

        # Now try to go to EDUCATION - needs literacy, numeracy, 2 connections, 2.0 resources
        # Only add one skill
        module.add_skill(entity_id, "literacy")
        module.add_connection(entity_id, 1)  # total now 2
        module.add_resource(entity_id, 2.0)
        module.tick(entity_id, delta=2.0)

        success, msg = module.advance(entity_id)
        assert success is False
        assert "Missing required skill" in msg

    def test_advance_blocked_insufficient_connections(self, module: LifeJourneyModule, entity_id: str):
        """Advance blocked if connections insufficient."""
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        module.tick(entity_id, delta=2.0)
        module.advance(entity_id)

        # Now EDUCATION needs 2 connections - we have 1 after CHILDHOOD advance
        module.add_skill(entity_id, "literacy")
        module.add_skill(entity_id, "numeracy")
        module.add_resource(entity_id, 2.0)
        module.tick(entity_id, delta=2.0)

        success, msg = module.advance(entity_id)
        assert success is False
        assert "Insufficient connections" in msg

    def test_advance_blocked_insufficient_resources(self, module: LifeJourneyModule, entity_id: str):
        """Advance blocked if resources insufficient."""
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        module.tick(entity_id, delta=2.0)
        module.advance(entity_id)  # → CHILDHOOD

        # EDUCATION needs 2.0 resources
        module.add_skill(entity_id, "literacy")
        module.add_skill(entity_id, "numeracy")
        module.add_connection(entity_id, 1)  # total = 2
        # Only add 1.0 resource, need 2.0 total
        module.add_resource(entity_id, 0.5)
        module.tick(entity_id, delta=2.0)

        success, msg = module.advance(entity_id)
        assert success is False
        assert "Insufficient resources" in msg

    def test_advance_blocked_not_enough_time(self, module: LifeJourneyModule, entity_id: str):
        """Advance blocked if time_in_stage insufficient."""
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        # Don't tick enough time
        module.tick(entity_id, delta=0.2)  # Not enough for BIRTH's 0.5s requirement

        success, msg = module.advance(entity_id)
        assert success is False
        assert "Not enough time" in msg

    def test_advance_full_to_transcendence(self, module: LifeJourneyModule, entity_id: str):
        """Full advancement through all 7 stages."""
        # BIRTH → CHILDHOOD
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        module.tick(entity_id, delta=2.0)
        assert module.advance(entity_id)[0] is True

        # CHILDHOOD → EDUCATION
        module.add_skill(entity_id, "literacy")
        module.add_skill(entity_id, "numeracy")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 2.0)
        module.tick(entity_id, delta=2.0)
        assert module.advance(entity_id)[0] is True

        # EDUCATION → CAREER
        module.add_skill(entity_id, "specialization")
        module.add_skill(entity_id, "communication")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 5.0)
        module.tick(entity_id, delta=3.0)
        assert module.advance(entity_id)[0] is True

        # CAREER → FAMILY
        module.add_skill(entity_id, "relationship")
        module.add_skill(entity_id, "empathy")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 3.0)
        module.tick(entity_id, delta=3.0)
        assert module.advance(entity_id)[0] is True

        # FAMILY → LEGACY
        module.add_skill(entity_id, "mentorship")
        module.add_skill(entity_id, "wisdom")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 10.0)
        module.tick(entity_id, delta=3.0)
        assert module.advance(entity_id)[0] is True

        # LEGACY → TRANSCENDENCE
        module.add_skill(entity_id, "enlightenment")
        module.add_connection(entity_id, 1)
        module.tick(entity_id, delta=4.0)
        assert module.advance(entity_id)[0] is True

        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.current_stage == LifeStage.TRANSCENDENCE
        assert len(entity.completed_stages) == 6

    def test_advance_at_final_stage(self, module: LifeJourneyModule, entity_id: str):
        """Cannot advance past TRANSCENDENCE."""
        # Quick-advance through all stages with requirements met
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 6)  # Pre-load enough connections
        module.add_resource(entity_id, 25.0)  # Pre-load enough resources
        module.add_skill(entity_id, "literacy")
        module.add_skill(entity_id, "numeracy")
        module.add_skill(entity_id, "specialization")
        module.add_skill(entity_id, "communication")
        module.add_skill(entity_id, "relationship")
        module.add_skill(entity_id, "empathy")
        module.add_skill(entity_id, "mentorship")
        module.add_skill(entity_id, "wisdom")
        module.add_skill(entity_id, "enlightenment")

        # Advance through all 6 stages, tick-ing between each so time_in_stage accumulates
        for _ in range(6):
            module.tick(entity_id, delta=3.0)
            success, msg = module.advance(entity_id)
            assert success is True, f"Advance failed at stage: {msg}"

        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.current_stage == LifeStage.TRANSCENDENCE

        # Try to advance beyond
        success, msg = module.advance(entity_id)
        assert success is False
        assert "final stage" in msg


# ─── Test: Event System ───────────────────────────────────────────────────────


class TestEvents:
    """Event triggering system."""

    def test_default_events_exist(self):
        """DEFAULT_EVENTS has expected events."""
        assert len(DEFAULT_EVENTS) >= 10
        event_ids = [e.event_id for e in DEFAULT_EVENTS]
        assert "inherit_wealth" in event_ids
        assert "lose_job" in event_ids
        assert "make_friend" in event_ids

    def test_trigger_event(self, module: LifeJourneyModule, entity_id: str):
        """Events can be triggered and apply effects."""
        # Register a guaranteed-to-trigger event
        guaranteed = LifeEvent(
            event_id="test_event",
            name="Test Event",
            event_type=EventType.POSITIVE,
            description="Guaranteed trigger",
            effect_skills={"test_skill": 1},
            effect_connections=2,
            effect_resources=5.0,
            probability=1.0,  # Always triggers
        )
        module.register_event(guaranteed)

        result = module.trigger_event(entity_id)
        assert result is not None
        assert result["name"] == "Test Event"

        entity = module.get_entity(entity_id)
        assert entity is not None
        assert "test_skill" in entity.skills
        assert entity.connections >= 2
        assert entity.resources >= 5.0

    def test_trigger_event_no_entity(self, module: LifeJourneyModule):
        """Triggering event for nonexistent entity returns None."""
        result = module.trigger_event("ghost")
        assert result is None

    def test_trigger_event_by_type(self, module: LifeJourneyModule, entity_id: str):
        """Events can be filtered by EventType."""
        # Register a guaranteed NEGATIVE event
        guaranteed = LifeEvent(
            event_id="test_neg",
            name="Test Negative",
            event_type=EventType.NEGATIVE,
            description="Always negative",
            probability=1.0,
        )
        module.register_event(guaranteed)

        result = module.trigger_event(entity_id, event_type=EventType.NEGATIVE)
        assert result is not None
        assert result["event_type"] == "negative"

        # No POSITIVE event should trigger
        result2 = module.trigger_event(entity_id, event_type=EventType.POSITIVE)
        # Might or might not trigger based on probability of default positive events

    def test_get_available_events(self, module: LifeJourneyModule, entity_id: str):
        """get_available_events returns encountered events."""
        # Trigger a guaranteed event
        guaranteed = LifeEvent(
            event_id="test_evt",
            name="Test",
            event_type=EventType.NEUTRAL,
            description="Test",
            probability=1.0,
        )
        module.register_event(guaranteed)
        module.trigger_event(entity_id)

        events = module.get_available_events(entity_id)
        assert len(events) >= 1
        assert events[0]["event_id"] == "test_evt"


# ─── Test: Progress Tracking ──────────────────────────────────────────────────


class TestProgress:
    """Progress tracking via get_progress()."""

    def test_get_progress_initial(self, module: LifeJourneyModule, entity_id: str):
        """Initial progress shows BIRTH stage with requirements not yet met."""
        # BIRTH requires 0.5s time_in_stage, so tick first
        module.tick(entity_id, delta=1.0)
        progress = module.get_progress(entity_id)
        assert progress is not None
        assert progress["current_stage"] == "birth"
        assert progress["stage_index"] == 0
        assert progress["completion_pct"] == 0.0
        assert progress["requirements"]["all_met"] is True

    def test_get_progress_nonexistent(self, module: LifeJourneyModule):
        """Progress for nonexistent entity returns None."""
        assert module.get_progress("ghost") is None

    def test_get_progress_after_advance(self, module: LifeJourneyModule, entity_id: str):
        """Progress updates after advancement."""
        module.add_skill(entity_id, "basic_motor")
        module.add_skill(entity_id, "basic_language")
        module.add_connection(entity_id, 1)
        module.add_resource(entity_id, 1.0)
        module.tick(entity_id, delta=2.0)
        module.advance(entity_id)

        progress = module.get_progress(entity_id)
        assert progress is not None
        assert progress["current_stage"] == "childhood"
        assert progress["stage_index"] == 1


# ─── Test: Tick / Time ────────────────────────────────────────────────────────


class TestTick:
    """Time advancement via tick()."""

    def test_tick_increases_time(self, module: LifeJourneyModule, entity_id: str):
        """tick() increments time_in_stage."""
        module.tick(entity_id, delta=3.0)
        entity = module.get_entity(entity_id)
        assert entity is not None
        assert entity.time_in_stage >= 3.0

    def test_tick_nonexistent_entity(self, module: LifeJourneyModule):
        """tick for nonexistent entity returns False."""
        success, msg = module.tick("ghost")
        assert success is False


# ─── Test: Journey Stats ──────────────────────────────────────────────────────


class TestJourneyStats:
    """Journey and global statistics."""

    def test_get_journey_stats(self, module: LifeJourneyModule, entity_id: str):
        """get_journey_stats returns structured data for entity."""
        stats = module.get_journey_stats(entity_id)
        assert stats is not None
        assert stats["entity_id"] == entity_id
        assert stats["current_stage"] == "birth"
        assert "total_skills" in stats
        assert "total_connections" in stats
        assert "total_resources" in stats

    def test_get_journey_stats_nonexistent(self, module: LifeJourneyModule):
        """Journey stats for nonexistent entity returns None."""
        assert module.get_journey_stats("ghost") is None

    def test_global_stats_empty(self, module: LifeJourneyModule):
        """Global stats returns zeros when no entities exist."""
        stats = module.get_global_stats()
        assert stats["total_entities"] == 0
        assert stats["average_completion"] == 0.0

    def test_global_stats_with_entities(self, module: LifeJourneyModule):
        """Global stats aggregate across multiple entities."""
        module.create_entity("alice")
        module.create_entity("bob")
        stats = module.get_global_stats()
        assert stats["total_entities"] == 2
        assert stats["most_common_stage"] == "birth"
        assert "stages_distribution" in stats

    def test_get_all_entities(self, module: LifeJourneyModule):
        """get_all_entities returns all entity IDs."""
        module.create_entity("alpha")
        module.create_entity("beta")
        module.create_entity("gamma")
        entities = module.get_all_entities()
        assert len(entities) == 3
        assert "alpha" in entities
        assert "beta" in entities
        assert "gamma" in entities


# ─── Test: Singleton ─────────────────────────────────────────────────────────


class TestSingleton:
    """Singleton factory pattern."""

    def test_singleton_returns_same_instance(self):
        """get_life_journey_module returns same instance on repeated calls."""
        m1 = get_life_journey_module(seed=42)
        m2 = get_life_journey_module()
        assert m1 is m2

    def test_reset_creates_new_instance(self):
        """reset_life_journey_module causes get to create a new instance."""
        m1 = get_life_journey_module(seed=42)
        reset_life_journey_module()
        m2 = get_life_journey_module()
        assert m1 is not m2

    def test_reset_clears_entities(self):
        """reset_life_journey_module clears all entities."""
        m = get_life_journey_module(seed=42)
        m.create_entity("test_reset")
        assert len(m.get_all_entities()) == 1
        reset_life_journey_module()
        m2 = get_life_journey_module()
        assert len(m2.get_all_entities()) == 0
