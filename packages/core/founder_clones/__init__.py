
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Founder Clones - 5 Optimized Founder Digital Clones (consolidated from 15)
Implements the 5 optimized founder clones for ASIMNEXUS autonomous company
"""

from .founder_clone import FounderClone, FounderCloneConfig, FounderRole, DecisionStyle
from .founder_manager import FounderCloneManager, get_founder_manager
from .auto_update import FounderAutoUpdate
from .recovery import FounderRecovery
from .integration import FounderIntegration
from .dashboard import FounderDashboard
from .company_group_chat import CompanyGroupChat, GroupMessage, MessagePriority, FounderAccount

# New Autonomous System (5 Optimized Founders)
from .optimized_founder_system import (
    OptimizedFounderRole, OptimizedFounderConfig, OptimizedFounderClone,
    OptimizedFounderCloneSystem, get_optimized_founder_system
)
from .autonomous_task_engine import AutonomousTaskEngine, get_autonomous_task_engine
from .unified_api_key_manager import UnifiedAPIKeyManager, get_unified_api_key_manager

# === 15 World-Role Founder Clones (AsimNexus Vision) ===
from .world_clones import (
    WorldClone, WorldCloneOrchestrator, CloneRole, CloneConfig,
    WORLD_CLONE_CONFIGS, get_world_clones
)

__all__ = [
    'FounderClone',
    'FounderCloneConfig',
    'FounderRole',
    'DecisionStyle',
    'FounderCloneManager',
    'get_founder_manager',
    'FounderAutoUpdate',
    'FounderRecovery',
    'FounderIntegration',
    'FounderDashboard',
    'CompanyGroupChat',
    'GroupMessage',
    'MessagePriority',
    'FounderAccount',
    # New Autonomous System
    'OptimizedFounderRole',
    'OptimizedFounderConfig',
    'OptimizedFounderClone',
    'OptimizedFounderCloneSystem',
    'get_optimized_founder_system',
    'AutonomousTaskEngine',
    'get_autonomous_task_engine',
    'UnifiedAPIKeyManager',
    'get_unified_api_key_manager',
    # 15 World-Role Clones
    'WorldClone',
    'WorldCloneOrchestrator',
    'CloneRole',
    'CloneConfig',
    'WORLD_CLONE_CONFIGS',
    'get_world_clones',
]
