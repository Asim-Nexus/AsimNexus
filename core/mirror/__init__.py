"""
AsimNexus Mirror Module
=======================
Digital Twin for every user - reflection and evolution engine.
"""

from .mirror_module import MirrorModule, MirrorReflection
from .consciousness import ConsciousnessLayer, Thought, ThoughtType, MirrorState, MirrorDailyReport
from .lora_engine import MirrorLoRA
from .dreaming_engine import DreamingEngine, Dream, DreamType

__all__ = [
    "MirrorModule",
    "ConsciousnessLayer", 
    "MirrorLoRA",
    "DreamingEngine",
    "MirrorReflection",
    "Thought",
    "ThoughtType",
    "MirrorState",
    "MirrorDailyReport",
    "Dream",
    "DreamType",
]