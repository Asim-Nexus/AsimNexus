#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade local model router
ASIMNEXUS Local Model Router
============================
Device capability-based model selection and routing.
Ensures optimal model selection based on available hardware and task requirements.
"""

import logging
import psutil
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("AsimNexus.ModelRouter")


class ModelTier(Enum):
    """Model capability tiers."""
    TINY = "tiny"       # < 1B params, edge devices
    SMALL = "small"     # 1-3B params, mobile
    MEDIUM = "medium"   # 3-7B params, laptop
    LARGE = "large"     # 7-13B params, desktop
    XLARGE = "xlarge"   # 13-70B params, workstation


class TaskType(Enum):
    """Task types for model selection."""
    CHAT = "chat"
    CODE = "code"
    MATH = "math"
    REASONING = "reasoning"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"


@dataclass
class DeviceCapability:
    """Device hardware capabilities."""
    cpu_cores: int
    cpu_freq_ghz: float
    total_ram_gb: float
    available_ram_gb: float
    gpu_available: bool
    gpu_memory_gb: Optional[float]
    gpu_name: Optional[str]
    
    def can_run_model_tier(self, tier: ModelTier) -> bool:
        """Check if device can run a model tier."""
        # Minimum requirements per tier
        tier_requirements = {
            ModelTier.TINY: {"ram": 2.0, "gpu": False},
            ModelTier.SMALL: {"ram": 4.0, "gpu": False},
            ModelTier.MEDIUM: {"ram": 8.0, "gpu": False},
            ModelTier.LARGE: {"ram": 16.0, "gpu": True},
            ModelTier.XLARGE: {"ram": 32.0, "gpu": True},
        }
        
        req = tier_requirements[tier]
        
        # RAM check
        if self.available_ram_gb < req["ram"]:
            return False
        
        # GPU check
        if req["gpu"] and not self.gpu_available:
            return False
        
        return True


@dataclass
class ModelSpec:
    """Model specification."""
    name: str
    tier: ModelTier
    params_b: float
    supported_tasks: List[TaskType]
    file_path: str
    context_length: int
    quantization: str  # e.g., "Q8_0", "Q4_K_M"


class ModelRouter:
    """
    Local model router with device capability detection.
    Selects optimal model based on hardware and task requirements.
    """
    
    def __init__(self):
        self.device_capability = self._detect_device_capability()
        self.available_models: Dict[str, ModelSpec] = {}
        self.active_model: Optional[str] = None
        
        logger.info(f"🔧 Model Router initialized - Device: {self.device_capability.cpu_cores} cores, "
                   f"{self.device_capability.total_ram_gb:.1f}GB RAM, "
                   f"GPU: {self.device_capability.gpu_name if self.device_capability.gpu_available else 'None'}")
    
    def _detect_device_capability(self) -> DeviceCapability:
        """Detect current device hardware capabilities."""
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 4
        cpu_freq = psutil.cpu_freq().max / 1000 if psutil.cpu_freq() else 2.0  # GHz
        
        mem = psutil.virtual_memory()
        total_ram_gb = mem.total / (1024**3)
        available_ram_gb = mem.available / (1024**3)
        
        # GPU detection (simplified - in production use proper CUDA/ROCm detection)
        gpu_available = False
        gpu_memory_gb = None
        gpu_name = None
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_available = True
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                gpu_name = torch.cuda.get_device_name(0)
        except ImportError:
            pass
        
        return DeviceCapability(
            cpu_cores=cpu_cores,
            cpu_freq_ghz=cpu_freq,
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            gpu_available=gpu_available,
            gpu_memory_gb=gpu_memory_gb,
            gpu_name=gpu_name
        )
    
    def register_model(self, spec: ModelSpec) -> bool:
        """Register a model for routing."""
        if not self.device_capability.can_run_model_tier(spec.tier):
            logger.warning(f"⚠️  Device cannot run {spec.name} (tier: {spec.tier})")
            return False
        
        self.available_models[spec.name] = spec
        logger.info(f"✅ Registered model: {spec.name} (tier: {spec.tier}, {spec.params_b}B params)")
        return True
    
    def select_model(self, task: TaskType, force_tier: Optional[ModelTier] = None) -> Optional[str]:
        """
        Select optimal model for task.
        If force_tier is specified, selects best model of that tier.
        """
        candidates = []
        
        for name, spec in self.available_models.items():
            if task not in spec.supported_tasks:
                continue
            
            if force_tier and spec.tier != force_tier:
                continue
            
            candidates.append(spec)
        
        if not candidates:
            logger.warning(f"⚠️  No model available for task: {task}")
            return None
        
        # Select highest tier that device can handle
        candidates.sort(key=lambda x: x.params_b, reverse=True)
        
        selected = candidates[0]
        logger.info(f"🎯 Selected model: {selected.name} for task: {task}")
        return selected.name
    
    def get_model_spec(self, name: str) -> Optional[ModelSpec]:
        """Get model specification by name."""
        return self.available_models.get(name)
    
    def list_available_models(self) -> List[ModelSpec]:
        """List all registered models."""
        return list(self.available_models.values())
    
    def get_device_capability(self) -> DeviceCapability:
        """Get current device capability."""
        return self.device_capability
    
    def get_recommended_tier(self) -> ModelTier:
        """Get recommended model tier based on device capability."""
        if self.device_capability.gpu_available and self.device_capability.gpu_memory_gb >= 16:
            return ModelTier.XLARGE
        elif self.device_capability.gpu_available and self.device_capability.gpu_memory_gb >= 8:
            return ModelTier.LARGE
        elif self.device_capability.available_ram_gb >= 16:
            return ModelTier.MEDIUM
        elif self.device_capability.available_ram_gb >= 8:
            return ModelTier.SMALL
        else:
            return ModelTier.TINY


# Global model router instance
_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get or create global model router instance."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router


def reset_model_router():
    """Reset global model router instance (for testing)."""
    global _model_router
    _model_router = None
