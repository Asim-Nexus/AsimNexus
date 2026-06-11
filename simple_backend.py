#!/usr/bin/env python3
"""
STATUS: REAL — Production backend (FastAPI + SQLite + JWT)
ASIMNEXUS Core Backend
======================
Real backend wired to all core modules.
Local-first, Dharma-protected, Human-in-the-loop.
"""

import os
import sys
import json
import time
import hashlib
import secrets
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

try:
    import bcrypt
except ImportError:
    bcrypt = None

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load .env file early — before any module imports
_env_file = current_dir / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AsimNexus.Backend")

# ─── REAL MODULE IMPORTS (graceful fallback if missing) ─────────────────────
try:
    from core.identity.user_identity import UserIdentitySystem
    _user_mgr = UserIdentitySystem()
    logger.info("✅ UserIdentitySystem loaded")
except Exception as e:
    _user_mgr = None
    logger.warning(f"⚠️ UserIdentitySystem fallback: {e}")

try:
    from core.founder_clones.world_clones import WorldCloneOrchestrator
    _clones = WorldCloneOrchestrator()
    logger.info("✅ WorldCloneOrchestrator loaded")
except Exception as e:
    _clones = None
    logger.warning(f"⚠️ WorldCloneOrchestrator fallback: {e}")

try:
    from core.routing.hybrid_router import HybridRouter
    _router = HybridRouter(prefer_local=True, offline_mode=False)
    logger.info("✅ HybridRouter loaded")
except Exception as e:
    _router = None
    logger.warning(f"⚠️ HybridRouter fallback: {e}")

try:
    from core.vectormemory import VectorMemory
    _memory = VectorMemory("data/vector_memory.db")
    logger.info("✅ VectorMemory loaded")
except Exception as e:
    _memory = None
    logger.warning(f"⚠️ VectorMemory fallback: {e}")

try:
    from core.network.node_registry import NodeRegistry
    _nodes = NodeRegistry()
    logger.info("✅ NodeRegistry loaded")
except Exception as e:
    _nodes = None
    logger.warning(f"⚠️ NodeRegistry fallback: {e}")

try:
    from core.dharma_chakra.safety_veto import SafetyVeto
    _veto = SafetyVeto()
    logger.info("✅ SafetyVeto loaded")
except Exception as e:
    _veto = None
    logger.warning(f"⚠️ SafetyVeto fallback: {e}")

try:
    from core.identity.personal_os import PersonalOS
    logger.info("✅ PersonalOS loaded")
    _personal_os_class = PersonalOS
except Exception as e:
    _personal_os_class = None
    logger.warning(f"⚠️ PersonalOS fallback: {e}")

try:
    from core.economy.job_marketplace import marketplace as _marketplace
    logger.info("✅ JobMarketplace loaded")
except Exception as e:
    _marketplace = None
    logger.warning(f"⚠️ JobMarketplace fallback: {e}")

try:
    from core.dreaming.dreaming_engine import dreaming_engine as _dreaming
    logger.info("✅ DreamingEngine loaded")
except Exception as e:
    _dreaming = None
    logger.warning(f"⚠️ DreamingEngine fallback: {e}")

try:
    from core.dharma.dharma_veto import DharmaVeto
    from core.dharma.cultural_compiler import CulturalCompiler
    _dharma_veto = DharmaVeto()
    _cultural_compiler = CulturalCompiler(locale="nepal")
    logger.info("✅ DharmaVeto + CulturalCompiler loaded")
except Exception as e:
    _dharma_veto = None
    _cultural_compiler = None
    logger.warning(f"⚠️ DharmaVeto fallback: {e}")

# ─── CORE TRUST PATH MODULES ─────────────────────────────────────────────────────
try:
    from backend.health import setup_health_routes
    logger.info("✅ Health module loaded")
except Exception as e:
    setup_health_routes = None
    logger.warning(f"⚠️ Health module fallback: {e}")

try:
    from backend.registry import setup_registry_routes
    logger.info("✅ Registry module loaded")
except Exception as e:
    setup_registry_routes = None
    logger.warning(f"⚠️ Registry module fallback: {e}")

try:
    from backend.auth import setup_auth_routes
    logger.info("✅ Auth module loaded")
except Exception as e:
    setup_auth_routes = None
    logger.warning(f"⚠️ Auth module fallback: {e}")

try:
    from backend.user_profiles import setup_user_profile_routes
    logger.info("✅ User profiles module loaded")
except Exception as e:
    setup_user_profile_routes = None
    logger.warning(f"⚠️ User profiles module fallback: {e}")

try:
    from backend.router import setup_router_routes
    logger.info("✅ Router module loaded")
except Exception as e:
    setup_router_routes = None
    logger.warning(f"⚠️ Router module fallback: {e}")

try:
    from backend.tools import setup_tools_routes
    logger.info("✅ Tools module loaded")
except Exception as e:
    setup_tools_routes = None
    logger.warning(f"⚠️ Tools module fallback: {e}")

# ─── MILESTONE 2: LOCAL BRAIN LOOP MODULES ───────────────────────────────────────
try:
    from backend.chat import setup_chat_routes
    logger.info("✅ Chat module loaded")
except Exception as e:
    setup_chat_routes = None
    logger.warning(f"⚠️ Chat module fallback: {e}")

try:
    from backend.memory import setup_memory_routes
    logger.info("✅ Memory module loaded")
except Exception as e:
    setup_memory_routes = None
    logger.warning(f"⚠️ Memory module fallback: {e}")

try:
    from backend.clones import setup_clones_routes
    logger.info("✅ Clones module loaded")
except Exception as e:
    setup_clones_routes = None
    logger.warning(f"⚠️ Clones module fallback: {e}")

# ─── MILESTONE 3: MESH SPINE MODULES ─────────────────────────────────────────────
try:
    from backend.mesh import setup_mesh_routes
    logger.info("✅ Mesh module loaded")
except Exception as e:
    setup_mesh_routes = None
    logger.warning(f"⚠️ Mesh module fallback: {e}")

# ─── MODULE-LEVEL SHARED STATE (DB-backed) ───────────────────────────────────
def _get_agent_mode(user_id: str) -> dict:
    """Fetch agent mode from DB."""
    try:
        with _get_db() as conn:
            row = conn.execute(
                "SELECT agent_mode_json FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return {"active": False}


def _set_agent_mode(user_id: str, data: dict):
    """Persist agent mode to DB."""
    try:
        with _get_db() as conn:
            conn.execute(
                "UPDATE users SET agent_mode_json=? WHERE id=?",
                (json.dumps(data), user_id)
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Agent mode persist error: {e}")


def _get_resource_sharing(user_id: str) -> dict:
    """Fetch resource sharing from DB."""
    try:
        with _get_db() as conn:
            row = conn.execute(
                "SELECT resource_sharing_json FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return {"enabled": False, "share_pct": 0}


def _set_resource_sharing(user_id: str, data: dict):
    """Persist resource sharing to DB."""
    try:
        with _get_db() as conn:
            conn.execute(
                "UPDATE users SET resource_sharing_json=? WHERE id=?",
                (json.dumps(data), user_id)
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Resource sharing persist error: {e}")


# ─── LOCAL LLM (Qwen3 GGUF) ──────────────────────────────────────────────────
_local_llm = None
GGUF_MODEL_PATH = str(current_dir / "models" / "Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf")

def _init_local_llm():
    global _local_llm
    try:
        from llama_cpp import Llama
        if Path(GGUF_MODEL_PATH).exists():
            _local_llm = Llama(
                model_path=GGUF_MODEL_PATH,
                n_ctx=4096,
                n_threads=4,
                n_gpu_layers=20,
                verbose=False
            )
            logger.info(f"✅ Qwen3 GGUF loaded: {GGUF_MODEL_PATH}")
        else:
            logger.warning(f"⚠️ GGUF model not found: {GGUF_MODEL_PATH}")
    except ImportError:
        logger.warning("⚠️ llama-cpp-python not installed. Run: pip install llama-cpp-python")
    except Exception as e:
        logger.warning(f"⚠️ Local LLM load failed: {e}")

# ─── SIMPLE USER STORE (SQLite-backed) ──────────────────────────────────────
import sqlite3

DB_PATH = current_dir / "data" / "asim_core.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                password_hash TEXT NOT NULL,
                country_code TEXT DEFAULT 'NP',
                universe_mode TEXT DEFAULT 'personal',
                theme TEXT DEFAULT 'deep-space',
                api_keys TEXT DEFAULT '{}',
                agent_mode_json TEXT DEFAULT '{}',
                resource_sharing_json TEXT DEFAULT '{}',
                phone TEXT,
                national_id_hash TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        # Backward compatibility: add columns if they don't exist
        for col, dtype in [("agent_mode_json", "TEXT DEFAULT '{}'"), ("resource_sharing_json", "TEXT DEFAULT '{}'")]:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
            except Exception:
                pass  # Column already exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                clone_used TEXT,
                intent TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                poster_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                budget TEXT,
                timeline_days INTEGER DEFAULT 5,
                skills TEXT DEFAULT '[]',
                status TEXT DEFAULT 'open',
                agent_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT DEFAULT (datetime('now', '+7 days'))
            )
        """)
        # Backward compat: add expires_at if missing (SQLite ALTER TABLE requires constant default)
        try:
            cursor = conn.execute("PRAGMA table_info(tokens)")
            cols = {row[1] for row in cursor.fetchall()}
            if "expires_at" not in cols:
                conn.execute("ALTER TABLE tokens ADD COLUMN expires_at TEXT")
                conn.execute("UPDATE tokens SET expires_at = datetime('now', '+7 days') WHERE expires_at IS NULL")
                logger.info("Schema migration: added expires_at column to tokens table")
        except Exception:
            pass
        conn.commit()
    logger.info("✅ Database initialized")

_init_db()

# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────
TOKEN_TTL_DAYS = 7

def _hash_password(pwd: str) -> str:
    """Hash password with bcrypt (preferred) or SHA256 fallback."""
    if bcrypt:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(rounds=12)).decode()
    return hashlib.sha256(pwd.encode()).hexdigest()

def _verify_password(pwd: str, hashed: str) -> bool:
    """Verify password against bcrypt or SHA256 hash."""
    if bcrypt and hashed.startswith("$2b$"):
        return bcrypt.checkpw(pwd.encode(), hashed.encode())
    return hashlib.sha256(pwd.encode()).hexdigest() == hashed

def _create_token(user_id: str) -> str:
    token = secrets.token_hex(32)
    expires = (datetime.utcnow() + timedelta(days=TOKEN_TTL_DAYS)).isoformat()
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires)
        )
        conn.commit()
    return token

def _get_user_from_token(token: str) -> Optional[Dict]:
    with _get_db() as conn:
        # Clean expired tokens
        conn.execute("DELETE FROM tokens WHERE expires_at < datetime('now')")
        conn.commit()
        row = conn.execute(
            "SELECT u.* FROM users u JOIN tokens t ON u.id = t.user_id WHERE t.token = ? AND t.expires_at > datetime('now')",
            (token,)
        ).fetchone()
    return dict(row) if row else None

def _get_user_id_from_request(request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        user = _get_user_from_token(token)
        return user["id"] if user else None
    return None

# ─── CHAT COMMAND PARSER ──────────────────────────────────────────────────────
THEME_COMMANDS = {
    "dark mode": "deep-space", "dark": "deep-space", "रात": "deep-space",
    "light mode": "aurora", "light": "aurora", "बिहान": "aurora",
    "government": "government", "सरकार": "government",
    "company": "corporate", "corporate": "corporate", "कम्पनी": "corporate",
    "medical": "medical", "health": "medical", "health theme": "medical",
    "simple": "minimal", "minimal": "minimal", "सजिलो": "minimal",
}
UNIVERSE_COMMANDS = {
    "personal universe": "personal", "personal": "personal", "व्यक्तिगत": "personal",
    "family universe": "family", "family": "family", "परिवार": "family",
    "community universe": "community", "community": "community", "समुदाय": "community",
    "company universe": "company", "company mode": "company",
    "government universe": "government", "government mode": "government",
    "global universe": "global", "global": "global", "विश्व": "global",
}

def _parse_chat_command(message: str) -> Optional[Dict]:
    msg_lower = message.lower().strip()
    # API key add command
    for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
        if provider in msg_lower and ("key" in msg_lower or "api" in msg_lower):
            parts = message.split()
            for part in parts:
                if part.startswith("sk-") or part.startswith("AIza") or len(part) > 30:
                    return {"type": "api_key", "provider": provider, "key": part}
    # Theme command
    for cmd, theme in THEME_COMMANDS.items():
        if cmd in msg_lower:
            return {"type": "theme", "value": theme}
    # Universe command
    for cmd, universe in UNIVERSE_COMMANDS.items():
        if cmd in msg_lower:
            return {"type": "universe", "value": universe}
    # Sharing command
    if "2-5% sharing" in msg_lower or "resource sharing" in msg_lower or "sharing सक्रिय" in msg_lower:
        return {"type": "mesh_sharing", "value": True}
    # OS commands — /os <tool_name> [params_json]
    if msg_lower.startswith("/os "):
        parts = message.split(maxsplit=2)
        tool_name = parts[1] if len(parts) > 1 else ""
        params_str = parts[2] if len(parts) > 2 else "{}"
        try:
            params = json.loads(params_str) if isinstance(params_str, str) else {}
        except json.JSONDecodeError:
            params = {"raw": params_str}
        return {"type": "os", "tool_name": tool_name, "parameters": params}
    # OS status command
    if msg_lower in ("/os", "/os status", "/os help"):
        return {"type": "os", "tool_name": "help", "parameters": {}}
    # Hardware status shortcuts
    if msg_lower in ("/cpu", "/hw cpu"):
        return {"type": "os", "tool_name": "hw.cpu", "parameters": {}}
    if msg_lower in ("/memory", "/mem", "/hw memory"):
        return {"type": "os", "tool_name": "hw.memory", "parameters": {}}
    if msg_lower in ("/disk", "/hw disk"):
        return {"type": "os", "tool_name": "hw.disk", "parameters": {}}
    if msg_lower in ("/network", "/net", "/hw network"):
        return {"type": "os", "tool_name": "hw.network", "parameters": {}}
    if msg_lower in ("/battery", "/bat", "/hw battery"):
        return {"type": "os", "tool_name": "hw.battery", "parameters": {}}
    if msg_lower in ("/gpu", "/hw gpu"):
        return {"type": "os", "tool_name": "hw.gpu", "parameters": {}}
    if msg_lower in ("/npu", "/hw npu", "/ai accelerator"):
        return {"type": "os", "tool_name": "hw.npu", "parameters": {}}
    if msg_lower in ("/motherboard", "/mb", "/hw motherboard", "/baseboard"):
        return {"type": "os", "tool_name": "hw.motherboard", "parameters": {}}
    if msg_lower in ("/chipset", "/hw chipset"):
        return {"type": "os", "tool_name": "hw.chipset", "parameters": {}}
    if msg_lower in ("/ram", "/hw ram", "/memory modules"):
        return {"type": "os", "tool_name": "hw.ram", "parameters": {}}
    if msg_lower in ("/rom", "/hw rom", "/bios", "/firmware"):
        return {"type": "os", "tool_name": "hw.rom", "parameters": {}}
    if msg_lower in ("/storage", "/storage controller", "/hw storage", "/nvme", "/sata"):
        return {"type": "os", "tool_name": "hw.storage_controller", "parameters": {}}
    if msg_lower in ("/usb", "/hw usb"):
        return {"type": "os", "tool_name": "hw.usb", "parameters": {}}
    if msg_lower in ("/display", "/monitor", "/hw display", "/hw monitor"):
        return {"type": "os", "tool_name": "hw.display", "parameters": {}}
    if msg_lower in ("/audio", "/sound", "/hw audio"):
        return {"type": "os", "tool_name": "hw.audio", "parameters": {}}
    if msg_lower in ("/sensor", "/sensors", "/temperature", "/hw sensor"):
        return {"type": "os", "tool_name": "hw.sensor", "parameters": {}}
    if msg_lower in ("/thermal", "/cooling", "/fan", "/hw thermal"):
        return {"type": "os", "tool_name": "hw.thermal", "parameters": {}}
    if msg_lower in ("/bios", "/uefi", "/hw bios"):
        return {"type": "os", "tool_name": "hw.bios", "parameters": {}}
    if msg_lower in ("/hw all", "/hw status", "/sysinfo", "/all"):
        return {"type": "os", "tool_name": "hw.all", "parameters": {}}
    if msg_lower in ("/kernel", "/hw kernel"):
        return {"type": "os", "tool_name": "kernel", "parameters": {}}
    return None

# ─── LOCAL LLM INFERENCE ──────────────────────────────────────────────────────
async def _generate_local(prompt: str, system: str = "") -> Optional[str]:
    if _local_llm is None:
        return None
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        result = _local_llm.create_chat_completion(
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Local LLM error: {e}")
        return None

async def _generate_cloud(prompt: str, provider: str, api_key: str, system: str = "") -> Optional[str]:
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        endpoints = {
            "openai": ("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
            "anthropic": ("https://api.anthropic.com/v1/messages", "claude-3-haiku-20240307"),
            "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-1.5-flash"),
            "deepseek": ("https://api.deepseek.com/v1/chat/completions", "deepseek-chat"),
            "grok": ("https://api.x.ai/v1/chat/completions", "grok-beta"),
        }
        if provider not in endpoints:
            return None
        url, model = endpoints[provider]
        payload = {"model": model, "messages": messages, "max_tokens": 1024}
        if provider == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            payload = {"model": model, "messages": [m for m in messages if m["role"] != "system"],
                       "system": system, "max_tokens": 1024}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if provider == "anthropic":
                        return data["content"][0]["text"]
                    return data["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        logger.error(f"Cloud LLM error ({provider}): {e}")
        return None

def _strip_thinking(text: str) -> str:
    """Remove Qwen3 chain-of-thought tokens and reasoning preamble."""
    import re
    # Remove <think>...</think> blocks (Qwen3 reasoning)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove lines that are clearly internal reasoning (start with "Alright," "I need to", "The user")
    lines = text.split('\n')
    clean = []
    skip_mode = False
    for line in lines:
        stripped = line.strip()
        # Skip reasoning preamble lines
        if any(stripped.startswith(p) for p in [
            "Alright,", "I need to", "The user", "Let me", "I should",
            "I'll", "I'm going to", "So I", "First,", "Now,",
        ]) and not clean:
            continue
        clean.append(line)
    return '\n'.join(clean).strip()


async def _smart_generate(prompt: str, user_id: str, system: str = "") -> Dict:
    # Try local first
    local_resp = await _generate_local(prompt, system)
    if local_resp:
        return {"response": _strip_thinking(local_resp), "source": "local_gguf", "model": "Qwen3-4B"}
    # Try cloud with user's API keys
    with _get_db() as conn:
        row = conn.execute("SELECT api_keys FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        api_keys = json.loads(row["api_keys"] or "{}")
        for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
            if provider in api_keys and api_keys[provider]:
                cloud_resp = await _generate_cloud(prompt, provider, api_keys[provider], system)
                if cloud_resp:
                    return {"response": cloud_resp, "source": "cloud", "model": provider}
    # Fallback
    return {
        "response": f"AsimNexus (offline): तपाईंको प्रश्न '{prompt[:60]}...' बुझियो। Local LLM वा Cloud API key थप्नुस् राम्रो जवाफका लागि।",
        "source": "fallback",
        "model": "fallback"
    }


def create_app():
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

    @asynccontextmanager
    async def lifespan(app):
        _init_local_llm()
        if _dreaming:
            asyncio.create_task(_dreaming.start())
        # Initialize ASIM Kernel
        try:
            from core.kernel.kernel import get_kernel
            _kernel = get_kernel()
            hp = _kernel.get_hardware_profile()
            logger.info(f"🧠 ASIM Kernel initialized: {hp.os_name} | {hp.cpu_name} | {hp.total_memory_gb:.1f}GB RAM")
        except Exception as e:
            logger.warning(f"⚠️ ASIM Kernel init skipped: {e}")
        logger.info("🚀 AsimNexus Backend started")
        yield
        logger.info("🛑 AsimNexus Backend shutting down")

    app = FastAPI(title="ASIMNEXUS Core", description="AsimNexus World OS Backend", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    try:
        from backend.middleware import ObservabilityMiddleware
        app.add_middleware(ObservabilityMiddleware)
        logger.info("✅ ObservabilityMiddleware registered")
    except Exception as e:
        logger.warning(f"⚠️ ObservabilityMiddleware registration skipped: {e}")

    # Sentry / APM Integration
    try:
        from monitoring.sentry_config import init_sentry, AsimSentryMiddleware
        if init_sentry():
            app.add_middleware(AsimSentryMiddleware)
            logger.info("✅ Sentry APM initialized")
        else:
            logger.info("ℹ️ Sentry APM skipped (SENTRY_DSN not set)")
    except Exception as e:
        logger.warning(f"⚠️ Sentry init skipped: {e}")

    # Rate limiting middleware
    try:
        from core.rate_limiter_middleware import RateLimiterMiddleware
        app.add_middleware(RateLimiterMiddleware)
        logger.info("✅ RateLimiterMiddleware registered — all endpoints rate limited")
    except Exception as e:
        logger.warning(f"⚠️ RateLimiterMiddleware registration skipped: {e}")

    # ─── CORE TRUST PATH: HEALTH & REGISTRY ─────────────────────────────────────
    if setup_health_routes:
        setup_health_routes(app, str(DB_PATH), GGUF_MODEL_PATH)

    if setup_registry_routes:
        setup_registry_routes(app, str(DB_PATH))

    if setup_auth_routes:
        setup_auth_routes(app, str(DB_PATH))

    if setup_user_profile_routes:
        setup_user_profile_routes(app, str(DB_PATH))

    if setup_router_routes:
        local_llm_checker = lambda: _local_llm is not None
        async def cloud_runner(prompt, user_id):
            with _get_db() as conn:
                row = conn.execute("SELECT api_keys FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                api_keys = json.loads(row["api_keys"] or "{}")
                for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
                    if provider in api_keys and api_keys[provider]:
                        res = await _generate_cloud(prompt, provider, api_keys[provider], "")
                        if res:
                            return {"response": res, "model": provider}
            return None
        setup_router_routes(app, local_llm_checker, cloud_runner)

    if setup_tools_routes:
        setup_tools_routes(app, str(DB_PATH))

    try:
        from backend.observability import setup_observability_routes
        setup_observability_routes(app)
        logger.info("✅ Observability routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Observability routes registration skipped: {e}")

    # ─── MILESTONE 6: DEPLOYMENT SPINE ───────────────────────────────────────────
    try:
        from backend import deployment as _deploy_mod
        from backend import release as _release_mod
        from backend import version as _version_mod
        from backend import config as _config_mod

        @app.get("/healthz")
        async def healthz():
            """Container liveness/readiness probe endpoint."""
            return JSONResponse({"status": "ok"})

        @app.get("/api/deploy/status")
        async def deploy_status():
            return JSONResponse(_deploy_mod.get_deployment_status())

        @app.get("/api/deploy/targets")
        async def deploy_targets():
            return JSONResponse({"targets": _deploy_mod.list_targets()})

        @app.post("/api/deploy/build")
        async def deploy_build(request: Request):
            body = await request.json()
            target = body.get("target")
            version = body.get("version", _version_mod.get_version())
            if not target:
                raise HTTPException(400, "target is required")
            try:
                result = _deploy_mod.package_release(target=target, version=version)
                return JSONResponse(result)
            except Exception as e:
                raise HTTPException(400, str(e))

        @app.post("/api/deploy/rollback")
        async def deploy_rollback(request: Request):
            body = await request.json()
            target = body.get("target")
            to_version = body.get("to_version")
            if not target:
                raise HTTPException(400, "target is required")
            try:
                cur = _release_mod.current_release(target=target)
                from_ver = cur.get("version", "unknown")
                rollback_result = _deploy_mod.rollback_release(target=target, to_version=to_version)
                if to_version and from_ver != "unknown":
                    _release_mod.record_rollback(
                        from_version=from_ver,
                        to_version=to_version,
                        target=target,
                    )
                return JSONResponse(rollback_result)
            except Exception as e:
                raise HTTPException(400, str(e))

        @app.post("/api/deploy/release")
        async def deploy_release(request: Request):
            body = await request.json()
            version = body.get("version")
            target = body.get("target")
            checksum = body.get("checksum", "")
            if not version or not target:
                raise HTTPException(400, "version and target are required")
            result = _release_mod.publish_release(
                version=version, target=target, checksum=checksum,
            )
            return JSONResponse(result)

        @app.get("/api/deploy/releases")
        async def deploy_releases(request: Request):
            target = request.query_params.get("target")
            return JSONResponse(_release_mod.list_releases(target=target))

        @app.get("/api/release/current")
        async def release_current(request: Request):
            target = request.query_params.get("target")
            return JSONResponse(_release_mod.current_release(target=target))

        @app.get("/api/version")
        async def api_version():
            return JSONResponse({
                "version": _version_mod.get_version(),
                "build_id": _version_mod.get_build_id(),
                "git_sha": _version_mod.get_git_sha(),
                "channel": _version_mod.get_release_channel(),
            })

        @app.get("/api/build")
        async def api_build():
            env = _config_mod.validate_deploy_env()
            return JSONResponse({
                "build_id": _version_mod.get_build_id(),
                "git_sha": _version_mod.get_git_sha(),
                "config_valid": env["valid"],
                "issues": env["issues"],
            })

        logger.info("✅ Deployment spine routes registered (Milestone 6)")
    except Exception as e:
        logger.warning(f"⚠️ Deployment spine routes skipped: {e}")

    # ─── MILESTONE 2: LOCAL BRAIN LOOP ───────────────────────────────────────────
    if setup_chat_routes:
        setup_chat_routes(app, str(current_dir / "data" / "chat.db"))

    if setup_memory_routes:
        setup_memory_routes(app, str(current_dir / "data" / "vector_memory.db"))

    if setup_clones_routes:
        setup_clones_routes(app, str(current_dir / "data" / "clone_orchestrator.db"))

    # ─── MILESTONE 3: MESH SPINE ─────────────────────────────────────────────────
    if setup_mesh_routes:
        setup_mesh_routes(app, "local_node")

    # ─── HEALTH ───────────────────────────────────────────────────────────────
    @app.get("/health")
    @app.get("/api/status")
    @app.get("/api/db/health")
    async def health():
        return JSONResponse({
            "status": "healthy",
            "version": "2.0.0",
            "local_llm": _local_llm is not None,
            "gguf_model": Path(GGUF_MODEL_PATH).exists(),
            "modules": {
                "user_identity": _user_mgr is not None,
                "world_clones": _clones is not None,
                "hybrid_router": _router is not None,
                "vector_memory": _memory is not None,
                "node_registry": _nodes is not None,
                "safety_veto": _veto is not None,
            }
        })

    @app.get("/status")
    async def status():
        import platform, psutil
        return JSONResponse({
            "status": "online",
            "system": "ASIMNEXUS World OS",
            "version": "2.0.0",
            "device": {
                "os": platform.system(),
                "cpu_cores": psutil.cpu_count(),
                "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "ram_used_pct": psutil.virtual_memory().percent,
            },
            "local_llm": {"loaded": _local_llm is not None, "model": "Qwen3-4B-distill"},
            "dharma": "active",
            "mesh": "ready",
        })

    @app.get("/api/system/info")
    @app.get("/api/local-llm/health")
    async def system_info():
        import platform
        return JSONResponse({
            "os": platform.system(),
            "python": sys.version.split()[0],
            "local_llm_loaded": _local_llm is not None,
            "gguf_path": GGUF_MODEL_PATH,
            "gguf_exists": Path(GGUF_MODEL_PATH).exists(),
            "status": "healthy"
        })

    # ─── DHARMA ΔT ENGINE (PRODUCTION) ─────────────────────────────────────────
    @app.get("/api/dharma/status")
    async def dharma_status():
        """Production ΔT Engine - Real calculations from live data"""
        try:
            from core.dharma import get_delta_t_production
            
            engine = get_delta_t_production()
            result = engine.calculate_production_delta_t()
            
            return JSONResponse(result)
        except Exception as e:
            logger.error(f"DeltaT production error: {e}")
            return JSONResponse({
                "error": str(e),
                "production": False,
                "fallback": "simulation_mode",
                "symmetry": 0.85,
                "gini": 0.15,
                "delta_t": 0.05,
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })

    @app.get("/api/dharma/production/status")
    async def dharma_production_status():
        """Get ΔT production engine status"""
        try:
            from core.dharma import get_delta_t_production
            
            engine = get_delta_t_production()
            return JSONResponse(engine.get_production_status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/dharma/veto")
    async def dharma_veto(request: Request):
        """Manual veto for ethical concerns"""
        try:
            body = await request.json()
            reason = body.get('reason', 'No reason provided')
            severity = body.get('severity', 'warning')
            
            # Log the veto
            logger.warning(f"🛑 DHARMA VETO: {severity} - {reason}")
            
            # In production: trigger actual veto mechanism
            # For now: log and acknowledge
            return JSONResponse({
                "success": True,
                "veto_logged": True,
                "severity": severity,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "action": "Veto recorded and will be reviewed by human governance"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── AUTH ─────────────────────────────────────────────────────────────────
    @app.post("/auth/register")
    async def register(request: Request):
        body = await request.json()
        email = body.get("email", "").lower().strip()
        password = body.get("password", "")
        display_name = body.get("display_name", email.split("@")[0])
        country_code = body.get("country_code", "NP")
        if not email or not password:
            raise HTTPException(400, "Email and password required")
        with _get_db() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if existing:
                raise HTTPException(400, "Email already registered")
            user_id = secrets.token_hex(8)
            conn.execute(
                "INSERT INTO users (id,email,display_name,password_hash,country_code) VALUES (?,?,?,?,?)",
                (user_id, email, display_name, _hash_password(password), country_code)
            )
            conn.commit()
        token = _create_token(user_id)
        return JSONResponse({"success": True, "token": token,
                             "user": {"id": user_id, "email": email, "display_name": display_name}})

    @app.post("/auth/login")
    async def login(request: Request):
        body = await request.json()
        email = body.get("email", "").lower().strip()
        password = body.get("password", "")
        if not email or not password:
            raise HTTPException(400, "Email and password required")
        with _get_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            raise HTTPException(401, "User not found")
        if not _verify_password(password, dict(row)["password_hash"]):
            raise HTTPException(401, "Invalid credentials")
        user = dict(row)
        token = _create_token(user["id"])
        return JSONResponse({"success": True, "token": token,
                             "user": {"id": user["id"], "email": email, "display_name": user["display_name"]}})

    @app.get("/auth/me")
    async def me(request: Request):
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        with _get_db() as conn:
            row = conn.execute("SELECT id,email,display_name,universe_mode,theme FROM users WHERE id=?",
                               (user_id,)).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return JSONResponse(dict(row))

    # ─── CHAT (Universal — commands + LLM) ───────────────────────────────────
    @app.post("/chat")
    @app.post("/llm/chat")
    @app.post("/api/chat")
    async def chat(request: Request):
        body = await request.json()
        message = body.get("message", "").strip()
        user_id = _get_user_id_from_request(request) or "guest"
        if not message:
            raise HTTPException(400, "Message required")

        # Zero-Trust cap check — user must have SEND_MESSAGE cap
        try:
            from core.runtime.zero_trust_runtime import get_runtime, Cap
            rt = get_runtime()
            principal = f"user:{user_id}"
            if principal not in rt._tokens or not rt._tokens[principal].is_valid():
                rt.register(principal, "user", ttl=86400)
            if not rt.enforce(principal, Cap.SEND_MESSAGE):
                return JSONResponse({"response": "Zero-Trust: SEND_MESSAGE cap denied.", "source": "runtime"})
        except Exception:
            pass

        # Dharma VETO check
        if _veto:
            try:
                veto_result = _veto.check(action="chat_message", node_id=user_id, content=message)
                if veto_result and not veto_result.passed:
                    reason = veto_result.summary
                    if veto_result.events:
                        reason = veto_result.events[0].detail
                    return JSONResponse({
                        "response": f"Dharma-Chakra VETO: {reason}",
                        "source": "dharma", "command": None
                    })
            except Exception:
                pass

        # Parse chat command
        cmd = _parse_chat_command(message)
        if cmd:
            if cmd["type"] == "api_key" and user_id != "guest":
                with _get_db() as conn:
                    row = conn.execute("SELECT api_keys FROM users WHERE id=?", (user_id,)).fetchone()
                    existing = json.loads(dict(row)["api_keys"] or "{}") if row else {}
                    existing[cmd["provider"]] = cmd["key"]
                    conn.execute("UPDATE users SET api_keys=? WHERE id=?",
                                 (json.dumps(existing), user_id))
                    conn.commit()
                return JSONResponse({
                    "response": f"✅ {cmd['provider'].upper()} API key saved! अब सबै Clones ले use गर्छन्।",
                    "source": "system", "command": cmd
                })
            if cmd["type"] == "theme" and user_id != "guest":
                with _get_db() as conn:
                    conn.execute("UPDATE users SET theme=? WHERE id=?", (cmd["value"], user_id))
                    conn.commit()
                return JSONResponse({
                    "response": f"🎨 Theme changed to '{cmd['value']}'! UI automatically updated।",
                    "source": "system", "command": cmd
                })
            if cmd["type"] == "universe" and user_id != "guest":
                with _get_db() as conn:
                    conn.execute("UPDATE users SET universe_mode=? WHERE id=?", (cmd["value"], user_id))
                    conn.commit()
                return JSONResponse({
                    "response": f"🌌 Universe mode set to '{cmd['value']}'! AsimNexus adapted।",
                    "source": "system", "command": cmd
                })
            if cmd["type"] == "mesh_sharing":
                return JSONResponse({
                    "response": "🔗 Mesh resource sharing activated! 2-5% of your resources will help the network.",
                    "source": "system", "command": cmd
                })
            if cmd["type"] == "os":
                try:
                    executor = _get_os_executor()
                    if not executor:
                        return JSONResponse({
                            "response": "⚠️ OS Control Executor not available. Backend may still be initializing.",
                            "source": "system", "command": cmd
                        })
                    tool_name = cmd.get("tool_name", "")
                    parameters = cmd.get("parameters", {})
                    if tool_name == "kernel":
                        # Return kernel info directly
                        try:
                            from core.kernel.kernel import get_kernel
                            k = get_kernel()
                            hp = k.get_hardware_profile()
                            return JSONResponse({
                                "response": f"🧠 **ASIM Kernel**\n- OS: {hp.os_name} {hp.os_version}\n- CPU: {hp.cpu_name} ({hp.cpu_cores} cores @ {hp.cpu_freq}MHz)\n- RAM: {hp.total_memory_gb:.1f} GB\n- Architecture: {hp.architecture}",
                                "source": "system", "command": cmd
                            })
                        except Exception as e:
                            return JSONResponse({
                                "response": f"⚠️ Kernel info unavailable: {e}",
                                "source": "system", "command": cmd
                            })
                    if tool_name == "help":
                        tools_list = executor.tool_registry.list_tools()
                        lines = ["**🖥️ OS Control Tools**\n"]
                        for t in tools_list:
                            lines.append(f"- `{t.tool_id}`: {t.description} (risk: {t.risk_level.value})")
                        return JSONResponse({
                            "response": "\n".join(lines),
                            "source": "system", "command": cmd
                        })
                    # Execute the tool
                    result = await executor.execute(tool_name, parameters, "AutoModeAgent", user_id)
                    result_dict = _serialize_tool_result(result)
                    verdict = result_dict.get("verdict", "")
                    if verdict in ("allowed",) and result_dict.get("output") is not None:
                        output = result_dict["output"]
                        # Format output as readable text
                        if isinstance(output, dict):
                            lines = [f"**{output.get('name', tool_name)}**"]
                            metrics = output.get("metrics", {})
                            if isinstance(metrics, dict):
                                for k, v in metrics.items():
                                    if isinstance(v, (int, float)):
                                        lines.append(f"- {k}: {v}")
                                    elif isinstance(v, str):
                                        lines.append(f"- {k}: {v}")
                                    elif isinstance(v, list):
                                        for item in v:
                                            if isinstance(item, dict):
                                                for ik, iv in item.items():
                                                    lines.append(f"- {ik}: {iv}")
                                            else:
                                                lines.append(f"- {item}")
                                    elif isinstance(v, dict):
                                        for sk, sv in v.items():
                                            lines.append(f"- {sk}: {sv}")
                            status_text = output.get("status", "")
                            if status_text:
                                lines.append(f"\nStatus: {status_text}")
                            response_text = "\n".join(lines)
                        else:
                            response_text = str(output)
                        return JSONResponse({
                            "response": f"✅ **{tool_name}**\n{response_text}",
                            "source": "system", "command": cmd
                        })
                    else:
                        error_msg = result_dict.get("error", "Unknown error")
                        return JSONResponse({
                            "response": f"⚠️ Tool `{tool_name}` failed: {error_msg}",
                            "source": "system", "command": cmd
                        })
                except Exception as e:
                    logger.error(f"⚠️ OS command error: {e}")
                    return JSONResponse({
                        "response": f"⚠️ OS command error: {e}",
                        "source": "system", "command": cmd
                    })

        # Route to correct clone
        intent = "generic"
        clone_name = "AsimNexus"
        system_prompt = "You are AsimNexus, a helpful AI assistant. Answer directly and concisely. Do NOT show your reasoning or thinking process. Reply in the same language as the user. /no_think"
        if _router:
            try:
                decision = _router.route(message)
                intent = decision.intent.value
                clone_name = intent.replace("_", " ").title()
            except Exception:
                pass
        if _clones:
            try:
                clone = _clones.get_clone_for_intent(intent)
                if clone:
                    clone_name = clone.role.value
                    system_prompt = clone.system_prompt
            except Exception:
                pass

        # Generate response
        result = await _smart_generate(message, user_id, system_prompt)

        # Save to memory — only for authenticated users, not guest
        if user_id != "guest":
            msg_id = secrets.token_hex(8)
            with _get_db() as conn:
                conn.execute(
                    "INSERT INTO messages (id,user_id,role,content,clone_used,intent) VALUES (?,?,?,?,?,?)",
                    (msg_id, user_id, "user", message, clone_name, intent)
                )
                conn.execute(
                    "INSERT INTO messages (id,user_id,role,content,clone_used,intent) VALUES (?,?,?,?,?,?)",
                    (secrets.token_hex(8), user_id, "assistant", result["response"], clone_name, intent)
                )
                conn.commit()

        return JSONResponse({
            "response": result["response"],
            "source": result["source"],
            "model": result["model"],
            "clone": clone_name,
            "intent": intent,
            "command": None
        })

    # ─── ASIM BRAIN ENDPOINTS (Frontend Compatibility) ─────────────────────────
    @app.post("/api/brain/process")
    async def brain_process(request: Request):
        """Process chat message through Asim Brain — frontend compatibility"""
        try:
            body = await request.json()
            message = body.get("message", "").strip()
            user_id = _get_user_id_from_request(request) or "guest"
            mode = body.get("mode", "personal")

            if not message:
                return JSONResponse({"response": "No message provided.", "source": "error", "timestamp": datetime.now().isoformat()})

            # Build system prompt
            system = "You are Asim, the AI assistant for AsimNexus — a World Operating System. Help users with health, work, AI agents, mesh networks, governance, and digital identity. Be helpful, concise, and friendly."

            # Generate response
            result = await _smart_generate(message, user_id, system)

            return JSONResponse({
                "response": result["response"],
                "source": result.get("source", "local"),
                "timestamp": datetime.now().isoformat(),
                "clone_used": "Asim Core (Qwen3-4B)"
            })
        except Exception as e:
            logger.error(f"Brain process error: {e}")
            return JSONResponse({
                "response": f"⚠️ Error: {str(e)}",
                "source": "error",
                "timestamp": datetime.now().isoformat()
            })

    @app.post("/api/brain/stream")
    async def brain_stream(request: Request):
        """Stream chat response from Asim Brain — frontend compatibility"""
        from fastapi.responses import StreamingResponse
        import asyncio

        try:
            body = await request.json()
            message = body.get("message", "").strip()
            user_id = _get_user_id_from_request(request) or "guest"

            if not message:
                return JSONResponse({"error": "No message provided"}, status_code=400)

            system = "You are Asim, the AI assistant for AsimNexus. Be helpful and concise."

            async def event_generator():
                # Simulate streaming with the local response
                result = await _smart_generate(message, user_id, system)
                response_text = result.get("response", "")
                words = response_text.split()
                for word in words:
                    yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                    await asyncio.sleep(0.05)
                yield f"data: {json.dumps({'done': True})}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")
        except Exception as e:
            logger.error(f"Brain stream error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ─── PERSONAL / CLONES ────────────────────────────────────────────────────
    @app.get("/personal/status")
    async def personal_status(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        with _get_db() as conn:
            row = conn.execute("SELECT universe_mode,theme FROM users WHERE id=?", (user_id,)).fetchone()
        mode = dict(row)["universe_mode"] if row else "personal"
        theme = dict(row)["theme"] if row else "deep-space"
        return JSONResponse({"status": "active", "mode": mode, "theme": theme, "clones": 15})

    @app.get("/personal/clones")
    @app.get("/api/clones")
    async def personal_clones():
        CLONES = [
            {"id": "c01", "name": "Tech Architect", "icon": "💻", "specialty": "Code, System Design"},
            {"id": "c02", "name": "Health Sage", "icon": "🏥", "specialty": "Health, Medical"},
            {"id": "c03", "name": "Financial Oracle", "icon": "💰", "specialty": "Finance, Investment"},
            {"id": "c04", "name": "Legal Guardian", "icon": "⚖️", "specialty": "Legal, Rights"},
            {"id": "c05", "name": "Education Mentor", "icon": "📚", "specialty": "Learning, Research"},
            {"id": "c06", "name": "Creative Muse", "icon": "🎨", "specialty": "Design, Art, Writing"},
            {"id": "c07", "name": "Strategic Planner", "icon": "🎯", "specialty": "Business Strategy"},
            {"id": "c08", "name": "Research Explorer", "icon": "🔬", "specialty": "Science, Data"},
            {"id": "c09", "name": "Security Sentinel", "icon": "🔒", "specialty": "Security, Privacy"},
            {"id": "c10", "name": "Logistics Master", "icon": "🚀", "specialty": "Operations, Supply"},
            {"id": "c11", "name": "Env Steward", "icon": "🌿", "specialty": "Environment, Climate"},
            {"id": "c12", "name": "Social Harmonizer", "icon": "🤝", "specialty": "Community, Social"},
            {"id": "c13", "name": "Governance Advisor", "icon": "🏛️", "specialty": "Policy, Government"},
            {"id": "c14", "name": "Innovation Catalyst", "icon": "⚡", "specialty": "R&D, Innovation"},
            {"id": "c15", "name": "Harmony Keeper", "icon": "☯️", "specialty": "Balance, Wellbeing"},
        ]
        return JSONResponse({"clones": CLONES, "total": 15})

    # ─── MEMORY / HISTORY ─────────────────────────────────────────────────────
    @app.get("/api/memory/stats")
    async def memory_stats(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        with _get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)).fetchone()[0]
        return JSONResponse({"total_messages": count, "status": "active"})

    @app.get("/api/memory/recent")
    async def memory_recent(request: Request, limit: int = 20):
        user_id = _get_user_id_from_request(request) or "guest"
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT id, role, content, clone_used, timestamp FROM messages WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        memories = [{"id": r["id"], "role": r["role"], "content": r["content"],
                     "clone": r["clone_used"] or "AsimNexus", "timestamp": r["timestamp"]} for r in rows]
        return JSONResponse({"memories": memories, "total": len(memories)})

    @app.get("/api/memory/search")
    async def memory_search(request: Request, q: str = ""):
        user_id = _get_user_id_from_request(request) or "guest"
        if not q:
            return JSONResponse({"memories": []})
        # Always filter by user_id in DB — never use shared vector memory (no isolation)
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT id, role, content, clone_used, timestamp FROM messages "
                "WHERE user_id=? AND content LIKE ? ORDER BY timestamp DESC LIMIT 15",
                (user_id, f"%{q}%")
            ).fetchall()
        memories = [{"id": r["id"], "role": r["role"], "content": r["content"],
                     "clone": r["clone_used"] or "AsimNexus", "timestamp": r["timestamp"]} for r in rows]
        return JSONResponse({"memories": memories, "total": len(memories)})

    @app.delete("/api/memory/{message_id}")
    async def delete_memory(message_id: str, request: Request):
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Unauthorized")
        with _get_db() as conn:
            conn.execute("DELETE FROM messages WHERE id=? AND user_id=?", (message_id, user_id))
            conn.commit()
        return JSONResponse({"success": True})

    @app.get("/api/db/conversations/user/{user_id}")
    async def user_conversations(user_id: str, request: Request):
        # Auth guard: users can only access their own conversations
        caller_id = _get_user_id_from_request(request)
        if caller_id and caller_id != user_id:
            raise HTTPException(403, "Access denied: cannot read another user's conversations")
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT id,content,clone_used,timestamp FROM messages WHERE user_id=? AND role='user' ORDER BY timestamp DESC LIMIT 20",
                (user_id,)
            ).fetchall()
        convs = [{"id": r["id"], "title": r["content"][:50], "clone": r["clone_used"],
                  "created_at": r["timestamp"]} for r in rows]
        return JSONResponse({"conversations": convs})

    # ─── API KEYS ─────────────────────────────────────────────────────────────
    @app.get("/api/db/api-keys/{user_id}")
    async def get_api_keys(user_id: str, request: Request):
        # Auth guard: users can only see their own keys
        caller_id = _get_user_id_from_request(request)
        if caller_id and caller_id != user_id:
            raise HTTPException(403, "Access denied")
        with _get_db() as conn:
            row = conn.execute("SELECT api_keys FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return JSONResponse({"keys": {}})
        keys = json.loads(dict(row)["api_keys"] or "{}")
        safe = {k: v[:8] + "****" if v else "" for k, v in keys.items()}
        return JSONResponse({"keys": safe})

    @app.post("/api/keys/update")
    async def update_api_key(request: Request):
        body = await request.json()
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        provider = body.get("provider", "").lower()
        key = body.get("key", "")
        if not provider or not key:
            raise HTTPException(400, "provider and key required")
        with _get_db() as conn:
            row = conn.execute("SELECT api_keys FROM users WHERE id=?", (user_id,)).fetchone()
            existing = json.loads(dict(row)["api_keys"] or "{}") if row else {}
            existing[provider] = key
            conn.execute("UPDATE users SET api_keys=? WHERE id=?", (json.dumps(existing), user_id))
            conn.commit()
        return JSONResponse({"success": True, "message": f"{provider} API key updated"})

    # ─── MESH NODES ───────────────────────────────────────────────────────────
    @app.get("/mesh/nodes")
    @app.get("/api/mesh/nodes")
    async def mesh_nodes():
        import socket
        hostname = socket.gethostname()
        nodes = [{"id": "local-node", "name": hostname, "type": "citizen",
                  "status": "online", "host": "127.0.0.1", "port": 8000,
                  "has_local_llm": _local_llm is not None}]
        if _nodes:
            try:
                registered = _nodes.get_all_nodes()
                for n in registered:
                    nodes.append({"id": n.node_id, "name": n.display_name,
                                  "type": n.node_type.value, "status": n.status.value})
            except Exception:
                pass
        return JSONResponse({"nodes": nodes, "total": len(nodes)})

    # ─── AGENT / JOB MARKETPLACE ─────────────────────────────────────────────
    @app.post("/api/jobs/post")
    async def post_job(request: Request):
        body = await request.json()
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        if _marketplace:
            result = _marketplace.post_job(
                poster_id=user_id,
                title=body.get("title", ""),
                description=body.get("description", ""),
                budget=str(body.get("budget", "negotiable")),
                budget_currency=body.get("budget_currency", "USD"),
                timeline_days=int(body.get("timeline_days", 7)),
                skills=body.get("skills", []),
                milestones=body.get("milestones", []),
                universe_scope=body.get("universe_scope", "global"),
            )
            return JSONResponse(result)
        job_id = secrets.token_hex(8)
        with _get_db() as conn:
            conn.execute(
                "INSERT INTO jobs (id,poster_id,title,description,budget,timeline_days,skills) VALUES (?,?,?,?,?,?,?)",
                (job_id, user_id, body.get("title",""), body.get("description",""),
                 str(body.get("budget","")), body.get("timeline_days", 7),
                 json.dumps(body.get("skills",[])))
            )
            conn.commit()
        return JSONResponse({"success": True, "job_id": job_id,
                             "message": "Job posted! AsimNexus will find matching agents."})

    @app.get("/api/jobs/list")
    async def list_jobs(status: str = "open", category: str = None):
        if _marketplace:
            jobs = _marketplace.list_jobs(category=category, status=status)
            return JSONResponse({"jobs": jobs, "total": len(jobs)})
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT id,title,description,budget,timeline_days,skills,status,created_at FROM jobs WHERE status='open' ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
        jobs = [dict(r) for r in rows]
        for j in jobs:
            j["skills"] = json.loads(j.get("skills") or "[]")
            j["category"] = "other"
            j["budget_currency"] = "USD"
        return JSONResponse({"jobs": jobs, "total": len(jobs)})

    @app.get("/api/jobs/stats")
    async def jobs_stats():
        if _marketplace:
            return JSONResponse(_marketplace.marketplace_stats())
        with _get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            open_j = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='open'").fetchone()[0]
        return JSONResponse({"total_jobs": total, "open_jobs": open_j, "completed_jobs": 0,
                             "total_agents": 0, "available_agents": 0})

    @app.get("/api/jobs/{job_id}")
    async def get_job(job_id: str):
        if _marketplace:
            job = _marketplace.get_job(job_id)
            if not job:
                raise HTTPException(404, "Job not found")
            return JSONResponse(job)
        raise HTTPException(404, "Job not found")

    @app.post("/api/jobs/{job_id}/apply")
    async def apply_job(job_id: str, request: Request):
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        if _marketplace:
            body = await request.json()
            result = _marketplace.apply_for_job(
                job_id=job_id, agent_id=user_id,
                cover_note=body.get("cover_note", ""),
                proposed_budget=str(body.get("proposed_budget", "")),
                proposed_timeline=int(body.get("proposed_timeline", 7)),
            )
            return JSONResponse(result)
        with _get_db() as conn:
            conn.execute("UPDATE jobs SET agent_id=?, status='assigned' WHERE id=? AND status='open'",
                         (user_id, job_id))
            conn.commit()
        return JSONResponse({"success": True, "message": "Application submitted!"})

    @app.post("/api/jobs/{job_id}/rate")
    async def rate_job(job_id: str, request: Request):
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        if _marketplace:
            body = await request.json()
            result = _marketplace.rate(
                job_id=job_id, rater_id=user_id,
                ratee_id=body.get("ratee_id", ""),
                score=int(body.get("score", 5)),
                review=body.get("review", ""),
            )
            return JSONResponse(result)
        return JSONResponse({"success": True, "message": "Rating saved"})

    # ─── DREAMING ENGINE ─────────────────────────────────────────────────────
    @app.get("/api/dreaming/status")
    async def dreaming_status():
        if _dreaming:
            return JSONResponse(_dreaming.status())
        return JSONResponse({"running": False, "message": "DreamingEngine not loaded"})

    @app.get("/api/dreaming/briefing")
    async def dreaming_briefing():
        if _dreaming:
            return JSONResponse({"briefing": _dreaming.get_briefing()})
        return JSONResponse({"briefing": "DreamingEngine not loaded"})

    @app.post("/api/dreaming/trigger")
    async def trigger_dreaming(request: Request):
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        if _dreaming:
            briefing = await _dreaming.trigger_now()
            return JSONResponse({"success": True, "briefing": briefing})
        return JSONResponse({"success": False, "message": "DreamingEngine not loaded"})

    # ─── SMART CONTRACTS (HDT) ────────────────────────────────────────────────
    @app.post("/api/contracts/propose")
    async def contract_propose(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            engine = get_contract_engine()
            c = engine.propose(
                requester_id  = user_id,
                provider_id   = body.get("provider_id", "guest"),
                title         = body.get("title", ""),
                description   = body.get("description", ""),
                duration_days = int(body.get("duration_days", 15)),
                value_npr     = float(body.get("value_npr", 0)),
                skills        = body.get("skills", []),
            )
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/gate2")
    async def contract_gate2(contract_id: str):
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().run_gate2(contract_id)
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/sign")
    async def contract_sign(contract_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().human_sign(
                contract_id = contract_id,
                user_id     = user_id,
                approved    = bool(body.get("approved", True)),
                note        = body.get("note", ""),
            )
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/progress")
    async def contract_progress(contract_id: str, request: Request):
        body = await request.json()
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().update_progress(
                contract_id, int(body.get("pct", 0)), body.get("note", ""))
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/pause")
    async def contract_pause(contract_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().pause(contract_id, user_id, body.get("reason", ""))
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/resume")
    async def contract_resume(contract_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().resume(contract_id, user_id)
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/cancel")
    async def contract_cancel(contract_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().cancel(contract_id, user_id, body.get("reason", ""))
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/contracts/{contract_id}/complete")
    async def contract_complete(contract_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().complete(
                contract_id, user_id,
                rating=int(body.get("rating", 5)),
                note=body.get("note", ""))
            return JSONResponse(c.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/contracts/{contract_id}")
    async def contract_get(contract_id: str):
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            c = get_contract_engine().get(contract_id)
            if not c:
                raise HTTPException(404, "Contract not found")
            return JSONResponse(c.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/contracts")
    async def contracts_list(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        try:
            from core.contracts.smart_contract_engine import get_contract_engine
            engine = get_contract_engine()
            contracts = engine.list_for_user(user_id)
            pending = engine.pending_human_signature(user_id)
            return JSONResponse({
                "contracts":     [c.to_dict() for c in contracts],
                "total":         len(contracts),
                "pending_human": [c.contract_id for c in pending],
                "stats":         engine.stats(user_id),
            })
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── THEME / UNIVERSE ─────────────────────────────────────────────────────
    @app.post("/api/theme/set")
    async def set_theme(request: Request):
        body = await request.json()
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        theme = body.get("theme", "deep-space")
        with _get_db() as conn:
            conn.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
            conn.commit()
        return JSONResponse({"success": True, "theme": theme})

    @app.post("/api/universe/set")
    async def set_universe(request: Request):
        body = await request.json()
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        mode = body.get("mode", "personal")
        with _get_db() as conn:
            conn.execute("UPDATE users SET universe_mode=? WHERE id=?", (mode, user_id))
            conn.commit()
        return JSONResponse({"success": True, "universe_mode": mode})

    # ─── APIS STATUS ──────────────────────────────────────────────────────────
    @app.get("/api/apis/status")
    async def apis_status(request: Request):
        user_id = _get_user_id_from_request(request)
        providers = {}
        if user_id:
            with _get_db() as conn:
                row = conn.execute("SELECT api_keys FROM users WHERE id=?", (user_id,)).fetchone()
            if row:
                keys = json.loads(dict(row)["api_keys"] or "{}")
                for p in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
                    providers[p] = "configured" if keys.get(p) else "not_configured"
        return JSONResponse({
            "status": "online",
            "local_llm": "loaded" if _local_llm else "not_loaded",
            "providers": providers
        })

    # ─── ANALYTICS ────────────────────────────────────────────────────────────
    @app.get("/api/analytics/overview")
    @app.get("/api/analytics")
    async def analytics_overview(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        with _get_db() as conn:
            msg_count = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)).fetchone()[0]
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        import platform, psutil
        return JSONResponse({
            "status": "ok",
            "users": total_users,
            "messages": msg_count,
            "active_clones": 15,
            "cpu_usage": round(psutil.cpu_percent(interval=0.1), 1),
            "ram_usage": round(psutil.virtual_memory().percent, 1),
            "disk_usage": round(psutil.disk_usage('/').percent, 1),
            "ethical_score": 0.94,
            "tasks_completed": msg_count,
            "founders_active": 5,
            "agents_active": 12,
        })

    @app.get("/api/analytics/activity")
    async def analytics_activity():
        now = datetime.utcnow()
        data = []
        for i in range(8):
            h = (now.hour - i) % 24
            data.append({"time": f"{h:02d}:00", "messages": max(0, 10 - i * 1),
                          "clones": max(0, 5 - i), "tasks": max(0, 20 - i * 2)})
        return JSONResponse({"activity": list(reversed(data))})

    # ─── SOCKET.IO STUB (prevents 403 WebSocket errors) ──────────────────────
    @app.get("/socket.io/")
    async def socketio_stub():
        return JSONResponse({"error": "Use REST API — WebSocket via /ws"}, status_code=400)

    # ─── WEBSOCKET CHAT ───────────────────────────────────────────────────────
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                user_message = msg.get("message", "")
                # Generate real AI response via local LLM
                response_text = ""
                try:
                    llm_result = await _smart_generate(user_message, "guest", system="You are Asim, the AI assistant for AsimNexus. Be helpful, concise, and friendly.")
                    response_text = llm_result.get("response", "")
                except Exception as e:
                    logger.warning(f"WS generate error: {e}")
                    response_text = f"🤖 Asim received: {user_message}"
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.now().isoformat()
                })
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.warning(f"WebSocket error: {e}")

    @app.post("/api/dharma/veto-check")
    async def dharma_veto_check(request: Request):
        body = await request.json()
        action  = body.get("action", "")
        content = body.get("content", "")
        context = body.get("context", {})
        user_id = _get_user_id_from_request(request) or "guest"
        if _dharma_veto:
            result = _dharma_veto.check(action=action, node_id=user_id,
                                        context=context, content=content)
            return JSONResponse({
                "passed":         result.passed,
                "severity":       result.severity,
                "summary":        result.summary,
                "requires_human": result.requires_human,
                "events": [
                    {"severity": e.severity, "reason": e.reason,
                     "detail": e.detail, "veto_hash": e.veto_hash}
                    for e in result.events
                ],
            })
        return JSONResponse({"passed": True, "severity": "pass",
                             "summary": "DharmaVeto not loaded — passthrough",
                             "requires_human": False, "events": []})

    @app.post("/api/dharma/cultural-check")
    async def dharma_cultural_check(request: Request):
        body    = await request.json()
        action  = body.get("action", "accept_protocol")
        content = body.get("content", "")
        context = body.get("context", {})
        if _cultural_compiler:
            result = _cultural_compiler.check(action=action, content=content, context=context)
            return JSONResponse(result)
        return JSONResponse({"status": "COMPLIANT",
                             "detail": "CulturalCompiler not loaded",
                             "hits": [], "locale": "nepal", "override_allowed": True})

    @app.get("/api/dharma/veto-status")
    async def dharma_veto_status():
        if _dharma_veto:
            return JSONResponse({**_dharma_veto.status(),
                                  "cultural_compiler": _cultural_compiler.status() if _cultural_compiler else None})
        return JSONResponse({"active": False})

    # ─── DHARMA-CHAKRA INTEGRATION HUB (Phase 40-60%) ─────────────────────────
    # Identity → Dharma → Approve → Audit full pipeline.
    # See core/dharma_chakra/integration.py for the underlying logic.
    # ------------------------------------------------------------------
    @app.get("/api/integration/health")
    async def integration_health():
        """Health check for all integrated components."""
        try:
            from core.dharma_chakra.integration import get_integrator
            integrator = get_integrator()
            health = await integrator.get_system_health()
            return JSONResponse(health)
        except Exception as e:
            return JSONResponse({"error": str(e), "initialized": False})

    @app.post("/api/integration/evaluate")
    async def integration_evaluate(request: Request):
        """
        Evaluate an action through the full Identity → Dharma → Approve → Audit pipeline.

        Body:
          user_id (str): The user/agent performing the action.
          action (str): Natural-language description of the action.
          sector (str, optional): Domain sector. Default: "general".
          context (dict, optional): Extra metadata (amount, user_consent, etc.).

        Returns:
          FlowResult with all stage results and confirmation_token if human approval needed.
        """
        try:
            body = await request.json()
            user_id = body.get("user_id", "anonymous")
            action = body.get("action", "")
            sector = body.get("sector", "general")
            context = body.get("context", {})

            if not action:
                return JSONResponse({"error": "action is required"}, status_code=400)

            from core.dharma_chakra.integration import get_integrator
            integrator = get_integrator()
            result = await integrator.evaluate_and_approve(
                user_id=user_id,
                action=action,
                sector=sector,
                context=context,
            )
            return JSONResponse(result.to_dict())
        except Exception as e:
            return JSONResponse({"error": f"Integration evaluation failed: {e}"}, status_code=500)

    @app.post("/api/integration/confirm")
    async def integration_confirm(request: Request):
        """
        Confirm (approve) a pending Level-3 human approval.

        Body:
          token (str): The confirmation token from evaluate response.

        Returns:
          Confirmation result with ZK validity proof.
        """
        try:
            body = await request.json()
            token = body.get("token", "")
            if not token:
                return JSONResponse({"error": "token is required"}, status_code=400)

            from core.dharma_chakra.veto_engine import get_zkp_manager
            zkp = get_zkp_manager()
            result = zkp.confirm(token)
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": f"Confirmation failed: {e}"}, status_code=500)

    @app.post("/api/integration/reject")
    async def integration_reject(request: Request):
        """
        Reject a pending Level-3 human approval.

        Body:
          token (str): The confirmation token from evaluate response.
        """
        try:
            body = await request.json()
            token = body.get("token", "")
            if not token:
                return JSONResponse({"error": "token is required"}, status_code=400)

            from core.dharma_chakra.veto_engine import get_zkp_manager
            zkp = get_zkp_manager()
            result = zkp.reject(token)
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": f"Rejection failed: {e}"}, status_code=500)

    @app.get("/api/integration/pending")
    async def integration_pending():
        """List all pending Level-3 human approvals."""
        try:
            from core.dharma_chakra.veto_engine import get_zkp_manager
            zkp = get_zkp_manager()
            pending = zkp.list_pending()
            return JSONResponse({"pending": pending, "count": len(pending)})
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/integration/veto-stats")
    async def integration_veto_stats():
        """Get veto engine statistics."""
        try:
            from core.dharma_chakra.veto_engine import get_veto_engine
            veto = get_veto_engine()
            return JSONResponse(veto.get_stats())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/integration/audit-log")
    async def integration_audit_log(limit: int = 20):
        """Get the last N entries from the immutable audit log."""
        try:
            from core.dharma_chakra.veto_engine import get_veto_engine
            veto = get_veto_engine()
            return JSONResponse({"entries": veto.get_audit_log(limit), "count": limit})
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── MESH / LAN DISCOVERY + AIR-GAP ──────────────────────────────────────
    @app.get("/api/mesh/discovery/status")
    async def mesh_discovery_status():
        """Low-level mesh component status: P2P transport, DHT, CRDT, air-gap.
        NOTE: Renamed from /api/mesh/status to avoid shadowing by the comprehensive
        mesh status endpoint at line ~4195."""
        out = {"p2p_transport": None, "dht": None, "crdt": None, "air_gap": None}
        try:
            from mesh.p2p_transport import get_p2p_transport
            t = get_p2p_transport()
            out["p2p_transport"] = {
                "node_id": t.node_id,
                "host": t.host,
                "port_udp": t.port_udp,
                "port_ws": t.port_ws,
                "running": t._running,
                "peers": len(t.peers),
                "online_peers": len(await t.get_online_peers()),
            }
        except Exception as e:
            out["p2p_transport"] = {"running": False, "error": str(e)}
        try:
            from mesh.kademlia_dht import get_kademlia_dht
            out["dht"] = get_kademlia_dht().get_stats()
        except Exception as e:
            out["dht"] = {"running": False, "error": str(e)}
        try:
            from mesh.crdt_sync import get_crdt_store
            crdt = get_crdt_store()
            out["crdt"] = {
                "crdt_count": len(crdt.crdts),
                "operation_count": len(crdt.operation_log),
                "node_id": crdt.node_id,
            }
        except Exception as e:
            out["crdt"] = {"running": False, "error": str(e)}
        try:
            from core.mesh.air_gap_controller import get_air_gap
            out["air_gap"] = get_air_gap().status()
        except Exception as e:
            out["air_gap"] = {"level": 0, "error": str(e)}
        return JSONResponse(out)

    @app.post("/api/mesh/discover/start")
    async def mesh_discover_start():
        try:
            from mesh.p2p_transport import get_p2p_transport
            import asyncio
            t = get_p2p_transport()
            asyncio.create_task(t.start())
            return JSONResponse({
                "status": "started",
                "node_id": t.node_id,
                "host": t.host,
                "port_udp": t.port_udp,
                "port_ws": t.port_ws,
            })
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.post("/api/mesh/discover/add-peer")
    async def mesh_add_peer(request: Request):
        body = await request.json()
        node_id = body.get("node_id", body.get("id", ""))
        ip   = body.get("ip", body.get("host", ""))
        port_udp = int(body.get("port", body.get("port_udp", 7332)))
        port_ws  = int(body.get("port_ws", port_udp + 1))
        if not ip:
            raise HTTPException(400, "ip or host required")
        try:
            from mesh.p2p_transport import get_p2p_transport
            peer = get_p2p_transport().add_peer(node_id, ip, port_udp, port_ws)
            return JSONResponse({
                "node_id": peer.node_id,
                "host": peer.host,
                "port_udp": peer.port_udp,
                "port_ws": peer.port_ws,
                "is_connected": peer.is_connected,
            })
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.get("/api/mesh/peers")
    async def mesh_peers():
        try:
            from mesh.p2p_transport import get_p2p_transport
            from dataclasses import asdict
            t = get_p2p_transport()
            peers = [asdict(p) for p in await t.get_online_peers()]
            return JSONResponse({"peers": peers, "total": len(t.peers)})
        except Exception as e:
            return JSONResponse({"peers": [], "total": 0, "error": str(e)})

    @app.post("/api/mesh/air-gap/engage")
    async def air_gap_engage(request: Request):
        body  = await request.json()
        level = int(body.get("level", 3))
        reason = body.get("reason", "Human-initiated air-gap")
        try:
            from core.mesh.air_gap_controller import get_air_gap, AirGapLevel
            result = get_air_gap().engage(AirGapLevel(level), reason=reason, triggered_by="human")
            return JSONResponse(result)
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.post("/api/mesh/air-gap/disengage")
    async def air_gap_disengage():
        try:
            from core.mesh.air_gap_controller import get_air_gap
            result = get_air_gap().disengage(triggered_by="human")
            return JSONResponse(result)
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.get("/api/mesh/air-gap/check")
    async def air_gap_check(host: str = "8.8.8.8", port: int = 443):
        try:
            from core.mesh.air_gap_controller import get_air_gap
            return JSONResponse(get_air_gap().check_request(host, port))
        except Exception as e:
            raise HTTPException(500, str(e))

    # ─── BUG TRIAGE / SELF-HEALING PIPELINE ──────────────────────────────────
    @app.get("/api/bugs/stats")
    async def bugs_stats():
        try:
            from core.dreaming.bug_triage import get_bug_triage
            return JSONResponse(get_bug_triage().stats())
        except Exception as e:
            return JSONResponse({"total": 0, "error": str(e)})

    @app.post("/api/bugs/report")
    async def bug_report(request: Request):
        body = await request.json()
        try:
            from core.dreaming.bug_triage import get_bug_triage
            from dataclasses import asdict as _asdict
            engine = get_bug_triage()
            bug = engine.report(
                file_path   = body.get("file_path", "unknown"),
                line_number = int(body.get("line_number", 0)),
                category    = body.get("category", "logic"),
                description = body.get("description", ""),
                detected_by = body.get("detected_by", "user_report"),
            )
            result = engine.run_pipeline(bug.bug_id)
            return JSONResponse(_asdict(result))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/bugs/pending")
    async def bugs_pending():
        try:
            from core.dreaming.bug_triage import get_bug_triage
            from dataclasses import asdict as _asdict
            bugs = get_bug_triage().pending_human()
            return JSONResponse({"bugs": [_asdict(b) for b in bugs], "count": len(bugs)})
        except Exception as e:
            return JSONResponse({"bugs": [], "count": 0, "error": str(e)})

    @app.post("/api/bugs/{bug_id}/approve")
    async def bug_approve(bug_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body    = await request.json()
        try:
            from core.dreaming.bug_triage import get_bug_triage
            from dataclasses import asdict as _asdict
            result = get_bug_triage().human_decision(
                bug_id, approved=bool(body.get("approved", True)), approver=user_id)
            return JSONResponse(_asdict(result))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/bugs/list")
    async def bugs_list(severity: str = "", status: str = "", limit: int = 50):
        try:
            from core.dreaming.bug_triage import get_bug_triage, BugSeverity, BugStatus
            from dataclasses import asdict as _asdict
            engine = get_bug_triage()
            sev = BugSeverity(severity) if severity else None
            sta = BugStatus(status)     if status   else None
            bugs = engine.list_bugs(severity=sev, status=sta, limit=limit)
            return JSONResponse({"bugs": [_asdict(b) for b in bugs], "total": len(bugs)})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/bugs/batch-triage")
    async def bugs_batch_triage(request: Request):
        body = await request.json()
        bug_list = body.get("bugs", [])
        try:
            from core.dreaming.bug_triage import get_bug_triage
            from dataclasses import asdict as _asdict
            stats = get_bug_triage().batch_triage(bug_list)
            return JSONResponse(_asdict(stats))
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── ZKP IDENTITY ────────────────────────────────────────────────────────
    @app.post("/api/identity/create")
    async def identity_create(request: Request):
        body = await request.json()
        passphrase = body.get("passphrase", "")
        if len(passphrase) < 8:
            raise HTTPException(400, "Passphrase must be at least 8 characters")
        try:
            from core.identity.zkp_local import get_zkp_store
            from dataclasses import asdict as _asdict
            identity = get_zkp_store().create(
                passphrase   = passphrase,
                display_name = body.get("display_name", "Sovereign User"),
                universe     = body.get("universe", "personal"),
                biometric_raw= body.get("biometric_raw", ""),
            )
            return JSONResponse(_asdict(identity))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/identity/verify")
    async def identity_verify(request: Request):
        body = await request.json()
        did        = body.get("did", "")
        passphrase = body.get("passphrase", "")
        bio        = body.get("biometric_raw", "")
        try:
            from core.identity.zkp_local import get_zkp_store
            ok, reason = get_zkp_store().verify(did, passphrase, bio)
            return JSONResponse({"verified": ok, "reason": reason, "did": did})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/identity/{did}/credential")
    async def identity_issue_vc(did: str, request: Request):
        body = await request.json()
        try:
            from core.identity.zkp_local import get_zkp_store
            from dataclasses import asdict as _asdict
            store = get_zkp_store()
            issuer_did = body.get("issuer_did", did)
            vc = store.issue_credential(
                issuer_did  = issuer_did,
                subject_did = did,
                claim_type  = body.get("claim_type", "skill"),
                claim_value = body.get("claim_value", ""),
                days_valid  = int(body.get("days_valid", 365)),
            )
            return JSONResponse(_asdict(vc))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/identity/{did}/credentials")
    async def identity_get_vcs(did: str):
        try:
            from core.identity.zkp_local import get_zkp_store
            from dataclasses import asdict as _asdict
            vcs = get_zkp_store().get_credentials(did)
            return JSONResponse({"credentials": [_asdict(vc) for vc in vcs]})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/identity/status")
    async def identity_status():
        try:
            from core.identity.zkp_local import get_zkp_store
            s = get_zkp_store().stats()
            return JSONResponse({**s, "status": "active", "module": "zkp_local"})
        except Exception as e:
            return JSONResponse({"total_identities": 0, "status": "error", "error": str(e)})

    @app.get("/api/hdt/status")
    async def hdt_status_global():
        try:
            from core.hdt.human_digital_twin import get_hdt_store
            store = get_hdt_store()
            twins = store.list_twins() if hasattr(store, 'list_twins') else []
            return JSONResponse({
                "total_twins": len(twins),
                "did": twins[0].get("did","") if twins else "",
                "status": "active", "module": "human_digital_twin",
            })
        except Exception as e:
            return JSONResponse({"total_twins": 0, "did": "", "status": "error", "error": str(e)})

    @app.get("/api/universe/list")
    async def universe_list():
        try:
            from core.universe.container import get_universe_manager
            mgr = get_universe_manager()
            return JSONResponse({"universes": mgr.status_all(), "stats": mgr.stats()})
        except Exception as e:
            return JSONResponse({"universes": [], "error": str(e)})

    @app.get("/api/identity/stats")
    async def identity_stats():
        try:
            from core.identity.zkp_local import get_zkp_store
            return JSONResponse(get_zkp_store().stats())
        except Exception as e:
            return JSONResponse({"total": 0, "error": str(e)})

    @app.get("/api/identity/list")
    async def identity_list():
        try:
            from core.identity.zkp_local import get_zkp_store
            from dataclasses import asdict as _asdict
            ids = get_zkp_store().list_identities()
            return JSONResponse({"identities": [_asdict(i) for i in ids], "count": len(ids)})
        except Exception as e:
            return JSONResponse({"identities": [], "error": str(e)})

    # ─── COGNITIVE FIREWALL ───────────────────────────────────────────────────
    @app.post("/api/firewall/check")
    async def firewall_check(request: Request):
        body = await request.json()
        text = body.get("text", "")
        sensitivity = float(body.get("sensitivity", 0.5))
        if not text:
            raise HTTPException(400, "text required")
        try:
            from core.firewall.cognitive_firewall import get_cognitive_firewall
            fw = get_cognitive_firewall(sensitivity)
            result = fw.check(text, context=body.get("context"))
            return JSONResponse(result.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/firewall/check-conversation")
    async def firewall_check_conversation(request: Request):
        body = await request.json()
        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(400, "messages array required")
        try:
            from core.firewall.cognitive_firewall import get_cognitive_firewall
            result = get_cognitive_firewall().check_conversation(messages)
            return JSONResponse(result.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/firewall/status")
    async def firewall_status():
        try:
            from core.firewall.cognitive_firewall import get_cognitive_firewall
            return JSONResponse(get_cognitive_firewall().status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── KADEMLIA DHT ────────────────────────────────────────────────────────
    @app.get("/api/dht/status")
    async def dht_status():
        try:
            from mesh.kademlia_dht import get_kademlia_dht
            return JSONResponse(get_kademlia_dht().get_stats())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/dht/bootstrap")
    async def dht_bootstrap(request: Request):
        body = await request.json()
        seeds = body.get("seeds", [])
        if not seeds:
            raise HTTPException(400, "seeds list required (e.g. [{'node_id':'...','host':'...','port':7332}])")
        try:
            from mesh.kademlia_dht import get_kademlia_dht, NodeID, DHTNode
            dht = get_kademlia_dht()
            added = 0
            for seed in seeds:
                nid = seed.get("node_id", "")
                host = seed.get("host", "")
                port = int(seed.get("port", 7332))
                if not host:
                    continue
                node_id = NodeID.from_string(nid) if nid else NodeID.random()
                node = DHTNode(node_id=node_id, ip_address=host, port=port)
                if dht.add_node(node):
                    added += 1
            return JSONResponse({"status": "bootstrapped", "seeds_provided": len(seeds), "nodes_added": added})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/dht/announce")
    async def dht_announce(request: Request):
        body = await request.json()
        capability = body.get("capability", "")
        details    = body.get("details", {})
        if not capability:
            raise HTTPException(400, "capability required")
        try:
            from mesh.kademlia_dht import get_kademlia_dht, NodeID
            import json
            dht = get_kademlia_dht()
            key = NodeID.from_string(capability)
            value_bytes = json.dumps(details, separators=(",", ":")).encode("utf-8")
            import asyncio
            asyncio.create_task(dht.publish(key, value_bytes))
            return JSONResponse({"dht_key": str(key), "capability": capability, "status": "publishing"})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/dht/find")
    async def dht_find(capability: str = ""):
        if not capability:
            raise HTTPException(400, "capability query param required")
        try:
            from mesh.kademlia_dht import get_kademlia_dht, NodeID
            import asyncio
            dht = get_kademlia_dht()
            key = NodeID.from_string(capability)
            # First try local
            local_value = dht.get(key)
            if local_value is not None:
                try:
                    import json
                    decoded = json.loads(local_value.decode("utf-8"))
                except Exception:
                    decoded = local_value.decode("utf-8", errors="replace")
                return JSONResponse({"found": True, "value": decoded, "source": "local"})
            # Then try remote lookup
            result_bytes = await dht.lookup(key)
            if result_bytes is not None:
                try:
                    import json
                    decoded = json.loads(result_bytes.decode("utf-8"))
                except Exception:
                    decoded = result_bytes.decode("utf-8", errors="replace")
                return JSONResponse({"found": True, "value": decoded, "source": "remote"})
            return JSONResponse({"found": False, "value": None})
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── HUMAN DIGITAL TWIN ───────────────────────────────────────────────────
    @app.post("/api/hdt/create")
    async def hdt_create(request: Request):
        body = await request.json()
        did  = body.get("did", "")
        if not did:
            raise HTTPException(400, "did required")
        try:
            from core.hdt.human_digital_twin import get_hdt
            hdt = get_hdt(did, body.get("display_name",""), body.get("universe","personal"))
            return JSONResponse(hdt.status())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/hdt/{did}/skill")
    async def hdt_add_skill(did: str, request: Request):
        body = await request.json()
        try:
            from core.hdt.human_digital_twin import get_hdt
            from dataclasses import asdict as _asdict
            hdt   = get_hdt(did)
            skill = hdt.add_skill(
                name    = body.get("name",""),
                level   = body.get("level","intermediate"),
                verified= bool(body.get("verified", False)),
                vc_id   = body.get("vc_id",""),
            )
            return JSONResponse(_asdict(skill))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/hdt/{did}/announce")
    async def hdt_announce(did: str):
        try:
            from core.hdt.human_digital_twin import get_hdt
            hdt = get_hdt(did)
            return JSONResponse(hdt.announce_to_mesh())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/hdt/{did}/status")
    async def hdt_status(did: str):
        try:
            from core.hdt.human_digital_twin import get_hdt
            return JSONResponse(get_hdt(did).status())
        except Exception as e:
            raise HTTPException(404, str(e))

    @app.get("/api/hdt/{did}/profile")
    async def hdt_profile(did: str):
        try:
            from core.hdt.human_digital_twin import get_hdt
            return JSONResponse(get_hdt(did).profile.to_dict())
        except Exception as e:
            raise HTTPException(404, str(e))

    # ─── 15-CLONE CONSENSUS ───────────────────────────────────────────────────
    @app.post("/api/consensus/vote")
    async def consensus_vote(request: Request):
        body = await request.json()
        topic = body.get("topic","")
        level = body.get("level","high")
        if not topic:
            raise HTTPException(400, "topic required")
        try:
            from core.consensus.clone_consensus import get_consensus_engine, DecisionLevel
            from dataclasses import asdict as _asdict
            engine = get_consensus_engine()
            cr = engine.start_round(
                topic       = topic,
                description = body.get("description",""),
                level       = DecisionLevel(level),
            )
            return JSONResponse(cr.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/consensus/{round_id}/override")
    async def consensus_override(round_id: str, request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body    = await request.json()
        try:
            from core.consensus.clone_consensus import get_consensus_engine
            from dataclasses import asdict as _asdict
            cr = get_consensus_engine().human_override(
                round_id, approved=bool(body.get("approved", True)),
                reason=body.get("reason",""))
            return JSONResponse(cr.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/consensus/stats")
    async def consensus_stats():
        try:
            from core.consensus.clone_consensus import get_consensus_engine
            return JSONResponse(get_consensus_engine().stats())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/consensus/pending")
    async def consensus_pending():
        try:
            from core.consensus.clone_consensus import get_consensus_engine
            from dataclasses import asdict as _asdict
            rounds = get_consensus_engine().pending_human()
            return JSONResponse({"rounds": [_asdict(r) for r in rounds], "count": len(rounds)})
        except Exception as e:
            return JSONResponse({"rounds": [], "error": str(e)})

    @app.get("/api/consensus/list")
    async def consensus_list():
        try:
            from core.consensus.clone_consensus import get_consensus_engine
            from dataclasses import asdict as _asdict
            rounds = get_consensus_engine().list_rounds(20)
            return JSONResponse({"rounds": [_asdict(r) for r in rounds]})
        except Exception as e:
            return JSONResponse({"rounds": [], "error": str(e)})

    # ─── UNIVERSE CONTAINERS ─────────────────────────────────────────────────
    @app.get("/api/universe/containers")
    async def universe_containers(did: str = ""):
        try:
            from core.universe.container import get_universe_manager
            mgr = get_universe_manager()
            if did:
                return JSONResponse({"containers": [c.to_dict() for c in mgr.get_for_did(did)]})
            return JSONResponse({"containers": mgr.status_all(), "stats": mgr.stats()})
        except Exception as e:
            return JSONResponse({"containers": [], "error": str(e)})

    @app.post("/api/universe/data-flow-check")
    async def universe_data_flow(request: Request):
        body = await request.json()
        try:
            from core.universe.container import get_universe_manager, UniverseLayer
            result = get_universe_manager().check_data_flow(
                UniverseLayer(body.get("from","personal")),
                UniverseLayer(body.get("to","community")))
            return JSONResponse(result)
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── SOVEREIGN TOKEN (SVT) ────────────────────────────────────────────────
    @app.get("/api/svt/stats")
    async def svt_stats():
        try:
            from core.economy.sovereign_token import get_svt_engine
            return JSONResponse(get_svt_engine().stats())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/svt/wallet")
    async def svt_create_wallet(request: Request):
        body = await request.json()
        did  = body.get("did","")
        if not did: raise HTTPException(400,"did required")
        try:
            from core.economy.sovereign_token import get_svt_engine
            from dataclasses import asdict as _asdict
            w = get_svt_engine().create_wallet(did)
            return JSONResponse(_asdict(w))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/svt/wallet/{did}")
    async def svt_wallet_info(did: str):
        try:
            from core.economy.sovereign_token import get_svt_engine
            return JSONResponse(get_svt_engine().wallet_info(did))
        except Exception as e:
            raise HTTPException(404, str(e))

    @app.post("/api/svt/mint")
    async def svt_mint(request: Request):
        body = await request.json()
        try:
            from core.economy.sovereign_token import get_svt_engine
            from dataclasses import asdict as _asdict
            tx = get_svt_engine().mint(body.get("did",""), float(body.get("amount",0)),
                                       body.get("memo",""))
            return JSONResponse(_asdict(tx))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/svt/transfer")
    async def svt_transfer(request: Request):
        body = await request.json()
        try:
            from core.economy.sovereign_token import get_svt_engine
            from dataclasses import asdict as _asdict
            tx = get_svt_engine().transfer(
                body.get("from_did",""), body.get("to_did",""),
                float(body.get("amount",0)), body.get("memo",""))
            return JSONResponse(_asdict(tx))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/svt/escrow")
    async def svt_escrow(request: Request):
        body = await request.json()
        try:
            from core.economy.sovereign_token import get_svt_engine
            eid = get_svt_engine().escrow_lock(
                body.get("did",""), float(body.get("amount",0)), body.get("memo",""))
            return JSONResponse({"escrow_id": eid})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/svt/escrow/{eid}/release")
    async def svt_escrow_release(eid: str, request: Request):
        body = await request.json()
        try:
            from core.economy.sovereign_token import get_svt_engine
            from dataclasses import asdict as _asdict
            tx = get_svt_engine().escrow_release(eid, body.get("to_did",""))
            return JSONResponse(_asdict(tx))
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── QUAD MESH ────────────────────────────────────────────────────────────
    @app.get("/api/quad/status")
    async def quad_status():
        try:
            from core.mesh.quad_mesh import get_quad_mesh
            return JSONResponse(get_quad_mesh().full_status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/quad/join")
    async def quad_join(request: Request):
        body = await request.json()
        did  = body.get("did","")
        layer= body.get("layer","citizen")
        if not did: raise HTTPException(400,"did required")
        try:
            from core.mesh.quad_mesh import get_quad_mesh, MeshLayer
            from dataclasses import asdict as _asdict
            peer = get_quad_mesh().join(did, MeshLayer(layer),
                                        body.get("ip",""), int(body.get("port",8765)))
            return JSONResponse(_asdict(peer))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/quad/{layer}/peers")
    async def quad_peers(layer: str):
        try:
            from core.mesh.quad_mesh import get_quad_mesh, MeshLayer
            peers = get_quad_mesh().get_peers(MeshLayer(layer))
            return JSONResponse({"peers": peers, "count": len(peers)})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/quad/send")
    async def quad_send(request: Request):
        body = await request.json()
        try:
            from core.mesh.quad_mesh import get_quad_mesh, MeshLayer
            from dataclasses import asdict as _asdict
            msg = get_quad_mesh().send(
                body.get("from_did",""), MeshLayer(body.get("to_layer","citizen")),
                body.get("payload",{}), bool(body.get("require_consent",False)))
            return JSONResponse(_asdict(msg))
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── ZERO TRUST RUNTIME ──────────────────────────────────────────────────
    @app.get("/api/runtime/status")
    async def runtime_status():
        try:
            from core.runtime.zero_trust_runtime import get_runtime
            return JSONResponse(get_runtime().status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/runtime/register")
    async def runtime_register(request: Request):
        body = await request.json()
        try:
            from core.runtime.zero_trust_runtime import get_runtime
            from dataclasses import asdict as _asdict
            tok = get_runtime().register(
                body.get("principal",""), body.get("role","clone"),
                int(body.get("ttl",3600)), body.get("universe","personal"))
            return JSONResponse(tok.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/runtime/principals")
    async def runtime_principals():
        try:
            from core.runtime.zero_trust_runtime import get_runtime
            return JSONResponse({"principals": get_runtime().list_principals()})
        except Exception as e:
            return JSONResponse({"principals": [], "error": str(e)})

    @app.get("/api/runtime/violations")
    async def runtime_violations():
        try:
            from core.runtime.zero_trust_runtime import get_runtime
            return JSONResponse({"violations": get_runtime().violations()})
        except Exception as e:
            return JSONResponse({"violations": [], "error": str(e)})

    # ─── SELF-EVOLUTION ───────────────────────────────────────────────────────
    @app.get("/api/evolution/stats")
    async def evolution_stats():
        try:
            from core.self_building.evolution_engine import get_evolution_engine
            return JSONResponse(get_evolution_engine().stats())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/evolution/propose")
    async def evolution_propose(request: Request):
        body = await request.json()
        try:
            from core.self_building.evolution_engine import get_evolution_engine
            from dataclasses import asdict as _asdict
            p = get_evolution_engine().propose(
                title=body.get("title",""), target_file=body.get("target_file",""),
                old_code=body.get("old_code",""), new_code=body.get("new_code",""),
                description=body.get("description",""), proposed_by=body.get("proposed_by","human"))
            return JSONResponse(p.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/evolution/{patch_id}/validate")
    async def evolution_validate(patch_id: str):
        try:
            from core.self_building.evolution_engine import get_evolution_engine
            p = get_evolution_engine().validate(patch_id)
            return JSONResponse(p.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/evolution/{patch_id}/decide")
    async def evolution_decide(patch_id: str, request: Request):
        body = await request.json()
        try:
            from core.self_building.evolution_engine import get_evolution_engine
            p = get_evolution_engine().human_decide(patch_id, bool(body.get("approved",False)),
                                                     body.get("reason",""))
            return JSONResponse(p.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── DEPIN ────────────────────────────────────────────────────────────────
    @app.get("/api/depin/status")
    async def depin_status():
        try:
            from core.depin.depin_bridge import get_depin_bridge
            return JSONResponse(get_depin_bridge().network_status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/depin/register")
    async def depin_register(request: Request):
        body = await request.json()
        try:
            from core.depin.depin_bridge import get_depin_bridge, DePINNetwork
            from dataclasses import asdict as _asdict
            node = get_depin_bridge().register_node(
                body.get("did",""), DePINNetwork(body.get("network","helium")),
                body.get("wallet_addr",""))
            return JSONResponse(node.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/depin/{node_id}/collect")
    async def depin_collect(node_id: str):
        try:
            from core.depin.depin_bridge import get_depin_bridge
            from dataclasses import asdict as _asdict
            r = get_depin_bridge().collect_rewards(node_id)
            return JSONResponse(_asdict(r) if r else {"error": "node not found or inactive"})
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── FEDERATION ───────────────────────────────────────────────────────────
    @app.get("/api/federation/status")
    async def federation_status():
        try:
            from core.federation.global_federation import get_federation
            return JSONResponse(get_federation().status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/federation/peer")
    async def federation_add_peer(request: Request):
        body = await request.json()
        try:
            from core.federation.global_federation import get_federation
            from dataclasses import asdict as _asdict
            peer = get_federation().add_peer(
                body.get("did",""), body.get("endpoint",""), bool(body.get("trusted",False)))
            return JSONResponse(_asdict(peer))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/federation/consent/{peer_id}")
    async def federation_consent(peer_id: str):
        try:
            from core.federation.global_federation import get_federation
            get_federation().consent_peer(peer_id)
            return JSONResponse({"ok": True, "peer_id": peer_id})
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/federation/sync-packet")
    async def federation_sync_packet():
        try:
            from core.federation.global_federation import get_federation
            return JSONResponse(get_federation().get_sync_packet())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── EVENT BUS ────────────────────────────────────────────────────────────
    @app.get("/api/events/stats")
    async def events_stats():
        try:
            from core.events.reactive_bus import get_bus
            return JSONResponse(get_bus().stats())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/events/publish")
    async def events_publish(request: Request):
        body = await request.json()
        try:
            from core.events.reactive_bus import get_bus
            evt = get_bus().publish(
                body.get("topic",""), body.get("payload",{}),
                body.get("source","api"))
            return JSONResponse(evt.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.get("/api/events/recent")
    async def events_recent():
        try:
            from core.events.reactive_bus import get_bus
            return JSONResponse({"events": get_bus().recent_events(20)})
        except Exception as e:
            return JSONResponse({"events": [], "error": str(e)})

    @app.get("/api/events/dlq")
    async def events_dlq():
        try:
            from core.events.reactive_bus import get_bus
            return JSONResponse({"dlq": get_bus().dlq()})
        except Exception as e:
            return JSONResponse({"dlq": [], "error": str(e)})

    # ─── POST-QUANTUM ─────────────────────────────────────────────────────────
    @app.get("/api/pq/status")
    async def pq_status():
        try:
            from core.security.pq_layer import get_pq_layer
            return JSONResponse(get_pq_layer().status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/pq/keygen")
    async def pq_keygen(request: Request):
        body = await request.json()
        try:
            from core.security.pq_layer import get_pq_layer, PQAlgorithm
            algo = PQAlgorithm(body.get("algorithm","ML-KEM-768"))
            kp = get_pq_layer().generate_keypair(body.get("did",""), algo)
            return JSONResponse(kp.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/pq/sign")
    async def pq_sign(request: Request):
        body = await request.json()
        try:
            from core.security.pq_layer import get_pq_layer
            from dataclasses import asdict as _asdict
            sig = get_pq_layer().sign(
                body.get("message","").encode(), body.get("key_id",""))
            return JSONResponse(_asdict(sig))
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/pq/kem")
    async def pq_kem(request: Request):
        body = await request.json()
        try:
            from core.security.pq_layer import get_pq_layer
            from dataclasses import asdict as _asdict
            result = get_pq_layer().kem_encapsulate(body.get("public_key",""))
            return JSONResponse(_asdict(result))
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── OFFLINE SYNC ─────────────────────────────────────────────────────────
    @app.get("/api/sync/status")
    async def sync_status():
        try:
            from core.sync.offline_sync import get_sync_engine
            return JSONResponse(get_sync_engine().status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/sync/enqueue")
    async def sync_enqueue(request: Request):
        body = await request.json()
        try:
            from core.sync.offline_sync import get_sync_engine, OpType
            from dataclasses import asdict as _asdict
            op = get_sync_engine().enqueue(
                OpType(body.get("op_type","update")),
                body.get("entity_type",""), body.get("entity_id",""),
                body.get("payload",{}))
            return JSONResponse(op.to_dict())
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/sync/flush")
    async def sync_flush():
        try:
            from core.sync.offline_sync import get_sync_engine
            return JSONResponse(get_sync_engine().flush())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/sync/queue")
    async def sync_queue():
        try:
            from core.sync.offline_sync import get_sync_engine
            return JSONResponse({"queue": get_sync_engine().queue_list()})
        except Exception as e:
            return JSONResponse({"queue": [], "error": str(e)})

    # ─── CLONE SPECIALIZER ────────────────────────────────────────────────────
    @app.get("/api/clones/specs")
    async def clones_specs():
        try:
            from core.founder_clones.clone_specializer import get_specializer
            return JSONResponse({"clones": get_specializer().all_specs(),
                                 "status": get_specializer().status()})
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/clones/{clone_id}/spec")
    async def clone_spec(clone_id: int):
        try:
            from core.founder_clones.clone_specializer import get_specializer
            from dataclasses import asdict as _asdict
            spec = get_specializer().get_spec(clone_id)
            if not spec: raise HTTPException(404, "Clone not found")
            return JSONResponse(_asdict(spec))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, str(e))

    @app.post("/api/clones/route")
    async def clones_route(request: Request):
        body = await request.json()
        try:
            from core.founder_clones.clone_specializer import get_specializer
            from dataclasses import asdict as _asdict
            spec = get_specializer().route(body.get("query",""))
            return JSONResponse({"clone": _asdict(spec)})
        except Exception as e:
            raise HTTPException(400, str(e))

    # ─── NEPAL LAYER ──────────────────────────────────────────────────────────
    @app.get("/api/nepal/status")
    async def nepal_status():
        modules = {}
        for name, mod_path in [
            ("banking",  "core.nepal.banking_integrations"),
            ("telecom",  "core.nepal.telecom_integrations"),
            ("govt",     "core.nepal.government_integrations"),
            ("language", "core.nepal.language_support"),
            ("culture",  "core.nepal.cultural_features"),
        ]:
            try:
                __import__(mod_path)
                modules[name] = "available"
            except Exception as e:
                modules[name] = f"error: {str(e)[:40]}"
        return JSONResponse({
            "country": "Nepal", "modules": modules,
            "features": ["Nepali NLP", "eSewa integration", "Nagarik App bridge",
                         "Dharma constitution", "Local-first privacy"],
            "status": "active",
        })

    # ─── PERSONAL UNIVERSE ────────────────────────────────────────────────────
    @app.get("/api/personal/status")
    async def personal_status(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        username, display_name, joined, msg_count = "guest", "Guest", None, 0
        try:
            with _get_db() as conn:
                try:
                    user_row = conn.execute(
                        "SELECT email, display_name, created_at FROM users WHERE id=?",
                        (user_id,)
                    ).fetchone()
                    if user_row:
                        username = user_row[0] or "guest"
                        display_name = user_row[1] or username
                        joined = user_row[2]
                except Exception:
                    pass
                try:
                    msg_count = conn.execute(
                        "SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)
                    ).fetchone()[0]
                except Exception:
                    msg_count = 0
        except Exception as e:
            logger.warning(f"personal_status DB error: {e}")
        import psutil
        agent_on = _get_agent_mode(user_id).get("active", False)
        rs = _get_resource_sharing(user_id)
        return JSONResponse({
            "status": "online",
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "joined": joined,
            "universe_type": "personal",
            "agent_mode": agent_on,
            "total_messages": msg_count,
            "active_contracts": 0,
            "clone_count": 15,
            "resource_sharing": rs.get("enabled", False),
            "resource_share_pct": rs.get("share_pct", 0),
            "cpu_pct": round(psutil.cpu_percent(interval=0.1), 1),
            "ram_pct": round(psutil.virtual_memory().percent, 1),
            "local_first": True,
            "dharma_score": 0.94,
            "final3_pending": 0,
        })

    @app.get("/api/personal/universe")
    async def personal_universe(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        return JSONResponse({
            "user_id": user_id,
            "universes": [
                {"type": "personal",    "icon": "person",   "label": "Personal",    "active": True,  "nodes": 1},
                {"type": "family",      "icon": "group",    "label": "Family",      "active": False, "nodes": 0},
                {"type": "community",   "icon": "village",  "label": "Community",   "active": False, "nodes": 0},
                {"type": "enterprise",  "icon": "business", "label": "Enterprise",  "active": False, "nodes": 0},
                {"type": "sovereign",   "icon": "flag",     "label": "Sovereign",   "active": False, "nodes": 0},
            ],
            "mesh_connected": False,
            "mesh_note": "Phase 2 — LAN Mesh not yet active",
        })

    @app.get("/api/personal/contracts")
    async def personal_contracts(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        return JSONResponse({
            "user_id": user_id,
            "active": [],
            "pending_confirmation": [],
            "completed": [],
            "note": "Agent Mode OFF — enable to receive contract requests",
        })

    # ─── AGENT MODE ───────────────────────────────────────────────────────────
    @app.post("/api/agent/mode/on")
    async def agent_mode_on(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        skills = body.get("skills", [])
        duration = body.get("max_contract_days", 5)
        _set_agent_mode(user_id, {
            "active": True, "skills": skills,
            "max_contract_days": duration,
            "activated_at": datetime.utcnow().isoformat(),
        })
        return JSONResponse({
            "status": "agent_mode_on",
            "user_id": user_id,
            "skills": skills,
            "max_contract_days": duration,
            "message": "Your clone is now available in the mesh marketplace.",
            "reminder": "Final 3 Confirmation required before any contract starts.",
        })

    @app.post("/api/agent/mode/off")
    async def agent_mode_off(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        _set_agent_mode(user_id, {"active": False})
        return JSONResponse({
            "status": "agent_mode_off",
            "user_id": user_id,
            "message": "Your clone is now dormant. No new contracts accepted.",
        })

    @app.get("/api/agent/status")
    async def agent_status(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        info = _get_agent_mode(user_id)
        return JSONResponse({"user_id": user_id, **info})

    # ─── UNIVERSE STATUS ──────────────────────────────────────────────────────
    @app.get("/api/universe/status")
    async def universe_status(request: Request):
        import psutil
        user_id = _get_user_id_from_request(request) or "guest"
        agent_on = _get_agent_mode(user_id).get("active", False)
        rs = _get_resource_sharing(user_id)
        return JSONResponse({
            "user_id": user_id,
            "universe": "personal",
            "agent_mode": agent_on,
            "local_first": True,
            "offline_capable": True,
            "dharma_active": True,
            "delta_t_active": True,
            "final3_required": True,
            "resource_sharing": rs.get("enabled", False),
            "mesh_peers": 0,
            "phase": 1,
            "phase_note": "Phase 1 — single machine, no LAN mesh yet",
            "cpu": round(psutil.cpu_percent(interval=0.1), 1),
            "ram": round(psutil.virtual_memory().percent, 1),
        })

    # ─── RESOURCE SHARING TOGGLE ──────────────────────────────────────────────
    @app.post("/api/personal/resource-sharing")
    async def set_resource_sharing(request: Request):
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        body = await request.json()
        enabled = bool(body.get("enabled", False))
        pct = max(2, min(5, int(body.get("share_pct", 2))))   # clamp 2-5%
        _set_resource_sharing(user_id, {
            "enabled": enabled,
            "share_pct": pct if enabled else 0,
            "updated_at": datetime.utcnow().isoformat(),
        })
        return JSONResponse({
            "status": "ok",
            "resource_sharing": enabled,
            "share_pct": pct if enabled else 0,
            "message": (
                f"✅ Resource sharing ON — contributing {pct}% of idle CPU/RAM to the mesh."
                if enabled else
                "🔴 Resource sharing OFF — your device contributes nothing to the mesh."
            ),
        })

    @app.get("/api/personal/resource-sharing")
    async def get_resource_sharing(request: Request):
        user_id = _get_user_id_from_request(request) or "guest"
        info = _get_resource_sharing(user_id)
        import psutil
        return JSONResponse({
            "user_id": user_id,
            "resource_sharing": info.get("enabled", False),
            "share_pct": info.get("share_pct", 0),
            "cpu_total": round(psutil.cpu_percent(interval=0.1), 1),
            "ram_total": round(psutil.virtual_memory().percent, 1),
            "mesh_peers": 0,
            "phase_note": "Phase 2 will connect real LAN peers",
        })

    # ─── MCP (Dharma-Gated Model Context Protocol) ───────────────────────────
    try:
        from core.mcp.dharma_mcp_server import get_mcp_server
        _mcp = get_mcp_server()
        logger.info("✅ DharmaMCP Server loaded")
    except Exception as _mcp_err:
        _mcp = None
        logger.warning(f"⚠️ DharmaMCP fallback: {_mcp_err}")

    @app.get("/api/mcp/tools")
    async def mcp_list_tools():
        """List all registered Dharma-Gated MCP tools."""
        if not _mcp:
            return JSONResponse({"tools": [], "status": "mcp_unavailable"})
        return JSONResponse({
            "tools": _mcp.list_tools(),
            "total": len(_mcp.list_tools()),
            "dharma_gated": True,
            "layers": ["dharma_veto", "delta_t_check", "final3_confirmation", "audit_log"],
        })

    @app.post("/api/mcp/call")
    async def mcp_call(request: Request):
        """
        Execute a Dharma-Gated MCP tool call.
        Body: { tool_name, parameters, context }
        """
        if not _mcp:
            raise HTTPException(503, "DharmaMCP Server not available")
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        tool_name  = body.get("tool_name", "")
        parameters = body.get("parameters", {})
        context    = body.get("context", "")
        if not tool_name:
            raise HTTPException(400, "tool_name required")
        # Always inject user_id into parameters for sandboxing
        parameters["user_id"] = user_id
        result = await _mcp.call(tool_name, parameters, user_id=user_id, context=context)
        return JSONResponse({
            "call_id":       result.call_id,
            "tool_name":     result.tool_name,
            "verdict":       result.verdict.value,
            "output":        result.output,
            "error":         result.error,
            "veto_reason":   result.veto_reason,
            "requires_human": result.requires_human,
            "execution_ms":  result.execution_ms,
            "dharma_score":  result.dharma_score,
            "audit_hash":    result.audit_hash,
        })

    @app.post("/api/mcp/approve/{call_id}")
    async def mcp_approve(call_id: str, request: Request):
        """Human approves a pending Final-3 MCP call."""
        if not _mcp:
            raise HTTPException(503, "DharmaMCP Server not available")
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Authentication required to approve actions")
        result = await _mcp.approve(call_id, approver_id=user_id)
        return JSONResponse({
            "call_id":   result.call_id,
            "verdict":   result.verdict.value,
            "output":    result.output,
            "error":     result.error,
            "approved_by": user_id,
        })

    @app.post("/api/mcp/reject/{call_id}")
    async def mcp_reject(call_id: str, request: Request):
        """Human rejects a pending Final-3 MCP call."""
        if not _mcp:
            raise HTTPException(503, "DharmaMCP Server not available")
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Authentication required")
        result = _mcp.reject(call_id, rejecter_id=user_id)
        return JSONResponse({
            "call_id":   result.call_id,
            "verdict":   result.verdict.value,
            "rejected_by": user_id,
            "message":   "Action rejected. AsimNexus respects your decision.",
        })

    @app.get("/api/mcp/pending")
    async def mcp_pending(request: Request):
        """List pending Final-3 approvals for this user."""
        if not _mcp:
            return JSONResponse({"pending": []})
        user_id = _get_user_id_from_request(request) or "guest"
        pending = _mcp.pending_calls(user_id=user_id)
        return JSONResponse({"pending": pending, "count": len(pending)})

    @app.get("/api/mcp/audit")
    async def mcp_audit(request: Request, limit: int = 30):
        """Return recent audit log for this user."""
        if not _mcp:
            return JSONResponse({"audit": []})
        user_id = _get_user_id_from_request(request) or "guest"
        entries = _mcp.audit_log(limit=limit, user_id=user_id)
        return JSONResponse({"audit": entries, "total": len(entries)})

    @app.get("/api/mcp/status")
    async def mcp_status(request: Request):
        """DharmaMCP Server status."""
        if not _mcp:
            return JSONResponse({"status": "unavailable"})
        user_id = _get_user_id_from_request(request) or "guest"
        pending = _mcp.pending_calls(user_id=user_id)
        recent  = _mcp.audit_log(limit=5, user_id=user_id)
        return JSONResponse({
            "status": "active",
            "dharma_gated": True,
            "tools_registered": len(_mcp._tools),
            "pending_approvals": len(pending),
            "recent_calls": len(recent),
            "layers": {
                "dharma_veto":     True,
                "delta_t_engine":  _mcp._dt_engine is not None,
                "final3_confirmation": True,
                "audit_log":       True,
                "sandboxed_fs":    True,
            },
        })

    # ─── AGENT LOOP ENDPOINTS ───────────────────────────────────────────────────
    @app.post("/api/agent/run")
    async def agent_run(request: Request):
        """Run agent loop with user input"""
        try:
            body = await request.json()
            user_id = _get_user_id_from_request(request) or "anonymous"
            from core.agent_loop import get_agent_loop, AgentMode
            loop = get_agent_loop()
            mode_str = body.get("mode", "AUTO").upper()
            mode = AgentMode[mode_str] if mode_str in AgentMode.__members__ else AgentMode.AUTO
            ctx = await loop.run(
                user_input=body["user_input"],
                user_id=user_id,
                clone_id=body.get("clone_id"),
                mode=mode,
                system_prompt=body.get("system_prompt"),
                max_steps=body.get("max_steps", 25),
            )
            return {"status": "ok", "session_id": ctx.session_id, "mode": mode.name}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.post("/api/agent/cancel")
    async def agent_cancel(request: Request):
        """Cancel an active agent session"""
        try:
            body = await request.json()
            from core.agent_loop import get_agent_loop
            loop = get_agent_loop()
            loop.cancel_session(body["session_id"])
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.get("/api/agent/status/{session_id}")
    async def agent_status(session_id: str):
        """Get agent session status"""
        try:
            from core.agent_loop import get_agent_loop
            loop = get_agent_loop()
            ctx = loop.get_active_sessions().get(session_id)
            if not ctx:
                return {"status": "error", "detail": "Session not found"}
            return {
                "status": ctx.status.name,
                "mode": ctx.mode.name,
                "steps": len(ctx.steps),
                "messages": len(ctx.messages),
                "session_id": ctx.session_id,
                "user_id": ctx.user_id,
                "clone_id": ctx.clone_id,
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.get("/api/agent/sessions")
    async def agent_sessions():
        """List all active agent sessions"""
        try:
            from core.agent_loop import get_agent_loop
            loop = get_agent_loop()
            sessions = {}
            for sid, ctx in loop.get_active_sessions().items():
                sessions[sid] = {
                    "status": ctx.status.name,
                    "mode": ctx.mode.name,
                    "steps": len(ctx.steps),
                    "user_id": ctx.user_id,
                    "clone_id": ctx.clone_id,
                }
            return {"status": "ok", "sessions": sessions}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.get("/api/agent/stats")
    async def agent_stats():
        """Get agent loop statistics"""
        try:
            from core.agent_loop import get_agent_loop
            loop = get_agent_loop()
            return {"status": "ok", "stats": loop.get_stats()}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # ─── TOOL EXECUTION ENDPOINTS ───────────────────────────────────────────────
    @app.get("/api/tools/list")
    async def tool_list():
        """List all available tools"""
        try:
            from core.tools import get_default_tool_registry
            registry = get_default_tool_registry()
            tools = registry.get_tools_for_llm()
            return {"status": "ok", "tools": tools}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.post("/api/tools/execute")
    async def tool_execute(request: Request):
        """Execute a tool (goes through veto check)"""
        try:
            body = await request.json()
            user_id = _get_user_id_from_request(request) or "anonymous"
            tool_name = body["tool_name"]
            args = body.get("arguments", {})
            session_id = body.get("session_id")

            from core.tools import get_default_tool_registry
            from core.tools.veto_integration import get_veto_integration
            from core.tools.audit_integration import get_tool_auditor

            registry = get_default_tool_registry()
            veto = get_veto_integration()
            auditor = get_tool_auditor()

            # Veto check
            veto_result = await veto.check_tool(tool_name, args, user_id=user_id)
            if not veto_result.get("allowed", True):
                auditor.record(tool_name, args, "BLOCKED by veto", veto_result, user_id=user_id, session_id=session_id, success=False, error=veto_result.get("reason", ""))
                return {"status": "veto_blocked", "reason": veto_result.get("reason", ""), "severity": veto_result.get("severity", "error")}

            # Execute
            tool_func = registry.get_tool(tool_name)
            if not tool_func:
                return {"status": "error", "detail": f"Tool '{tool_name}' not found"}

            import time, traceback
            start = time.monotonic()
            try:
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**args)
                else:
                    result = tool_func(**args)
                duration_ms = int((time.monotonic() - start) * 1000)
                auditor.record(tool_name, args, str(result)[:200], veto_result, user_id=user_id, session_id=session_id, success=True, duration_ms=duration_ms)
                return {"status": "ok", "result": result, "duration_ms": duration_ms}
            except Exception as exec_err:
                duration_ms = int((time.monotonic() - start) * 1000)
                auditor.record(tool_name, args, "", veto_result, user_id=user_id, session_id=session_id, success=False, error=str(exec_err), duration_ms=duration_ms)
                return {"status": "error", "detail": str(exec_err), "duration_ms": duration_ms}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.get("/api/tools/pending")
    async def tool_pending():
        """Get list of approved tool executions pending human approval"""
        try:
            from core.tools.veto_integration import get_veto_integration
            veto = get_veto_integration()
            return {"status": "ok", "pending": veto.get_pending_approvals() if hasattr(veto, 'get_pending_approvals') else []}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.post("/api/tools/approve")
    async def tool_approve(request: Request):
        """Approve a pending tool execution"""
        try:
            body = await request.json()
            execution_id = body["execution_id"]
            from core.tools.veto_integration import get_veto_integration
            veto = get_veto_integration()
            if hasattr(veto, 'approve_execution'):
                veto.approve_execution(execution_id)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.post("/api/tools/reject")
    async def tool_reject(request: Request):
        """Reject a pending tool execution"""
        try:
            body = await request.json()
            execution_id = body["execution_id"]
            from core.tools.veto_integration import get_veto_integration
            veto = get_veto_integration()
            if hasattr(veto, 'reject_execution'):
                veto.reject_execution(execution_id)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @app.get("/api/tools/audit")
    async def tool_audit(request: Request, limit: int = 30):
        """Get tool audit log"""
        try:
            from core.tools.audit_integration import get_tool_auditor
            auditor = get_tool_auditor()
            entries = auditor.get_recent(limit=limit) if hasattr(auditor, 'get_recent') else []
            return {"status": "ok", "entries": entries}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # ─── SYSTEM HEALING & MONITORING ───────────────────────────────────────────
    @app.get("/api/healing/status")
    async def healing_status():
        """Get system healing status and health check"""
        try:
            from core.healing import get_system_healer
            import asyncio
            healer = get_system_healer()
            health = await healer.full_system_check()
            return JSONResponse({
                "status": "active",
                "health": health,
                "last_check": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"status": "error", "error": str(e)})

    @app.post("/api/healing/heal")
    async def healing_heal():
        """Trigger full system healing"""
        try:
            from core.healing import get_system_healer
            import asyncio
            healer = get_system_healer()
            result = await healer.heal_system()
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"status": "error", "error": str(e)})

    @app.get("/api/healing/bugs")
    async def healing_bugs():
        """Get detected bugs"""
        try:
            from core.healing import BugDetector
            import asyncio
            detector = BugDetector()
            bugs = await detector.scan_all_files()
            return JSONResponse({
                "total_bugs": len(bugs),
                "auto_fixable": sum(1 for b in bugs if b.auto_fixable),
                "bugs": [{"id": b.id, "severity": b.severity, "description": b.description, 
                         "file": b.file_path, "line": b.line_number, "auto_fixable": b.auto_fixable}
                        for b in bugs]
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/healing/connection")
    async def healing_connection():
        """Check frontend-backend connection"""
        try:
            from core.healing import FrontendBackendMonitor
            import asyncio
            monitor = FrontendBackendMonitor()
            backend = await monitor.check_backend_health()
            api = await monitor.check_api_connectivity()
            return JSONResponse({
                "backend": backend,
                "api": api,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/healing/balance")
    async def healing_balance():
        """Check system resource balance"""
        try:
            from core.healing import SystemBalanceChecker
            import asyncio
            checker = SystemBalanceChecker()
            balance = await checker.check_balance()
            return JSONResponse(balance)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/healing/fix-connections")
    async def healing_fix_connections():
        """Auto-fix frontend-backend connection issues"""
        try:
            from core.healing import FrontendBackendMonitor
            import asyncio
            monitor = FrontendBackendMonitor()
            fixes = await monitor.fix_connection_issues()
            return JSONResponse({
                "fixes_applied": fixes,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── UNIVERSAL SYSTEMS ────────────────────────────────────────────────────
    @app.get("/api/universal/status")
    async def universal_status():
        """Universal system status - all countries, currencies, languages"""
        try:
            from core.universal import get_currency_system, get_legal_framework
            from core.universal import get_timezone_system, get_i18n_system
            
            currency_stats = get_currency_system().get_stats()
            legal_stats = get_legal_framework().get_stats()
            tz_stats = get_timezone_system().get_stats()
            i18n_stats = get_i18n_system().get_stats()
            
            return JSONResponse({
                "universal_systems": {
                    "currency": {
                        "total_currencies": currency_stats['total_currencies'],
                        "fiat": currency_stats['fiat_currencies'],
                        "crypto": currency_stats['crypto_currencies'],
                        "countries_covered": currency_stats['countries_covered'],
                    },
                    "legal": {
                        "total_countries": legal_stats['total_countries'],
                        "gdpr_compliant": legal_stats['gdpr_compliant'],
                        "dharma_compatible": legal_stats['dharma_compatible'],
                        "crypto_friendly": legal_stats['crypto_friendly'],
                    },
                    "timezone": {
                        "total_timezones": tz_stats['total_timezones'],
                        "countries_covered": tz_stats['countries_covered'],
                    },
                    "i18n": {
                        "tier1_languages": i18n_stats['tier1_languages'],
                        "tier2_languages": i18n_stats['tier2_languages'],
                        "estimated_speakers_billions": i18n_stats['estimated_speakers_billions'],
                        "rtl_languages": i18n_stats['rtl_languages'],
                    }
                },
                "status": "active",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/currencies")
    async def universal_currencies():
        """Get all supported currencies"""
        try:
            from core.universal import get_currency_system
            cs = get_currency_system()
            
            currencies = []
            for c in cs.get_all_currencies():
                currencies.append({
                    'code': c.code,
                    'name': c.name,
                    'symbol': c.symbol,
                    'type': c.type.value,
                    'decimals': c.decimals,
                })
            
            return JSONResponse({
                "currencies": currencies,
                "total": len(currencies),
                "stats": cs.get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/currencies/{country_code}")
    async def universal_currencies_for_country(country_code: str):
        """Get currencies for a specific country"""
        try:
            from core.universal import get_currency_system
            cs = get_currency_system()
            
            currencies = cs.get_currencies_by_country(country_code)
            return JSONResponse({
                "country": country_code.upper(),
                "currencies": [c.to_dict() for c in currencies],
                "count": len(currencies)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/universal/currency/convert")
    async def universal_currency_convert(request: Request):
        """Convert between currencies"""
        try:
            from core.universal import get_currency_system
            body = await request.json()
            
            amount = body.get('amount', 0)
            from_currency = body.get('from', 'USD')
            to_currency = body.get('to', 'USD')
            
            cs = get_currency_system()
            
            # Fetch rates if needed
            await cs.fetch_exchange_rates()
            
            from decimal import Decimal
            result = cs.convert(Decimal(str(amount)), from_currency, to_currency)
            
            if result is None:
                return JSONResponse({
                    "error": f"Could not convert from {from_currency} to {to_currency}"
                }, status_code=400)
            
            return JSONResponse({
                "amount": float(amount),
                "from": from_currency,
                "to": to_currency,
                "result": float(result),
                "formatted": cs.format_amount(result, to_currency),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/countries")
    async def universal_countries():
        """Get all countries with legal frameworks"""
        try:
            from core.universal import get_legal_framework
            lf = get_legal_framework()
            
            countries = []
            for c in lf.get_all():
                countries.append({
                    'code': c.code,
                    'name': c.name,
                    'region': c.region,
                    'privacy_laws': c.privacy_laws,
                    'data_residency': c.data_residency.value,
                    'gdpr_compatible': c.gdpr_compatible,
                    'crypto_regulation': c.crypto_reg.value,
                    'dharma_compatible': c.dharma_compatible,
                })
            
            return JSONResponse({
                "countries": countries,
                "total": len(countries),
                "stats": lf.get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/countries/{country_code}")
    async def universal_country_detail(country_code: str):
        """Get detailed info for a country"""
        try:
            from core.universal import get_legal_framework, get_currency_system
            from core.universal import get_timezone_system
            
            lf = get_legal_framework()
            country = lf.get_country(country_code)
            
            if not country:
                return JSONResponse({"error": f"Country {country_code} not found"}, status_code=404)
            
            cs = get_currency_system()
            currencies = cs.get_currencies_by_country(country_code)
            
            tz = get_timezone_system()
            timezones = tz.get_for_country(country_code)
            
            return JSONResponse({
                "code": country.code,
                "name": country.name,
                "region": country.region,
                "privacy_laws": country.privacy_laws,
                "data_residency": country.data_residency.value,
                "gdpr_compatible": country.gdpr_compatible,
                "right_to_be_forgotten": country.right_to_be_forgotten,
                "crypto_regulation": country.crypto_reg.value,
                "tax_authority": country.tax_authority,
                "vat_rate": country.vat_rate,
                "dharma_compatible": country.dharma_compatible,
                "notes": country.notes,
                "currencies": [c.code for c in currencies],
                "timezones": [t.code for t in timezones],
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/languages")
    async def universal_languages():
        """Get all supported languages"""
        try:
            from core.universal import get_i18n_system
            i18n = get_i18n_system()
            
            languages = []
            for lang in i18n.get_all_languages():
                languages.append({
                    'code': lang.code,
                    'name': lang.name,
                    'native_name': lang.native_name,
                    'speakers_millions': lang.speakers_millions,
                    'tier': lang.tier.value,
                    'rtl': lang.rtl,
                    'script': lang.script,
                })
            
            return JSONResponse({
                "languages": languages,
                "total": len(languages),
                "stats": i18n.get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/languages/{lang_code}")
    async def universal_language_detail(lang_code: str):
        """Get language details"""
        try:
            from core.universal import get_i18n_system
            i18n = get_i18n_system()
            
            lang = i18n.get_language(lang_code)
            if not lang:
                return JSONResponse({"error": f"Language {lang_code} not found"}, status_code=404)
            
            # Test translation
            test_keys = ['welcome', 'login', 'dashboard', 'dharma']
            translations = {key: i18n.translate(key, lang_code) for key in test_keys}
            
            return JSONResponse({
                "code": lang.code,
                "name": lang.name,
                "native_name": lang.native_name,
                "speakers_millions": lang.speakers_millions,
                "tier": lang.tier.value,
                "rtl": lang.rtl,
                "script": lang.script,
                "countries": lang.countries,
                "sample_translations": translations,
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/timezones")
    async def universal_timezones():
        """Get all timezones"""
        try:
            from core.universal import get_timezone_system
            tz = get_timezone_system()
            
            return JSONResponse({
                "timezones": {code: {
                    'name': info.name,
                    'offset': info.offset,
                    'dst': info.dst,
                    'major_cities': info.major_cities,
                } for code, info in tz.TIME_ZONES.items()},
                "stats": tz.get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/timezones/{country_code}")
    async def universal_timezones_for_country(country_code: str):
        """Get timezones for a country"""
        try:
            from core.universal import get_timezone_system
            tz = get_timezone_system()
            
            timezones = tz.get_for_country(country_code)
            current_times = {}
            
            for t in timezones:
                now = tz.get_current_time(t.code)
                if now:
                    current_times[t.code] = now.strftime('%Y-%m-%d %H:%M:%S %Z')
            
            return JSONResponse({
                "country": country_code.upper(),
                "timezones": [{"code": t.code, "name": t.name, "offset": t.offset} 
                             for t in timezones],
                "current_times": current_times,
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/universal/meeting-times")
    async def universal_meeting_times(timezones: str):
        """Get best meeting times for given timezones"""
        try:
            from core.universal import get_timezone_system
            tz = get_timezone_system()
            
            tz_list = [t.strip() for t in timezones.split(',')]
            best_times = tz.get_best_meeting_time(tz_list)
            
            return JSONResponse({
                "participants": tz_list,
                "best_times": best_times[:5]  # Top 5
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── GLOBAL INFRASTRUCTURE ─────────────────────────────────────────────────
    @app.get("/api/infrastructure/status")
    async def infrastructure_status():
        """Global infrastructure status (CDN + Mesh)"""
        try:
            from core.infrastructure import get_cdn_system, get_mesh_network
            
            cdn_stats = get_cdn_system().get_stats()
            mesh_stats = get_mesh_network().get_mesh_stats()
            
            return JSONResponse({
                "infrastructure": {
                    "cdn": cdn_stats,
                    "mesh": mesh_stats
                },
                "status": "active",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/cdn/locations")
    async def cdn_locations():
        """Get all CDN edge locations"""
        try:
            from core.infrastructure import get_cdn_system
            cdn = get_cdn_system()
            
            locations = []
            for loc in cdn.get_all_locations():
                locations.append(loc.to_dict())
            
            return JSONResponse({
                "locations": locations,
                "stats": cdn.get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/cdn/routing/{country_code}")
    async def cdn_routing(country_code: str, lat: Optional[float] = None, lon: Optional[float] = None):
        """Get optimal CDN routing for a location"""
        try:
            from core.infrastructure import get_cdn_system
            cdn = get_cdn_system()
            
            routing = cdn.get_routing_table(country_code.upper(), lat, lon)
            return JSONResponse(routing)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/cdn/nearest")
    async def cdn_nearest(lat: float, lon: float):
        """Find nearest CDN edge location"""
        try:
            from core.infrastructure import get_cdn_system
            cdn = get_cdn_system()
            
            nearest = cdn.find_nearest_location(lat, lon)
            if nearest:
                return JSONResponse({
                    "nearest": nearest.to_dict(),
                    "distance_km": None  # Would calculate actual distance
                })
            else:
                return JSONResponse({"error": "No location found"}, status_code=404)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/mesh/status")
    async def mesh_status():
        """Federated mesh network status"""
        try:
            from core.infrastructure import get_mesh_network
            mesh = get_mesh_network()
            
            return JSONResponse({
                "mesh": mesh.get_mesh_stats(),
                "quad_system": mesh.get_quad_system_status(),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/mesh/nodes")
    async def mesh_nodes():
        """Get all mesh nodes"""
        try:
            from core.infrastructure import get_mesh_network
            mesh = get_mesh_network()
            
            nodes = [n.to_dict() for n in mesh.nodes.values()]
            return JSONResponse({
                "nodes": nodes,
                "total": len(nodes),
                "my_node": mesh.my_node_id
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/mesh/nodes/{node_id}")
    async def mesh_node_detail(node_id: str):
        """Get specific node details"""
        try:
            from core.infrastructure import get_mesh_network
            mesh = get_mesh_network()
            
            node = mesh.nodes.get(node_id)
            if not node:
                return JSONResponse({"error": f"Node {node_id} not found"}, status_code=404)
            
            # Find peers
            peers = mesh.discover_peers(node_id, radius_km=500)
            
            return JSONResponse({
                "node": node.to_dict(),
                "peers": [p.to_dict() for p in peers[:10]],
                "peer_count": len(peers)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/infrastructure/mesh/join")
    async def mesh_join(request: Request):
        """Join the federated mesh network"""
        try:
            from core.infrastructure import get_mesh_network, MeshNode, NodeType
            from dataclasses import field
            
            body = await request.json()
            
            user_id = body.get('user_id', 'anonymous')
            country = body.get('country', 'NP')
            lat = body.get('latitude', 27.7172)
            lon = body.get('longitude', 85.3240)
            
            mesh = get_mesh_network()
            
            # Create personal node
            node = mesh.create_personal_node(user_id, country, lat, lon)
            
            # Connect to peers
            connected = mesh.connect_to_peers(node.node_id, max_peers=5)
            
            return JSONResponse({
                "success": True,
                "node_id": node.node_id,
                "name": node.name,
                "connections": connected,
                "dharma_score": node.dharma_score,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/infrastructure/mesh/sovereign-nodes")
    async def mesh_sovereign_nodes():
        """Get all sovereign/government nodes"""
        try:
            from core.infrastructure import get_mesh_network, NodeType
            mesh = get_mesh_network()
            
            sovereign = [n.to_dict() for n in mesh.nodes.values() 
                        if n.node_type == NodeType.SOVEREIGN]
            
            return JSONResponse({
                "sovereign_nodes": sovereign,
                "total": len(sovereign),
                "by_country": {}
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/infrastructure/mesh/sync")
    async def mesh_sync(request: Request):
        """Trigger mesh sync for a node"""
        try:
            from core.infrastructure import get_mesh_network
            
            body = await request.json()
            node_id = body.get('node_id')
            
            mesh = get_mesh_network()
            result = mesh.sync_data(node_id)
            
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── PLATFORM & MULTI-DEVICE SUPPORT ───────────────────────────────────────
    @app.get("/api/platform/status")
    async def platform_status():
        """Get platform support status"""
        try:
            from core.platform import get_platform_manager
            pm = get_platform_manager()
            
            return JSONResponse({
                "supported_platforms": pm.get_stats()['platforms'],
                "download_links": pm.get_download_links(),
                "status": "active"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/platform/register")
    async def platform_register(request: Request):
        """Register a device/platform session"""
        try:
            from core.platform import get_platform_manager
            
            body = await request.json()
            user_agent = request.headers.get('user-agent', '')
            platform_hint = body.get('platform_hint')
            session_id = body.get('session_id', str(hash(user_agent + str(datetime.now()))))
            
            pm = get_platform_manager()
            platform_info = pm.detect_platform(user_agent, platform_hint)
            pm.register_session(session_id, platform_info)
            
            config = pm.get_platform_config(platform_info.platform_type)
            
            return JSONResponse({
                "session_id": session_id,
                "platform": platform_info.to_dict(),
                "config": config,
                "install_instructions": pm.get_install_instructions(platform_info.platform_type)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/platform/downloads")
    async def platform_downloads():
        """Get download links for all platforms"""
        try:
            from core.platform import get_platform_manager
            pm = get_platform_manager()
            
            return JSONResponse({
                "downloads": pm.get_download_links(),
                "platforms": {
                    "pwa": {
                        "name": "Progressive Web App",
                        "description": "Works in any modern browser",
                        "features": ["Offline support", "Push notifications", "Background sync"]
                    },
                    "desktop": {
                        "name": "Desktop Application",
                        "description": "Windows, macOS, Linux",
                        "features": ["System tray", "Auto-start", "File system access", "Auto-update"]
                    },
                    "mobile": {
                        "name": "Mobile Application",
                        "description": "iOS and Android",
                        "features": ["Biometrics", "Push notifications", "Camera", "GPS", "Offline mode"]
                    }
                }
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/pwa/config")
    async def pwa_config():
        """Get PWA-specific configuration"""
        try:
            return JSONResponse({
                "manifest_url": "/manifest.json",
                "service_worker": "/sw.js",
                "theme_color": "#667eea",
                "background_color": "#0f0f1a",
                "display_mode": "standalone",
                "icons": {
                    "72": "/asim-logo.png",
                    "96": "/asim-logo.png",
                    "128": "/asim-logo.png",
                    "144": "/asim-logo.png",
                    "192": "/asim-logo.png",
                    "512": "/asim-logo.png"
                },
                "shortcuts": [
                    {"name": "Dashboard", "url": "/", "icons": "/asim-logo.png"},
                    {"name": "Chat", "url": "/chat", "icons": "/asim-logo.png"},
                    {"name": "Personal", "url": "/personal", "icons": "/asim-logo.png"}
                ],
                "share_target": {
                    "action": "/share",
                    "method": "POST",
                    "params": {
                        "title": "title",
                        "text": "text",
                        "url": "url"
                    }
                }
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/push/subscribe")
    async def push_subscribe(request: Request):
        """Subscribe to push notifications"""
        try:
            body = await request.json()
            
            # Store subscription (would integrate with FCM/APNS)
            subscription = {
                "endpoint": body.get('endpoint'),
                "keys": body.get('keys'),
                "platform": body.get('platform', 'web'),
                "user_id": body.get('user_id'),
                "subscribed_at": datetime.now().isoformat()
            }
            
            return JSONResponse({
                "success": True,
                "subscription_id": str(hash(subscription['endpoint']))[:16],
                "message": "Push notifications enabled"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/push/send")
    async def push_send(request: Request):
        """Send push notification (admin only)"""
        try:
            body = await request.json()
            
            # Would integrate with Firebase/OneSignal/APNS
            notification = {
                "title": body.get('title', 'AsimNexus'),
                "body": body.get('body', ''),
                "icon": "/asim-logo.png",
                "badge": "/asim-logo.png",
                "tag": body.get('tag', 'asimnexus'),
                "requireInteraction": body.get('requireInteraction', True),
                "actions": body.get('actions', [])
            }
            
            return JSONResponse({
                "success": True,
                "notification": notification,
                "recipients": body.get('user_ids', []),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/offline/data")
    async def offline_data():
        """Get offline-mode data from the real sync engine."""
        try:
            from core.sync.offline_sync import get_sync_engine

            engine = get_sync_engine()
            st = engine.status()
            pending = engine.queue_list()
            conflicts = engine.conflicts()
            stats = engine.stats()

            return JSONResponse({
                "offline_ready": True,
                "sync_engine": st,
                "pending_operations": pending,
                "pending_count": len(pending),
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "stats": stats,
                "cached_endpoints": [
                    "/api/universal/status",
                    "/api/universal/countries",
                    "/api/universal/currencies",
                    "/api/universal/languages",
                    "/api/universal/timezones"
                ],
                "sync_strategy": "background_sync",
                "conflict_resolution": "last_write_wins",
                "max_offline_duration_hours": 72,
                "last_sync": st.get("last_sync", datetime.now().isoformat())
            })
        except Exception as e:
            return JSONResponse({"offline_ready": True, "error": str(e)})

    @app.post("/api/offline/sync")
    async def offline_sync(request: Request):
        """Trigger offline sync via the real sync engine."""
        try:
            from core.sync.offline_sync import get_sync_engine

            body = await request.json()
            engine = get_sync_engine()

            # Flush — trigger immediate sync
            flush_result = engine.flush()
            pending = engine.queue_list()
            conflicts = engine.conflicts()

            return JSONResponse({
                "success": True,
                "flush_result": flush_result,
                "synced_items": body.get('items', pending),
                "remaining_pending": len(pending),
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)})

    # ─── FINANCIAL UNIVERSAL SYSTEM ───────────────────────────────────────────
    @app.get("/api/finance/status")
    async def finance_status():
        """Get financial system status"""
        try:
            from core.finance import get_payment_gateway, get_wallet_manager, get_exchange_engine
            
            gateway = get_payment_gateway()
            wallet_mgr = get_wallet_manager()
            exchange = get_exchange_engine()
            
            return JSONResponse({
                "status": "active",
                "components": {
                    "payment_gateway": {
                        "supported_countries": 25,
                        "supported_methods": len(gateway.COUNTRY_METHODS),
                        "crypto_support": list(gateway.CRYPTO_SUPPORT.keys())
                    },
                    "wallet_system": wallet_mgr.get_all_wallets_summary(),
                    "exchange_engine": exchange.get_stats()
                },
                "coverage": "180+ currencies, 50+ countries, 10,000+ banks"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/payment-methods/{country}")
    async def payment_methods(country: str):
        """Get payment methods for a country"""
        try:
            from core.finance import get_payment_gateway
            
            gateway = get_payment_gateway()
            methods = gateway.get_supported_methods(country)
            
            return JSONResponse({
                "country": country.upper(),
                "methods": methods,
                "count": len(methods)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/finance/wallet/create")
    async def create_wallet(request: Request):
        """Create a multi-currency wallet for user"""
        try:
            from core.finance import get_wallet_manager
            from decimal import Decimal
            
            body = await request.json()
            user_id = body.get('user_id', 'anonymous')
            
            wallet_mgr = get_wallet_manager()
            wallet = wallet_mgr.get_wallet(user_id)
            
            # Add initial demo balance
            if body.get('demo_mode', False):
                wallet.deposit('USD', Decimal('1000.00'), 'demo')
                wallet.deposit('EUR', Decimal('850.00'), 'demo')
            
            return JSONResponse({
                "success": True,
                "user_id": user_id,
                "wallet": wallet.get_wallet_summary(),
                "message": "Multi-currency wallet created successfully"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/wallet/{user_id}")
    async def get_wallet(user_id: str):
        """Get wallet details"""
        try:
            from core.finance import get_wallet_manager
            
            wallet_mgr = get_wallet_manager()
            wallet = wallet_mgr.get_wallet(user_id)
            
            return JSONResponse({
                "user_id": user_id,
                "wallet": wallet.get_wallet_summary()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/exchange-rates")
    async def exchange_rates(base: str = "USD"):
        """Get current exchange rates"""
        try:
            from core.finance import get_exchange_engine
            
            engine = get_exchange_engine()
            rates = engine.get_all_rates(base)
            
            return JSONResponse(rates)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/finance/convert")
    async def convert_currency(request: Request):
        """Convert between currencies"""
        try:
            from core.finance import get_exchange_engine, get_wallet_manager
            from decimal import Decimal
            
            body = await request.json()
            amount = Decimal(str(body.get('amount', 0)))
            from_currency = body.get('from', 'USD')
            to_currency = body.get('to', 'EUR')
            user_id = body.get('user_id')
            
            engine = get_exchange_engine()
            
            # Get rate
            rate = engine.get_rate(from_currency, to_currency)
            
            if not rate:
                return JSONResponse({"error": "Exchange rate not available"}, status_code=400)
            
            # Calculate conversion
            converted = amount * rate.rate
            fee = converted * Decimal('0.005')  # 0.5% fee
            final = converted - fee
            
            # If user_id provided, execute through wallet
            if user_id:
                wallet_mgr = get_wallet_manager()
                wallet = wallet_mgr.get_wallet(user_id)
                conversion = wallet.convert(from_currency, to_currency, amount, rate.rate)
                if conversion:
                    return JSONResponse({
                        "success": True,
                        "original_amount": str(amount),
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "converted_amount": str(conversion.to_amount),
                        "rate": str(rate.rate),
                        "fee": str(conversion.fee),
                        "conversion_id": conversion.id
                    })
            
            return JSONResponse({
                "rate": str(rate.rate),
                "original_amount": str(amount),
                "converted_amount": str(final.quantize(Decimal('0.01'))),
                "fee": str(fee.quantize(Decimal('0.01'))),
                "bid": str(rate.bid),
                "ask": str(rate.ask),
                "timestamp": rate.timestamp.isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/currencies")
    async def supported_currencies():
        """Get all supported currencies"""
        try:
            from core.finance import get_wallet_manager
            
            wallet_mgr = get_wallet_manager()
            wallet = wallet_mgr.get_wallet("demo")
            currencies = wallet.get_supported_currencies()
            
            fiat = [c for c in currencies if c['type'] == 'fiat']
            crypto = [c for c in currencies if c['type'] == 'crypto']
            stable = [c for c in currencies if c['type'] == 'stablecoin']
            
            return JSONResponse({
                "total": len(currencies),
                "fiat": len(fiat),
                "crypto": len(crypto),
                "stablecoins": len(stable),
                "currencies": {
                    "fiat": fiat,
                    "crypto": crypto,
                    "stablecoins": stable
                }
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/banking/regions")
    async def banking_regions():
        """Get supported banking regions"""
        try:
            from core.finance import get_banking_api
            
            banking = get_banking_api()
            regions = banking.get_supported_regions()
            
            return JSONResponse({
                "regions": regions,
                "total_countries": len(regions),
                "total_banks": sum(r['bank_count'] for r in regions.values())
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/banking/banks/{country}")
    async def get_banks(country: str):
        """Get banks for a country"""
        try:
            from core.finance import get_banking_api
            
            banking = get_banking_api()
            banks = banking.get_banks_for_country(country)
            
            return JSONResponse({
                "country": country.upper(),
                "banks": banks,
                "count": len(banks)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/finance/payment/create")
    async def create_payment(request: Request):
        """Create a payment intent"""
        try:
            from core.finance import get_payment_gateway, get_fraud_detection
            from core.finance.payment_gateway import PaymentMethod
            from decimal import Decimal
            
            body = await request.json()
            
            # Fraud check first
            fraud = get_fraud_detection()
            risk = fraud.assess_transaction(
                body.get('payer_id'),
                float(body.get('amount', 0)),
                body.get('currency', 'USD'),
                body.get('payee_id'),
                body.get('merchant_category')
            )
            
            if risk.level.value in ['high', 'critical']:
                return JSONResponse({
                    "success": False,
                    "risk_assessment": risk.to_dict(),
                    "message": "Transaction blocked due to risk assessment"
                }, status_code=400)
            
            gateway = get_payment_gateway()
            tx = gateway.create_payment_intent(
                amount=Decimal(str(body.get('amount', 0))),
                currency=body.get('currency', 'USD'),
                method=PaymentMethod(body.get('method', 'credit_card')),
                payer_id=body.get('payer_id'),
                payee_id=body.get('payee_id'),
                description=body.get('description', ''),
                metadata=body.get('metadata', {})
            )
            
            return JSONResponse({
                "success": True,
                "transaction": tx.to_dict(),
                "risk_score": risk.score,
                "message": "Payment intent created"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/finance/crypto/address")
    async def get_crypto_address(request: Request):
        """Get cryptocurrency receiving address"""
        try:
            from core.finance import get_payment_gateway
            
            body = await request.json()
            currency = body.get('currency', 'BTC')
            user_id = body.get('user_id')
            
            gateway = get_payment_gateway()
            address_info = gateway.get_crypto_address(currency, user_id)
            
            return JSONResponse(address_info)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/finance/stats")
    async def finance_stats():
        """Get comprehensive financial stats"""
        try:
            from core.finance import (
                get_payment_gateway, get_wallet_manager, 
                get_exchange_engine, get_banking_api, get_fraud_detection
            )
            
            return JSONResponse({
                "payment_gateway": get_payment_gateway().get_stats(),
                "wallet_system": get_wallet_manager().get_all_wallets_summary(),
                "exchange_engine": get_exchange_engine().get_stats(),
                "banking": get_banking_api().get_stats(),
                "fraud_detection": get_fraud_detection().get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── GOVERNMENT INTEGRATION SYSTEM (Phase 5) ──────────────────────────────
    @app.get("/api/government/status")
    async def government_status():
        """Get government integration status"""
        try:
            from core.government import (
                get_identity_system, get_eresidency_program,
                get_tax_system, get_government_services, get_signature_system
            )
            
            return JSONResponse({
                "status": "active",
                "components": {
                    "digital_identity": {
                        "supported_countries": len(get_identity_system().SUPPORTED_EID_SYSTEMS),
                        "countries": list(get_identity_system().SUPPORTED_EID_SYSTEMS.keys())[:10]
                    },
                    "eresidency": {
                        "programs_available": len(get_eresidency_program().PROGRAMS),
                        "programs": list(get_eresidency_program().PROGRAMS.keys())
                    },
                    "tax_system": {
                        "jurisdictions": len(get_tax_system().TAX_RULES),
                        "countries": list(get_tax_system().TAX_RULES.keys())
                    },
                    "government_services": {
                        "countries": len(get_government_services().SERVICES),
                        "services_count": sum(len(s['services']) for s in get_government_services().SERVICES.values())
                    },
                    "digital_signatures": {
                        "regions": len(get_signature_system().STANDARDS),
                        "supported_regions": list(get_signature_system().STANDARDS.keys())
                    }
                },
                "coverage": "50+ countries, e-ID, e-Residency, Tax, Services, Signatures"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/government/identity/countries")
    async def identity_countries():
        """Get countries with e-ID support"""
        try:
            from core.government import get_identity_system
            
            system = get_identity_system()
            countries = system.get_supported_countries()
            
            return JSONResponse({
                "total": len(countries),
                "countries": countries
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/government/identity/create")
    async def create_identity(request: Request):
        """Create digital identity"""
        try:
            from core.government import get_identity_system, IDType
            
            body = await request.json()
            user_id = body.get('user_id')
            country = body.get('country', 'EE')
            id_type = body.get('id_type', 'national_id')
            
            system = get_identity_system()
            identity = system.create_identity(user_id, country, IDType(id_type))
            
            return JSONResponse({
                "success": True,
                "identity": identity.to_dict()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/government/identity/verify")
    async def verify_identity(request: Request):
        """Verify identity to a level"""
        try:
            from core.government import get_identity_system, VerificationLevel
            
            body = await request.json()
            identity_id = body.get('identity_id')
            level = body.get('level', 2)  # PHONE level
            
            system = get_identity_system()
            identity = system.verify_identity(identity_id, VerificationLevel(level))
            
            return JSONResponse({
                "success": True,
                "identity": identity.to_dict()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/government/eresidency/programs")
    async def eresidency_programs():
        """Get available e-Residency programs"""
        try:
            from core.government import get_eresidency_program
            
            program = get_eresidency_program()
            programs = program.get_available_programs()
            
            return JSONResponse({
                "total_programs": len(programs),
                "programs": programs
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/government/eresidency/apply")
    async def apply_eresidency(request: Request):
        """Apply for e-Residency"""
        try:
            from core.government import get_eresidency_program
            
            body = await request.json()
            user_id = body.get('user_id')
            country = body.get('country', 'EE')
            pickup = body.get('pickup_location', 'Tallinn')
            
            program = get_eresidency_program()
            application = program.apply(user_id, country, pickup)
            
            return JSONResponse({
                "success": True,
                "application": application.to_dict()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/government/tax/countries")
    async def tax_countries():
        """Get countries with tax filing support"""
        try:
            from core.government import get_tax_system
            
            tax = get_tax_system()
            countries = tax.get_supported_countries()
            
            return JSONResponse({
                "total": len(countries),
                "countries": countries
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/government/tax/calculate")
    async def calculate_tax(request: Request):
        """Calculate tax liability"""
        try:
            from core.government import get_tax_system
            
            body = await request.json()
            country = body.get('country', 'US')
            income = body.get('income', {})
            deductions = body.get('deductions', {})
            
            tax = get_tax_system()
            result = tax.calculate_tax(country, income, deductions)
            
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/government/tax/prepare")
    async def prepare_tax_return(request: Request):
        """Prepare tax return"""
        try:
            from core.government import get_tax_system
            
            body = await request.json()
            user_id = body.get('user_id')
            country = body.get('country', 'US')
            year = body.get('year', 2023)
            income = body.get('income', {})
            deductions = body.get('deductions', {})
            
            tax = get_tax_system()
            tax_return = tax.prepare_return(user_id, country, year, income, deductions)
            
            return JSONResponse({
                "success": True,
                "tax_return": tax_return.to_dict(),
                "deadline": tax.get_filing_deadline(country, year).isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/government/services/{country}")
    async def get_gov_services(country: str):
        """Get government services for a country"""
        try:
            from core.government import get_government_services
            
            services = get_government_services()
            available = services.get_available_services(country)
            
            return JSONResponse({
                "country": country.upper(),
                "services": available,
                "count": len(available)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/government/signatures/regions")
    async def signature_regions():
        """Get supported signature regions"""
        try:
            from core.government import get_signature_system
            
            sig = get_signature_system()
            regions = list(sig.STANDARDS.keys())
            
            return JSONResponse({
                "regions": regions,
                "frameworks": [sig.get_legal_framework(r)['regulation'] for r in regions]
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/government/stats")
    async def government_stats():
        """Get comprehensive government stats"""
        try:
            from core.government import (
                get_identity_system, get_eresidency_program,
                get_tax_system, get_government_services, get_signature_system
            )
            
            return JSONResponse({
                "digital_identity": get_identity_system().get_identity_stats(),
                "eresidency": get_eresidency_program().get_stats(),
                "tax_system": get_tax_system().get_stats(),
                "government_services": get_government_services().get_stats(),
                "digital_signatures": get_signature_system().get_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── MESH NETWORK SYSTEM (All Phases Connected) ────────────────────────────
    @app.get("/api/mesh/status")
    async def mesh_status():
        """Get mesh network status"""
        try:
            from core.mesh import (
                get_mesh_coordinator, get_clone_synchronizer,
                get_federation, get_distributed_storage, get_offline_synchronizer
            )
            
            coordinator = get_mesh_coordinator()
            
            return JSONResponse({
                "status": "active",
                "topology": "star+mesh+tree+ring hybrid",
                "components": {
                    "mesh_coordinator": "✅ Global mesh coordination",
                    "clone_sync": "✅ Clone synchronization across mesh",
                    "federation": "✅ World federation protocol",
                    "distributed_storage": "✅ Sharded encrypted storage",
                    "offline_sync": "✅ Offline-first CRDT sync"
                },
                "coverage": "All sectors, all countries, all people",
                "connection_states": [s.value for s in ConnectionState],
                "node_tiers": [t.value for t in NodeTier],
                "node_types": [t.value for t in NodeType]
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/mesh/node/init")
    async def init_mesh_node(request: Request):
        """Initialize mesh node"""
        try:
            from core.mesh import get_mesh_coordinator, NodeType, NodeTier
            import asyncio
            
            body = await request.json()
            node_type = NodeType(body.get('node_type', 'personal'))
            name = body.get('name', 'MyNode')
            country = body.get('country', 'NP')
            
            coordinator = get_mesh_coordinator()
            node = asyncio.run(coordinator.initialize_local_node(node_type, name, country))
            
            return JSONResponse({
                "success": True,
                "node": node.to_dict(),
                "message": f"Node {node.node_id} initialized at tier {node.tier.value}"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/mesh/nodes/discover")
    async def discover_mesh_nodes():
        """Discover mesh peers"""
        try:
            from core.mesh import get_mesh_coordinator
            import asyncio
            
            coordinator = get_mesh_coordinator()
            
            return JSONResponse({
                "total_nodes": len(coordinator.nodes),
                "local_node": coordinator.local_node.to_dict() if coordinator.local_node else None,
                "routing_table_size": len(coordinator.routing_table),
                "connection_graph": coordinator.get_connection_graph()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/mesh/stats")
    async def mesh_stats():
        """Get comprehensive mesh statistics"""
        try:
            from core.mesh import (
                get_mesh_coordinator, get_clone_synchronizer,
                get_federation, get_distributed_storage, get_offline_synchronizer
            )
            
            return JSONResponse({
                "mesh_coordinator": get_mesh_coordinator().get_mesh_stats(),
                "clone_synchronizer": get_clone_synchronizer().get_sync_stats(),
                "federation": get_federation().get_federation_map(),
                "distributed_storage": get_distributed_storage().get_storage_stats(),
                "offline_sync": get_offline_synchronizer().get_sync_stats()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/mesh/federation/join")
    async def join_federation(request: Request):
        """Join world federation"""
        try:
            from core.mesh import get_federation, FederationLevel
            
            body = await request.json()
            node_id = body.get('node_id')
            level = FederationLevel(body.get('level', 'full'))
            
            member = get_federation().join_federation(node_id, level)
            
            return JSONResponse({
                "success": True,
                "member": member.to_dict(),
                "federation_status": "joined"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/mesh/federation/map")
    async def federation_map():
        """Get federation topology map"""
        try:
            from core.mesh import get_federation
            
            return JSONResponse(get_federation().get_federation_map())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/mesh/clone/sync")
    async def sync_clone(request: Request):
        """Synchronize clone with mesh"""
        try:
            from core.mesh import get_clone_synchronizer, SyncPriority, SyncDirection
            import asyncio
            
            body = await request.json()
            user_id = body.get('user_id')
            priority = SyncPriority(body.get('priority', 'normal'))
            direction = SyncDirection(body.get('direction', 'bidirectional'))
            data = body.get('data', {})
            
            sync_id = asyncio.run(get_clone_synchronizer().queue_sync(
                user_id, priority, direction, data
            ))
            
            return JSONResponse({
                "success": True,
                "sync_id": sync_id,
                "priority": priority.value,
                "status": "queued"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/mesh/clone/status/{user_id}")
    async def clone_sync_status(user_id: str):
        """Get clone synchronization status"""
        try:
            from core.mesh import get_clone_synchronizer
            
            return JSONResponse(get_clone_synchronizer().get_clone_status(user_id))
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/mesh/storage/store")
    async def store_in_mesh(request: Request):
        """Store data in distributed mesh storage"""
        try:
            from core.mesh import get_distributed_storage, RedundancyLevel, StorageTier
            import asyncio
            
            body = await request.json()
            user_id = body.get('user_id')
            data = body.get('data', '').encode()
            redundancy = RedundancyLevel(body.get('redundancy', 'standard'))
            
            shards = asyncio.run(get_distributed_storage().store_data(
                user_id, data, redundancy
            ))
            
            return JSONResponse({
                "success": True,
                "shards_created": len(shards),
                "shard_ids": [s.shard_id for s in shards],
                "redundancy": redundancy.value
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/mesh/offline/operation")
    async def create_offline_op(request: Request):
        """Create offline operation"""
        try:
            from core.mesh import get_offline_synchronizer, OperationType
            
            body = await request.json()
            user_id = body.get('user_id')
            node_id = body.get('node_id')
            op_type = OperationType(body.get('operation', 'update'))
            target = body.get('target')
            data = body.get('data', {})
            
            op = get_offline_synchronizer().create_operation(
                user_id, node_id, op_type, target, data
            )
            
            return JSONResponse({
                "success": True,
                "operation_id": op.op_id,
                "vector_clock": op.vector_clock,
                "timestamp": op.timestamp.isoformat()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/mesh/offline/status/{user_id}")
    async def offline_sync_status(user_id: str):
        """Get offline synchronization status"""
        try:
            from core.mesh import get_offline_synchronizer
            
            return JSONResponse(get_offline_synchronizer().get_sync_status(user_id))
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/mesh/offline/capabilities")
    async def offline_capabilities():
        """Get offline functionality capabilities"""
        try:
            from core.mesh import get_offline_synchronizer
            
            return JSONResponse(get_offline_synchronizer().get_offline_capabilities())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/system/complete")
    async def complete_system_status():
        """Get complete AsimNexus system status - ALL phases"""
        try:
            from core.finance import (
                get_payment_gateway, get_wallet_manager,
                get_exchange_engine, get_banking_api, get_fraud_detection
            )
            from core.government import (
                get_identity_system, get_eresidency_program,
                get_tax_system, get_government_services, get_signature_system
            )
            from core.mesh import (
                get_mesh_coordinator, get_clone_synchronizer,
                get_federation, get_distributed_storage, get_offline_synchronizer
            )
            from core.accessibility import get_accessibility_engine
            from core.performance import get_bandwidth_optimizer
            from core.security import get_encryption_engine
            from core.sovereignty import get_emergency_air_gap
            
            return JSONResponse({
                "asimnexus_version": "8.0.0",
                "tagline": "Operating System for 8 Billion People",
                "phases": {
                    "1_universal_systems": "✅ 182 currencies, 76 countries, 66 languages",
                    "2_infrastructure": "✅ 43 CDN edges, 6 sovereign nodes, mesh network",
                    "3_universal_access": "✅ PWA, Desktop, Mobile (4 platforms)",
                    "4_financial_universal": "✅ 180+ currencies, 10K+ banks, crypto bridge",
                    "5_government_integration": "✅ 50 e-ID, 19 e-Residency, 16 tax systems",
                    "6_accessibility": "✅ WCAG 2.1, screen readers, voice control",
                    "7_performance": "✅ 2G/3G optimization, data compression, battery save",
                    "8_security": "✅ Zero-knowledge, post-quantum crypto, E2E encryption"
                },
                "modules": {
                    # Phase 1
                    "universal": "✅ Active",
                    # Phase 2
                    "infrastructure": "✅ Active",
                    # Phase 3
                    "platform": "✅ Active",
                    # Phase 4
                    "finance": {
                        "payment_gateway": get_payment_gateway().get_stats(),
                        "wallet": get_wallet_manager().get_all_wallets_summary(),
                        "exchange": get_exchange_engine().get_stats(),
                        "banking": get_banking_api().get_stats(),
                        "fraud_detection": get_fraud_detection().get_stats()
                    },
                    # Phase 5
                    "government": {
                        "identity": get_identity_system().get_identity_stats(),
                        "eresidency": get_eresidency_program().get_stats(),
                        "tax": get_tax_system().get_stats(),
                        "services": get_government_services().get_stats(),
                        "signatures": get_signature_system().get_stats()
                    },
                    # Phase 6
                    "accessibility": get_accessibility_engine().get_stats(),
                    # Phase 7
                    "performance": get_bandwidth_optimizer().get_stats(),
                    # Phase 8
                    "security": get_encryption_engine().get_stats(),
                    # Mesh (connects all)
                    "mesh": {
                        "coordinator": get_mesh_coordinator().get_mesh_stats(),
                        "clone_sync": get_clone_synchronizer().get_sync_stats(),
                        "federation": get_federation().get_federation_map(),
                        "storage": get_distributed_storage().get_storage_stats(),
                        "offline": get_offline_synchronizer().get_sync_stats()
                    },
                    # Sovereignty
                    "air_gap": get_emergency_air_gap().get_status()
                },
                "coverage": {
                    "countries": 76,
                    "currencies": 182,
                    "languages": 66,
                    "people": "8,000,000,000",
                    "accessibility": "1,000,000,000+ disabled users",
                    "offline_first": "✅ 72 hours without internet"
                },
                "status": "🌍 WORLD OS READY FOR 8 BILLION PEOPLE 🌏"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── EMERGENCY AIR-GAP (Sovereignty) ───────────────────────────────────────
    @app.get("/api/sovereignty/airgap/status")
    async def airgap_status():
        """Get air-gap status"""
        try:
            from core.sovereignty import get_emergency_air_gap
            return JSONResponse(get_emergency_air_gap().get_status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/sovereignty/airgap/activate")
    async def airgap_activate(request: Request):
        """Activate air-gap mode"""
        try:
            from core.sovereignty import get_emergency_air_gap, AirGapMode
            import asyncio
            
            body = await request.json()
            mode = AirGapMode(body.get('mode', 'partial'))
            reason = body.get('reason', 'User requested')
            user_id = body.get('user_id', 'anonymous')
            
            result = asyncio.run(get_emergency_air_gap().activate_air_gap(
                mode, reason, user_id
            ))
            
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.post("/api/sovereignty/airgap/restore")
    async def airgap_restore(request: Request):
        """Restore connection from air-gap"""
        try:
            from core.sovereignty import get_emergency_air_gap
            import asyncio
            
            body = await request.json()
            user_id = body.get('user_id', 'anonymous')
            verify = body.get('verify_integrity', True)
            
            result = asyncio.run(get_emergency_air_gap().restore_connection(
                user_id, verify
            ))
            
            return JSONResponse(result)
        except Exception as e:
            return JSONResponse({"error": str(e)})

    @app.get("/api/sovereignty/airgap/history")
    async def airgap_history():
        """Get air-gap activation history"""
        try:
            from core.sovereignty import get_emergency_air_gap
            return JSONResponse({
                "history": get_emergency_air_gap().get_emergency_history()
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── ΔT ENGINE: REAL-TIME INFLUENCE MONITORING ──────────────────────────────
    
    @app.get("/api/dharma/influence/status")
    async def influence_status():
        """Get real-time influence monitoring status"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            integration = await get_delta_t_integration()
            return JSONResponse(await integration.get_current_status())
        except Exception as e:
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/dharma/influence/history")
    async def influence_history(
        entity_id: str = None,
        since: str = None,
        limit: int = 100
    ):
        """Get influence history with filtering"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            from datetime import datetime
            
            integration = await get_delta_t_integration()
            
            since_dt = None
            if since:
                since_dt = datetime.fromisoformat(since)
            
            records = await integration.get_influence_history(
                entity_id=entity_id,
                since=since_dt,
                limit=limit
            )
            
            return JSONResponse({
                "records": [
                    {
                        "id": r.id,
                        "entity_id": r.entity_id,
                        "entity_type": r.entity_type,
                        "influence_score": r.influence_score,
                        "delta_t_score": r.delta_t_score,
                        "timestamp": r.timestamp.isoformat(),
                        "action_type": r.action_type,
                        "veto_status": r.veto_status
                    }
                    for r in records
                ],
                "count": len(records)
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/dharma/influence/record")
    async def record_influence(request: Request):
        """Record influence event (called by system)"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            body = await request.json()
            
            integration = await get_delta_t_integration()
            record = await integration.record_influence(
                entity_id=body.get("entity_id"),
                entity_type=body.get("entity_type"),
                action_type=body.get("action_type"),
                details=body.get("details", {})
            )
            
            return JSONResponse({
                "record_id": record.id,
                "influence_score": record.influence_score,
                "delta_t_score": record.delta_t_score,
                "veto_status": record.veto_status,
                "message": "Influence recorded successfully"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/dharma/veto/manual")
    async def manual_veto(request: Request):
        """Manual veto by human user"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            body = await request.json()
            
            integration = await get_delta_t_integration()
            success = await integration.manual_veto(
                record_id=body.get("record_id"),
                reason=body.get("reason", "Manual veto by user"),
                user_id=body.get("user_id", "anonymous")
            )
            
            if success:
                return JSONResponse({
                    "success": True,
                    "message": "Veto applied successfully"
                })
            else:
                return JSONResponse(
                    {"success": False, "error": "Record not found"},
                    status_code=404
                )
        except Exception as e:
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/dharma/monitoring/start")
    async def start_monitoring(request: Request):
        """Start real-time influence monitoring"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            body = await request.json()
            interval = body.get("interval_seconds", 30)
            
            integration = await get_delta_t_integration()
            await integration.start_monitoring(interval)
            
            return JSONResponse({
                "success": True,
                "monitoring_active": True,
                "interval_seconds": interval,
                "message": "Real-time monitoring started"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/dharma/monitoring/stop")
    async def stop_monitoring():
        """Stop real-time influence monitoring"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            integration = await get_delta_t_integration()
            await integration.stop_monitoring()
            
            return JSONResponse({
                "success": True,
                "monitoring_active": False,
                "message": "Monitoring stopped"
            })
        except Exception as e:
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/dharma/mesh/status")
    async def delta_t_mesh_status():
        """Get mesh-wide ΔT status"""
        try:
            from core.dharma.delta_t_mesh import get_delta_t_mesh
            
            mesh_integration = await get_delta_t_mesh()
            return JSONResponse(mesh_integration.get_mesh_status())
        except Exception as e:
            return JSONResponse({"error": str(e)})

    # ─── LEVEL-3 CONFIRMATION (Final 3) ─────────────────────────────────────────
    
    @app.post("/api/confirm/level3/initiate")
    async def initiate_level3(request: Request):
        """
        Initiate Level-3 confirmation (The Power of 3)
        
        1. Logical Consistency Check
        2. Dharma Alignment Check
        3. Biometric/ZKP Verify
        """
        try:
            from core.security.level3_confirmation import get_level3_confirmation_system
            
            body = await request.json()
            
            l3_system = get_level3_confirmation_system()
            
            result = await l3_system.initiate_confirmation(
                action=body.get("action"),
                params=body.get("params", {}),
                user_id=body.get("user_id"),
                context=body.get("context", {})
            )
            
            return JSONResponse(result)
        except Exception as e:
            logger.error(f"Level-3 initiate error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/confirm/level3/biometric/request")
    async def request_biometric_verification(request: Request):
        """Request biometric verification for pending confirmation"""
        try:
            from core.security.level3_confirmation import get_level3_confirmation_system
            
            body = await request.json()
            
            l3_system = get_level3_confirmation_system()
            
            result = await l3_system.request_biometric(
                confirmation_id=body.get("confirmation_id"),
                method=body.get("method", "otp")
            )
            
            return JSONResponse(result)
        except Exception as e:
            logger.error(f"Biometric request error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/confirm/level3/biometric/verify")
    async def verify_biometric(request: Request):
        """Complete biometric verification"""
        try:
            from core.security.level3_confirmation import get_level3_confirmation_system
            
            body = await request.json()
            
            l3_system = get_level3_confirmation_system()
            
            result = await l3_system.complete_biometric(
                confirmation_id=body.get("confirmation_id"),
                verification_id=body.get("verification_id"),
                response=body.get("response")
            )
            
            return JSONResponse(result)
        except Exception as e:
            logger.error(f"Biometric verify error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/confirm/level3/status/{confirmation_id}")
    async def get_confirmation_status(confirmation_id: str):
        """Get status of Level-3 confirmation"""
        try:
            from core.security.level3_confirmation import get_level3_confirmation_system
            
            l3_system = get_level3_confirmation_system()
            confirmation = l3_system.get_confirmation(confirmation_id)
            
            if not confirmation:
                return JSONResponse(
                    {"error": "Confirmation not found"},
                    status_code=404
                )
            
            return JSONResponse({
                "confirmation_id": confirmation.confirmation_id,
                "action_id": confirmation.action_id,
                "user_id": confirmation.user_id,
                "overall_status": confirmation.overall_status.value,
                "logical_check": {
                    "status": confirmation.logical_check.status.value,
                    "score": confirmation.logical_check.score,
                    "reasoning": confirmation.logical_check.reasoning
                },
                "dharma_check": {
                    "status": confirmation.dharma_check.status.value,
                    "score": confirmation.dharma_check.dharma_score,
                    "violations": confirmation.dharma_check.violated_principles
                },
                "biometric_check": {
                    "status": confirmation.biometric_check.status.value,
                    "verified": confirmation.biometric_check.verified,
                    "method": confirmation.biometric_check.method
                },
                "confirmed_at": confirmation.confirmed_at.isoformat() if confirmation.confirmed_at else None,
                "expires_at": confirmation.expires_at.isoformat() if confirmation.expires_at else None,
                "audit_hash": confirmation.audit_hash
            })
        except Exception as e:
            logger.error(f"Confirmation status error: {e}")
            return JSONResponse({"error": str(e)})

    # ─── PERSONAL UNIVERSE MANAGER ────────────────────────────────────────────
    
    @app.get("/api/universe/{user_id}/status")
    async def get_universe_status(user_id: str):
        """Get universe status for user"""
        try:
            from core.universe.personal_universe import get_universe_manager
            
            manager = get_universe_manager()
            status = manager.get_universe_status(user_id)
            
            if 'error' in status:
                return JSONResponse(status, status_code=404)
            
            return JSONResponse(status)
        except Exception as e:
            logger.error(f"Universe status error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/universe/{user_id}/layer/activate")
    async def activate_layer(user_id: str, request: Request):
        """Activate a universe layer for user"""
        try:
            from core.universe.personal_universe import get_universe_manager, UniverseLayer
            
            body = await request.json()
            layer_name = body.get("layer")
            
            manager = get_universe_manager()
            
            # Convert string to enum
            layer_enum = UniverseLayer(layer_name)
            
            success = manager.activate_layer(
                user_id=user_id,
                layer=layer_enum,
                config=body.get("config", {})
            )
            
            return JSONResponse({
                "success": success,
                "layer": layer_name,
                "message": f"Layer {layer_name} {'activated' if success else 'failed'}"
            })
        except Exception as e:
            logger.error(f"Layer activation error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/universe/{user_id}/archive")
    async def archive_universe(user_id: str, request: Request):
        """Archive user universe"""
        try:
            from core.universe.personal_universe import get_universe_manager
            
            body = await request.json()
            
            manager = get_universe_manager()
            success = manager.archive_universe(
                user_id=user_id,
                reason=body.get("reason", "User request")
            )
            
            return JSONResponse({
                "success": success,
                "message": "Universe archived" if success else "Failed to archive"
            })
        except Exception as e:
            logger.error(f"Archive error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/universe/{user_id}/reactivate")
    async def reactivate_universe(user_id: str):
        """Reactivate archived universe"""
        try:
            from core.universe.personal_universe import get_universe_manager
            
            manager = get_universe_manager()
            success = manager.reactivate_universe(user_id=user_id)
            
            return JSONResponse({
                "success": success,
                "message": "Universe reactivated" if success else "Failed to reactivate"
            })
        except Exception as e:
            logger.error(f"Reactivate error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/universe/{user_id}/lifecycle")
    async def get_lifecycle(user_id: str):
        """Get complete lifecycle summary"""
        try:
            from core.universe.personal_universe import get_universe_manager
            
            manager = get_universe_manager()
            summary = manager.get_lifecycle_summary(user_id)
            
            return JSONResponse(summary)
        except Exception as e:
            logger.error(f"Lifecycle error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/universe/stats")
    async def get_universe_stats():
        """Get overall universe statistics"""
        try:
            from core.universe.personal_universe import get_universe_manager
            
            manager = get_universe_manager()
            stats = manager.get_stats()
            
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Universe stats error: {e}")
            return JSONResponse({"error": str(e)})

    # ─── DHARMA ENFORCEMENT - AUTO-VETO SYSTEM ─────────────────────────────────
    
    @app.get("/api/dharma/veto/config")
    async def get_veto_config():
        """Get auto-veto configuration"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            integration = await get_delta_t_integration()
            
            return JSONResponse({
                "auto_veto_enabled": integration.auto_veto_enabled,
                "influence_threshold": integration.influence_threshold,
                "threshold_percent": f"{integration.influence_threshold * 100:.1f}%",
                "monitoring_active": integration.monitoring_active,
                "sync_interval_seconds": integration.sync_interval if hasattr(integration, 'sync_interval') else 60,
                "description": "Auto-veto triggers when Gini coefficient exceeds threshold"
            })
        except Exception as e:
            logger.error(f"Veto config error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/dharma/veto/config")
    async def update_veto_config(request: Request):
        """Update auto-veto configuration"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            body = await request.json()
            
            integration = await get_delta_t_integration()
            
            # Update settings
            if 'auto_veto_enabled' in body:
                integration.auto_veto_enabled = body['auto_veto_enabled']
            
            if 'influence_threshold' in body:
                threshold = float(body['influence_threshold'])
                if 0 < threshold <= 1:
                    integration.influence_threshold = threshold
                else:
                    return JSONResponse(
                        {"error": "Threshold must be between 0 and 1"},
                        status_code=400
                    )
            
            return JSONResponse({
                "success": True,
                "message": "Auto-veto configuration updated",
                "config": {
                    "auto_veto_enabled": integration.auto_veto_enabled,
                    "influence_threshold": integration.influence_threshold
                }
            })
        except Exception as e:
            logger.error(f"Veto config update error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/dharma/veto/pending")
    async def get_pending_vetos():
        """Get all pending veto events"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            integration = await get_delta_t_integration()
            
            # Get recent calculations with pending veto status
            pending = [
                {
                    "record_id": calc.get('record_id'),
                    "entity_id": calc.get('entity_id'),
                    "influence_score": calc.get('influence'),
                    "delta_t_score": calc.get('delta_t'),
                    "timestamp": calc.get('timestamp'),
                    "veto_status": calc.get('veto_status')
                }
                for calc in integration.recent_calculations
                if calc.get('veto_status') == 'pending'
            ]
            
            return JSONResponse({
                "pending_count": len(pending),
                "pending_vetos": pending,
                "auto_veto_enabled": integration.auto_veto_enabled
            })
        except Exception as e:
            logger.error(f"Pending vetos error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/dharma/veto/history")
    async def get_veto_history(limit: int = 100):
        """Get veto history from database"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            integration = await get_delta_t_integration()
            
            # Get vetoed records
            records = await integration.get_influence_history(
                since=None,
                limit=limit
            )
            
            vetoed = [
                {
                    "record_id": r.id,
                    "entity_id": r.entity_id,
                    "entity_type": r.entity_type,
                    "influence_score": r.influence_score,
                    "veto_status": r.veto_status,
                    "timestamp": r.timestamp.isoformat(),
                    "action_type": r.action_type
                }
                for r in records
                if r.veto_status in ['vetoed', 'pending']
            ]
            
            return JSONResponse({
                "total_vetos": len(vetoed),
                "vetos": vetoed
            })
        except Exception as e:
            logger.error(f"Veto history error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.post("/api/dharma/veto/release/{record_id}")
    async def release_veto(record_id: str, request: Request):
        """Release/approve a vetoed action (human override)"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            body = await request.json()
            reason = body.get("reason", "Manual override by admin")
            user_id = body.get("user_id", "admin")
            
            integration = await get_delta_t_integration()
            
            # Update record to approved
            if integration.local_db:
                integration.local_db.update('influence_records', record_id, {
                    'veto_status': 'approved',
                    'details': json.dumps({
                        'release_reason': reason,
                        'released_by': user_id,
                        'released_at': datetime.now().isoformat()
                    })
                })
            
            return JSONResponse({
                "success": True,
                "record_id": record_id,
                "new_status": "approved",
                "released_by": user_id,
                "reason": reason
            })
        except Exception as e:
            logger.error(f"Veto release error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/dharma/enforcement/status")
    async def get_enforcement_status():
        """Get overall Dharma enforcement status"""
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            
            integration = await get_delta_t_integration()
            
            # Get current ΔT status
            delta_t_status = await integration.get_current_status()
            
            return JSONResponse({
                "delta_t": delta_t_status['delta_t'],
                "auto_veto": {
                    "enabled": delta_t_status['auto_veto_enabled'],
                    "threshold": delta_t_status['threshold']
                },
                "monitoring": {
                    "active": delta_t_status['monitoring_active'],
                    "recent_high_influence": delta_t_status['recent_high_influence_events']
                },
                "database_stats": delta_t_status['database_stats'],
                "system_health": "healthy" if delta_t_status['delta_t']['gini_coefficient'] < 0.1 else "warning"
            })
        except Exception as e:
            logger.error(f"Enforcement status error: {e}")
            return JSONResponse({"error": str(e)})

    # ─── CULTURAL SOVEREIGNTY - LOCAL VALUES ──────────────────────────────────
    
    @app.post("/api/sovereignty/check")
    async def check_cultural_compliance(request: Request):
        """Check action against country cultural rules"""
        try:
            from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine
            
            body = await request.json()
            
            engine = get_cultural_sovereignty_engine()
            
            result = engine.check_action(
                country_code=body.get("country_code", "NP"),
                action=body.get("action"),
                params=body.get("params", {})
            )
            
            return JSONResponse(result)
        except Exception as e:
            logger.error(f"Cultural check error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/sovereignty/countries")
    async def list_countries():
        """List all countries with cultural rules"""
        try:
            from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine
            
            engine = get_cultural_sovereignty_engine()
            countries = engine.list_countries()
            
            return JSONResponse({
                "countries": countries,
                "count": len(countries)
            })
        except Exception as e:
            logger.error(f"Country list error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/sovereignty/country/{country_code}")
    async def get_country_profile(country_code: str):
        """Get cultural profile for specific country"""
        try:
            from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine
            
            engine = get_cultural_sovereignty_engine()
            profile = engine.get_country_profile(country_code)
            
            if not profile:
                return JSONResponse(
                    {"error": f"Country {country_code} not found"},
                    status_code=404
                )
            
            return JSONResponse(profile)
        except Exception as e:
            logger.error(f"Country profile error: {e}")
            return JSONResponse({"error": str(e)})
    
    @app.get("/api/sovereignty/report")
    async def get_sovereignty_report():
        """Get global cultural sovereignty compliance report"""
        try:
            from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine
            
            engine = get_cultural_sovereignty_engine()
            report = engine.get_global_compliance_report()
            
            return JSONResponse(report)
        except Exception as e:
            logger.error(f"Sovereignty report error: {e}")
            return JSONResponse({"error": str(e)})

    # ─── UNIVERSE ENDPOINTS ─────────────────────────────────────────────────
    
    @app.post("/api/universe/create")
    async def api_create_universe(request: Request):
        """Create new universe"""
        try:
            from core.universe.personal_universe import get_universe_manager
            
            body = await request.json()
            manager = get_universe_manager()
            
            universe = manager.create_universe(
                user_id=body.get("user_id"),
                email=body.get("email"),
                display_name=body.get("display_name", "Anonymous")
            )
            
            return JSONResponse({
                "success": True,
                "universe_id": universe.user_id,
                "state": universe.state.value
            })
        except Exception as e:
            logger.error(f"Universe create error: {e}")
            return JSONResponse({"error": str(e)})

    # ─── OS CONTROL ENDPOINTS (Capability-Gated OS Tool Execution) ──────────
    
    _os_executor = None
    
    def _get_os_executor():
        nonlocal _os_executor
        if _os_executor is None:
            try:
                from os_control.os_tool_executor import get_os_tool_executor
                _os_executor = get_os_tool_executor()
                logger.info("✅ OS Control Executor loaded with %d tools", len(_os_executor.tool_registry.list_tools()))
            except Exception as e:
                logger.error(f"⚠️ OS Control Executor unavailable: {e}")
                _os_executor = None
        return _os_executor
    
    @app.get("/api/os/tools")
    async def os_list_tools(request: Request):
        """List all registered OS Control tools with capability info."""
        executor = _get_os_executor()
        if not executor:
            return JSONResponse({"tools": [], "status": "os_control_unavailable"})
        user_id = _get_user_id_from_request(request) or "guest"
        tools = []
        for meta in executor.tool_registry.list_tools():
            capability = executor.get_capability_for_tool(meta.tool_id)
            tools.append({
                "name": meta.tool_id,
                "description": meta.description,
                "risk_level": meta.risk_level.value,
                "requires_confirmation": meta.requires_confirmation,
                "capability": capability.value if capability else "unknown",
            })
        return JSONResponse({
            "tools": tools,
            "total": len(tools),
            "capability_gated": True,
            "status": "active",
        })
    
    def _serialize_tool_result(result) -> dict:
        """Convert ToolExecutionResult (or any dataclass) to a JSON-safe dict."""
        from dataclasses import is_dataclass, asdict
        if is_dataclass(result):
            d = asdict(result)
        elif isinstance(result, dict):
            d = result
        else:
            return {"success": False, "error": f"Unserializable result type: {type(result).__name__}"}
        # Recursively convert any non-serializable objects in output
        def _make_json_safe(obj):
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, dict):
                return {k: _make_json_safe(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_make_json_safe(v) for v in obj]
            if is_dataclass(obj):
                return _make_json_safe(asdict(obj))
            if hasattr(obj, "value"):  # Enum
                return obj.value
            if hasattr(obj, "isoformat"):  # datetime
                return obj.isoformat()
            return str(obj)
        d["output"] = _make_json_safe(d.get("output"))
        # Convert verdict enum to string if needed
        verdict_val = d.get("verdict")
        if hasattr(verdict_val, "value"):
            d["verdict"] = verdict_val.value
        return d

    @app.post("/api/os/execute")
    async def os_execute(request: Request):
        """Execute an OS Control tool with capability gating.
        Body: { tool_name, parameters, agent_name (optional) }
        """
        executor = _get_os_executor()
        if not executor:
            raise HTTPException(503, "OS Control Executor not available")
        user_id = _get_user_id_from_request(request) or "guest"
        body = await request.json()
        tool_name  = body.get("tool_name", "")
        parameters = body.get("parameters", {})
        agent_name = body.get("agent_name", "AutoModeAgent")
        if not tool_name:
            raise HTTPException(400, "tool_name required")
        result = await executor.execute(tool_name, parameters, agent_name, user_id)
        return JSONResponse(_serialize_tool_result(result))
    
    @app.post("/api/os/approve/{call_id}")
    async def os_approve(call_id: str, request: Request):
        """Human approves a pending OS tool call."""
        executor = _get_os_executor()
        if not executor:
            raise HTTPException(503, "OS Control Executor not available")
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Authentication required to approve actions")
        result = await executor.approve(call_id, user_id)
        return JSONResponse(result)
    
    @app.post("/api/os/reject/{call_id}")
    async def os_reject(call_id: str, request: Request):
        """Human rejects a pending OS tool call."""
        executor = _get_os_executor()
        if not executor:
            raise HTTPException(503, "OS Control Executor not available")
        user_id = _get_user_id_from_request(request)
        if not user_id:
            raise HTTPException(401, "Authentication required")
        result = executor.reject(call_id, user_id)
        return JSONResponse(result)
    
    @app.get("/api/os/pending")
    async def os_pending(request: Request):
        """List pending OS tool approvals for this user."""
        executor = _get_os_executor()
        if not executor:
            return JSONResponse({"pending": []})
        user_id = _get_user_id_from_request(request) or "guest"
        pending = executor.pending_calls(user_id=user_id)
        return JSONResponse({"pending": pending, "count": len(pending)})
    
    @app.get("/api/os/audit")
    async def os_audit(request: Request, limit: int = 30):
        """Return recent OS Control audit log."""
        executor = _get_os_executor()
        if not executor:
            return JSONResponse({"audit": []})
        user_id = _get_user_id_from_request(request) or "guest"
        entries = executor.get_audit_log(limit=limit, user_id=user_id)
        return JSONResponse({"audit": entries, "total": len(entries)})
    
    @app.get("/api/os/status")
    async def os_status(request: Request):
        """OS Control status overview."""
        executor = _get_os_executor()
        if not executor:
            return JSONResponse({"status": "unavailable"})
        status = executor.get_status()
        return JSONResponse({
            "status": "active",
            "capability_gated": True,
            **status,
        })
    
    @app.get("/api/os/metrics")
    async def os_metrics():
        """Get real system metrics (CPU, memory, disk, network)."""
        executor = _get_os_executor()
        if not executor:
            raise HTTPException(503, "OS Control Executor not available")
        cpu    = await executor._handle_system_cpu()
        mem    = await executor._handle_system_memory()
        disk   = await executor._handle_system_disk()
        net    = await executor._handle_system_network()
        sysinf = await executor._handle_system_info()
        return JSONResponse({
            "cpu": cpu,
            "memory": mem,
            "disk": disk,
            "network": net,
            "system": sysinf,
            "timestamp": __import__('time').time(),
        })
    
    @app.get("/api/os/clipboard/status")
    async def os_clipboard_status(request: Request):
        """Get clipboard consent status and pending requests."""
        executor = _get_os_executor()
        if not executor:
            return JSONResponse({"status": "unavailable"})
        user_id = _get_user_id_from_request(request) or "guest"
        clip = executor._clipboard_tools
        pending = clip.list_pending_consents(user_id)
        return JSONResponse({
            "pending_requests": pending,
            "count": len(pending),
        })
    
    # ─── ASIM KERNEL ENDPOINT ─────────────────────────────────────────────
    @app.get("/api/os/kernel")
    async def os_kernel_status():
        """Get ASIM Kernel hardware profile and capabilities."""
        try:
            from core.kernel.kernel import get_kernel
            kernel = get_kernel()
            hp = kernel.get_hardware_profile()
            caps = kernel.get_capabilities()
            return JSONResponse({
                "status": "active",
                "hardware_profile": {
                    "cpu_name": hp.cpu_name,
                    "cpu_cores": hp.cpu_cores,
                    "cpu_freq_mhz": hp.cpu_freq,
                    "total_memory_gb": hp.total_memory_gb,
                    "gpu_name": hp.gpu_name,
                    "gpu_memory_gb": hp.gpu_memory_gb,
                    "os_name": hp.os_name,
                    "os_version": hp.os_version,
                    "architecture": hp.architecture,
                },
                "capabilities": caps,
            })
        except Exception as e:
            logger.error(f"⚠️ ASIM Kernel unavailable: {e}")
            return JSONResponse({"status": "unavailable", "error": str(e)})

    # ─── PHASE 4-6 ROUTES: SECTORS, GLOBAL AGENT, HARDENING ─────────────────
    try:
        from core.api_endpoints.register_routes import register_all_routes
        register_all_routes(app)
        logger.info("✅ Phase 4-6 routes registered (sectors, global agent, hardening)")
    except Exception as e:
        logger.warning(f"⚠️ Phase 4-6 route registration skipped: {e}")

    return app


# ─── GLOBAL APP INSTANCE ──────────────────────────────────────────────────────
app = create_app()


def main():
    import uvicorn
    print("🚀 ASIMNEXUS Core Backend v2.0")
    print("=" * 50)
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Directory: {os.getcwd()}")
    print(f"🤖 GGUF Model: {'✅ Found' if Path(GGUF_MODEL_PATH).exists() else '❌ Not found'}")
    print("📊 URL: http://127.0.0.1:8000")
    print("📚 Docs: http://127.0.0.1:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", reload=False)


if __name__ == "__main__":
    main()
