
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Gemini Connector
===========================
Connector for Google Gemini API
Provides integration with Google's language models
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("GeminiConnector")

# Try to import google generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")


class GeminiModel(Enum):
    """Gemini model types"""
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_ULTRA = "gemini-ultra"


@dataclass
class GenerationConfig:
    """Generation configuration"""
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 40
    max_output_tokens: int = 1024


class GeminiConnector:
    """
    Gemini Connector
    
    Provides:
    - Text generation
    - Chat completion
    - Multi-modal support
    - Model management
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("GeminiConnector")
        self.api_key = api_key
        self.client = None
        self.default_model = GeminiModel.GEMINI_PRO
        
        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(self.default_model.value)
                self.logger.info("Gemini client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return GEMINI_AVAILABLE and self.client is not None
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[GeminiModel] = None,
        config: Optional[GenerationConfig] = None
    ) -> Optional[str]:
        """
        Generate text using Gemini
        
        Args:
            prompt: Input prompt
            model: Model to use
            config: Generation configuration
            
        Returns:
            Generated text
        """
        if not self.is_available():
            self.logger.warning("Gemini connector not available")
            return None
        
        model = model or self.default_model
        config = config or GenerationConfig()
        
        try:
            if model.value != self.default_model.value:
                model_client = genai.GenerativeModel(model.value)
            else:
                model_client = self.client
            
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                max_output_tokens=config.max_output_tokens
            )
            
            response = model_client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[GeminiModel] = None,
        config: Optional[GenerationConfig] = None
    ) -> Optional[str]:
        """
        Chat completion using Gemini
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            config: Generation configuration
            
        Returns:
            Generated response
        """
        if not self.is_available():
            self.logger.warning("Gemini connector not available")
            return None
        
        model = model or self.default_model
        config = config or GenerationConfig()
        
        try:
            if model.value != self.default_model.value:
                model_client = genai.GenerativeModel(model.value)
            else:
                model_client = self.client
            
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                max_output_tokens=config.max_output_tokens
            )
            
            chat = model_client.start_chat(history=messages[:-1])
            response = chat.send_message(
                messages[-1]["content"],
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            return None
    
    async def stream_text(
        self,
        prompt: str,
        model: Optional[GeminiModel] = None,
        config: Optional[GenerationConfig] = None
    ):
        """
        Stream text generation using Gemini
        
        Args:
            prompt: Input prompt
            model: Model to use
            config: Generation configuration
            
        Yields:
            Text chunks
        """
        if not self.is_available():
            self.logger.warning("Gemini connector not available")
            return
        
        model = model or self.default_model
        config = config or GenerationConfig()
        
        try:
            if model.value != self.default_model.value:
                model_client = genai.GenerativeModel(model.value)
            else:
                model_client = self.client
            
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                max_output_tokens=config.max_output_tokens
            )
            
            response = model_client.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            self.logger.error(f"Stream generation failed: {e}")
    
    def get_model_info(self, model: GeminiModel) -> Dict:
        """Get information about a model"""
        model_info = {
            GeminiModel.GEMINI_PRO: {
                "name": "Gemini Pro",
                "context": 1000000,
                "description": "Most capable model for complex tasks"
            },
            GeminiModel.GEMINI_PRO_VISION: {
                "name": "Gemini Pro Vision",
                "context": 1000000,
                "description": "Multi-modal model with vision capabilities"
            },
            GeminiModel.GEMINI_ULTRA: {
                "name": "Gemini Ultra",
                "context": 1000000,
                "description": "Most advanced model"
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
            for model in GeminiModel
        ]
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "gemini_installed": GEMINI_AVAILABLE,
            "default_model": self.default_model.value,
            "api_key_configured": bool(self.api_key)
        }
