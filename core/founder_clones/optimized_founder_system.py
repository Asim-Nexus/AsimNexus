"""
ASIMNEXUS Optimized Founder System
===================================
5 Optimized Founder Digital Clones for autonomous company operation.
Each founder has a specific role, strategy, and configuration.

Roles:
  - CEO_STRATEGY: Strategic direction, high-level decisions
  - CTO_INNOVATION: Technology innovation, architecture
  - CFO_OPERATIONS: Financial operations, resource management
  - CPO_MARKET: Product management, market strategy
  - CDO_ANALYTICS: Data analytics, insights, reporting
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.OptimizedFounderSystem")


class OptimizedFounderRole(Enum):
    """Roles for the 5 optimized founder clones."""
    CEO_STRATEGY = "ceo_strategy"
    CTO_INNOVATION = "cto_innovation"
    CFO_OPERATIONS = "cfo_operations"
    CPO_MARKET = "cpo_market"
    CDO_ANALYTICS = "cdo_analytics"


@dataclass
class OptimizedFounderConfig:
    """Configuration for an optimized founder clone."""
    role: OptimizedFounderRole
    name: str
    description: str
    system_prompt: str = ""
    model_preference: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2048
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizedFounderClone:
    """An optimized founder clone instance."""
    config: OptimizedFounderConfig
    status: str = "idle"
    memory: Dict[str, Any] = field(default_factory=dict)
    task_history: List[Dict[str, Any]] = field(default_factory=list)

    def assign_task(self, task: Dict[str, Any]) -> None:
        """Assign a task to this founder clone."""
        self.task_history.append(task)
        self.status = "active"

    def complete_task(self, task_id: str, result: Any) -> None:
        """Mark a task as completed."""
        for task in self.task_history:
            if task.get("id") == task_id:
                task["status"] = "completed"
                task["result"] = result
                break
        self.status = "idle"

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of this founder clone."""
        return {
            "role": self.config.role.value,
            "name": self.config.name,
            "status": self.status,
            "tasks_completed": len([t for t in self.task_history if t.get("status") == "completed"]),
            "tasks_pending": len([t for t in self.task_history if t.get("status") != "completed"]),
        }


class OptimizedFounderCloneSystem:
    """Manages all 5 optimized founder clones."""

    DEFAULT_CONFIGS: Dict[OptimizedFounderRole, Dict[str, Any]] = {
        OptimizedFounderRole.CEO_STRATEGY: {
            "name": "CEO Strategist",
            "description": "Strategic direction, high-level decisions, vision",
            "system_prompt": "You are the CEO Strategist. Focus on strategic direction and high-level decisions.",
            "model_preference": "gpt-4",
            "temperature": 0.7,
        },
        OptimizedFounderRole.CTO_INNOVATION: {
            "name": "CTO Innovator",
            "description": "Technology innovation, architecture, technical strategy",
            "system_prompt": "You are the CTO Innovator. Focus on technology innovation and architecture.",
            "model_preference": "gpt-4",
            "temperature": 0.8,
        },
        OptimizedFounderRole.CFO_OPERATIONS: {
            "name": "CFO Operator",
            "description": "Financial operations, resource management, budgeting",
            "system_prompt": "You are the CFO Operator. Focus on financial operations and resource management.",
            "model_preference": "gpt-4",
            "temperature": 0.5,
        },
        OptimizedFounderRole.CPO_MARKET: {
            "name": "CPO Marketer",
            "description": "Product management, market strategy, user research",
            "system_prompt": "You are the CPO Marketer. Focus on product management and market strategy.",
            "model_preference": "gpt-4",
            "temperature": 0.7,
        },
        OptimizedFounderRole.CDO_ANALYTICS: {
            "name": "CDO Analyst",
            "description": "Data analytics, insights, reporting, metrics",
            "system_prompt": "You are the CDO Analyst. Focus on data analytics and insights.",
            "model_preference": "gpt-4",
            "temperature": 0.4,
        },
    }

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self.founders: Dict[OptimizedFounderRole, OptimizedFounderClone] = {}
        self._initialize_founders()

    def _initialize_founders(self) -> None:
        """Create all 5 founder clones with their configurations."""
        for role, config_data in self.DEFAULT_CONFIGS.items():
            config = OptimizedFounderConfig(
                role=role,
                **config_data,
            )
            self.founders[role] = OptimizedFounderClone(config=config)
        logger.info(f"Initialized {len(self.founders)} optimized founder clones")

    def get_founder(self, role: OptimizedFounderRole) -> Optional[OptimizedFounderClone]:
        """Get a founder clone by role."""
        return self.founders.get(role)

    def get_all_founders(self) -> List[OptimizedFounderClone]:
        """Get all founder clones."""
        return list(self.founders.values())

    def assign_task_to_founder(self, role: OptimizedFounderRole, task: Dict[str, Any]) -> bool:
        """Assign a task to a specific founder."""
        founder = self.get_founder(role)
        if founder:
            founder.assign_task(task)
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get the status of all founder clones."""
        return {
            "total_founders": len(self.founders),
            "founders": {
                role.value: clone.get_status()
                for role, clone in self.founders.items()
            },
        }


# Singleton instance
_optimized_founder_system: Optional[OptimizedFounderCloneSystem] = None


def get_optimized_founder_system(api_keys: Optional[Dict[str, str]] = None) -> OptimizedFounderCloneSystem:
    """Get or create the singleton OptimizedFounderCloneSystem."""
    global _optimized_founder_system
    if _optimized_founder_system is None:
        _optimized_founder_system = OptimizedFounderCloneSystem(api_keys=api_keys)
    return _optimized_founder_system


def reset_optimized_founder_system() -> None:
    """Reset the singleton (for testing)."""
    global _optimized_founder_system
    _optimized_founder_system = None
