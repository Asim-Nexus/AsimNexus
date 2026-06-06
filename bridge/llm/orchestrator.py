
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Adaptive LLM Orchestrator
==================================
Intelligent switching between local and cloud models
Monitors RTX 2060 VRAM usage and optimizes performance
"""

import asyncio
import logging
import json
import time
import psutil
import GPUtil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import subprocess

logger = logging.getLogger("LLMOrchestrator")

class AdaptiveLLMOrchestrator:
    """Intelligent LLM switching based on hardware load"""
    
    def __init__(self):
        self.local_models = {
            "llama-3-8b": {
                "name": "Llama 3 8B",
                "path": "/models/llama-3-8b.Q4_K_M.gguf",
                "vram_required": 6,  # GB
                "performance": 75,
                "context_length": 8192,
                "speed": "fast"
            },
            "qwen-7b": {
                "name": "Qwen 7B",
                "path": "/models/qwen-7b.Q4_K_M.gguf", 
                "vram_required": 5,  # GB
                "performance": 70,
                "context_length": 8192,
                "speed": "fast"
            },
            "mistral-7b": {
                "name": "Mistral 7B",
                "path": "/models/mistral-7b.Q4_K_M.gguf",
                "vram_required": 5,  # GB
                "performance": 72,
                "context_length": 8192,
                "speed": "fast"
            }
        }
        
        self.cloud_models = {
            "claude-3-5-sonnet": {
                "name": "Claude 3.5 Sonnet",
                "provider": "OpenRouter",
                "cost_per_input": 0.003,
                "cost_per_output": 0.015,
                "performance": 95,
                "context_length": 200000,
                "speed": "medium"
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "provider": "OpenRouter", 
                "cost_per_input": 0.01,
                "cost_per_output": 0.03,
                "performance": 92,
                "context_length": 128000,
                "speed": "medium"
            },
            "gemini-pro": {
                "name": "Gemini Pro",
                "provider": "OpenRouter",
                "cost_per_input": 0.0005,
                "cost_per_output": 0.0015,
                "performance": 88,
                "context_length": 32768,
                "speed": "fast"
            }
        }
        
        self.switching_config = {
            "vram_threshold": 80,  # Switch to cloud if VRAM > 80%
            "cpu_threshold": 85,    # Switch to cloud if CPU > 85%
            "memory_threshold": 90,  # Switch to cloud if RAM > 90%
            "temperature_threshold": 75,  # Switch to cloud if GPU temp > 75°C
            "switch_cooldown": 30,  # Wait 30 seconds between switches
            "prefer_local": True,  # Prefer local models when available
            "cost_optimization": True,  # Consider cost in model selection
            "performance_weight": 0.7,  # Weight performance vs cost
            "cost_weight": 0.3
        }
        
        self.current_model = None
        self.current_provider = None
        self.switch_history = []
        self.performance_metrics = {
            "local_responses": 0,
            "cloud_responses": 0,
            "avg_local_time": 0.0,
            "avg_cloud_time": 0.0,
            "total_cost": 0.0
        }
        
        self.hardware_monitor = {
            "gpu_vram_usage": 0,
            "gpu_temperature": 0,
            "cpu_usage": 0,
            "ram_usage": 0,
            "gpu_utilization": 0
        }
        
        self.last_switch_time = 0
        self.api_key = None
        
    async def initialize_orchestrator(self, openrouter_api_key: str) -> bool:
        """Initialize the LLM orchestrator"""
        try:
            logger.info("🧠 Initializing Adaptive LLM Orchestrator...")
            
            self.api_key = openrouter_api_key
            
            # Initialize hardware monitoring
            await self._initialize_hardware_monitoring()
            
            # Select initial model
            await self._select_optimal_model()
            
            logger.info("✅ Adaptive LLM Orchestrator initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}")
            return False
    
    async def _initialize_hardware_monitoring(self) -> None:
        """Initialize hardware monitoring"""
        try:
            # Get GPU info
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.hardware_monitor["gpu_vram_usage"] = gpu.memoryUtil * 100
                self.hardware_monitor["gpu_temperature"] = gpu.temperature
                self.hardware_monitor["gpu_utilization"] = gpu.load * 100
                logger.info(f"🎮 GPU detected: {gpu.name}, VRAM: {gpu.memoryTotal}GB")
            else:
                logger.warning("⚠️ No GPU detected, using CPU-only mode")
            
            # Get system info
            self.hardware_monitor["cpu_usage"] = psutil.cpu_percent()
            self.hardware_monitor["ram_usage"] = psutil.virtual_memory().percent
            
            logger.info(f"💻 System: CPU {self.hardware_monitor['cpu_usage']}%, RAM {self.hardware_monitor['ram_usage']}%")
            
        except Exception as e:
            logger.error(f"❌ Hardware monitoring error: {e}")
    
    async def _select_optimal_model(self) -> Dict[str, Any]:
        """Select optimal model based on current conditions"""
        try:
            # Check if we can use local models
            can_use_local = await self._can_use_local_models()
            
            if can_use_local and self.switching_config["prefer_local"]:
                # Select best local model
                best_local = await self._select_best_local_model()
                if best_local:
                    self.current_model = best_local["id"]
                    self.current_provider = "local"
                    logger.info(f"🏠 Selected local model: {best_local['name']}")
                    return best_local
            
            # Select best cloud model
            best_cloud = await self._select_best_cloud_model()
            if best_cloud:
                self.current_model = best_cloud["id"]
                self.current_provider = "cloud"
                logger.info(f"☁️ Selected cloud model: {best_cloud['name']}")
                return best_cloud
            
            # Fallback to smallest local model
            fallback_model = list(self.local_models.keys())[0]
            self.current_model = fallback_model
            self.current_provider = "local"
            logger.warning(f"⚠️ Fallback to local model: {fallback_model}")
            
            return self.local_models[fallback_model]
            
        except Exception as e:
            logger.error(f"❌ Model selection error: {e}")
            return {"id": "error", "error": str(e)}
    
    async def _can_use_local_models(self) -> bool:
        """Check if local models can be used"""
        try:
            # Check VRAM availability
            if self.hardware_monitor["gpu_vram_usage"] > self.switching_config["vram_threshold"]:
                return False
            
            # Check GPU temperature
            if self.hardware_monitor["gpu_temperature"] > self.switching_config["temperature_threshold"]:
                return False
            
            # Check CPU usage
            if self.hardware_monitor["cpu_usage"] > self.switching_config["cpu_threshold"]:
                return False
            
            # Check RAM usage
            if self.hardware_monitor["ram_usage"] > self.switching_config["memory_threshold"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Local model check error: {e}")
            return False
    
    async def _select_best_local_model(self) -> Optional[Dict[str, Any]]:
        """Select best local model based on available VRAM"""
        try:
            available_models = []
            
            for model_id, model_info in self.local_models.items():
                # Check if model fits in available VRAM
                available_vram = 8 - (self.hardware_monitor["gpu_vram_usage"] / 100 * 8)
                
                if model_info["vram_required"] <= available_vram:
                    score = model_info["performance"]
                    available_models.append({
                        **model_info,
                        "id": model_id,
                        "score": score,
                        "available_vram": available_vram
                    })
            
            if not available_models:
                return None
            
            # Sort by performance score
            available_models.sort(key=lambda x: x["score"], reverse=True)
            return available_models[0]
            
        except Exception as e:
            logger.error(f"❌ Local model selection error: {e}")
            return None
    
    async def _select_best_cloud_model(self) -> Optional[Dict[str, Any]]:
        """Select best cloud model based on cost and performance"""
        try:
            scored_models = []
            
            for model_id, model_info in self.cloud_models.items():
                # Calculate score based on performance and cost
                performance_score = model_info["performance"]
                cost_score = 100 - (model_info["cost_per_input"] + model_info["cost_per_output"]) * 1000
                
                combined_score = (
                    performance_score * self.switching_config["performance_weight"] +
                    cost_score * self.switching_config["cost_weight"]
                )
                
                scored_models.append({
                    **model_info,
                    "id": model_id,
                    "score": combined_score
                })
            
            if not scored_models:
                return None
            
            # Sort by combined score
            scored_models.sort(key=lambda x: x["score"], reverse=True)
            return scored_models[0]
            
        except Exception as e:
            logger.error(f"❌ Cloud model selection error: {e}")
            return None
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response using current optimal model"""
        try:
            start_time = time.time()
            
            # Update hardware metrics
            await self._update_hardware_metrics()
            
            # Check if we need to switch models
            if await self._should_switch_models():
                await self._switch_model()
            
            # Generate response based on current provider
            if self.current_provider == "local":
                response = await self._generate_local_response(prompt, context)
            else:
                response = await self._generate_cloud_response(prompt, context)
            
            # Update performance metrics
            end_time = time.time()
            response_time = end_time - start_time
            
            await self._update_performance_metrics(response_time, response.get("cost", 0))
            
            return {
                "success": True,
                "response": response.get("content", ""),
                "model_used": self.current_model,
                "provider": self.current_provider,
                "response_time": response_time,
                "cost": response.get("cost", 0),
                "hardware_metrics": self.hardware_monitor.copy(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_local_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response using local model"""
        try:
            model_info = self.local_models.get(self.current_model)
            if not model_info:
                raise Exception(f"Local model {self.current_model} not found")
            
            # Simulate local model inference
            # In real implementation, this would use llama.cpp or similar
            logger.info(f"🏠 Generating response with local model: {model_info['name']}")
            
            # Simulate processing time based on model performance
            processing_time = 2.0 + (100 - model_info["performance"]) / 50
            
            # Generate mock response
            response_content = f"[Local {model_info['name']}] This is a simulated response to: {prompt[:100]}..."
            
            return {
                "content": response_content,
                "processing_time": processing_time,
                "cost": 0,
                "model_info": model_info
            }
            
        except Exception as e:
            logger.error(f"❌ Local response generation error: {e}")
            return {"content": "", "error": str(e)}
    
    async def _generate_cloud_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response using cloud model via OpenRouter"""
        try:
            model_info = self.cloud_models.get(self.current_model)
            if not model_info:
                raise Exception(f"Cloud model {self.current_model} not found")
            
            logger.info(f"☁️ Generating response with cloud model: {model_info['name']}")
            
            # Prepare OpenRouter API request
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
                "top_p": 0.9
            }
            
            # Make API request
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                    
                    result = await response.json()
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Extract response and calculate cost
            message = result.get("choices", [{}])[0].get("message", {})
            response_content = message.get("content", "")
            
            usage = result.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            cost = (
                input_tokens * model_info["cost_per_input"] / 1000 +
                output_tokens * model_info["cost_per_output"] / 1000
            )
            
            return {
                "content": response_content,
                "processing_time": response_time,
                "cost": cost,
                "usage": usage,
                "model_info": model_info
            }
            
        except Exception as e:
            logger.error(f"❌ Cloud response generation error: {e}")
            return {"content": "", "error": str(e)}
    
    async def _update_hardware_metrics(self) -> None:
        """Update hardware metrics"""
        try:
            # Update GPU metrics
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.hardware_monitor["gpu_vram_usage"] = gpu.memoryUtil * 100
                self.hardware_monitor["gpu_temperature"] = gpu.temperature
                self.hardware_monitor["gpu_utilization"] = gpu.load * 100
            
            # Update system metrics
            self.hardware_monitor["cpu_usage"] = psutil.cpu_percent()
            self.hardware_monitor["ram_usage"] = psutil.virtual_memory().percent
            
        except Exception as e:
            logger.error(f"❌ Hardware metrics update error: {e}")
    
    async def _should_switch_models(self) -> bool:
        """Check if we should switch models"""
        try:
            # Check cooldown
            current_time = time.time()
            if current_time - self.last_switch_time < self.switching_config["switch_cooldown"]:
                return False
            
            # Check if current model is still optimal
            if self.current_provider == "local":
                # Check if local is still viable
                if not await self._can_use_local_models():
                    return True
            else:
                # Check if we can switch back to local
                if await self._can_use_local_models() and self.switching_config["prefer_local"]:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Model switch check error: {e}")
            return False
    
    async def _switch_model(self) -> None:
        """Switch to optimal model"""
        try:
            old_provider = self.current_provider
            old_model = self.current_model
            
            # Select new optimal model
            new_model_info = await self._select_optimal_model()
            
            if new_model_info and new_model_info["id"] != old_model:
                self.current_model = new_model_info["id"]
                self.current_provider = "local" if new_model_info in self.local_models else "cloud"
                
                # Log the switch
                switch_event = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "from_provider": old_provider,
                    "from_model": old_model,
                    "to_provider": self.current_provider,
                    "to_model": self.current_model,
                    "reason": "optimization",
                    "hardware_metrics": self.hardware_monitor.copy()
                }
                
                self.switch_history.append(switch_event)
                self.last_switch_time = time.time()
                
                logger.info(f"🔄 Model switch: {old_provider}:{old_model} → {self.current_provider}:{self.current_model}")
            
        except Exception as e:
            logger.error(f"❌ Model switch error: {e}")
    
    async def _update_performance_metrics(self, response_time: float, cost: float) -> None:
        """Update performance metrics"""
        try:
            if self.current_provider == "local":
                self.performance_metrics["local_responses"] += 1
                
                # Update average local response time
                total_local_time = (
                    self.performance_metrics["avg_local_time"] * (self.performance_metrics["local_responses"] - 1) + 
                    response_time
                )
                self.performance_metrics["avg_local_time"] = total_local_time / self.performance_metrics["local_responses"]
            else:
                self.performance_metrics["cloud_responses"] += 1
                self.performance_metrics["total_cost"] += cost
                
                # Update average cloud response time
                total_cloud_time = (
                    self.performance_metrics["avg_cloud_time"] * (self.performance_metrics["cloud_responses"] - 1) + 
                    response_time
                )
                self.performance_metrics["avg_cloud_time"] = total_cloud_time / self.performance_metrics["cloud_responses"]
            
        except Exception as e:
            logger.error(f"❌ Performance metrics update error: {e}")
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        try:
            return {
                "current_model": self.current_model,
                "current_provider": self.current_provider,
                "hardware_metrics": self.hardware_monitor.copy(),
                "performance_metrics": self.performance_metrics.copy(),
                "switching_config": self.switching_config.copy(),
                "switch_history": self.switch_history[-10:],  # Last 10 switches
                "available_local_models": len(self.local_models),
                "available_cloud_models": len(self.cloud_models),
                "last_switch": datetime.fromtimestamp(self.last_switch_time).isoformat() if self.last_switch_time > 0 else None
            }
            
        except Exception as e:
            logger.error(f"❌ Status check error: {e}")
            return {"error": str(e)}
    
    async def update_switching_config(self, config: Dict[str, Any]) -> bool:
        """Update switching configuration"""
        try:
            for key, value in config.items():
                if key in self.switching_config:
                    self.switching_config[key] = value
                    logger.info(f"⚙️ Updated config: {key} = {value}")
            
            # Re-evaluate current model
            await self._select_optimal_model()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Config update error: {e}")
            return False
    
    async def force_switch_to_provider(self, provider: str) -> bool:
        """Force switch to specific provider"""
        try:
            if provider not in ["local", "cloud"]:
                return False
            
            old_provider = self.current_provider
            old_model = self.current_model
            
            if provider == "local":
                best_local = await self._select_best_local_model()
                if best_local:
                    self.current_model = best_local["id"]
                    self.current_provider = "local"
            else:
                best_cloud = await self._select_best_cloud_model()
                if best_cloud:
                    self.current_model = best_cloud["id"]
                    self.current_provider = "cloud"
            
            # Log the forced switch
            switch_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "from_provider": old_provider,
                "from_model": old_model,
                "to_provider": self.current_provider,
                "to_model": self.current_model,
                "reason": "forced",
                "hardware_metrics": self.hardware_monitor.copy()
            }
            
            self.switch_history.append(switch_event)
            self.last_switch_time = time.time()
            
            logger.info(f"🔄 Forced switch: {old_provider}:{old_model} → {self.current_provider}:{self.current_model}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Forced switch error: {e}")
            return False
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        try:
            total_responses = self.performance_metrics["local_responses"] + self.performance_metrics["cloud_responses"]
            
            if total_responses == 0:
                return {"error": "No responses recorded"}
            
            local_percentage = (self.performance_metrics["local_responses"] / total_responses) * 100
            cloud_percentage = (self.performance_metrics["cloud_responses"] / total_responses) * 100
            
            avg_local_time = self.performance_metrics["avg_local_time"]
            avg_cloud_time = self.performance_metrics["avg_cloud_time"]
            
            efficiency_score = 0
            if avg_local_time > 0 and avg_cloud_time > 0:
                # Calculate efficiency (lower is better)
                efficiency_score = max(0, 100 - ((avg_cloud_time - avg_local_time) / avg_cloud_time) * 100)
            
            return {
                "total_responses": total_responses,
                "local_responses": self.performance_metrics["local_responses"],
                "cloud_responses": self.performance_metrics["cloud_responses"],
                "local_percentage": round(local_percentage, 1),
                "cloud_percentage": round(cloud_percentage, 1),
                "avg_local_time": round(avg_local_time, 3),
                "avg_cloud_time": round(avg_cloud_time, 3),
                "total_cost": round(self.performance_metrics["total_cost"], 4),
                "efficiency_score": round(efficiency_score, 1),
                "recommendations": await self._generate_recommendations()
            }
            
        except Exception as e:
            logger.error(f"❌ Performance report error: {e}")
            return {"error": str(e)}
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        try:
            # Check GPU utilization
            if self.hardware_monitor["gpu_utilization"] > 90:
                recommendations.append("Consider upgrading GPU for better performance")
            
            # Check VRAM usage
            if self.hardware_monitor["gpu_vram_usage"] > 85:
                recommendations.append("VRAM usage is high, consider using smaller models or cloud fallback")
            
            # Check cost efficiency
            if self.performance_metrics["total_cost"] > 10:  # $10 in current session
                recommendations.append("High cloud usage detected, consider optimizing prompts or using local models")
            
            # Check response times
            if self.performance_metrics["avg_cloud_time"] > 5:
                recommendations.append("Cloud response times are slow, check network connection")
            
            # Check switch frequency
            recent_switches = [
                switch for switch in self.switch_history
                if datetime.fromisoformat(switch["timestamp"]) > datetime.utcnow() - timedelta(hours=1)
            ]
            
            if len(recent_switches) > 5:
                recommendations.append("Frequent model switching detected, consider adjusting thresholds")
            
            if not recommendations:
                recommendations.append("System is performing optimally")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Recommendation generation error: {e}")
            return ["Error generating recommendations"]

# Global LLM orchestrator
_adaptive_orchestrator = AdaptiveLLMOrchestrator()

async def main():
    """Main entry point for testing"""
    # Initialize orchestrator
    success = await _adaptive_orchestrator.initialize_orchestrator("your-openrouter-api-key")
    print(f"Orchestrator initialization: {success}")
    
    if success:
        # Test response generation
        response = await _adaptive_orchestrator.generate_response(
            "What is the capital of Nepal?",
            {"context": "general_knowledge"}
        )
        print(f"Response generation: {response}")
        
        # Get status
        status = await _adaptive_orchestrator.get_orchestrator_status()
        print(f"Orchestrator status: {status}")
        
        # Get performance report
        report = await _adaptive_orchestrator.get_performance_report()
        print(f"Performance report: {report}")

if __name__ == "__main__":
    asyncio.run(main())
