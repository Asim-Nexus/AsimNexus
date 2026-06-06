
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS DeepSeek Connector
============================
Connector for DeepSeek API
Provides integration with DeepSeek's language models
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("DeepSeekConnector")

# Try to import openai (DeepSeek uses OpenAI-compatible API)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed. Install with: pip install openai")


class DeepSeekModel(Enum):
    """DeepSeek model types"""
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_CODER = "deepseek-coder"


class DeepSeekConnector:
    """
    DeepSeek Connector
    
    Provides:
    - Text generation
    - Chat completion
    - Code generation
    - Streaming responses
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("DeepSeekConnector")
        self.api_key = api_key
        self.client = None
        self.base_url = "https://api.deepseek.com/v1"
        self.default_model = DeepSeekModel.DEEPSEEK_CHAT
        
        if OPENAI_AVAILABLE and api_key:
            try:
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=self.base_url
                )
                self.logger.info("DeepSeek client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize DeepSeek client: {e}")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return OPENAI_AVAILABLE and self.client is not None
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[DeepSeekModel] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using DeepSeek
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.is_available():
            self.logger.warning("DeepSeek connector not available")
            return None
        
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model.value,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[DeepSeekModel] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Chat completion using DeepSeek
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        if not self.is_available():
            self.logger.warning("DeepSeek connector not available")
            return None
        
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model.value,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            return None
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Generate code using DeepSeek Coder
        
        Args:
            prompt: Code generation prompt
            language: Programming language
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated code
        """
        if not self.is_available():
            self.logger.warning("DeepSeek connector not available")
            return None
        
        try:
            enhanced_prompt = f"Write {language} code for: {prompt}"
            response = self.client.chat.completions.create(
                model=DeepSeekModel.DEEPSEEK_CODER.value,
                messages=[{"role": "user", "content": enhanced_prompt}],
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return None
    
    async def stream_text(
        self,
        prompt: str,
        model: Optional[DeepSeekModel] = None,
        max_tokens: int = 4096
    ):
        """
        Stream text generation using DeepSeek
        
        Args:
            prompt: Input prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks
        """
        if not self.is_available():
            self.logger.warning("DeepSeek connector not available")
            return
        
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model.value,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.logger.error(f"Stream generation failed: {e}")
    
    def get_model_info(self, model: DeepSeekModel) -> Dict:
        """Get information about a model"""
        model_info = {
            DeepSeekModel.DEEPSEEK_CHAT: {
                "name": "DeepSeek Chat",
                "context": 128000,
                "description": "General purpose language model with reasoning capabilities"
            },
            DeepSeekModel.DEEPSEEK_CODER: {
                "name": "DeepSeek Coder",
                "context": 128000,
                "description": "Specialized model for code generation and programming tasks"
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
            for model in DeepSeekModel
        ]
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "openai_installed": OPENAI_AVAILABLE,
            "default_model": self.default_model.value,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url
        }
