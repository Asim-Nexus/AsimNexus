"""
Personal LoRA Adapter — Mirror Module Shim
===========================================
Backward-compatible re-export from the consolidated core LoRA engine.

The canonical implementation now lives at:
    core/dreaming/lora_engine.py

All types and classes are re-exported here so existing imports from
``core.mirror.lora_engine`` continue to work without modification.
"""

from __future__ import annotations

from core.dreaming.lora_engine import (
    LoRAEngine,
    LoRAConfig,
    TrainingExample,
)

# MirrorLoRA is an alias for LoRAEngine to preserve backward compatibility
MirrorLoRA = LoRAEngine

__all__ = [
    "LoRAEngine",
    "MirrorLoRA",
    "LoRAConfig",
    "TrainingExample",
]
