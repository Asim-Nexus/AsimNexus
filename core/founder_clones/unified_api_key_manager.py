
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified API Key Manager
==================================
Central management for ALL external API keys, MCP connections, and model routing.
Single point of control for the entire ASIMNEXUS autonomous system.

Manages:
- 21 NVIDIA NIM API keys (with model assignments)
- OpenAI, Anthropic, Google Gemini keys
- MCP (Model Context Protocol) connections
- Custom API connections
- Key rotation, health checks, rate limiting
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """API Providers"""
    NVIDIA_NIM = "nvidia_nim"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    CUSTOM = "custom"
    MCP = "mcp"


class KeyStatus(Enum):
    """API Key Status"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    EXPIRED = "expired"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class APIKeyEntry:
    """Single API Key Entry"""
    key_id: str
    provider: str
    api_key: str
    base_url: str
    model: str = ""
    key_type: str = "general"  # reasoning, coding, general, reasoning_flash, reasoning_tools
    status: str = "active"
    usage_count: int = 0
    last_used: Optional[str] = None
    last_error: Optional[str] = None
    rate_limit_reset: Optional[float] = None
    capabilities: List[str] = field(default_factory=list)
    params: Dict = field(default_factory=dict)
    description: str = ""
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPConnection:
    """MCP (Model Context Protocol) Connection"""
    id: str
    name: str
    url: str
    protocol: str = "http"
    api_key: str = ""
    status: str = "active"
    capabilities: List[str] = field(default_factory=list)
    last_connected: Optional[str] = None


class UnifiedAPIKeyManager:
    """
    Unified API Key Manager for ASIMNEXUS
    Manages all external API connections from a single point
    """
    
    def __init__(self, storage_path: str = "./data/api_keys.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.api_keys: Dict[str, APIKeyEntry] = {}
        self.mcp_connections: Dict[str, MCPConnection] = {}
        
        self._load_storage()
        self._initialize_default_keys()
        
        logger.info(f"UnifiedAPIKeyManager initialized: {len(self.api_keys)} keys, {len(self.mcp_connections)} MCP connections")
    
    def _load_storage(self):
        """Load saved API keys and connections"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for key_id, key_data in data.get('api_keys', {}).items():
                    self.api_keys[key_id] = APIKeyEntry(**key_data)
                
                for mcp_id, mcp_data in data.get('mcp_connections', {}).items():
                    self.mcp_connections[mcp_id] = MCPConnection(**mcp_data)
                
                logger.info(f"Loaded {len(self.api_keys)} API keys and {len(self.mcp_connections)} MCP connections")
            except Exception as e:
                logger.error(f"Error loading API key storage: {e}")
    
    def _save_storage(self):
        """Save API keys and connections to disk"""
        try:
            data = {
                'api_keys': {k: asdict(v) for k, v in self.api_keys.items()},
                'mcp_connections': {k: asdict(v) for k, v in self.mcp_connections.items()},
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving API key storage: {e}")
    
    def _initialize_default_keys(self):
        """Load all API keys from environment variables. NEVER hardcode keys in source."""
        # === NVIDIA NIM — single or numbered keys from .env ===
        nvidia_keys = {}
        single_nim = os.getenv("NVIDIA_NIM_API_KEY", "")
        if single_nim:
            nvidia_keys[single_nim] = {
                'model': os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct"),
                'type': 'general', 'params': {'temperature': 0.7, 'top_p': 0.95, 'max_tokens': 4096}
            }
        for i in range(1, 30):
            k = os.getenv(f"NVIDIA_NIM_API_KEY_{i}", "")
            if k and k not in nvidia_keys:
                nvidia_keys[k] = {
                    'model': os.getenv(f"NVIDIA_NIM_MODEL_{i}", "meta/llama-3.1-8b-instruct"),
                    'type': os.getenv(f"NVIDIA_NIM_TYPE_{i}", "general"),
                    'params': {'temperature': 0.7, 'top_p': 0.95, 'max_tokens': 4096}
                }

        # === All other providers from .env ===
        google_keys = {}
        if os.getenv("GEMINI_API_KEY"):
            google_keys[os.getenv("GEMINI_API_KEY")] = {
                'model': os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                'type': 'fast', 'params': {'temperature': 0.7, 'max_tokens': 8192}
            }

        deepseek_keys = {}
        if os.getenv("DEEPSEEK_API_KEY"):
            deepseek_keys[os.getenv("DEEPSEEK_API_KEY")] = {
                'model': os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                'type': 'reasoning', 'params': {'temperature': 0.7, 'max_tokens': 4096}
            }

        grok_keys = {}
        if os.getenv("GROK_API_KEY"):
            grok_keys[os.getenv("GROK_API_KEY")] = {
                'model': os.getenv("GROK_MODEL", "grok-beta"),
                'type': 'general', 'params': {'temperature': 0.7, 'max_tokens': 4096}
            }

        openai_keys = {}
        if os.getenv("OPENAI_API_KEY"):
            openai_keys[os.getenv("OPENAI_API_KEY")] = {
                'model': os.getenv("OPENAI_MODEL", "gpt-4o"),
                'type': 'general', 'params': {'temperature': 0.7, 'max_tokens': 4096}
            }

        anthropic_keys = {}
        if os.getenv("ANTHROPIC_API_KEY"):
            anthropic_keys[os.getenv("ANTHROPIC_API_KEY")] = {
                'model': os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                'type': 'reasoning', 'params': {'temperature': 0.7, 'max_tokens': 4096}
            }

        news_keys = {}
        if os.getenv("NEWS_API_KEY"):
            news_keys[os.getenv("NEWS_API_KEY")] = {'model': 'news-api', 'type': 'general', 'params': {}}

        crypto_keys = {}
        if os.getenv("COINGECKO_API_KEY"):
            crypto_keys[os.getenv("COINGECKO_API_KEY")] = {'model': 'crypto-prices', 'type': 'general', 'params': {}}

        github_keys = {}
        if os.getenv("GITHUB_API_KEY"):
            github_keys[os.getenv("GITHUB_API_KEY")] = {'model': 'github-api', 'type': 'general', 'params': {}}

        cloudinary_keys = {}
        if os.getenv("CLOUDINARY_URL"):
            cloudinary_keys[os.getenv("CLOUDINARY_URL")] = {
                'model': 'cloudinary-api', 'type': 'general',
                'params': {'cloud_name': os.getenv("CLOUDINARY_CLOUD_NAME", "")}
            }

        supabase_keys = {}
        if os.getenv("SUPABASE_KEY"):
            supabase_keys[os.getenv("SUPABASE_KEY")] = {
                'model': 'supabase-api', 'type': 'database',
                'params': {'url': os.getenv("SUPABASE_URL", "")}
            }

        pollinations_keys = {}
        if os.getenv("POLLINATIONS_API_KEY"):
            pollinations_keys[os.getenv("POLLINATIONS_API_KEY")] = {
                'model': 'pollinations-api', 'type': 'general', 'params': {}
            }

        mongodb_keys = {}
        if os.getenv("MONGODB_URI"):
            mongodb_keys["mongodb"] = {
                'model': 'mongodb-atlas', 'type': 'database',
                'params': {'connection_string': os.getenv("MONGODB_URI", "")}
            }
        
        # Add all NVIDIA keys
        for i, (api_key, config) in enumerate(nvidia_keys.items()):
            key_id = f"nvidia_nim_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="nvidia_nim",
                    api_key=api_key,
                    base_url="https://integrate.api.nvidia.com/v1",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"NVIDIA NIM - {config['model']}"
                )
        
        # Add all Google Gemini keys
        for i, (api_key, config) in enumerate(google_keys.items()):
            key_id = f"gemini_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="gemini",
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"Google Gemini - {config['model']}"
                )
        
        # Add all DeepSeek keys
        for i, (api_key, config) in enumerate(deepseek_keys.items()):
            key_id = f"deepseek_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="deepseek",
                    api_key=api_key,
                    base_url="https://api.deepseek.com/v1",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"DeepSeek - {config['model']}"
                )
        
        # Add all Grok keys
        for i, (api_key, config) in enumerate(grok_keys.items()):
            key_id = f"grok_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="grok",
                    api_key=api_key,
                    base_url="https://api.x.ai/v1",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"Grok - {config['model']}"
                )
        
        # Add all News API keys
        for i, (api_key, config) in enumerate(news_keys.items()):
            key_id = f"news_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="newsapi",
                    api_key=api_key,
                    base_url="https://newsapi.org/v2",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"NewsAPI - {config['model']}"
                )
        
        # Add all Crypto API keys
        for i, (api_key, config) in enumerate(crypto_keys.items()):
            key_id = f"crypto_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="coingecko",
                    api_key=api_key,
                    base_url="https://api.coingecko.com/api/v3",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"CoinGecko - {config['model']}"
                )
        
        # Add all GitHub API keys
        for i, (api_key, config) in enumerate(github_keys.items()):
            key_id = f"github_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="github",
                    api_key=api_key,
                    base_url="https://api.github.com",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"GitHub - {config['model']}"
                )
        
        # Add all Cloudinary API keys
        for i, (api_key, config) in enumerate(cloudinary_keys.items()):
            key_id = f"cloudinary_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="cloudinary",
                    api_key=api_key,
                    base_url="https://api.cloudinary.com/v1_1/dm2hzpe1o",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"Cloudinary - {config['model']}"
                )
        
        # Add all Supabase API keys
        for i, (api_key, config) in enumerate(supabase_keys.items()):
            key_id = f"supabase_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="supabase",
                    api_key=api_key,
                    base_url="https://mlfkbaijdqrtowqkncyj.supabase.co",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"Supabase - {config['model']}"
                )
        
        # Add all Pollinations.ai API keys
        for i, (api_key, config) in enumerate(pollinations_keys.items()):
            key_id = f"pollinations_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="pollinations",
                    api_key=api_key,
                    base_url="https://enter.pollinations.ai",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"Pollinations.ai - {config['model']}"
                )
        
        # Add all MongoDB API keys
        for i, (api_key, config) in enumerate(mongodb_keys.items()):
            key_id = f"mongodb_{i+1}"
            if key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider="mongodb",
                    api_key=api_key,
                    base_url="mongodb+srv://",
                    model=config['model'],
                    key_type=config['type'],
                    params=config.get('params', {}),
                    description=f"MongoDB - {config['model']}"
                )
        
        # Load additional keys from environment variables
        env_keys = [
            ("OPENAI_API_KEY", "openai_main", "openai", "https://api.openai.com/v1", "gpt-4", "reasoning"),
            ("ANTHROPIC_API_KEY", "anthropic_main", "anthropic", "https://api.anthropic.com/v1", "claude-3-opus", "reasoning"),
            ("GOOGLE_API_KEY", "google_main", "google", "https://generativelanguage.googleapis.com/v1", "gemini-pro", "general"),
            ("GEMINI_API_KEY", "google_gemini", "google", "https://generativelanguage.googleapis.com/v1", "gemini-pro", "general"),
        ]
        
        for env_var, key_id, provider, base_url, model, key_type in env_keys:
            key = os.getenv(env_var)
            if key and key_id not in self.api_keys:
                self.add_api_key(
                    key_id=key_id,
                    provider=provider,
                    api_key=key,
                    base_url=base_url,
                    model=model,
                    key_type=key_type,
                    description=f"Auto-loaded from {env_var}"
                )
        
        self._save_storage()
        logger.info(f"Initialized {len(self.api_keys)} API keys ({len(nvidia_keys)} NVIDIA NIM)")
    
    def add_api_key(self, key_id: str, provider: str, api_key: str, base_url: str,
                    model: str = "", key_type: str = "general", 
                    capabilities: List[str] = None, params: Dict = None,
                    description: str = "") -> APIKeyEntry:
        """Add or update an API key"""
        entry = APIKeyEntry(
            key_id=key_id,
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            key_type=key_type,
            capabilities=capabilities or [],
            params=params or {},
            description=description
        )
        self.api_keys[key_id] = entry
        self._save_storage()
        logger.info(f"Added API key: {key_id} ({provider}/{key_type})")
        return entry
    
    def add_api_key_from_chat(self, message: str) -> Dict:
        """Parse API key from natural chat message and add it
        
        Supports formats:
        - "api key nvapi-xxx for nvidia nim"
        - "connect to openai with key sk-xxx"
        - "add api: provider=openai, key=sk-xxx, base_url=..."
        - "mcp server at localhost:3000"
        """
        import re
        
        message_lower = message.lower().strip()
        result = {"success": False, "message": ""}
        
        # Detect NVIDIA NIM key
        nvidia_match = re.search(r'(nvapi-[a-zA-Z0-9_-]+)', message)
        if nvidia_match:
            api_key = nvidia_match.group(1)
            key_id = f"nvidia_nim_chat_{int(time.time())}"
            
            # Detect model from message
            model = "deepseek-ai/deepseek-v4-pro"  # default
            key_type = "reasoning"
            
            if any(kw in message_lower for kw in ['coder', 'code', 'qwen3-coder', 'devstral']):
                model = "qwen/qwen3-coder-480b-a35b-instruct"
                key_type = "coding"
            elif any(kw in message_lower for kw in ['flash', 'fast', 'quick']):
                model = "stepfun-ai/step-3.5-flash"
                key_type = "reasoning_flash"
            elif any(kw in message_lower for kw in ['tools', 'tool', 'glm-5']):
                model = "z-ai/glm-5.1"
                key_type = "reasoning_tools"
            elif any(kw in message_lower for kw in ['general', 'chat', 'instruct']):
                model = "moonshotai/kimi-k2-instruct-0905"
                key_type = "general"
            elif any(kw in message_lower for kw in ['deepseek', 'reasoning', 'think']):
                model = "deepseek-ai/deepseek-v4-pro"
                key_type = "reasoning"
            elif any(kw in message_lower for kw in ['nemotron', '120b']):
                model = "nvidia/nemotron-3-super-120b-a12b"
                key_type = "reasoning"
            
            entry = self.add_api_key(
                key_id=key_id,
                provider="nvidia_nim",
                api_key=api_key,
                base_url="https://integrate.api.nvidia.com/v1",
                model=model,
                key_type=key_type,
                description=f"Added from chat: {message[:100]}"
            )
            
            result = {
                "success": True,
                "message": f"✅ **NVIDIA NIM API Key Added!**\n\n- **Key ID:** {key_id}\n- **Model:** {model}\n- **Type:** {key_type}\n- **Base URL:** {entry.base_url}\n\nThis key is now available for all 5 founder clones.",
                "key_id": key_id,
                "provider": "nvidia_nim"
            }
            return result
        
        # Detect OpenAI key
        openai_match = re.search(r'(sk-[a-zA-Z0-9_-]+)', message)
        if openai_match:
            api_key = openai_match.group(1)
            key_id = f"openai_chat_{int(time.time())}"
            
            entry = self.add_api_key(
                key_id=key_id,
                provider="openai",
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                model="gpt-4",
                key_type="reasoning",
                description=f"Added from chat"
            )
            
            result = {
                "success": True,
                "message": f"✅ **OpenAI API Key Added!**\n\n- **Key ID:** {key_id}\n- **Model:** gpt-4\n\nThis key is now available for founder clones.",
                "key_id": key_id,
                "provider": "openai"
            }
            return result
        
        # Detect Google/Gemini key
        google_match = re.search(r'(AIza[a-zA-Z0-9_-]+)', message)
        if google_match:
            api_key = google_match.group(1)
            key_id = f"google_chat_{int(time.time())}"
            
            entry = self.add_api_key(
                key_id=key_id,
                provider="google",
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1",
                model="gemini-pro",
                key_type="general",
                description=f"Added from chat"
            )
            
            result = {
                "success": True,
                "message": f"✅ **Google Gemini API Key Added!**\n\n- **Key ID:** {key_id}\n- **Model:** gemini-pro\n\nThis key is now available for founder clones.",
                "key_id": key_id,
                "provider": "google"
            }
            return result
        
        # Detect MCP server
        if any(kw in message_lower for kw in ['mcp server', 'mcp connect', 'model context protocol']):
            url_match = re.search(r'(https?://[^\s]+)', message)
            url = url_match.group(1) if url_match else "localhost:3000"
            
            mcp_id = f"mcp_chat_{int(time.time())}"
            self.mcp_connections[mcp_id] = MCPConnection(
                id=mcp_id,
                name=f"MCP Server {mcp_id}",
                url=url,
                protocol="http",
                status="active",
                last_connected=datetime.now().isoformat()
            )
            self._save_storage()
            
            result = {
                "success": True,
                "message": f"✅ **MCP Server Connected!**\n\n- **ID:** {mcp_id}\n- **URL:** {url}\n\nMCP connection is now active.",
                "mcp_id": mcp_id
            }
            return result
        
        # Structured format: "add api: provider=xxx, key=xxx, ..."
        if 'add api' in message_lower or 'connect api' in message_lower:
            params = {}
            for pair in re.findall(r'(\w+)=([^\s,]+)', message):
                params[pair[0].lower()] = pair[1]
            
            if 'key' in params or 'api_key' in params:
                key_id = f"custom_chat_{int(time.time())}"
                entry = self.add_api_key(
                    key_id=key_id,
                    provider=params.get('provider', 'custom'),
                    api_key=params.get('key', params.get('api_key', '')),
                    base_url=params.get('base_url', params.get('url', '')),
                    model=params.get('model', ''),
                    key_type=params.get('type', 'general'),
                    description=f"Added from chat"
                )
                
                result = {
                    "success": True,
                    "message": f"✅ **Custom API Key Added!**\n\n- **Key ID:** {key_id}\n- **Provider:** {entry.provider}\n- **Model:** {entry.model or 'Not specified'}",
                    "key_id": key_id
                }
                return result
        
        result["message"] = "❌ Could not detect API key format. Try:\n- `api key nvapi-xxx for nvidia nim`\n- `connect to openai with key sk-xxx`\n- `add api: provider=openai, key=sk-xxx, base_url=...`\n- `mcp server at http://localhost:3000`"
        return result
    
    def remove_api_key(self, key_id: str) -> bool:
        """Remove an API key"""
        if key_id in self.api_keys:
            del self.api_keys[key_id]
            self._save_storage()
            return True
        return False
    
    def get_key(self, key_id: str) -> Optional[APIKeyEntry]:
        """Get a specific API key entry"""
        return self.api_keys.get(key_id)
    
    def get_keys_by_provider(self, provider: str) -> List[APIKeyEntry]:
        """Get all keys for a specific provider"""
        return [k for k in self.api_keys.values() if k.provider == provider]
    
    def get_keys_by_type(self, key_type: str) -> List[APIKeyEntry]:
        """Get all keys of a specific type"""
        return [k for k in self.api_keys.values() if k.key_type == key_type and k.status == "active"]
    
    def get_active_keys(self) -> List[APIKeyEntry]:
        """Get all active API keys"""
        return [k for k in self.api_keys.values() if k.status == "active"]
    
    def get_nvidia_keys_for_founders(self) -> Dict:
        """Get NVIDIA API keys formatted for the Optimized Founder System
        
        Returns dict of api_key -> {model, type, params} for founder assignment
        """
        nvidia_keys = {}
        for entry in self.api_keys.values():
            if entry.provider == "nvidia_nim" and entry.status == "active":
                nvidia_keys[entry.api_key] = {
                    'model': entry.model,
                    'type': entry.key_type,
                    'params': entry.params,
                    'key_id': entry.key_id
                }
        return nvidia_keys
    
    def get_best_key_for_task(self, task_type: str) -> Optional[APIKeyEntry]:
        """Get the best available API key for a given task type"""
        type_map = {
            'reasoning': ['reasoning', 'reasoning_tools', 'general'],
            'coding': ['coding', 'reasoning', 'general'],
            'general': ['general', 'reasoning_flash', 'reasoning'],
            'fast': ['reasoning_flash', 'general', 'reasoning'],
            'tools': ['reasoning_tools', 'reasoning', 'general'],
        }
        
        preferred_types = type_map.get(task_type, ['general', 'reasoning'])
        
        for pref_type in preferred_types:
            keys = self.get_keys_by_type(pref_type)
            if keys:
                # Return least recently used key
                keys.sort(key=lambda k: k.last_used or "")
                return keys[0]
        
        # Fallback to any active key
        active = self.get_active_keys()
        if active:
            return active[0]
        
        return None
    
    def mark_key_used(self, key_id: str):
        """Mark a key as used"""
        if key_id in self.api_keys:
            self.api_keys[key_id].usage_count += 1
            self.api_keys[key_id].last_used = datetime.now().isoformat()
            self._save_storage()
    
    def mark_key_rate_limited(self, key_id: str, reset_time: float = None):
        """Mark a key as rate limited"""
        if key_id in self.api_keys:
            self.api_keys[key_id].status = "rate_limited"
            self.api_keys[key_id].rate_limit_reset = reset_time or (time.time() + 60)
            self._save_storage()
    
    def check_key_health(self, key_id: str) -> Dict:
        """Check health of an API key"""
        entry = self.api_keys.get(key_id)
        if not entry:
            return {"status": "not_found"}
        
        # Check if rate limit has expired
        if entry.status == "rate_limited" and entry.rate_limit_reset:
            if time.time() > entry.rate_limit_reset:
                entry.status = "active"
                entry.rate_limit_reset = None
                self._save_storage()
        
        return {
            "status": entry.status,
            "provider": entry.provider,
            "model": entry.model,
            "usage_count": entry.usage_count,
            "last_used": entry.last_used,
            "last_error": entry.last_error
        }
    
    def health_check_all(self) -> Dict:
        """Check health of all API keys"""
        results = {}
        for key_id, entry in self.api_keys.items():
            results[key_id] = self.check_key_health(key_id)
        return results
    
    def get_status_summary(self) -> Dict:
        """Get overall status summary"""
        active = sum(1 for k in self.api_keys.values() if k.status == "active")
        rate_limited = sum(1 for k in self.api_keys.values() if k.status == "rate_limited")
        error = sum(1 for k in self.api_keys.values() if k.status == "error")
        
        providers = {}
        for entry in self.api_keys.values():
            providers[entry.provider] = providers.get(entry.provider, 0) + 1
        
        return {
            "total_keys": len(self.api_keys),
            "active_keys": active,
            "rate_limited_keys": rate_limited,
            "error_keys": error,
            "mcp_connections": len(self.mcp_connections),
            "providers": providers,
            "nvidia_keys_for_founders": len(self.get_nvidia_keys_for_founders())
        }
    
    def get_status_text(self) -> str:
        """Get human-readable status for chat display"""
        summary = self.get_status_summary()
        
        lines = [
            f"**🔑 ASIMNEXUS API Key Manager Status**\n",
            f"- **Total Keys:** {summary['total_keys']}",
            f"- **Active:** {summary['active_keys']} 🟢",
            f"- **Rate Limited:** {summary['rate_limited_keys']} 🟡",
            f"- **Error:** {summary['error_keys']} 🔴",
            f"- **MCP Connections:** {summary['mcp_connections']}",
            f"- **NVIDIA Keys for Founders:** {summary['nvidia_keys_for_founders']}",
            f"\n**Providers:**"
        ]
        
        for provider, count in summary['providers'].items():
            lines.append(f"- {provider}: {count} key(s)")
        
        # Show NVIDIA keys detail
        nvidia_keys = self.get_nvidia_keys_for_founders()
        if nvidia_keys:
            lines.append(f"\n**NVIDIA NIM Models Available:**")
            for api_key, config in nvidia_keys.items():
                lines.append(f"- {config['model']} ({config['type']})")
        
        return "\n".join(lines)


# === Singleton Instance ===
_instance = None

def get_unified_api_key_manager() -> UnifiedAPIKeyManager:
    """Get or create the singleton UnifiedAPIKeyManager instance"""
    global _instance
    if _instance is None:
        _instance = UnifiedAPIKeyManager()
    return _instance
