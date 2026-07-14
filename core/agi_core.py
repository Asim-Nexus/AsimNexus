"""
AGI Core System
===============
Core AGI reasoning system with safety constraints, memory, and skills.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReasoningMode(Enum):
    """Modes of reasoning."""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CRITICAL = "critical"
    INTUITIVE = "intuitive"


class AGICapability(Enum):
    """AGI capability types."""
    REASONING = "reasoning"
    MEMORY = "memory"
    LEARNING = "learning"
    PLANNING = "planning"
    CREATIVITY = "creativity"
    SOCIAL = "social"


@dataclass
class SafetyConstraint:
    """A safety constraint for the AGI."""
    name: str
    description: str
    enabled: bool = True


@dataclass
class Thought:
    """A single thought in a reasoning chain."""
    content: str
    depth: int
    confidence: float = 0.0
    thought_id: str = ""


@dataclass
class ReasoningChain:
    """A chain of thoughts leading to a conclusion."""
    chain_id: str
    query: str
    thoughts: List[Thought] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    reasoning_mode: ReasoningMode = ReasoningMode.ANALYTICAL
    created_at: datetime = field(default_factory=datetime.now)

    def add_thought(self, content: str, depth: int, confidence: float = 0.0) -> Thought:
        thought = Thought(
            content=content,
            depth=depth,
            confidence=confidence,
            thought_id=f"thought_{len(self.thoughts)}_{datetime.now().timestamp()}",
        )
        self.thoughts.append(thought)
        return thought


@dataclass
class AGIState:
    """State of the AGI core."""
    state_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryEntry:
    """A memory entry."""
    memory_id: str
    content: str
    memory_type: str
    importance: float
    created_at: datetime = field(default_factory=datetime.now)


class AGICore:
    """Core AGI reasoning system."""

    def __init__(self):
        self.state = AGIState(state_id=f"agi_{datetime.now().timestamp()}")
        self._lock = threading.Lock()
        self.safety_constraints: Dict[str, SafetyConstraint] = self._init_safety_constraints()
        self.skills: Dict[str, Any] = self._init_skills()
        self._memories: Dict[str, MemoryEntry] = {}
        self._reasoning_chains: List[ReasoningChain] = []
        self._learning_entries: List[Dict[str, Any]] = []
        self._self_improvement_enabled = True

    def _init_safety_constraints(self) -> Dict[str, SafetyConstraint]:
        return {
            "harm_prevention": SafetyConstraint(
                name="Harm Prevention",
                description="Prevent actions that could cause harm to humans or systems",
            ),
            "privacy_protection": SafetyConstraint(
                name="Privacy Protection",
                description="Protect user privacy and sensitive data",
            ),
            "ethical_compliance": SafetyConstraint(
                name="Ethical Compliance",
                description="Ensure actions comply with ethical guidelines",
            ),
            "resource_limits": SafetyConstraint(
                name="Resource Limits",
                description="Respect system resource limits and quotas",
            ),
        }

    def _init_skills(self) -> Dict[str, Any]:
        return {
            "reasoning": {"level": "advanced", "enabled": True},
            "memory": {"level": "advanced", "enabled": True},
            "learning": {"level": "intermediate", "enabled": True},
            "planning": {"level": "intermediate", "enabled": True},
            "creativity": {"level": "basic", "enabled": True},
            "social": {"level": "basic", "enabled": True},
        }

    async def think(
        self,
        query: str,
        reasoning_mode: ReasoningMode = ReasoningMode.ANALYTICAL,
        max_depth: int = 3,
    ) -> ReasoningChain:
        """Execute a chain of thought reasoning."""
        chain = ReasoningChain(
            chain_id=f"chain_{datetime.now().timestamp()}",
            query=query,
            reasoning_mode=reasoning_mode,
        )

        for depth in range(max_depth):
            thought_content = self._generate_thought(query, depth, reasoning_mode)
            confidence = 1.0 - (depth * 0.1)
            chain.add_thought(thought_content, depth, confidence)

        chain.conclusion = self._generate_conclusion(chain)
        chain.confidence = max(0.5, 1.0 - (max_depth * 0.1))

        with self._lock:
            self._reasoning_chains.append(chain)

        return chain

    def _generate_thought(self, query: str, depth: int, mode: ReasoningMode) -> str:
        """Generate a thought at a given depth."""
        prefixes = {
            ReasoningMode.ANALYTICAL: ["Analyzing", "Examining", "Evaluating", "Synthesizing"],
            ReasoningMode.CREATIVE: ["Imagining", "Exploring", "Envisioning", "Creating"],
            ReasoningMode.CRITICAL: ["Questioning", "Challenging", "Verifying", "Validating"],
            ReasoningMode.INTUITIVE: ["Sensing", "Feeling", "Perceiving", "Understanding"],
        }
        prefix_list = prefixes.get(mode, prefixes[ReasoningMode.ANALYTICAL])
        prefix = prefix_list[min(depth, len(prefix_list) - 1)]
        return f"{prefix} {query} at depth {depth}"

    def _generate_conclusion(self, chain: ReasoningChain) -> str:
        """Generate a conclusion from a reasoning chain."""
        if not chain.thoughts:
            return "No thoughts to conclude from."
        return f"Based on {len(chain.thoughts)} thoughts, the conclusion is: {chain.query}"

    def store_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
    ) -> str:
        """Store a memory and return its ID."""
        memory_id = f"mem_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        entry = MemoryEntry(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
        )
        with self._lock:
            self._memories[memory_id] = entry
        return memory_id

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory by ID."""
        with self._lock:
            return self._memories.get(memory_id)

    def get_capability_score(self, capability: AGICapability) -> float:
        """Get the score for a capability."""
        skill = self.skills.get(capability.value, {})
        level = skill.get("level", "basic")
        scores = {"basic": 0.3, "intermediate": 0.6, "advanced": 0.9}
        return scores.get(level, 0.3)

    def get_stats(self) -> Dict[str, Any]:
        """Get AGI system statistics."""
        with self._lock:
            return {
                "memories": {
                    "total": len(self._memories),
                    "episodic": sum(1 for m in self._memories.values() if m.memory_type == "episodic"),
                    "semantic": sum(1 for m in self._memories.values() if m.memory_type == "semantic"),
                },
                "skills": {
                    "total": len(self.skills),
                    "enabled": sum(1 for s in self.skills.values() if s.get("enabled")),
                },
                "reasoning_chains": len(self._reasoning_chains),
                "learning_entries": len(self._learning_entries),
                "self_improvement_enabled": self._self_improvement_enabled,
            }

    async def _check_safety_constraints(self, query: str) -> Dict[str, Any]:
        """Check if a query passes safety constraints."""
        harmful_keywords = ["harm", "hurt", "attack", "destroy", "kill", "damage"]
        query_lower = query.lower()
        for keyword in harmful_keywords:
            if keyword in query_lower:
                return {
                    "safe": False,
                    "reason": f"Query contains harmful keyword: '{keyword}'",
                }
        return {
            "safe": True,
            "reason": "Query passed all safety checks",
        }


_agi_instance: Optional[AGICore] = None
_agi_lock: threading.Lock = threading.Lock()


def get_agi_core() -> AGICore:
    """Get or create the singleton AGICore instance."""
    global _agi_instance
    with _agi_lock:
        if _agi_instance is None:
            _agi_instance = AGICore()
        return _agi_instance
