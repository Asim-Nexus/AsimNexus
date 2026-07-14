"""
Mythos Scanner — AI-powered vulnerability scanner for ASIMNEXUS.
===============================================================
Detects security vulnerabilities in source code using pattern matching
and AST analysis, generates patches, and supports auto-patching.

Exports:
    MythosScanner       — main scanner class
    Vulnerability       — dataclass representing a detected vulnerability
    SecurityPatch       — dataclass representing a generated patch
    VulnerabilitySeverity — enum for severity levels
    VulnerabilityType   — enum for vulnerability types
"""

import ast
import os
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class VulnerabilitySeverity(Enum):
    """Severity levels for vulnerabilities."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Types of vulnerabilities detected."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    HARDCODED_SECRET = "hardcoded_secret"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    WEAK_CRYPTO = "weak_crypto"
    HARDCODED_PASSWORD = "hardcoded_password"
    DANGEROUS_IMPORT = "dangerous_import"
    INFO_LEAK = "info_leak"


@dataclass
class Vulnerability:
    """A detected security vulnerability."""
    id: str
    type: VulnerabilityType
    severity: VulnerabilitySeverity
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    patched: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPatch:
    """A generated security patch for a vulnerability."""
    id: str
    vulnerability_id: str
    original_code: str
    patched_code: str
    applied: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Pattern definitions ─────────────────────────────────────────────────────

_PATTERNS: Dict[str, List[Dict[str, Any]]] = {
    "sql_injection": [
        {
            "regex": r'execute\s*\(\s*["\'].*?\+.*?["\']',
            "severity": VulnerabilitySeverity.CRITICAL,
            "description": "SQL injection: string concatenation in query execution",
        },
        {
            "regex": r'SELECT\s+.*?\+\s*',
            "severity": VulnerabilitySeverity.CRITICAL,
            "description": "SQL injection: string concatenation in SELECT query",
        },
    ],
    "xss": [
        {
            "regex": r'\.innerHTML\s*=',
            "severity": VulnerabilitySeverity.HIGH,
            "description": "XSS: assigning to innerHTML",
        },
        {
            "regex": r'document\.write\s*\(',
            "severity": VulnerabilitySeverity.HIGH,
            "description": "XSS: using document.write",
        },
    ],
    "hardcoded_secret": [
        {
            "regex": r'(?:API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)\s*=\s*["\'][A-Za-z0-9_\-]{8,}',
            "severity": VulnerabilitySeverity.HIGH,
            "description": "Hardcoded secret or API key",
        },
        {
            "regex": r'password\s*=\s*["\'][^"\']{4,}',
            "severity": VulnerabilitySeverity.HIGH,
            "description": "Hardcoded password",
        },
    ],
    "command_injection": [
        {
            "regex": r'(?:os\.system|subprocess\.(?:call|Popen|run))\s*\(.*?\+',
            "severity": VulnerabilitySeverity.CRITICAL,
            "description": "Command injection: string concatenation in shell command",
        },
    ],
    "insecure_deserialization": [
        {
            "regex": r'pickle\.(?:loads|load)\s*\(',
            "severity": VulnerabilitySeverity.HIGH,
            "description": "Insecure deserialization using pickle",
        },
    ],
    "weak_crypto": [
        {
            "regex": r'(?:md5|sha1)\s*\(',
            "severity": VulnerabilitySeverity.MEDIUM,
            "description": "Weak cryptographic hash function",
        },
    ],
}


class MythosScanner:
    """AI-powered vulnerability scanner with pattern matching and AST analysis."""

    def __init__(self):
        self.patterns = _PATTERNS
        self._vulnerabilities: List[Vulnerability] = []
        self._patches: List[SecurityPatch] = []

    # ── Scanning ─────────────────────────────────────────────────────────

    def scan_file(self, file_path: str, code: str) -> List[Vulnerability]:
        """Scan a single file's code for vulnerabilities.

        Args:
            file_path: Path to the file (used for reporting)
            code: Source code content to scan

        Returns:
            List of detected Vulnerability objects
        """
        found: List[Vulnerability] = []

        # Pattern-based scanning
        for vuln_type, patterns in self.patterns.items():
            for pattern_def in patterns:
                for match in re.finditer(pattern_def["regex"], code, re.IGNORECASE):
                    line_number = code[:match.start()].count("\n") + 1
                    vuln = Vulnerability(
                        id=f"{vuln_type}_{uuid.uuid4().hex[:8]}",
                        type=VulnerabilityType(vuln_type),
                        severity=pattern_def["severity"],
                        file_path=file_path,
                        line_number=line_number,
                        description=pattern_def["description"],
                        code_snippet=match.group().strip(),
                    )
                    found.append(vuln)

        # AST analysis for Python files
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(code)
                found.extend(self._ast_scan(tree, file_path, code))
            except SyntaxError:
                pass

        self._vulnerabilities.extend(found)
        return found

    def scan_directory(self, directory: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scan all files in a directory for vulnerabilities.

        Args:
            directory: Path to the directory to scan
            extensions: List of file extensions to scan (e.g. ['.py', '.js'])

        Returns:
            Dict with 'files_scanned' and 'vulnerabilities_found' counts
        """
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".java", ".php"]

        files_scanned = 0
        vulnerabilities_found = 0

        for root, _dirs, files in os.walk(directory):
            for filename in files:
                if any(filename.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            code = f.read()
                        vulns = self.scan_file(filepath, code)
                        files_scanned += 1
                        vulnerabilities_found += len(vulns)
                    except (IOError, OSError):
                        pass

        return {
            "files_scanned": files_scanned,
            "vulnerabilities_found": vulnerabilities_found,
        }

    # ── AST Analysis ─────────────────────────────────────────────────────

    def _ast_scan(self, tree: ast.AST, file_path: str, code: str) -> List[Vulnerability]:
        """Scan AST for dangerous patterns."""
        found: List[Vulnerability] = []

        for node in ast.walk(tree):
            # Detect dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("pickle", "subprocess", "shelve", "marshal"):
                        vuln = Vulnerability(
                            id=f"dangerous_import_{uuid.uuid4().hex[:8]}",
                            type=VulnerabilityType.DANGEROUS_IMPORT,
                            severity=VulnerabilitySeverity.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            description=f"Dangerous import: {alias.name}",
                            code_snippet=f"import {alias.name}",
                        )
                        found.append(vuln)

            # Detect eval/exec usage
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    vuln = Vulnerability(
                        id=f"dangerous_call_{uuid.uuid4().hex[:8]}",
                        type=VulnerabilityType.COMMAND_INJECTION,
                        severity=VulnerabilitySeverity.HIGH,
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Dangerous function call: {node.func.id}()",
                        code_snippet=ast.get_source_segment(code, node) or node.func.id,
                    )
                    found.append(vuln)

        return found

    # ── Patch Generation ─────────────────────────────────────────────────

    def generate_patch(self, vulnerability: Vulnerability) -> Optional[SecurityPatch]:
        """Generate a security patch for a vulnerability.

        Args:
            vulnerability: The Vulnerability to patch

        Returns:
            SecurityPatch if a patch could be generated, None otherwise
        """
        patched_code = self._generate_patched_code(vulnerability)
        if patched_code is None:
            return None

        patch = SecurityPatch(
            id=f"patch_{uuid.uuid4().hex[:8]}",
            vulnerability_id=vulnerability.id,
            original_code=vulnerability.code_snippet,
            patched_code=patched_code,
        )
        self._patches.append(patch)
        return patch

    def _generate_patched_code(self, vulnerability: Vulnerability) -> Optional[str]:
        """Generate patched code for a vulnerability type."""
        vuln_type = vulnerability.type

        if vuln_type == VulnerabilityType.SQL_INJECTION:
            # Replace string concatenation with parameterized query
            return re.sub(
                r'\s*\+\s*\w+',
                ' ?',
                vulnerability.code_snippet,
            )

        if vuln_type == VulnerabilityType.XSS:
            # Replace innerHTML with textContent
            return vulnerability.code_snippet.replace("innerHTML", "textContent")

        if vuln_type == VulnerabilityType.HARDCODED_SECRET:
            # Replace hardcoded value with environment variable reference
            return re.sub(
                r'=\s*["\'][^"\']+["\']',
                '= os.environ.get("SECRET")',
                vulnerability.code_snippet,
            )

        if vuln_type == VulnerabilityType.HARDCODED_PASSWORD:
            return re.sub(
                r'=\s*["\'][^"\']+["\']',
                '= os.environ.get("PASSWORD")',
                vulnerability.code_snippet,
            )

        if vuln_type == VulnerabilityType.COMMAND_INJECTION:
            # Add shlex.quote() wrapping
            return vulnerability.code_snippet.replace(
                "+", "+ shlex.quote("
            ) + ")"

        if vuln_type == VulnerabilityType.INSECURE_DESERIALIZATION:
            return vulnerability.code_snippet.replace(
                "pickle", "json"
            ).replace("loads", "loads")

        if vuln_type == VulnerabilityType.WEAK_CRYPTO:
            return vulnerability.code_snippet.replace(
                "md5(", "hashlib.sha256("
            ).replace("sha1(", "hashlib.sha256(")

        return None

    # ── Query Methods ────────────────────────────────────────────────────

    def get_vulnerabilities(self, severity: Optional[VulnerabilitySeverity] = None) -> List[Vulnerability]:
        """Get detected vulnerabilities, optionally filtered by severity.

        Args:
            severity: Optional severity level to filter by

        Returns:
            List of Vulnerability objects
        """
        if severity is None:
            return list(self._vulnerabilities)
        return [v for v in self._vulnerabilities if v.severity == severity]

    def get_unpatched_vulnerabilities(self) -> List[Vulnerability]:
        """Get vulnerabilities that have not been patched yet.

        Returns:
            List of unpatched Vulnerability objects
        """
        return [v for v in self._vulnerabilities if not v.patched]

    def get_scan_summary(self) -> Dict[str, Any]:
        """Get a summary of the scan results.

        Returns:
            Dict with 'total_vulnerabilities' and 'severity_distribution'
        """
        severity_distribution: Dict[str, int] = {}
        for vuln in self._vulnerabilities:
            key = vuln.severity.value
            severity_distribution[key] = severity_distribution.get(key, 0) + 1

        return {
            "total_vulnerabilities": len(self._vulnerabilities),
            "severity_distribution": severity_distribution,
            "total_patches": len(self._patches),
            "patches_applied": sum(1 for p in self._patches if p.applied),
        }

    # ── Auto-Patching ────────────────────────────────────────────────────

    def auto_patch_all(self) -> Dict[str, Any]:
        """Generate and apply patches for all unpatched vulnerabilities.

        Returns:
            Dict with 'patches_generated' and 'patches_applied' counts
        """
        patches_generated = 0
        patches_applied = 0

        for vuln in self.get_unpatched_vulnerabilities():
            patch = self.generate_patch(vuln)
            if patch is not None:
                patches_generated += 1
                # Mark as applied (in-memory)
                patch.applied = True
                vuln.patched = True
                patches_applied += 1

        return {
            "patches_generated": patches_generated,
            "patches_applied": patches_applied,
        }
