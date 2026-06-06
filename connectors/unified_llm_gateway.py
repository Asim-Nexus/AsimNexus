
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified LLM Gateway
============================
Smart, unified connector for all LLM providers
Consolidates OpenAI, Anthropic, Gemini, Grok, Gemma4 into one efficient system
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

# Import Standard API Schema
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from core.api_schema import StandardResponse, StandardMetadata, schema_validator
    API_SCHEMA_AVAILABLE = True
except ImportError:
    API_SCHEMA_AVAILABLE = False
    logging.warning("API Schema not available, using fallback")

# Import base connector for compatibility
try:
    from connectors.base_llm_connector import BaseLLMConnector, ModelProvider, CompletionRequest, CompletionResponse, ModelInfo
    BASE_CONNECTOR_AVAILABLE = True
except ImportError:
    BASE_CONNECTOR_AVAILABLE = False
    logging.warning("Base connector not available, using standalone implementation")


class LLMProvider(Enum):
    """All supported LLM providers — Local-first, with NVIDIA NIM support"""
    LOCAL = "local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GEMMA = "gemma"
    XAI_GROK = "xai_grok"
    DEEPSEEK = "deepseek"
    NVIDIA_NIM = "nvidia_nim"


@dataclass
class ProviderConfig:
    """Configuration for a specific provider"""
    provider: LLMProvider
    api_key: str
    base_url: str
    default_model: str
    max_tokens: int
    temperature: float
    enabled: bool
    # Support multiple API keys for load balancing
    api_keys: List[str] = None
    current_key_index: int = 0
    
    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = [self.api_key] if self.api_key else []


@dataclass
class UnifiedCompletionRequest:
    """Unified completion request for all providers"""
    messages: List[Dict[str, str]]
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False


@dataclass
class UnifiedCompletionResponse:
    """Unified completion response from any provider"""
    content: str
    provider: LLMProvider
    model: str
    finish_reason: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: float


class UnifiedLLMGateway:
    """
    Unified LLM Gateway - Smart connector for all providers
    
    Features:
    - Automatic provider selection based on request type
    - Load balancing across providers
    - Failover support
    - Cost optimization
    - Unified API for all providers
    - Streaming support
    - Rate limiting per provider
    - Smart caching
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_UnifiedLLM")
        self.providers: Dict[LLMProvider, ProviderConfig] = {}
        self.sessions: Dict[LLMProvider, aiohttp.ClientSession] = {}
        
        # Statistics
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.provider_stats: Dict[LLMProvider, Dict] = {}
        
        # Model registry
        self.model_registry: Dict[str, Dict] = self._initialize_model_registry()
        
        # NVIDIA NIM models list
        self.nvidia_models: List[tuple] = []
        
        # Rate limiting
        self.rate_limits: Dict[LLMProvider, List[datetime]] = {}
        
        # Smart routing
        self.provider_preferences: Dict[str, LLMProvider] = {
            "code": LLMProvider.ANTHROPIC,
            "reasoning": LLMProvider.NVIDIA_NIM,
            "chat": LLMProvider.NVIDIA_NIM,
            "fast": LLMProvider.GEMINI,
            "local": LLMProvider.LOCAL,
            "complex": LLMProvider.NVIDIA_NIM,
            "vision": LLMProvider.NVIDIA_NIM
        }
        
        # Load configurations
        self._load_configurations()
        
        self.logger.info("Unified LLM Gateway initialized")
    
    def _initialize_model_registry(self) -> Dict[str, Dict]:
        """Initialize model registry with all available models"""
        return {
            # OpenAI Models
            "gpt-4-turbo-preview": {
                "provider": LLMProvider.OPENAI,
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03,
                "best_for": ["complex", "reasoning"]
            },
            "gpt-4": {
                "provider": LLMProvider.OPENAI,
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06,
                "best_for": ["complex", "reasoning"]
            },
            "gpt-3.5-turbo": {
                "provider": LLMProvider.OPENAI,
                "context_window": 16385,
                "max_output": 4096,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015,
                "best_for": ["chat", "fast"]
            },
            
            # Anthropic Models
            "claude-3-sonnet-20240229": {
                "provider": LLMProvider.ANTHROPIC,
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015,
                "best_for": ["code", "reasoning", "analysis"]
            },
            "claude-3-opus-20240229": {
                "provider": LLMProvider.ANTHROPIC,
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075,
                "best_for": ["complex", "reasoning", "analysis"]
            },
            
            # Gemini Models
            "gemini-3-flash-preview": {
                "provider": LLMProvider.GEMINI,
                "context_window": 1000000,
                "max_output": 8192,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "best_for": ["chat", "fast", "multimodal", "reasoning"]
            },
            "gemini-pro": {
                "provider": LLMProvider.GEMINI,
                "context_window": 91728,
                "max_output": 8192,
                "cost_per_1k_input": 0.00025,
                "cost_per_1k_output": 0.0005,
                "best_for": ["chat", "multimodal"]
            },
            
            # Gemma Models
            "gemma-7b": {
                "provider": LLMProvider.GEMMA,
                "context_window": 8192,
                "max_output": 2048,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "best_for": ["local", "fast"]
            },
            
            # Grok Models
            "grok-beta": {
                "provider": LLMProvider.XAI_GROK,
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.002,
                "cost_per_1k_output": 0.006,
                "best_for": ["chat", "realtime"]
            },
            
            # DeepSeek Models
            "deepseek-chat": {
                "provider": LLMProvider.DEEPSEEK,
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.001,
                "cost_per_1k_output": 0.002,
                "best_for": ["chat", "reasoning", "coding"]
            },
            "deepseek-coder": {
                "provider": LLMProvider.DEEPSEEK,
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.001,
                "cost_per_1k_output": 0.002,
                "best_for": ["coding", "programming"]
            }
        }
    
    def _load_configurations(self):
        """Load provider configurations from environment and config files"""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.providers[LLMProvider.OPENAI] = ProviderConfig(
                provider=LLMProvider.OPENAI,
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                default_model="gpt-4-turbo-preview",
                max_tokens=4096,
                temperature=0.7,
                enabled=True
            )
            self.provider_stats[LLMProvider.OPENAI] = {"requests": 0, "tokens": 0, "cost": 0.0}
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers[LLMProvider.ANTHROPIC] = ProviderConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key=anthropic_key,
                base_url="https://api.anthropic.com/v1",
                default_model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7,
                enabled=True
            )
            self.provider_stats[LLMProvider.ANTHROPIC] = {"requests": 0, "tokens": 0, "cost": 0.0}
        
        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.providers[LLMProvider.GEMINI] = ProviderConfig(
                provider=LLMProvider.GEMINI,
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta",
                default_model="gemini-3-flash-preview",
                max_tokens=8192,
                temperature=0.7,
                enabled=True
            )
            self.provider_stats[LLMProvider.GEMINI] = {"requests": 0, "tokens": 0, "cost": 0.0}
        
        # Grok
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            self.providers[LLMProvider.XAI_GROK] = ProviderConfig(
                provider=LLMProvider.XAI_GROK,
                api_key=grok_key,
                base_url="https://api.x.ai/v1",
                default_model="grok-beta",
                max_tokens=4096,
                temperature=0.7,
                enabled=True
            )
            self.provider_stats[LLMProvider.XAI_GROK] = {"requests": 0, "tokens": 0, "cost": 0.0}
        
        # DeepSeek
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            self.providers[LLMProvider.DEEPSEEK] = ProviderConfig(
                provider=LLMProvider.DEEPSEEK,
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1",
                default_model="deepseek-chat",
                max_tokens=4096,
                temperature=0.7,
                enabled=True
            )
            self.provider_stats[LLMProvider.DEEPSEEK] = {"requests": 0, "tokens": 0, "cost": 0.0}
        
        # NVIDIA NIM - Load all keys from api_keys.json
        try:
            from pathlib import Path
            api_keys_file = Path(__file__).parent.parent / "data" / "api_keys.json"
            if api_keys_file.exists():
                with open(api_keys_file, 'r') as f:
                    api_config = json.load(f)
                
                # Load all active NVIDIA NIM keys
                nvidia_keys = [k for k in api_config.get('api_keys', {}).values() 
                              if k.get('provider') == 'nvidia_nim' and k.get('status') == 'active']
                
                if nvidia_keys:
                    # Extract all API keys and models
                    api_keys_list = [k['api_key'] for k in nvidia_keys]
                    models_list = [(k['key_id'], k['model'], k.get('key_type', 'general')) for k in nvidia_keys]
                    
                    # Use first key as default
                    first_key = nvidia_keys[0]
                    nvidia_url = first_key['base_url']
                    default_model = first_key['model']
                    
                    self.providers[LLMProvider.NVIDIA_NIM] = ProviderConfig(
                        provider=LLMProvider.NVIDIA_NIM,
                        api_key=first_key['api_key'],
                        base_url=nvidia_url,
                        default_model=default_model,
                        max_tokens=16384,
                        temperature=1.0,
                        enabled=True,
                        api_keys=api_keys_list
                    )
                    self.provider_stats[LLMProvider.NVIDIA_NIM] = {"requests": 0, "tokens": 0, "cost": 0.0}
                    
                    # Store model configurations for routing
                    self.nvidia_models = models_list
                    self.logger.info(f"✅ Loaded {len(nvidia_keys)} NVIDIA NIM API keys with {len(models_list)} models")
                
                # Load DeepSeek keys
                deepseek_keys = [k for k in api_config.get('api_keys', {}).values() 
                                if k.get('provider') == 'deepseek' and k.get('status') == 'active']
                
                if deepseek_keys and LLMProvider.DEEPSEEK not in self.providers:
                    first_key = deepseek_keys[0]
                    api_keys_list = [k['api_key'] for k in deepseek_keys]
                    
                    self.providers[LLMProvider.DEEPSEEK] = ProviderConfig(
                        provider=LLMProvider.DEEPSEEK,
                        api_key=first_key['api_key'],
                        base_url=first_key['base_url'],
                        default_model=first_key['model'],
                        max_tokens=4096,
                        temperature=0.7,
                        enabled=True,
                        api_keys=api_keys_list
                    )
                    self.provider_stats[LLMProvider.DEEPSEEK] = {"requests": 0, "tokens": 0, "cost": 0.0}
                    self.logger.info(f"✅ Loaded {len(deepseek_keys)} DeepSeek API keys")
                
                # Load Grok keys
                grok_keys = [k for k in api_config.get('api_keys', {}).values() 
                           if k.get('provider') == 'grok' and k.get('status') == 'active']
                
                if grok_keys and LLMProvider.XAI_GROK not in self.providers:
                    first_key = grok_keys[0]
                    api_keys_list = [k['api_key'] for k in grok_keys]
                    
                    self.providers[LLMProvider.XAI_GROK] = ProviderConfig(
                        provider=LLMProvider.XAI_GROK,
                        api_key=first_key['api_key'],
                        base_url=first_key['base_url'],
                        default_model=first_key['model'],
                        max_tokens=4096,
                        temperature=0.7,
                        enabled=True,
                        api_keys=api_keys_list
                    )
                    self.provider_stats[LLMProvider.XAI_GROK] = {"requests": 0, "tokens": 0, "cost": 0.0}
                    self.logger.info(f"✅ Loaded {len(grok_keys)} Grok API keys")
                
                # Load Gemini keys
                gemini_keys = [k for k in api_config.get('api_keys', {}).values() 
                              if k.get('provider') == 'gemini' and k.get('status') == 'active']
                
                if gemini_keys and LLMProvider.GEMINI not in self.providers:
                    first_key = gemini_keys[0]
                    api_keys_list = [k['api_key'] for k in gemini_keys]
                    
                    self.providers[LLMProvider.GEMINI] = ProviderConfig(
                        provider=LLMProvider.GEMINI,
                        api_key=first_key['api_key'],
                        base_url=first_key['base_url'],
                        default_model=first_key['model'],
                        max_tokens=8192,
                        temperature=0.7,
                        enabled=True,
                        api_keys=api_keys_list
                    )
                    self.provider_stats[LLMProvider.GEMINI] = {"requests": 0, "tokens": 0, "cost": 0.0}
                    self.logger.info(f"✅ Loaded {len(gemini_keys)} Gemini API keys")
            else:
                # Fallback to environment variable
                nvidia_key = os.getenv("NVIDIA_API_KEY")
                nvidia_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
                if nvidia_key:
                    self.providers[LLMProvider.NVIDIA_NIM] = ProviderConfig(
                        provider=LLMProvider.NVIDIA_NIM,
                        api_key=nvidia_key,
                        base_url=nvidia_url,
                        default_model="nvidia/nemotron-3-super-120b-a12b",
                        max_tokens=16384,
                        temperature=1.0,
                        enabled=True
                    )
                    self.provider_stats[LLMProvider.NVIDIA_NIM] = {"requests": 0, "tokens": 0, "cost": 0.0}
                    self.nvidia_models = []
        except Exception as e:
            self.logger.warning(f"Failed to load NVIDIA NIM keys from config: {e}")
            # Fallback to environment variable
            nvidia_key = os.getenv("NVIDIA_API_KEY")
            nvidia_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            if nvidia_key:
                self.providers[LLMProvider.NVIDIA_NIM] = ProviderConfig(
                    provider=LLMProvider.NVIDIA_NIM,
                    api_key=nvidia_key,
                    base_url=nvidia_url,
                    default_model="nvidia/nemotron-3-super-120b-a12b",
                    max_tokens=16384,
                    temperature=1.0,
                    enabled=True
                )
                self.provider_stats[LLMProvider.NVIDIA_NIM] = {"requests": 0, "tokens": 0, "cost": 0.0}
                self.nvidia_models = []
        
        # Local (ASIMNEXUS LLM Engine)
        local_url = os.getenv("LLM_ENGINE_URL", "http://localhost:8000")
        self.providers[LLMProvider.LOCAL] = ProviderConfig(
            provider=LLMProvider.LOCAL,
            api_key="",
            base_url=local_url,
            default_model="gemma-2-2b-it",
            max_tokens=512,
            temperature=0.7,
            enabled=True
        )
        self.provider_stats[LLMProvider.LOCAL] = {"requests": 0, "tokens": 0, "cost": 0.0}
        
        self.logger.info(f"Loaded {len(self.providers)} provider configurations")
    
    async def initialize(self):
        """Initialize all provider sessions"""
        for provider, config in self.providers.items():
            if not config.enabled:
                continue
            
            try:
                if provider == LLMProvider.OPENAI:
                    self.sessions[provider] = aiohttp.ClientSession(
                        headers={"Authorization": f"Bearer {config.api_key}"}
                    )
                elif provider == LLMProvider.ANTHROPIC:
                    self.sessions[provider] = aiohttp.ClientSession(
                        headers={
                            "x-api-key": config.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        }
                    )
                elif provider == LLMProvider.GEMINI:
                    self.sessions[provider] = aiohttp.ClientSession()
                elif provider == LLMProvider.XAI_GROK:
                    self.sessions[provider] = aiohttp.ClientSession(
                        headers={"Authorization": f"Bearer {config.api_key}"}
                    )
                elif provider == LLMProvider.NVIDIA_NIM:
                    self.sessions[provider] = aiohttp.ClientSession(
                        headers={"Authorization": f"Bearer {config.api_key}"}
                    )
                elif provider == LLMProvider.LOCAL:
                    self.sessions[provider] = aiohttp.ClientSession()
                
                self.logger.info(f"{provider.value} session initialized")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider.value}: {e}")
    
    async def _initialize_single_provider(self, provider: LLMProvider):
        """Initialize a single provider on-demand"""
        config = self.providers.get(provider)
        if not config or not config.enabled:
            raise ValueError(f"Provider {provider.value} not available or not enabled")
        
        if provider == LLMProvider.LOCAL:
            self.sessions[provider] = aiohttp.ClientSession()
        elif provider == LLMProvider.OPENAI:
            self.sessions[provider] = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {config.api_key}"}
            )
        elif provider == LLMProvider.ANTHROPIC:
            self.sessions[provider] = aiohttp.ClientSession(
                headers={
                    "x-api-key": config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
            )
        elif provider == LLMProvider.GEMINI:
            self.sessions[provider] = aiohttp.ClientSession()
        elif provider == LLMProvider.XAI_GROK:
            self.sessions[provider] = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {config.api_key}"}
            )
        elif provider == LLMProvider.NVIDIA_NIM:
            self.sessions[provider] = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {config.api_key}"}
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.logger.info(f"On-demand initialized {provider.value}")
    
    def _select_provider(self, request_type: str = "chat") -> LLMProvider:
        """Smart provider selection based on request type"""
        # Check preference
        preferred = self.provider_preferences.get(request_type)
        if preferred and preferred in self.providers and self.providers[preferred].enabled:
            return preferred
        
        # Fallback to available providers
        for provider in [LLMProvider.LOCAL, LLMProvider.GEMINI, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            if provider in self.providers and self.providers[provider].enabled:
                return provider
        
        return LLMProvider.OPENAI  # Default fallback
    
    def _select_nvidia_model(self, request_type: str = "chat") -> tuple:
        """Select best NVIDIA NIM model based on request type"""
        if not self.nvidia_models:
            return None, None, None
        
        # Map request types to key types
        type_mapping = {
            "code": "coding",
            "reasoning": "reasoning",
            "chat": "general",
            "fast": "reasoning_flash",
            "complex": "reasoning",
            "vision": "reasoning",
            "tools": "reasoning_tools"
        }
        
        target_type = type_mapping.get(request_type, "general")
        
        # Find models matching the target type
        matching_models = [m for m in self.nvidia_models if m[2] == target_type]
        
        if matching_models:
            # Return first matching model
            return matching_models[0]
        
        # Fallback to reasoning models
        reasoning_models = [m for m in self.nvidia_models if m[2] == "reasoning"]
        if reasoning_models:
            return reasoning_models[0]
        
        # Fallback to first available model
        return self.nvidia_models[0]
    
    def _detect_request_type(self, messages: List[Dict[str, str]]) -> str:
        """Detect request type from message content"""
        if not messages:
            return "chat"
        
        # Get last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break
        
        # Keywords for different request types
        type_keywords = {
            "code": ["code", "function", "class", "algorithm", "programming", "debug", "fix", "implement"],
            "reasoning": ["think", "reason", "analyze", "explain", "why", "how", "logic", "solve"],
            "fast": ["quick", "fast", "short", "brief", "simple"],
            "complex": ["complex", "detailed", "comprehensive", "thorough", "in-depth"],
            "tools": ["tool", "function", "api", "call", "execute"]
        }
        
        # Check for matching keywords
        for req_type, keywords in type_keywords.items():
            if any(keyword in user_message for keyword in keywords):
                return req_type
        
        return "chat"
    
    async def _check_rate_limit(self, provider: LLMProvider):
        """Check and enforce rate limiting"""
        if provider not in self.rate_limits:
            self.rate_limits[provider] = []
        
        now = datetime.now()
        # Remove timestamps older than 1 minute
        self.rate_limits[provider] = [
            ts for ts in self.rate_limits[provider]
            if (now - ts).total_seconds() < 60
        ]
        
        if len(self.rate_limits[provider]) >= 60:  # 60 requests per minute
            sleep_time = 60 - (now - self.rate_limits[provider][0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.rate_limits[provider].append(now)
    
    async def complete(self, request: UnifiedCompletionRequest) -> UnifiedCompletionResponse:
        """Generate completion using unified gateway"""
        start_time = time.time()
        
        # Detect request type from message content
        request_type = self._detect_request_type(request.messages)
        
        # Smart provider selection if not specified
        if not request.provider or request.provider not in self.providers:
            request.provider = self._select_provider(request_type)
        
        provider = request.provider
        config = self.providers[provider]
        
        # For NVIDIA NIM, select appropriate model
        if provider == LLMProvider.NVIDIA_NIM and self.nvidia_models:
            key_id, model_name, _ = self._select_nvidia_model(request_type)
            if model_name and not request.model:
                request.model = model_name
                self.logger.info(f"Selected NVIDIA NIM model: {model_name} (key_id: {key_id})")
        
        if not config.enabled:
            # Try fallback
            fallback = self._select_provider(request_type)
            if fallback != provider:
                request.provider = fallback
                provider = fallback
                config = self.providers[provider]
            else:
                raise ValueError(f"No enabled providers available")
        
        await self._check_rate_limit(provider)
        
        # Get session
        session = self.sessions.get(provider)
        if not session:
            # Try to initialize the provider on-demand
            self.logger.warning(f"Provider {provider.value} session not found, attempting on-demand initialization")
            try:
                await self._initialize_single_provider(provider)
                session = self.sessions.get(provider)
                if not session:
                    raise ValueError(f"Provider {provider.value} not initialized")
            except Exception as e:
                raise ValueError(f"Provider {provider.value} not initialized: {e}")
        
        # Route to specific provider implementation
        if provider == LLMProvider.OPENAI:
            response = await self._complete_openai(session, request, config)
        elif provider == LLMProvider.ANTHROPIC:
            response = await self._complete_anthropic(session, request, config)
        elif provider == LLMProvider.GEMINI:
            response = await self._complete_gemini(session, request, config)
        elif provider == LLMProvider.XAI_GROK:
            response = await self._complete_grok(session, request, config)
        elif provider == LLMProvider.DEEPSEEK:
            response = await self._complete_deepseek(session, request, config)
        elif provider == LLMProvider.NVIDIA_NIM:
            response = await self._complete_nvidia_nim(session, request, config)
        elif provider == LLMProvider.LOCAL:
            response = await self._complete_local(session, request, config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Update statistics
        latency_ms = int((time.time() - start_time) * 1000)
        response.latency_ms = latency_ms
        
        self.total_requests += 1
        self.total_tokens += response.tokens_used
        self.total_cost += response.cost
        
        self.provider_stats[provider]["requests"] += 1
        self.provider_stats[provider]["tokens"] += response.tokens_used
        self.provider_stats[provider]["cost"] += response.cost
        
        return response
    
    async def _complete_openai(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using OpenAI"""
        model = request.model or config.default_model
        
        data = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False
        }
        
        async with session.post(
            f"{config.base_url}/chat/completions",
            json=data
        ) as response:
            result = await response.json()
            
            choice = result["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice["finish_reason"]
            
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            model_info = self.model_registry.get(model, {})
            cost = self._calculate_cost(model_info, prompt_tokens, completion_tokens)
            
            return UnifiedCompletionResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=model,
                finish_reason=finish_reason,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=0
            )
    
    async def _complete_anthropic(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using Anthropic"""
        model = request.model or config.default_model
        
        # Convert messages to Claude format
        claude_messages = []
        system_message = None
        
        for msg in request.messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": claude_messages
        }
        
        if system_message:
            payload["system"] = system_message
        
        async with session.post(
            f"{config.base_url}/messages",
            json=payload
        ) as response:
            result = await response.json()
            
            content = result["content"][0]["text"]
            finish_reason = result.get("stop_reason", "end_turn")
            
            usage = result.get("usage", {})
            prompt_tokens = usage.get("input_tokens", 0)
            completion_tokens = usage.get("output_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens
            
            model_info = self.model_registry.get(model, {})
            cost = self._calculate_cost(model_info, prompt_tokens, completion_tokens)
            
            return UnifiedCompletionResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=model,
                finish_reason=finish_reason,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=0
            )
    
    async def _complete_gemini(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using Gemini"""
        model = request.model or config.default_model
        
        # Convert messages to Gemini format
        contents = []
        for msg in request.messages:
            contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "topP": request.top_p
            }
        }
        
        async with session.post(
            f"{config.base_url}/models/{model}:generateContent?key={config.api_key}",
            json=payload
        ) as response:
            result = await response.json()
            
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            finish_reason = "stop"
            
            # Estimate tokens (Gemini doesn't always return exact counts)
            prompt_tokens = len(str(request.messages)) // 4
            completion_tokens = len(content) // 4
            total_tokens = prompt_tokens + completion_tokens
            
            model_info = self.model_registry.get(model, {})
            cost = self._calculate_cost(model_info, prompt_tokens, completion_tokens)
            
            return UnifiedCompletionResponse(
                content=content,
                provider=LLMProvider.GEMINI,
                model=model,
                finish_reason=finish_reason,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=0
            )
    
    async def _complete_grok(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using Grok (similar to OpenAI)"""
        # Grok API is similar to OpenAI
        return await self._complete_openai(session, request, config)
    
    async def _complete_nvidia_nim(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using NVIDIA NIM (OpenAI-compatible)"""
        model = request.model or config.default_model
        
        data = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": False
        }
        
        async with session.post(
            f"{config.base_url}/chat/completions",
            json=data,
            headers={"Authorization": f"Bearer {config.api_key}"}
        ) as response:
            result = await response.json()
            
            choice = result["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "stop")
            
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # NVIDIA NIM cost calculation (simplified)
            cost = 0.0  # NVIDIA NIM pricing varies by model
            
            return UnifiedCompletionResponse(
                content=content,
                provider=LLMProvider.NVIDIA_NIM,
                model=model,
                finish_reason=finish_reason,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=0
            )
    
    async def _complete_deepseek(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using DeepSeek (OpenAI-compatible)"""
        model = request.model or config.default_model
        
        data = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": False
        }
        
        async with session.post(
            f"{config.base_url}/chat/completions",
            json=data,
            headers={"Authorization": f"Bearer {config.api_key}"}
        ) as response:
            result = await response.json()
            
            choice = result["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "stop")
            
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            model_info = self.model_registry.get(model, {})
            cost = self._calculate_cost(model_info, prompt_tokens, completion_tokens)
            
            return UnifiedCompletionResponse(
                content=content,
                provider=LLMProvider.DEEPSEEK,
                model=model,
                finish_reason=finish_reason,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=0
            )
    
    async def _complete_local(
        self,
        session: aiohttp.ClientSession,
        request: UnifiedCompletionRequest,
        config: ProviderConfig
    ) -> UnifiedCompletionResponse:
        """Complete using ASIMNEXUS LLM Engine"""
        model = request.model or config.default_model
        
        # Convert messages to prompt for local LLM
        prompt = ""
        if request.messages:
            for msg in request.messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    prompt += f"System: {content}\n"
                elif role == "user":
                    prompt += f"User: {content}\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n"
        prompt += "Assistant: "
        
        data = {
            "prompt": prompt.strip(),
            "model_id": model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        async with session.post(
            f"{config.base_url}/api/local-llm/generate",
            json=data
        ) as response:
            result = await response.json()
            
            content = result.get("text", "")
            finish_reason = "stop"
            
            # Estimate tokens (local LLM doesn't always return exact counts)
            prompt_tokens = len(str(request.messages)) // 4
            completion_tokens = len(content) // 4
            total_tokens = prompt_tokens + completion_tokens
            
            return UnifiedCompletionResponse(
                content=content,
                provider=LLMProvider.LOCAL,
                model=model,
                finish_reason=finish_reason,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=0.0,  # Local is free
                latency_ms=0
            )
    
    def _calculate_cost(self, model_info: Dict, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for completion"""
        if not model_info:
            return 0.0
        
        input_cost = (prompt_tokens / 1000) * model_info.get("cost_per_1k_input", 0)
        output_cost = (completion_tokens / 1000) * model_info.get("cost_per_1k_output", 0)
        return input_cost + output_cost
    
    async def complete_stream(self, request: UnifiedCompletionRequest) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        # For now, return non-streaming (streaming implementation would be similar)
        response = await self.complete(request)
        yield response.content
    
    def get_available_models(self) -> List[str]:
        """Get all available models"""
        return list(self.model_registry.keys())
    
    def get_models_by_provider(self, provider: LLMProvider) -> List[str]:
        """Get models for specific provider"""
        return [
            model for model, info in self.model_registry.items()
            if info.get("provider") == provider
        ]
    
    def get_statistics(self) -> Dict:
        """Get gateway statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": f"${self.total_cost:.4f}",
            "enabled_providers": len([p for p in self.providers.values() if p.enabled]),
            "provider_stats": {
                p.value: stats for p, stats in self.provider_stats.items()
            }
        }
    
    async def close(self):
        """Close all sessions"""
        for session in self.sessions.values():
            await session.close()
        self.logger.info("All provider sessions closed")


# Global unified gateway instance
unified_llm_gateway = UnifiedLLMGateway()
