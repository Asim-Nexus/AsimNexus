"""
Digital Twin System
===================
Manages digital twins representing real-world entities.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Gender(Enum):
    """Gender enumeration."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class LifeStage(Enum):
    """Life stage enumeration."""
    CHILD = "child"
    TEENAGER = "teenager"
    YOUNG_ADULT = "young_adult"
    ADULT = "adult"
    MIDDLE_AGED = "middle_aged"
    SENIOR = "senior"
    ELDERLY = "elderly"


@dataclass
class LifeEvent:
    """A life event for a digital twin."""
    event_id: str
    event_type: str
    event_date: date
    description: str
    location: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """A skill for a digital twin."""
    skill_name: str
    proficiency_level: float
    years_experience: int
    skill_id: str = ""


@dataclass
class DigitalTwin:
    """A digital twin representing a real-world entity."""
    twin_id: str
    legal_name: str
    date_of_birth: date
    nationality: str
    gender: Gender
    life_stage: LifeStage = LifeStage.ADULT
    life_events: List[LifeEvent] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def identity(self) -> "DigitalTwin":
        """Return self as identity (for backward compatibility)."""
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "legal_name": self.legal_name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "nationality": self.nationality,
            "gender": self.gender.value,
            "life_stage": self.life_stage.value,
            "life_events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "event_date": e.event_date.isoformat(),
                    "description": e.description,
                    "location": e.location,
                }
                for e in self.life_events
            ],
            "skills": [
                {
                    "skill_name": s.skill_name,
                    "proficiency_level": s.proficiency_level,
                    "years_experience": s.years_experience,
                }
                for s in self.skills
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DigitalTwinSystem:
    """System for managing digital twins."""

    def __init__(self):
        self._lock = threading.Lock()
        self.twins: Dict[str, DigitalTwin] = {}

    def create_twin(
        self,
        legal_name: str,
        date_of_birth: date,
        nationality: str,
        gender: Gender,
    ) -> DigitalTwin:
        """Create a new digital twin."""
        twin_id = f"twin_{datetime.now().timestamp()}"
        life_stage = self._calculate_life_stage(date_of_birth)
        twin = DigitalTwin(
            twin_id=twin_id,
            legal_name=legal_name,
            date_of_birth=date_of_birth,
            nationality=nationality,
            gender=gender,
            life_stage=life_stage,
        )
        with self._lock:
            self.twins[twin_id] = twin
        return twin

    def get_twin(self, twin_id: str) -> Optional[DigitalTwin]:
        """Get a twin by ID."""
        with self._lock:
            return self.twins.get(twin_id)

    def get_all_twins(self) -> List[DigitalTwin]:
        """Get all twins."""
        with self._lock:
            return list(self.twins.values())

    def add_life_event(
        self,
        twin_id: str,
        event_type: str,
        event_date: date,
        description: str,
        location: str = "",
    ) -> Optional[LifeEvent]:
        """Add a life event to a twin."""
        twin = self.get_twin(twin_id)
        if not twin:
            return None
        event = LifeEvent(
            event_id=f"event_{datetime.now().timestamp()}",
            event_type=event_type,
            event_date=event_date,
            description=description,
            location=location,
        )
        with self._lock:
            twin.life_events.append(event)
            twin.updated_at = datetime.now()
        return event

    def add_skill(
        self,
        twin_id: str,
        skill_name: str,
        proficiency_level: float,
        years_experience: int,
    ) -> Optional[Skill]:
        """Add a skill to a twin."""
        twin = self.get_twin(twin_id)
        if not twin:
            return None
        skill = Skill(
            skill_id=f"skill_{datetime.now().timestamp()}",
            skill_name=skill_name,
            proficiency_level=proficiency_level,
            years_experience=years_experience,
        )
        with self._lock:
            twin.skills.append(skill)
            twin.updated_at = datetime.now()
        return skill

    def get_twin_summary(self, twin_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a twin."""
        twin = self.get_twin(twin_id)
        if not twin:
            return None
        return {
            "life_stage": twin.life_stage.value,
            "social_connections_count": 0,
            "life_events_count": len(twin.life_events),
            "skills_count": len(twin.skills),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        with self._lock:
            return {
                "total_twins": len(self.twins),
                "twins": list(self.twins.keys()),
            }

    @staticmethod
    def _calculate_life_stage(dob: date) -> LifeStage:
        """Calculate life stage from date of birth."""
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 13:
            return LifeStage.CHILD
        elif age < 20:
            return LifeStage.TEENAGER
        elif age < 25:
            return LifeStage.YOUNG_ADULT
        elif age < 40:
            return LifeStage.ADULT
        elif age < 60:
            return LifeStage.MIDDLE_AGED
        elif age < 80:
            return LifeStage.SENIOR
        else:
            return LifeStage.ELDERLY


_system_instance: Optional[DigitalTwinSystem] = None
_system_lock: threading.Lock = threading.Lock()


def get_digital_twin_system() -> DigitalTwinSystem:
    """Get or create the singleton DigitalTwinSystem instance."""
    global _system_instance
    with _system_lock:
        if _system_instance is None:
            _system_instance = DigitalTwinSystem()
        return _system_instance
