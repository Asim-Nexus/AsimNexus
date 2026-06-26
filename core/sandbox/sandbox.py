#!/usr/bin/env python3
"""
STATUS: NEW — Sandbox Executor
AsimNexus Sandbox System
========================
Docker/containerd मार्फत OS tools सुरक्षित चलाउने।
"""

import asyncio
import time
import uuid
import docker
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("AsimNexus.Sandbox")


@dataclass
class SandboxResult:
    success: bool
    output: Any = None
    error: str = ""
    execution_id: str = ""
    duration_ms: float = 0.0
    container_id: str = ""


class ToolSandbox:
    """
    OS Tools (file, process, system) सुरक्षित चलाउने।
    Docker container मा सञ्चालन गर्ने।
    """
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            self.base_image = "python:3.11-slim"
            logger.info("✅ Docker client initialized")
        except Exception as e:
            self.docker_client = None
            logger.warning(f"Docker not available: {e}")
            
    async def execute_in_sandbox(
        self, 
        tool_id: str, 
        parameters: Dict[str, Any],
        timeout_sec: int = 30
    ) -> SandboxResult:
        """
        Tool लाई sandbox मा चलाउने।
        """
        if not self.docker_client:
            return SandboxResult(
                success=False,
                error="Docker not available",
                execution_id=str(uuid.uuid4())
            )
            
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Create container with limited resources
            container = self.docker_client.containers.run(
                self.base_image,
                command=f"python -c 'print({parameters})'",
                detach=True,
                mem_limit="128m",
                cpu_quota=50000,  # 50% CPU
                network_disabled=True,  # No network access
                remove=False
            )
            
            # Wait for result
            try:
                result = container.wait(timeout=timeout_sec)
                output = container.logs().decode('utf-8')
            except Exception:
                container.kill()
                return SandboxResult(
                    success=False,
                    error="Timeout exceeded",
                    execution_id=execution_id,
                    duration_ms=(time.time() - start_time) * 1000,
                    container_id=container.id
                )
                
            duration = (time.time() - start_time) * 1000
            
            # Cleanup
            try:
                container.remove()
            except Exception:
                pass
                
            return SandboxResult(
                success=True,
                output=output,
                execution_id=execution_id,
                duration_ms=duration,
                container_id=container.id
            )
            
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return SandboxResult(
                success=False,
                error=str(e),
                execution_id=execution_id
            )


class ToolGuard:
    """
    Tool Execution को लागि सुरक्षा ढाँचा।
    Dharma Veto को साथ जोडिने।
    """
    
    HIGH_RISK_PATTERNS = [
        "delete", "remove", "format", "kill", "shutdown",
        "drop database", "rm -rf", "dangerous"
    ]
    
    def __init__(self):
        self.sandbox = ToolSandbox()
        
    async def check_and_execute(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        user_id: str = "default",
        context: Dict[str, Any] = None
    ) -> SandboxResult:
        """
        सुरक्षा जाँच गरेर Tool चलाउने।
        """
        context = context or {}
        
        # १. Dharma Veto जाँच
        veto_result = await self._check_veto(tool_id, parameters, context)
        if not veto_result[0]:
            return SandboxResult(
                success=False,
                error=f"Dharma Veto: {veto_result[1]}"
            )
            
        # २. High-risk जाँच
        if self._is_high_risk(tool_id, parameters):
            # Human approval चाहिन्छ
            if not context.get("human_approval", False):
                return SandboxResult(
                    success=False,
                    error="High-risk action - human approval required"
                )
                
        # ३. Sandbox मा चलाउने
        return await self.sandbox.execute_in_sandbox(tool_id, parameters)
        
    async def _check_veto(
        self, 
        tool_id: str, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Dharma Veto को साथ जाँच।
        """
        try:
            from core.dharma_chakra.veto_engine import get_veto_engine, VetoLevel
            engine = get_veto_engine()
            
            message = f"{tool_id}: {parameters}"
            result = engine.check(message, sector="general")
            
            if result.level == VetoLevel.BLOCK:
                return False, result.reason
            elif result.level == VetoLevel.REQUIRE_HUMAN:
                return True, "Human approval required"
                
            return True, "Allowed"
            
        except ImportError:
            return True, "Veto engine not available - proceeding"
            
    def _is_high_risk(self, tool_id: str, parameters: Dict[str, Any]) -> bool:
        """
        उच्च जोखिमको Tool भन्ने।
        """
        # Tool ID मा high-risk keywords
        for pattern in self.HIGH_RISK_PATTERNS:
            if pattern in tool_id.lower():
                return True
                
        # Parameters मा पनि जाँच
        param_str = str(parameters).lower()
        for pattern in self.HIGH_RISK_PATTERNS:
            if pattern in param_str:
                return True
                
        return False


# Global sandbox instance
sandbox = ToolSandbox()
tool_guard = ToolGuard()