
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""Risk validation layer for tool execution safety."""
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


class RiskLevel(Enum):
    """Risk levels for operations."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    tool_name: str
    risk_level: RiskLevel
    requires_confirmation: bool
    requires_sandbox: bool
    warnings: List[str]
    blocked: bool
    reason: Optional[str] = None


class RiskValidator:
    """
    Validates tool execution requests for safety.
    
    Checks:
    - Dangerous command patterns
    - Sensitive file access
    - System-modifying operations
    - Network exfiltration risks
    """
    
    # Dangerous patterns by risk level
    CRITICAL_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+~",
        r"rm\s+-rf\s+\.",
        r"dd\s+if=.*of=/dev/",
        r">\s*/dev/",
        r"mkfs\.",
        r"format\s+[c-z]:",
        r"del\s+/[fq]\s+",
        r"rmdir\s+/s\s+/q",
    ]
    
    HIGH_PATTERNS = [
        r"sudo\s+",
        r"su\s+-",
        r"passwd",
        r"useradd",
        r"usermod",
        r"chmod\s+777",
        r"chown\s+-R",
        r"rm\s+-rf",
        r"del\s+/f",
    ]
    
    MEDIUM_PATTERNS = [
        r"curl\s+.*\|\s*bash",
        r"wget\s+.*\|\s*sh",
        r"eval\s*\(",
        r"exec\s*\(",
        r"system\s*\(",
        r"__import__\s*\(",
        r"subprocess\.call",
        r"os\.system",
        r"os\.popen",
        r"\$\(.*\)",
        r"`.*`",
    ]
    
    # Sensitive paths
    SENSITIVE_PATHS = [
        r"/etc/passwd",
        r"/etc/shadow",
        r"/etc/hosts",
        r"/proc/",
        r"/sys/",
        r"C:\\Windows\\System32",
        r"~/.ssh",
        r"~/.aws",
        r".env",
        r"config\.json",
        r"secrets",
        r"password",
        r"api[_-]?key",
        r"private[_-]?key",
    ]
    
    # Tool-specific risk levels
    TOOL_RISKS: Dict[str, RiskLevel] = {
        "file_read": RiskLevel.LOW,
        "file_write": RiskLevel.MEDIUM,
        "file_delete": RiskLevel.HIGH,
        "directory_list": RiskLevel.LOW,
        "execute_command": RiskLevel.CRITICAL,
        "system_scan": RiskLevel.LOW,
        "process_list": RiskLevel.LOW,
        "http_request": RiskLevel.MEDIUM,
        "api_connect": RiskLevel.MEDIUM,
        "agent_spawn": RiskLevel.MEDIUM,
        "agent_message": RiskLevel.LOW,
        "code_search": RiskLevel.LOW,
        "code_analyze": RiskLevel.LOW,
        "browser_automation": RiskLevel.HIGH,
        "db_query": RiskLevel.HIGH,
        "email_send": RiskLevel.MEDIUM,
    }
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._compiled_critical = [re.compile(p, re.IGNORECASE) for p in self.CRITICAL_PATTERNS]
        self._compiled_high = [re.compile(p, re.IGNORECASE) for p in self.HIGH_PATTERNS]
        self._compiled_medium = [re.compile(p, re.IGNORECASE) for p in self.MEDIUM_PATTERNS]
    
    def validate_tool_execution(self, tool_name: str, 
                               parameters: Dict,
                               user_role: str = "user") -> RiskAssessment:
        """
        Validate tool execution request.
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            user_role: User role for permission check
        
        Returns:
            RiskAssessment with safety determination
        """
        warnings = []
        blocked = False
        reason = None
        
        # Get base risk level
        base_risk = self.TOOL_RISKS.get(tool_name, RiskLevel.MEDIUM)
        
        # Check command parameter for dangerous patterns
        command = parameters.get("command", "")
        if command:
            risk, pattern_warnings = self._analyze_command(command)
            warnings.extend(pattern_warnings)
            base_risk = max(base_risk, risk, key=lambda x: list(RiskLevel).index(x))
        
        # Check path parameter for sensitive files
        path = parameters.get("path", "")
        if path:
            if self._is_sensitive_path(path):
                warnings.append(f"Access to sensitive path: {path}")
                base_risk = RiskLevel.HIGH
        
        # Check URL parameter
        url = parameters.get("url", "")
        if url:
            if self._is_suspicious_url(url):
                warnings.append(f"Suspicious URL detected: {url}")
                base_risk = RiskLevel.HIGH
        
        # Check content for dangerous patterns
        content = parameters.get("content", "")
        if content:
            risk, content_warnings = self._analyze_content(content)
            warnings.extend(content_warnings)
            base_risk = max(base_risk, risk, key=lambda x: list(RiskLevel).index(x))
        
        # Determine blocking
        if base_risk == RiskLevel.CRITICAL:
            if self.strict_mode:
                blocked = True
                reason = "Critical risk operation blocked"
            else:
                warnings.append("CRITICAL: Operation requires admin approval")
        
        # Role-based overrides
        if user_role == "admin":
            blocked = False  # Admins can override
        elif user_role == "guest" and base_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            blocked = True
            reason = "Guests cannot execute high-risk operations"
        
        return RiskAssessment(
            tool_name=tool_name,
            risk_level=base_risk,
            requires_confirmation=base_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            requires_sandbox=base_risk in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
            warnings=warnings,
            blocked=blocked,
            reason=reason
        )
    
    def _analyze_command(self, command: str) -> Tuple[RiskLevel, List[str]]:
        """Analyze command for dangerous patterns."""
        warnings = []
        
        # Check critical patterns
        for pattern in self._compiled_critical:
            if pattern.search(command):
                warnings.append(f"CRITICAL pattern detected: {command[:50]}")
                return RiskLevel.CRITICAL, warnings
        
        # Check high patterns
        for pattern in self._compiled_high:
            if pattern.search(command):
                warnings.append(f"HIGH risk pattern detected: {command[:50]}")
                return RiskLevel.HIGH, warnings
        
        # Check medium patterns
        for pattern in self._compiled_medium:
            if pattern.search(command):
                warnings.append(f"MEDIUM risk pattern detected: {command[:50]}")
                return RiskLevel.MEDIUM, warnings
        
        return RiskLevel.LOW, warnings
    
    def _analyze_content(self, content: str) -> Tuple[RiskLevel, List[str]]:
        """Analyze content for dangerous patterns."""
        warnings = []
        
        # Check for executable code
        dangerous_code = [
            r"os\.system",
            r"subprocess\.call",
            r"subprocess\.run",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"import\s+os",
            r"import\s+subprocess",
        ]
        
        for pattern in dangerous_code:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"Potentially dangerous code pattern: {pattern}")
                return RiskLevel.HIGH, warnings
        
        return RiskLevel.LOW, warnings
    
    def _is_sensitive_path(self, path: str) -> bool:
        """Check if path is sensitive."""
        path_lower = path.lower()
        for sensitive in self.SENSITIVE_PATHS:
            if re.search(sensitive.replace(".", r"\.").replace("~", r".*"), path_lower):
                return True
        return False
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is suspicious."""
        suspicious_patterns = [
            r"localhost",
            r"127\.0\.0\.1",
            r"0\.0\.0\.0",
            r"192\.168\.",
            r"10\.",
            r"file://",
            r"ftp://",
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower):
                return True
        return False
    
    def get_tool_safety_info(self, tool_name: str) -> Dict:
        """Get safety information for a tool."""
        risk = self.TOOL_RISKS.get(tool_name, RiskLevel.MEDIUM)
        
        return {
            "tool": tool_name,
            "risk_level": risk.value,
            "requires_confirmation": risk in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            "requires_sandbox": risk in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
            "description": self._get_risk_description(risk)
        }
    
    def _get_risk_description(self, risk: RiskLevel) -> str:
        """Get human-readable risk description."""
        descriptions = {
            RiskLevel.SAFE: "Read-only operations, no system impact",
            RiskLevel.LOW: "Low risk, minimal system impact",
            RiskLevel.MEDIUM: "Moderate risk, requires sandbox",
            RiskLevel.HIGH: "High risk, requires explicit confirmation",
            RiskLevel.CRITICAL: "Critical risk, admin approval required"
        }
        return descriptions.get(risk, "Unknown risk level")


# Global instance
_validator_instance = None

def get_risk_validator() -> RiskValidator:
    """Get global risk validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = RiskValidator()
    return _validator_instance
