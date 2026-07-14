"""
AsimNexus Security Route Module
================================
Security, Level-3 confirmation, integration, and HSM biometric endpoints.
"""

import logging
from typing import List
from fastapi import APIRouter, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Security")

router = APIRouter(tags=["Security"])

# Module-level globals (set via init_security)
orchestrator = None


def init_security(app_globals: dict) -> None:
    """Initialize security module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── HSM Biometric ───────────────────────────────────────────────────────────


@router.post("/api/v1/security/hsm/biometric")
async def biometric_verify(data: dict = Body(...)):
    """Verify biometric via HSM"""
    try:
        from core.security.hsm import get_hsm_manager
        hsm = get_hsm_manager()
        result = hsm.verify_biometric(
            user_id=data.get("user_id"),
            biometric_data=data.get("biometric_data", {}),
            modality=data.get("modality", "fingerprint")
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"HSM biometric error: {e}")
        return error(str(e))


# ─── Level-3 Confirmation (The Power of 3) ───────────────────────────────────


@router.post("/api/confirm/level3/initiate")
async def initiate_level3(data: dict = Body(...)):
    """
    Initiate Level-3 confirmation (The Power of 3)

    1. Logical Consistency Check
    2. Dharma Alignment Check
    3. Biometric/ZKP Verify
    """
    try:
        from core.security.level3_confirmation import get_level3_confirmation_system

        l3_system = get_level3_confirmation_system()

        result = await l3_system.initiate_confirmation(
            action=data.get("action"),
            params=data.get("params", {}),
            user_id=data.get("user_id"),
            context=data.get("context", {})
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Level-3 initiate error: {e}")
        return error(str(e))


@router.post("/api/confirm/level3/biometric/request")
async def request_biometric_verification(data: dict = Body(...)):
    """Request biometric verification for pending confirmation"""
    try:
        from core.security.level3_confirmation import get_level3_confirmation_system

        l3_system = get_level3_confirmation_system()

        result = await l3_system.request_biometric(
            confirmation_id=data.get("confirmation_id"),
            method=data.get("method", "otp")
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Biometric request error: {e}")
        return error(str(e))


@router.post("/api/confirm/level3/biometric/verify")
async def verify_biometric(data: dict = Body(...)):
    """Complete biometric verification"""
    try:
        from core.security.level3_confirmation import get_level3_confirmation_system

        l3_system = get_level3_confirmation_system()

        result = await l3_system.complete_biometric(
            confirmation_id=data.get("confirmation_id"),
            verification_id=data.get("verification_id"),
            response=data.get("response")
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Biometric verify error: {e}")
        return error(str(e))


@router.get("/api/confirm/level3/status/{confirmation_id}")
async def get_confirmation_status(confirmation_id: str):
    """Get status of Level-3 confirmation"""
    try:
        from core.security.level3_confirmation import get_level3_confirmation_system

        l3_system = get_level3_confirmation_system()
        confirmation = l3_system.get_confirmation(confirmation_id)

        if not confirmation:
            return error("Confirmation not found")

        return ok(data={
            "confirmation_id": confirmation.confirmation_id,
            "action_id": confirmation.action_id,
            "user_id": confirmation.user_id,
            "overall_status": confirmation.overall_status.value,
            "logical_check": {
                "status": confirmation.logical_check.status.value,
                "score": confirmation.logical_check.score,
                "reasoning": confirmation.logical_check.reasoning
            },
            "dharma_check": {
                "status": confirmation.dharma_check.status.value,
                "score": confirmation.dharma_check.dharma_score,
                "violations": confirmation.dharma_check.violated_principles
            },
            "biometric_check": {
                "status": confirmation.biometric_check.status.value,
                "verified": confirmation.biometric_check.verified,
                "method": confirmation.biometric_check.method
            },
            "confirmed_at": confirmation.confirmed_at.isoformat() if confirmation.confirmed_at else None,
            "expires_at": confirmation.expires_at.isoformat() if confirmation.expires_at else None,
            "audit_hash": confirmation.audit_hash
        })
    except Exception as e:
        logger.error(f"Confirmation status error: {e}")
        return error(str(e))


# ─── Integration Health & Level-3 Approval ───────────────────────────────────


@router.get("/api/integration/health")
async def integration_health():
    """Health check for all integrated components."""
    try:
        from core.integration import get_integration_manager
        im = get_integration_manager()
        return ok(data=im.get_health())
    except Exception as e:
        logger.error(f"Integration health error: {e}")
        return error(str(e))


@router.post("/api/integration/evaluate")
async def integration_evaluate(data: dict = Body(...)):
    """
    Evaluate an action through the Level-3 confirmation pipeline.
    Returns whether human approval is needed.
    """
    try:
        from core.integration import get_integration_manager

        im = get_integration_manager()
        result = im.evaluate_action(
            action=data.get("action"),
            params=data.get("params", {}),
            user_id=data.get("user_id", "system"),
            context=data.get("context", {})
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Integration evaluate error: {e}")
        return error(str(e))


@router.post("/api/integration/confirm")
async def integration_confirm(data: dict = Body(...)):
    """
    Confirm (approve) a pending Level-3 action.
    Requires human-in-the-loop approval.
    """
    try:
        from core.integration import get_integration_manager

        im = get_integration_manager()
        result = im.confirm_action(
            confirmation_id=data.get("confirmation_id"),
            user_id=data.get("user_id", "admin"),
            notes=data.get("notes", "")
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Integration confirm error: {e}")
        return error(str(e))


@router.post("/api/integration/reject")
async def integration_reject(data: dict = Body(...)):
    """
    Reject a pending Level-3 action.
    Human-in-the-loop rejection with reason.
    """
    try:
        from core.integration import get_integration_manager

        im = get_integration_manager()
        result = im.reject_action(
            confirmation_id=data.get("confirmation_id"),
            user_id=data.get("user_id", "admin"),
            reason=data.get("reason", "Rejected by human operator")
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Integration reject error: {e}")
        return error(str(e))


@router.get("/api/integration/pending")
async def integration_pending():
    """List all pending Level-3 human approvals."""
    try:
        from core.integration import get_integration_manager
        im = get_integration_manager()
        pending = im.get_pending_approvals()
        return ok(data={
            "pending_count": len(pending),
            "pending_approvals": pending
        })
    except Exception as e:
        logger.error(f"Integration pending error: {e}")
        return error(str(e))


@router.get("/api/integration/veto-stats")
async def integration_veto_stats():
    """Get veto engine statistics."""
    try:
        from core.integration import get_integration_manager
        im = get_integration_manager()
        return ok(data=im.get_veto_stats())
    except Exception as e:
        logger.error(f"Veto stats error: {e}")
        return error(str(e))


@router.get("/api/integration/audit-log")
async def integration_audit_log(limit: int = 20):
    """Get the last N entries from the immutable audit log."""
    try:
        from core.integration import get_integration_manager
        im = get_integration_manager()
        log = im.get_audit_log(limit=limit)
        return ok(data={
            "entries": log,
            "count": len(log)
        })
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        return error(str(e))


# ─── Compliance ──────────────────────────────────────────────────────────────


@router.get("/api/compliance/gov-standards")
async def gov_standards():
    """Get government compliance standards"""
    try:
        from core.compliance import get_compliance_engine
        engine = get_compliance_engine()
        return ok(data=engine.get_gov_standards())
    except Exception as e:
        logger.error(f"Gov standards error: {e}")
        return error(str(e))


@router.get("/api/compliance/security")
async def security_compliance():
    """Get security compliance status"""
    try:
        from core.compliance import get_compliance_engine
        engine = get_compliance_engine()
        return ok(data=engine.get_security_status())
    except Exception as e:
        logger.error(f"Security compliance error: {e}")
        return error(str(e))


@router.get("/api/compliance/vapt-status")
async def vapt_status():
    """Get VAPT security audit status"""
    try:
        from core.compliance.vapt_process import VAPTProcess
        vapt = VAPTProcess()
        return ok(data=vapt.run_security_check())
    except Exception as e:
        logger.error(f"VAPT status error: {e}")
        return error(str(e))


# ─── Disaster Recovery ───────────────────────────────────────────────────────────

@router.post("/api/disaster-recovery/backup")
async def create_backup():
    """Create a backup of critical data."""
    try:
        from core.disaster_recovery import get_disaster_recovery_manager
        drm = get_disaster_recovery_manager()
        result = drm.create_backup()
        return ok(data=result)
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return error(str(e))


@router.get("/api/disaster-recovery/backups")
async def list_backups():
    """List all available backups."""
    try:
        from core.disaster_recovery import get_disaster_recovery_manager
        drm = get_disaster_recovery_manager()
        backups = drm.list_backups()
        return ok(data=backups)
    except Exception as e:
        logger.error(f"List backups error: {e}")
        return error(str(e))


@router.post("/api/disaster-recovery/restore")
async def restore_backup(backup_name: str = Body(..., embed=True)):
    """Restore from a backup."""
    try:
        from core.disaster_recovery import get_disaster_recovery_manager
        drm = get_disaster_recovery_manager()
        result = drm.restore_backup(backup_name)
        return ok(data=result)
    except Exception as e:
        logger.error(f"Restore error: {e}")
        return error(str(e))


# ─── DePIN Bridge ──────────────────────────────────────────────────────────────

@router.post("/api/depin/register")
async def depin_register(node_id: str = Body(..., embed=True),
                          capabilities: List[str] = Body(default=[], embed=True)):
    """Register a DePIN node."""
    try:
        from core.depin_bridge import get_depin_bridge
        bridge = get_depin_bridge()
        result = await bridge.register_node(node_id, capabilities)
        return ok(data=result)
    except Exception as e:
        logger.error(f"DePIN register error: {e}")
        return error(str(e))


@router.get("/api/depin/stats")
async def depin_stats():
    """Get DePIN network statistics."""
    try:
        from core.depin_bridge import get_depin_bridge
        bridge = get_depin_bridge()
        return ok(data=bridge.get_stats())
    except Exception as e:
        logger.error(f"DePIN stats error: {e}")
        return error(str(e))


# ─── Blockchain Constitution ───────────────────────────────────────────────────

@router.get("/api/constitution/status")
async def constitution_status():
    """Get blockchain constitution anchor status."""
    try:
        from core.governance.blockchain_constitution_anchor import get_constitution_anchor
        anchor = get_constitution_anchor()
        return ok(data=anchor.get_status())
    except Exception as e:
        logger.error(f"Constitution status error: {e}")
        return error(str(e))


# ─── Phase 4 — TPM Hardware Key Status ────────────────────────────────────────


@router.get("/api/security/tpm/status")
async def tpm_status():
    """Get TPM 2.0 hardware security module status (Phase 4)."""
    try:
        from core.security.tpm_binding import get_tpm_binding
        tpm = get_tpm_binding()
        status = tpm.get_status()
        return ok(data={
            "tpm_initialized": status.get("initialized", False),
            "provider": status.get("provider", "unknown"),
            "key_count": status.get("key_count", 0),
            "constitution_anchored": status.get("constitution_anchored", False),
            "phase": "Phase 4 — Apple Secure Enclave Pattern",
        })
    except Exception as e:
        logger.error(f"TPM status error: {e}")
        return error(str(e))


@router.get("/api/security/tpm/keys")
async def tpm_keys():
    """List all TPM-bound hardware keys (Phase 4)."""
    try:
        from core.security.tpm_binding import get_tpm_binding
        tpm = get_tpm_binding()
        keys = tpm.list_keys()
        return ok(data={
            "keys": [k.to_dict() for k in keys],
            "count": len(keys),
        })
    except Exception as e:
        logger.error(f"TPM keys error: {e}")
        return error(str(e))


@router.post("/api/security/tpm/key/generate")
async def tpm_generate_key(data: dict = Body(...)):
    """Generate a new TPM-bound hardware key (Phase 4)."""
    try:
        from core.security.tpm_binding import get_tpm_binding, KeyType
        tpm = get_tpm_binding()
        key_type_str = data.get("key_type", "SIGNING")
        key_type = KeyType(key_type_str) if hasattr(KeyType, key_type_str) else KeyType.SIGNING
        key = tpm.generate_key(
            key_type=key_type,
            key_id=data.get("key_id"),
            metadata=data.get("metadata", {}),
        )
        return ok(data=key.to_dict())
    except Exception as e:
        logger.error(f"TPM generate key error: {e}")
        return error(str(e))


# ─── Phase 4 — Level-3 with TPM Hardware Key ──────────────────────────────────


@router.post("/api/confirm/level3/tpm/verify")
async def level3_tpm_verify(data: dict = Body(...)):
    """
    Phase 4 — Apple Secure Enclave Pattern Verification.
    
    Uses TPM 2.0 LEVEL3_APPROVAL signing key for hardware-backed
    cryptographic challenge-response. Biometric match required
    before the TPM chip signs the challenge.
    """
    try:
        from core.security.level3_confirmation import get_level3_confirmation_system
        l3_system = get_level3_confirmation_system()
        verifier = l3_system.biometric_verifier

        result = await verifier.verify_with_tpm_hardware_key(
            user_id=data.get("user_id"),
            action_id=data.get("action_id"),
            challenge=data.get("challenge"),
        )

        return ok(data={
            "status": result.status.value,
            "verified": result.verified,
            "method": result.method,
            "zkp_proof": result.zkp_proof,
            "hardware_bound": True,
            "phase": "Phase 4 — Apple Secure Enclave Pattern",
        })
    except Exception as e:
        logger.error(f"Level-3 TPM verify error: {e}")
        return error(str(e))


@router.get("/api/confirm/level3/tpm/key-status")
async def level3_tpm_key_status():
    """Get Level-3 TPM hardware key status (Phase 4)."""
    try:
        from core.security.level3_confirmation import get_level3_confirmation_system
        l3_system = get_level3_confirmation_system()
        verifier = l3_system.biometric_verifier

        tpm_available = verifier._tpm is not None
        key_id = verifier._level3_key_id

        return ok(data={
            "tpm_available": tpm_available,
            "level3_key_id": key_id,
            "hardware_bound": tpm_available and key_id is not None,
            "pattern": "Apple Secure Enclave — biometric match required before TPM signs",
            "phase": "Phase 4",
        })
    except Exception as e:
        logger.error(f"Level-3 TPM key status error: {e}")
        return error(str(e))
