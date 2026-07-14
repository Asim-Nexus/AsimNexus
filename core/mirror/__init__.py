"""
AsimNexus Mirror Module
=======================
Digital Twin for every user with full self-evolution capabilities.
- LoRA/QLoRA Auto Fine-Tuning
- Dreaming Engine for pattern discovery
- Log analysis from StructuredLogger
- Integration with Data Lake for OLAP analytics
- Code improvement via evolution engine
"""

from __future__ import annotations

from .consciousness import ConsciousnessLayer, Thought, ThoughtType
from .mirror_module import MirrorModule, MirrorReflection, EvolutionSuggestion, get_mirror
from .lora_engine import MirrorLoRA
from .dreaming_engine import DreamingEngine, Dream, DreamType

__all__ = [
    "ConsciousnessLayer",
    "Thought",
    "ThoughtType",
    "MirrorModule",
    "MirrorReflection",
    "EvolutionSuggestion",
    "get_mirror",
    "MirrorLoRA",
    "DreamingEngine",
    "Dream",
    "DreamType",
]
