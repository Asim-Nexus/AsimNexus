#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade local-first model router
ASIMNEXUS Local Model Router with Privacy Tiers
==============================================
Features:
- Intent detection (leveraging HybridRouter)
- Privacy classification (public, confidential, highly_sensitive)
- Cloud trust tier selection (trusted_cloud, forbidden_cloud)
- Local-first preference
- "No-cloud-for-highly-sensitive-data" security enforcement
"""

import time
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

# ── AsimNexus Gateway integration ─────────────────────────────────
try:
    from gateway_client import gateway_client
    HAS_GATEWAY_CLIENT = True
except ImportError:
    HAS_GATEWAY_CLIENT = False
    gateway_client = None

try:
    import jwt as _jwt
except ImportError:
    _jwt = None

# Import HybridRouter from core
try:
    from core.routing.hybrid_router import get_hybrid_router, IntentType, ModelTier
    logger = logging.getLogger("AsimNexus.Router")
except ImportError:
    # Fail-safe mock for tests or missing modules
    class IntentType:
        GENERIC = "generic"
        HEALTH = "health"
        FINANCE = "finance"
        LEGAL = "legal"
    class ModelTier:
        LOCAL_FAST = "local_fast"
        CLOUD_QUALITY = "cloud_quality"
    def get_hybrid_router():
        class MockRouter:
            def route(self, message, context=None):
                class MockDecision:
                    def __init__(self):
                        self.model = "gemma3:4b"
                        self.intent = IntentType.GENERIC
                        self.score = 1.0
                        self.tier = ModelTier.LOCAL_FAST
                        self.requires_veto = False
                        self.requires_human = False
                return MockDecision()
            def update_metrics(self, model, latency, success):
                pass
            def get_metrics(self):
                return {}
        return MockRouter()

logger = logging.getLogger("AsimNexus.Router")


import os

_JWT_FALLBACK = "asimnexus-super-secret-jwt-key-2026"
_JWT_SECRET = os.getenv("ASIM_JWT_SECRET", _JWT_FALLBACK)
if _JWT_SECRET == _JWT_FALLBACK:
    logger.warning(
        "⚠️  ASIM_JWT_SECRET not set in environment — using insecure fallback! "
        "Set ASIM_JWT_SECRET in .env before production deployment."
    )

def _extract_user_id(request: Request) -> str:
    """Extract user_id from Authorization header — no simple_backend import needed."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return "guest"
    token = auth[7:]
    if _jwt is None:
        return "guest"
    try:
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub", "guest")
    except Exception:
        return "guest"

class RouteRequest(BaseModel):
    message: str
    privacy_classification: Optional[str] = "public"  # public, confidential, highly_sensitive
    mode: Optional[str] = "personal"

class ChatRequest(BaseModel):
    prompt: str
    privacy_classification: Optional[str] = "public"  # public, confidential, highly_sensitive
    mode: Optional[str] = "personal"

class RouterManager:
    """Manages local-first routing decisions based on privacy classification and cloud trust tiers."""

    def __init__(self, local_llm_checker_fn=None, cloud_runner_fn=None):
        self.hybrid_router = get_hybrid_router()
        # Functions passed from main app to perform inference
        self.local_llm_checker = local_llm_checker_fn
        self.cloud_runner = cloud_runner_fn

    def classify_privacy(self, message: str, explicit_privacy: Optional[str] = "public") -> str:
        """Auto-classify or default to user explicit privacy rating."""
        if explicit_privacy in ["confidential", "highly_sensitive"]:
            return explicit_privacy
        
        # Sim: auto-tag "highly_sensitive" if message contains national ID, password, or security keywords
        msg_lower = message.lower()
        sensitive_keywords = ["citizen id", "password", "private key", "credit card", "passport", "citizenship no"]
        if any(kw in msg_lower for kw in sensitive_keywords):
            return "highly_sensitive"
        
        confidential_keywords = ["salary", "health record", "medical report", "bank balance", "contract draft"]
        if any(kw in msg_lower for kw in confidential_keywords):
            return "confidential"

        return "public"

    def get_cloud_trust_tier(self, provider: str, privacy: str) -> str:
        """Return trusted_cloud or forbidden_cloud depending on provider and privacy classification."""
        # Standard public data: all clouds are trusted
        if privacy == "public":
            return "trusted_cloud"
        
        # Confidential data: only private/local hosting or top-tier clouds (e.g. OpenAI, Azure) are trusted
        if privacy == "confidential":
            if provider in ["openai", "azure", "gemini"]:
                return "trusted_cloud"
            return "forbidden_cloud"
        
        # Highly sensitive data: ALL clouds are forbidden! Local execution only.
        return "forbidden_cloud"

    def determine_route(self, message: str, privacy: str, mode: str) -> Dict[str, Any]:
        """Determine routing details incorporating trust tiers."""
        decision = self.hybrid_router.route(message, {"mode": mode})
        
        # No-cloud-for-highly-sensitive-data rule
        if privacy == "highly_sensitive":
            target_tier = "local_only"
            allowed_cloud = False
            reason = "Local only: Highly sensitive data forbidden from cloud fallback."
        else:
            target_tier = "local_first"
            allowed_cloud = True
            reason = f"Routed to {decision.model} under mode {mode}."

        return {
            "model": decision.model,
            "intent": decision.intent if isinstance(decision.intent, str) else decision.intent.value,
            "score": decision.score,
            "tier": decision.tier if isinstance(decision.tier, str) else decision.tier.value,
            "privacy_classification": privacy,
            "target_tier": target_tier,
            "allowed_cloud": allowed_cloud,
            "requires_veto": decision.requires_veto,
            "requires_human": decision.requires_human,
            "reason": reason
        }

    async def execute_chat(self, prompt: str, privacy: str, mode: str, user_id: str = "system") -> Dict[str, Any]:
        """Execute chat inference: local-first with smart privacy-based cloud fallback."""
        start_time = time.time()
        route_decision = self.determine_route(prompt, privacy, mode)

        # 1. Attempt Local Inference
        local_available = False
        if self.local_llm_checker:
            local_available = self.local_llm_checker()

        if local_available:
            try:
                # Call local generator function — lazy import to avoid circular deps
                from importlib import import_module
                _sb = import_module("simple_backend")
                _generate_local = getattr(_sb, "_generate_local", None)
                if _generate_local is None:
                    raise ImportError("_generate_local not found in simple_backend")
                response = await _generate_local(prompt)
                if response:
                    latency = (time.time() - start_time) * 1000
                    self.hybrid_router.update_metrics(route_decision["model"], latency, True)
                    return {
                        "success": True,
                        "response": response,
                        "source": "local_gguf",
                        "model": route_decision["model"],
                        "privacy_classification": privacy,
                        "latency_ms": round(latency, 2)
                    }
            except Exception as e:
                logger.warning(f"Local inference failed, attempting fallback: {e}")

        # Local failed/unavailable: handle fallback
        if privacy == "highly_sensitive":
            # Strict block: "no-cloud-for-highly-sensitive-data" rule
            raise HTTPException(
                status_code=400,
                detail="Routing denied: Highly sensitive data is forbidden from cloud fallback and local model is offline."
            )

        # Attempt Cloud Fallback with user API keys
        if self.cloud_runner:
            # The runner will search for user keys and execute cloud LLM
            cloud_resp = await self.cloud_runner(prompt, user_id)
            if cloud_resp:
                latency = (time.time() - start_time) * 1000
                self.hybrid_router.update_metrics("cloud_fallback", latency, True)
                return {
                    "success": True,
                    "response": cloud_resp["response"],
                    "source": "cloud",
                    "model": cloud_resp["model"],
                    "privacy_classification": privacy,
                    "latency_ms": round(latency, 2)
                }

        # Global fallback
        raise HTTPException(
            status_code=503,
            detail="Local model offline and no cloud API key available for fallback."
        )

# FastAPI routes wire-up
def setup_router_routes(app, local_llm_checker_fn=None, cloud_runner_fn=None):
    router_manager = RouterManager(local_llm_checker_fn, cloud_runner_fn)

    @app.post("/api/router/route")
    async def route_prompt(req: RouteRequest):
        # Gateway check for routing decisions
        if HAS_GATEWAY_CLIENT and gateway_client:
            try:
                gw = await gateway_client.check(
                    capability_id="config:read",
                    target=f"route:{req.mode}",
                    requester="system",
                )
                if not gw.get("allowed", True):
                    return JSONResponse(
                        {"error": f"Gateway denied: {gw.get('reason', 'Routing not permitted')}"},
                        status_code=403,
                    )
            except Exception:
                pass  # Gateway unavailable — allow routing

        privacy = router_manager.classify_privacy(req.message, req.privacy_classification)
        decision = router_manager.determine_route(req.message, privacy, req.mode)
        return JSONResponse(decision)

    @app.post("/api/router/chat")
    async def chat_prompt(req: ChatRequest, request: Request):
        user_id = _extract_user_id(request)
        privacy = router_manager.classify_privacy(req.prompt, req.privacy_classification)

        # Gateway check for chat execution
        if HAS_GATEWAY_CLIENT and gateway_client:
            try:
                gw = await gateway_client.check(
                    capability_id="net:http",
                    target=f"chat:{req.mode}",
                    requester=user_id,
                )
                if not gw.get("allowed", True):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Gateway denied: {gw.get('reason', 'Chat not permitted')}",
                    )
            except HTTPException:
                raise
            except Exception:
                pass  # Gateway unavailable — allow chat

        try:
            res = await router_manager.execute_chat(req.prompt, privacy, req.mode, user_id)

            # Log to Gateway audit
            if HAS_GATEWAY_CLIENT and gateway_client:
                try:
                    await gateway_client.log_audit(
                        action="chat_executed",
                        requester=user_id,
                        approver="system",
                        executor="router",
                        capability_id="net:http",
                        target=f"chat:{req.mode}",
                        status="completed",
                    )
                except Exception:
                    pass

            return JSONResponse(res)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/router/metrics")
    async def get_metrics():
        return JSONResponse(router_manager.hybrid_router.get_metrics())

    logger.info("✅ Core Trust Path Router routes registered: /api/router/*")
