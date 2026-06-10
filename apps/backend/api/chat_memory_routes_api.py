import logging, json, os, sys, secrets, hashlib, asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

logger = logging.getLogger("AsimNexus.ChatMemory")

router = APIRouter(tags=["Chat, Brain & Memory"])

# ─── SQLite DB ────────────────────────────────────────────────────────────────
import sqlite3
DB_PATH = Path(__file__).parent.parent / "data" / "asim_core.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────
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

# ─── MODULE-LEVEL GLOBALS (mirrored from simple_backend) ──────────────────────
_local_llm = None

try:
    from core.founder_clones.world_clones import WorldCloneOrchestrator
    _clones = WorldCloneOrchestrator()
except Exception:
    _clones = None

try:
    from core.routing.hybrid_router import HybridRouter
    _router = HybridRouter(prefer_local=True, offline_mode=False)
except Exception:
    _router = None

try:
    from core.dharma_chakra.safety_veto import SafetyVeto
    _veto = SafetyVeto()
except Exception:
    _veto = None

_os_executor = None

def _get_os_executor():
    global _os_executor
    if _os_executor is None:
        try:
            from os_control.os_tool_executor import get_os_tool_executor
            _os_executor = get_os_tool_executor()
            logger.info("OS Control Executor loaded with %d tools", len(_os_executor.tool_registry.list_tools()))
        except Exception as e:
            logger.error("OS Control Executor unavailable: %s", e)
            _os_executor = None
    return _os_executor

def _serialize_tool_result(result) -> dict:
    from dataclasses import is_dataclass, asdict
    if is_dataclass(result):
        d = asdict(result)
    elif isinstance(result, dict):
        d = result
    else:
        return {"success": False, "error": f"Unserializable result type: {type(result).__name__}"}
    def _make_json_safe(obj):
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: _make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_make_json_safe(v) for v in obj]
        if is_dataclass(obj):
            return _make_json_safe(asdict(obj))
        if hasattr(obj, "value"):
            return obj.value
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)
    d["output"] = _make_json_safe(d.get("output"))
    verdict_val = d.get("verdict")
    if hasattr(verdict_val, "value"):
        d["verdict"] = verdict_val.value
    return d

# ─── THEME / UNIVERSE COMMANDS ────────────────────────────────────────────────
THEME_COMMANDS = {
    "dark mode": "deep-space", "dark": "deep-space", "\u0930\u093e\u0924": "deep-space",
    "light mode": "aurora", "light": "aurora", "\u092c\u093f\u0939\u093e\u0928": "aurora",
    "government": "government", "\u0938\u0930\u0915\u093e\u0930": "government",
    "company": "corporate", "corporate": "corporate", "\u0915\u092e\u094d\u092a\u0928\u0940": "corporate",
    "medical": "medical", "health": "medical", "health theme": "medical",
    "simple": "minimal", "minimal": "minimal", "\u0938\u091c\u093f\u0932\u094b": "minimal",
}
UNIVERSE_COMMANDS = {
    "personal universe": "personal", "personal": "personal", "\u0935\u094d\u092f\u0915\u094d\u0924\u093f\u0917\u0924": "personal",
    "family universe": "family", "family": "family", "\u092a\u0930\u093f\u0935\u093e\u0930": "family",
    "community universe": "community", "community": "community", "\u0938\u092e\u0941\u0926\u093e\u092f": "community",
    "company universe": "company", "company mode": "company",
    "government universe": "government", "government mode": "government",
    "global universe": "global", "global": "global", "\u0935\u093f\u0936\u094d\u0935": "global",
}

def _parse_chat_command(message: str) -> Optional[Dict]:
    msg_lower = message.lower().strip()
    for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
        if provider in msg_lower and ("key" in msg_lower or "api" in msg_lower):
            parts = message.split()
            for part in parts:
                if part.startswith("sk-") or part.startswith("AIza") or len(part) > 30:
                    return {"type": "api_key", "provider": provider, "key": part}
    for cmd, theme in THEME_COMMANDS.items():
        if cmd in msg_lower:
            return {"type": "theme", "value": theme}
    for cmd, universe in UNIVERSE_COMMANDS.items():
        if cmd in msg_lower:
            return {"type": "universe", "value": universe}
    if "2-5% sharing" in msg_lower or "resource sharing" in msg_lower or "sharing \u0938\u0915\u094d\u0930\u093f\u092f" in msg_lower:
        return {"type": "mesh_sharing", "value": True}
    if msg_lower.startswith("/os "):
        parts = message.split(maxsplit=2)
        tool_name = parts[1] if len(parts) > 1 else ""
        params_str = parts[2] if len(parts) > 2 else "{}"
        try:
            params = json.loads(params_str) if isinstance(params_str, str) else {}
        except json.JSONDecodeError:
            params = {"raw": params_str}
        return {"type": "os", "tool_name": tool_name, "parameters": params}
    if msg_lower in ("/os", "/os status", "/os help"):
        return {"type": "os", "tool_name": "help", "parameters": {}}
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

# ─── LLM HELPERS ──────────────────────────────────────────────────────────────
def _strip_thinking(text: str) -> str:
    import re
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    lines = text.split('\n')
    clean = []
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(p) for p in ["Alright,", "I need to", "The user", "Let me", "I should", "I'll", "I'm going to", "So I", "First,", "Now,"]) and not clean:
            continue
        clean.append(line)
    return '\n'.join(clean).strip()

async def _generate_local(prompt: str, system: str = "") -> Optional[str]:
    if _local_llm is None:
        return None
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        result = _local_llm.create_chat_completion(messages=messages, max_tokens=1024, temperature=0.7)
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Local LLM error: {e}")
        return None

async def _generate_cloud(prompt: str, provider: str, api_key: str, system: str = "") -> Optional[str]:
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
        payload = {"model": model, "messages": [m for m in messages if m["role"] != "system"], "system": system, "max_tokens": 1024}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if provider == "anthropic":
                    return data["content"][0]["text"]
                return data["choices"][0]["message"]["content"]
    return None

async def _smart_generate(prompt: str, user_id: str, system: str = "") -> Dict:
    local_resp = await _generate_local(prompt, system)
    if local_resp:
        return {"response": _strip_thinking(local_resp), "source": "local_gguf", "model": "Qwen3-4B"}
    with _get_db() as conn:
        row = conn.execute("SELECT api_keys FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        api_keys = json.loads(row["api_keys"] or "{}")
        for provider in ["openai", "anthropic", "gemini", "deepseek", "grok"]:
            if provider in api_keys and api_keys[provider]:
                cloud_resp = await _generate_cloud(prompt, provider, api_keys[provider], system)
                if cloud_resp:
                    return {"response": cloud_resp, "source": "cloud", "model": provider}
    return {"response": f"AsimNexus (offline): Received '{prompt[:60]}...'. Add API key for better responses.", "source": "fallback", "model": "fallback"}

# ─── CHAT ROUTES ──────────────────────────────────────────────────────────────
@router.post("/chat")
@router.post("/llm/chat")
@router.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "").strip()
    user_id = _get_user_id_from_request(request) or "guest"
    if not message:
        raise HTTPException(400, "Message required")
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
                "response": f"✅ {cmd['provider'].upper()} API key saved!",
                "source": "system", "command": cmd
            })
        if cmd["type"] == "theme" and user_id != "guest":
            with _get_db() as conn:
                conn.execute("UPDATE users SET theme=? WHERE id=?", (cmd["value"], user_id))
                conn.commit()
            return JSONResponse({
                "response": f"🎨 Theme changed to '{cmd['value']}'! UI automatically updated.",
                "source": "system", "command": cmd
            })
        if cmd["type"] == "universe" and user_id != "guest":
            with _get_db() as conn:
                conn.execute("UPDATE users SET universe_mode=? WHERE id=?", (cmd["value"], user_id))
                conn.commit()
            return JSONResponse({
                "response": f"🌌 Universe mode set to '{cmd['value']}'! AsimNexus adapted.",
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
                result = await executor.execute(tool_name, parameters, "AutoModeAgent", user_id)
                result_dict = _serialize_tool_result(result)
                verdict = result_dict.get("verdict", "")
                if verdict in ("allowed",) and result_dict.get("output") is not None:
                    output = result_dict["output"]
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
    result = await _smart_generate(message, user_id, system_prompt)
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

# ─── ASIM BRAIN ENDPOINTS ─────────────────────────────────────────────────────
@router.post("/api/brain/process")
async def brain_process(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        user_id = _get_user_id_from_request(request) or "guest"
        mode = body.get("mode", "personal")
        if not message:
            return JSONResponse({"response": "No message provided.", "source": "error", "timestamp": datetime.now().isoformat()})
        system = "You are Asim, the AI assistant for AsimNexus — a World Operating System. Help users with health, work, AI agents, mesh networks, governance, and digital identity. Be helpful, concise, and friendly."
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

@router.post("/api/brain/stream")
async def brain_stream(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        user_id = _get_user_id_from_request(request) or "guest"
        if not message:
            return JSONResponse({"error": "No message provided"}, status_code=400)
        system = "You are Asim, the AI assistant for AsimNexus. Be helpful and concise."
        async def event_generator():
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

# ─── WEBSOCKET CHAT ──────────────────────────────────────────────────────────
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_message = msg.get("message", "")
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

# ─── MEMORY / HISTORY ROUTES ──────────────────────────────────────────────────
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

# ─── REGISTRATION ─────────────────────────────────────────────────────────────
def register_chat_routes(app):
    app.include_router(router)
    logger.info("✅ Chat, Brain & Memory routes registered")
