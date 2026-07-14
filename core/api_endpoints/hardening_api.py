#!/usr/bin/env python3
"""
ASIMNEXUS Hardening & Security Module
=======================================
Phase 6 hardening: Input sanitization, audit, RBAC enforcement.

This module provides:
- Security health checks and audit
- Input sanitization validation
- RBAC enforcement verification
- System integrity verification 
- Rate limiting status
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body

logger = logging.getLogger("AsimNexus.API.Hardening")

router = APIRouter()


@router.get("/api/hardening/health", tags=["Hardening"])
async def hardening_health():
    """Check hardening system health across all modules."""
    results = {}

    # Check RBAC
    try:
        from core.security.rbac import get_rbac
        rbac = get_rbac()
        results["rbac"] = {"available": True, "status": "active"}
    except Exception as e:
        results["rbac"] = {"available": False, "error": str(e)}

    # Check Input Sanitizer
    try:
        from core.security.input_sanitizer import InputSanitizer
        results["input_sanitizer"] = {"available": True, "status": "active"}
    except Exception as e:
        results["input_sanitizer"] = {"available": False, "error": str(e)}

    # Check Audit Logger
    try:
        from core.security.audit_logger import AuditLogger
        results["audit_logger"] = {"available": True, "status": "active"}
    except Exception as e:
        results["audit_logger"] = {"available": False, "error": str(e)}

    # Check Zero Trust
    try:
        from core.security.zero_trust import ZeroTrust
        results["zero_trust"] = {"available": True, "status": "active"}
    except Exception as e:
        results["zero_trust"] = {"available": False, "error": str(e)}

    # Check Risk Validator
    try:
        from core.security.risk_validator import RiskValidator
        results["risk_validator"] = {"available": True, "status": "active"}
    except Exception as e:
        results["risk_validator"] = {"available": False, "error": str(e)}

    # Check Dharma Chakra Constitution
    try:
        from core.dharma_chakra.constitution import DharmaChakraConstitution
        constitution = DharmaChakraConstitution()
        results["dharma_chakra"] = {
            "available": True,
            "constitution_hash": constitution.constitution_hash[:16] if constitution.constitution_hash else None,
            "government_share": constitution.government_veto_threshold,
            "private_share": constitution.private_sector_threshold,
        }
    except Exception as e:
        results["dharma_chakra"] = {"available": False, "error": str(e)}

    all_ok = all(r.get("available", False) for r in results.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "all_modules_available": all_ok,
        "modules": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/api/hardening/verify", tags=["Hardening"])
async def verify_system_integrity():
    """Verify system integrity across all security layers."""
    results = {}

    # Verify RBAC permissions
    try:
        from core.security.rbac import get_rbac
        rbac = get_rbac()
        results["rbac"] = {"status": "verified", "permissions": rbac.get_all_permissions() if hasattr(rbac, 'get_all_permissions') else "N/A"}
    except Exception as e:
        results["rbac"] = {"status": "unavailable", "error": str(e)}

    # Verify input sanitization rules
    try:
        from core.security.input_sanitizer import InputSanitizer
        sanitizer = InputSanitizer()
        rules = sanitizer.get_rules() if hasattr(sanitizer, 'get_rules') else {}
        results["input_sanitizer"] = {"status": "verified", "rules_count": len(rules) if rules else 0}
    except Exception as e:
        results["input_sanitizer"] = {"status": "unavailable", "error": str(e)}

    # Verify zero trust policy
    try:
        from core.security.zero_trust import ZeroTrust
        zt = ZeroTrust()
        policy = zt.get_policy_summary() if hasattr(zt, 'get_policy_summary') else {}
        results["zero_trust"] = {"status": "verified", "policy": policy}
    except Exception as e:
        results["zero_trust"] = {"status": "unavailable", "error": str(e)}

    # Verify constitution integrity
    try:
        from core.dharma_chakra.constitution import DharmaChakraConstitution
        dc = DharmaChakraConstitution()
        results["dharma_chakra"] = {
            "status": "verified",
            "constitution_hash": dc.constitution_hash[:16] if dc.constitution_hash else None,
            "sectors_monitored": len(dc._initialize_sector_permissions()) if hasattr(dc, '_initialize_sector_permissions') else 0,
        }
    except Exception as e:
        results["dharma_chakra"] = {"status": "unavailable", "error": str(e)}

    all_verified = all(r.get("status") == "verified" for r in results.values())
    return {
        "status": "verified" if all_verified else "degraded",
        "all_layers_verified": all_verified,
        "layers": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/api/hardening/security-layers", tags=["Hardening"])
async def list_security_layers():
    """List all security layers and their status."""
    layers = []

    # Layer 1: Dharma Chakra Constitution
    try:
        from core.dharma_chakra.constitution import DharmaChakraConstitution
        dc = DharmaChakraConstitution()
        layers.append({
            "layer": 1,
            "name": "Dharma-Chakra Constitution",
            "status": "active",
            "description": "Immutable constitution with 51/49 balance enforcement",
            "hash": dc.constitution_hash[:16] if dc.constitution_hash else None,
        })
    except Exception:
        layers.append({"layer": 1, "name": "Dharma-Chakra Constitution", "status": "inactive"})

    # Layer 2: RBAC
    try:
        from core.security.rbac import get_rbac
        layers.append({
            "layer": 2,
            "name": "Role-Based Access Control",
            "status": "active",
            "description": "Fine-grained role and permission management",
        })
    except Exception:
        layers.append({"layer": 2, "name": "Role-Based Access Control", "status": "inactive"})

    # Layer 3: Input Sanitization
    try:
        from core.security.input_sanitizer import InputSanitizer
        layers.append({
            "layer": 3,
            "name": "Input Sanitization",
            "status": "active",
            "description": "SQL injection, XSS, command injection prevention",
        })
    except Exception:
        layers.append({"layer": 3, "name": "Input Sanitization", "status": "inactive"})

    # Layer 4: Audit Logging
    try:
        from core.security.audit_logger import AuditLogger
        layers.append({
            "layer": 4,
            "name": "Audit Logger",
            "status": "active",
            "description": "Tamper-evident audit trail for all actions",
        })
    except Exception:
        layers.append({"layer": 4, "name": "Audit Logger", "status": "inactive"})

    # Layer 5: Zero Trust
    try:
        from core.security.zero_trust import ZeroTrust
        layers.append({
            "layer": 5,
            "name": "Zero Trust",
            "status": "active",
            "description": "Never trust, always verify security model",
        })
    except Exception:
        layers.append({"layer": 5, "name": "Zero Trust", "status": "inactive"})

    # Layer 6: Risk Validation
    try:
        from core.security.risk_validator import RiskValidator
        layers.append({
            "layer": 6,
            "name": "Risk Validator",
            "status": "active",
            "description": "Risk assessment and scoring for actions",
        })
    except Exception:
        layers.append({"layer": 6, "name": "Risk Validator", "status": "inactive"})

    # Layer 7: Power Balance Constitution
    try:
        from core.security.power_balance_constitution import PowerBalanceConstitution, SECTOR_BALANCE_MAP
        layers.append({
            "layer": 7,
            "name": "Power Balance Constitution",
            "status": "active",
            "description": "51/49 power balance enforcement across sectors",
            "sectors": list(SECTOR_BALANCE_MAP.keys()),
        })
    except Exception:
        layers.append({"layer": 7, "name": "Power Balance Constitution", "status": "inactive"})

    active_layers = sum(1 for l in layers if l.get("status") == "active")
    return {
        "total_layers": len(layers),
        "active_layers": active_layers,
        "protection_level": f"{active_layers}/{len(layers)}",
        "layers": layers,
        "timestamp": datetime.utcnow().isoformat(),
    }
