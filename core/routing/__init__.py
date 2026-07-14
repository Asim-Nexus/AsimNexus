"""Routing package for intent classification and hybrid routing."""
from .hybrid_router import (
    HybridRouter,
    KeywordClassifier,
    EmbeddingClassifier,
    IntentType,
    RouteDecision,
    ClassificationResult,
)


# Re-export from root-level module: context_router.py
from core.context_router import (
    ContextRouter,
    MODES,
    TOOL_PERMISSIONS,
    get_context_router,
    initialize_context_router,
    reset_context_router,
)



# Re-export from root-level module: smart_llm_router.py
from core.smart_llm_router import (
    ModelConfig,
    SmartLLMRouter,
    TaskPriority,
    TaskType,
    get_smart_router,
)


__all__ = [
    "HybridRouter",
    "KeywordClassifier",
    "EmbeddingClassifier",
    "IntentType",
    "RouteDecision",
    "ClassificationResult",
]
