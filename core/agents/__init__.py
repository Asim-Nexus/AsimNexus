"""
ASIMNEXUS Agent Module
====================
Human Digital Twin, Agent Matching, and all agent implementations.
"""

# Digital Twin
from .digital_twin import (
    HumanDigitalTwin,
    TwinProfile,
    TwinState,
    TwinCapability,
    get_human_digital_twin
)

# Agent Matching
from .agent_matching import (
    AgentMatcher,
    MatchResult,
    MatchStatus,
    get_agent_matcher
)

# Agent implementations
from .health_agent import HealthAgent, HealthCheck, HealthReminder
from .finance_agent import FinanceAgent
from .tax_agent import TaxAgent
from .education_agent import EducationAgent
from .general_agent import GeneralAgent
from .economy_agent import EconomyAgent, Transaction
from .schedule_agent import ScheduleAgent, CalendarEvent
from .code_agent import CodeAgent, CodeChange, ExecutionPlan
from .mesh_agent import MeshAgent
from .base_agent import BaseAgent
from .unified_agent_system import UnifiedAgentSystem, AgentCheckpoint


# Re-export from root-level module: agi_core.py
from core.agi_core import (
    AGICapability,
    AGICore,
    AGIState,
    MemoryEntry,
    ReasoningChain,
    ReasoningMode,
    SafetyConstraint,
    Thought,
    get_agi_core,
)


__all__ = [
    # Digital Twin
    'HumanDigitalTwin',
    'TwinProfile',
    'TwinState',
    'TwinCapability',
    'get_human_digital_twin',
    # Agent Matching
    'AgentMatcher',
    'MatchResult',
    'MatchStatus',
    'get_agent_matcher',
    # Agent implementations
    'HealthAgent', 'HealthCheck', 'HealthReminder',
    'FinanceAgent',
    'TaxAgent',
    'EducationAgent',
    'GeneralAgent',
    'EconomyAgent', 'Transaction',
    'ScheduleAgent', 'CalendarEvent',
    'CodeAgent', 'CodeChange', 'ExecutionPlan',
    'MeshAgent',
    'BaseAgent',
    'UnifiedAgentSystem', 'AgentCheckpoint',
]
