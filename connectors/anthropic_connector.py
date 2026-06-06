
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Anthropic Connector
==============================
Connector for Anthropic Claude API
Provides integration with Anthropic's language models
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("AnthropicConnector")

# Try to import anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic not installed. Install with: pip install anthropic")


class ModelType(Enum):
    """Anthropic model types"""
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_2 = "claude-2.1"
    CLAUDE_INSTANT = "claude-instant-1.2"


@dataclass
class Message:
    """A message for the API"""
    role: str
    content: str


class AnthropicConnector:
    """
    Anthropic Claude Connector
    
    Provides:
    - Text generation
    - Chat completion
    - Streaming responses
    - Model management
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("AnthropicConnector")
        self.api_key = api_key
        self.client = None
        self.default_model = ModelType.CLAUDE_3_SONNET
        
        if ANTHROPIC_AVAILABLE and api_key:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
                self.logger.info("Anthropic client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return ANTHROPIC_AVAILABLE and self.client is not None
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[ModelType] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using Claude
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.is_available():
            self.logger.warning("Anthropic connector not available")
            return None
        
        model = model or self.default_model
        
        try:
            message = self.client.messages.create(
                model=model.value,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[ModelType] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Chat completion using Claude
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        if not self.is_available():
            self.logger.warning("Anthropic connector not available")
            return None
        
        model = model or self.default_model
        
        try:
            message = self.client.messages.create(
                model=model.value,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            
            return message.content[0].text
            
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            return None
    
    async def stream_text(
        self,
        prompt: str,
        model: Optional[ModelType] = None,
        max_tokens: int = 1024
    ):
        """
        Stream text generation using Claude
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks
        """
        if not self.is_available():
            self.logger.warning("Anthropic connector not available")
            return
        
        model = model or self.default_model
        
        try:
            with self.client.messages.stream(
                model=model.value,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            self.logger.error(f"Stream generation failed: {e}")
    
    def get_model_info(self, model: ModelType) -> Dict:
        """Get information about a model"""
        model_info = {
            ModelType.CLAUDE_3_OPUS: {
                "name": "Claude 3 Opus",
                "context": 200000,
                "description": "Most capable model for complex tasks"
            },
            ModelType.CLAUDE_3_SONNET: {
                "name": "Claude 3 Sonnet",
                "context": 200000,
                "description": "Balanced model for most use cases"
            },
            ModelType.CLAUDE_3_HAIKU: {
                "name": "Claude 3 Haiku",
                "context": 200000,
                "description": "Fast and lightweight model"
            },
            ModelType.CLAUDE_2: {
                "name": "Claude 2.1",
                "context": 100000,
                "description": "Previous generation model"
            },
            ModelType.CLAUDE_INSTANT: {
                "name": "Claude Instant",
                "context": 100000,
                "description": "Fast and cost-effective model"
            }
        }
        
        return model_info.get(model, {})
    
    def list_models(self) -> List[Dict]:
        """List available models"""
        return [
            {
                "id": model.value,
                "name": model.value,
                "info": self.get_model_info(model)
            }
            for model in ModelType
        ]
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "anthropic_installed": ANTHROPIC_AVAILABLE,
            "default_model": self.default_model.value,
            "api_key_configured": bool(self.api_key)
        }
