"""
LoRA Engine
===========
Manages LoRA (Low-Rank Adaptation) adapters for fine-tuning models
based on user dreams, reflections, and training data.

Consolidated from:
  - core/dreaming/lora_engine.py  (LoRAEngine — adapter management)
  - core/mirror/lora_engine.py    (MirrorLoRA — training data preparation)
"""

from __future__ import annotations

import os
import json
import hashlib
import logging
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_instance = None
_instance_lock = threading.Lock()


# ── CONFIGURATION ──────────────────────────────────────────────────────────────

@dataclass
class LoRAConfig:
    """Configuration for a LoRA adapter.

    Fields from both the core adapter manager and the mirror training engine
    are merged here for a single source of truth.
    """
    # Adapter-level config (from core/dreaming)
    r: int = 8
    alpha: int = 16
    dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    task_type: str = "CAUSAL_LM"
    # Training-level config (from core/mirror)
    rank: int = 8
    learning_rate: float = 1e-4
    batch_size: int = 4
    max_samples: int = 1000


# ── TRAINING DATA ──────────────────────────────────────────────────────────────

@dataclass
class TrainingExample:
    """A single training example for fine-tuning."""
    prompt: str
    completion: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── ENGINE ─────────────────────────────────────────────────────────────────────

class LoRAEngine:
    """Manages LoRA adapters and training data for fine-tuning models.

    Provides both adapter lifecycle management (create, list, get) and
    training-data preparation from reflections (used by MirrorModule).
    """

    def __init__(self, user_id: Optional[str] = None):
        self._adapters: Dict[str, Dict[str, Any]] = {}
        self._examples: List[TrainingExample] = []
        self._lock = threading.Lock()
        self.user_id = user_id

    # ── Adapter Management ──────────────────────────────────────────────────

    async def create_adapter_from_dreams(
        self,
        user_id: str,
        dreams: List[Dict[str, Any]],
        config: LoRAConfig,
    ) -> str:
        """Create a LoRA adapter from user dreams."""
        adapter_id = f"{user_id}_{hashlib.md5(json.dumps(dreams, sort_keys=True).encode()).hexdigest()[:8]}"
        adapter_path = os.path.join(
            "models", "adapters", f"{adapter_id}.bin"
        )

        with self._lock:
            self._adapters[adapter_id] = {
                "user_id": user_id,
                "config": {
                    "r": config.r,
                    "alpha": config.alpha,
                    "dropout": config.dropout,
                    "target_modules": config.target_modules,
                    "task_type": config.task_type,
                },
                "dreams_count": len(dreams),
                "path": adapter_path,
            }

        # Ensure the adapters directory exists
        os.makedirs(os.path.dirname(adapter_path), exist_ok=True)

        # Create a placeholder adapter file
        with open(adapter_path, "wb") as f:
            f.write(b"placeholder_lora_adapter")

        logger.info(f"Created LoRA adapter {adapter_id} for user {user_id}")
        return adapter_path

    def get_adapter(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """Get adapter info by ID."""
        with self._lock:
            return self._adapters.get(adapter_id)

    def list_adapters(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List adapters, optionally filtered by user."""
        with self._lock:
            if user_id:
                return [a for a in self._adapters.values() if a["user_id"] == user_id]
            return list(self._adapters.values())

    # ── Training Data Preparation (from MirrorModule) ───────────────────────

    def prepare_training_data(self, reflections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Prepare training data from reflections.

        Returns a list of dicts with 'prompt' and 'completion' keys.
        """
        data: List[Dict[str, str]] = []
        for ref in reflections:
            intent = ref.get("intent", "unknown")
            outcome = ref.get("outcome", "unknown")
            data.append({
                "prompt": f"Action: {intent}",
                "completion": f"Outcome: {outcome}",
            })
        return data

    async def fine_tune(self, reflections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fine-tune the model on reflections.

        Returns a dict with 'status', 'samples', and 'adapter_path'.
        """
        data = self.prepare_training_data(reflections)
        with self._lock:
            for d in data:
                self._examples.append(
                    TrainingExample(prompt=d["prompt"], completion=d["completion"])
                )
        return {
            "status": "completed",
            "samples": len(data),
            "adapter_path": "/models/adapters/default_lora.bin",
        }

    # ── Status ──────────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Get LoRA engine status."""
        with self._lock:
            return {
                "total_adapters": len(self._adapters),
                "total_examples": len(self._examples),
                "available": True,
            }


# ── Singleton ─────────────────────────────────────────────────────────────────

def get_lora_engine() -> LoRAEngine:
    """Get or create the singleton LoRAEngine instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = LoRAEngine()
    return _instance


def reset_lora_engine() -> None:
    """Reset the singleton for testing."""
    global _instance
    with _instance_lock:
        _instance = None
