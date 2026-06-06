
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS OpenAI Connector
==========================
Connector for OpenAI API
Provides integration with OpenAI's language models
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("OpenAIConnector")

# Try to import openai
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed. Install with: pip install openai")


class OpenAIModel(Enum):
    """OpenAI model types"""
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_4_32K = "gpt-4-32k"
    TEXT_DAVINCI_003 = "text-davinci-003"


@dataclass
class Message:
    """A message for the API"""
    role: str
    content: str


class OpenAIConnector:
    """
    OpenAI Connector
    
    Provides:
    - Text generation
    - Chat completion
    - Streaming responses
    - Model management
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("OpenAIConnector")
        self.api_key = api_key
        self.client = None
        self.default_model = OpenAIModel.GPT_3_5_TURBO
        
        if OPENAI_AVAILABLE and api_key:
            try:
                openai.api_key = api_key
                self.client = openai
                self.logger.info("OpenAI client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return OPENAI_AVAILABLE and self.client is not None
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[OpenAIModel] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using OpenAI
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.is_available():
            self.logger.warning("OpenAI connector not available")
            return None
        
        model = model or self.default_model
        
        try:
            response = self.client.Completion.create(
                model=model.value,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].text
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[OpenAIModel] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Chat completion using OpenAI
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        if not self.is_available():
            self.logger.warning("OpenAI connector not available")
            return None
        
        model = model or self.default_model
        
        try:
            response = self.client.ChatCompletion.create(
                model=model.value,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            return None
    
    async def stream_text(
        self,
        prompt: str,
        model: Optional[OpenAIModel] = None,
        max_tokens: int = 1024
    ):
        """
        Stream text generation using OpenAI
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks
        """
        if not self.is_available():
            self.logger.warning("OpenAI connector not available")
            return
        
        model = model or self.default_model
        
        try:
            response = self.client.Completion.create(
                model=model.value,
                prompt=prompt,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].text:
                    yield chunk.choices[0].text
                    
        except Exception as e:
            self.logger.error(f"Stream generation failed: {e}")
    
    def get_model_info(self, model: OpenAIModel) -> Dict:
        """Get information about a model"""
        model_info = {
            OpenAIModel.GPT_4_TURBO: {
                "name": "GPT-4 Turbo",
                "context": 128000,
                "description": "Most advanced model with vision capabilities"
            },
            OpenAIModel.GPT_4: {
                "name": "GPT-4",
                "context": 8192,
                "description": "Advanced model for complex tasks"
            },
            OpenAIModel.GPT_3_5_TURBO: {
                "name": "GPT-3.5 Turbo",
                "context": 4096,
                "description": "Fast and cost-effective model"
            },
            OpenAIModel.GPT_3_5_TURBO_16K: {
                "name": "GPT-3.5 Turbo 16K",
                "context": 16384,
                "description": "Extended context version of GPT-3.5 Turbo"
            },
            OpenAIModel.GPT_4_32K: {
                "name": "GPT-4 32K",
                "context": 32768,
                "description": "Extended context version of GPT-4"
            },
            OpenAIModel.TEXT_DAVINCI_003: {
                "name": "Text Davinci 003",
                "context": 4096,
                "description": "Legacy text generation model"
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
            for model in OpenAIModel
        ]
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "openai_installed": OPENAI_AVAILABLE,
            "default_model": self.default_model.value,
            "api_key_configured": bool(self.api_key)
        }
