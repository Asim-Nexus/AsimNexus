"""
Digital Consciousness Layer
===========================
Manages thoughts and principles for the Mirror Module.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ThoughtType(Enum):
    """Types of thoughts in the consciousness layer."""
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    INSIGHT = "insight"
    PRINCIPLE = "principle"
    CONTRADICTION = "contradiction"
    INTENTION = "intention"


@dataclass
class Thought:
    """A single thought in the consciousness layer."""
    thought_type: ThoughtType
    content: str
    thought_id: str = ""
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.thought_id:
            self.thought_id = f"thought_{datetime.now().timestamp()}"
        if not self.timestamp:
            self.timestamp = datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought_id": self.thought_id,
            "thought_type": self.thought_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class ConsciousnessLayer:
    """Digital consciousness layer managing thoughts and principles."""

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or "default"
        self._lock = threading.Lock()
        self.conscious_thoughts: List[Thought] = []
        self.principles: List[str] = []

    def add_thought(self, thought: Thought) -> None:
        """Add a thought to consciousness."""
        with self._lock:
            self.conscious_thoughts.append(thought)

    def update_principles(self, action: Dict[str, Any]) -> List[str]:
        """Update principles based on an action and return the principles list."""
        intent = action.get("intent", "")
        if intent:
            # Extract a principle from the intent
            principle = f"Act with intention: {intent}"
            with self._lock:
                if principle not in self.principles:
                    self.principles.append(principle)
        return self.principles.copy()

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of consciousness."""
        with self._lock:
            return {
                "user_id": self.user_id,
                "principles_count": len(self.principles),
                "thoughts_count": len(self.conscious_thoughts),
                "thoughts": [t.to_dict() for t in self.conscious_thoughts],
                "principles": self.principles.copy(),
            }
