"""
AsimNexus Gateway Package
=========================
Consolidated gateway and connector modules.

This package re-exports all modules from the legacy `connectors/` package
for backward compatibility. New code should import from `core.gateway` directly.
"""

import logging

logger = logging.getLogger(__name__)

# --- Direct re-exports from gateway modules ---
from .base_llm_connector import BaseLLMConnector, ModelProvider, CompletionRequest, CompletionResponse, ModelInfo
from .unified_llm_gateway import UnifiedLLMGateway, LLMProvider, ProviderConfig, UnifiedCompletionRequest, UnifiedCompletionResponse
from .unified_gateway import UnifiedGateway
from .local_llm_connector import LocalLLM, LocalLLMConfig
from .openai_connector import OpenAIConnector, OpenAIModel, Message
from .smart_model_router import AsimBrainRouter, RouteDecision
from .multiversal_bridge import MultiversalBridge, UniverseType, BridgeStatus, Universe, BridgeConnection
from .nexus_secure_connector import NexusSecureConnector, ModuleType, ConnectorError
from .nepal_banking import NepalBanking, BankType, PaymentGateway, TransactionStatus, BankAccount, Transaction
from .google_ecosystem import GoogleEcosystem, GoogleService, ServiceStatus, GoogleResource
from .unified_messaging_connector import UnifiedMessagingConnector, UniversalMessage

# --- Lazy imports for optional integration_platforms ---
def __getattr__(name):
    if name in ("ComposioConnector", "MuleSoftConnector", "DremioConnector"):
        import importlib
        mod = importlib.import_module("connectors.integration_platforms")
        return getattr(mod, name)
    raise AttributeError(f"module 'core.gateway' has no attribute {name!r}")


# Re-export from root-level module: rate_limiter_middleware.py
from core.rate_limiter_middleware import (
    DEFAULT_LIMIT,
    DEFAULT_WINDOW,
    RateLimiterMiddleware,
)



# Re-export from root-level module: universal_api_gateway.py
from core.universal_api_gateway import (
    APIGateway,
    APIRoute,
    GatewayConfig,
)


__all__ = [
    "BaseLLMConnector", "ModelProvider", "CompletionRequest", "CompletionResponse", "ModelInfo",
    "UnifiedLLMGateway", "LLMProvider", "ProviderConfig", "UnifiedCompletionRequest", "UnifiedCompletionResponse",
    "UnifiedGateway",
    "LocalLLM", "LocalLLMConfig",
    "OpenAIConnector", "OpenAIModel", "Message",
    "AsimBrainRouter", "RouteDecision",
    "MultiversalBridge", "UniverseType", "BridgeStatus", "Universe", "BridgeConnection",
    "NexusSecureConnector", "ModuleType", "ConnectorError",
    "NepalBanking", "BankType", "PaymentGateway", "TransactionStatus", "BankAccount", "Transaction",
    "GoogleEcosystem", "GoogleService", "ServiceStatus", "GoogleResource",
    "UnifiedMessagingConnector", "UniversalMessage",
    "ComposioConnector", "MuleSoftConnector", "DremioConnector",
]
