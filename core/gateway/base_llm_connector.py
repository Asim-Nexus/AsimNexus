
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Base LLM Connector
============================
Common patterns for all LLM connectors

Provides:
- Standard initialization
- Common completion methods
- Streaming support
- Error handling
- Rate limiting
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

class ModelProvider(Enum):
    """Model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GEMMA = "gemma"
    XAI = "xai"

@dataclass
class CompletionRequest:
    """Standard completion request"""
    messages: List[Dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False

@dataclass
class CompletionResponse:
    """Standard completion response"""
    content: str
    model: str
    finish_reason: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float

@dataclass
class ModelInfo:
    """Model information"""
    model_id: str
    provider: ModelProvider
    context_window: int
    max_output: int
    cost_per_1k_input: float
    cost_per_1k_output: float

class BaseLLMConnector(ABC):
    """
    Base class for all LLM connectors
    
    Provides common functionality:
    - Initialization pattern
    - Completion methods
    - Streaming support
    - Error handling
    - Cost tracking
    """
    
    def __init__(self, provider: ModelProvider, api_key: str = None):
        self.provider = provider
        self.api_key = api_key
        self.logger = logging.getLogger(f"ASIM_Connector_{provider.value}")
        
        # Statistics
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        
        # Rate limiting
        self.requests_per_minute = 60
        self.request_timestamps: List[datetime] = []
        
        # Available models
        self.models: Dict[str, ModelInfo] = {}
        
    @abstractmethod
    async def initialize(self):
        """Initialize the connector - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate completion - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def complete_stream(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """Generate streaming completion - must be implemented by subclasses"""
        pass
    
    async def _check_rate_limit(self):
        """Check if rate limit is respected"""
        now = datetime.now()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).total_seconds() < 60
        ]
        
        if len(self.request_timestamps) >= self.requests_per_minute:
            # Rate limit reached, wait
            sleep_time = 60 - (now - self.request_timestamps[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Get model information"""
        return self.models.get(model)
    
    def list_models(self) -> List[str]:
        """List available models"""
        return list(self.models.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connector statistics"""
        return {
            "provider": self.provider.value,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": f"${self.total_cost:.4f}",
            "available_models": len(self.models)
        }
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for completion"""
        model_info = self.models.get(model)
        if not model_info:
            return 0.0
        
        input_cost = (prompt_tokens / 1000) * model_info.cost_per_1k_input
        output_cost = (completion_tokens / 1000) * model_info.cost_per_1k_output
        return input_cost + output_cost
    
    def set_rate_limit(self, requests_per_minute: int):
        """Set rate limit"""
        self.requests_per_minute = requests_per_minute
        self.logger.info(f"Rate limit set to {requests_per_minute} requests/minute")
