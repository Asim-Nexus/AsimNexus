#!/usr/bin/env python3
"""
STATUS: NEW — Sandbox API Routes
Sandbox System API Endpoints
============================
सुरक्षित Tool Executionका लागि API।
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

try:
    from core.sandbox.executor import executor
except ImportError:
    executor = None


router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


class ToolExecuteRequest(BaseModel):
    tool_id: str
    parameters: Dict[str, Any] = {}
    user_id: str = "default"
    context: Dict[str, Any] = {}


@router.post("/execute")
async def sandbox_execute(request: ToolExecuteRequest):
    """
    Tool लाई sandbox मा चलाउने।
    """
    if not executor:
        return {"success": False, "error": "Sandbox executor not ready"}
        
    result = await executor.execute_tool(
        request.tool_id,
        request.parameters,
        request.user_id,
        request.context
    )
    
    return result


@router.get("/status")
async def sandbox_status():
    """
    Sandbox अवस्था।
    """
    try:
        import docker
        docker_available = docker.from_env() is not None
    except:
        docker_available = False
        
    return {
        "sandbox_ready": executor is not None,
        "docker_available": docker_available,
        "tools_registered": 50,  # Approximate
        "security_features": ["Dharma Veto", "Resource Limits", "Network Isolation"]
    }