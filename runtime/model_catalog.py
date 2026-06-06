
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

class ModelType(Enum):
    REFLEX = "reflex"      # Small (1B-3B) for fast chat/intent
    REASONING = "reasoning" # Medium (4B-8B) for planning/complex
    EXPERT = "expert"      # Large/Cloud (70B+) for coding/specialized

@dataclass
class ModelInfo:
    name: str
    type: ModelType
    provider: str
    endpoint: str
    context_window: int
    capabilities: List[str]

class ModelCatalog:
    """
    Model Catalog for ASIM Nexus.
    Defines available LLMs, their roles, and execution endpoints.
    """
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {
            "gemma-4-7b": ModelInfo(
                name="Google Gemma-4-7B-Instruct",
                type=ModelType.REASONING,
                provider="huggingface",
                endpoint="http://localhost:8000/v1",
                context_window=8192,
                capabilities=["reasoning", "planning", "general", "coding", "multilingual"]
            ),
            "qwen-2.5-0.5b": ModelInfo(
                name="Qwen-2.5-0.5B",
                type=ModelType.REFLEX,
                provider="llama_cpp",
                endpoint="http://127.0.0.1:8000/v1",
                context_window=2048,
                capabilities=["intent_detection", "fast_chat"]
            ),
            "gpt-4o": ModelInfo(
                name="GPT-4o",
                type=ModelType.EXPERT,
                provider="openai",
                endpoint="https://api.openai.com/v1",
                context_window=128000,
                capabilities=["coding", "advanced_logic"]
            )
        }

    def get_model(self, name: str) -> Optional[ModelInfo]:
        return self.models.get(name)

    def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        return [m for m in self.models.values() if m.type == model_type]

# Global Model Catalog instance
model_catalog = ModelCatalog()
