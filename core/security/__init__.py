"""
AsimNexus Security Package
==========================
Hardware-backed security modules including biometric gate, TPM binding,
ZKP privacy, HSM integration, and zero-trust architecture.

Consolidated Module Structure (Phase 11.3):
  - biometric_gate.py       ← biometric_hardware_gate.py + hardware_dna.py
  - hard_lock.py            ← hard_lock.py + hardware_hard_lock.py
  - hsm_client.py           ← Primary HSM client implementation
  - hsm_integration.py      ← Real HSM integration (production)
  - immutable_constitution.py  ← immutable_constitution.py + power_balance_constitution.py
  - security_audit.py       ← audit_log.py + audit_logger.py
  - zkp.py                  ← zkp_privacy.py + real_zkp.py + bulletproof_zkp.py + zkp_production.py + zkp_verification.py
  - (standalone)            ← auth_middleware, input_sanitizer, jwt, level3_confirmation,
                               mtls, mythos_scanner, post_quantum_crypto, rbac,
                               risk_validator, tpm_binding, zero_trust, identity_manager
"""

# ── Backward-compatible re-exports for consolidated modules ──────────────

# ZKP (consolidated from 5 files → zkp.py)
from core.security.zkp import (
    # From zkp_privacy.py
    ZeroKnowledgeProofSystem, get_zkp_system, reset_zkp_system,
    ZKPProtocol, ProofType, DataSensitivity,
    ZKPProof, PrivateData, VerificationRequest,
    SchnorrProver, PedersenCommitment, RangeProof,
    # From real_zkp.py
    RealZKPManager, ZKProof, VerificationResult, get_zkp_manager_real, HAS_REAL_ZKP,
    # From bulletproof_zkp.py
    commit, prove_knowledge, verify, BulletProofZKP, P, G, H,
    # From zkp_production.py
    ProductionZKP, ZKPProduction, get_zkp, reset_zkp,
    # From zkp_verification.py
    ZKPVerifier, VerificationLevel, ZKPStatus, get_zkp_verifier,
)

# HSM (consolidated from 4 files → hsm_client.py + hsm_integration.py)
from core.security.hsm_client import HSMClient
from core.security.hsm_integration import HSMIntegration, get_hsm
from core.security.hsm_production_shim import (
    ProductionHSM,
    HSMProduction,
)

# Audit (consolidated from 2 files → security_audit.py)
from core.security.security_audit import (
    AuditLog, audit_log,
    AuditEventType, AuditSeverity,
    AuditLogger,
    AuditAction,
)

# Hard Lock (consolidated from 2 files → hard_lock.py)
from core.security.hard_lock import (
    HardLockSecurity,
    HardwareHardLock,
)

# Biometric / Hardware Auth (consolidated from 2 files → biometric_gate.py)
from core.security.biometric_gate import (
    BiometricHardwareGate, get_biometric_gate, reset_biometric_gate,
    BiometricGateState,
    HardwareDNA, get_hardware_dna, DeviceDNA,
)

# Constitution (consolidated from 2 files → immutable_constitution.py)
from core.security.immutable_constitution import (
    ImmutableConstitution, immutable_constitution,
    get_compliance_checker, check_constitution,
    ConstitutionalPrinciple, PrincipleCategory, PrincipleSeverity,
    PowerBalanceConstitution, get_power_balance, reset_power_balance,
    BalanceVerdict, SECTOR_BALANCE_MAP,
)

# Standalone modules
from core.security.auth_middleware import AuthMiddleware
from core.security.input_sanitizer import InputSanitizer
from core.security.jwt import TokenData, create_access_token, create_refresh_token
from core.security.level3_confirmation import Level3Confirmation, Level3ConfirmationSystem, get_level3_confirmation_system, reset_level3_system
from core.security.mtls import MTLSManager, get_mtls
from core.security.mythos_scanner import MythosScanner
from core.security.post_quantum_crypto import PostQuantumCrypto, get_post_quantum_crypto
from core.security.rbac import RBACManager, get_rbac_manager, get_rate_limiter
from core.security.risk_validator import RiskValidator, get_risk_validator
from core.security.tpm_binding import TPMBinding, get_tpm_binding
from core.security.zero_trust import ZeroTrustSecurity
from core.security.identity_manager import IdentityManager

# Soul Key Security Protocol
from core.security.soul_key import (
    SoulKeyProtocol, get_soul_key_protocol, reset_soul_key_protocol,
    LifeEventType, LockoutState, AttestationResult,
    LifeEvent, SoulKey, LockoutRecord,
)


# Re-export from root-level module: audit_bus.py
from core.audit_bus import (
    AUDIT_BUS_PATH,
    audit_summary,
    emit_audit,
    fetch_audit,
)



# Re-export from root-level module: security_headers_middleware.py
from core.security_headers_middleware import (
    SecurityHeadersMiddleware,
)



# Re-export from root-level module: security_layer.py
from core.security_layer import (
    HSMBridge,
    HSMService,
    ZKPBridge,
    hsm,
    zkp,
)


__all__ = [
    # ZKP
    "ZeroKnowledgeProofSystem", "get_zkp_system", "reset_zkp_system",
    "ZKPProtocol", "ProofType", "DataSensitivity",
    "ZKPProof", "PrivateData", "VerificationRequest",
    "SchnorrProver", "PedersenCommitment", "RangeProof",
    "RealZKPManager", "ZKProof", "VerificationResult", "get_zkp_manager_real", "HAS_REAL_ZKP",
    "commit", "prove_knowledge", "verify", "BulletProofZKP", "P", "G", "H",
    "ProductionZKP", "ZKPProduction", "get_zkp", "reset_zkp",
    "ZKPVerifier", "VerificationLevel", "ZKPStatus", "get_zkp_verifier",
    # HSM
    "HSMClient", "HSMIntegration", "get_hsm", "ProductionHSM", "HSMProduction",
    # Audit
    "AuditLog", "audit_log", "AuditEventType", "AuditSeverity",
    "AuditLogger", "AuditAction",
    # Hard Lock
    "HardLockSecurity", "HardwareHardLock",
    # Biometric
    "BiometricHardwareGate", "get_biometric_gate", "reset_biometric_gate",
    "BiometricGateState", "HardwareDNA", "get_hardware_dna", "DeviceDNA",
    # Constitution
    "ImmutableConstitution", "immutable_constitution", "get_compliance_checker",
    "check_constitution", "ConstitutionalPrinciple", "PrincipleCategory", "PrincipleSeverity",
    "PowerBalanceConstitution", "get_power_balance", "reset_power_balance",
    "BalanceVerdict", "SECTOR_BALANCE_MAP",
    # Standalone
    "AuthMiddleware",
    "InputSanitizer",
    "TokenData", "create_access_token", "create_refresh_token",
    "Level3Confirmation", "Level3ConfirmationSystem", "get_level3_confirmation_system", "reset_level3_system",
    "MTLSManager", "get_mtls",
    "MythosScanner",
    "PostQuantumCrypto", "get_post_quantum_crypto",
    "RBACManager", "get_rbac_manager", "get_rate_limiter",
    "RiskValidator", "get_risk_validator",
    "TPMBinding", "get_tpm_binding",
    "ZeroTrustSecurity",
    "IdentityManager",
    # Soul Key
    "SoulKeyProtocol", "get_soul_key_protocol", "reset_soul_key_protocol",
    "LifeEventType", "LockoutState", "AttestationResult",
    "LifeEvent", "SoulKey", "LockoutRecord",
]
