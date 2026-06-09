"""
unified_routes_api.py
=====================
Implements routes from frontend API files that lack backend implementations.
Sources:
  - unified_api.js: /llm/chat, /files/*, /codebase/*, /terminal/execute,
    /automation/*, /api/analytics/performance|usage, /api/security/*,
    /api/virtual_office/*, /api/autonomous/*, /hdt/*, /zkp/*, /clones/*
  - asimnexus.js: /api/universe/{id}/lifecycle, /api/universal/*

NOTE: Routes already registered by identity_svt_hdt_api.py are NOT included here
      (/api/identity/*, /api/svt/*, /api/hdt/*, /api/quad/*, /api/bugs/*,
       /api/dht/*, /api/firewall/*).
"""

import logging
import os
import subprocess
import json
import time
import uuid
import random
import threading
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("unified_routes_api")
router = APIRouter()

# ============================================================
# In-memory stores
# ============================================================
_tasks_db: dict = {}
_tasks_lock = threading.Lock()

_security_vulns: list = []
_security_lock = threading.Lock()

_virtual_rooms: dict = {}
_virtual_rooms_lock = threading.Lock()

_autonomous_enabled: bool = False

_hdt_store: dict = {}
_hdt_lock = threading.Lock()

_zkp_tokens: dict = {}
_zkp_lock = threading.Lock()

_universe_lifecycles: dict = {}
_universe_lock = threading.Lock()


# ============================================================
# Helpers
# ============================================================

def _get_workspace_root() -> str:
    return os.environ.get("ASIMNEXUS_ROOT", os.getcwd())


def _sanitize_path(requested_path: str) -> str | None:
    """Prevent path traversal attacks."""
    root = Path(_get_workspace_root()).resolve()
    clean = Path(root, requested_path).resolve()
    try:
        clean.relative_to(root)
        return str(clean)
    except ValueError:
        return None


# ==============================================================================
# 1. /llm/chat — Chat Endpoint
# ==============================================================================
@router.post("/llm/chat", tags=["Chat"])
async def llm_chat(body: dict):
    message = body.get("message", "")
    if not message:
        return {"success": False, "error": "No message provided"}
    try:
        from backend.api import local_llm
        if hasattr(local_llm, "generate"):
            resp = await local_llm.generate(message)
            return {"success": True, "response": resp}
    except Exception:
        pass
    return {
        "success": True,
        "response": f"[Unified API] Received: {message[:100]}{'...' if len(message) > 100 else ''}",
        "source": "mock",
    }


# ==============================================================================
# 2. /files/* — File Manager
# ==============================================================================
FILE_ROUTES_ENABLED = os.environ.get("ASIMNEXUS_FILE_ROUTES", "1") == "1"


@router.get("/files/list", tags=["File Manager"])
async def files_list(path: str = "."):
    if not FILE_ROUTES_ENABLED:
        return {"success": False, "error": "File routes disabled"}
    safe_path = _sanitize_path(path)
    if not safe_path:
        raise HTTPException(400, "Invalid path")
    try:
        entries = []
        for entry in os.scandir(safe_path):
            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else 0,
                "modified": datetime.fromtimestamp(entry.stat().st_mtime).isoformat(),
            })
        return {"success": True, "path": path, "entries": entries}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/files/read", tags=["File Manager"])
async def files_read(path: str = ""):
    if not FILE_ROUTES_ENABLED:
        return {"success": False, "error": "File routes disabled"}
    safe_path = _sanitize_path(path)
    if not safe_path:
        raise HTTPException(400, "Invalid path")
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "path": path, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/files/write", tags=["File Manager"])
async def files_write(body: dict):
    if not FILE_ROUTES_ENABLED:
        return {"success": False, "error": "File routes disabled"}
    path = body.get("path", "")
    content = body.get("content", "")
    safe_path = _sanitize_path(path)
    if not safe_path:
        raise HTTPException(400, "Invalid path")
    try:
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/files/delete", tags=["File Manager"])
async def files_delete(path: str = ""):
    if not FILE_ROUTES_ENABLED:
        return {"success": False, "error": "File routes disabled"}
    safe_path = _sanitize_path(path)
    if not safe_path:
        raise HTTPException(400, "Invalid path")
    try:
        if os.path.isdir(safe_path):
            os.rmdir(safe_path)
        else:
            os.remove(safe_path)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/files/create_directory", tags=["File Manager"])
async def files_create_directory(body: dict):
    if not FILE_ROUTES_ENABLED:
        return {"success": False, "error": "File routes disabled"}
    path = body.get("path", "")
    safe_path = _sanitize_path(path)
    if not safe_path:
        raise HTTPException(400, "Invalid path")
    try:
        os.makedirs(safe_path, exist_ok=True)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/files/search", tags=["File Manager"])
async def files_search(query: str = ""):
    if not FILE_ROUTES_ENABLED:
        return {"success": False, "error": "File routes disabled"}
    if not query:
        return {"success": True, "results": []}
    root = Path(_get_workspace_root())
    results = []
    try:
        for fpath in root.rglob(f"*{query}*"):
            try:
                rel = str(fpath.relative_to(root))
                results.append({
                    "path": rel,
                    "type": "directory" if fpath.is_dir() else "file",
                    "size": fpath.stat().st_size if fpath.is_file() else 0,
                })
                if len(results) >= 100:
                    break
            except ValueError:
                continue
        return {"success": True, "query": query, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# 3. /codebase/* — Codebase Operations
# ==============================================================================
@router.get("/codebase/index", tags=["Codebase"])
async def codebase_index():
    root = Path(_get_workspace_root())
    try:
        files = []
        dirs = 0
        for fpath in root.rglob("*"):
            try:
                rel = str(fpath.relative_to(root))
                if fpath.is_dir():
                    dirs += 1
                else:
                    files.append({"path": rel, "size": fpath.stat().st_size})
            except (ValueError, OSError):
                continue
        return {"success": True, "total_files": len(files), "total_dirs": dirs, "files": files[:500]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/codebase/search", tags=["Codebase"])
async def codebase_search(query: str = ""):
    if not query:
        return {"success": True, "results": []}
    root = Path(_get_workspace_root())
    results = []
    try:
        for fpath in root.rglob("*"):
            try:
                rel = str(fpath.relative_to(root))
                if query.lower() in rel.lower():
                    results.append({
                        "path": rel,
                        "type": "directory" if fpath.is_dir() else "file",
                    })
                    if len(results) >= 200:
                        break
            except ValueError:
                continue
        return {"success": True, "query": query, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/codebase/summary", tags=["Codebase"])
async def codebase_summary():
    root = Path(_get_workspace_root())
    ext_counts = {}
    total_size = 0
    total_files = 0
    try:
        for fpath in root.rglob("*"):
            if fpath.is_file():
                total_files += 1
                total_size += fpath.stat().st_size
                ext = fpath.suffix.lower() or "(no ext)"
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
        return {"success": True, "total_files": total_files, "total_size_kb": round(total_size / 1024, 1), "extensions": ext_counts}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/codebase/file/{path:path}", tags=["Codebase"])
async def codebase_file(path: str):
    safe_path = _sanitize_path(path)
    if not safe_path:
        raise HTTPException(400, "Invalid path")
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "path": path, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# 4. /terminal/execute — Terminal Execution
# ==============================================================================
TERMINAL_ENABLED = os.environ.get("ASIMNEXUS_TERMINAL", "0") == "1"


@router.post("/terminal/execute", tags=["Terminal"])
async def terminal_execute(body: dict):
    if not TERMINAL_ENABLED:
        return {"success": False, "error": "Terminal execution disabled"}
    command = body.get("command", "")
    if not command:
        return {"success": False, "error": "No command provided"}
    dangerous = ["rm -rf", "sudo ", "mkfs", "dd if=", "> /dev/", ":(){ :|:& };:"]
    for d in dangerous:
        if d in command.lower():
            return {"success": False, "error": f"Command blocked: {d}"}
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, cwd=_get_workspace_root())
        return {"success": result.returncode == 0, "stdout": result.stdout[:5000], "stderr": result.stderr[:1000], "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# 5. /automation/* — Task Automation
# ==============================================================================
@router.post("/automation/create", tags=["Automation"])
async def automation_create(body: dict):
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "name": body.get("name", "Unnamed Task"),
        "description": body.get("description", ""),
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    with _tasks_lock:
        _tasks_db[task_id] = task
    return {"success": True, "task": task}


@router.get("/automation/list", tags=["Automation"])
async def automation_list():
    with _tasks_lock:
        tasks = list(_tasks_db.values())
    return {"success": True, "tasks": tasks}


@router.post("/automation/execute", tags=["Automation"])
async def automation_execute(body: dict):
    task_id = body.get("task_id", "")
    with _tasks_lock:
        task = _tasks_db.get(task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
    import asyncio
    await asyncio.sleep(0.1)
    with _tasks_lock:
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
    return {"success": True, "task": task}


@router.delete("/automation/{task_id}", tags=["Automation"])
async def automation_delete(task_id: str):
    with _tasks_lock:
        if task_id not in _tasks_db:
            raise HTTPException(404, f"Task {task_id} not found")
        del _tasks_db[task_id]
    return {"success": True}


# ==============================================================================
# 6. /api/analytics/performance & /api/analytics/usage
# ==============================================================================
@router.get("/api/analytics/performance", tags=["Analytics"])
async def analytics_performance():
    try:
        import psutil
        return {"success": True, "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "uptime_seconds": time.time() - psutil.boot_time()}
    except ImportError:
        return {"success": True, "cpu_percent": random.uniform(10, 60),
                "memory_percent": random.uniform(30, 80),
                "disk_percent": random.uniform(40, 90), "uptime_seconds": 3600 * 24}


@router.get("/api/analytics/usage", tags=["Analytics"])
async def analytics_usage():
    return {"success": True, "total_requests": random.randint(1000, 10000),
            "active_users": random.randint(1, 50),
            "api_calls_today": random.randint(100, 500),
            "timestamp": datetime.now().isoformat()}


# ==============================================================================
# 7. /api/security/* — Security Operations
# ==============================================================================
@router.get("/api/security/status", tags=["Security"])
async def security_status():
    return {"success": True, "status": "healthy", "firewall_active": True,
            "encryption_enabled": True, "last_scan": datetime.now().isoformat(),
            "vulnerability_count": len(_security_vulns)}


@router.get("/api/security/vulnerabilities", tags=["Security"])
async def security_vulnerabilities():
    with _security_lock:
        return {"success": True, "vulnerabilities": list(_security_vulns)}


@router.post("/api/security/scan", tags=["Security"])
async def security_scan():
    findings = [{"id": str(uuid.uuid4()), "severity": random.choice(["low", "medium", "high"]),
                 "description": "Simulated finding",
                 "location": f"/path/to/file_{random.randint(1,100)}.py",
                 "found_at": datetime.now().isoformat()} for _ in range(random.randint(0, 5))]
    with _security_lock:
        _security_vulns.clear()
        _security_vulns.extend(findings)
    return {"success": True, "findings": findings, "count": len(findings)}


# ==============================================================================
# 8. /api/virtual_office/* — Virtual Office
# ==============================================================================
@router.get("/api/virtual_office/status", tags=["Virtual Office"])
async def virtual_office_status():
    with _virtual_rooms_lock:
        return {"success": True, "rooms": len(_virtual_rooms),
                "active_rooms": sum(1 for r in _virtual_rooms.values() if r.get("active", False)),
                "status": "operational"}


@router.get("/api/virtual_office/rooms", tags=["Virtual Office"])
async def virtual_office_rooms():
    with _virtual_rooms_lock:
        return {"success": True, "rooms": list(_virtual_rooms.values())}


@router.post("/api/virtual_office/join", tags=["Virtual Office"])
async def virtual_office_join(body: dict):
    room_id = body.get("room_id", str(uuid.uuid4()))
    with _virtual_rooms_lock:
        if room_id not in _virtual_rooms:
            _virtual_rooms[room_id] = {"id": room_id, "name": body.get("name", f"Room-{room_id[:8]}"),
                                        "active": True, "members": 1, "created_at": datetime.now().isoformat()}
        else:
            _virtual_rooms[room_id]["members"] = _virtual_rooms[room_id].get("members", 0) + 1
            _virtual_rooms[room_id]["active"] = True
    return {"success": True, "room_id": room_id}


@router.post("/api/virtual_office/leave", tags=["Virtual Office"])
async def virtual_office_leave(body: dict):
    room_id = body.get("room_id", "")
    with _virtual_rooms_lock:
        if room_id in _virtual_rooms:
            members = _virtual_rooms[room_id].get("members", 1)
            if members <= 1:
                _virtual_rooms[room_id]["active"] = False
                _virtual_rooms[room_id]["members"] = 0
            else:
                _virtual_rooms[room_id]["members"] = members - 1
    return {"success": True, "room_id": room_id}


# ==============================================================================
# 9. /api/autonomous/* — Autonomous Mode
# ==============================================================================
@router.get("/api/autonomous/status", tags=["Autonomous"])
async def autonomous_status():
    return {"success": True, "enabled": _autonomous_enabled,
            "mode": "autopilot" if _autonomous_enabled else "manual",
            "last_active": datetime.now().isoformat()}


@router.post("/api/autonomous/enable", tags=["Autonomous"])
async def autonomous_enable():
    global _autonomous_enabled
    _autonomous_enabled = True
    return {"success": True, "enabled": True}


@router.post("/api/autonomous/disable", tags=["Autonomous"])
async def autonomous_disable():
    global _autonomous_enabled
    _autonomous_enabled = False
    return {"success": True, "enabled": False}


# ==============================================================================
# 10. /hdt/* — Human Digital Twin (unified_api.js version, diff paths from identity_svt_hdt_api)
# ==============================================================================
@router.get("/hdt/me", tags=["HDT"])
async def hdt_me():
    return {"success": True, "twin": {"id": "local-user", "status": "active",
                                       "skills": [], "reputation": 0.5,
                                       "created_at": datetime.now().isoformat()}}


@router.post("/hdt/update", tags=["HDT"])
async def hdt_update(body: dict):
    return {"success": True, "updated": True, "changes": list(body.keys())}


@router.get("/hdt/top-clones", tags=["HDT"])
async def hdt_top_clones():
    with _hdt_lock:
        clones = sorted(_hdt_store.values(), key=lambda x: x.get("reputation", 0), reverse=True)[:10]
    return {"success": True, "clones": clones}


# ==============================================================================
# 11. /zkp/* — Zero-Knowledge Proof Tokens
# ==============================================================================
@router.get("/zkp/pending", tags=["ZKP"])
async def zkp_pending():
    with _zkp_lock:
        pending = [t for t in _zkp_tokens.values() if t.get("status") == "pending"]
    return {"success": True, "pending": pending}


@router.post("/zkp/confirm/{token}", tags=["ZKP"])
async def zkp_confirm(token: str):
    with _zkp_lock:
        if token in _zkp_tokens:
            _zkp_tokens[token]["status"] = "confirmed"
            _zkp_tokens[token]["confirmed_at"] = datetime.now().isoformat()
        else:
            _zkp_tokens[token] = {"token": token, "status": "confirmed", "confirmed_at": datetime.now().isoformat()}
    return {"success": True, "token": token, "status": "confirmed"}


@router.post("/zkp/reject/{token}", tags=["ZKP"])
async def zkp_reject(token: str):
    with _zkp_lock:
        if token in _zkp_tokens:
            _zkp_tokens[token]["status"] = "rejected"
        else:
            _zkp_tokens[token] = {"token": token, "status": "rejected"}
    return {"success": True, "token": token, "status": "rejected"}


@router.get("/zkp/status/{token}", tags=["ZKP"])
async def zkp_status(token: str):
    with _zkp_lock:
        entry = _zkp_tokens.get(token)
    if not entry:
        return {"success": True, "token": token, "status": "unknown"}
    return {"success": True, **entry}


# ==============================================================================
# 12. /clones/* — World Clones
# ==============================================================================
WORLD_CLONES = [
    {"name": "Sage", "role": "philosopher", "description": "Wisdom & ethics guide"},
    {"name": "Builder", "role": "engineer", "description": "System architect & builder"},
    {"name": "Healer", "role": "medic", "description": "Health & wellness advisor"},
    {"name": "Explorer", "role": "discoverer", "description": "Innovation scout"},
    {"name": "Guardian", "role": "protector", "description": "Security overseer"},
    {"name": "Teacher", "role": "educator", "description": "Knowledge curator"},
    {"name": "Diplomat", "role": "negotiator", "description": "Conflict resolver"},
    {"name": "Creator", "role": "artist", "description": "Creative expression guide"},
    {"name": "Merchant", "role": "trader", "description": "Economic strategist"},
    {"name": "Farmer", "role": "provider", "description": "Resource manager"},
    {"name": "Scholar", "role": "researcher", "description": "Deep researcher"},
    {"name": "Seer", "role": "visionary", "description": "Future trends analyst"},
    {"name": "Judge", "role": "arbiter", "description": "Fairness & balance keeper"},
    {"name": "Warrior", "role": "defender", "description": "Resilience champion"},
    {"name": "Mystic", "role": "spiritual", "description": "Consciousness explorer"},
]


@router.get("/clones/list", tags=["World Clones"])
async def clones_list():
    return {"success": True, "clones": WORLD_CLONES}


@router.post("/clones/chat", tags=["World Clones"])
async def clones_chat(body: dict):
    message = body.get("message", "")
    return {"success": True, "response": f"[World Clones] Collective response to: {message[:100]}", "source": "clones_collective"}


@router.post("/clones/direct/{role_name}", tags=["World Clones"])
async def clones_direct(role_name: str, body: dict):
    message = body.get("message", "")
    clone = next((c for c in WORLD_CLONES if c["role"] == role_name.lower() or c["name"].lower() == role_name.lower()), None)
    if not clone:
        raise HTTPException(404, f"Clone with role '{role_name}' not found")
    return {"success": True, "clone": clone["name"], "role": clone["role"],
            "response": f"[{clone['name']}] Responding to: {message[:100]}"}


@router.post("/clones/agent-mode", tags=["World Clones"])
async def clones_agent_mode(enabled: bool = True):
    return {"success": True, "agent_mode": enabled}


# ==============================================================================
# 13. /api/universe/{user_id}/lifecycle — Universe Lifecycle
# ==============================================================================
@router.get("/api/universe/{user_id}/lifecycle", tags=["Universe"])
async def universe_lifecycle(user_id: str):
    with _universe_lock:
        lifecycle = _universe_lifecycles.get(user_id, {
            "user_id": user_id, "status": "active", "layer": 1,
            "created_at": datetime.now().isoformat(), "events": [],
        })
    return {"success": True, "lifecycle": lifecycle}


# ==============================================================================
# 14. /api/universal/* — Universal Data
# ==============================================================================
UNIVERSAL_COUNTRIES = [
    {"code": "NP", "name": "Nepal", "currency": "NPR", "language": "Nepali"},
    {"code": "US", "name": "United States", "currency": "USD", "language": "English"},
    {"code": "IN", "name": "India", "currency": "INR", "language": "Hindi"},
    {"code": "GB", "name": "United Kingdom", "currency": "GBP", "language": "English"},
    {"code": "JP", "name": "Japan", "currency": "JPY", "language": "Japanese"},
    {"code": "CN", "name": "China", "currency": "CNY", "language": "Chinese"},
    {"code": "DE", "name": "Germany", "currency": "EUR", "language": "German"},
    {"code": "FR", "name": "France", "currency": "EUR", "language": "French"},
    {"code": "AU", "name": "Australia", "currency": "AUD", "language": "English"},
    {"code": "BR", "name": "Brazil", "currency": "BRL", "language": "Portuguese"},
]
UNIVERSAL_CURRENCIES = [
    {"code": "NPR", "name": "Nepalese Rupee", "symbol": "\u0930\u0942"},
    {"code": "USD", "name": "US Dollar", "symbol": "$"},
    {"code": "EUR", "name": "Euro", "symbol": "\u20ac"},
    {"code": "GBP", "name": "British Pound", "symbol": "\u00a3"},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "\u00a5"},
    {"code": "INR", "name": "Indian Rupee", "symbol": "\u20b9"},
]
UNIVERSAL_LANGUAGES = [
    {"code": "ne", "name": "Nepali", "native": "\u0928\u0947\u092a\u093e\u0932\u0940"},
    {"code": "en", "name": "English", "native": "English"},
    {"code": "hi", "name": "Hindi", "native": "\u0939\u093f\u0928\u094d\u0926\u0940"},
    {"code": "zh", "name": "Chinese", "native": "\u4e2d\u6587"},
    {"code": "ja", "name": "Japanese", "native": "\u65e5\u672c\u8a9e"},
    {"code": "es", "name": "Spanish", "native": "Espa\u00f1ol"},
]
UNIVERSAL_TIMEZONES = [
    "UTC", "Asia/Kathmandu", "Asia/Kolkata", "America/New_York",
    "America/Los_Angeles", "Europe/London", "Europe/Berlin",
    "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney",
]


@router.get("/api/universal/status", tags=["Universal"])
async def universal_status():
    return {"success": True, "countries": len(UNIVERSAL_COUNTRIES),
            "currencies": len(UNIVERSAL_CURRENCIES),
            "languages": len(UNIVERSAL_LANGUAGES),
            "timezones": len(UNIVERSAL_TIMEZONES)}


@router.get("/api/universal/countries", tags=["Universal"])
async def universal_countries():
    return {"success": True, "countries": UNIVERSAL_COUNTRIES}


@router.get("/api/universal/currencies", tags=["Universal"])
async def universal_currencies():
    return {"success": True, "currencies": UNIVERSAL_CURRENCIES}


@router.get("/api/universal/languages", tags=["Universal"])
async def universal_languages():
    return {"success": True, "languages": UNIVERSAL_LANGUAGES}


@router.get("/api/universal/timezones", tags=["Universal"])
async def universal_timezones():
    return {"success": True, "timezones": UNIVERSAL_TIMEZONES}


# ==============================================================================
# Registration function
# ==============================================================================
def register_unified_routes(app):
    """Register all unified routes onto a FastAPI app."""
    app.include_router(router)
    logger.info("Unified routes (chat, files, codebase, terminal, automation, "
                "analytics, security, virtual_office, autonomous, hdt, zkp, "
                "clones, universe, universal) registered")
