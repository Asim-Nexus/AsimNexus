#!/usr/bin/env python3
"""
core/life/life_journey_module.py
AsimNexus — Life Journey Module

Event-driven life journey tracking with stage progression,
skill acquisition, connections, resources, and random events.

Provides:
  - LifeStage enum (BIRTH → CHILDHOOD → EDUCATION → CAREER → FAMILY → LEGACY → TRANSCENDENCE)
  - EventType enum (POSITIVE, NEGATIVE, NEUTRAL)
  - StageRequirements, LifeEvent, LifeEntity dataclasses
  - LifeJourneyModule: entity creation, skill/connection/resource management,
    stage advancement, event triggering, progress tracking
  - STAGE_ORDER, STAGE_REQUIREMENTS, DEFAULT_EVENTS constants
  - Singleton factory: get_life_journey_module() / reset_life_journey_module()
"""

import time
import random
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Generator

logger = logging.getLogger(__name__)


# ── LifeStage Enum ────────────────────────────────────────────────────────────

class LifeStage(str, Enum):
    """Seven stages of life journey."""
    BIRTH = "birth"
    CHILDHOOD = "childhood"
    EDUCATION = "education"
    CAREER = "career"
    FAMILY = "family"
    LEGACY = "legacy"
    TRANSCENDENCE = "transcendence"


# ── EventType Enum ────────────────────────────────────────────────────────────

class EventType(str, Enum):
    """Types of life events."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


# ── Stage Order ───────────────────────────────────────────────────────────────

STAGE_ORDER: List[LifeStage] = [
    LifeStage.BIRTH,
    LifeStage.CHILDHOOD,
    LifeStage.EDUCATION,
    LifeStage.CAREER,
    LifeStage.FAMILY,
    LifeStage.LEGACY,
    LifeStage.TRANSCENDENCE,
]


# ── StageRequirements Dataclass ───────────────────────────────────────────────

@dataclass
class StageRequirements:
    """Requirements needed to advance from one stage to the next."""
    skills: Dict[str, int] = field(default_factory=dict)
    connections: int = 0
    resources: float = 0.0
    time_in_stage: float = 0.0


# ── Stage Requirements Map ────────────────────────────────────────────────────

STAGE_REQUIREMENTS: Dict[LifeStage, StageRequirements] = {
    LifeStage.BIRTH: StageRequirements(
        skills={},
        connections=0,
        resources=0.0,
        time_in_stage=0.5,
    ),
    LifeStage.CHILDHOOD: StageRequirements(
        skills={"basic_motor": 1, "basic_language": 1},
        connections=1,
        resources=1.0,
        time_in_stage=1.0,
    ),
    LifeStage.EDUCATION: StageRequirements(
        skills={"literacy": 1, "numeracy": 1},
        connections=2,
        resources=2.0,
        time_in_stage=2.0,
    ),
    LifeStage.CAREER: StageRequirements(
        skills={"specialization": 1, "communication": 1},
        connections=3,
        resources=5.0,
        time_in_stage=3.0,
    ),
    LifeStage.FAMILY: StageRequirements(
        skills={"relationship": 1, "empathy": 1},
        connections=4,
        resources=3.0,
        time_in_stage=3.0,
    ),
    LifeStage.LEGACY: StageRequirements(
        skills={"mentorship": 1, "wisdom": 1},
        connections=5,
        resources=10.0,
        time_in_stage=3.0,
    ),
    LifeStage.TRANSCENDENCE: StageRequirements(
        skills={"enlightenment": 1},
        connections=6,
        resources=0.0,
        time_in_stage=3.0,
    ),
}


# ── LifeEvent Dataclass ───────────────────────────────────────────────────────

@dataclass
class LifeEvent:
    """A random event that can affect an entity."""
    event_id: str
    name: str
    event_type: EventType
    description: str
    effect_skills: Dict[str, int] = field(default_factory=dict)
    effect_connections: int = 0
    effect_resources: float = 0.0
    probability: float = 0.3
    min_stage: LifeStage = LifeStage.BIRTH
    max_stage: LifeStage = LifeStage.TRANSCENDENCE


# ── Default Events ────────────────────────────────────────────────────────────

DEFAULT_EVENTS: List[LifeEvent] = [
    LifeEvent(
        event_id="inherit_wealth",
        name="Inherit Wealth",
        event_type=EventType.POSITIVE,
        description="You inherit a modest fortune from a distant relative.",
        effect_resources=10.0,
        probability=0.15,
    ),
    LifeEvent(
        event_id="lose_job",
        name="Lose Job",
        event_type=EventType.NEGATIVE,
        description="Your company downsizes and you lose your job.",
        effect_resources=-5.0,
        probability=0.2,
        min_stage=LifeStage.CAREER,
    ),
    LifeEvent(
        event_id="make_friend",
        name="Make a Friend",
        event_type=EventType.POSITIVE,
        description="You meet someone who becomes a close friend.",
        effect_connections=1,
        probability=0.4,
    ),
    LifeEvent(
        event_id="get_scholarship",
        name="Get Scholarship",
        event_type=EventType.POSITIVE,
        description="You receive a scholarship for your education.",
        effect_resources=3.0,
        probability=0.2,
        min_stage=LifeStage.EDUCATION,
        max_stage=LifeStage.EDUCATION,
    ),
    LifeEvent(
        event_id="accident",
        name="Accident",
        event_type=EventType.NEGATIVE,
        description="You are in a minor accident and need time to recover.",
        effect_resources=-2.0,
        probability=0.1,
    ),
    LifeEvent(
        event_id="promotion",
        name="Promotion",
        event_type=EventType.POSITIVE,
        description="You get promoted at work!",
        effect_resources=5.0,
        effect_skills={"specialization": 1},
        probability=0.25,
        min_stage=LifeStage.CAREER,
    ),
    LifeEvent(
        event_id="mentor_found",
        name="Find a Mentor",
        event_type=EventType.POSITIVE,
        description="An experienced professional takes you under their wing.",
        effect_skills={"wisdom": 1},
        effect_connections=1,
        probability=0.2,
        min_stage=LifeStage.EDUCATION,
    ),
    LifeEvent(
        event_id="health_issue",
        name="Health Issue",
        event_type=EventType.NEGATIVE,
        description="You face a health challenge that sets you back.",
        effect_resources=-3.0,
        probability=0.15,
    ),
    LifeEvent(
        event_id="community_award",
        name="Community Award",
        event_type=EventType.POSITIVE,
        description="Your community recognizes your contributions.",
        effect_skills={"empathy": 1},
        effect_connections=1,
        probability=0.15,
        min_stage=LifeStage.FAMILY,
    ),
    LifeEvent(
        event_id="random_encounter",
        name="Random Encounter",
        event_type=EventType.NEUTRAL,
        description="You have an interesting encounter that broadens your perspective.",
        effect_skills={"wisdom": 1},
        probability=0.3,
    ),
    LifeEvent(
        event_id="business_venture",
        name="Business Venture",
        event_type=EventType.POSITIVE,
        description="Your side business starts generating income.",
        effect_resources=8.0,
        probability=0.1,
        min_stage=LifeStage.CAREER,
    ),
    LifeEvent(
        event_id="family_reunion",
        name="Family Reunion",
        event_type=EventType.POSITIVE,
        description="You reconnect with extended family members.",
        effect_connections=2,
        probability=0.2,
        min_stage=LifeStage.FAMILY,
    ),
]


# ── LifeEntity Dataclass ──────────────────────────────────────────────────────

@dataclass
class LifeEntity:
    """A life journey entity tracking its progression through stages."""
    entity_id: str
    user_id: str = ""
    current_stage: LifeStage = LifeStage.BIRTH
    skills: Dict[str, int] = field(default_factory=dict)
    connections: int = 0
    resources: float = 0.0
    time_in_stage: float = 0.0
    completed_stages: List[str] = field(default_factory=list)
    encountered_events: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


# ── LifeJourneyModule ─────────────────────────────────────────────────────────

class LifeJourneyModule:
    """
    Life journey simulation engine.

    Manages entities through 7 life stages with skill, connection,
    resource, and time requirements for advancement.
    """

    def __init__(self, seed: Optional[int] = None):
        self._entities: Dict[str, LifeEntity] = {}
        self._events: List[LifeEvent] = list(DEFAULT_EVENTS)
        self._rng = random.Random(seed) if seed is not None else random.Random()
        self._entity_counter = 0

    # ── Entity Management ─────────────────────────────────────────────────

    def create_entity(self, user_id: str = "",
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new life journey entity. Returns entity ID."""
        self._entity_counter += 1
        entity_id = f"entity_{self._entity_counter:04d}"

        if user_id and user_id in self._entities:
            raise ValueError(f"Entity '{user_id}' already exists")

        eid = user_id if user_id else entity_id
        if eid in self._entities:
            raise ValueError(f"Entity '{eid}' already exists")

        self._entities[eid] = LifeEntity(
            entity_id=eid,
            user_id=user_id,
            metadata=metadata or {},
        )
        return eid

    def get_entity(self, entity_id: str) -> Optional[LifeEntity]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_all_entities(self) -> List[str]:
        """Get all entity IDs."""
        return list(self._entities.keys())

    # ── Skill Management ──────────────────────────────────────────────────

    def add_skill(self, entity_id: str, skill_name: str,
                  count: int = 1) -> Tuple[bool, str]:
        """Add a skill to an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return False, f"Entity '{entity_id}' not found"

        entity.skills[skill_name] = entity.skills.get(skill_name, 0) + count
        return True, f"Added skill '{skill_name}' (level {entity.skills[skill_name]})"

    # ── Connection Management ─────────────────────────────────────────────

    def add_connection(self, entity_id: str, count: int = 1) -> Tuple[bool, str]:
        """Add connections to an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return False, f"Entity '{entity_id}' not found"

        entity.connections += count
        return True, f"Added {count} connection(s) (total: {entity.connections})"

    # ── Resource Management ───────────────────────────────────────────────

    def add_resource(self, entity_id: str, amount: float) -> Tuple[bool, str]:
        """Add resources to an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return False, f"Entity '{entity_id}' not found"

        entity.resources += amount
        return True, f"Added {amount} resources (total: {entity.resources})"

    # ── Time Management ───────────────────────────────────────────────────

    def tick(self, entity_id: str, delta: float = 1.0) -> Tuple[bool, str]:
        """Advance time for an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return False, f"Entity '{entity_id}' not found"

        entity.time_in_stage += delta
        return True, f"Time advanced by {delta} (total: {entity.time_in_stage})"

    # ── Stage Advancement ─────────────────────────────────────────────────

    def advance(self, entity_id: str) -> Tuple[bool, str]:
        """Attempt to advance an entity to the next life stage."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return False, f"Entity '{entity_id}' not found"

        # Check if at final stage
        current_idx = STAGE_ORDER.index(entity.current_stage)
        if current_idx >= len(STAGE_ORDER) - 1:
            return False, "Already at final stage (TRANSCENDENCE)"

        next_stage = STAGE_ORDER[current_idx + 1]
        reqs = STAGE_REQUIREMENTS.get(next_stage, StageRequirements())

        # Check requirements
        for skill_name, level in reqs.skills.items():
            if entity.skills.get(skill_name, 0) < level:
                return False, f"Missing required skill: {skill_name} (need {level})"

        if entity.connections < reqs.connections:
            return False, f"Insufficient connections: have {entity.connections}, need {reqs.connections}"

        if entity.resources < reqs.resources:
            return False, f"Insufficient resources: have {entity.resources}, need {reqs.resources}"

        if entity.time_in_stage < reqs.time_in_stage:
            return False, f"Not enough time in stage: have {entity.time_in_stage}, need {reqs.time_in_stage}"

        # Advance
        entity.completed_stages.append(entity.current_stage.value)
        entity.current_stage = next_stage
        entity.time_in_stage = 0.0

        return True, f"Advanced to {next_stage.value}"

    # ── Event System ──────────────────────────────────────────────────────

    def register_event(self, event: LifeEvent) -> None:
        """Register a custom event."""
        self._events.append(event)

    def trigger_event(self, entity_id: str,
                      event_type: Optional[EventType] = None) -> Optional[Dict[str, Any]]:
        """Trigger a random event for an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return None

        # Filter eligible events
        eligible = []
        for evt in self._events:
            if event_type and evt.event_type != event_type:
                continue
            stage_idx = STAGE_ORDER.index(entity.current_stage)
            min_idx = STAGE_ORDER.index(evt.min_stage)
            max_idx = STAGE_ORDER.index(evt.max_stage)
            if min_idx <= stage_idx <= max_idx:
                eligible.append(evt)

        if not eligible:
            return None

        # First, try guaranteed events (probability >= 1.0)
        for evt in eligible:
            if evt.probability >= 1.0:
                # Apply effects
                for skill_name, level in evt.effect_skills.items():
                    entity.skills[skill_name] = entity.skills.get(skill_name, 0) + level
                entity.connections += evt.effect_connections
                entity.resources += evt.effect_resources
                entity.encountered_events.append(evt.event_id)

                return {
                    "event_id": evt.event_id,
                    "name": evt.name,
                    "event_type": evt.event_type.value,
                    "description": evt.description,
                }

        # Roll for each eligible event
        for evt in eligible:
            if self._rng.random() < evt.probability:
                # Apply effects
                for skill_name, level in evt.effect_skills.items():
                    entity.skills[skill_name] = entity.skills.get(skill_name, 0) + level
                entity.connections += evt.effect_connections
                entity.resources += evt.effect_resources
                entity.encountered_events.append(evt.event_id)

                return {
                    "event_id": evt.event_id,
                    "name": evt.name,
                    "event_type": evt.event_type.value,
                    "description": evt.description,
                }

        return None

    def get_available_events(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get events that have been encountered by an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return []

        result = []
        for evt_id in entity.encountered_events:
            for evt in self._events:
                if evt.event_id == evt_id:
                    result.append({
                        "event_id": evt.event_id,
                        "name": evt.name,
                        "event_type": evt.event_type.value,
                    })
                    break
        return result

    # ── Progress Tracking ─────────────────────────────────────────────────

    def get_progress(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return None

        current_idx = STAGE_ORDER.index(entity.current_stage)
        total_stages = len(STAGE_ORDER)
        completion_pct = (current_idx / (total_stages - 1)) * 100 if total_stages > 1 else 0

        # Check requirements for current stage
        current_stage = entity.current_stage
        reqs = STAGE_REQUIREMENTS.get(current_stage, StageRequirements())
        reqs_met = True
        for skill_name, level in reqs.skills.items():
            if entity.skills.get(skill_name, 0) < level:
                reqs_met = False
                break
        if entity.connections < reqs.connections:
            reqs_met = False
        if entity.resources < reqs.resources:
            reqs_met = False
        if entity.time_in_stage < reqs.time_in_stage:
            reqs_met = False

        return {
            "entity_id": entity_id,
            "current_stage": entity.current_stage.value,
            "stage_index": current_idx,
            "completion_pct": round(completion_pct, 1),
            "requirements": {
                "all_met": reqs_met,
            },
        }

    # ── Statistics ────────────────────────────────────────────────────────

    def get_journey_stats(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get journey statistics for an entity."""
        entity = self._entities.get(entity_id)
        if entity is None:
            return None

        return {
            "entity_id": entity_id,
            "current_stage": entity.current_stage.value,
            "total_skills": len(entity.skills),
            "total_connections": entity.connections,
            "total_resources": entity.resources,
            "completed_stages": len(entity.completed_stages),
            "total_events": len(entity.encountered_events),
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics across all entities."""
        if not self._entities:
            return {
                "total_entities": 0,
                "average_completion": 0.0,
                "most_common_stage": "none",
                "stages_distribution": {},
            }

        stage_counts: Dict[str, int] = {}
        total_completion = 0.0
        total_stages = len(STAGE_ORDER)

        for entity in self._entities.values():
            stage_name = entity.current_stage.value
            stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1
            current_idx = STAGE_ORDER.index(entity.current_stage)
            total_completion += (current_idx / (total_stages - 1)) * 100

        most_common = max(stage_counts, key=stage_counts.get)

        return {
            "total_entities": len(self._entities),
            "average_completion": round(total_completion / len(self._entities), 1),
            "most_common_stage": most_common,
            "stages_distribution": stage_counts,
        }


# ── Singleton Factory ─────────────────────────────────────────────────────────

_module_instance: Optional[LifeJourneyModule] = None


def get_life_journey_module(seed: Optional[int] = None) -> LifeJourneyModule:
    """Return the singleton LifeJourneyModule instance."""
    global _module_instance
    if _module_instance is None:
        _module_instance = LifeJourneyModule(seed=seed)
    return _module_instance


def reset_life_journey_module() -> None:
    """Reset the singleton (for testing)."""
    global _module_instance
    _module_instance = None
