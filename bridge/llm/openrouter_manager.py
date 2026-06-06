
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Multi-Model Support - OpenRouter API
===============================================
Fallback to cloud models when local GPU is busy
Supports GPT-4, Claude 3, Gemini, and more
"""

import asyncio
import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
import time

logger = logging.getLogger("OpenRouterManager")

class OpenRouterManager:
    """Manages OpenRouter API for multi-model fallback support"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://openrouter.ai/api/v1"
        self.models = {
            # Premium Models (High Performance)
            "gpt-4-turbo": {
                "id": "openai/gpt-4-turbo-preview",
                "name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "cost_per_input": 0.01,
                "cost_per_output": 0.03,
                "context_length": 128000,
                "performance": 95,
                "category": "premium"
            },
            "claude-3-opus": {
                "id": "anthropic/claude-3-opus",
                "name": "Claude 3 Opus",
                "provider": "Anthropic",
                "cost_per_input": 0.015,
                "cost_per_output": 0.075,
                "context_length": 200000,
                "performance": 98,
                "category": "premium"
            },
            "claude-3-sonnet": {
                "id": "anthropic/claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "cost_per_input": 0.003,
                "cost_per_output": 0.015,
                "context_length": 200000,
                "performance": 92,
                "category": "premium"
            },
            "gemini-pro": {
                "id": "google/gemini-pro",
                "name": "Gemini Pro",
                "provider": "Google",
                "cost_per_input": 0.0005,
                "cost_per_output": 0.0015,
                "context_length": 32768,
                "performance": 88,
                "category": "standard"
            },
            
            # Standard Models (Cost Effective)
            "gpt-3.5-turbo": {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "cost_per_input": 0.0005,
                "cost_per_output": 0.0015,
                "context_length": 16384,
                "performance": 75,
                "category": "standard"
            },
            "claude-instant": {
                "id": "anthropic/claude-instant",
                "name": "Claude Instant",
                "provider": "Anthropic",
                "cost_per_input": 0.0008,
                "cost_per_output": 0.0024,
                "context_length": 100000,
                "performance": 70,
                "category": "standard"
            },
            
            # Specialized Models
            "codellama-70b": {
                "id": "meta-llama/codellama-70b-instruct",
                "name": "CodeLlama 70B",
                "provider": "Meta",
                "cost_per_input": 0.0009,
                "cost_per_output": 0.0009,
                "context_length": 4096,
                "performance": 82,
                "category": "coding"
            },
            "mistral-7b": {
                "id": "mistralai/mistral-7b-instruct",
                "name": "Mistral 7B",
                "provider": "Mistral",
                "cost_per_input": 0.00007,
                "cost_per_output": 0.00007,
                "context_length": 32768,
                "performance": 65,
                "category": "budget"
            },
            
            # Nepal-Specific (if available)
            "nepali-llama": {
                "id": "meta-llama/llama-3-8b-instruct",
                "name": "Llama 3 8B (Nepali)",
                "provider": "Meta",
                "cost_per_input": 0.00005,
                "cost_per_output": 0.00005,
                "context_length": 8192,
                "performance": 60,
                "category": "budget"
            }
        }
        
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "model_usage": {},
            "last_reset": datetime.now().isoformat()
        }
        
        self.fallback_config = {
            "enable_fallback": True,
            "local_gpu_threshold": 80,  # Use cloud if local GPU > 80% busy
            "preferred_models": ["claude-3-sonnet", "gpt-4-turbo", "gemini-pro"],
            "budget_models": ["mistral-7b", "nepali-llama"],
            "max_cost_per_request": 0.10,
            "rate_limit_rpm": 60,
            "rate_limit_tpm": 10000
        }
        
        self.request_cache = {}
        self.rate_limiter = {}
        
    async def initialize(self, api_key: str) -> bool:
        """Initialize OpenRouter manager with API key"""
        try:
            self.api_key = api_key
            
            # Test API connection
            test_result = await self._test_api_connection()
            
            if test_result:
                logger.info("🔗 OpenRouter API initialized successfully")
                return True
            else:
                logger.error("❌ OpenRouter API connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenRouter: {e}")
            return False
    
    async def _test_api_connection(self) -> bool:
        """Test OpenRouter API connection"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/models", headers=headers) as response:
                    if response.status == 200:
                        logger.info("✅ OpenRouter API connection verified")
                        return True
                    else:
                        logger.error(f"❌ OpenRouter API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ OpenRouter API test failed: {e}")
            return False
    
    async def check_local_gpu_load(self) -> Dict[str, Any]:
        """Check local GPU load to determine if fallback is needed"""
        try:
            # This would integrate with your RTX Stress Adaptor
            # For now, we'll simulate GPU load checking
            
            # Simulate GPU load (in real implementation, check nvidia-smi)
            gpu_load = 45 + (time.time() % 40)  # Simulate 45-85% load
            memory_used = 6 + (time.time() % 4)  # Simulate 6-10GB used
            
            return {
                "gpu_load": gpu_load,
                "memory_used_gb": memory_used,
                "memory_total_gb": 8,  # RTX 2060 has 8GB
                "should_fallback": gpu_load > self.fallback_config["local_gpu_threshold"]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to check GPU load: {e}")
            return {"gpu_load": 100, "should_fallback": True}  # Fallback to cloud if check fails
    
    async def select_best_model(self, task_type: str = "general", budget_constraint: float = None) -> str:
        """Select the best model based on task type and constraints"""
        
        # Check if we should use cloud fallback
        gpu_status = await self.check_local_gpu_load()
        
        if not self.fallback_config["enable_fallback"] or not gpu_status["should_fallback"]:
            return "local"  # Use local model
        
        # Select cloud model based on task type
        model_candidates = []
        
        if task_type == "coding":
            model_candidates = ["codellama-70b", "claude-3-sonnet", "gpt-4-turbo"]
        elif task_type == "reasoning":
            model_candidates = ["claude-3-opus", "gpt-4-turbo", "claude-3-sonnet"]
        elif task_type == "nepali":
            model_candidates = ["nepali-llama", "claude-3-sonnet", "gemini-pro"]
        elif task_type == "budget":
            model_candidates = self.fallback_config["budget_models"]
        else:
            model_candidates = self.fallback_config["preferred_models"]
        
        # Apply budget constraint if specified
        if budget_constraint:
            affordable_models = []
            for model_id in model_candidates:
                model_info = self.models.get(model_id)
                if model_info:
                    estimated_cost = model_info["cost_per_input"] + model_info["cost_per_output"]
                    if estimated_cost <= budget_constraint:
                        affordable_models.append(model_id)
            
            if affordable_models:
                model_candidates = affordable_models
        
        # Select model based on performance and availability
        best_model = None
        best_score = -1
        
        for model_id in model_candidates:
            model_info = self.models.get(model_id)
            if model_info:
                # Score based on performance and cost efficiency
                cost_efficiency = 1 / (model_info["cost_per_input"] + model_info["cost_per_output"])
                score = model_info["performance"] * 0.7 + cost_efficiency * 30
                
                if score > best_score:
                    best_score = score
                    best_model = model_id
        
        return best_model or self.fallback_config["preferred_models"][0]
    
    async def generate_response(self, prompt: str, model_id: str = None, task_type: str = "general") -> Dict[str, Any]:
        """Generate response using OpenRouter API"""
        try:
            if not self.api_key:
                raise Exception("OpenRouter API key not configured")
            
            # Select model if not specified
            if not model_id:
                model_id = await self.select_best_model(task_type)
                if model_id == "local":
                    return {"success": False, "error": "Use local model instead"}
            
            model_info = self.models.get(model_id)
            if not model_info:
                raise Exception(f"Unknown model: {model_id}")
            
            # Check rate limits
            if not await self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://asimnexus.com",
                "X-Title": "ASIMNEXUS AI Agent"
            }
            
            payload = {
                "model": model_info["id"],
                "messages": [
                    {
                        "role": "system",
                        "content": "You are ASIMNEXUS, an advanced AI assistant. Provide helpful, accurate, and contextually relevant responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": min(2048, model_info["context_length"] // 4),
                "temperature": 0.7,
                "top_p": 0.9,
                "stream": False
            }
            
            # Make request
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions", 
                                     headers=headers, json=payload) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
            # Process response
            end_time = time.time()
            response_time = end_time - start_time
            
            message = result.get("choices", [{}])[0].get("message", {})
            usage = result.get("usage", {})
            
            # Calculate cost
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = input_tokens + output_tokens
            
            cost = (input_tokens * model_info["cost_per_input"] / 1000) + \
                   (output_tokens * model_info["cost_per_output"] / 1000)
            
            # Update usage stats
            await self._update_usage_stats(model_id, total_tokens, cost)
            
            response_data = {
                "success": True,
                "model_id": model_id,
                "model_name": model_info["name"],
                "provider": model_info["provider"],
                "response": message.get("content", ""),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                },
                "cost": cost,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Generated response using {model_info['name']} ({total_tokens} tokens, ${cost:.4f})")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Failed to generate response: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_rate_limit(self) -> bool:
        """Check if rate limits are exceeded"""
        current_time = time.time()
        minute_key = int(current_time // 60)
        
        # Initialize rate limiter if needed
        if minute_key not in self.rate_limiter:
            self.rate_limiter[minute_key] = {"requests": 0, "tokens": 0}
        
        # Check requests per minute
        if self.rate_limiter[minute_key]["requests"] >= self.fallback_config["rate_limit_rpm"]:
            return False
        
        return True
    
    async def _update_usage_stats(self, model_id: str, tokens: int, cost: float) -> None:
        """Update usage statistics"""
        self.usage_stats["total_requests"] += 1
        self.usage_stats["total_tokens"] += tokens
        self.usage_stats["total_cost"] += cost
        
        if model_id not in self.usage_stats["model_usage"]:
            self.usage_stats["model_usage"][model_id] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        
        self.usage_stats["model_usage"][model_id]["requests"] += 1
        self.usage_stats["model_usage"][model_id]["tokens"] += tokens
        self.usage_stats["model_usage"][model_id]["cost"] += cost
        
        # Update rate limiter
        current_time = time.time()
        minute_key = int(current_time // 60)
        
        if minute_key not in self.rate_limiter:
            self.rate_limiter[minute_key] = {"requests": 0, "tokens": 0}
        
        self.rate_limiter[minute_key]["requests"] += 1
        self.rate_limiter[minute_key]["tokens"] += tokens
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their info"""
        return [
            {
                "id": model_id,
                "name": info["name"],
                "provider": info["provider"],
                "category": info["category"],
                "performance": info["performance"],
                "context_length": info["context_length"],
                "cost_per_input": info["cost_per_input"],
                "cost_per_output": info["cost_per_output"]
            }
            for model_id, info in self.models.items()
        ]
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            **self.usage_stats,
            "current_month_cost": self.usage_stats["total_cost"],
            "models_available": len(self.models),
            "fallback_enabled": self.fallback_config["enable_fallback"],
            "gpu_threshold": self.fallback_config["local_gpu_threshold"]
        }
    
    async def reset_usage_stats(self) -> bool:
        """Reset usage statistics"""
        try:
            self.usage_stats = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "model_usage": {},
                "last_reset": datetime.now().isoformat()
            }
            
            logger.info("📊 Usage statistics reset")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reset usage stats: {e}")
            return False
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Update fallback configuration"""
        try:
            for key, value in config.items():
                if key in self.fallback_config:
                    self.fallback_config[key] = value
                    logger.info(f"⚙️ Updated config: {key} = {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update config: {e}")
            return False
    
    async def test_model(self, model_id: str, test_prompt: str = "Hello, how are you?") -> Dict[str, Any]:
        """Test a specific model"""
        try:
            result = await self.generate_response(test_prompt, model_id)
            
            if result["success"]:
                return {
                    "success": True,
                    "model_id": model_id,
                    "model_name": result["model_name"],
                    "response": result["response"],
                    "response_time": result["response_time"],
                    "cost": result["cost"]
                }
            else:
                return {
                    "success": False,
                    "model_id": model_id,
                    "error": result["error"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "model_id": model_id,
                "error": str(e)
            }

# Global OpenRouter manager instance
_openrouter_manager = OpenRouterManager()

async def main():
    """Main entry point for testing"""
    # Initialize with API key (you would get this from environment or config)
    success = await _openrouter_manager.initialize("your-openrouter-api-key")
    print(f"OpenRouter initialization: {success}")
    
    if success:
        # Test model selection
        best_model = await _openrouter_manager.select_best_model("reasoning")
        print(f"Best model for reasoning: {best_model}")
        
        # Test response generation
        result = await _openrouter_manager.generate_response(
            "What is the capital of Nepal?",
            task_type="general"
        )
        print(f"Generation result: {result}")
        
        # Get usage stats
        stats = await _openrouter_manager.get_usage_stats()
        print(f"Usage stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
