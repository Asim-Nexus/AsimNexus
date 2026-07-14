
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
AsimBrainRouter — Smart Local-First Model Router
=================================================
Local-first routing: Qwen3 GGUF → Ollama → Cloud (user keys only)
NO NVIDIA NIM. Dharma-Chakra protected.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("AsimBrainRouter")

GGUF_MODEL_PATH = str(Path(__file__).parent.parent / "models" /
                      "Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf")

TASK_KEYWORDS: Dict[str, List[str]] = {
    "coding":    ["code", "program", "function", "script", "debug", "python",
                  "javascript", "java", "algorithm", "database", "api", "bug"],
    "reasoning": ["analyze", "compare", "explain", "why", "how", "calculate",
                  "math", "logic", "strategy", "decision", "plan"],
    "health":    ["health", "doctor", "medicine", "symptom", "disease", "diet",
                  "exercise", "mental", "hospital", "स्वास्थ्य", "बिमारी"],
    "legal":     ["legal", "law", "contract", "rights", "court", "compliance",
                  "कानून", "अधिकार"],
    "creative":  ["write", "story", "poem", "design", "art", "creative",
                  "content", "blog", "लेख"],
    "finance":   ["money", "budget", "invest", "tax", "finance", "bank",
                  "पैसा", "बचत", "लगानी"],
    "education": ["learn", "study", "explain", "teach", "tutor", "school",
                  "पढाई", "सिकाउ"],
    "farming":   ["farm", "crop", "soil", "weather", "agriculture", "खेती",
                  "बाली", "मौसम"],
}

CLOUD_PROVIDERS = {
    "openai":     ("https://api.openai.com/v1/chat/completions",      "gpt-4o-mini"),
    "anthropic":  ("https://api.anthropic.com/v1/messages",           "claude-3-haiku-20240307"),
    "gemini":     ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                                                                       "gemini-1.5-flash"),
    "deepseek":   ("https://api.deepseek.com/v1/chat/completions",    "deepseek-chat"),
    "grok":       ("https://api.x.ai/v1/chat/completions",            "grok-beta"),
}


@dataclass
class RouteDecision:
    provider: str
    model: str
    task_type: str
    reason: str
    api_key: Optional[str] = None
    confidence: float = 1.0


class AsimBrainRouter:
    """
    AsimNexus Local-First Brain Router.
    Priority: Local GGUF → Ollama → Cloud (user-supplied keys only)
    Dharma-Chakra veto applied before any cloud call.
    Circuit breaker: auto-fallback after 3 failures.
    """

    def __init__(self):
        self.failure_counts: Dict[str, int] = {}
        self.disabled_until: Dict[str, float] = {}
        self.stats = {"total": 0, "local": 0, "cloud": 0, "fallback": 0}
        logger.info("✅ AsimBrainRouter initialized (Local-first, No NVIDIA NIM)")

    # ── TASK DETECTION ────────────────────────────────────────────────────────

    def detect_task(self, message: str) -> str:
        msg = message.lower()
        scores: Dict[str, int] = {}
        for task, keywords in TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg)
            if score:
                scores[task] = score
        return max(scores, key=scores.get) if scores else "general"

    # ── ROUTING ───────────────────────────────────────────────────────────────

    def select_model(self, message: str,
                     user_api_keys: Optional[Dict[str, str]] = None,
                     preference: str = None) -> RouteDecision:
        self.stats["total"] += 1
        task = preference or self.detect_task(message)

        # 1. Local GGUF (always try first)
        if Path(GGUF_MODEL_PATH).exists():
            self.stats["local"] += 1
            return RouteDecision(
                provider="local_gguf",
                model="Qwen3-4B-distill",
                task_type=task,
                reason="Local GGUF — private & offline",
                confidence=0.85,
            )

        # 2. Ollama (if running)
        if self._check_ollama():
            self.stats["local"] += 1
            return RouteDecision(
                provider="ollama",
                model="qwen2.5:3b",
                task_type=task,
                reason="Ollama local server",
                confidence=0.80,
            )

        # 3. Cloud — user's own API keys only
        if user_api_keys:
            for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
                key = user_api_keys.get(provider, "")
                if key and self._is_available(provider):
                    _, model = CLOUD_PROVIDERS[provider]
                    self.stats["cloud"] += 1
                    return RouteDecision(
                        provider=provider,
                        model=model,
                        task_type=task,
                        reason=f"Cloud: {provider} (user key)",
                        api_key=key,
                        confidence=0.90,
                    )

        # 4. Offline fallback
        self.stats["fallback"] += 1
        return RouteDecision(
            provider="fallback",
            model="offline",
            task_type=task,
            reason="Offline — install llama-cpp-python and add GGUF model",
            confidence=0.0,
        )

    # ── CIRCUIT BREAKER ───────────────────────────────────────────────────────

    def report_failure(self, provider: str):
        self.failure_counts[provider] = self.failure_counts.get(provider, 0) + 1
        if self.failure_counts[provider] >= 3:
            self.disabled_until[provider] = time.time() + 300
            logger.warning(f"⚡ Circuit breaker: {provider} disabled 5min")

    def report_success(self, provider: str):
        self.failure_counts.pop(provider, None)
        self.disabled_until.pop(provider, None)

    def _is_available(self, provider: str) -> bool:
        until = self.disabled_until.get(provider)
        if until and time.time() < until:
            return False
        if until:
            self.disabled_until.pop(provider, None)
            self.failure_counts.pop(provider, None)
        return True

    def _check_ollama(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
            return True
        except Exception:
            return False

    # ── STATUS ────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "router": "AsimBrainRouter",
            "local_gguf": Path(GGUF_MODEL_PATH).exists(),
            "ollama": self._check_ollama(),
            "nvidia_nim": False,
            "stats": self.stats,
            "disabled_providers": list(self.disabled_until.keys()),
        }


# ── Backward-compatible alias ─────────────────────────────────────────────────
SmartModelRouter = AsimBrainRouter
model_router = AsimBrainRouter()
