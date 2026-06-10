
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Hybrid Execution Manager
=================================
Auto-switching between Small Quantized Models and Full Neural Core
Hardware-adaptive execution based on available resources
"""

import asyncio
import logging
import psutil
import platform
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import torch
import numpy as np

logger = logging.getLogger("HybridManager")

class ExecutionMode(Enum):
    """Execution modes based on hardware capabilities"""
    QUANTIZED_LIGHT = "quantized_light"      # 2-bit GGUF for mobile/old devices
    QUANTIZED_MEDIUM = "quantized_medium"    # 4-bit GGUF for mid-range devices
    QUANTIZED_HEAVY = "quantized_heavy"      # 8-bit GGUF for good devices
    FULL_NEURAL = "full_neural"             # Full parameters for high-end systems
    CLOUD_OFFLOAD = "cloud_offload"         # Offload to cloud for heavy tasks

class HardwareTier(Enum):
    """Hardware capability tiers"""
    TIER_1_MOBILE = "tier_1_mobile"         # < 4GB RAM, no GPU
    TIER_2_BASIC = "tier_2_basic"           # 4-8GB RAM, integrated GPU
    TIER_3_STANDARD = "tier_3_standard"     # 8-16GB RAM, dedicated GPU
    TIER_4_PERFORMANCE = "tier_4_performance" # 16-32GB RAM, good GPU
    TIER_5_ENTERPRISE = "tier_5_enterprise"   # >32GB RAM, high-end GPU

@dataclass
class HardwareProfile:
    """Hardware capability profile"""
    tier: HardwareTier
    ram_total: int
    ram_available: int
    cpu_count: int
    gpu_available: bool
    gpu_memory: int
    gpu_name: str
    execution_mode: ExecutionMode
    model_size_limit: int  # Maximum model size in parameters
    batch_size_limit: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ExecutionTask:
    """Task execution definition"""
    task_id: str
    task_type: str
    complexity: str  # simple, moderate, complex, expert
    priority: str
    estimated_memory: int
    requires_gpu: bool
    execution_mode: Optional[ExecutionMode] = None
    created_at: datetime = field(default_factory=datetime.now)

class HybridExecutionManager:
    """Hybrid Execution Manager - Hardware-adaptive AI execution"""
    
    def __init__(self):
        self.logger = logging.getLogger("HybridManager")
        self.is_active = False
        self.current_profile: Optional[HardwareProfile] = None
        self.execution_history: List[Dict[str, Any]] = []
        
        # Model configurations for different modes
        self.model_configs = self._initialize_model_configs()
        
        # Performance tracking
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "memory_efficiency": 0.0
        }
        
        self.logger.info("🔄 Hybrid Execution Manager Initialized")
    
    def _initialize_model_configs(self) -> Dict[ExecutionMode, Dict[str, Any]]:
        """Initialize model configurations for different execution modes"""
        return {
            ExecutionMode.QUANTIZED_LIGHT: {
                "model_type": "gguf",
                "quantization": "2-bit",
                "max_parameters": 1_000_000_000,  # 1B parameters
                "memory_requirement": 2_000_000_000,  # 2GB RAM
                "batch_size": 1,
                "precision": "int2",
                "description": "Ultra-lightweight for mobile and old devices"
            },
            ExecutionMode.QUANTIZED_MEDIUM: {
                "model_type": "gguf",
                "quantization": "4-bit",
                "max_parameters": 3_000_000_000,  # 3B parameters
                "memory_requirement": 4_000_000_000,  # 4GB RAM
                "batch_size": 2,
                "precision": "int4",
                "description": "Balanced for mid-range devices"
            },
            ExecutionMode.QUANTIZED_HEAVY: {
                "model_type": "gguf",
                "quantization": "8-bit",
                "max_parameters": 7_000_000_000,  # 7B parameters
                "memory_requirement": 8_000_000_000,  # 8GB RAM
                "batch_size": 4,
                "precision": "int8",
                "description": "Heavy quantized for good devices"
            },
            ExecutionMode.FULL_NEURAL: {
                "model_type": "full",
                "quantization": "fp16",
                "max_parameters": 70_000_000_000,  # 70B parameters
                "memory_requirement": 16_000_000_000,  # 16GB RAM
                "batch_size": 8,
                "precision": "float16",
                "description": "Full neural core for high-end systems"
            },
            ExecutionMode.CLOUD_OFFLOAD: {
                "model_type": "cloud",
                "quantization": "full",
                "max_parameters": 175_000_000_000,  # 175B parameters
                "memory_requirement": 1_000_000_000,  # 1GB local for interface
                "batch_size": 16,
                "precision": "float32",
                "description": "Cloud offload for enterprise tasks"
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize Hybrid Execution Manager"""
        try:
            # Detect hardware capabilities
            self.current_profile = await self._detect_hardware_capabilities()
            
            # Test execution modes
            await self._test_execution_modes()
            
            self.is_active = True
            
            self.logger.info(f"✅ Hybrid Manager initialized - Mode: {self.current_profile.execution_mode.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Hybrid Manager initialization failed: {e}")
            return False
    
    async def _detect_hardware_capabilities(self) -> HardwareProfile:
        """Detect current hardware capabilities"""
        try:
            # Get basic system info
            ram = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            # Check GPU availability
            gpu_available = False
            gpu_memory = 0
            gpu_name = "No GPU"
            
            try:
                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory
                    gpu_name = torch.cuda.get_device_name(0)
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    # Apple Silicon GPU
                    gpu_available = True
                    gpu_memory = 8_000_000_000  # Approximate 8GB for Apple Silicon
                    gpu_name = "Apple Silicon GPU"
            except Exception:
                pass
            
            # Determine hardware tier
            tier = self._determine_hardware_tier(ram.total, gpu_available, gpu_memory)
            
            # Determine optimal execution mode
            execution_mode = self._determine_execution_mode(tier, ram.available, gpu_memory)
            
            profile = HardwareProfile(
                tier=tier,
                ram_total=ram.total,
                ram_available=ram.available,
                cpu_count=cpu_count,
                gpu_available=gpu_available,
                gpu_memory=gpu_memory,
                gpu_name=gpu_name,
                execution_mode=execution_mode,
                model_size_limit=self.model_configs[execution_mode]["max_parameters"],
                batch_size_limit=self.model_configs[execution_mode]["batch_size"]
            )
            
            self.logger.info(f"🖥️ Hardware detected: {tier.value}, GPU: {gpu_name}, Mode: {execution_mode.value}")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"❌ Hardware detection failed: {e}")
            # Return minimal profile
            return HardwareProfile(
                tier=HardwareTier.TIER_1_MOBILE,
                ram_total=2_000_000_000,
                ram_available=1_000_000_000,
                cpu_count=2,
                gpu_available=False,
                gpu_memory=0,
                gpu_name="No GPU",
                execution_mode=ExecutionMode.QUANTIZED_LIGHT,
                model_size_limit=1_000_000_000,
                batch_size_limit=1
            )
    
    def _determine_hardware_tier(self, ram_total: int, gpu_available: bool, gpu_memory: int) -> HardwareTier:
        """Determine hardware tier based on specifications"""
        ram_gb = ram_total // (1024**3)
        gpu_gb = gpu_memory // (1024**3) if gpu_memory > 0 else 0
        
        if ram_gb < 4 and not gpu_available:
            return HardwareTier.TIER_1_MOBILE
        elif 4 <= ram_gb < 8 and (not gpu_available or gpu_gb < 2):
            return HardwareTier.TIER_2_BASIC
        elif 8 <= ram_gb < 16 and gpu_available and gpu_gb >= 4:
            return HardwareTier.TIER_3_STANDARD
        elif 16 <= ram_gb < 32 and gpu_available and gpu_gb >= 8:
            return HardwareTier.TIER_4_PERFORMANCE
        else:
            return HardwareTier.TIER_5_ENTERPRISE
    
    def _determine_execution_mode(self, tier: HardwareTier, ram_available: int, gpu_memory: int) -> ExecutionMode:
        """Determine optimal execution mode based on hardware"""
        tier_to_mode = {
            HardwareTier.TIER_1_MOBILE: ExecutionMode.QUANTIZED_LIGHT,
            HardwareTier.TIER_2_BASIC: ExecutionMode.QUANTIZED_MEDIUM,
            HardwareTier.TIER_3_STANDARD: ExecutionMode.QUANTIZED_HEAVY,
            HardwareTier.TIER_4_PERFORMANCE: ExecutionMode.FULL_NEURAL,
            HardwareTier.TIER_5_ENTERPRISE: ExecutionMode.FULL_NEURAL
        }
        
        base_mode = tier_to_mode[tier]
        
        # Adjust based on available memory
        config = self.model_configs[base_mode]
        if ram_available < config["memory_requirement"]:
            # Downgrade to lighter mode
            if base_mode == ExecutionMode.FULL_NEURAL:
                return ExecutionMode.QUANTIZED_HEAVY
            elif base_mode == ExecutionMode.QUANTIZED_HEAVY:
                return ExecutionMode.QUANTIZED_MEDIUM
            elif base_mode == ExecutionMode.QUANTIZED_MEDIUM:
                return ExecutionMode.QUANTIZED_LIGHT
        
        return base_mode
    
    async def _test_execution_modes(self):
        """Test available execution modes"""
        try:
            # Test basic Python execution
            test_result = await self._execute_test_task("basic_python")
            if test_result:
                self.logger.info("✅ Basic Python execution test passed")
            else:
                self.logger.warning("⚠️ Basic Python execution test failed")
            
            # Test memory allocation
            memory_test = await self._test_memory_allocation()
            self.logger.info(f"🧠 Memory test: {memory_test['allocated_mb']}MB allocated")
            
        except Exception as e:
            self.logger.error(f"❌ Execution mode testing failed: {e}")
    
    async def _execute_test_task(self, task_type: str) -> bool:
        """Execute a test task to verify system functionality"""
        try:
            if task_type == "basic_python":
                # Simple computation test
                result = sum(i * i for i in range(1000))
                return result == 332833500  # Expected result
            return False
        except Exception:
            return False
    
    async def _test_memory_allocation(self) -> Dict[str, Any]:
        """Test memory allocation capabilities"""
        try:
            # Try to allocate memory in chunks
            chunk_size = 100 * 1024 * 1024  # 100MB chunks
            allocated = []
            
            for i in range(10):  # Try up to 1GB
                try:
                    chunk = bytearray(chunk_size)
                    allocated.append(chunk)
                except MemoryError:
                    break
            
            allocated_mb = len(allocated) * 100
            return {"allocated_mb": allocated_mb, "chunks": len(allocated)}
            
        except Exception as e:
            return {"error": str(e), "allocated_mb": 0}
    
    async def execute_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """Execute a task with optimal execution mode"""
        try:
            start_time = datetime.now()
            
            # Determine optimal execution mode
            optimal_mode = await self._determine_task_execution_mode(task)
            task.execution_mode = optimal_mode
            
            # Execute task based on mode
            if optimal_mode == ExecutionMode.CLOUD_OFFLOAD:
                result = await self._execute_cloud_task(task)
            else:
                result = await self._execute_local_task(task, optimal_mode)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            self.performance_metrics["total_executions"] += 1
            if result.get("success", False):
                self.performance_metrics["successful_executions"] += 1
            
            # Record execution
            execution_record = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "execution_mode": optimal_mode.value,
                "success": result.get("success", False),
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            }
            self.execution_history.append(execution_record)
            
            # Keep only last 1000 executions
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            return {
                "success": result.get("success", False),
                "execution_mode": optimal_mode.value,
                "execution_time": execution_time,
                "result": result.get("result", {}),
                "error": result.get("error")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Task execution failed: {e}",
                "execution_mode": task.execution_mode.value if task.execution_mode else "unknown"
            }
    
    async def _determine_task_execution_mode(self, task: ExecutionTask) -> ExecutionMode:
        """Determine optimal execution mode for a specific task"""
        # Check if task requires specific mode
        if task.execution_mode:
            return task.execution_mode
        
        # Determine based on task complexity and hardware
        if task.requires_gpu and not self.current_profile.gpu_available:
            # Force cloud offload for GPU tasks without GPU
            return ExecutionMode.CLOUD_OFFLOAD
        
        # Check memory requirements
        if task.estimated_memory > self.current_profile.ram_available:
            return ExecutionMode.CLOUD_OFFLOAD
        
        # Select mode based on complexity
        complexity_modes = {
            "simple": ExecutionMode.QUANTIZED_LIGHT,
            "moderate": ExecutionMode.QUANTIZED_MEDIUM,
            "complex": ExecutionMode.QUANTIZED_HEAVY,
            "expert": ExecutionMode.FULL_NEURAL
        }
        
        base_mode = complexity_modes.get(task.complexity, ExecutionMode.QUANTIZED_MEDIUM)
        
        # Adjust based on current hardware
        if base_mode.value > self.current_profile.execution_mode.value:
            return self.current_profile.execution_mode
        
        return base_mode
    
    async def _execute_local_task(self, task: ExecutionTask, mode: ExecutionMode) -> Dict[str, Any]:
        """Execute task locally with specified mode"""
        try:
            config = self.model_configs[mode]
            
            # Simulate task execution based on mode
            if task.task_type == "inference":
                result = await self._simulate_inference(task, config)
            elif task.task_type == "training":
                result = await self._simulate_training(task, config)
            elif task.task_type == "generation":
                result = await self._simulate_generation(task, config)
            else:
                result = await self._simulate_generic_task(task, config)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_cloud_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """Execute task via cloud offload"""
        try:
            # Simulate cloud execution
            await asyncio.sleep(2.0)  # Simulate network latency
            
            return {
                "success": True,
                "result": {
                    "cloud_execution": True,
                    "model_size": "175B parameters",
                    "response": f"Cloud processed {task.task_type} task"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _simulate_inference(self, task: ExecutionTask, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate inference task"""
        # Simulate processing time based on model size
        processing_time = config["max_parameters"] / 1_000_000_000 * 0.1  # 0.1s per 1B parameters
        await asyncio.sleep(processing_time)
        
        return {
            "inference_result": f"Processed with {config['quantization']} quantization",
            "model_size": config["max_parameters"],
            "batch_size": config["batch_size"]
        }
    
    async def _simulate_training(self, task: ExecutionTask, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate training task"""
        # Training takes longer
        processing_time = config["max_parameters"] / 1_000_000_000 * 0.5  # 0.5s per 1B parameters
        await asyncio.sleep(processing_time)
        
        return {
            "training_result": f"Training completed with {config['precision']} precision",
            "epochs": 10,
            "final_loss": 0.05
        }
    
    async def _simulate_generation(self, task: ExecutionTask, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate text generation task"""
        # Generation is relatively fast
        processing_time = config["max_parameters"] / 1_000_000_000 * 0.05  # 0.05s per 1B parameters
        await asyncio.sleep(processing_time)
        
        return {
            "generated_text": f"Generated text using {config['model_type']} model",
            "tokens_generated": 100,
            "time_per_token": processing_time / 100
        }
    
    async def _simulate_generic_task(self, task: ExecutionTask, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate generic task"""
        await asyncio.sleep(0.1)
        
        return {
            "task_completed": True,
            "execution_mode": config["description"],
            "parameters": config["max_parameters"]
        }
    
    async def get_hardware_profile(self) -> Dict[str, Any]:
        """Get current hardware profile"""
        if not self.current_profile:
            return {"error": "Hardware profile not initialized"}
        
        return {
            "tier": self.current_profile.tier.value,
            "ram_total_gb": self.current_profile.ram_total // (1024**3),
            "ram_available_gb": self.current_profile.ram_available // (1024**3),
            "cpu_count": self.current_profile.cpu_count,
            "gpu_available": self.current_profile.gpu_available,
            "gpu_memory_gb": self.current_profile.gpu_memory // (1024**3) if self.current_profile.gpu_memory > 0 else 0,
            "gpu_name": self.current_profile.gpu_name,
            "execution_mode": self.current_profile.execution_mode.value,
            "model_size_limit_b": self.current_profile.model_size_limit,
            "batch_size_limit": self.current_profile.batch_size_limit,
            "timestamp": self.current_profile.timestamp.isoformat()
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        total = self.performance_metrics["total_executions"]
        successful = self.performance_metrics["successful_executions"]
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Calculate average execution time from history
        if self.execution_history:
            avg_time = sum(e["execution_time"] for e in self.execution_history) / len(self.execution_history)
        else:
            avg_time = 0.0
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate_percent": success_rate,
            "average_execution_time": avg_time,
            "execution_history_count": len(self.execution_history),
            "current_execution_mode": self.current_profile.execution_mode.value if self.current_profile else "unknown"
        }
    
    async def switch_execution_mode(self, new_mode: ExecutionMode) -> Dict[str, Any]:
        """Manually switch execution mode"""
        try:
            if not self.current_profile:
                return {"error": "Hardware profile not initialized"}
            
            old_mode = self.current_profile.execution_mode
            self.current_profile.execution_mode = new_mode
            
            # Update model size and batch limits
            config = self.model_configs[new_mode]
            self.current_profile.model_size_limit = config["max_parameters"]
            self.current_profile.batch_size_limit = config["batch_size"]
            
            self.logger.info(f"🔄 Execution mode switched: {old_mode.value} -> {new_mode.value}")
            
            return {
                "success": True,
                "old_mode": old_mode.value,
                "new_mode": new_mode.value,
                "model_size_limit": config["max_parameters"],
                "batch_size_limit": config["batch_size"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def optimize_for_task(self, task_type: str, complexity: str) -> Dict[str, Any]:
        """Get optimal configuration for a specific task type"""
        try:
            # Create test task
            test_task = ExecutionTask(
                task_id="optimization_test",
                task_type=task_type,
                complexity=complexity,
                priority="medium",
                estimated_memory=0,
                requires_gpu=task_type in ["training", "inference"]
            )
            
            # Determine optimal mode
            optimal_mode = await self._determine_task_execution_mode(test_task)
            config = self.model_configs[optimal_mode]
            
            return {
                "optimal_mode": optimal_mode.value,
                "configuration": config,
                "estimated_performance": self._estimate_performance(task_type, complexity, optimal_mode)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _estimate_performance(self, task_type: str, complexity: str, mode: ExecutionMode) -> Dict[str, Any]:
        """Estimate performance for task configuration"""
        config = self.model_configs[mode]
        
        # Base performance estimates
        performance = {
            "estimated_speed": "fast",
            "estimated_accuracy": "high",
            "memory_efficiency": "good"
        }
        
        # Adjust based on mode
        if mode == ExecutionMode.QUANTIZED_LIGHT:
            performance.update({
                "estimated_speed": "very_fast",
                "estimated_accuracy": "medium",
                "memory_efficiency": "excellent"
            })
        elif mode == ExecutionMode.FULL_NEURAL:
            performance.update({
                "estimated_speed": "medium",
                "estimated_accuracy": "very_high",
                "memory_efficiency": "fair"
            })
        elif mode == ExecutionMode.CLOUD_OFFLOAD:
            performance.update({
                "estimated_speed": "fast",
                "estimated_accuracy": "very_high",
                "memory_efficiency": "excellent"
            })
        
        return performance
    
    async def shutdown(self):
        """Shutdown Hybrid Execution Manager"""
        self.is_active = False
        self.logger.info("🛑 Hybrid Execution Manager Shutdown")

# Global instance
_hybrid_manager_instance = None

def get_hybrid_manager() -> HybridExecutionManager:
    """Get singleton Hybrid Execution Manager instance"""
    global _hybrid_manager_instance
    if _hybrid_manager_instance is None:
        _hybrid_manager_instance = HybridExecutionManager()
    return _hybrid_manager_instance
