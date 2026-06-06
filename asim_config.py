
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified Configuration
=================================
Single source of truth for all ASIM settings.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AsimConfig:
    """Unified ASIMNEXUS configuration"""
    
    # Cloud settings
    cloud_enabled: bool = True
    cloud_url: str = "https://api.asim-nexus.ai"
    cloud_api_key: Optional[str] = None
    
    # WAMP settings
    wamp_enabled: bool = False
    wamp_url: str = "ws://localhost:8080/ws"
    wamp_realm: str = "asim_nexus"
    
    # Security settings
    security_mode: str = "strict"  # strict | relaxed | debug
    require_mtls: bool = True
    require_oauth2: bool = True
    
    # LLM providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # Local model
    local_model_enabled: bool = True
    local_model_path: Optional[str] = None
    
    # Nepal-first defaults
    default_locale: str = "ne-NP"
    default_language: str = "ne"
    default_currency: str = "NPR"
    
    # Storage
    memory_path: str = "memory"
    clone_storage_path: str = "memory/clones"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "AsimConfig":
        """Load config from environment variables"""
        return cls(
            cloud_enabled=os.getenv("ASIM_CLOUD_ENABLED", "true").lower() == "true",
            cloud_url=os.getenv("ASIM_CLOUD_URL", "https://api.asim-nexus.ai"),
            cloud_api_key=os.getenv("ASIM_CLOUD_API_KEY"),
            wamp_enabled=os.getenv("ASIM_WAMP_ENABLED", "false").lower() == "true",
            wamp_url=os.getenv("ASIM_WAMP_URL", "ws://localhost:8080/ws"),
            security_mode=os.getenv("ASIM_SECURITY_MODE", "strict"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            default_locale=os.getenv("ASIM_LOCALE", "ne-NP"),
            log_level=os.getenv("ASIM_LOG_LEVEL", "INFO")
        )
    
    @classmethod
    def from_file(cls, path: str = "asim_config.yaml") -> "AsimConfig":
        """Load config from YAML file"""
        if not os.path.exists(path):
            return cls.from_env()
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

# Global config instance
_config: Optional[AsimConfig] = None

def get_config() -> AsimConfig:
    """Get global config (lazy load)"""
    global _config
    if _config is None:
        _config = AsimConfig.from_env()
    return _config

def set_config(config: AsimConfig):
    """Set global config"""
    global _config
    _config = config

# Load on import
config = get_config()
