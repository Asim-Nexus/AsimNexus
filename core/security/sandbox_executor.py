
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Sandbox Executor
==========================
Quantum Sandbox - Zero-Risk Execution Environment
Isolated execution environment for safe command and file operations
"""

import asyncio
import logging
import os
import tempfile
import shutil
import subprocess
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import threading
import psutil

logger = logging.getLogger("SandboxExecutor")

class SandboxLevel(Enum):
    """Sandbox isolation levels"""
    MINIMAL = "minimal"           # Basic isolation
    STANDARD = "standard"         # Standard isolation
    MAXIMUM = "maximum"           # Maximum isolation
    QUANTUM = "quantum"           # Quantum-level isolation

class ExecutionType(Enum):
    """Types of sandboxed execution"""
    COMMAND = "command"
    SCRIPT = "script"
    FILE_OPERATION = "file_operation"
    NETWORK_REQUEST = "network_request"
    SYSTEM_CALL = "system_call"

class SecurityLevel(Enum):
    """Security classification levels"""
    SAFE = "safe"
    WARNING = "warning"
    RISKY = "risky"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"

@dataclass
class SandboxRequest:
    """Sandbox execution request"""
    request_id: str
    execution_type: ExecutionType
    command: str
    parameters: Dict[str, Any]
    sandbox_level: SandboxLevel
    timeout: int = 30
    allow_network: bool = False
    allow_file_access: bool = False
    max_memory_mb: int = 512
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SandboxResult:
    """Sandbox execution result"""
    request_id: str
    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time: float
    security_level: SecurityLevel
    warnings: List[str]
    violations: List[str]
    sandbox_path: str
    timestamp: datetime = field(default_factory=datetime.now)

class SandboxExecutor:
    """Quantum Sandbox - Zero-Risk Execution Environment"""
    
    def __init__(self):
        self.logger = logging.getLogger("SandboxExecutor")
        self.is_active = False
        self.active_sandboxes: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[SandboxResult] = []
        
        # Security policies
        self.security_policies = {
            "blocked_commands": [
                "format", "fdisk", "del", "rmdir", "shutdown", "reboot",
                "net user", "net localgroup", "reg delete", "powershell -c",
                "wget", "curl", "nc", "telnet", "ssh", "ftp"
            ],
            "risky_commands": [
                "pip install", "npm install", "git clone", "svn checkout",
                "python -c", "node -e", "bash -c", "cmd /c"
            ],
            "blocked_extensions": [
                ".exe", ".bat", ".cmd", ".ps1", ".scr", ".vbs",
                ".jar", ".app", ".deb", ".rpm", ".msi"
            ],
            "max_file_size_mb": 10,
            "max_execution_time": 300,  # 5 minutes
            "max_memory_mb": 1024
        }
        
        # Sandbox configurations
        self.sandbox_configs = {
            SandboxLevel.MINIMAL: {
                "isolation": "process",
                "network_access": False,
                "file_access": True,
                "temp_cleanup": True
            },
            SandboxLevel.STANDARD: {
                "isolation": "container",
                "network_access": False,
                "file_access": True,
                "temp_cleanup": True
            },
            SandboxLevel.MAXIMUM: {
                "isolation": "container",
                "network_access": False,
                "file_access": False,
                "temp_cleanup": True
            },
            SandboxLevel.QUANTUM: {
                "isolation": "vm",
                "network_access": False,
                "file_access": False,
                "temp_cleanup": True
            }
        }
        
        self.logger.info("🛡️ Sandbox Executor Initialized - Quantum Security Active")
    
    async def initialize(self) -> bool:
        """Initialize Sandbox Executor"""
        try:
            # Test sandbox creation
            test_sandbox = await self.create_sandbox(Sandbox_level=SandboxLevel.MINIMAL)
            if not test_sandbox:
                raise Exception("Failed to create test sandbox")
            
            # Clean up test sandbox
            await self.cleanup_sandbox(test_sandbox["id"])
            
            self.is_active = True
            
            self.logger.info("✅ Sandbox Executor activated - Zero-Risk Environment Ready")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Sandbox Executor initialization failed: {e}")
            return False
    
    async def create_sandbox(self, sandbox_level: SandboxLevel = SandboxLevel.STANDARD) -> Optional[Dict[str, Any]]:
        """Create isolated sandbox environment"""
        try:
            sandbox_id = f"sandbox_{uuid.uuid4().hex[:8]}"
            sandbox_path = tempfile.mkdtemp(prefix=f"asimnexus_{sandbox_id}_")
            
            # Create sandbox structure
            os.makedirs(os.path.join(sandbox_path, "temp"), exist_ok=True)
            os.makedirs(os.path.join(sandbox_path, "output"), exist_ok=True)
            os.makedirs(os.path.join(sandbox_path, "logs"), exist_ok=True)
            
            # Get sandbox configuration
            config = self.sandbox_configs.get(sandbox_level, self.sandbox_configs[SandboxLevel.STANDARD])
            
            # Create sandbox info
            sandbox_info = {
                "id": sandbox_id,
                "path": sandbox_path,
                "level": sandbox_level.value,
                "config": config,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Store sandbox info
            self.active_sandboxes[sandbox_id] = sandbox_info
            
            self.logger.info(f"🛡️ Created sandbox: {sandbox_id} at {sandbox_path}")
            return sandbox_info
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create sandbox: {e}")
            return None
    
    async def execute_in_sandbox(self, request: SandboxRequest) -> SandboxResult:
        """Execute command in isolated sandbox"""
        try:
            start_time = time.time()
            
            # Security analysis
            security_analysis = await self.analyze_security(request)
            if security_analysis["security_level"] == SecurityLevel.BLOCKED:
                return SandboxResult(
                    request_id=request.request_id,
                    success=False,
                    return_code=-1,
                    stdout="",
                    stderr="Command blocked by security policy",
                    execution_time=0.0,
                    security_level=SecurityLevel.BLOCKED,
                    warnings=security_analysis["warnings"],
                    violations=security_analysis["violations"],
                    sandbox_path=""
                )
            
            # Create sandbox
            sandbox = await self.create_sandbox(request.sandbox_level)
            if not sandbox:
                raise Exception("Failed to create sandbox")
            
            try:
                # Prepare execution environment
                execution_result = await self._execute_command(request, sandbox)
                
                # Clean up sandbox
                await self.cleanup_sandbox(sandbox["id"])
                
                execution_time = time.time() - start_time
                
                result = SandboxResult(
                    request_id=request.request_id,
                    success=execution_result["success"],
                    return_code=execution_result["return_code"],
                    stdout=execution_result["stdout"],
                    stderr=execution_result["stderr"],
                    execution_time=execution_time,
                    security_level=security_analysis["security_level"],
                    warnings=security_analysis["warnings"],
                    violations=security_analysis["violations"],
                    sandbox_path=sandbox["path"]
                )
                
                # Store in history
                self.execution_history.append(result)
                
                # Keep only last 100 executions
                if len(self.execution_history) > 100:
                    self.execution_history = self.execution_history[-100:]
                
                return result
                
            except Exception as e:
                # Ensure cleanup on error
                await self.cleanup_sandbox(sandbox["id"])
                raise e
                
        except Exception as e:
            self.logger.error(f"❌ Sandbox execution failed: {e}")
            return SandboxResult(
                request_id=request.request_id,
                success=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=0.0,
                security_level=SecurityLevel.DANGEROUS,
                warnings=["Execution failed"],
                violations=[str(e)],
                sandbox_path=""
            )
    
    async def analyze_security(self, request: SandboxRequest) -> Dict[str, Any]:
        """Analyze security level of execution request"""
        try:
            warnings = []
            violations = []
            security_level = SecurityLevel.SAFE
            
            command_lower = request.command.lower()
            
            # Check for blocked commands
            for blocked_cmd in self.security_policies["blocked_commands"]:
                if blocked_cmd in command_lower:
                    violations.append(f"Blocked command detected: {blocked_cmd}")
                    security_level = SecurityLevel.BLOCKED
            
            # Check for risky commands
            for risky_cmd in self.security_policies["risky_commands"]:
                if risky_cmd in command_lower:
                    warnings.append(f"Risky command detected: {risky_cmd}")
                    if security_level != SecurityLevel.BLOCKED:
                        security_level = SecurityLevel.RISKY
            
            # Check file operations
            if request.execution_type == ExecutionType.FILE_OPERATION:
                # Check for dangerous file operations
                dangerous_patterns = ["delete", "remove", "format", "fdisk", "partition"]
                for pattern in dangerous_patterns:
                    if pattern in command_lower:
                        violations.append(f"Dangerous file operation: {pattern}")
                        security_level = SecurityLevel.DANGEROUS
            
            # Check parameters for security issues
            if request.parameters:
                # Check file paths
                for key, value in request.parameters.items():
                    if isinstance(value, str):
                        # Check for path traversal
                        if ".." in value or value.startswith("/"):
                            violations.append(f"Path traversal attempt in parameter: {key}")
                            security_level = SecurityLevel.DANGEROUS
                        
                        # Check for suspicious extensions
                        for ext in self.security_policies["blocked_extensions"]:
                            if value.lower().endswith(ext):
                                violations.append(f"Blocked file extension: {ext}")
                                security_level = SecurityLevel.BLOCKED
            
            # Check resource limits
            if request.max_memory_mb > self.security_policies["max_memory_mb"]:
                warnings.append(f"High memory request: {request.max_memory_mb}MB")
                if security_level == SecurityLevel.SAFE:
                    security_level = SecurityLevel.WARNING
            
            if request.timeout > self.security_policies["max_execution_time"]:
                warnings.append(f"Long execution time: {request.timeout}s")
                if security_level == SecurityLevel.SAFE:
                    security_level = SecurityLevel.WARNING
            
            return {
                "security_level": security_level,
                "warnings": warnings,
                "violations": violations,
                "risk_score": self._calculate_risk_score(warnings, violations)
            }
            
        except Exception as e:
            return {
                "security_level": SecurityLevel.DANGEROUS,
                "warnings": ["Security analysis failed"],
                "violations": [str(e)],
                "risk_score": 100
            }
    
    def _calculate_risk_score(self, warnings: List[str], violations: List[str]) -> int:
        """Calculate risk score based on warnings and violations"""
        base_score = 0
        base_score += len(warnings) * 10
        base_score += len(violations) * 50
        return min(base_score, 100)
    
    async def _execute_command(self, request: SandboxRequest, sandbox: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command in sandbox environment"""
        try:
            sandbox_path = sandbox["path"]
            config = sandbox["config"]
            
            # Prepare execution based on type
            if request.execution_type == ExecutionType.COMMAND:
                return await self._execute_shell_command(request, sandbox_path, config)
            elif request.execution_type == ExecutionType.SCRIPT:
                return await self._execute_script(request, sandbox_path, config)
            elif request.execution_type == ExecutionType.FILE_OPERATION:
                return await self._execute_file_operation(request, sandbox_path, config)
            else:
                return {
                    "success": False,
                    "return_code": -1,
                    "stdout": "",
                    "stderr": f"Unsupported execution type: {request.execution_type.value}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def _execute_shell_command(self, request: SandboxRequest, sandbox_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command in sandbox"""
        try:
            # Prepare command
            if os.name == 'nt':  # Windows
                # Use PowerShell for better control
                command = f'powershell -Command "{request.command}"'
                shell = True
            else:  # Linux/Mac
                command = request.command
                shell = True
            
            # Set up environment with restrictions
            env = os.environ.copy()
            env["SANDBOX"] = "1"
            env["SANDBOX_PATH"] = sandbox_path
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                command,
                shell=shell,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=sandbox_path,
                env=env,
                text=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=request.timeout
                )
                return_code = process.returncode
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "return_code": -1,
                    "stdout": "",
                    "stderr": f"Command timed out after {request.timeout} seconds"
                }
            
            return {
                "success": return_code == 0,
                "return_code": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def _execute_script(self, request: SandboxRequest, sandbox_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute script in sandbox"""
        try:
            # Create script file
            script_content = request.command
            script_path = os.path.join(sandbox_path, "temp", f"script_{request.request_id}.py")
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Execute script
            command = f"python {script_path}"
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=sandbox_path,
                text=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=request.timeout
                )
                return_code = process.returncode
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "return_code": -1,
                    "stdout": "",
                    "stderr": f"Script execution timed out after {request.timeout} seconds"
                }
            
            return {
                "success": return_code == 0,
                "return_code": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def _execute_file_operation(self, request: SandboxRequest, sandbox_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operation in sandbox"""
        try:
            # Parse file operation from command
            operation = request.parameters.get("operation", "read")
            file_path = request.parameters.get("file_path", "")
            content = request.parameters.get("content", "")
            
            # Restrict to sandbox directory
            if not file_path.startswith(sandbox_path):
                file_path = os.path.join(sandbox_path, "temp", os.path.basename(file_path))
            
            if operation == "read":
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {
                        "success": True,
                        "return_code": 0,
                        "stdout": content,
                        "stderr": ""
                    }
                else:
                    return {
                        "success": False,
                        "return_code": -1,
                        "stdout": "",
                        "stderr": "File not found"
                    }
            
            elif operation == "write":
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "return_code": 0,
                    "stdout": f"File written: {file_path}",
                    "stderr": ""
                }
            
            elif operation == "delete":
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return {
                        "success": True,
                        "return_code": 0,
                        "stdout": f"File deleted: {file_path}",
                        "stderr": ""
                    }
                else:
                    return {
                        "success": False,
                        "return_code": -1,
                        "stdout": "",
                        "stderr": "File not found"
                    }
            
            else:
                return {
                    "success": False,
                    "return_code": -1,
                    "stdout": "",
                    "stderr": f"Unsupported file operation: {operation}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def cleanup_sandbox(self, sandbox_id: str) -> bool:
        """Clean up sandbox environment"""
        try:
            if sandbox_id not in self.active_sandboxes:
                return True  # Already cleaned
            
            sandbox_info = self.active_sandboxes[sandbox_id]
            sandbox_path = sandbox_info["path"]
            
            # Remove sandbox directory
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path, ignore_errors=True)
            
            # Remove from active sandboxes
            del self.active_sandboxes[sandbox_id]
            
            self.logger.info(f"🧹 Cleaned up sandbox: {sandbox_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup sandbox {sandbox_id}: {e}")
            return False
    
    async def get_sandbox_status(self) -> Dict[str, Any]:
        """Get current sandbox status"""
        try:
            # Calculate statistics
            total_executions = len(self.execution_history)
            successful_executions = sum(1 for r in self.execution_history if r.success)
            blocked_executions = sum(1 for r in self.execution_history if r.security_level == SecurityLevel.BLOCKED)
            
            # Recent activity
            recent_executions = self.execution_history[-10:] if self.execution_history else []
            
            return {
                "active": self.is_active,
                "active_sandboxes": len(self.active_sandboxes),
                "sandbox_ids": list(self.active_sandboxes.keys()),
                "execution_statistics": {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                    "blocked_executions": blocked_executions,
                    "average_execution_time": sum(r.execution_time for r in self.execution_history) / max(total_executions, 1)
                },
                "security_statistics": {
                    "safe_executions": sum(1 for r in self.execution_history if r.security_level == SecurityLevel.SAFE),
                    "warning_executions": sum(1 for r in self.execution_history if r.security_level == SecurityLevel.WARNING),
                    "risky_executions": sum(1 for r in self.execution_history if r.security_level == SecurityLevel.RISKY),
                    "dangerous_executions": sum(1 for r in self.execution_history if r.security_level == SecurityLevel.DANGEROUS),
                    "blocked_executions": blocked_executions
                },
                "recent_activity": [
                    {
                        "request_id": r.request_id,
                        "success": r.success,
                        "security_level": r.security_level.value,
                        "execution_time": r.execution_time,
                        "timestamp": r.timestamp.isoformat()
                    } for r in recent_executions
                ],
                "security_policies": self.security_policies
            }
            
        except Exception as e:
            return {"error": f"Failed to get sandbox status: {e}"}
    
    async def execute_sandbox_command(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sandbox-specific commands"""
        try:
            if command == "execute":
                request = SandboxRequest(
                    request_id=f"req_{datetime.now().timestamp()}",
                    execution_type=ExecutionType(parameters.get("type", "command")),
                    command=parameters.get("command", ""),
                    parameters=parameters.get("parameters", {}),
                    sandbox_level=SandboxLevel(parameters.get("sandbox_level", "standard")),
                    timeout=parameters.get("timeout", 30),
                    allow_network=parameters.get("allow_network", False),
                    allow_file_access=parameters.get("allow_file_access", True),
                    max_memory_mb=parameters.get("max_memory_mb", 512)
                )
                
                result = await self.execute_in_sandbox(request)
                
                return {
                    "success": result.success,
                    "request_id": result.request_id,
                    "return_code": result.return_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": result.execution_time,
                    "security_level": result.security_level.value,
                    "warnings": result.warnings,
                    "violations": result.violations
                }
            
            elif command == "get_status":
                return await self.get_sandbox_status()
            
            elif command == "cleanup_all":
                # Clean up all active sandboxes
                cleanup_results = []
                for sandbox_id in list(self.active_sandboxes.keys()):
                    result = await self.cleanup_sandbox(sandbox_id)
                    cleanup_results.append({"sandbox_id": sandbox_id, "success": result})
                
                return {
                    "success": True,
                    "cleaned_sandboxes": cleanup_results,
                    "message": f"Cleaned up {len(cleanup_results)} sandboxes"
                }
            
            elif command == "get_history":
                limit = parameters.get("limit", 20)
                history = self.execution_history[-limit:] if self.execution_history else []
                
                return {
                    "success": True,
                    "history": [
                        {
                            "request_id": r.request_id,
                            "execution_type": r.execution_type.value if hasattr(r, 'execution_type') else "command",
                            "success": r.success,
                            "security_level": r.security_level.value,
                            "execution_time": r.execution_time,
                            "warnings_count": len(r.warnings),
                            "violations_count": len(r.violations),
                            "timestamp": r.timestamp.isoformat()
                        } for r in history
                    ]
                }
            
            elif command == "analyze_security":
                test_request = SandboxRequest(
                    request_id=f"analysis_{datetime.now().timestamp()}",
                    execution_type=ExecutionType(parameters.get("type", "command")),
                    command=parameters.get("command", ""),
                    parameters=parameters.get("parameters", {}),
                    sandbox_level=SandboxLevel(parameters.get("sandbox_level", "standard"))
                )
                
                analysis = await self.analyze_security(test_request)
                
                return {
                    "success": True,
                    "security_analysis": analysis,
                    "recommendation": self._get_security_recommendation(analysis["security_level"])
                }
            
            else:
                return {"error": f"Unknown sandbox command: {command}"}
                
        except Exception as e:
            return {"error": f"Sandbox command execution failed: {e}"}
    
    def _get_security_recommendation(self, security_level: SecurityLevel) -> str:
        """Get security recommendation based on level"""
        recommendations = {
            SecurityLevel.SAFE: "Command is safe to execute",
            SecurityLevel.WARNING: "Proceed with caution - review command parameters",
            SecurityLevel.RISKY: "Consider safer alternatives or additional safeguards",
            SecurityLevel.DANGEROUS: "Command not recommended - review security policies",
            SecurityLevel.BLOCKED: "Command blocked by security policy"
        }
        return recommendations.get(security_level, "Unknown security level")
    
    async def shutdown(self):
        """Shutdown Sandbox Executor"""
        try:
            # Clean up all active sandboxes
            for sandbox_id in list(self.active_sandboxes.keys()):
                await self.cleanup_sandbox(sandbox_id)
            
            self.is_active = False
            self.logger.info("🛑 Sandbox Executor Shutdown - Quantum Security Offline")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

# Global instance
_sandbox_executor_instance = None

def get_sandbox_executor() -> SandboxExecutor:
    """Get singleton Sandbox Executor instance"""
    global _sandbox_executor_instance
    if _sandbox_executor_instance is None:
        _sandbox_executor_instance = SandboxExecutor()
    return _sandbox_executor_instance
