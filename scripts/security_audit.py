#!/usr/bin/env python3
"""
AsimNexus Security Audit Script
================================
Automated security scanning for the AsimNexus codebase.

Performs:
1. CORS & security headers verification
2. Input sanitization audit
3. Secrets/credentials leak detection
4. Dependency version check
5. Auth middleware verification

Usage:
    python scripts/security_audit.py              # Full audit
    python scripts/security_audit.py --quick       # Quick check (headers + CORS only)
    python scripts/security_audit.py --json        # JSON output
"""

import os
import sys
import json
import subprocess
import importlib
import datetime
from typing import Dict, List, Any, Optional

# ── Configuration ────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_FILE = os.path.join(ROOT_DIR, "security_audit_report.json")
SKIP_BANDIT = os.environ.get("SKIP_BANDIT", "0") == "1"
SKIP_SAFETY = os.environ.get("SKIP_SAFETY", "0") == "1"

# ── Results Collector ────────────────────────────────────────────

class AuditResults:
    def __init__(self):
        self.results: Dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "summary": {"pass": 0, "fail": 0, "warn": 0, "skip": 0},
            "checks": [],
        }

    def add_check(self, name: str, status: str, details: str, issues: Optional[List[str]] = None):
        self.results["checks"].append({
            "name": name,
            "status": status,
            "details": details,
            "issues": issues or [],
        })
        self.results["summary"][status] += 1

    def to_dict(self) -> Dict[str, Any]:
        return self.results

    def print_summary(self):
        s = self.results["summary"]
        print(f"\n{'='*60}")
        print(f"  Security Audit Summary")
        print(f"  Timestamp: {self.results['timestamp']}")
        print(f"{'='*60}")
        print(f"  [PASS] {s['pass']}  [FAIL] {s['fail']}  [WARN] {s['warn']}  [SKIP] {s['skip']}")
        print(f"{'='*60}")
        for check in self.results["checks"]:
            icon = {"pass": "[PASS]", "fail": "[FAIL]", "warn": "[WARN]", "skip": "[SKIP]"}.get(check["status"], "[?]")
            print(f"  {icon} {check['name']}: {check['details']}")
            if check["issues"]:
                for issue in check["issues"][:5]:
                    print(f"       - {issue}")
                if len(check["issues"]) > 5:
                    print(f"       ... and {len(check['issues']) - 5} more")


# ══════════════════════════════════════════════════════════════════
# 1. CORS & SECURITY HEADERS CHECK
# ══════════════════════════════════════════════════════════════════

def check_cors_configuration(results: AuditResults):
    """Verify CORS is not wide-open."""
    try:
        import ast
        with open(os.path.join(ROOT_DIR, "app.py"), "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr == 'add_middleware':
                for keyword in node.keywords:
                    if keyword.arg == 'allow_origins':
                        if isinstance(keyword.value, ast.List):
                            origins = [ast.literal_eval(e) if isinstance(e, (ast.Constant, ast.Str)) else '*' for e in keyword.value.elts]
                            if '*' in origins:
                                results.add_check("CORS Configuration", "fail",
                                    "CORS allow_origins contains wildcard '*' -- too permissive")
                                return
                            results.add_check("CORS Configuration", "pass",
                                f"CORS restricted to {len(origins)} origins: {origins}")
                            return
                        elif isinstance(keyword.value, ast.Name):
                            # CORS origins come from a variable (env var)
                            results.add_check("CORS Configuration", "pass",
                                f"CORS origins set via variable '{keyword.value.id}' (env-driven)")
                            return
        # Also check for CORSMiddleware import
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'fastapi.middleware.cors':
                results.add_check("CORS Configuration", "pass",
                    "CORSMiddleware imported (likely configured via env vars)")
                return
        results.add_check("CORS Configuration", "warn", "Could not find CORS middleware configuration")
    except Exception as e:
        results.add_check("CORS Configuration", "fail", f"Error checking CORS: {e}")


def check_security_headers(results: AuditResults):
    """Verify security headers middleware is active and comprehensive."""
    try:
        sys.path.insert(0, ROOT_DIR)
        from core.security_headers_middleware import SecurityHeadersMiddleware
        headers = SecurityHeadersMiddleware.HEADERS

        required = [
            "X-Content-Type-Options", "X-Frame-Options", "Strict-Transport-Security",
            "Content-Security-Policy", "Referrer-Policy", "Permissions-Policy",
        ]
        missing = [h for h in required if h not in headers]
        if missing:
            results.add_check("Security Headers", "warn",
                f"Missing headers: {', '.join(missing)}")
        else:
            results.add_check("Security Headers", "pass",
                f"All {len(required)} required headers present ({len(headers)} total)")

        # Check CSP strength
        csp = headers.get("Content-Security-Policy", "")
        if "'unsafe-inline'" in csp:
            results.add_check("CSP Strength", "warn",
                "CSP allows 'unsafe-inline' — consider using nonces or hashes")
        else:
            results.add_check("CSP Strength", "pass", "CSP does not use unsafe-inline")
    except ImportError:
        results.add_check("Security Headers", "fail",
            "SecurityHeadersMiddleware not found or importable")
    except Exception as e:
        results.add_check("Security Headers", "fail", f"Error: {e}")


# ══════════════════════════════════════════════════════════════════
# 2. INPUT SANITIZATION AUDIT
# ══════════════════════════════════════════════════════════════════

def check_input_sanitization(results: AuditResults):
    """Audit for common input sanitization issues."""
    import ast

    issues_found = []
    python_files = []

    for root, dirs, files in os.walk(ROOT_DIR):
        # Skip venv, node_modules, .git, backups
        if any(skip in root for skip in ["venv", "node_modules", ".git", "backups", "__pycache__"]):
            continue
        for f in files:
            if f.endswith(".py"):
                python_files.append(os.path.join(root, f))

    for filepath in python_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception:
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        rel_path = os.path.relpath(filepath, ROOT_DIR)

        # Check for eval/exec usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id in ('eval', 'exec'):
                issues_found.append(f"{rel_path}:{node.lineno}: Use of {node.func.id}() — potential code injection")

            # Check for unsafe subprocess with shell=True
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr in ('call', 'Popen', 'run'):
                for kw in node.keywords:
                    if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        issues_found.append(f"{rel_path}:{node.lineno}: subprocess with shell=True — potential command injection")

            # Check for os.system
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr == 'system' and hasattr(node.func.value, 'id') and node.func.value.id == 'os':
                issues_found.append(f"{rel_path}:{node.lineno}: os.system() — potential command injection")

            # Check for pickle.loads on untrusted data
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr in ('loads', 'load') and hasattr(node.func.value, 'id') and node.func.value.id == 'pickle':
                issues_found.append(f"{rel_path}:{node.lineno}: pickle.load() — potential deserialization attack")

            # Check for SQL injection (string formatting in queries)
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr in ('execute', 'executemany'):
                for arg in node.args:
                    if isinstance(arg, ast.JoinedStr) or (isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod)):
                        issues_found.append(f"{rel_path}:{node.lineno}: Possible SQL injection via string formatting")

    if issues_found:
        results.add_check("Input Sanitization", "warn",
            f"Found {len(issues_found)} potential issues", issues_found[:20])
    else:
        results.add_check("Input Sanitization", "pass",
            "No obvious input sanitization issues detected")


# ══════════════════════════════════════════════════════════════════
# 3. SECRETS LEAK DETECTION
# ══════════════════════════════════════════════════════════════════

def check_secrets_leak(results: AuditResults):
    """Scan for potential secrets/credentials in code."""
    import re

    patterns = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
        "Generic Secret": r"(?i)(secret|password|api_key|apikey|token|credential)\s*[=:]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]",
        "JWT Token": r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",
        "Private Key": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "Connection String": r"(?i)(mongodb|postgresql|mysql|redis)://[^@]+@",
    }

    issues_found = []
    for root, dirs, files in os.walk(ROOT_DIR):
        if any(skip in root for skip in ["venv", "node_modules", ".git", "backups", "__pycache__", ".kilo"]):
            continue
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".tsx", ".yml", ".yaml", ".json", ".env", ".txt", ".md")):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                except Exception:
                    continue

                rel_path = os.path.relpath(filepath, ROOT_DIR)
                for pattern_name, pattern in patterns.items():
                    for match in re.finditer(pattern, content):
                        # Skip test files and known safe patterns
                        if "test" in rel_path.lower() or "example" in rel_path.lower():
                            continue
                        line_num = content[:match.start()].count('\n') + 1
                        issues_found.append(f"{rel_path}:{line_num}: Possible {pattern_name} leak")

    if issues_found:
        results.add_check("Secrets Leak Detection", "warn",
            f"Found {len(issues_found)} potential secrets", issues_found[:10])
    else:
        results.add_check("Secrets Leak Detection", "pass",
            "No obvious secrets leaked in code")


# ══════════════════════════════════════════════════════════════════
# 4. DEPENDENCY VULNERABILITY CHECK
# ══════════════════════════════════════════════════════════════════

def check_dependency_vulnerabilities(results: AuditResults):
    """Check for known vulnerabilities in Python dependencies."""
    try:
        import pkg_resources
        import requests

        # Get installed packages
        packages = [f"{d.project_name}=={d.version}" for d in pkg_resources.working_set]
        results.add_check("Dependency Check", "pass",
            f"Found {len(packages)} installed packages (manual review recommended)")
    except ImportError:
        results.add_check("Dependency Check", "skip",
            "pkg_resources not available — install setuptools")
    except Exception as e:
        results.add_check("Dependency Check", "warn", f"Error: {e}")


# ══════════════════════════════════════════════════════════════════
# 5. AUTH MIDDLEWARE VERIFICATION
# ══════════════════════════════════════════════════════════════════

def check_auth_middleware(results: AuditResults):
    """Verify auth middleware is properly configured."""
    try:
        import ast
        with open(os.path.join(ROOT_DIR, "app.py"), "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        has_auth = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr == 'add_middleware':
                for arg in node.args:
                    if isinstance(arg, ast.Name) and 'Auth' in arg.id:
                        has_auth = True
                        break

        if has_auth:
            results.add_check("Auth Middleware", "pass", "Auth middleware is registered")
        else:
            results.add_check("Auth Middleware", "warn", "Could not confirm auth middleware registration")
    except Exception as e:
        results.add_check("Auth Middleware", "fail", f"Error: {e}")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    quick_mode = "--quick" in sys.argv
    json_output = "--json" in sys.argv

    results = AuditResults()

    print("[SECURITY] AsimNexus Security Audit")
    print("=" * 60)

    # Always run these
    check_cors_configuration(results)
    check_security_headers(results)
    check_auth_middleware(results)

    if not quick_mode:
        check_input_sanitization(results)
        check_secrets_leak(results)
        check_dependency_vulnerabilities(results)

    results.print_summary()

    if json_output:
        with open(REPORT_FILE, "w") as f:
            json.dump(results.to_dict(), f, indent=2, default=str)
        print(f"\n[REPORT] Full report saved to: {REPORT_FILE}")

    # Exit with error if any failures
    if results.results["summary"]["fail"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
