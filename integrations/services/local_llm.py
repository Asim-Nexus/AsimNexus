
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Local LLM Runner
===========================
Ollama and LM Studio integration for offline LLM
Includes: Model management, inference, streaming, quantization
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("LocalLLM")


class LLMProvider(Enum):
    """Local LLM providers"""
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class ModelStatus(Enum):
    """Model statuses"""
    AVAILABLE = "available"
    LOADING = "loading"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LocalModel:
    """Local LLM model"""
    model_id: str
    name: str
    provider: LLMProvider
    size_gb: float
    quantization: str
    status: ModelStatus
    parameters: Dict[str, Any]


@dataclass
class LLMInference:
    """LLM inference result"""
    inference_id: str
    model_id: str
    prompt: str
    response: str
    tokens_generated: int
    time_seconds: float
    created_at: datetime = field(default_factory=datetime.utcnow)


class LocalLLM:
    """Local LLM runner integration"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", lm_studio_url: str = "http://localhost:1234"):
        self.ollama_url = ollama_url
        self.lm_studio_url = lm_studio_url
        self.models: Dict[str, LocalModel] = {}
        self.inferences: Dict[str, LLMInference] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize local LLM runner"""
        logger.info("🤖 Initializing Local LLM Runner...")
        logger.info("🦙 Setting up Ollama integration")
        logger.info("🎨 Setting up LM Studio integration")
        logger.info("📊 Setting up model management")
        logger.info("✅ Local LLM Runner initialized")
    
    async def list_ollama_models(self) -> List[LocalModel]:
        """List available Ollama models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model_data in data.get("models", []):
                            model = LocalModel(
                                model_id=model_data.get("name"),
                                name=model_data.get("name"),
                                provider=LLMProvider.OLLAMA,
                                size_gb=model_data.get("size", 0) / (1024**3),
                                quantization="unknown",
                                status=ModelStatus.AVAILABLE,
                                parameters={}
                            )
                            models.append(model)
                            self.models[model.model_id] = model
                        logger.info(f"✅ Found {len(models)} Ollama models")
                        return models
                    return []
        except Exception as e:
            logger.error(f"Ollama models retrieval error: {e}")
            return []
    
    async def list_lm_studio_models(self) -> List[LocalModel]:
        """List available LM Studio models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lm_studio_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model_data in data.get("data", []):
                            model = LocalModel(
                                model_id=model_data.get("id"),
                                name=model_data.get("id"),
                                provider=LLMProvider.LM_STUDIO,
                                size_gb=0,
                                quantization="unknown",
                                status=ModelStatus.AVAILABLE,
                                parameters={}
                            )
                            models.append(model)
                            self.models[model.model_id] = model
                        logger.info(f"✅ Found {len(models)} LM Studio models")
                        return models
                    return []
        except Exception as e:
            logger.error(f"LM Studio models retrieval error: {e}")
            return []
    
    async def generate(
        self,
        prompt: str,
        model: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> LLMInference:
        """Generate text with local LLM"""
        start_time = datetime.utcnow()
        
        if provider == LLMProvider.OLLAMA:
            return await self._ollama_generate(prompt, model, max_tokens, temperature, start_time)
        else:
            return await self._lm_studio_generate(prompt, model, max_tokens, temperature, start_time)
    
    async def _ollama_generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        start_time: datetime
    ) -> LLMInference:
        """Generate with Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get("response", "")
                        tokens_generated = len(response_text.split())
                        
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        
                        inference = LLMInference(
                            inference_id=f"inf_{uuid.uuid4().hex[:8]}",
                            model_id=model,
                            prompt=prompt,
                            response=response_text,
                            tokens_generated=tokens_generated,
                            time_seconds=duration
                        )
                        
                        self.inferences[inference.inference_id] = inference
                        logger.info(f"✅ Generated {tokens_generated} tokens with Ollama")
                        return inference
                    else:
                        logger.error(f"Ollama generation failed: {response.status}")
                        return LLMInference(
                            inference_id=f"inf_{uuid.uuid4().hex[:8]}",
                            model_id=model,
                            prompt=prompt,
                            response="Generation failed",
                            tokens_generated=0,
                            time_seconds=0
                        )
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return LLMInference(
                inference_id=f"inf_{uuid.uuid4().hex[:8]}",
                model_id=model,
                prompt=prompt,
                response=f"Error: {str(e)}",
                tokens_generated=0,
                time_seconds=0
            )
    
    async def _lm_studio_generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        start_time: datetime
    ) -> LLMInference:
        """Generate with LM Studio"""
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.lm_studio_url}/v1/chat/completions", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data["choices"][0]["message"]["content"]
                        tokens_generated = len(response_text.split())
                        
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        
                        inference = LLMInference(
                            inference_id=f"inf_{uuid.uuid4().hex[:8]}",
                            model_id=model,
                            prompt=prompt,
                            response=response_text,
                            tokens_generated=tokens_generated,
                            time_seconds=duration
                        )
                        
                        self.inferences[inference.inference_id] = inference
                        logger.info(f"✅ Generated {tokens_generated} tokens with LM Studio")
                        return inference
                    else:
                        logger.error(f"LM Studio generation failed: {response.status}")
                        return LLMInference(
                            inference_id=f"inf_{uuid.uuid4().hex[:8]}",
                            model_id=model,
                            prompt=prompt,
                            response="Generation failed",
                            tokens_generated=0,
                            time_seconds=0
                        )
        except Exception as e:
            logger.error(f"LM Studio generation error: {e}")
            return LLMInference(
                inference_id=f"inf_{uuid.uuid4().hex[:8]}",
                model_id=model,
                prompt=prompt,
                response=f"Error: {str(e)}",
                tokens_generated=0,
                time_seconds=0
            )
    
    async def stream_generate(
        self,
        prompt: str,
        model: str,
        provider: LLMProvider = LLMProvider.OLLAMA
    ):
        """Stream generation"""
        if provider == LLMProvider.OLLAMA:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                        async for line in response.content:
                            if line:
                                yield line.decode('utf-8')
            except Exception as e:
                logger.error(f"Stream generation error: {e}")
    
    async def pull_model(self, model: str, provider: LLMProvider = LLMProvider.OLLAMA) -> bool:
        """Pull a model"""
        if provider == LLMProvider.OLLAMA:
            payload = {"name": model}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.ollama_url}/api/pull", json=payload) as response:
                        if response.status == 200:
                            logger.info(f"✅ Pulling model: {model}")
                            return True
                        else:
                            logger.error(f"Model pull failed: {response.status}")
                            return False
            except Exception as e:
                logger.error(f"Model pull error: {e}")
                return False
        
        return False
    
    def get_model(self, model_id: str) -> Optional[LocalModel]:
        """Get model by ID"""
        return self.models.get(model_id)
    
    def get_inference(self, inference_id: str) -> Optional[LLMInference]:
        """Get inference by ID"""
        return self.inferences.get(inference_id)


# Global instance
_local_llm: Optional[LocalLLM] = None


def get_local_llm() -> LocalLLM:
    """Get singleton instance"""
    global _local_llm
    if _local_llm is None:
        _local_llm = LocalLLM()
    return _local_llm
