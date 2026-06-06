
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Tool Safety Validator
===============================
Validates and sanitizes all tool executions
Enforces permission levels and human-in-the-loop for high-risk operations
"""

import asyncio
import re
import json
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger("ASIM_TOOL_SAFETY")

class RiskLevel(Enum):
    """Tool execution risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PermissionLevel(Enum):
    """Agent permission levels"""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"

@dataclass
class ToolValidation:
    """Tool validation result"""
    tool_name: str
    is_valid: bool
    risk_level: RiskLevel
    required_permission: PermissionLevel
    requires_human_approval: bool
    sanitized_parameters: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
    validation_id: str

class ToolSafetyValidator:
    """
    Tool Safety Validator
    Validates all tool executions before they run
    """
    
    def __init__(self):
        self._initialized = False
        self._pending_approvals: Dict[str, Dict] = {}
        self._approval_timeout = 300  # 5 minutes
        
        # Tool risk definitions
        self._tool_risks = {
            # File operations
            "read_file": RiskLevel.LOW,
            "write_file": RiskLevel.MEDIUM,
            "delete_file": RiskLevel.HIGH,
            "create_file": RiskLevel.MEDIUM,
            "list_directory": RiskLevel.LOW,
            
            # System operations
            "execute_command": RiskLevel.CRITICAL,
            "run_script": RiskLevel.CRITICAL,
            "system_info": RiskLevel.MEDIUM,
            "process_kill": RiskLevel.HIGH,
            
            # Network operations
            "http_request": RiskLevel.MEDIUM,
            "api_call": RiskLevel.MEDIUM,
            "socket_connect": RiskLevel.HIGH,
            
            # Database operations
            "db_query": RiskLevel.MEDIUM,
            "db_write": RiskLevel.HIGH,
            "db_delete": RiskLevel.HIGH,
            
            # AI/ML operations
            "llm_call": RiskLevel.LOW,
            "model_train": RiskLevel.MEDIUM,
            "data_processing": RiskLevel.LOW
        }
        
        # Permission requirements
        self._permission_requirements = {
            RiskLevel.LOW: PermissionLevel.GUEST,
            RiskLevel.MEDIUM: PermissionLevel.USER,
            RiskLevel.HIGH: PermissionLevel.ADMIN,
            RiskLevel.CRITICAL: PermissionLevel.SYSTEM
        }
        
        # Human approval requirements
        self._human_approval_required = {
            RiskLevel.LOW: False,
            RiskLevel.MEDIUM: False,
            RiskLevel.HIGH: True,
            RiskLevel.CRITICAL: True
        }
    
    async def initialize(self) -> bool:
        """Initialize tool safety validator"""
        try:
            self._initialized = True
            logger.info("✅ Tool Safety Validator initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Tool Safety Validator initialization failed: {e}")
            return False
    
    async def validate_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_id: str,
        agent_permission: PermissionLevel
    ) -> ToolValidation:
        """
        Validate tool execution request
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            agent_id: Agent requesting execution
            agent_permission: Agent's permission level
        """
        if not self._initialized:
            await self.initialize()
        
        validation_id = str(uuid.uuid4())
        
        # Get tool risk level
        risk_level = self._tool_risks.get(tool_name, RiskLevel.MEDIUM)
        required_permission = self._permission_requirements[risk_level]
        requires_human_approval = self._human_approval_required[risk_level]
        
        warnings = []
        errors = []
        
        # NEW: Validate agent identity to prevent spoofing
        if not self._validate_agent_identity(agent_id, agent_permission):
            errors.append("Invalid agent identity or permission spoofing detected")
        
        # Check permission level
        if not self._has_permission(agent_permission, required_permission):
            errors.append(f"Insufficient permissions. Required: {required_permission.value}, Agent has: {agent_permission.value}")
        
        # Sanitize parameters
        sanitized_parameters = await self._sanitize_parameters(tool_name, parameters, risk_level)
        
        # Additional safety checks
        safety_warnings, safety_errors = await self._perform_safety_checks(tool_name, sanitized_parameters, risk_level)
        warnings.extend(safety_warnings)
        errors.extend(safety_errors)
        
        # Check if human approval is needed
        approval_id = None
        if requires_human_approval and errors:
            approval_id = await self._request_human_approval(validation_id, tool_name, parameters, agent_id, risk_level)
        
        is_valid = len(errors) == 0
        
        validation = ToolValidation(
            tool_name=tool_name,
            is_valid=is_valid,
            risk_level=risk_level,
            required_permission=required_permission,
            requires_human_approval=requires_human_approval,
            sanitized_parameters=sanitized_parameters,
            warnings=warnings,
            errors=errors,
            validation_id=validation_id
        )
        
        logger.info(f"🔍 Tool validation: {tool_name} - Risk: {risk_level.value} - Valid: {is_valid}")
        
        return validation
    
    def _validate_agent_identity(self, agent_id: str, claimed_permission: PermissionLevel) -> bool:
        """Validate agent identity and prevent spoofing"""
        # Check if agent ID format is valid
        if not agent_id or not isinstance(agent_id, str):
            return False
        
        # Check for suspicious agent IDs
        suspicious_patterns = ["fake_", "bypass_", "mock_", "test_", "sneaky_"]
        if any(pattern in agent_id.lower() for pattern in suspicious_patterns):
            return False
        
        # Additional validation for SYSTEM privilege claims
        if claimed_permission == PermissionLevel.SYSTEM:
            # Only specific agents can have SYSTEM privilege
            system_agents = ["ceo_clone", "system_agent", "master_agent"]
            if agent_id not in system_agents:
                return False
        
        return True
    
    def _has_permission(self, agent_permission: PermissionLevel, required_permission: PermissionLevel) -> bool:
        """Check if agent has required permission"""
        permission_hierarchy = {
            PermissionLevel.GUEST: 0,
            PermissionLevel.USER: 1,
            PermissionLevel.ADMIN: 2,
            PermissionLevel.SYSTEM: 3
        }
        
        return permission_hierarchy[agent_permission] >= permission_hierarchy[required_permission]
    
    async def _sanitize_parameters(self, tool_name: str, parameters: Dict[str, Any], risk_level: RiskLevel) -> Dict[str, Any]:
        """Sanitize tool parameters based on risk level"""
        sanitized = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Remove dangerous characters for high/critical risk
                if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    # Remove shell injection attempts
                    value = re.sub(r'[;&|`$(){}[\]]', '', value)
                    # Remove path traversal attempts
                    value = re.sub(r'\.\.[\\/]', '', value)
                    # Limit length
                    value = value[:1000]
                
                sanitized[key] = value
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                sanitized[key] = [str(item)[:500] for item in value[:10]]  # Limit list size
            elif isinstance(value, dict):
                sanitized[key] = {k: str(v)[:500] for k, v in list(value.items())[:10]}  # Limit dict size
            else:
                # Convert other types to string and limit
                sanitized[key] = str(value)[:500]
        
        return sanitized
    
    async def _perform_safety_checks(self, tool_name: str, parameters: Dict[str, Any], risk_level: RiskLevel) -> Tuple[List[str], List[str]]:
        """Perform additional safety checks"""
        warnings = []
        errors = []
        
        # File operation checks
        if tool_name in ["delete_file", "write_file", "create_file"]:
            file_path = parameters.get("file_path", "")
            if file_path:
                # Check for dangerous paths
                dangerous_paths = [
                    "/etc/", "/sys/", "/proc/", "/dev/",
                    "C:\\Windows\\", "C:\\Program Files\\",
                    "..", "~"
                ]
                
                for dangerous_path in dangerous_paths:
                    if dangerous_path in file_path:
                        errors.append(f"Dangerous file path detected: {file_path}")
                        break
                
                # Check file extensions for executable files
                executable_extensions = [".exe", ".bat", ".cmd", ".sh", ".py", ".js"]
                if any(file_path.lower().endswith(ext) for ext in executable_extensions):
                    warnings.append(f"Executable file detected: {file_path}")
        
        # Command execution checks
        if tool_name in ["execute_command", "run_script"]:
            command = parameters.get("command", "")
            if command:
                # Check for dangerous commands
                dangerous_commands = [
                    "rm -rf", "del /f", "format", "fdisk",
                    "shutdown", "reboot", "halt",
                    "sudo", "su", "passwd",
                    "curl", "wget", "nc", "netcat"
                ]
                
                for dangerous_cmd in dangerous_commands:
                    if dangerous_cmd in command.lower():
                        errors.append(f"Dangerous command detected: {command}")
                        break
        
        # Network operation checks
        if tool_name in ["http_request", "api_call", "socket_connect"]:
            url = parameters.get("url", "")
            host = parameters.get("host", "")
            
            # Check for internal network access
            internal_networks = ["127.0.0.1", "localhost", "192.168.", "10.", "172.16."]
            target = url or host
            
            for internal_net in internal_networks:
                if internal_net in target:
                    warnings.append(f"Internal network access: {target}")
                    break
        
        return warnings, errors
    
    async def _request_human_approval(self, validation_id: str, tool_name: str, parameters: Dict[str, Any], agent_id: str, risk_level: RiskLevel) -> str:
        """Request human approval for high-risk operations"""
        approval_id = str(uuid.uuid4())
        
        approval_request = {
            "approval_id": approval_id,
            "validation_id": validation_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "agent_id": agent_id,
            "risk_level": risk_level.value,
            "requested_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        self._pending_approvals[approval_id] = approval_request
        
        logger.warning(f"🚨 Human approval required for {tool_name} by {agent_id} (Approval ID: {approval_id})")
        
        # In a real system, this would send notification to user/admin
        # For now, we'll log it and require manual approval
        
        return approval_id
    
    async def approve_human_request(self, approval_id: str, approved_by: str) -> bool:
        """Approve a human approval request"""
        if approval_id not in self._pending_approvals:
            return False
        
        approval = self._pending_approvals[approval_id]
        approval["status"] = "approved"
        approval["approved_by"] = approved_by
        approval["approved_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ Human approval granted: {approval_id} by {approved_by}")
        
        return True
    
    async def deny_human_request(self, approval_id: str, denied_by: str, reason: str) -> bool:
        """Deny a human approval request"""
        if approval_id not in self._pending_approvals:
            return False
        
        approval = self._pending_approvals[approval_id]
        approval["status"] = "denied"
        approval["denied_by"] = denied_by
        approval["denied_at"] = datetime.now().isoformat()
        approval["reason"] = reason
        
        logger.warning(f"❌ Human approval denied: {approval_id} by {denied_by} - Reason: {reason}")
        
        return True
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending human approvals"""
        current_time = datetime.now()
        
        # Remove expired approvals
        expired_approvals = []
        for approval_id, approval in self._pending_approvals.items():
            if approval["status"] == "pending":
                requested_time = datetime.fromisoformat(approval["requested_at"])
                if (current_time - requested_time).total_seconds() > self._approval_timeout:
                    approval["status"] = "expired"
                    expired_approvals.append(approval_id)
        
        for approval_id in expired_approvals:
            del self._pending_approvals[approval_id]
        
        return [approval for approval in self._pending_approvals.values() if approval["status"] == "pending"]
    
    async def check_approval_status(self, approval_id: str) -> Optional[Dict]:
        """Check status of human approval request"""
        if approval_id not in self._pending_approvals:
            return None
        
        approval = self._pending_approvals[approval_id]
        
        # Check if expired
        if approval["status"] == "pending":
            current_time = datetime.now()
            requested_time = datetime.fromisoformat(approval["requested_at"])
            if (current_time - requested_time).total_seconds() > self._approval_timeout:
                approval["status"] = "expired"
        
        return approval

# Global instance
_tool_safety_validator = None

def get_tool_safety_validator() -> ToolSafetyValidator:
    """Get global tool safety validator instance"""
    global _tool_safety_validator
    if _tool_safety_validator is None:
        _tool_safety_validator = ToolSafetyValidator()
    return _tool_safety_validator

# Decorator for automatic tool validation
def with_tool_validation(tool_name: str, agent_permission: PermissionLevel = PermissionLevel.USER):
    """Decorator to automatically validate tool execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            validator = get_tool_safety_validator()
            
            # Extract parameters from kwargs
            parameters = {k: v for k, v in kwargs.items() if k != 'agent_id'}
            agent_id = kwargs.get('agent_id', 'unknown_agent')
            
            # Validate tool execution
            validation = await validator.validate_tool_execution(
                tool_name=tool_name,
                parameters=parameters,
                agent_id=agent_id,
                agent_permission=agent_permission
            )
            
            if not validation.is_valid:
                if validation.errors:
                    raise Exception(f"Tool validation failed: {', '.join(validation.errors)}")
                elif validation.requires_human_approval:
                    raise Exception(f"Human approval required. Approval ID: {validation.validation_id}")
            
            # Execute with sanitized parameters
            sanitized_kwargs = kwargs.copy()
            sanitized_kwargs.update(validation.sanitized_parameters)
            
            return await func(*args, **sanitized_kwargs)
        
        return wrapper
    return decorator
