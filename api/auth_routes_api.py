"""
ASIMNEXUS Auth, Keys, Personal, Memory, Theme, Universe, Agent & Resource-Sharing Routes
=========================================================================================
Extracted from simple_backend.py into a modular APIRouter file.
"""

import logging
import json
import hashlib
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.API.Auth")

# ─── BCRYPT ─────────────────────────────────────────────────────────
try:
    import bcrypt
except ImportError:
    bcrypt = None

# ─── DB ─────────────────────────────────────────────────────────────
_current_dir = Path(__file__).parent.parent
DB_PATH = _current_dir / "data" / "asim_core.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ─── AUTH HELPERS ───────────────────────────────────────────────────
TOKEN_TTL_DAYS = 7


def _hash_password(pwd: str) -> str:
    if bcrypt:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(rounds=12)).decode()
    return hashlib.sha256(pwd.encode()).hexdigest()


def _verify_password(pwd: str, hashed: str) -> bool:
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


# ─── AGENT MODE HELPERS ─────────────────────────────────────────────
def _get_agent_mode(user_id: str) -> dict:
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
    try:
        with _get_db() as conn:
            conn.execute(
                "UPDATE users SET agent_mode_json=? WHERE id=?",
                (json.dumps(data), user_id)
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Agent mode persist error: {e}")


# ─── RESOURCE SHARING HELPERS ───────────────────────────────────────
def _get_resource_sharing(user_id: str) -> dict:
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
    try:
        with _get_db() as conn:
            conn.execute(
                "UPDATE users SET resource_sharing_json=? WHERE id=?",
                (json.dumps(data), user_id)
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Resource sharing persist error: {e}")


# ─── LOCAL LLM REFERENCE ────────────────────────────────────────────
_local_llm = None


# ─── ROUTER ─────────────────────────────────────────────────────────
router = APIRouter(tags=["Auth, Keys & User Profile"])


# ═════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.post("/auth/register")
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


@router.post("/auth/login")
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


@router.get("/auth/me")
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


# ═════════════════════════════════════════════════════════════════════
# API KEYS ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.get("/api/db/api-keys/{user_id}")
async def get_api_keys(user_id: str, request: Request):
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


@router.post("/api/keys/update")
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


@router.get("/api/db/health")
async def db_health():
    return JSONResponse({"status": "ok"})


# ═════════════════════════════════════════════════════════════════════
# PERSONAL ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.get("/personal/status")
async def personal_status(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    with _get_db() as conn:
        row = conn.execute("SELECT universe_mode,theme FROM users WHERE id=?", (user_id,)).fetchone()
    mode = dict(row)["universe_mode"] if row else "personal"
    theme = dict(row)["theme"] if row else "deep-space"
    return JSONResponse({"status": "active", "mode": mode, "theme": theme, "clones": 15})


@router.get("/personal/clones")
@router.get("/api/clones")
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


# ═════════════════════════════════════════════════════════════════════
# MEMORY / HISTORY ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.get("/api/memory/stats")
async def memory_stats(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    with _get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)).fetchone()[0]
    return JSONResponse({"total_messages": count, "status": "active"})


@router.get("/api/memory/recent")
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


@router.get("/api/memory/search")
async def memory_search(request: Request, q: str = ""):
    user_id = _get_user_id_from_request(request) or "guest"
    if not q:
        return JSONResponse({"memories": []})
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, role, content, clone_used, timestamp FROM messages "
            "WHERE user_id=? AND content LIKE ? ORDER BY timestamp DESC LIMIT 15",
            (user_id, f"%{q}%")
        ).fetchall()
    memories = [{"id": r["id"], "role": r["role"], "content": r["content"],
                 "clone": r["clone_used"] or "AsimNexus", "timestamp": r["timestamp"]} for r in rows]
    return JSONResponse({"memories": memories, "total": len(memories)})


@router.delete("/api/memory/{message_id}")
async def delete_memory(message_id: str, request: Request):
    user_id = _get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(401, "Unauthorized")
    with _get_db() as conn:
        conn.execute("DELETE FROM messages WHERE id=? AND user_id=?", (message_id, user_id))
        conn.commit()
    return JSONResponse({"success": True})


@router.get("/api/db/conversations/user/{user_id}")
async def user_conversations(user_id: str, request: Request):
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


# ═════════════════════════════════════════════════════════════════════
# THEME / UNIVERSE SET ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.post("/api/theme/set")
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


@router.post("/api/universe/set")
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


# ═════════════════════════════════════════════════════════════════════
# APIS STATUS
# ═════════════════════════════════════════════════════════════════════
@router.get("/api/apis/status")
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


# ═════════════════════════════════════════════════════════════════════
# AGENT MODE ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.post("/api/agent/mode/on")
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


@router.post("/api/agent/mode/off")
async def agent_mode_off(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    _set_agent_mode(user_id, {"active": False})
    return JSONResponse({
        "status": "agent_mode_off",
        "user_id": user_id,
        "message": "Your clone is now dormant. No new contracts accepted.",
    })


@router.get("/api/agent/status")
async def agent_status(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    info = _get_agent_mode(user_id)
    return JSONResponse({"user_id": user_id, **info})


# ═════════════════════════════════════════════════════════════════════
# RESOURCE SHARING ROUTES
# ═════════════════════════════════════════════════════════════════════
@router.post("/api/personal/resource-sharing")
async def set_resource_sharing(request: Request):
    user_id = _get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    body = await request.json()
    enabled = bool(body.get("enabled", False))
    pct = max(2, min(5, int(body.get("share_pct", 2))))
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


@router.get("/api/personal/resource-sharing")
async def get_resource_sharing_route(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    info = _get_resource_sharing(user_id)
    try:
        import psutil
        cpu = round(psutil.cpu_percent(interval=0.1), 1)
        ram = round(psutil.virtual_memory().percent, 1)
    except Exception:
        cpu = 0
        ram = 0
    return JSONResponse({
        "user_id": user_id,
        "resource_sharing": info.get("enabled", False),
        "share_pct": info.get("share_pct", 0),
        "cpu_total": cpu,
        "ram_total": ram,
        "mesh_peers": 0,
        "phase_note": "Phase 2 will connect real LAN peers",
    })


# ═════════════════════════════════════════════════════════════════════
# REGISTRATION
# ═════════════════════════════════════════════════════════════════════
def register_auth_routes(app):
    """Register all auth, keys, personal, memory, theme, universe, agent & resource-sharing routes."""
    app.include_router(router)
    logger.info("Auth, Keys, Personal, Memory, Theme, Universe, Agent & Resource-sharing routes registered")
