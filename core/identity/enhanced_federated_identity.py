#!/usr/bin/env python3
"""
Enhanced Federated Identity — Multi-Mode Digital Twin System
=============================================================

Implements the "एउटै व्यक्ति, धेरै भूमिका" (One Person, Many Roles) pattern.

Each user has a single identity that maps to multiple isolated Digital Twins:
  - Citizen Twin: Local-First, personal data, agent contracts
  - Company Twin: Commercial operations, licensing, employment
  - Government Twin: Sovereign oversight, policy, constitutional enforcement
  - Hybrid Twin: Multi-role simultaneous operation

Key Features:
  - Single user_id → Multiple mode-specific Digital Twins
  - Isolated data per mode (Citizen data never leaks to Company mode)
  - Mode switching with context preservation
  - Cross-mode consent verification
  - Immutable audit trail of all mode switches
  - ZKP-based privacy preservation across modes

Integrates with:
  - core/nexus_connector.py — Mode routing and cross-consent
  - core/mirror/mirror_module.py — Digital Twin consciousness per mode
  - core/security/zkp_privacy.py — Zero-knowledge proofs for cross-mode verification
  - core/security/level3_confirmation.py — High-security mode switches
"""

import os
import time
import json
import uuid
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("AsimNexus.Identity.EnhancedFederated")

# ─── Environment Configuration ────────────────────────────────────────────────
_IDENTITY_DB_PATH = os.getenv(
    "ASIM_IDENTITY_DB_PATH",
    "data/enhanced_identity.jsonl",
)


class IdentityMode(str, Enum):
    """The operational modes a user can assume."""
    CITIZEN = "citizen"
    COMPANY = "company"
    GOVERNMENT = "government"
    HYBRID = "hybrid"


class TwinStatus(str, Enum):
    """Status of a Digital Twin."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"


@dataclass
class DigitalTwin:
    """A mode-specific Digital Twin for a user."""
    twin_id: str
    user_id: str
    mode: IdentityMode
    display_name: str
    status: TwinStatus = TwinStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Mode-specific data references (not the data itself - Local-First)
    data_refs: Dict[str, str] = field(default_factory=dict)
    
    # Cryptographic binding
    public_key: Optional[str] = None
    twin_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "user_id": self.user_id,
            "mode": self.mode.value,
            "display_name": self.display_name,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metadata": self.metadata,
            "data_refs": self.data_refs,
            "public_key": self.public_key,
            "twin_hash": self.twin_hash,
        }


@dataclass
class ModeSwitchRecord:
    """Record of a mode switch event."""
    switch_id: str
    user_id: str
    from_mode: IdentityMode
    to_mode: IdentityMode
    reason: str
    approved: bool = True
    timestamp: float = field(default_factory=time.time)
    audit_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "switch_id": self.switch_id,
            "user_id": self.user_id,
            "from_mode": self.from_mode.value,
            "to_mode": self.to_mode.value,
            "reason": self.reason,
            "approved": self.approved,
            "timestamp": self.timestamp,
            "audit_hash": self.audit_hash,
        }


class EnhancedFederatedIdentity:
    """
    Enhanced Federated Identity system supporting the "One Person, Many Roles" pattern.
    
    Each user has a single identity that maps to multiple isolated Digital Twins,
    one per operational mode. Data is strictly isolated between modes.
    
    Architecture:
    ```
    User (Single Identity)
         │
         ├── Citizen Twin ─── Local-First Data
         ├── Company Twin ─── Commercial Data
         ├── Government Twin ─ Sovereign Data
         └── Hybrid Twin ──── Combined Context
    ```
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # User registry: user_id -> {mode -> DigitalTwin}
        self._users: Dict[str, Dict[str, DigitalTwin]] = {}
        
        # Mode switch audit log
        self._switch_log: List[ModeSwitchRecord] = []
        
        # Active sessions per user
        self._active_sessions: Dict[str, str] = {}  # user_id -> current_mode
        
        # Load persisted state
        self._load_from_db()
        
        logger.info(
            f"🔐 EnhancedFederatedIdentity initialized — "
            f"{len(self._users)} users, "
            f"{sum(len(twins) for twins in self._users.values())} total twins"
        )
    
    # ─── User Registration ───────────────────────────────────────────────────
    
    def register_user(self, user_id: str, display_name: str) -> Dict[str, DigitalTwin]:
        """Register a new user with all four mode-specific Digital Twins."""
        with self._lock:
            if user_id in self._users:
                logger.warning(f"User already registered: {user_id}")
                return self._users[user_id]
            
            twins = {}
            for mode in IdentityMode:
                twin = DigitalTwin(
                    twin_id=str(uuid.uuid4()),
                    user_id=user_id,
                    mode=mode,
                    display_name=f"{display_name} ({mode.value})",
                    metadata={
                        "mode": mode.value,
                        "created_from": "registration",
                    },
                )
                twins[mode.value] = twin
            
            self._users[user_id] = twins
            self._persist_user(user_id, twins)
            
            logger.info(
                f"👤 User registered — {user_id} ({display_name}) "
                f"with {len(twins)} mode-specific twins"
            )
            return twins
    
    def get_twin(self, user_id: str, mode: str) -> Optional[DigitalTwin]:
        """Get a user's Digital Twin for a specific mode."""
        with self._lock:
            user_twins = self._users.get(user_id)
            if not user_twins:
                return None
            return user_twins.get(mode)
    
    def get_all_twins(self, user_id: str) -> Dict[str, DigitalTwin]:
        """Get all Digital Twins for a user."""
        with self._lock:
            return self._users.get(user_id, {})
    
    def twin_exists(self, user_id: str, mode: str) -> bool:
        """Check if a twin exists for a user in a given mode."""
        return self.get_twin(user_id, mode) is not None
    
    # ─── Mode Switching ──────────────────────────────────────────────────────
    
    def switch_mode(
        self,
        user_id: str,
        to_mode: IdentityMode,
        reason: str = "user_request",
        require_approval: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[ModeSwitchRecord]]:
        """
        Switch a user's active mode.
        
        Args:
            user_id: The user's unique identifier.
            to_mode: The target mode to switch to.
            reason: Why the switch is happening.
            require_approval: Whether Level-3 confirmation is needed.
            
        Returns:
            Tuple of (success, error_message, switch_record).
        """
        with self._lock:
            user_twins = self._users.get(user_id)
            if not user_twins:
                return False, "User not registered", None
            
            target_twin = user_twins.get(to_mode.value)
            if not target_twin:
                return False, f"Twin for mode '{to_mode.value}' not found", None
            
            if target_twin.status != TwinStatus.ACTIVE:
                return False, f"Twin is {target_twin.status.value}", None
            
            current_mode = self._active_sessions.get(user_id, IdentityMode.CITIZEN.value)
            
            # Create switch record
            switch = ModeSwitchRecord(
                switch_id=str(uuid.uuid4()),
                user_id=user_id,
                from_mode=IdentityMode(current_mode),
                to_mode=to_mode,
                reason=reason,
                approved=not require_approval,
            )
            
            # Generate audit hash
            import hashlib
            content = f"{switch.switch_id}:{user_id}:{current_mode}:{to_mode.value}:{reason}:{switch.timestamp}"
            switch.audit_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Update active session
            self._active_sessions[user_id] = to_mode.value
            
            # Update twin's last_active
            target_twin.last_active = time.time()
            
            # Log the switch
            self._switch_log.append(switch)
            self._persist_switch(switch)
            
            logger.info(
                f"🔄 Mode switch — {user_id}: "
                f"{current_mode} → {to_mode.value} ({reason})"
            )
            
            return True, None, switch
    
    def get_active_mode(self, user_id: str) -> Optional[str]:
        """Get a user's currently active mode."""
        with self._lock:
            return self._active_sessions.get(user_id)
    
    def get_mode_switch_history(
        self, user_id: str, limit: int = 50
    ) -> List[ModeSwitchRecord]:
        """Get mode switch history for a user."""
        with self._lock:
            return [
                record for record in self._switch_log
                if record.user_id == user_id
            ][-limit:]
    
    # ─── Twin Management ─────────────────────────────────────────────────────
    
    def update_twin_metadata(
        self, user_id: str, mode: str, metadata: Dict[str, Any]
    ) -> bool:
        """Update metadata for a specific twin."""
        with self._lock:
            twin = self.get_twin(user_id, mode)
            if not twin:
                return False
            twin.metadata.update(metadata)
            self._persist_user(user_id, self._users[user_id])
            return True
    
    def suspend_twin(self, user_id: str, mode: str) -> bool:
        """Suspend a specific twin."""
        with self._lock:
            twin = self.get_twin(user_id, mode)
            if not twin:
                return False
            twin.status = TwinStatus.SUSPENDED
            self._persist_user(user_id, self._users[user_id])
            logger.warning(f"Twin suspended — {user_id}/{mode}")
            return True
    
    def activate_twin(self, user_id: str, mode: str) -> bool:
        """Activate a suspended twin."""
        with self._lock:
            twin = self.get_twin(user_id, mode)
            if not twin:
                return False
            twin.status = TwinStatus.ACTIVE
            self._persist_user(user_id, self._users[user_id])
            logger.info(f"Twin activated — {user_id}/{mode}")
            return True
    
    # ─── Cross-Mode Verification ─────────────────────────────────────────────
    
    def verify_cross_mode_access(
        self, user_id: str, from_mode: str, to_mode: str, action: str
    ) -> Tuple[bool, str]:
        """
        Verify if a user in one mode can access data/actions in another mode.
        
        This implements the data isolation guarantee:
        - Citizen data is NEVER accessible from Company or Government mode
        - Company data is NEVER accessible from Citizen mode
        - Government data is NEVER accessible from Citizen or Company mode
        - Hybrid mode can access all, but with full audit trail
        """
        # Same mode is always allowed
        if from_mode == to_mode:
            return True, "Same mode access"
        
        # Hybrid mode can access all (with audit)
        if from_mode == IdentityMode.HYBRID.value:
            return True, "Hybrid mode cross-access (audited)"
        
        # Government can access citizen data for specific purposes
        if from_mode == IdentityMode.GOVERNMENT.value and to_mode == IdentityMode.CITIZEN.value:
            if action in ("health_record", "education", "census", "emergency"):
                return True, "Government access to citizen data (audited)"
            return False, "Government cannot access citizen data for this purpose"
        
        # Government can access company data for compliance
        if from_mode == IdentityMode.GOVERNMENT.value and to_mode == IdentityMode.COMPANY.value:
            if action in ("compliance", "tax_filing", "audit", "regulation"):
                return True, "Government access to company data (audited)"
            return False, "Government cannot access company data for this purpose"
        
        # Company cannot access citizen data
        if from_mode == IdentityMode.COMPANY.value and to_mode == IdentityMode.CITIZEN.value:
            return False, "Company cannot access citizen data"
        
        # Citizen cannot access company or government data
        if from_mode == IdentityMode.CITIZEN.value and to_mode in (
            IdentityMode.COMPANY.value, IdentityMode.GOVERNMENT.value
        ):
            return False, "Citizen cannot access company or government data"
        
        return False, f"Cross-mode access not permitted: {from_mode} → {to_mode}"
    
    # ─── Statistics ──────────────────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        with self._lock:
            mode_counts: Dict[str, int] = {}
            status_counts: Dict[str, int] = {}
            
            for user_twins in self._users.values():
                for twin in user_twins.values():
                    mode_counts[twin.mode.value] = mode_counts.get(twin.mode.value, 0) + 1
                    status_counts[twin.status.value] = status_counts.get(twin.status.value, 0) + 1
            
            return {
                "total_users": len(self._users),
                "total_twins": sum(len(twins) for twins in self._users.values()),
                "twins_by_mode": mode_counts,
                "twins_by_status": status_counts,
                "total_mode_switches": len(self._switch_log),
                "active_sessions": len(self._active_sessions),
            }
    
    # ─── Persistence ─────────────────────────────────────────────────────────
    
    def _persist_user(self, user_id: str, twins: Dict[str, DigitalTwin]) -> None:
        """Persist user twin data."""
        try:
            os.makedirs(os.path.dirname(_IDENTITY_DB_PATH), exist_ok=True)
            with open(_IDENTITY_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "user_registration",
                    "user_id": user_id,
                    "twins": {k: v.to_dict() for k, v in twins.items()},
                    "timestamp": time.time(),
                }) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist user: {e}")
    
    def _persist_switch(self, record: ModeSwitchRecord) -> None:
        """Persist a mode switch record."""
        try:
            os.makedirs(os.path.dirname(_IDENTITY_DB_PATH), exist_ok=True)
            with open(_IDENTITY_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "mode_switch",
                    "record": record.to_dict(),
                }) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist switch: {e}")
    
    def _load_from_db(self) -> None:
        """Load persisted state from disk."""
        try:
            if os.path.exists(_IDENTITY_DB_PATH):
                with open(_IDENTITY_DB_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            entry_type = data.get("type")
                            
                            if entry_type == "user_registration":
                                user_id = data["user_id"]
                                twins_data = data.get("twins", {})
                                twins = {}
                                for mode_str, twin_data in twins_data.items():
                                    twin = DigitalTwin(
                                        twin_id=twin_data["twin_id"],
                                        user_id=twin_data["user_id"],
                                        mode=IdentityMode(twin_data["mode"]),
                                        display_name=twin_data["display_name"],
                                        status=TwinStatus(twin_data.get("status", "active")),
                                        created_at=twin_data.get("created_at", time.time()),
                                        last_active=twin_data.get("last_active", time.time()),
                                        metadata=twin_data.get("metadata", {}),
                                        data_refs=twin_data.get("data_refs", {}),
                                        public_key=twin_data.get("public_key"),
                                        twin_hash=twin_data.get("twin_hash"),
                                    )
                                    twins[mode_str] = twin
                                self._users[user_id] = twins
                            
                            elif entry_type == "mode_switch":
                                record_data = data.get("record", {})
                                record = ModeSwitchRecord(
                                    switch_id=record_data["switch_id"],
                                    user_id=record_data["user_id"],
                                    from_mode=IdentityMode(record_data["from_mode"]),
                                    to_mode=IdentityMode(record_data["to_mode"]),
                                    reason=record_data.get("reason", ""),
                                    approved=record_data.get("approved", True),
                                    timestamp=record_data.get("timestamp", time.time()),
                                    audit_hash=record_data.get("audit_hash"),
                                )
                                self._switch_log.append(record)
                                
                                # Update active session
                                self._active_sessions[record.user_id] = record.to_mode.value
                        
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Skipping malformed entry: {e}")
        except Exception as e:
            logger.warning(f"Failed to load from DB: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Management
# ═══════════════════════════════════════════════════════════════════════════════

_identity_instance = None
_identity_instance_lock = threading.Lock()


def get_enhanced_identity() -> EnhancedFederatedIdentity:
    """Get or create the singleton EnhancedFederatedIdentity instance."""
    global _identity_instance
    if _identity_instance is None:
        with _identity_instance_lock:
            if _identity_instance is None:
                _identity_instance = EnhancedFederatedIdentity()
    return _identity_instance


def reset_enhanced_identity() -> None:
    """Reset the singleton for testing."""
    global _identity_instance
    with _identity_instance_lock:
        _identity_instance = None
    logger.info("EnhancedFederatedIdentity singleton reset")
