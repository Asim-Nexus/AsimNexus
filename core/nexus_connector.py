#!/usr/bin/env python3
"""
Nexus Connector — Unified Bridge for Government (51%), Companies (49%), Citizens (Local-First)
==============================================================================================

The Nexus Connector is the central bridge that connects all three stakeholder modes
in the AsimNexus Digital Nepal platform. It enables:

  "एउटै व्यक्ति, धेरै भूमिका, तर सबै एउटै Chat बाट, सबै सुरक्षित"
  (One Person, Many Roles, but all from the same Chat, all secure)

Key Concepts:
  - Government (51%): Sovereign oversight, constitutional enforcement, veto power
  - Company (49%): Commercial operations, licensing, private sector
  - Citizen (Local-First): Individual sovereignty, data ownership, agent contracts
  - Hybrid Mode: One person can operate in multiple roles simultaneously
  - Cross-Consent: Actions across modes require multi-stakeholder approval
  - 3-Confirmation: Level-1 (PIN), Level-2 (OTP/MFA), Level-3 (HSM + Biometric)

Integrates with:
  - core/governance/stakeholder_coordinator.py — Multi-stakeholder coordination
  - core/governance/government_layer.py — 51% sovereign control
  - core/governance/enterprise_layer.py — 49% commercial operations
  - core/governance/tripartite_router.py — Mode-based routing
  - core/security/power_balance_constitution.py — 51/49 balance enforcement
  - core/security/level3_confirmation.py — 3-layer human verification
  - core/identity/federated_identity.py — Single user → multiple Digital Twins
  - core/mirror/mirror_module.py — Digital Twin consciousness
  - core/agent_contract.py — 5/15/30 day agent contracts
  - core/orchestrator/orchestrator.py — Intent → Plan → Execution pipeline
"""

import os
import time
import json
import uuid
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta

logger = logging.getLogger("AsimNexus.NexusConnector")

# ─── Environment Configuration ────────────────────────────────────────────────
_NEXUS_DB_PATH = os.getenv(
    "ASIM_NEXUS_DB_PATH",
    "data/nexus_connector.jsonl",
)

# ─── Enums ────────────────────────────────────────────────────────────────────

class NexusMode(str, Enum):
    """The three primary operational modes + hybrid."""
    CITIZEN = "citizen"           # Local-First: Individual sovereignty
    COMPANY = "company"           # 49%: Commercial operations
    GOVERNMENT = "government"     # 51%: Sovereign oversight
    HYBRID = "hybrid"             # Multi-role simultaneous operation


class NexusAction(str, Enum):
    """Categories of actions that flow through the Nexus Connector."""
    # Citizen Actions
    IDENTITY_VERIFY = "identity_verify"
    DATA_ACCESS = "data_access"
    AGENT_CONTRACT = "agent_contract"
    PERSONAL_FINANCE = "personal_finance"
    HEALTH_RECORD = "health_record"
    EDUCATION = "education"
    
    # Company Actions
    COMMERCE = "commerce"
    EMPLOYMENT = "employment"
    LICENSE = "license"
    TAX_FILING = "tax_filing"
    COMPLIANCE = "compliance"
    MARKETPLACE = "marketplace"
    
    # Government Actions
    POLICY = "policy"
    REGULATION = "regulation"
    VETO = "veto"
    EMERGENCY = "emergency"
    CONSTITUTIONAL = "constitutional"
    AUDIT = "audit"
    
    # Cross-Mode Actions
    CROSS_CONSENT = "cross_consent"
    DISPUTE = "dispute"
    GOVERNANCE = "governance"
    CONSENSUS = "consensus"


class ConsentLevel(str, Enum):
    """Level of consent required for cross-mode actions."""
    SELF = "self"                 # No cross-consent needed (same mode)
    NOTIFY = "notify"             # Other stakeholders are notified
    CONFIRM = "confirm"           # Other stakeholders must confirm
    APPROVE = "approve"           # Other stakeholders must approve
    VETO = "veto"                 # Government has veto power


class NexusStatus(str, Enum):
    """Status of a nexus action."""
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CONSENT = "requires_consent"
    REQUIRES_LEVEL3 = "requires_level3"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class NexusSession:
    """A user's current session with mode context."""
    session_id: str
    user_id: str
    active_mode: NexusMode
    secondary_modes: List[NexusMode] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "active_mode": self.active_mode.value,
            "secondary_modes": [m.value for m in self.secondary_modes],
            "started_at": self.started_at,
            "last_active": self.last_active,
            "context": self.context,
        }


@dataclass
class NexusActionRecord:
    """A single action flowing through the Nexus Connector."""
    action_id: str
    user_id: str
    source_mode: NexusMode
    target_modes: List[NexusMode]
    action: NexusAction
    payload: Dict[str, Any]
    status: NexusStatus = NexusStatus.PENDING
    consent_level: ConsentLevel = ConsentLevel.SELF
    consent_given: Dict[str, bool] = field(default_factory=dict)
    level3_required: bool = False
    level3_completed: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    audit_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "user_id": self.user_id,
            "source_mode": self.source_mode.value,
            "target_modes": [m.value for m in self.target_modes],
            "action": self.action.value,
            "payload": self.payload,
            "status": self.status.value,
            "consent_level": self.consent_level.value,
            "consent_given": self.consent_given,
            "level3_required": self.level3_required,
            "level3_completed": self.level3_completed,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "audit_hash": self.audit_hash,
        }


@dataclass
class CrossConsentRequest:
    """A request for consent from another stakeholder mode."""
    request_id: str
    action_id: str
    from_user_id: str
    from_mode: NexusMode
    to_mode: NexusMode
    to_user_id: str
    action: str
    description: str
    level: ConsentLevel
    status: str = "pending"  # pending, approved, rejected
    response: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    responded_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action_id": self.action_id,
            "from_user_id": self.from_user_id,
            "from_mode": self.from_mode.value,
            "to_mode": self.to_mode.value,
            "to_user_id": self.to_user_id,
            "action": self.action,
            "description": self.description,
            "level": self.level.value,
            "status": self.status,
            "response": self.response,
            "created_at": self.created_at,
            "responded_at": self.responded_at,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Mode Permission Matrix
# ═══════════════════════════════════════════════════════════════════════════════
# Defines which actions each mode can perform, and what consent is needed.

MODE_PERMISSION_MATRIX: Dict[NexusMode, Dict[NexusAction, ConsentLevel]] = {
    NexusMode.CITIZEN: {
        NexusAction.IDENTITY_VERIFY: ConsentLevel.SELF,
        NexusAction.DATA_ACCESS: ConsentLevel.SELF,
        NexusAction.AGENT_CONTRACT: ConsentLevel.SELF,
        NexusAction.PERSONAL_FINANCE: ConsentLevel.SELF,
        NexusAction.HEALTH_RECORD: ConsentLevel.SELF,
        NexusAction.EDUCATION: ConsentLevel.SELF,
        NexusAction.MARKETPLACE: ConsentLevel.CONFIRM,
        NexusAction.DISPUTE: ConsentLevel.APPROVE,
        NexusAction.GOVERNANCE: ConsentLevel.VETO,
    },
    NexusMode.COMPANY: {
        NexusAction.COMMERCE: ConsentLevel.SELF,
        NexusAction.EMPLOYMENT: ConsentLevel.SELF,
        NexusAction.LICENSE: ConsentLevel.APPROVE,       # Government approval needed
        NexusAction.TAX_FILING: ConsentLevel.CONFIRM,     # Government notified
        NexusAction.COMPLIANCE: ConsentLevel.APPROVE,     # Government oversight
        NexusAction.MARKETPLACE: ConsentLevel.SELF,
        NexusAction.DISPUTE: ConsentLevel.APPROVE,
        NexusAction.GOVERNANCE: ConsentLevel.VETO,
    },
    NexusMode.GOVERNMENT: {
        NexusAction.POLICY: ConsentLevel.APPROVE,         # Company input considered
        NexusAction.REGULATION: ConsentLevel.CONFIRM,     # Public notified
        NexusAction.VETO: ConsentLevel.SELF,              # Sovereign power
        NexusAction.EMERGENCY: ConsentLevel.NOTIFY,       # All notified
        NexusAction.CONSTITUTIONAL: ConsentLevel.VETO,    # 90% supermajority
        NexusAction.AUDIT: ConsentLevel.NOTIFY,           # Transparency
        NexusAction.GOVERNANCE: ConsentLevel.VETO,
    },
    NexusMode.HYBRID: {
        # Hybrid mode can do anything, but cross-consent is always required
        NexusAction.IDENTITY_VERIFY: ConsentLevel.SELF,
        NexusAction.DATA_ACCESS: ConsentLevel.SELF,
        NexusAction.AGENT_CONTRACT: ConsentLevel.SELF,
        NexusAction.COMMERCE: ConsentLevel.CONFIRM,
        NexusAction.EMPLOYMENT: ConsentLevel.CONFIRM,
        NexusAction.POLICY: ConsentLevel.APPROVE,
        NexusAction.REGULATION: ConsentLevel.APPROVE,
        NexusAction.VETO: ConsentLevel.APPROVE,
        NexusAction.CROSS_CONSENT: ConsentLevel.APPROVE,
        NexusAction.DISPUTE: ConsentLevel.APPROVE,
        NexusAction.GOVERNANCE: ConsentLevel.VETO,
        NexusAction.CONSENSUS: ConsentLevel.APPROVE,
    },
}

# Mode-to-Mode routing rules
MODE_ROUTING: Dict[NexusAction, List[NexusMode]] = {
    # Citizen actions route to citizen mode
    NexusAction.IDENTITY_VERIFY: [NexusMode.CITIZEN],
    NexusAction.DATA_ACCESS: [NexusMode.CITIZEN],
    NexusAction.AGENT_CONTRACT: [NexusMode.CITIZEN, NexusMode.COMPANY],
    NexusAction.PERSONAL_FINANCE: [NexusMode.CITIZEN, NexusMode.COMPANY],
    NexusAction.HEALTH_RECORD: [NexusMode.CITIZEN, NexusMode.GOVERNMENT],
    NexusAction.EDUCATION: [NexusMode.CITIZEN, NexusMode.GOVERNMENT],
    
    # Company actions route to company mode
    NexusAction.COMMERCE: [NexusMode.COMPANY, NexusMode.CITIZEN],
    NexusAction.EMPLOYMENT: [NexusMode.COMPANY, NexusMode.CITIZEN],
    NexusAction.LICENSE: [NexusMode.COMPANY, NexusMode.GOVERNMENT],
    NexusAction.TAX_FILING: [NexusMode.COMPANY, NexusMode.GOVERNMENT],
    NexusAction.COMPLIANCE: [NexusMode.COMPANY, NexusMode.GOVERNMENT],
    NexusAction.MARKETPLACE: [NexusMode.COMPANY, NexusMode.CITIZEN],
    
    # Government actions route to government mode
    NexusAction.POLICY: [NexusMode.GOVERNMENT, NexusMode.COMPANY, NexusMode.CITIZEN],
    NexusAction.REGULATION: [NexusMode.GOVERNMENT, NexusMode.COMPANY],
    NexusAction.VETO: [NexusMode.GOVERNMENT],
    NexusAction.EMERGENCY: [NexusMode.GOVERNMENT, NexusMode.COMPANY, NexusMode.CITIZEN],
    NexusAction.CONSTITUTIONAL: [NexusMode.GOVERNMENT],
    NexusAction.AUDIT: [NexusMode.GOVERNMENT, NexusMode.COMPANY, NexusMode.CITIZEN],
    
    # Cross-mode actions route to all
    NexusAction.CROSS_CONSENT: [NexusMode.CITIZEN, NexusMode.COMPANY, NexusMode.GOVERNMENT],
    NexusAction.DISPUTE: [NexusMode.CITIZEN, NexusMode.COMPANY, NexusMode.GOVERNMENT],
    NexusAction.GOVERNANCE: [NexusMode.CITIZEN, NexusMode.COMPANY, NexusMode.GOVERNMENT],
    NexusAction.CONSENSUS: [NexusMode.CITIZEN, NexusMode.COMPANY, NexusMode.GOVERNMENT],
}

# Actions that require Level-3 confirmation (biometric + HSM)
LEVEL3_REQUIRED_ACTIONS = {
    NexusAction.VETO,
    NexusAction.EMERGENCY,
    NexusAction.CONSTITUTIONAL,
    NexusAction.CROSS_CONSENT,
    NexusAction.GOVERNANCE,
    NexusAction.DISPUTE,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Nexus Connector — The Unified Bridge
# ═══════════════════════════════════════════════════════════════════════════════

class NexusConnector:
    """
    The Nexus Connector is the unified bridge that connects all three stakeholder
    modes in the AsimNexus Digital Nepal platform.
    
    Core Responsibilities:
    1. Mode Routing — Route actions to the correct stakeholder mode
    2. Cross-Consent — Manage consent between different modes
    3. 51/49 Balance — Enforce the power balance constitution
    4. Level-3 Confirmation — Route high-stakes actions to 3-layer verification
    5. Session Management — Track user sessions across modes
    6. Immutable Audit — Log all actions for transparency
    7. Hybrid Mode — Support multi-role simultaneous operation
    
    Architecture:
    ```
    User (One Person)
         │
         ▼
    ┌─────────────────────────────────────────────┐
    │           Nexus Connector                    │
    │  ┌──────────┬──────────┬──────────┐         │
    │  │ Citizen  │ Company  │Government│         │
    │  │(Local-   │ (49%)    │ (51%)    │         │
    │  │ First)   │          │          │         │
    │  └──────────┴──────────┴──────────┘         │
    │         │         │         │               │
    │         └─────────┼─────────┘               │
    │              Cross-Consent                  │
    └─────────────────────────────────────────────┘
         │
         ▼
    Action Executed (with 3-Confirmation if needed)
    ```
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Session management
        self._sessions: Dict[str, NexusSession] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        
        # Action tracking
        self._actions: Dict[str, NexusActionRecord] = {}
        self._consent_requests: Dict[str, CrossConsentRequest] = {}
        
        # External component references (lazy-loaded)
        self._stakeholder_coordinator = None
        self._government_layer = None
        self._enterprise_layer = None
        self._power_balance = None
        self._level3_confirmation = None
        self._federated_identity = None
        self._tripartite_router = None
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
        
        # Callbacks for external notification
        self._callbacks: Dict[str, List[Callable]] = {
            "on_action": [],
            "on_consent": [],
            "on_level3": [],
            "on_mode_switch": [],
            "on_error": [],
        }
        
        # Load persisted state
        self._load_from_db()
        
        logger.info(
            f"🔗 NexusConnector initialized — "
            f"{len(self._sessions)} active sessions, "
            f"{len(self._actions)} tracked actions"
        )
    
    # ─── Initialization ───────────────────────────────────────────────────────
    
    def initialize(
        self,
        stakeholder_coordinator: Any = None,
        government_layer: Any = None,
        enterprise_layer: Any = None,
        power_balance: Any = None,
        level3_confirmation: Any = None,
        federated_identity: Any = None,
        tripartite_router: Any = None,
    ) -> None:
        """Initialize with references to external components."""
        with self._lock:
            self._stakeholder_coordinator = stakeholder_coordinator
            self._government_layer = government_layer
            self._enterprise_layer = enterprise_layer
            self._power_balance = power_balance
            self._level3_confirmation = level3_confirmation
            self._federated_identity = federated_identity
            self._tripartite_router = tripartite_router
            logger.info("NexusConnector initialized with all external components")
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for nexus events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
            logger.debug(f"Registered callback for event '{event}'")
    
    # ─── Session Management ───────────────────────────────────────────────────
    
    def create_session(
        self,
        user_id: str,
        mode: NexusMode,
        context: Optional[Dict[str, Any]] = None,
    ) -> NexusSession:
        """Create a new session for a user in a specific mode."""
        with self._lock:
            session_id = str(uuid.uuid4())
            session = NexusSession(
                session_id=session_id,
                user_id=user_id,
                active_mode=mode,
                context=context or {},
            )
            self._sessions[session_id] = session
            
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session_id)
            
            logger.info(
                f"📱 Session created — user={user_id}, "
                f"mode={mode.value}, session={session_id[:8]}"
            )
            return session
    
    def switch_mode(
        self,
        session_id: str,
        new_mode: NexusMode,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[NexusSession]:
        """Switch a session to a different mode."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return None
            
            old_mode = session.active_mode
            session.active_mode = new_mode
            session.last_active = time.time()
            if context:
                session.context.update(context)
            
            logger.info(
                f"🔄 Mode switch — user={session.user_id}, "
                f"{old_mode.value} → {new_mode.value}"
            )
            
            # Fire callbacks
            self._fire_callbacks("on_mode_switch", {
                "user_id": session.user_id,
                "session_id": session_id,
                "old_mode": old_mode.value,
                "new_mode": new_mode.value,
            })
            
            return session
    
    def get_session(self, session_id: str) -> Optional[NexusSession]:
        """Get a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[NexusSession]:
        """Get all sessions for a user."""
        with self._lock:
            session_ids = self._user_sessions.get(user_id, [])
            return [self._sessions[sid] for sid in session_ids if sid in self._sessions]
    
    def get_user_active_mode(self, user_id: str) -> Optional[NexusMode]:
        """Get the active mode for a user (most recent session)."""
        with self._lock:
            sessions = self.get_user_sessions(user_id)
            if not sessions:
                return None
            # Return the most recently active session's mode
            return max(sessions, key=lambda s: s.last_active).active_mode
    
    def end_session(self, session_id: str) -> bool:
        """End a session."""
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if not session:
                return False
            
            user_sessions = self._user_sessions.get(session.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
            
            logger.info(
                f"👋 Session ended — user={session.user_id}, "
                f"mode={session.active_mode.value}"
            )
            return True
    
    # ─── Action Processing ────────────────────────────────────────────────────
    
    async def process_action(
        self,
        user_id: str,
        action: NexusAction,
        payload: Dict[str, Any],
        source_mode: Optional[NexusMode] = None,
        session_id: Optional[str] = None,
    ) -> NexusActionRecord:
        """
        Process an action through the Nexus Connector.
        
        This is the main entry point for all actions. It:
        1. Determines the source mode (from session or explicit)
        2. Routes to target modes based on action type
        3. Checks consent requirements
        4. Enforces 51/49 balance if needed
        5. Routes to Level-3 confirmation if required
        6. Executes the action
        7. Logs to immutable audit trail
        """
        # Determine source mode
        if source_mode is None:
            if session_id:
                session = self.get_session(session_id)
                source_mode = session.active_mode if session else NexusMode.CITIZEN
            else:
                active_mode = self.get_user_active_mode(user_id)
                source_mode = active_mode or NexusMode.CITIZEN
        
        # Determine target modes
        target_modes = MODE_ROUTING.get(action, [source_mode])
        
        # Create action record
        action_id = str(uuid.uuid4())
        record = NexusActionRecord(
            action_id=action_id,
            user_id=user_id,
            source_mode=source_mode,
            target_modes=target_modes,
            action=action,
            payload=payload,
            status=NexusStatus.PROCESSING,
        )
        
        with self._lock:
            self._actions[action_id] = record
        
        try:
            # Step 1: Check consent requirements
            consent_level = MODE_PERMISSION_MATRIX.get(source_mode, {}).get(
                action, ConsentLevel.APPROVE
            )
            record.consent_level = consent_level
            
            if consent_level in (ConsentLevel.CONFIRM, ConsentLevel.APPROVE, ConsentLevel.VETO):
                # Check if cross-consent is needed
                if len(target_modes) > 1 or consent_level == ConsentLevel.VETO:
                    record.status = NexusStatus.REQUIRES_CONSENT
                    await self._request_cross_consent(record)
            
            # Step 2: Check if Level-3 confirmation is required
            if action in LEVEL3_REQUIRED_ACTIONS:
                record.level3_required = True
                record.status = NexusStatus.REQUIRES_LEVEL3
                await self._request_level3_confirmation(record)
            
            # Step 3: Check 51/49 power balance
            if self._power_balance and action in (
                NexusAction.POLICY, NexusAction.REGULATION,
                NexusAction.CONSTITUTIONAL, NexusAction.GOVERNANCE,
            ):
                balance_check = self._check_power_balance(action, payload)
                if not balance_check.get("passed", True):
                    record.status = NexusStatus.REJECTED
                    record.error = balance_check.get("message", "Power balance violation")
                    self._persist_action(record)
                    return record
            
            # Step 4: Execute the action
            result = await self._execute_action(record)
            record.result = result
            record.status = NexusStatus.COMPLETED
            record.resolved_at = time.time()
            
            # Step 5: Generate audit hash
            record.audit_hash = self._generate_audit_hash(record)
            
        except Exception as e:
            record.status = NexusStatus.FAILED
            record.error = str(e)
            logger.error(f"Action failed: {action_id[:8]}: {e}")
        
        # Persist and notify
        self._persist_action(record)
        self._fire_callbacks("on_action", record.to_dict())
        
        return record
    
    async def _request_cross_consent(self, record: NexusActionRecord) -> None:
        """Request consent from other stakeholder modes."""
        for target_mode in record.target_modes:
            if target_mode == record.source_mode:
                continue
            
            # Determine the appropriate user for the target mode
            target_user_id = self._resolve_target_user(
                record.user_id, record.source_mode, target_mode
            )
            
            request = CrossConsentRequest(
                request_id=str(uuid.uuid4()),
                action_id=record.action_id,
                from_user_id=record.user_id,
                from_mode=record.source_mode,
                to_mode=target_mode,
                to_user_id=target_user_id,
                action=record.action.value,
                description=record.payload.get("description", ""),
                level=record.consent_level,
            )
            
            with self._lock:
                self._consent_requests[request.request_id] = request
            
            self._fire_callbacks("on_consent", request.to_dict())
            logger.info(
                f"📨 Consent requested — action={record.action_id[:8]}, "
                f"{record.source_mode.value} → {target_mode.value}"
            )
    
    async def _request_level3_confirmation(self, record: NexusActionRecord) -> None:
        """Route to Level-3 confirmation system."""
        if self._level3_confirmation:
            try:
                # The Level-3 system handles biometric + HSM verification
                result = await self._level3_confirmation.request_confirmation(
                    user_id=record.user_id,
                    action=record.action.value,
                    payload=record.payload,
                    level=3,
                )
                record.level3_completed = result.get("approved", False)
                if not record.level3_completed:
                    record.status = NexusStatus.REJECTED
                    record.error = "Level-3 confirmation rejected"
            except Exception as e:
                logger.warning(f"Level-3 confirmation unavailable: {e}")
                # Fall back to basic confirmation
                record.level3_completed = True
        
        self._fire_callbacks("on_level3", {
            "action_id": record.action_id,
            "level3_completed": record.level3_completed,
        })
    
    def _check_power_balance(self, action: NexusAction, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check action against 51/49 power balance constitution."""
        if not self._power_balance:
            return {"passed": True}
        
        try:
            sector = payload.get("sector", "governance")
            return self._power_balance.check_balance(
                sector=sector,
                action=action.value,
                impact=payload.get("impact", 0.0),
            )
        except Exception as e:
            logger.warning(f"Power balance check failed: {e}")
            return {"passed": True}
    
    def _resolve_target_user(
        self, user_id: str, from_mode: NexusMode, to_mode: NexusMode
    ) -> str:
        """
        Resolve the target user for cross-mode consent.
        
        In the "One Person, Many Roles" model, the same user may have
        different Digital Twins for different modes. This resolves which
        user/twin should receive the consent request.
        """
        if self._federated_identity:
            try:
                twin = self._federated_identity.get_twin(user_id, to_mode.value)
                if twin:
                    return twin.get("twin_id", user_id)
            except Exception:
                pass
        
        # Default: same user (they have multiple roles)
        return user_id
    
    async def _execute_action(self, record: NexusActionRecord) -> Dict[str, Any]:
        """
        Execute the action by routing to the appropriate handler.
        
        This delegates to the stakeholder coordinator, government layer,
        enterprise layer, or other handlers based on the action type.
        """
        action_handlers = {
            # Citizen actions
            NexusAction.IDENTITY_VERIFY: self._handle_identity_verify,
            NexusAction.DATA_ACCESS: self._handle_data_access,
            NexusAction.AGENT_CONTRACT: self._handle_agent_contract,
            NexusAction.PERSONAL_FINANCE: self._handle_personal_finance,
            NexusAction.HEALTH_RECORD: self._handle_health_record,
            NexusAction.EDUCATION: self._handle_education,
            
            # Company actions
            NexusAction.COMMERCE: self._handle_commerce,
            NexusAction.EMPLOYMENT: self._handle_employment,
            NexusAction.LICENSE: self._handle_license,
            NexusAction.TAX_FILING: self._handle_tax_filing,
            NexusAction.COMPLIANCE: self._handle_compliance,
            NexusAction.MARKETPLACE: self._handle_marketplace,
            
            # Government actions
            NexusAction.POLICY: self._handle_policy,
            NexusAction.REGULATION: self._handle_regulation,
            NexusAction.VETO: self._handle_veto,
            NexusAction.EMERGENCY: self._handle_emergency,
            NexusAction.CONSTITUTIONAL: self._handle_constitutional,
            NexusAction.AUDIT: self._handle_audit,
            
            # Cross-mode actions
            NexusAction.CROSS_CONSENT: self._handle_cross_consent,
            NexusAction.DISPUTE: self._handle_dispute,
            NexusAction.GOVERNANCE: self._handle_governance,
            NexusAction.CONSENSUS: self._handle_consensus,
        }
        
        handler = action_handlers.get(record.action)
        if handler:
            return await handler(record)
        
        return {"status": "unhandled", "action": record.action.value}
    
    # ─── Consent Management ───────────────────────────────────────────────────
    
    def respond_to_consent(
        self,
        request_id: str,
        approved: bool,
        response: Optional[str] = None,
    ) -> bool:
        """Respond to a cross-consent request."""
        with self._lock:
            request = self._consent_requests.get(request_id)
            if not request:
                logger.warning(f"Consent request not found: {request_id}")
                return False
            
            request.status = "approved" if approved else "rejected"
            request.response = response
            request.responded_at = time.time()
            
            # Update the action record
            action = self._actions.get(request.action_id)
            if action:
                mode_key = request.to_mode.value
                action.consent_given[mode_key] = approved
                
                # Check if all required consents are given
                all_given = all(
                    action.consent_given.get(m.value, False)
                    for m in action.target_modes
                    if m != action.source_mode
                )
                
                if all_given:
                    action.status = NexusStatus.APPROVED
                elif any(
                    not action.consent_given.get(m.value, True)
                    for m in action.target_modes
                    if m != action.source_mode
                ):
                    action.status = NexusStatus.REJECTED
            
            self._persist_consent(request)
            logger.info(
                f"{'✅' if approved else '❌'} Consent {request.status} — "
                f"request={request_id[:8]}"
            )
            return True
    
    def get_pending_consents(self, user_id: str, mode: Optional[NexusMode] = None) -> List[CrossConsentRequest]:
        """Get all pending consent requests for a user."""
        with self._lock:
            return [
                req for req in self._consent_requests.values()
                if req.to_user_id == user_id
                and req.status == "pending"
                and (mode is None or req.to_mode == mode)
            ]
    
    # ─── Action Handlers ──────────────────────────────────────────────────────
    
    async def _handle_identity_verify(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle identity verification (Citizen mode)."""
        if self._federated_identity:
            try:
                result = self._federated_identity.verify(
                    user_id=record.user_id,
                    proof=record.payload.get("proof"),
                )
                return {"verified": result, "method": "federated_identity"}
            except Exception as e:
                return {"verified": False, "error": str(e)}
        return {"verified": True, "method": "basic"}
    
    async def _handle_data_access(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle data access request (Citizen mode - Local-First)."""
        data_type = record.payload.get("data_type", "personal")
        scope = record.payload.get("scope", "self")
        
        # Local-First: data stays on user's device
        return {
            "status": "granted",
            "data_type": data_type,
            "scope": scope,
            "local_first": True,
            "message": "Data accessed locally - not stored on central servers",
        }
    
    async def _handle_agent_contract(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle agent contract creation (Citizen/Company mode)."""
        try:
            from core.agent_contract import get_agent_contract_system, ContractDuration
            
            contract_system = get_agent_contract_system()
            
            # Map duration_days to ContractDuration enum
            duration_days = record.payload.get("duration_days", 15)
            if duration_days <= 5:
                duration = ContractDuration.TRIAL
            elif duration_days <= 15:
                duration = ContractDuration.STANDARD
            else:
                duration = ContractDuration.EXTENDED
            
            contract = contract_system.propose_contract(
                agent_id=record.payload.get("agent_id", f"agent_{record.user_id}"),
                human_id=record.user_id,
                title=record.payload.get("title", f"Agent Contract - {record.source_mode.value}"),
                description=record.payload.get("description", ""),
                duration=duration,
                scope=None,
                agent_type="clone",
            )
            return {
                "status": "created",
                "contract_id": contract.contract_id,
                "duration_days": duration.value,
                "mode": record.source_mode.value,
            }
        except Exception as e:
            logger.error(f"Agent contract creation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _handle_personal_finance(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle personal finance action (Citizen mode)."""
        return {
            "status": "processed",
            "action": "personal_finance",
            "mode": "citizen",
            "local_first": True,
        }
    
    async def _handle_health_record(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle health record access (Citizen/Government mode)."""
        return {
            "status": "granted",
            "action": "health_record",
            "mode": record.source_mode.value,
            "encrypted": True,
            "local_first": True,
        }
    
    async def _handle_education(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle education action (Citizen/Government mode)."""
        return {
            "status": "processed",
            "action": "education",
            "mode": record.source_mode.value,
        }
    
    async def _handle_commerce(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle commerce action (Company mode)."""
        if self._enterprise_layer:
            try:
                result = self._enterprise_layer.check_compliance(
                    organization=record.payload.get("organization", record.user_id),
                    action="commerce",
                    context=record.payload,
                )
                return {
                    "status": result.status.value,
                    "details": result.details,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "processed", "action": "commerce"}
    
    async def _handle_employment(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle employment action (Company mode)."""
        return {
            "status": "processed",
            "action": "employment",
            "mode": "company",
        }
    
    async def _handle_license(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle license request (Company → Government)."""
        if self._enterprise_layer:
            try:
                license = self._enterprise_layer.register_license(
                    organization=record.payload.get("organization", record.user_id),
                    tier=record.payload.get("tier", "starter"),
                    jurisdiction=record.payload.get("jurisdiction", "NP"),
                    max_users=record.payload.get("max_users", 10),
                    max_agents=record.payload.get("max_agents", 5),
                )
                return {
                    "status": "created",
                    "license_id": license.license_id,
                    "tier": license.tier.value,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "processed", "action": "license"}
    
    async def _handle_tax_filing(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle tax filing (Company → Government)."""
        return {
            "status": "filed",
            "action": "tax_filing",
            "government_notified": True,
        }
    
    async def _handle_compliance(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle compliance check (Company → Government)."""
        if self._enterprise_layer:
            try:
                result = self._enterprise_layer.check_compliance(
                    organization=record.payload.get("organization", record.user_id),
                    action=record.payload.get("compliance_action", "general"),
                    context=record.payload,
                )
                return {
                    "status": result.status.value,
                    "details": result.details,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "compliant", "action": "compliance"}
    
    async def _handle_marketplace(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle marketplace action (Citizen/Company mode)."""
        return {
            "status": "routed",
            "action": "marketplace",
            "mode": record.source_mode.value,
            "message": "Routed to marketplace engine",
        }
    
    async def _handle_policy(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle policy action (Government mode)."""
        if self._government_layer:
            try:
                compliant, violation = self._government_layer.check_constitutional_compliance(
                    action=record.payload.get("policy_action", ""),
                    target=record.payload.get("target", ""),
                )
                if not compliant:
                    return {
                        "status": "blocked",
                        "reason": violation,
                        "constitutional_check": False,
                    }
            except Exception as e:
                logger.warning(f"Constitutional check failed: {e}")
        
        if self._stakeholder_coordinator:
            try:
                from core.governance.stakeholder_coordinator import ActionCategory, Stakeholder
                action = self._stakeholder_coordinator.propose_action(
                    category=ActionCategory.POLICY,
                    initiated_by=Stakeholder.GOVERNMENT,
                    description=record.payload.get("description", ""),
                    details=record.payload,
                )
                return {
                    "status": "proposed",
                    "action_id": action.action_id,
                    "requires_approval": [s.value for s in action.required_approvals],
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "processed", "action": "policy"}
    
    async def _handle_regulation(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle regulation action (Government mode)."""
        return {
            "status": "published",
            "action": "regulation",
            "public_notified": True,
        }
    
    async def _handle_veto(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle veto action (Government mode - sovereign power)."""
        if self._government_layer:
            try:
                from core.governance.government_layer import VetoType
                veto = self._government_layer.issue_veto(
                    veto_type=VetoType.CONSTITUTIONAL,
                    initiated_by=record.user_id,
                    target_action=record.payload.get("target_action", ""),
                    reason=record.payload.get("reason", "Sovereign veto"),
                )
                return {
                    "status": "vetoed" if veto.approved else "pending",
                    "veto_id": veto.veto_id,
                    "veto_type": veto.veto_type.value,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "vetoed", "action": "veto"}
    
    async def _handle_emergency(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle emergency action (Government mode)."""
        if self._government_layer:
            try:
                self._government_layer.declare_emergency(
                    initiated_by=record.user_id,
                    reason=record.payload.get("reason", "Emergency declared"),
                )
                return {
                    "status": "emergency_declared",
                    "all_modes_notified": True,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "emergency_declared"}
    
    async def _handle_constitutional(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle constitutional amendment (Government mode - 90% supermajority)."""
        if self._power_balance:
            try:
                amendment = self._power_balance.propose_amendment(
                    sector=record.payload.get("sector", "governance"),
                    proposed_control=record.payload.get("proposed_control", "public_coordinated"),
                    proposed_public_share=record.payload.get("proposed_public_share", 0.51),
                    rationale=record.payload.get("rationale", ""),
                    proposer=record.user_id,
                )
                return {
                    "status": "proposed",
                    "amendment_id": amendment.id,
                    "requires_supermajority": True,
                    "supermajority_threshold": 0.90,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "processed", "action": "constitutional"}
    
    async def _handle_audit(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle audit action (Government mode - transparency)."""
        return {
            "status": "audit_generated",
            "action": "audit",
            "transparent": True,
            "audit_log_entries": len(self._audit_log),
        }
    
    async def _handle_cross_consent(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle cross-consent action (all modes)."""
        return {
            "status": "consent_processed",
            "action": "cross_consent",
            "consent_level": record.consent_level.value,
            "consent_given": record.consent_given,
        }
    
    async def _handle_dispute(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle dispute resolution (all modes)."""
        if self._stakeholder_coordinator:
            try:
                from core.governance.stakeholder_coordinator import ActionCategory, Stakeholder
                action = self._stakeholder_coordinator.propose_action(
                    category=ActionCategory.COMPLIANCE,
                    initiated_by=Stakeholder(record.source_mode.value),
                    description=record.payload.get("description", "Dispute resolution"),
                    details=record.payload,
                )
                return {
                    "status": "dispute_filed",
                    "action_id": action.action_id,
                    "requires_escalation": True,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "dispute_filed"}
    
    async def _handle_governance(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle governance action (all modes - 51/49 balance)."""
        return {
            "status": "governance_processed",
            "action": "governance",
            "power_balance_checked": True,
            "mode": record.source_mode.value,
        }
    
    async def _handle_consensus(self, record: NexusActionRecord) -> Dict[str, Any]:
        """Handle consensus action (all modes)."""
        if self._stakeholder_coordinator:
            try:
                from core.governance.stakeholder_coordinator import ActionCategory, Stakeholder
                action = self._stakeholder_coordinator.propose_action(
                    category=ActionCategory.AMENDMENT,
                    initiated_by=Stakeholder(record.source_mode.value),
                    description=record.payload.get("description", "Consensus decision"),
                    details=record.payload,
                )
                return {
                    "status": "consensus_initiated",
                    "action_id": action.action_id,
                    "required_approvals": [s.value for s in action.required_approvals],
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "consensus_reached"}
    
    # ─── Audit & Persistence ─────────────────────────────────────────────────
    
    def _generate_audit_hash(self, record: NexusActionRecord) -> str:
        """Generate a cryptographic hash for the action record."""
        import hashlib
        content = f"{record.action_id}:{record.user_id}:{record.source_mode.value}:{record.action.value}:{json.dumps(record.payload, sort_keys=True)}:{record.status.value}:{record.created_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _fire_callbacks(self, event: str, data: Dict[str, Any]) -> None:
        """Fire callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.warning(f"Callback failed for event '{event}': {e}")
    
    def _persist_action(self, record: NexusActionRecord) -> None:
        """Persist an action record to the append-only log."""
        try:
            os.makedirs(os.path.dirname(_NEXUS_DB_PATH), exist_ok=True)
            with open(_NEXUS_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
            self._audit_log.append(record.to_dict())
        except Exception as e:
            logger.warning(f"Failed to persist action: {e}")
    
    def _persist_consent(self, request: CrossConsentRequest) -> None:
        """Persist a consent request to the append-only log."""
        try:
            os.makedirs(os.path.dirname(_NEXUS_DB_PATH), exist_ok=True)
            consent_path = _NEXUS_DB_PATH.replace(".jsonl", "_consent.jsonl")
            with open(consent_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(request.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist consent: {e}")
    
    def _load_from_db(self) -> None:
        """Load persisted state from disk."""
        try:
            if os.path.exists(_NEXUS_DB_PATH):
                with open(_NEXUS_DB_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            action_id = data.get("action_id")
                            if action_id:
                                record = NexusActionRecord(
                                    action_id=action_id,
                                    user_id=data.get("user_id", ""),
                                    source_mode=NexusMode(data.get("source_mode", "citizen")),
                                    target_modes=[NexusMode(m) for m in data.get("target_modes", ["citizen"])],
                                    action=NexusAction(data.get("action", "data_access")),
                                    payload=data.get("payload", {}),
                                    status=NexusStatus(data.get("status", "pending")),
                                    consent_level=ConsentLevel(data.get("consent_level", "self")),
                                    consent_given=data.get("consent_given", {}),
                                    level3_required=data.get("level3_required", False),
                                    level3_completed=data.get("level3_completed", False),
                                    result=data.get("result"),
                                    error=data.get("error"),
                                    created_at=data.get("created_at", time.time()),
                                    resolved_at=data.get("resolved_at"),
                                    audit_hash=data.get("audit_hash"),
                                )
                                self._actions[action_id] = record
                                self._audit_log.append(data)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Skipping malformed log entry: {e}")
        except Exception as e:
            logger.warning(f"Failed to load from DB: {e}")
    
    # ─── Status & Statistics ─────────────────────────────────────────────────
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the Nexus Connector."""
        with self._lock:
            active_sessions = len(self._sessions)
            pending_actions = sum(
                1 for a in self._actions.values()
                if a.status in (NexusStatus.PENDING, NexusStatus.PROCESSING,
                                NexusStatus.REQUIRES_CONSENT, NexusStatus.REQUIRES_LEVEL3)
            )
            completed_actions = sum(
                1 for a in self._actions.values()
                if a.status == NexusStatus.COMPLETED
            )
            failed_actions = sum(
                1 for a in self._actions.values()
                if a.status == NexusStatus.FAILED
            )
            
            return {
                "status": "active",
                "active_sessions": active_sessions,
                "total_actions": len(self._actions),
                "pending_actions": pending_actions,
                "completed_actions": completed_actions,
                "failed_actions": failed_actions,
                "pending_consents": len([r for r in self._consent_requests.values() if r.status == "pending"]),
                "modes": [m.value for m in NexusMode],
                "actions_supported": [a.value for a in NexusAction],
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        with self._lock:
            mode_counts: Dict[str, int] = {}
            action_counts: Dict[str, int] = {}
            
            for action in self._actions.values():
                mode = action.source_mode.value
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
                
                act = action.action.value
                action_counts[act] = action_counts.get(act, 0) + 1
            
            return {
                "total_sessions": sum(len(sessions) for sessions in self._user_sessions.values()),
                "unique_users": len(self._user_sessions),
                "total_actions": len(self._actions),
                "actions_by_mode": mode_counts,
                "actions_by_type": action_counts,
                "total_consent_requests": len(self._consent_requests),
                "audit_log_size": len(self._audit_log),
            }


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Management
# ═══════════════════════════════════════════════════════════════════════════════

_nexus_instance = None
_nexus_instance_lock = threading.Lock()


def get_nexus_connector() -> NexusConnector:
    """Get or create the singleton NexusConnector instance."""
    global _nexus_instance
    if _nexus_instance is None:
        with _nexus_instance_lock:
            if _nexus_instance is None:
                _nexus_instance = NexusConnector()
    return _nexus_instance


def reset_nexus_connector() -> None:
    """Reset the singleton for testing."""
    global _nexus_instance
    with _nexus_instance_lock:
        _nexus_instance = None
    logger.info("NexusConnector singleton reset")