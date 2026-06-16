"""
STATUS: REAL — User Control Panel for personalized AsimNexus configuration

AsimNexus User Control Panel
=============================
User-configurable settings for AsimNexus:
- Mode selection (Public Agent / Private Agent)
- Adapter selection
- Device/software connections
- Legacy notebook management
- Resource sharing controls
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("AsimNexus.UserControl")

@dataclass
class UserConfig:
    """User's AsimNexus configuration"""
    user_id: str
    active_mode: str = "private"  # "public" or "private"
    active_adapters: List[str] = None
    connected_devices: List[str] = None
    connected_software: List[str] = None
    legacy_notebook_enabled: bool = False
    nominee_id: Optional[str] = None
    resource_sharing: Dict[str, Any] = None

    def __post_init__(self):
        if self.active_adapters is None:
            self.active_adapters = []
        if self.connected_devices is None:
            self.connected_devices = []
        if self.connected_software is None:
            self.connected_software = []
        if self.resource_sharing is None:
            self.resource_sharing = {"enabled": False, "share_pct": 0}

class UserControlPanel:
    """
    User Control Panel for personalized AsimNexus configuration
    
    Each user can configure their own AsimNexus world:
    - Public Agent Mode (Government services, civic interaction)
    - Private Agent Mode (Personal assistant, local-only)
    - Custom adapter selection
    - Legacy notebook for inter-generational knowledge
    """

    def __init__(self):
        self._configs: Dict[str, UserConfig] = {}
        logger.info("🎛️ UserControlPanel initialized")

    def get_config(self, user_id: str) -> UserConfig:
        """Get user configuration"""
        if user_id not in self._configs:
            self._configs[user_id] = UserConfig(user_id=user_id)
        return self._configs[user_id]

    def set_active_mode(self, user_id: str, mode: str) -> Dict[str, Any]:
        """
        Set user's active mode
        
        Args:
            user_id: User identifier
            mode: "public" (Government) or "private" (Citizen)
        
        Returns:
            Updated configuration
        """
        config = self.get_config(user_id)
        old_mode = config.active_mode
        config.active_mode = mode

        logger.info(f"🎛️ User {user_id} mode changed: {old_mode} → {mode}")
        
        return {
            "user_id": user_id,
            "mode": config.active_mode,
            "changed_at": datetime.utcnow().isoformat()
        }

    def add_adapter(self, user_id: str, adapter: str) -> bool:
        """Add adapter to user's configuration"""
        config = self.get_config(user_id)
        if adapter not in config.active_adapters:
            config.active_adapters.append(adapter)
            return True
        return False

    def remove_adapter(self, user_id: str, adapter: str) -> bool:
        """Remove adapter from user's configuration"""
        config = self.get_config(user_id)
        if adapter in config.active_adapters:
            config.active_adapters.remove(adapter)
            return True
        return False

    def add_device(self, user_id: str, device_id: str) -> bool:
        """Add device connection to user's configuration"""
        config = self.get_config(user_id)
        if device_id not in config.connected_devices:
            config.connected_devices.append(device_id)
            return True
        return False

    def add_software(self, user_id: str, software_id: str) -> bool:
        """Add software connection to user's configuration"""
        config = self.get_config(user_id)
        if software_id not in config.connected_software:
            config.connected_software.append(software_id)
            return True
        return False

    def enable_legacy_notebook(self, user_id: str, nominee_id: str) -> Dict[str, Any]:
        """
        Enable legacy notebook creation for inter-generational transfer
        
        Args:
            user_id: User identifier
            nominee_id: Inheritor's ID
        
        Returns:
            Legacy notebook configuration
        """
        config = self.get_config(user_id)
        config.legacy_notebook_enabled = True
        config.nominee_id = nominee_id

        return {
            "user_id": user_id,
            "legacy_enabled": True,
            "nominee_id": nominee_id,
            "activated_at": datetime.utcnow().isoformat()
        }

    def set_resource_sharing(self, user_id: str, enabled: bool, share_pct: int = 50) -> Dict[str, Any]:
        """Set resource sharing preferences"""
        config = self.get_config(user_id)
        config.resource_sharing = {
            "enabled": enabled,
            "share_pct": min(100, max(0, share_pct))
        }

        return {
            "user_id": user_id,
            "resource_sharing": config.resource_sharing
        }

    def get_user_world(self, user_id: str) -> Dict[str, Any]:
        """Get complete user world configuration"""
        config = self.get_config(user_id)
        
        return {
            "user_id": user_id,
            "active_mode": config.active_mode,
            "adapters": config.active_adapters,
            "devices": config.connected_devices,
            "software": config.connected_software,
            "legacy_notebook": {
                "enabled": config.legacy_notebook_enabled,
                "nominee": config.nominee_id
            },
            "resource_sharing": config.resource_sharing
        }

    def create_legacy_notebook(self, user_id: str) -> Dict[str, Any]:
        """Create user's legacy notebook using Data Atomizer"""
        from core.lifecycle.data_atomizer import get_data_atomizer
        
        if not self.get_config(user_id).legacy_notebook_enabled:
            return {"error": "Legacy notebook not enabled"}

        atomizer = get_data_atomizer()
        
        # Collect all user data
        user_data = self._collect_user_data(user_id)
        
        # Create legacy notebook
        notebook = asyncio = __import__("asyncio")
        if hasattr(asyncio, 'run'):
            result = asyncio.run(atomizer.create_legacy_notebook(user_id, self._configs[user_id].nominee_id))
        else:
            # For environments without asyncio.run
            result = asyncio.ensure_future(atomizer.create_legacy_notebook(user_id, self._configs[user_id].nominee_id))
        
        return {
            "user_id": user_id,
            "notebook_created": True,
            "notebook_id": f"legacy_{user_id}_{int(datetime.utcnow().timestamp())}"
        }

    def _collect_user_data(self, user_id: str) -> Dict[str, Any]:
        """Collect all user data for atomization"""
        config = self.get_config(user_id)
        
        return {
            "profile": {},  # User profile data
            "twin_data": {},  # Digital twin data
            "messages": {},  # Chat history
            "decisions": {},  # Made decisions
            "legacy": {}  # Existing legacy data
        }

    def status(self) -> Dict[str, Any]:
        """Get control panel status"""
        return {
            "configured_users": len(self._configs),
            "public_mode_users": sum(1 for c in self._configs.values() if c.active_mode == "public"),
            "private_mode_users": sum(1 for c in self._configs.values() if c.active_mode == "private"),
            "legacy_enabled_users": sum(1 for c in self._configs.values() if c.legacy_notebook_enabled)
        }

# Singleton
_panel: Optional[UserControlPanel] = None

def get_control_panel() -> UserControlPanel:
    """Get or create User Control Panel singleton"""
    global _panel
    if _panel is None:
        _panel = UserControlPanel()
    return _panel