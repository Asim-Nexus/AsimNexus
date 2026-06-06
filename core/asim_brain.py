"""
STATUS: REAL — Local GGUF + cloud fallback with Dharma inline check

AsimBrain — Unified Intelligence Layer
=======================================
Single entry point for ALL AI operations in AsimNexus.
Wires: Router → Clone → Dharma → Memory → Response

Priority chain:
  1. Local GGUF (Qwen3-4B) — offline, private
  2. Ollama local server
  3. Cloud API (user's own keys: OpenAI/Anthropic/Gemini/DeepSeek/Grok)
  4. Graceful offline fallback

Every request passes through Dharma-Chakra VETO before cloud calls.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("AsimBrain")

# ── GGUF MODEL PATH ───────────────────────────────────────────────────────────
GGUF_PATH = Path(__file__).parent.parent / "models" / \
            "Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf"

# ── CLONE → SYSTEM PROMPT MAP ─────────────────────────────────────────────────
CLONE_PROMPTS: Dict[str, str] = {
    "coding":    "You are the Tech Architect of AsimNexus. Write clean, secure, scalable code. "
                 "Explain technical concepts clearly. Answer in the user's language.",
    "health":    "You are the Health Sage of AsimNexus. Provide health guidance with care. "
                 "Always recommend consulting a real doctor for serious issues.",
    "finance":   "You are the Financial Oracle of AsimNexus. Give practical, ethical financial "
                 "advice. Never recommend illegal or harmful financial actions.",
    "legal":     "You are the Legal Guardian of AsimNexus. Explain legal concepts clearly. "
                 "Always note that professional legal counsel is recommended.",
    "creative":  "You are the Creative Muse of AsimNexus. Help with writing, art, design, "
                 "and all creative tasks with imagination and originality.",
    "reasoning": "You are the Strategic Planner of AsimNexus. Analyze situations deeply, "
                 "provide structured reasoning and balanced perspectives.",
    "education": "You are the Education Mentor of AsimNexus. Teach clearly and patiently. "
                 "Adapt your explanation to the user's level.",
    "farming":   "You are the Farm Guide of AsimNexus. Provide practical agricultural advice "
                 "based on local conditions, seasons, and sustainable practices.",
    "general":   "You are AsimNexus, a helpful AI assistant for all of humanity. "
                 "Answer clearly and helpfully in the same language the user uses.",
}

# ── DHARMA VETO RULES (immutable inline fallback) ────────────────────────────
DHARMA_BLOCKED_PATTERNS = [
    "make bomb", "build weapon", "kill people", "hack password", "steal",
    "child abuse", "violence against", "terrorism", "genocide",
    "बम बनाउ", "हत्या गर", "चोरी गर",
]


@dataclass
class BrainResponse:
    response: str
    source: str          # "local_gguf" | "ollama" | "openai" | ... | "fallback"
    model: str
    clone: str
    task_type: str
    intent: str
    dharma_checked: bool = True
    command: Optional[Dict] = None


class AsimBrain:
    """
    Unified Intelligence Brain for AsimNexus.
    One instance per deployment. Thread-safe via asyncio.
    """

    def __init__(self):
        self._llm = None          # llama_cpp.Llama instance
        self._llm_loaded = False
        self._load_attempted = False
        logger.info("AsimBrain initialized")

    # ── LOCAL LLM SETUP ───────────────────────────────────────────────────────

    def load_local_llm(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        try:
            from llama_cpp import Llama
            if GGUF_PATH.exists():
                self._llm = Llama(
                    model_path=str(GGUF_PATH),
                    n_ctx=4096,
                    n_threads=min(4, os.cpu_count() or 4),
                    n_gpu_layers=20,
                    verbose=False,
                )
                self._llm_loaded = True
                logger.info(f"✅ Qwen3 GGUF loaded: {GGUF_PATH.name}")
            else:
                logger.warning(f"⚠️ GGUF not found: {GGUF_PATH}")
        except ImportError:
            logger.warning("⚠️ llama-cpp-python not installed")
        except Exception as e:
            logger.warning(f"⚠️ GGUF load failed: {e}")

    # ── DHARMA CHECK ──────────────────────────────────────────────────────────

    def dharma_check(self, message: str) -> Optional[str]:
        msg_lower = message.lower()
        for pattern in DHARMA_BLOCKED_PATTERNS:
            if pattern in msg_lower:
                return f"Dharma-Chakra VETO: This request violates constitutional ethics ({pattern})."

        # Try real veto module
        try:
            from core.dharma_chakra.safety_veto import SafetyVeto
            veto = SafetyVeto()
            result = veto.check(message)
            if result and not result.get("allowed", True):
                return f"Dharma-Chakra VETO: {result.get('reason', 'Ethical constraint')}"
        except Exception:
            pass
        return None

    # ── INTENT / TASK DETECTION ───────────────────────────────────────────────

    def detect_intent(self, message: str) -> str:
        try:
            from connectors.smart_model_router import model_router
            return model_router.detect_task(message)
        except Exception:
            pass
        msg = message.lower()
        for task, keywords in {
            "coding": ["code", "program", "python", "debug"],
            "health": ["health", "doctor", "symptom", "स्वास्थ्य"],
            "finance": ["money", "budget", "tax", "पैसा"],
            "legal": ["law", "legal", "court", "कानून"],
            "creative": ["write", "story", "design", "लेख"],
            "education": ["learn", "study", "teach", "पढाई"],
            "farming": ["farm", "crop", "खेती", "बाली"],
        }.items():
            if any(kw in msg for kw in keywords):
                return task
        return "general"

    def get_clone_prompt(self, intent: str) -> tuple:
        prompt = CLONE_PROMPTS.get(intent, CLONE_PROMPTS["general"])
        clone_names = {
            "coding": "Tech Architect 💻",
            "health": "Health Sage 🏥",
            "finance": "Financial Oracle 💰",
            "legal": "Legal Guardian ⚖️",
            "creative": "Creative Muse 🎨",
            "reasoning": "Strategic Planner 🎯",
            "education": "Education Mentor 📚",
            "farming": "Farm Guide 🌾",
            "general": "AsimNexus 🌌",
        }
        return prompt, clone_names.get(intent, "AsimNexus 🌌")

    # ── GENERATION ────────────────────────────────────────────────────────────

    async def _generate_gguf(self, prompt: str, system: str) -> Optional[str]:
        if not self._llm_loaded:
            return None
        try:
            result = self._llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024,
                temperature=0.7,
            )
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"GGUF generation error: {e}")
            return None

    async def _generate_ollama(self, prompt: str, system: str) -> Optional[str]:
        try:
            import aiohttp
            payload = {
                "model": "qwen2.5:3b",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }
            async with aiohttp.ClientSession() as s:
                async with s.post("http://localhost:11434/api/chat",
                                  json=payload,
                                  timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content")
        except Exception:
            return None

    async def _generate_cloud(self, prompt: str, system: str,
                               provider: str, api_key: str) -> Optional[str]:
        try:
            import aiohttp
            endpoints = {
                "openai":    ("https://api.openai.com/v1/chat/completions",    "gpt-4o-mini"),
                "anthropic": ("https://api.anthropic.com/v1/messages",         "claude-3-haiku-20240307"),
                "gemini":    ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                              "gemini-1.5-flash"),
                "deepseek":  ("https://api.deepseek.com/v1/chat/completions",  "deepseek-chat"),
                "grok":      ("https://api.x.ai/v1/chat/completions",          "grok-beta"),
            }
            if provider not in endpoints:
                return None
            url, model = endpoints[provider]
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": prompt}]
            payload = {"model": model, "messages": messages, "max_tokens": 1024}
            if provider == "anthropic":
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"
                payload = {"model": model,
                           "messages": [{"role": "user", "content": prompt}],
                           "system": system, "max_tokens": 1024}
            async with aiohttp.ClientSession() as s:
                async with s.post(url, json=payload, headers=headers,
                                  timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if provider == "anthropic":
                            return data["content"][0]["text"]
                        return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Cloud {provider} error: {e}")
            return None

    # ── MAIN PROCESS ──────────────────────────────────────────────────────────

    async def process(self, message: str,
                      user_id: str = "guest",
                      user_api_keys: Optional[Dict[str, str]] = None,
                      conversation_history: Optional[List[Dict]] = None) -> BrainResponse:

        # 1. Dharma check
        veto = self.dharma_check(message)
        if veto:
            return BrainResponse(
                response=veto, source="dharma", model="dharma-chakra",
                clone="Dharma Guardian ☯️", task_type="veto", intent="veto",
            )

        # 2. Detect intent → pick clone
        intent = self.detect_intent(message)
        system_prompt, clone_name = self.get_clone_prompt(intent)

        # 3. Try local GGUF first
        if not self._load_attempted:
            self.load_local_llm()
        response = await self._generate_gguf(message, system_prompt)
        if response:
            return BrainResponse(response=response, source="local_gguf",
                                 model="Qwen3-4B-distill", clone=clone_name,
                                 task_type=intent, intent=intent)

        # 4. Try Ollama
        response = await self._generate_ollama(message, system_prompt)
        if response:
            return BrainResponse(response=response, source="ollama",
                                 model="qwen2.5:3b", clone=clone_name,
                                 task_type=intent, intent=intent)

        # 5. Try user cloud keys
        if user_api_keys:
            for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
                key = (user_api_keys or {}).get(provider, "")
                if key:
                    response = await self._generate_cloud(message, system_prompt, provider, key)
                    if response:
                        return BrainResponse(response=response, source=provider,
                                             model=provider, clone=clone_name,
                                             task_type=intent, intent=intent)

        # 6. Offline fallback
        lang_hint = "नेपाली" if any(c > "\u0900" for c in message) else "English"
        fallback = (
            f"AsimNexus (offline mode): तपाईंको प्रश्न बुझियो — '{message[:80]}'\n\n"
            f"Local LLM load गर्न: pip install llama-cpp-python\n"
            f"Cloud API key थप्न Chat मा लेख्नुस्: 'openai api key: sk-xxxx'"
        ) if lang_hint == "नेपाली" else (
            f"AsimNexus (offline): Your message was understood — '{message[:80]}'\n\n"
            f"To enable AI: Install llama-cpp-python or add a cloud API key in chat."
        )
        return BrainResponse(response=fallback, source="fallback", model="offline",
                             clone=clone_name, task_type=intent, intent=intent)

    # ── STATUS ────────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        return {
            "local_gguf_loaded": self._llm_loaded,
            "gguf_path_exists": GGUF_PATH.exists(),
            "gguf_model": GGUF_PATH.name,
            "nvidia_nim": False,
            "dharma": "active",
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
brain = AsimBrain()
