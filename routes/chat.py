"""
Chat, Brain, and Agent Routes
=============================
Endpoints for chat, brain processing, agent loop, streaming,
and the legacy /chat, /llm/chat, /api/chat endpoints.
"""

import asyncio
import json
import re
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from routes.response import ok, error, unavailable

logger = logging.getLogger("AsimNexus.Routes.Chat")

router = APIRouter(tags=["Chat & Brain"])

# Will be set by init function
orchestrator = None
LLM_AVAILABLE = False
CLONES_AVAILABLE = False
WORLD_CLONE_CONFIGS = []
local_llm = None


def init_chat(app_globals: dict) -> None:
    """Initialize chat module from app.py globals."""
    global orchestrator, LLM_AVAILABLE, CLONES_AVAILABLE, WORLD_CLONE_CONFIGS, local_llm
    orchestrator = app_globals.get("orchestrator")
    LLM_AVAILABLE = app_globals.get("LLM_AVAILABLE", False)
    CLONES_AVAILABLE = app_globals.get("CLONES_AVAILABLE", False)
    WORLD_CLONE_CONFIGS = app_globals.get("WORLD_CLONE_CONFIGS", [])
    local_llm = app_globals.get("local_llm")


# ─── Shared brain processing logic ────────────────────────────────────────

async def _process_brain_message(message: str, clone: str = "auto", mode: str = "personal"):
    """Shared logic for processing brain messages."""
    import json
    import re

    # Check for tool command pattern: "tool.name: {params}"
    tool_match = re.match(r'^(\w+(?:\.\w+)+)\s*:\s*(\{.*\})?', message.strip())
    if tool_match:
        tool_id = tool_match.group(1)
        params_str = tool_match.group(2)
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                params = {"raw": params_str}
        try:
            from core.orchestrator.os_tool_executor import get_os_tool_executor
            executor = get_os_tool_executor()
            result = executor.execute_tool(tool_id, params, "AutoModeAgent", "web_user")
            return {"response": result.get("result", str(result)), "source": "tool"}
        except Exception as e:
            return {"response": f"⚠️ Tool execution error: {e}", "source": "error"}

    # Try orchestrator first — with timeout to avoid hanging on human approval
    if orchestrator:
        try:
            result = await asyncio.wait_for(
                orchestrator.process("web_user", message, mode),
                timeout=5.0
            )
            if result and "audit_id" in result:
                return {"response": result.get("message", ""), "source": "orchestrator", "audit_id": result["audit_id"]}
        except asyncio.TimeoutError:
            logger.warning("Orchestrator process timed out (human approval wait), falling through")
        except Exception as e:
            logger.warning(f"Orchestrator process failed: {e}")

    # Fallback to LLM gateway — only if gateway is actually initialized
    if LLM_AVAILABLE:
        try:
            from core.gateway.unified_llm_gateway import unified_llm_gateway, LLMProvider, UnifiedCompletionRequest
            # Check if gateway is actually initialized (has providers configured)
            if not (unified_llm_gateway and hasattr(unified_llm_gateway, 'providers') and unified_llm_gateway.providers):
                logger.debug("LLM gateway not initialized, skipping")
            else:
                system_prompt = "You are Asim, a helpful AI assistant for the AsimNexus World OS."
                if CLONES_AVAILABLE and clone != "auto":
                    for cfg in WORLD_CLONE_CONFIGS:
                        if cfg.role.value == clone:
                            system_prompt = cfg.system_prompt
                            break

                req = UnifiedCompletionRequest(
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
                    provider=LLMProvider.LOCAL,
                    temperature=0.7,
                    max_tokens=512,
                )
                response = await unified_llm_gateway.complete(req)
                return {"response": response.text, "source": "llm", "clone_used": clone}
        except Exception as e:
            logger.warning(f"LLM gateway failed: {e}")

    # Ultimate fallback
    return _smart_response(message, clone)


def _smart_response(message: str, clone: str, system_prompt: str = None, rag_context: str = None):
    """Fallback smart responses without LLM - Asim Nexus AI Assistant"""
    lower_msg = message.lower().strip()

    if system_prompt and "tech architect" in system_prompt.lower():
        response = f"🌌 **Asim**\n\n{message}\n\nम तपाईंको Asim हुँ — तकनीकी सल्लाहकारी। के म तपाईंलाई कसरी मद्दत गर्न सक्छु?"
    elif system_prompt and "health" in system_prompt.lower():
        response = f"🌌 **Asim**\n\n{message}\n\nस्वास्थ्य सम्बन्धी कुरा तथ्याङ्कहरू वा प्रश्नहरू बताउनुहोस्।"
    elif system_prompt and "finance" in system_prompt.lower():
        response = f"🌌 **Asim**\n\n{message}\n\nम तपाईंको वित्तीय सल्लाहकारी हुँ। वित्तीय सल्लाहका लागि।"
    elif "hey" in lower_msg or "hello" in lower_msg or "hi" in lower_msg or "नमस्ते" in lower_msg:
        response = "🌌 **Asim**\n\nNamaste! म तपाईंको Asim हुँ — तपाईंको विश्व OS सहयोगी।\n\nकसरी मद्दत गर्न सक्छु? 🏥 Health · 💼 Work · 🤖 Agents · 🌐 Mesh · ⚖️ Governance · 💰 Wallet"
    elif "health" in lower_msg or "swasthya" in lower_msg or "स्वास्थ्य" in lower_msg:
        response = "🌌 **Asim**\n\n**स्वास्थ्य ड्यासबोर्ड**\n\n• रकतचाप: 120/80 mmHg (साधारण)\n• हृदयगति: 72 bpm (विश्राम)\n• निद्रा: 7.5 घण्टा\n• आजको चरण: 8,432\n\nसिफारिसहरू: 2L पानी, 30 मिनेट मेडिटेसन"
    elif "work" in lower_msg or "काम" in lower_msg:
        response = "🌌 **Asim**\n\n**काम मोड**\n\n• अनुबन्धहरू: ३ सक्रिय\n• माइलो: २/५ पूरा\n• आमदनी: $20,800 यस महिना\n• एजेन्टहरू काम गरिरहेका छन्"
    elif "mesh" in lower_msg or "जालो" in lower_msg:
        response = "🌌 **Asim**\n\n**मेष जाल जानकारी**\n\n• नोडहरू: ३ जडान भएका\n• आज: ४५ MB अपलोड, १२८ MB डाउनलोड\n• स्थिति: अनलाइन र सिङ्क भएको"
    elif "agent" in lower_msg or "क्लोन" in lower_msg or "hire" in lower_msg or "एजेन्ट" in lower_msg:
        response = "🌌 **Asim**\n\n**AI एजेन्टहरू**\n\nउपलब्ध: Tech Architect, Data Engineer, Security Sentinel, Health Sage\nकमाण्डहरू: /hire · /pause · /budget"
    elif rag_context:
        response = f"🌌 **Asim**\n\nतपाईंको प्रश्नको लागि मैले AsimNexus Knowledge Base (Neutron Star) बाट यी जानकारीहरू फेला पारेको छु:\n\n{rag_context}"
    elif message.strip():
        response = f"🌌 **Asim**\n\nReceived: {message}\n\nम तपाईंलाई कसरी मद्दत गर्न सक्छु? 🏥 स्वास्थ्य · 💼 काम · 🌐 मेष · 🤖 एजेन्टहरू · 💰 वालेट"
    else:
        response = "🌌 **Asim**\n\nNamaste! म तपाईंको Asim हुँ। के बताउन चाहनुहुन्छ?"

    return {
        "response": response,
        "source": "asim_nexus",
        "clone_used": clone
    }


# ─── Chat Endpoints ───────────────────────────────────────────────────────

@router.post("/api/brain/process")
async def brain_process(data: dict = Body(...)):
    """
    Process chat message and return AI response.
    Used by AsimBrainService.js in frontend.
    Priority: Orchestrator -> Fallback
    """
    try:
        message = data.get("message", "")
        context = data.get("context", {})
        clone = context.get("clone", "auto")
        return await _process_brain_message(message, clone, context.get("mode", "personal"))
    except Exception as e:
        return error(str(e))


@router.post("/api/brain/stream")
async def brain_stream(data: dict = Body(...)):
    """Stream chat response from Asim Brain — frontend compatibility"""
    try:
        message = data.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message required")

        from fastapi.responses import StreamingResponse

        async def event_generator():
            result = await _process_brain_message(message, "auto", "personal")
            response_text = result.get("response", "")
            yield f"data: {json.dumps({'token': response_text})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Agent Loop Endpoints ─────────────────────────────────────────────────

@router.post("/api/agent/run")
async def agent_run(data: dict = Body(...)):
    """Execute agent loop with AUTO/GUIDE/PLAN/OBSERVE modes."""
    message = data.get("user_input", "")
    mode = data.get("mode", "AUTO")

    result = await _process_brain_message(message, "auto", mode)

    return ok(data={
        "result": result.get("response", ""),
        "session_id": None,
        "steps": [{
            "type": "llm_response",
            "status": "completed",
            "result": result.get("response", ""),
            "ts": datetime.now().isoformat()
        }]
    })


@router.post("/api/agent/cancel")
async def agent_cancel(data: dict = Body(...)):
    """Cancel agent session (placeholder)."""
    return ok(data={"cancelled": True})


@router.get("/api/agent/sessions")
async def agent_sessions():
    """List agent sessions (placeholder)."""
    return ok(data={"sessions": []})


@router.get("/api/agent/stats")
async def agent_stats():
    """Agent statistics (placeholder)."""
    return ok(data={"stats": {"total_sessions": 0, "active": 0}})


@router.get("/api/agent/status/{session_id}")
async def agent_status(session_id: str):
    """Get session status (placeholder)."""
    return ok(data={"status": "none", "session_id": session_id})


# ─── Legacy Chat Endpoints ────────────────────────────────────────────────

@router.post("/chat")
@router.post("/llm/chat")
@router.post("/api/chat")
async def chat(data: dict = Body(...)):
    """Legacy chat endpoint — handles multiple paths."""
    message = data.get("message", "").strip()
    user_id = data.get("user_id", "web_user") or "guest"
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    # Zero-Trust cap check
    try:
        from core.security.zero_trust import ZeroTrustManager
        zt = ZeroTrustManager()
        if not zt.check_capability(user_id, "SEND_MESSAGE"):
            return {"response": "❌ Access denied: Missing SEND_MESSAGE capability", "source": "zero_trust"}
    except ImportError:
        pass

    # Check for tool command
    try:
        from core.orchestrator.tool_registry import tool_registry
        tool_match = re.match(r'^/(\w+)\s*(.*)', message)
        if tool_match:
            cmd = tool_match.group(1)
            args = tool_match.group(2).strip()
            if cmd == "help":
                tools = [{"name": r.tool_id, "description": r.description} for r in tool_registry.list_tools()]
                return {"response": f"Available tools: {json.dumps(tools, indent=2)}", "source": "tool"}
            for t in tool_registry.list_tools():
                if t.tool_id == cmd:
                    from core.orchestrator.os_tool_executor import get_os_tool_executor
                    executor = get_os_tool_executor()
                    params = {}
                    if args:
                        try:
                            params = json.loads(args)
                        except json.JSONDecodeError:
                            params = {"input": args}
                    result = executor.execute_tool(cmd, params, "AutoModeAgent", user_id)
                    return {"response": result.get("result", str(result)), "source": "tool"}
    except ImportError:
        pass

    # Try orchestrator
    if orchestrator:
        try:
            result = await orchestrator.process_message(message, "auto", "personal")
            if result and "response" in result:
                return result
        except Exception:
            pass

    # Try LLM gateway — only if gateway is actually initialized
    if LLM_AVAILABLE:
        try:
            from core.gateway.unified_llm_gateway import unified_llm_gateway, LLMProvider, UnifiedCompletionRequest
            # Check if gateway is actually initialized (has providers configured)
            if unified_llm_gateway and hasattr(unified_llm_gateway, 'providers') and unified_llm_gateway.providers:
                req = UnifiedCompletionRequest(
                    messages=[{"role": "user", "content": message}],
                    provider=LLMProvider.OLLAMA,
                    temperature=0.7,
                    max_tokens=512,
                )
                response = await unified_llm_gateway.complete(req)
                return {"response": response.text, "source": "llm"}
        except Exception:
            pass

    # Fallback
    return _smart_response(message, "auto")


# ─── OmniChat Endpoints ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    mode: Optional[str] = "citizen"
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    status: str
    response: str
    source: str = "asim_nexus"
    audit_id: Optional[str] = None


@router.post("/api/v1/chat", tags=["OmniChat"])
async def omni_chat(req: ChatRequest):
    """
    OmniChat endpoint — unified chat for all modes.
    Supports citizen, company, government, and hybrid modes.
    """
    result = await _process_brain_message(req.message, "auto", req.mode)
    audit_id = result.get("audit_id") or str(uuid.uuid4())
    return ok(data={
        "response": result.get("response", ""),
        "source": result.get("source", "asim_nexus"),
        "audit_id": audit_id,
    })


@router.post("/api/v1/orchestrator/process", tags=["OmniChat"])
async def orchestrator_process(req: dict = Body(...)):
    """
    Orchestrator process endpoint — routes to appropriate handler.
    """
    try:
        message = req.get("message", "")
        context = req.get("context", {})
        clone = context.get("clone", "auto")
        mode = context.get("mode", "personal")

        if orchestrator:
            result = await orchestrator.process_message(message, clone, mode)
            if result:
                return result

        return await _process_brain_message(message, clone, mode)
    except Exception as e:
        return error(str(e))


@router.get("/api/v1/orchestrator/status", tags=["OmniChat"])
async def orchestrator_status():
    """Get orchestrator status."""
    if orchestrator:
        try:
            return ok(data={"status": "active", "orchestrator": str(orchestrator)})
        except Exception:
            pass
    return unavailable("orchestrator")


# ─── Contract-Mandated Chat Endpoints ─────────────────────────────────────

@router.post("/api/chat/message")
async def api_chat_message(data: dict = Body(...)):
    """Send a chat message."""
    try:
        message = data.get("message", "")
        session_id = data.get("session_id", "")
        if not message:
            return error("Message required")
        result = await _process_brain_message(message, "auto", "personal")
        return ok(data={"response": result.get("response", ""), "session_id": session_id, "source": result.get("source", "asim_nexus")})
    except Exception as e:
        logger.error(f"api_chat_message error: {e}")
        return error(str(e))


@router.get("/api/chat/messages/{session_id}")
async def api_chat_messages(session_id: str):
    """Get messages for a chat session."""
    try:
        if orchestrator and hasattr(orchestrator, "get_chat_messages"):
            data = await orchestrator.get_chat_messages(session_id)
            return ok(data=data)
        return ok(data={"session_id": session_id, "messages": [], "count": 0})
    except Exception as e:
        logger.error(f"api_chat_messages error: {e}")
        return error(str(e))


@router.post("/api/chat/session")
async def api_chat_session(data: dict = Body(...)):
    """Create a new chat session."""
    try:
        session_id = str(uuid.uuid4())
        return ok(data={"session_id": session_id, "status": "created", "user_id": data.get("user_id", "anonymous")})
    except Exception as e:
        logger.error(f"api_chat_session error: {e}")
        return error(str(e))


@router.get("/api/chat/session/{session_id}")
async def api_chat_session_get(session_id: str):
    """Get chat session details."""
    try:
        if orchestrator and hasattr(orchestrator, "get_session"):
            data = await orchestrator.get_session(session_id)
            return ok(data=data)
        return ok(data={"session_id": session_id, "status": "active"})
    except Exception as e:
        logger.error(f"api_chat_session_get error: {e}")
        return error(str(e))


@router.delete("/api/chat/session/{session_id}")
async def api_chat_session_delete(session_id: str):
    """Delete a chat session."""
    try:
        if orchestrator and hasattr(orchestrator, "delete_session"):
            await orchestrator.delete_session(session_id)
        return ok(data={"session_id": session_id, "status": "deleted"})
    except Exception as e:
        logger.error(f"api_chat_session_delete error: {e}")
        return error(str(e))


@router.get("/api/chat/sessions/{user_id}")
async def api_chat_sessions(user_id: str):
    """List chat sessions for a user."""
    try:
        if orchestrator and hasattr(orchestrator, "list_sessions"):
            data = await orchestrator.list_sessions(user_id)
            return ok(data=data)
        return ok(data={"user_id": user_id, "sessions": [], "count": 0})
    except Exception as e:
        logger.error(f"api_chat_sessions error: {e}")
        return error(str(e))


@router.get("/api/chat/stats")
async def api_chat_stats():
    """Get chat system statistics."""
    try:
        if orchestrator and hasattr(orchestrator, "get_chat_stats"):
            data = await orchestrator.get_chat_stats()
            return ok(data=data)
        return ok(data={"total_messages": 0, "active_sessions": 0})
    except Exception as e:
        logger.error(f"api_chat_stats error: {e}")
        return error(str(e))
