"""
AsimNexus Universe Module
=========================
Manages user's complete lifecycle in AsimNexus.
Personal data, preferences, history, connections across 5 universe layers:
- PERSONAL (Self)
- FAMILY (Family connections)
- COMMUNITY (Local community)
- ENTERPRISE (Work/Company)
- SOVEREIGN (Country/Global)
"""

from __future__ import annotations

from .personal_universe import (
    PersonalUniverse, PersonalUniverseManager,
    UniverseLayer, UserState,
    get_universe_manager,
)


# Re-export from root-level module: digital_twin_system.py
from core.digital_twin_system import (
    DigitalTwin,
    DigitalTwinSystem,
    Gender,
    LifeEvent,
    LifeStage,
    Skill,
    get_digital_twin_system,
)


__all__ = [
    "PersonalUniverse",
    "PersonalUniverseManager",
    "UniverseLayer",
    "UserState",
    "get_universe_manager",
]
