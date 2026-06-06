
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Mode System
=====================
Mode management and switching
Manages different operational modes for the system
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ModeSystem")


class SystemMode(Enum):
    """System operational modes"""
    NORMAL = "normal"
    SAFE = "safe"
    PERFORMANCE = "performance"
    DEBUG = "debug"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


class ModeTransition(Enum):
    """Mode transition types"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    CONDITIONAL = "conditional"


@dataclass
class ModeConfig:
    """Configuration for a mode"""
    mode: SystemMode
    settings: Dict[str, Any] = field(default_factory=dict)
    restrictions: List[str] = field(default_factory=list)
    enabled: bool = True


class ModeManager:
    """
    Mode Manager
    
    Provides:
    - Mode switching
    - Mode configuration
    - Transition management
    - Mode restrictions
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ModeManager")
        self.current_mode: SystemMode = SystemMode.NORMAL
        self.mode_configs: Dict[SystemMode, ModeConfig] = {}
        self.transition_history: List[Dict] = []
        self._initialize_default_modes()
    
    def _initialize_default_modes(self):
        """Initialize default mode configurations"""
        default_modes = [
            ModeConfig(
                mode=SystemMode.NORMAL,
                settings={"cpu_limit": 80, "memory_limit": 80},
                restrictions=[]
            ),
            ModeConfig(
                mode=SystemMode.SAFE,
                settings={"cpu_limit": 50, "memory_limit": 50},
                restrictions=["no_autonomous_actions", "require_approval"]
            ),
            ModeConfig(
                mode=SystemMode.PERFORMANCE,
                settings={"cpu_limit": 100, "memory_limit": 100},
                restrictions=[]
            ),
            ModeConfig(
                mode=SystemMode.DEBUG,
                settings={"logging_level": "DEBUG", "verbose": True},
                restrictions=["no_production"]
            ),
            ModeConfig(
                mode=SystemMode.MAINTENANCE,
                settings={"read_only": True},
                restrictions=["no_user_requests"]
            ),
            ModeConfig(
                mode=SystemMode.EMERGENCY,
                settings={"minimal_operations": True},
                restrictions=["critical_only"]
            )
        ]
        
        for config in default_modes:
            self.mode_configs[config.mode] = config
        
        self.logger.info(f"Initialized {len(default_modes)} modes")
    
    def switch_mode(
        self,
        new_mode: SystemMode,
        transition_type: ModeTransition = ModeTransition.MANUAL,
        reason: Optional[str] = None
    ) -> bool:
        """
        Switch to a new mode
        
        Args:
            new_mode: Mode to switch to
            transition_type: Type of transition
            reason: Reason for transition
            
        Returns:
            True if successful
        """
        if new_mode not in self.mode_configs:
            self.logger.error(f"Unknown mode: {new_mode}")
            return False
        
        if not self.mode_configs[new_mode].enabled:
            self.logger.error(f"Mode {new_mode} is disabled")
            return False
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        # Record transition
        self.transition_history.append({
            "from_mode": old_mode.value,
            "to_mode": new_mode.value,
            "transition_type": transition_type.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"Switched mode: {old_mode.value} -> {new_mode.value}")
        return True
    
    def get_current_mode(self) -> Dict:
        """Get current mode information"""
        config = self.mode_configs[self.current_mode]
        return {
            "mode": self.current_mode.value,
            "settings": config.settings,
            "restrictions": config.restrictions,
            "enabled": config.enabled
        }
    
    def get_mode_config(self, mode: SystemMode) -> Optional[Dict]:
        """Get configuration for a specific mode"""
        if mode not in self.mode_configs:
            return None
        
        config = self.mode_configs[mode]
        return {
            "mode": config.mode.value,
            "settings": config.settings,
            "restrictions": config.restrictions,
            "enabled": config.enabled
        }
    
    def update_mode_config(
        self,
        mode: SystemMode,
        settings: Optional[Dict[str, Any]] = None,
        restrictions: Optional[List[str]] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """Update mode configuration"""
        if mode not in self.mode_configs:
            return False
        
        config = self.mode_configs[mode]
        
        if settings is not None:
            config.settings.update(settings)
        
        if restrictions is not None:
            config.restrictions = restrictions
        
        if enabled is not None:
            config.enabled = enabled
        
        self.logger.info(f"Updated mode config: {mode.value}")
        return True
    
    def check_restriction(self, restriction: str) -> bool:
        """Check if a restriction is active in current mode"""
        config = self.mode_configs[self.current_mode]
        return restriction in config.restrictions
    
    def list_modes(self) -> List[Dict]:
        """List all available modes"""
        return [
            {
                "mode": mode.value,
                "enabled": config.enabled,
                "restrictions_count": len(config.restrictions)
            }
            for mode, config in self.mode_configs.items()
        ]
    
    def get_transition_history(self, limit: int = 50) -> List[Dict]:
        """Get mode transition history"""
        return self.transition_history[-limit:]
    
    def get_stats(self) -> Dict:
        """Get mode manager statistics"""
        return {
            "current_mode": self.current_mode.value,
            "total_modes": len(self.mode_configs),
            "enabled_modes": sum(1 for c in self.mode_configs.values() if c.enabled),
            "total_transitions": len(self.transition_history)
        }
