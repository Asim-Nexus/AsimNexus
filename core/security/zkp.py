"""
AsimNexus ZKP Module (Consolidated)
====================================
Consolidated from: zkp_privacy.py, real_zkp.py, bulletproof_zkp.py,
                    zkp_production.py, zkp_verification.py

All exports are re-exported from the primary implementation files.
"""

# Re-export from primary ZKP implementation (zkp_privacy.py - production)
from core.security.zkp_privacy import (
    ZeroKnowledgeProofSystem, get_zkp_system, reset_zkp_system,
    ZKPProtocol, ProofType, DataSensitivity,
    ZKPProof, PrivateData, VerificationRequest,
    SchnorrProver, PedersenCommitment, RangeProof,
)

# Re-export from real_zkp.py
from core.security.real_zkp import (
    RealZKPManager, ZKProof, VerificationResult,
    get_zkp_manager_real, HAS_REAL_ZKP,
)

# Re-export from bulletproof_zkp.py
from core.security.bulletproof_zkp import (
    commit, prove_knowledge, verify,
    BulletProofZKP, P, G, H,
)

# Re-export from zkp_production.py
from core.security.zkp_production import (
    ProductionZKP, ZKPProduction, get_zkp, reset_zkp,
)

# Re-export from zkp_verification.py
from core.security.zkp_verification import (
    ZKPVerifier, VerificationLevel, ZKPStatus,
    get_zkp_verifier,
)

__all__ = [
    # zkp_privacy
    "ZeroKnowledgeProofSystem", "get_zkp_system", "reset_zkp_system",
    "ZKPProtocol", "ProofType", "DataSensitivity",
    "ZKPProof", "PrivateData", "VerificationRequest",
    "SchnorrProver", "PedersenCommitment", "RangeProof",
    # real_zkp
    "RealZKPManager", "ZKProof", "VerificationResult",
    "get_zkp_manager_real", "HAS_REAL_ZKP",
    # bulletproof_zkp
    "commit", "prove_knowledge", "verify",
    "BulletProofZKP", "P", "G", "H",
    # zkp_production
    "ProductionZKP", "ZKPProduction", "get_zkp", "reset_zkp",
    # zkp_verification
    "ZKPVerifier", "VerificationLevel", "ZKPStatus",
    "get_zkp_verifier",
]
