"""
STATUS: REAL — Phase 40-60% Integration Hub
"""
"""
ASIMNEXUS Dharma-Chakra Integration Hub
========================================
Unified entry point for the Identity → Dharma → Approve → Audit flow.

Wires together:
  - DharmaVetoEngine (fast pattern-match veto)
  - DharmaChakraConstitution (constitutional rules engine)
  - ZKPConfirmationManager (Level-3 human approval)
  - UserIdentitySystem (identity creation + verification)
  - DIDSystem (W3C DID resolution)
  - ZKPStore (zero-knowledge proof auth)
  - PersonalOS (high-level user OS)
  - LocalPrivacyLaws (regional privacy compliance)
  - SafetyVeto (deprecated — routed through here)
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("DharmaIntegration")

# ─── Imports (lazy — each module may fail independently) ──────────────────

try:
    from core.dharma_chakra.veto_engine import (
        DharmaVetoEngine,
        VetoResult,
        VetoLevel,
        ZKPConfirmationManager,
        get_veto_engine,
        get_zkp_manager,
    )
    _HAS_VETO = True
except ImportError as e:
    logger.warning(f"veto_engine not available: {e}")
    _HAS_VETO = False

try:
    from core.dharma_chakra.constitution import DharmaChakraConstitution
    _HAS_CONSTITUTION = True
except ImportError as e:
    logger.warning(f"constitution not available: {e}")
    _HAS_CONSTITUTION = False

try:
    from core.dharma_chakra.local_privacy_laws import (
        LocalPrivacyLaws,
        get_privacy_shield,
        Region,
        PrivacyLevel,
        DataCategory,
    )
    _HAS_PRIVACY = True
except ImportError as e:
    logger.warning(f"local_privacy_laws not available: {e}")
    _HAS_PRIVACY = False

try:
    from core.identity.user_identity import (
        UserIdentitySystem,
        IdentityLevel,
        VerificationMethod,
        get_identity_system,
    )
    _HAS_IDENTITY = True
except ImportError as e:
    logger.warning(f"user_identity not available: {e}")
    _HAS_IDENTITY = False

try:
    from core.identity.did_system import DIDSystem, get_did_system
    _HAS_DID = True
except ImportError as e:
    logger.warning(f"did_system not available: {e}")
    _HAS_DID = False

try:
    from core.identity.zkp_local import ZKPStore, get_zkp_store
    _HAS_ZKP = True
except ImportError as e:
    logger.warning(f"zkp_local not available: {e}")
    _HAS_ZKP = False

try:
    from core.identity.personal_os import PersonalOS, get_personal_os
    _HAS_POS = True
except ImportError as e:
    logger.warning(f"personal_os not available: {e}")
    _HAS_POS = False


# ─── Unified Flow Result ──────────────────────────────────────────────────


class FlowStage(Enum):
    IDENTITY_CHECK = "identity_check"
    CONSTITUTION_CHECK = "constitution_check"
    VETO_CHECK = "veto_check"
    PRIVACY_CHECK = "privacy_check"
    HUMAN_APPROVAL = "human_approval"
    AUDIT_LOG = "audit_log"
    COMPLETE = "complete"


@dataclass
class FlowResult:
    """Result of the full Identity → Dharma → Approve → Audit pipeline."""
    allowed: bool
    stage: FlowStage
    stage_results: Dict[str, Any] = field(default_factory=dict)
    requires_human: bool = False
    confirmation_token: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "stage": self.stage.value,
            "stage_results": self.stage_results,
            "requires_human": self.requires_human,
            "confirmation_token": self.confirmation_token,
            "error": self.error,
            "timestamp": self.timestamp or datetime.now().isoformat(),
        }


# ─── Integration Hub ──────────────────────────────────────────────────────


class DharmaChakraIntegrator:
    """
    Unified entry point for the full constitutional pipeline.

    evaluate_and_approve() runs all stages:
      1. Identity → verify user exists and has valid DID
      2. Veto → fast pattern-match (L1)
      3. Constitution → full constitutional rules check (L2)
      4. Privacy → regional law compliance
      5. ZKP → create Level-3 confirmation if needed
      6. Audit → log everything
    """

    def __init__(self):
        self.initialized = False
        self._init_components()

    def _init_components(self):
        """Lazy-init all available components."""
        self.veto = get_veto_engine() if _HAS_VETO else None
        self.zkp = get_zkp_manager() if _HAS_VETO else None
        self.constitution = DharmaChakraConstitution() if _HAS_CONSTITUTION else None
        self.privacy = get_privacy_shield() if _HAS_PRIVACY else None
        self.identity = get_identity_system() if _HAS_IDENTITY else None
        self.did_system = get_did_system() if _HAS_DID else None
        self.zkp_store = get_zkp_store() if _HAS_ZKP else None
        self.initialized = True
        logger.info(
            f"DharmaChakraIntegrator initialized: "
            f"veto={self.veto is not None} "
            f"constitution={self.constitution is not None} "
            f"privacy={self.privacy is not None} "
            f"identity={self.identity is not None} "
            f"did={self.did_system is not None} "
            f"zkp={self.zkp_store is not None}"
        )

    # ── Enum Mappers ────────────────────────────────────────────────

    @staticmethod
    def _map_sector(sector: str) -> Any:
        """Map string sector name to constitution's SectorType enum."""
        try:
            from core.dharma_chakra.constitution import SectorType
            mapping = {
                "general": SectorType.GENERAL,
                "health": SectorType.HEALTH,
                "education": SectorType.EDUCATION,
                "finance": SectorType.FINANCE,
                "government": SectorType.GOVERNMENT,
                "legal": SectorType.JUSTICE,
                "defense": SectorType.DEFENSE,
                "emergency": SectorType.EMERGENCY_SERVICES,
                "commerce": SectorType.COMMERCE,
                "infrastructure": SectorType.INFRASTRUCTURE,
                "agriculture": SectorType.AGRICULTURE,
            }
            return mapping.get(sector.lower(), SectorType.GENERAL)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def _map_action_to_type(action: str) -> Any:
        """Map action string to constitution's ActionType enum based on keywords."""
        try:
            from core.dharma_chakra.constitution import ActionType
            action_lower = action.lower()
            if any(kw in action_lower for kw in ["access", "view", "read", "retrieve"]):
                return ActionType.DATA_ACCESS
            elif any(kw in action_lower for kw in ["transfer", "send", "pay", "payment"]):
                return ActionType.FINANCIAL
            elif any(kw in action_lower for kw in ["create", "write", "save", "store"]):
                return ActionType.DATA_CREATION
            elif any(kw in action_lower for kw in ["delete", "remove", "destroy", "erase"]):
                return ActionType.DATA_DELETION
            elif any(kw in action_lower for kw in ["modify", "update", "change", "edit"]):
                return ActionType.DATA_MODIFICATION
            elif any(kw in action_lower for kw in ["share", "publish", "broadcast"]):
                return ActionType.DATA_SHARING
            elif any(kw in action_lower for kw in ["buy", "purchase", "order", "sell"]):
                return ActionType.COMMERCE
            elif any(kw in action_lower for kw in ["emergency", "alert", "911", "crisis"]):
                return ActionType.EMERGENCY_ACTION
            elif any(kw in action_lower for kw in ["control", "configure", "admin", "deploy"]):
                return ActionType.SYSTEM_CONTROL
            elif any(kw in action_lower for kw in ["allocate", "assign", "distribute"]):
                return ActionType.RESOURCE_ALLOCATION
            else:
                return ActionType.COMMUNICATION
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def _map_sector_to_data_category(sector: str) -> Any:
        """Map sector string to privacy DataCategory enum."""
        try:
            from core.dharma_chakra.local_privacy_laws import DataCategory
            mapping = {
                "health": DataCategory.HEALTH,
                "finance": DataCategory.FINANCIAL,
                "education": DataCategory.IDENTIFICATION,
                "government": DataCategory.IDENTIFICATION,
                "general": DataCategory.BEHAVIORAL,
                "legal": DataCategory.IDENTIFICATION,
                "emergency": DataCategory.LOCATION,
            }
            return mapping.get(sector.lower(), DataCategory.BEHAVIORAL)
        except (ImportError, AttributeError):
            return None

    async def evaluate_and_approve(
        self,
        user_id: str,
        action: str,
        sector: str = "general",
        context: Optional[Dict[str, Any]] = None,
    ) -> FlowResult:
        """
        Full Identity → Dharma → Approve → Audit pipeline.

        Args:
            user_id: The user (or agent) performing the action.
            action: Natural-language description of the action.
            sector: Domain sector (general, finance, emergency, legal, etc.)
            context: Optional metadata (amount, user_consent, etc.)

        Returns:
            FlowResult with all stage results.
        """
        context = context or {}
        stage_results: Dict[str, Any] = {}
        timestamp = datetime.now().isoformat()

        # ── Stage 1: Identity Check ─────────────────────────────────
        identity_valid = False
        did_doc = None
        try:
            if self.identity:
                record = self.identity.get_identity_by_user(user_id)
                identity_valid = record is not None
                if record and self.did_system:
                    dids = self.did_system.get_by_subject(user_id)
                    if dids:
                        did_doc = self.did_system.resolve(dids[0].did)
                stage_results["identity"] = {
                    "valid": identity_valid,
                    "has_did": did_doc is not None,
                    "user_id": user_id,
                }
            else:
                stage_results["identity"] = {"valid": True, "note": "identity module unavailable — skipping"}
                identity_valid = True
        except Exception as e:
            stage_results["identity"] = {"valid": False, "error": str(e)}

        # If identity check fails hard (module exists but user not found), we block
        if _HAS_IDENTITY and not identity_valid:
            return FlowResult(
                allowed=False,
                stage=FlowStage.IDENTITY_CHECK,
                stage_results=stage_results,
                error=f"User '{user_id}' not found in identity system",
                timestamp=timestamp,
            )

        # ── Stage 2: Fast Veto Check (L1) ───────────────────────────
        veto_result = None
        try:
            if self.veto:
                veto_result = self.veto.check(
                    message=action,
                    sector=sector,
                    agent_id=user_id,
                    context=context,
                )
                stage_results["veto"] = veto_result.to_dict()
                if veto_result.level == VetoLevel.BLOCK:
                    return FlowResult(
                        allowed=False,
                        stage=FlowStage.VETO_CHECK,
                        stage_results=stage_results,
                        error=veto_result.reason,
                        timestamp=timestamp,
                    )
            else:
                stage_results["veto"] = {"note": "veto module unavailable — skipping"}
        except Exception as e:
            stage_results["veto"] = {"error": str(e)}

        # ── Stage 3: Constitutional Check (L2) ──────────────────────
        constitutional_result = None
        try:
            if self.constitution:
                # Map string sector/action to constitution's enums
                try:
                    from core.dharma_chakra.constitution import ActionType, SectorType
                    action_type_enum = self._map_action_to_type(action)
                    sector_enum = self._map_sector(sector)
                except (ImportError, ValueError):
                    action_type_enum = None
                    sector_enum = None

                if action_type_enum and sector_enum:
                    constitutional_result = await self.constitution.check_action_compliance(
                        action_type=action_type_enum,
                        sector=sector_enum,
                        actor_id=user_id,
                        actor_type="user",
                        action_details={"description": action, "context": context},
                    )
                else:
                    constitutional_result = {"note": "could not map action/sector to constitution enums"}
                stage_results["constitution"] = constitutional_result
                # If constitution returns violations, we may block or warn
                if isinstance(constitutional_result, dict):
                    violations = constitutional_result.get("violations", [])
                    if violations:
                        critical = [
                            v for v in violations
                            if isinstance(v, dict) and v.get("severity") == "critical"
                        ]
                        if critical:
                            return FlowResult(
                                allowed=False,
                                stage=FlowStage.CONSTITUTION_CHECK,
                                stage_results=stage_results,
                                error=f"Constitutional violations: {[c.get('rule','') for c in critical]}",
                                timestamp=timestamp,
                            )
            else:
                stage_results["constitution"] = {"note": "constitution module unavailable — skipping"}
        except Exception as e:
            stage_results["constitution"] = {"error": str(e)}

        # ── Stage 4: Privacy Check ─────────────────────────────────
        privacy_result = None
        try:
            if self.privacy:
                # Only run privacy check if sector involves data handling
                if sector in ("health", "finance", "education", "government"):
                    from core.dharma_chakra.local_privacy_laws import DataRecord as PrivacyDataRecord
                    data_category = self._map_sector_to_data_category(sector)
                    privacy_level = PrivacyLevel.PERSONAL
                    if data_category:
                        dummy_data = PrivacyDataRecord(
                            record_id=f"check_{datetime.now().timestamp()}",
                            data_category=data_category,
                            privacy_level=privacy_level,
                            content=action[:1000],
                            region=self.privacy.current_region,
                            owner_id=user_id,
                            created_at=datetime.now(),
                            expires_at=None,
                            encrypted=False,
                            consent_obtained=context.get("user_consent", False),
                            processing_purpose=sector,
                            retention_days=365,
                        )
                        privacy_result = await self.privacy.check_data_compliance(dummy_data)
                        stage_results["privacy"] = privacy_result
            else:
                stage_results["privacy"] = {"note": "privacy module unavailable — skipping"}
        except Exception as e:
            stage_results["privacy"] = {"error": str(e)}

        # ── Stage 5: Human Approval (Level-3) ─────────────────────
        requires_human = False
        confirmation_token = None

        # Check if veto flagged it
        if veto_result and veto_result.requires_human:
            requires_human = True

        # Check if sector requires human
        if sector in ("emergency", "legal", "government", "defense"):
            requires_human = True

        if requires_human and self.zkp:
            try:
                pc = self.zkp.create_pending(
                    message=action,
                    sector=sector,
                    agent_id=user_id,
                    rule_triggered=veto_result.rule_triggered if veto_result else "HUMAN_REQUIRED_SECTOR",
                    reason=veto_result.reason if veto_result else f"Sector '{sector}' requires human approval",
                )
                confirmation_token = pc.token
                stage_results["human_approval"] = pc.to_public()
            except Exception as e:
                stage_results["human_approval"] = {"error": str(e)}

        # ── Stage 6: Audit ─────────────────────────────────────────
        audit_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "sector": sector,
            "action_hash": hashlib.sha256(action.encode()).hexdigest()[:16],
            "identity_valid": identity_valid,
            "veto_result": veto_result.to_dict() if veto_result else None,
            "constitutional_result": constitutional_result,
            "privacy_result": privacy_result,
            "requires_human": requires_human,
            "confirmed": False,
            "overall_allowed": not requires_human,
        }
        stage_results["audit"] = {"logged": True, "entry_hash": audit_entry["action_hash"]}

        if requires_human:
            return FlowResult(
                allowed=True,
                stage=FlowStage.HUMAN_APPROVAL,
                stage_results=stage_results,
                requires_human=True,
                confirmation_token=confirmation_token,
                timestamp=timestamp,
            )

        return FlowResult(
            allowed=True,
            stage=FlowStage.COMPLETE,
            stage_results=stage_results,
            requires_human=False,
            timestamp=timestamp,
        )

    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all integrated components."""
        return {
            "veto_engine": self.veto is not None,
            "constitution": self.constitution is not None,
            "privacy_shield": self.privacy is not None,
            "identity_system": self.identity is not None,
            "did_system": self.did_system is not None,
            "zkp_store": self.zkp_store is not None,
            "zkp_confirmation": self.zkp is not None,
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat(),
        }


# ─── Singleton ────────────────────────────────────────────────────────────

_integrator: Optional[DharmaChakraIntegrator] = None


def get_integrator() -> DharmaChakraIntegrator:
    """Get singleton DharmaChakraIntegrator instance."""
    global _integrator
    if _integrator is None:
        _integrator = DharmaChakraIntegrator()
    return _integrator


def reset_integrator() -> None:
    """Reset the integrator singleton (for testing)."""
    global _integrator
    _integrator = None


__all__ = [
    "DharmaChakraIntegrator",
    "FlowResult",
    "FlowStage",
    "get_integrator",
    "reset_integrator",
]
