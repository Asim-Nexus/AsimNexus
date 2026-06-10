
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Security Audit Module
===============================
Comprehensive security auditing system
Includes: Auth, Injection, API, Dependency, Business Logic audits
"""

import asyncio
import logging
import ast
import re
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("SecurityAudit")


class Severity(Enum):
    """Severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuditType(Enum):
    """Types of security audits"""
    AUTH_AUTHORIZATION = "auth_authorization"
    INJECTION_INPUT_VALIDATION = "injection_input_validation"
    API_DATA_EXPOSURE = "api_data_exposure"
    DEPENDENCY_CONFIG = "dependency_config"
    BUSINESS_LOGIC = "business_logic"


@dataclass
class SecurityFinding:
    """Security finding"""
    finding_id: str
    audit_type: AuditType
    severity: Severity
    title: str
    description: str
    location: str
    line_number: Optional[int]
    recommendation: str
    code_snippet: Optional[str]
    fixed_snippet: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditReport:
    """Security audit report"""
    report_id: str
    audit_type: AuditType
    findings: List[SecurityFinding]
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SecurityAudit:
    """Security audit system"""
    
    def __init__(self):
        self.findings: Dict[str, SecurityFinding] = {}
        self.reports: Dict[str, AuditReport] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize security audit system"""
        logger.info("🔒 Initializing Security Audit System...")
        logger.info("🔐 Setting up Authentication Audit")
        logger.info("💉 Setting up Injection Audit")
        logger.info("🌐 Setting up API Exposure Audit")
        logger.info("📦 Setting up Dependency Audit")
        logger.info("🧠 Setting up Business Logic Audit")
        logger.info("✅ Security Audit System initialized")
    
    def audit_file(self, file_path: str) -> List[AuditReport]:
        """Audit a single file for all security issues"""
        reports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Run all 5 audit types
            reports.append(self._audit_auth_authorization(file_path, content))
            reports.append(self._audit_injection_input_validation(file_path, content))
            reports.append(self._audit_api_data_exposure(file_path, content))
            reports.append(self._audit_dependency_config(file_path, content))
            reports.append(self._audit_business_logic(file_path, content))
            
            logger.info(f"✅ Completed security audit for: {file_path}")
            return reports
        
        except Exception as e:
            logger.error(f"Audit error for {file_path}: {e}")
            return []
    
    def _audit_auth_authorization(self, file_path: str, content: str) -> AuditReport:
        """Audit for authentication and authorization issues"""
        findings = []
        lines = content.split('\n')
        
        # Check for hardcoded credentials
        for i, line in enumerate(lines, 1):
            if re.search(r'(password|secret|api_key|token)\s*=\s*["\'].*["\']', line, re.IGNORECASE):
                if not re.search(r'(os\.getenv|environ|config)', line):
                    findings.append(SecurityFinding(
                        finding_id=f"auth_{uuid.uuid4().hex[:8]}",
                        audit_type=AuditType.AUTH_AUTHORIZATION,
                        severity=Severity.HIGH,
                        title="Hardcoded Credential",
                        description="Hardcoded credential detected in code",
                        location=file_path,
                        line_number=i,
                        recommendation="Use environment variables or secret management",
                        code_snippet=line.strip(),
                        fixed_snippet="variable = os.getenv('ENV_VAR')"
                    ))
        
        # Check for weak password patterns
        if re.search(r'(password|pwd)\s*=\s*["\'].*["\']', content, re.IGNORECASE):
            findings.append(SecurityFinding(
                finding_id=f"auth_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.AUTH_AUTHORIZATION,
                severity=Severity.MEDIUM,
                title="Weak Password Pattern",
                description="Potential weak password pattern detected",
                location=file_path,
                line_number=None,
                recommendation="Use strong password policies and hashing",
                code_snippet="password = '...'",
                fixed_snippet="password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
            ))
        
        # Check for missing JWT validation
        if 'jwt' in content.lower() and 'verify' not in content.lower():
            findings.append(SecurityFinding(
                finding_id=f"auth_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.AUTH_AUTHORIZATION,
                severity=Severity.HIGH,
                title="Missing JWT Validation",
                description="JWT token usage without proper validation",
                location=file_path,
                line_number=None,
                recommendation="Always validate JWT tokens before use",
                code_snippet="jwt.decode(token)",
                fixed_snippet="jwt.decode(token, options={'verify_signature': True})"
            ))
        
        return self._create_report(AuditType.AUTH_AUTHORIZATION, findings)
    
    def _audit_injection_input_validation(self, file_path: str, content: str) -> AuditReport:
        """Audit for injection vulnerabilities"""
        findings = []
        lines = content.split('\n')
        
        # Check for SQL injection patterns
        for i, line in enumerate(lines, 1):
            if re.search(r'(execute|query|cursor)\([^)]*\+[^)]*\)', line):
                findings.append(SecurityFinding(
                    finding_id=f"inj_{uuid.uuid4().hex[:8]}",
                    audit_type=AuditType.INJECTION_INPUT_VALIDATION,
                    severity=Severity.CRITICAL,
                    title="SQL Injection Risk",
                    description="String concatenation in SQL query",
                    location=file_path,
                    line_number=i,
                    recommendation="Use parameterized queries",
                    code_snippet=line.strip(),
                    fixed_snippet="cursor.execute(query, params)"
                ))
        
        # Check for command injection
        if re.search(r'(os\.system|subprocess\.call|subprocess\.run)\([^)]*\+[^)]*\)', content):
            findings.append(SecurityFinding(
                finding_id=f"inj_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.INJECTION_INPUT_VALIDATION,
                severity=Severity.CRITICAL,
                title="Command Injection Risk",
                description="String concatenation in system command",
                location=file_path,
                line_number=None,
                recommendation="Use subprocess with shell=False and validate input",
                code_snippet="os.system(cmd + user_input)",
                fixed_snippet="subprocess.run([cmd, validated_input], shell=False)"
            ))
        
        # Check for XSS patterns
        if re.search(r'(innerHTML|outerHTML)\s*=', content):
            findings.append(SecurityFinding(
                finding_id=f"inj_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.INJECTION_INPUT_VALIDATION,
                severity=Severity.HIGH,
                title="XSS Vulnerability",
                description="Direct HTML injection without sanitization",
                location=file_path,
                line_number=None,
                recommendation="Use textContent or sanitize HTML",
                code_snippet="element.innerHTML = user_input",
                fixed_snippet="element.textContent = user_input"
            ))
        
        # Check for LLM prompt injection
        if 'prompt' in content.lower() and 'sanitize' not in content.lower():
            findings.append(SecurityFinding(
                finding_id=f"inj_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.INJECTION_INPUT_VALIDATION,
                severity=Severity.HIGH,
                title="LLM Prompt Injection Risk",
                description="User input directly used in LLM prompt without sanitization",
                location=file_path,
                line_number=None,
                recommendation="Sanitize and validate user input before using in prompts",
                code_snippet="prompt = user_input",
                fixed_snippet="prompt = sanitize_input(user_input)"
            ))
        
        return self._create_report(AuditType.INJECTION_INPUT_VALIDATION, findings)
    
    def _audit_api_data_exposure(self, file_path: str, content: str) -> AuditReport:
        """Audit for API and data exposure issues"""
        findings = []
        
        # Check for sensitive data in logs
        if re.search(r'(logger|print|log)\([^)]*(password|token|secret|key)', content, re.IGNORECASE):
            findings.append(SecurityFinding(
                finding_id=f"api_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.API_DATA_EXPOSURE,
                severity=Severity.HIGH,
                title="Sensitive Data in Logs",
                description="Logging sensitive information",
                location=file_path,
                line_number=None,
                recommendation="Never log sensitive data",
                code_snippet="logger.info(f'Token: {token}')",
                fixed_snippet="logger.info('Token processed')"
            ))
        
        # Check for verbose error messages
        if re.search(r'(except.*:.*print|except.*:.*logger)', content):
            findings.append(SecurityFinding(
                finding_id=f"api_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.API_DATA_EXPOSURE,
                severity=Severity.MEDIUM,
                title="Verbose Error Message",
                description="Detailed error messages may expose system information",
                location=file_path,
                line_number=None,
                recommendation="Use generic error messages in production",
                code_snippet="except Exception as e: print(str(e))",
                fixed_snippet="except Exception as e: logger.error('Error occurred')"
            ))
        
        # Check for missing rate limiting
        if 'api' in content.lower() and 'rate_limit' not in content.lower():
            findings.append(SecurityFinding(
                finding_id=f"api_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.API_DATA_EXPOSURE,
                severity=Severity.MEDIUM,
                title="Missing Rate Limiting",
                description="API endpoint without rate limiting",
                location=file_path,
                line_number=None,
                recommendation="Implement rate limiting on all API endpoints",
                code_snippet="@app.route('/api/data')",
                fixed_snippet="@app.route('/api/data')\n@limiter.limit('100/hour')"
            ))
        
        return self._create_report(AuditType.API_DATA_EXPOSURE, findings)
    
    def _audit_dependency_config(self, file_path: str, content: str) -> AuditReport:
        """Audit for dependency and configuration issues"""
        findings = []
        
        # Check for hardcoded URLs
        if re.search(r'https?://[^\s"\']+', content):
            findings.append(SecurityFinding(
                finding_id=f"dep_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.DEPENDENCY_CONFIG,
                severity=Severity.LOW,
                title="Hardcoded URL",
                description="Hardcoded URL detected",
                location=file_path,
                line_number=None,
                recommendation="Use environment variables for URLs",
                code_snippet="url = 'https://api.example.com'",
                fixed_snippet="url = os.getenv('API_URL', 'https://api.example.com')"
            ))
        
        # Check for insecure TLS/SSL
        if re.search(r'(ssl|tls).*verify\s*=\s*False', content, re.IGNORECASE):
            findings.append(SecurityFinding(
                finding_id=f"dep_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.DEPENDENCY_CONFIG,
                severity=Severity.HIGH,
                title="Insecure SSL Configuration",
                description="SSL verification disabled",
                location=file_path,
                line_number=None,
                recommendation="Always enable SSL verification",
                code_snippet="verify=False",
                fixed_snippet="verify=True"
            ))
        
        # Check for debug mode in production
        if re.search(r'debug\s*=\s*True', content):
            findings.append(SecurityFinding(
                finding_id=f"dep_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.DEPENDENCY_CONFIG,
                severity=Severity.HIGH,
                title="Debug Mode Enabled",
                description="Debug mode should be disabled in production",
                location=file_path,
                line_number=None,
                recommendation="Use environment variable for debug mode",
                code_snippet="DEBUG = True",
                fixed_snippet="DEBUG = os.getenv('DEBUG', 'False') == 'True'"
            ))
        
        return self._create_report(AuditType.DEPENDENCY_CONFIG, findings)
    
    def _audit_business_logic(self, file_path: str, content: str) -> AuditReport:
        """Audit for business logic and state management issues"""
        findings = []
        
        # Check for race conditions
        if re.search(r'(global|shared).*state', content, re.IGNORECASE):
            findings.append(SecurityFinding(
                finding_id=f"biz_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.BUSINESS_LOGIC,
                severity=Severity.HIGH,
                title="Potential Race Condition",
                description="Shared state without proper synchronization",
                location=file_path,
                line_number=None,
                recommendation="Use proper locking mechanisms for shared state",
                code_snippet="global state",
                fixed_snippet="with lock: state = ..."
            ))
        
        # Check for IDOR (Insecure Direct Object Reference)
        if re.search(r'user_id|object_id', content, re.IGNORECASE) and 'authorize' not in content.lower():
            findings.append(SecurityFinding(
                finding_id=f"biz_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.BUSINESS_LOGIC,
                severity=Severity.HIGH,
                title="Potential IDOR",
                description="Direct object reference without authorization check",
                location=file_path,
                line_number=None,
                recommendation="Always verify user has access to requested object",
                code_snippet="get_object(user_id)",
                fixed_snippet="if user_can_access(current_user, user_id): get_object(user_id)"
            ))
        
        # Check for economic attack vectors in token operations
        if re.search(r'(transfer|send).*token', content, re.IGNORECASE):
            findings.append(SecurityFinding(
                finding_id=f"biz_{uuid.uuid4().hex[:8]}",
                audit_type=AuditType.BUSINESS_LOGIC,
                severity=Severity.HIGH,
                title="Economic Attack Vector",
                description="Token transfer without proper validation",
                location=file_path,
                line_number=None,
                recommendation="Implement double-spend protection and transaction validation",
                code_snippet="transfer_tokens(from, to, amount)",
                fixed_snippet="validate_and_transfer(from, to, amount, nonce)"
            ))
        
        return self._create_report(AuditType.BUSINESS_LOGIC, findings)
    
    def _create_report(self, audit_type: AuditType, findings: List[SecurityFinding]) -> AuditReport:
        """Create audit report from findings"""
        critical = len([f for f in findings if f.severity == Severity.CRITICAL])
        high = len([f for f in findings if f.severity == Severity.HIGH])
        medium = len([f for f in findings if f.severity == Severity.MEDIUM])
        low = len([f for f in findings if f.severity == Severity.LOW])
        
        report = AuditReport(
            report_id=f"report_{uuid.uuid4().hex[:8]}",
            audit_type=audit_type,
            findings=findings,
            total_findings=len(findings),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low
        )
        
        self.reports[report.report_id] = report
        
        for finding in findings:
            self.findings[finding.finding_id] = finding
        
        return report
    
    def audit_directory(self, directory: str) -> Dict[str, List[AuditReport]]:
        """Audit entire directory"""
        reports = {}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    file_reports = self.audit_file(file_path)
                    if file_reports:
                        reports[file_path] = file_reports
        
        return reports
    
    def get_findings_by_severity(self, severity: Severity) -> List[SecurityFinding]:
        """Get findings by severity"""
        return [f for f in self.findings.values() if f.severity == severity]
    
    def get_findings_by_type(self, audit_type: AuditType) -> List[SecurityFinding]:
        """Get findings by audit type"""
        return [f for f in self.findings.values() if f.audit_type == audit_type]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get security audit summary"""
        severity_counts = {}
        for finding in self.findings.values():
            severity_counts[finding.severity.value] = severity_counts.get(finding.severity.value, 0) + 1
        
        type_counts = {}
        for finding in self.findings.values():
            type_counts[finding.audit_type.value] = type_counts.get(finding.audit_type.value, 0) + 1
        
        return {
            "total_findings": len(self.findings),
            "total_reports": len(self.reports),
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
            "medium_count": severity_counts.get("medium", 0),
            "low_count": severity_counts.get("low", 0)
        }


# Global instance
_security_audit: Optional[SecurityAudit] = None


def get_security_audit() -> SecurityAudit:
    """Get singleton instance"""
    global _security_audit
    if _security_audit is None:
        _security_audit = SecurityAudit()
    return _security_audit
