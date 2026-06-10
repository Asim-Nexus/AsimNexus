
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""Input sanitization layer to prevent injection attacks."""
import re
import html
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    """Threat severity levels."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    original: str
    sanitized: str
    threat_level: ThreatLevel
    issues: List[str]
    is_valid: bool
    blocked: bool


class InputSanitizer:
    """
    Multi-layer input sanitization.
    
    Protects against:
    - Prompt injection attacks
    - HTML/script injection
    - Command injection
    - Data exfiltration attempts
    """
    
    # Known injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+system\s+prompt",
        r"forget\s+(?:everything|all)\s+(?:i\s+said|before)",
        r"you\s+are\s+now\s+in\s+.*mode",
        r"act\s+as\s+if\s+you\s+are",
        r"system\s*:\s*",
        r"user\s*:\s*",
        r"assistant\s*:\s*",
        r"developer\s*:\s*",
        r"new\s+instructions?",
        r"override\s+constraints",
        r"bypass\s+restrictions",
        r"simulate\s+(?:admin|root|system)",
        r"pretend\s+to\s+be",
        r"role\s*:\s*(?:system|developer|admin)",
    ]
    
    # Dangerous command patterns
    COMMAND_INJECTION_PATTERNS = [
        r";\s*rm\s+-rf",
        r"\|\s*bash",
        r"\|\s*sh\s+-c",
        r"`\s*rm\s+",
        r"\$\(.*rm",
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"subprocess\.call",
        r"os\.system",
        r"os\.popen",
    ]
    
    # Data exfiltration patterns
    EXFILTRATION_PATTERNS = [
        r"send\s+(?:data|info|password|key|secret)\s+to",
        r"email\s+(?:me|to)\s+.*(?:password|secret|key)",
        r"post\s+to\s+https?://",
        r"curl\s+.*https?://",
        r"wget\s+.*https?://",
        r"upload\s+to",
        r"transfer\s+data",
    ]
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.max_length = 10000
        self.blocked_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency."""
        return {
            "prompt_injection": [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS],
            "command_injection": [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INJECTION_PATTERNS],
            "exfiltration": [re.compile(p, re.IGNORECASE) for p in self.EXFILTRATION_PATTERNS],
        }
    
    def sanitize(self, input_text: str, context: str = "general") -> SanitizationResult:
        """
        Sanitize user input.
        
        Args:
            input_text: Raw user input
            context: Usage context (general, code, file_operation, etc.)
        
        Returns:
            SanitizationResult with sanitized text and threat assessment
        """
        issues = []
        blocked = False
        threat_level = ThreatLevel.SAFE
        
        original = input_text
        
        # Check length
        if len(input_text) > self.max_length:
            issues.append(f"Input exceeds maximum length ({self.max_length} chars)")
            input_text = input_text[:self.max_length]
            threat_level = ThreatLevel.MEDIUM
        
        # Check for prompt injection
        injection_matches = self._check_patterns(input_text, "prompt_injection")
        if injection_matches:
            issues.extend([f"Prompt injection attempt: {m}" for m in injection_matches[:3]])
            threat_level = self._escalate_threat(threat_level, ThreatLevel.HIGH)
            if self.strict_mode:
                blocked = True
        
        # Check for command injection (stricter for code context)
        if context in ["code", "system_command", "file_operation"]:
            command_matches = self._check_patterns(input_text, "command_injection")
            if command_matches:
                issues.extend([f"Command injection: {m}" for m in command_matches[:3]])
                threat_level = self._escalate_threat(threat_level, ThreatLevel.CRITICAL)
                blocked = True
        
        # Check for data exfiltration
        exfil_matches = self._check_patterns(input_text, "exfiltration")
        if exfil_matches:
            issues.extend([f"Potential data exfiltration: {m}" for m in exfil_matches[:3]])
            threat_level = self._escalate_threat(threat_level, ThreatLevel.HIGH)
            blocked = True
        
        # HTML encode to prevent XSS
        sanitized = html.escape(input_text)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return SanitizationResult(
            original=original,
            sanitized=sanitized,
            threat_level=threat_level,
            issues=issues,
            is_valid=not blocked and threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW],
            blocked=blocked
        )
    
    def _check_patterns(self, text: str, pattern_type: str) -> List[str]:
        """Check text against compiled patterns."""
        matches = []
        for pattern in self.blocked_patterns.get(pattern_type, []):
            if pattern.search(text):
                matches.append(pattern.pattern[:50] + "...")
        return matches
    
    def _escalate_threat(self, current: ThreatLevel, new: ThreatLevel) -> ThreatLevel:
        """Escalate threat level if new is higher."""
        levels = [ThreatLevel.SAFE, ThreatLevel.LOW, ThreatLevel.MEDIUM, 
                 ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        return max(current, new, key=lambda x: levels.index(x))
    
    def validate_filename(self, filename: str) -> Tuple[bool, str]:
        """Validate filename for path traversal attempts."""
        # Block path traversal
        if ".." in filename or filename.startswith("/") or ":" in filename:
            return False, "Path traversal detected"
        
        # Block suspicious extensions
        dangerous_exts = ['.exe', '.bat', '.cmd', '.sh', '.php', '.jsp']
        if any(filename.lower().endswith(ext) for ext in dangerous_exts):
            return False, "Potentially dangerous file extension"
        
        return True, "Valid"


class PromptInjectionDetector:
    """Specialized detector for prompt injection attacks."""
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
    
    def detect(self, user_input: str, system_prompt: str) -> Dict:
        """
        Detect if user input is trying to override system prompt.
        
        Returns detection result with confidence score.
        """
        result = self.sanitizer.sanitize(user_input)
        
        # Calculate injection confidence
        confidence = 0.0
        
        if result.threat_level == ThreatLevel.CRITICAL:
            confidence = 1.0
        elif result.threat_level == ThreatLevel.HIGH:
            confidence = 0.8
        elif result.threat_level == ThreatLevel.MEDIUM:
            confidence = 0.5
        elif result.threat_level == ThreatLevel.LOW:
            confidence = 0.2
        
        return {
            "is_injection": result.blocked or confidence > 0.7,
            "confidence": confidence,
            "threat_level": result.threat_level.value,
            "issues": result.issues,
            "sanitized_input": result.sanitized
        }


# Global instance
_sanitizer_instance = None

def get_input_sanitizer() -> InputSanitizer:
    """Get global input sanitizer instance."""
    global _sanitizer_instance
    if _sanitizer_instance is None:
        _sanitizer_instance = InputSanitizer()
    return _sanitizer_instance
