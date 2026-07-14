"""
AsimNexus Founder Clones Module
================================
15 Specialized AI Agents for Autonomous Company Operations
and 15 World-Role Founder Clones covering every dimension of human life.
"""

from .founder_clone_system import (
    FounderCloneSystem,
    FounderClone,
    FounderConfig,
    FounderRole,
)
from .world_clones import (
    WorldCloneOrchestrator,
    WorldClone,
    CloneConfig,
    CloneRole,
    get_world_clones,
)


# Re-export from root-level module: universal_clone_system.py
from core.universal_clone_system import (
    CloneResult,
    PatternRecognizer,
    PatternSignature,
    PatternTranslator,
    PatternType,
    UniversalCloneSystem,
    UniversalOS,
)


__all__ = [
    "FounderCloneSystem",
    "FounderClone",
    "FounderConfig",
    "FounderRole",
    "WorldCloneOrchestrator",
    "WorldClone",
    "CloneConfig",
    "CloneRole",
    "get_world_clones",
]
