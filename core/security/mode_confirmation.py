#!/usr/bin/env python3
"""
Mode-Aware 3-Confirmation System
=================================

Ensures Level-1 (PIN), Level-2 (OTP/MFA), Level-3 (HSM + Biometric) confirmation
works consistently across ALL modes: Citizen, Company, Government, Hybrid.

Key Features:
  - Mode-aware confirmation routing (different modes need different confirmation levels)
  - Cross-mode confirmation (actions spanning multiple modes)
  - Escalation rules (automatic level escalation based on risk)
  - Cooling-off periods per mode
  - Integration with Nexus Connector and Enhanced Federated Identity

Confirmation Levels:
  Level-1 (PIN):        Simple PIN/password confirmation
  Level-2 (OTP/MFA):    Multi-factor authentication
  Level-3 (HSM+Bio):    Hardware Security Module + Biometric verification

Mode-Specific Rules:
  Citizen:  Level-1 for personal, Level-2 for financial, Level-3 for irreversible
  Company:  Level-2 for standard ops, Level-3 for high-value/compliance
  Government: Level-3 for ALL actions (constitutional requirement)
  Hybrid:   Highest level among active modes

Integrates with:
  - core/security/level3_confirmation.py — Existing 3-layer verification
  - core/nexus_connector.py — Mode routing and action processing
  - core/identity/enhanced_federated_identity.py — Multi-mode identity
"""

import os
import time
import json
import uuid
import hashlib
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime, timedelta

logger = logging.getLogger("AsimNexus.Security.ModeConfirmation")

# ─── Environment Configuration ────────────────────────────────────────────────
_CONFIRM_DB_PATH = os.getenv(
    "ASIM_CONFIRM_DB_PATH",
    "data/mode_confirmation.jsonl",
)
os.makedirs(os.path.dirname(_CONFIRM_DB_PATH) if os.path.dirname(_CONFIRM_DB_PATH) else ".", exist_ok=True)

# Default cooling periods per mode (in hours)
_MODE_COOLING_HOURS: Dict[str, int] = {
    "citizen": 24,      # 24 hours cooling for irreversible citizen actions
    "company": 48,      # 48 hours cooling for company actions
    "government": 72,   # 72 hours cooling for government actions (highest)
    "hybrid": 72,       # 72 hours cooling for hybrid (max of all modes)
}


class ConfirmationLevel(str, Enum):
    """The three confirmation levels."""
    LEVEL_1 = "level_1"       # PIN/password
    LEVEL_2 = "level_2"       # OTP/MFA
    LEVEL_3 = "level_3"       # HSM + Biometric


class ConfirmationStatus(str, Enum):
    """Status of a confirmation request."""
    PENDING = "pending"           # Awaiting user response
    APPROVED = "approved"         # Successfully confirmed
    REJECTED = "rejected"         # User rejected
    EXPIRED = "expired"           # Timed out
    ESCALATED = "escalated"       # Escalated to higher level
    COOLING = "cooling"           # In cooling-off period


class ActionRisk(str, Enum):
    """Risk level of an action."""
    LOW = "low"                   # Level-1 sufficient
    MEDIUM = "medium"             # Level-2 required
    HIGH = "high"                 # Level-3 required
    CRITICAL = "critical"         # Level-3 + cooling-off period


@dataclass
class ConfirmationRequest:
    """A confirmation request for an action."""
    request_id: str
    user_id: str
    mode: str                      # Citizen/Company/Government/Hybrid
    action: str                    # The action being confirmed
    action_id: str                 # Reference to the action
    level: ConfirmationLevel       # Required confirmation level
    risk: ActionRisk               # Risk assessment
    description: str               # Human-readable description
    status: ConfirmationStatus = ConfirmationStatus.PENDING
    approved_by: List[str] = field(default_factory=list)  # Who approved
    rejection_reason: str = ""
    escalation_to: Optional[ConfirmationLevel] = None
    expires_at: float = 0.0
    created_at: float = 0.0
    responded_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.expires_at:
            self.expires_at = self.created_at + 300  # 5 minute default expiry

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "mode": self.mode,
            "action": self.action,
            "action_id": self.action_id,
            "level": self.level.value if isinstance(self.level, ConfirmationLevel) else self.level,
            "risk": self.risk.value if isinstance(self.risk, ActionRisk) else self.risk,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, ConfirmationStatus) else self.status,
            "approved_by": self.approved_by,
            "rejection_reason": self.rejection_reason,
            "escalation_to": self.escalation_to.value if isinstance(self.escalation_to, ConfirmationLevel) else self.escalation_to,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "responded_at": self.responded_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfirmationRequest":
        if "level" in data and isinstance(data["level"], str):
            try:
                data["level"] = ConfirmationLevel(data["level"])
            except ValueError:
                data["level"] = ConfirmationLevel.LEVEL_1
        if "risk" in data and isinstance(data["risk"], str):
            try:
                data["risk"] = ActionRisk(data["risk"])
            except ValueError:
                data["risk"] = ActionRisk.LOW
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = ConfirmationStatus(data["status"])
            except ValueError:
                data["status"] = ConfirmationStatus.PENDING
        if "escalation_to" in data and isinstance(data["escalation_to"], str):
            try:
                data["escalation_to"] = ConfirmationLevel(data["escalation_to"])
            except ValueError:
                data["escalation_to"] = None
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CoolingPeriod:
    """A cooling-off period for an action."""
    cooling_id: str
    user_id: str
    mode: str
    action: str
    action_id: str
    reason: str
    cool_until: float              # Timestamp when cooling ends
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    @property
    def is_active(self) -> bool:
        return time.time() < self.cool_until

    @property
    def remaining_seconds(self) -> float:
        remaining = self.cool_until - time.time()
        return max(0.0, remaining)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cooling_id": self.cooling_id,
            "user_id": self.user_id,
            "mode": self.mode,
            "action": self.action,
            "action_id": self.action_id,
            "reason": self.reason,
            "cool_until": self.cool_until,
            "is_active": self.is_active,
            "remaining_seconds": self.remaining_seconds,
            "created_at": self.created_at,
        }


# ─── Mode-Specific Confirmation Rules ─────────────────────────────────────────

# Maps mode → action → required confirmation level
MODE_CONFIRMATION_RULES: Dict[str, Dict[str, ConfirmationLevel]] = {
    "citizen": {
        # Personal actions
        "identity_verify": ConfirmationLevel.LEVEL_1,
        "data_access": ConfirmationLevel.LEVEL_1,
        "profile_update": ConfirmationLevel.LEVEL_1,
        # Financial actions
        "personal_finance": ConfirmationLevel.LEVEL_2,
        "commerce": ConfirmationLevel.LEVEL_2,
        "agent_contract": ConfirmationLevel.LEVEL_2,
        # Sensitive actions
        "health_record": ConfirmationLevel.LEVEL_2,
        "education": ConfirmationLevel.LEVEL_1,
        "employment": ConfirmationLevel.LEVEL_2,
        # High-risk actions
        "license": ConfirmationLevel.LEVEL_2,
        "tax_filing": ConfirmationLevel.LEVEL_3,
        "marketplace": ConfirmationLevel.LEVEL_2,
    },
    "company": {
        # Standard operations
        "identity_verify": ConfirmationLevel.LEVEL_2,
        "data_access": ConfirmationLevel.LEVEL_2,
        "profile_update": ConfirmationLevel.LEVEL_2,
        # Commercial actions
        "commerce": ConfirmationLevel.LEVEL_2,
        "agent_contract": ConfirmationLevel.LEVEL_2,
        "marketplace": ConfirmationLevel.LEVEL_2,
        "employment": ConfirmationLevel.LEVEL_2,
        # Compliance actions
        "compliance": ConfirmationLevel.LEVEL_3,
        "license": ConfirmationLevel.LEVEL_3,
        "tax_filing": ConfirmationLevel.LEVEL_3,
        # High-value actions
        "personal_finance": ConfirmationLevel.LEVEL_3,
    },
    "government": {
        # ALL government actions require Level-3 (constitutional requirement)
        "identity_verify": ConfirmationLevel.LEVEL_3,
        "data_access": ConfirmationLevel.LEVEL_3,
        "policy": ConfirmationLevel.LEVEL_3,
        "regulation": ConfirmationLevel.LEVEL_3,
        "veto": ConfirmationLevel.LEVEL_3,
        "emergency": ConfirmationLevel.LEVEL_3,
        "constitutional": ConfirmationLevel.LEVEL_3,
        "audit": ConfirmationLevel.LEVEL_3,
        "governance": ConfirmationLevel.LEVEL_3,
        "compliance": ConfirmationLevel.LEVEL_3,
        "license": ConfirmationLevel.LEVEL_3,
        "tax_filing": ConfirmationLevel.LEVEL_3,
        "cross_consent": ConfirmationLevel.LEVEL_3,
        "dispute": ConfirmationLevel.LEVEL_3,
        "consensus": ConfirmationLevel.LEVEL_3,
    },
    "hybrid": {
        # Hybrid uses the highest level among active modes
        # This is computed dynamically, but defaults to Level-3
        "identity_verify": ConfirmationLevel.LEVEL_3,
        "data_access": ConfirmationLevel.LEVEL_3,
        "policy": ConfirmationLevel.LEVEL_3,
        "regulation": ConfirmationLevel.LEVEL_3,
        "veto": ConfirmationLevel.LEVEL_3,
        "emergency": ConfirmationLevel.LEVEL_3,
        "constitutional": ConfirmationLevel.LEVEL_3,
        "audit": ConfirmationLevel.LEVEL_3,
        "governance": ConfirmationLevel.LEVEL_3,
        "compliance": ConfirmationLevel.LEVEL_3,
        "license": ConfirmationLevel.LEVEL_3,
        "tax_filing": ConfirmationLevel.LEVEL_3,
        "cross_consent": ConfirmationLevel.LEVEL_3,
        "dispute": ConfirmationLevel.LEVEL_3,
        "consensus": ConfirmationLevel.LEVEL_3,
        "commerce": ConfirmationLevel.LEVEL_3,
        "agent_contract": ConfirmationLevel.LEVEL_3,
        "marketplace": ConfirmationLevel.LEVEL_3,
        "employment": ConfirmationLevel.LEVEL_3,
        "personal_finance": ConfirmationLevel.LEVEL_3,
        "health_record": ConfirmationLevel.LEVEL_3,
        "education": ConfirmationLevel.LEVEL_3,
    },
}

# Actions that ALWAYS require Level-3 regardless of mode
ALWAYS_LEVEL_3_ACTIONS: Set[str] = {
    "veto",
    "emergency",
    "constitutional",
    "cross_consent",
    "governance",
    "dispute",
    "consensus",
}

# Actions that require cooling-off period
COOLING_REQUIRED_ACTIONS: Set[str] = {
    "veto",
    "emergency",
    "constitutional",
    "cross_consent",
    "governance",
    "dispute",
    "tax_filing",
    "compliance",
}


class ModeConfirmationSystem:
    """
    Mode-aware 3-Confirmation system.

    Routes confirmation requests based on the user's active mode and the
    action being performed. Ensures consistent security across all modes.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Dict[str, ConfirmationRequest] = {}
        self._cooling_periods: Dict[str, CoolingPeriod] = {}
        self._user_pending: Dict[str, Set[str]] = {}  # user_id → {request_ids}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._load_from_db()

    # ─── Confirmation Request ───────────────────────────────────────────────

    def request_confirmation(
        self,
        user_id: str,
        mode: str,
        action: str,
        action_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConfirmationRequest:
        """
        Request confirmation for an action based on the user's mode.

        Automatically determines the required confirmation level based on:
        1. The user's current mode
        2. The action being performed
        3. Risk assessment of the action
        """
        # Determine required level
        level = self._determine_required_level(mode, action)

        # Determine risk
        risk = self._assess_risk(mode, action)

        # Check if cooling period is active
        cooling = self._check_cooling(user_id, mode, action)
        if cooling:
            # If cooling is active, automatically escalate to Level-3
            level = ConfirmationLevel.LEVEL_3
            risk = ActionRisk.CRITICAL

        request = ConfirmationRequest(
            request_id=f"cf_{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            mode=mode,
            action=action,
            action_id=action_id,
            level=level,
            risk=risk,
            description=description or f"Confirm {action} in {mode} mode",
            metadata=metadata or {},
        )

        with self._lock:
            self._requests[request.request_id] = request
            self._user_pending.setdefault(user_id, set()).add(request.request_id)
            self._persist_request(request)
            self._fire_callbacks("request_created", request.to_dict())

        logger.info(
            f"Confirmation requested: {request.request_id} "
            f"(User: {user_id}, Mode: {mode}, Action: {action}, Level: {level.value})"
        )
        return request

    def approve(
        self,
        request_id: str,
        user_id: str,
        verification_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Approve a confirmation request.

        verification_data should contain the proof for the required level:
          Level-1: {"pin": "****"}
          Level-2: {"otp": "******", "method": "sms/email/totp"}
          Level-3: {"hsm_signature": "...", "biometric_hash": "..."}
        """
        with self._lock:
            request = self._requests.get(request_id)
            if not request:
                return False
            if request.user_id != user_id:
                return False
            if request.status != ConfirmationStatus.PENDING:
                return False
            if request.is_expired:
                request.status = ConfirmationStatus.EXPIRED
                self._persist_request(request)
                return False

            # Verify based on level
            if not self._verify_level(request.level, verification_data or {}):
                return False

            request.status = ConfirmationStatus.APPROVED
            request.responded_at = time.time()
            request.approved_by.append(user_id)
            if verification_data:
                request.metadata["verification"] = verification_data

            # If cooling is required, create cooling period
            if request.action in COOLING_REQUIRED_ACTIONS:
                self._create_cooling_period(
                    user_id=user_id,
                    mode=request.mode,
                    action=request.action,
                    action_id=request.action_id,
                    reason=f"Post-approval cooling for {request.action}",
                )

            self._persist_request(request)
            self._fire_callbacks("request_approved", request.to_dict())

        logger.info(f"Confirmation approved: {request_id} (Level: {request.level.value})")
        return True

    def reject(
        self,
        request_id: str,
        user_id: str,
        reason: str = "",
    ) -> bool:
        """Reject a confirmation request."""
        with self._lock:
            request = self._requests.get(request_id)
            if not request or request.user_id != user_id:
                return False
            if request.status != ConfirmationStatus.PENDING:
                return False

            request.status = ConfirmationStatus.REJECTED
            request.responded_at = time.time()
            request.rejection_reason = reason
            self._persist_request(request)
            self._fire_callbacks("request_rejected", request.to_dict())

        logger.info(f"Confirmation rejected: {request_id} (Reason: {reason})")
        return True

    def escalate(
        self,
        request_id: str,
        user_id: str,
        reason: str = "",
    ) -> bool:
        """
        Escalate a confirmation to a higher level.

        Level-1 → Level-2 → Level-3
        """
        with self._lock:
            request = self._requests.get(request_id)
            if not request or request.user_id != user_id:
                return False
            if request.status != ConfirmationStatus.PENDING:
                return False

            # Determine next level
            next_level = {
                ConfirmationLevel.LEVEL_1: ConfirmationLevel.LEVEL_2,
                ConfirmationLevel.LEVEL_2: ConfirmationLevel.LEVEL_3,
                ConfirmationLevel.LEVEL_3: ConfirmationLevel.LEVEL_3,  # Already max
            }.get(request.level, ConfirmationLevel.LEVEL_3)

            if next_level == request.level:
                return False  # Already at max level

            request.level = next_level
            request.risk = ActionRisk.CRITICAL
            request.escalation_to = next_level
            request.metadata["escalation_reason"] = reason
            request.metadata["escalated_at"] = time.time()
            request.metadata["escalated_by"] = user_id
            self._persist_request(request)
            self._fire_callbacks("request_escalated", request.to_dict())

        logger.info(f"Confirmation escalated: {request_id} → {next_level.value} (Reason: {reason})")
        return True

    def get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """Get a confirmation request by ID."""
        return self._requests.get(request_id)

    def get_pending_requests(
        self,
        user_id: str,
        mode: Optional[str] = None,
    ) -> List[ConfirmationRequest]:
        """Get all pending confirmation requests for a user."""
        with self._lock:
            request_ids = self._user_pending.get(user_id, set())
            results = []
            for rid in request_ids:
                request = self._requests.get(rid)
                if request and request.status == ConfirmationStatus.PENDING:
                    if mode is None or request.mode == mode:
                        results.append(request)
            return sorted(results, key=lambda x: x.created_at, reverse=True)

    def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[ConfirmationRequest]:
        """Get confirmation history for a user."""
        with self._lock:
            results = []
            for request in self._requests.values():
                if request.user_id == user_id:
                    results.append(request)
            return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

    # ─── Cooling Period Management ──────────────────────────────────────────

    def get_active_cooling(
        self,
        user_id: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> List[CoolingPeriod]:
        """Get all active cooling periods, optionally filtered."""
        with self._lock:
            results = []
            for cooling in self._cooling_periods.values():
                if not cooling.is_active:
                    continue
                if user_id and cooling.user_id != user_id:
                    continue
                if mode and cooling.mode != mode:
                    continue
                results.append(cooling)
            return sorted(results, key=lambda x: x.cool_until)

    def get_cooling_status(self, user_id: str, mode: str, action: str) -> Optional[CoolingPeriod]:
        """Check if a specific action is in cooling-off period."""
        return self._check_cooling(user_id, mode, action)

    # ─── Internal Methods ───────────────────────────────────────────────────

    def _determine_required_level(self, mode: str, action: str) -> ConfirmationLevel:
        """Determine the required confirmation level for an action in a mode."""
        # Always Level-3 for critical actions
        if action in ALWAYS_LEVEL_3_ACTIONS:
            return ConfirmationLevel.LEVEL_3

        # Check mode-specific rules
        mode_rules = MODE_CONFIRMATION_RULES.get(mode, {})
        return mode_rules.get(action, ConfirmationLevel.LEVEL_2)  # Default Level-2

    def _assess_risk(self, mode: str, action: str) -> ActionRisk:
        """Assess the risk level of an action in a mode."""
        if action in ALWAYS_LEVEL_3_ACTIONS:
            return ActionRisk.CRITICAL

        level = self._determine_required_level(mode, action)
        risk_map = {
            ConfirmationLevel.LEVEL_1: ActionRisk.LOW,
            ConfirmationLevel.LEVEL_2: ActionRisk.MEDIUM,
            ConfirmationLevel.LEVEL_3: ActionRisk.HIGH,
        }
        risk = risk_map.get(level, ActionRisk.MEDIUM)

        # Government mode always high risk
        if mode == "government":
            return ActionRisk.HIGH

        return risk

    def _verify_level(
        self,
        level: ConfirmationLevel,
        verification_data: Dict[str, Any],
    ) -> bool:
        """
        Verify the confirmation proof for a given level.

        In production, this would integrate with:
          Level-1: Local PIN verification (hashed comparison)
          Level-2: OTP/MFA service (Twilio, Authy, TOTP)
          Level-3: HSM (Hardware Security Module) + Biometric (fingerprint/face)
        """
        if level == ConfirmationLevel.LEVEL_1:
            # PIN verification (simplified)
            return "pin" in verification_data and len(str(verification_data.get("pin", ""))) >= 4

        elif level == ConfirmationLevel.LEVEL_2:
            # OTP/MFA verification (simplified)
            return (
                "otp" in verification_data
                and len(str(verification_data.get("otp", ""))) >= 4
                and verification_data.get("method") in ("sms", "email", "totp", "authenticator")
            )

        elif level == ConfirmationLevel.LEVEL_3:
            # HSM + Biometric verification (simplified)
            return (
                "hsm_signature" in verification_data
                and "biometric_hash" in verification_data
                and len(str(verification_data.get("hsm_signature", ""))) > 10
                and len(str(verification_data.get("biometric_hash", ""))) > 10
            )

        return False

    def _check_cooling(
        self,
        user_id: str,
        mode: str,
        action: str,
    ) -> Optional[CoolingPeriod]:
        """Check if there's an active cooling period for this user/mode/action."""
        for cooling in self._cooling_periods.values():
            if (
                cooling.user_id == user_id
                and cooling.mode == mode
                and cooling.action == action
                and cooling.is_active
            ):
                return cooling
        return None

    def _create_cooling_period(
        self,
        user_id: str,
        mode: str,
        action: str,
        action_id: str,
        reason: str = "",
    ) -> CoolingPeriod:
        """Create a cooling-off period for an action."""
        cooling_hours = _MODE_COOLING_HOURS.get(mode, 48)
        cooling = CoolingPeriod(
            cooling_id=f"cool_{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            mode=mode,
            action=action,
            action_id=action_id,
            reason=reason,
            cool_until=time.time() + (cooling_hours * 3600),
        )
        self._cooling_periods[cooling.cooling_id] = cooling
        self._persist_cooling(cooling)
        logger.info(
            f"Cooling period created: {cooling.cooling_id} "
            f"(User: {user_id}, Mode: {mode}, Action: {action}, "
            f"Duration: {cooling_hours}h)"
        )
        return cooling

    def _clean_expired_cooling(self) -> int:
        """Remove expired cooling periods. Returns count removed."""
        expired = [
            cid for cid, c in self._cooling_periods.items() if not c.is_active
        ]
        for cid in expired:
            del self._cooling_periods[cid]
        return len(expired)

    def _clean_expired_requests(self) -> int:
        """Mark expired pending requests. Returns count marked."""
        count = 0
        for request in self._requests.values():
            if request.status == ConfirmationStatus.PENDING and request.is_expired:
                request.status = ConfirmationStatus.EXPIRED
                count += 1
        return count

    # ─── Callbacks ──────────────────────────────────────────────────────────

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        with self._lock:
            self._callbacks.setdefault(event, []).append(callback)

    def _fire_callbacks(self, event: str, data: Dict[str, Any]) -> None:
        """Fire callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    # ─── Persistence ────────────────────────────────────────────────────────

    def _persist_request(self, request: ConfirmationRequest) -> None:
        """Append confirmation request state to JSONL."""
        try:
            with open(_CONFIRM_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "request",
                    "data": request.to_dict(),
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist request {request.request_id}: {e}")

    def _persist_cooling(self, cooling: CoolingPeriod) -> None:
        """Append cooling period state to JSONL."""
        try:
            with open(_CONFIRM_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "cooling",
                    "data": cooling.to_dict(),
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist cooling {cooling.cooling_id}: {e}")

    def _load_from_db(self) -> None:
        """Load state from persistent storage."""
        if not os.path.exists(_CONFIRM_DB_PATH):
            return
        try:
            with open(_CONFIRM_DB_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        record_type = record.get("type")
                        data = record.get("data", {})
                        if record_type == "request":
                            request = ConfirmationRequest.from_dict(data)
                            self._requests[request.request_id] = request
                            if request.status == ConfirmationStatus.PENDING:
                                self._user_pending.setdefault(request.user_id, set()).add(request.request_id)
                        elif record_type == "cooling":
                            cooling = CoolingPeriod(**{k: v for k, v in data.items() if k in ("cooling_id", "user_id", "mode", "action", "action_id", "reason", "cool_until", "created_at")})
                            self._cooling_periods[cooling.cooling_id] = cooling
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to load confirmation state: {e}")

    # ─── Status & Stats ─────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the confirmation system."""
        with self._lock:
            self._clean_expired_requests()
            self._clean_expired_cooling()
            return {
                "system": "Mode-Aware 3-Confirmation System",
                "version": "1.0.0",
                "total_requests": len(self._requests),
                "pending_requests": sum(
                    1 for r in self._requests.values()
                    if r.status == ConfirmationStatus.PENDING
                ),
                "active_cooling": sum(
                    1 for c in self._cooling_periods.values() if c.is_active
                ),
                "db_path": _CONFIRM_DB_PATH,
                "db_exists": os.path.exists(_CONFIRM_DB_PATH),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        with self._lock:
            self._clean_expired_requests()
            self._clean_expired_cooling()

            # Status breakdown
            status_counts: Dict[str, int] = {}
            for request in self._requests.values():
                s = request.status.value if isinstance(request.status, ConfirmationStatus) else request.status
                status_counts[s] = status_counts.get(s, 0) + 1

            # Level breakdown
            level_counts: Dict[str, int] = {}
            for request in self._requests.values():
                l = request.level.value if isinstance(request.level, ConfirmationLevel) else request.level
                level_counts[l] = level_counts.get(l, 0) + 1

            # Mode breakdown
            mode_counts: Dict[str, int] = {}
            for request in self._requests.values():
                mode_counts[request.mode] = mode_counts.get(request.mode, 0) + 1

            # Risk breakdown
            risk_counts: Dict[str, int] = {}
            for request in self._requests.values():
                r = request.risk.value if isinstance(request.risk, ActionRisk) else request.risk
                risk_counts[r] = risk_counts.get(r, 0) + 1

            return {
                "requests": {
                    "total": len(self._requests),
                    "by_status": status_counts,
                    "by_level": level_counts,
                    "by_mode": mode_counts,
                    "by_risk": risk_counts,
                },
                "cooling": {
                    "active": sum(1 for c in self._cooling_periods.values() if c.is_active),
                    "total_created": len(self._cooling_periods),
                },
                "approval_rate": self._compute_approval_rate(),
            }

    def _compute_approval_rate(self) -> float:
        """Compute the overall approval rate."""
        total_responded = sum(
            1 for r in self._requests.values()
            if r.status in (ConfirmationStatus.APPROVED, ConfirmationStatus.REJECTED)
        )
        if total_responded == 0:
            return 0.0
        approved = sum(1 for r in self._requests.values() if r.status == ConfirmationStatus.APPROVED)
        return round(approved / total_responded * 100, 2)


# ─── Singleton ─────────────────────────────────────────────────────────────────

_CONFIRM_INSTANCE: Optional[ModeConfirmationSystem] = None
_CONFIRM_LOCK = threading.Lock()


def get_mode_confirmation() -> ModeConfirmationSystem:
    """Get or create the singleton ModeConfirmationSystem instance."""
    global _CONFIRM_INSTANCE
    if _CONFIRM_INSTANCE is None:
        with _CONFIRM_LOCK:
            if _CONFIRM_INSTANCE is None:
                _CONFIRM_INSTANCE = ModeConfirmationSystem()
    return _CONFIRM_INSTANCE


def reset_mode_confirmation() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _CONFIRM_INSTANCE
    with _CONFIRM_LOCK:
        _CONFIRM_INSTANCE = None
        try:
            if os.path.exists(_CONFIRM_DB_PATH):
                os.remove(_CONFIRM_DB_PATH)
        except Exception as e:
            logger.warning(f"Failed to clean confirmation DB: {e}")
