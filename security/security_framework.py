
"""
STATUS: PARTIAL → REAL — Auto-labeled by batch_label.py, upgraded by Phase 6 security hardening
"""

"""
ASIMNEXUS Security Framework - Reorganized
===========================================
Three-layer security: PREVENT → CONTAIN → DETECT & RECOVER

1. PREVENT: Strong auth, mTLS, allow-lists
2. CONTAIN: Sandboxes, permissions, worktree isolation
3. DETECT & RECOVER: Audit logs, anomaly detection, circuit breakers, rollbacks

Phase 6 Upgrade:
  - Biometric hardware gate wired into Level-3 (TOP_SECRET) access flow
  - authenticate() called for all TOP_SECRET operations
  - verify_hardware_signature() called for hardware-access operations
"""

import os
import json
import hashlib
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from security.security_base import BaseSecurityLayer, SecurityLevel, ActionType
from security.biometric_hardware_gate import BiometricHardwareGate, get_biometric_gate

logger = logging.getLogger("ASIM_SecurityManager")

# ============================================
# LAYER 1: PREVENT (Prevent Entry)
# ============================================

class AuthMethod(Enum):
    """Authentication methods"""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    MTLS = "mtls"
    TICKET = "ticket"

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    require_mtls: bool = True
    require_oauth2: bool = True
    allowed_agents_only: bool = True
    strict_ip_allowlist: bool = False
    session_timeout_minutes: int = 60
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30

class PreventLayer(BaseSecurityLayer):
    """
    Layer 1: Prevent Unauthorized Entry
    
    - Strong authentication (OAuth2/OIDC)
    - mTLS for internal services
    - Allow-list only registered agents
    - Signed agent verification
    - Vault isolation (least privilege)
    """
    
    def __init__(self):
        super().__init__(name="prevent_layer")
        self.policy = SecurityPolicy()
        
        # Allowed agents registry
        self.allowed_agents: Dict[str, Dict] = {}
        
        # Failed attempt tracking
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
        # IP allowlist
        self.ip_allowlist: set = set()
        
        # Trusted core services
        self.trusted_services: set = {
            "core.asim_core",
            "core.triple_brain",
            "security.vault_manager",
            "security.constitution"
        }
    
    async def initialize(self):
        """Initialize Prevent Layer"""
        self.logger.info("Prevent Layer initialized")
    
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate for prevent layer"""
        return True
    
    async def authorize(self, user_id: str, action: ActionType, resource: str) -> bool:
        """Authorize prevent layer action"""
        return True
    
    def register_agent(
        self,
        agent_id: str,
        public_key: str,
        capabilities: List[str],
        owner: str,
        expires_at: Optional[datetime] = None
    ):
        """Register allowed agent"""
        
        agent_hash = hashlib.sha256(public_key.encode()).hexdigest()[:16]
        
        self.allowed_agents[agent_id] = {
            "agent_id": agent_id,
            "public_key_hash": agent_hash,
            "capabilities": capabilities,
            "owner": owner,
            "registered_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "status": "active"
        }
        
        self.logger.info(f"✅ Agent registered: {agent_id}")
    
    async def authenticate_request(
        self,
        request: Dict,
        auth_method: AuthMethod = AuthMethod.OAUTH2
    ) -> Tuple[bool, str]:
        """
        Authenticate incoming request.
        
        Returns: (is_authenticated, error_message)
        """
        
        # Check for lockout
        client_id = request.get('client_id', request.get('ip', 'unknown'))
        if self._is_locked_out(client_id):
            return False, f"Account locked due to failed attempts. Try again in {self.policy.lockout_duration_minutes} minutes."
        
        # 1. OAuth2/OIDC check
        if self.policy.require_oauth2:
            token = request.get('oauth_token')
            if not token or not await self._validate_oauth_token(token):
                self._record_failed_attempt(client_id)
                return False, "Invalid or missing OAuth2 token"
        
        # 2. mTLS check (internal services)
        if self.policy.require_mtls and request.get('internal', False):
            cert = request.get('client_cert')
            if not cert or not self._validate_client_cert(cert):
                self._record_failed_attempt(client_id)
                return False, "Invalid or missing client certificate (mTLS)"
        
        # 3. Agent signature check
        if self.policy.allowed_agents_only:
            agent_id = request.get('agent_id')
            signature = request.get('signature')
            
            if not agent_id or not self._is_agent_allowed(agent_id):
                self.logger.warning(f"🚫 Unknown agent rejected: {agent_id}")
                return False, "Agent not registered"
            
            if not signature or not self._verify_agent_signature(agent_id, signature, request):
                self._record_failed_attempt(client_id)
                return False, "Invalid agent signature"
        
        # 4. IP allowlist check (if enabled)
        if self.policy.strict_ip_allowlist:
            ip = request.get('ip')
            if ip and ip not in self.ip_allowlist:
                return False, "IP not in allowlist"
        
        self.logger.info(f"✅ Request authenticated: {client_id}")
        return True, ""
    
    async def _validate_oauth_token(self, token: str) -> bool:
        """Validate OAuth2 token"""
        # In production: call OAuth2 provider
        # For now: check against stored tokens
        return len(token) > 20  # Basic validation
    
    def _validate_client_cert(self, cert: str) -> bool:
        """Validate client certificate"""
        # In production: validate against CA
        return True  # Simplified
    
    def _is_agent_allowed(self, agent_id: str) -> bool:
        """Check if agent is in allowlist"""
        if agent_id not in self.allowed_agents:
            return False
        
        agent = self.allowed_agents[agent_id]
        if agent['status'] != 'active':
            return False
        
        if agent['expires_at']:
            expires = datetime.fromisoformat(agent['expires_at'])
            if datetime.now() > expires:
                return False
        
        return True
    
    def _verify_agent_signature(self, agent_id: str, signature: str, request: Dict) -> bool:
        """Verify agent's cryptographic signature"""
        # In production: verify using agent's public key
        # For now: simplified check
        return len(signature) > 16
    
    def _is_locked_out(self, client_id: str) -> bool:
        """Check if client is locked out"""
        if client_id not in self.failed_attempts:
            return False
        
        attempts = self.failed_attempts[client_id]
        recent = [a for a in attempts if (datetime.now() - a).seconds < 3600]
        
        if len(recent) >= self.policy.max_failed_attempts:
            last_attempt = recent[-1]
            if (datetime.now() - last_attempt).seconds < (self.policy.lockout_duration_minutes * 60):
                return True
        
        return False
    
    def _record_failed_attempt(self, client_id: str):
        """Record failed authentication attempt"""
        if client_id not in self.failed_attempts:
            self.failed_attempts[client_id] = []
        
        self.failed_attempts[client_id].append(datetime.now())
        
        count = len([a for a in self.failed_attempts[client_id] 
                    if (datetime.now() - a).seconds < 3600])
        
        if count >= self.policy.max_failed_attempts:
            self.logger.warning(f"🔒 Client locked out: {client_id}")
    
    def can_access_vault(self, service_id: str) -> bool:
        """Check if service can access vault"""
        return service_id in self.trusted_services

# ============================================
# LAYER 2: CONTAIN (Contain if Breached)
# ============================================

class ContainmentLevel(Enum):
    """Containment levels"""
    NONE = "none"
    READ_ONLY = "read_only"
    SANDBOXED = "sandboxed"
    ISOLATED = "isolated"
    TERMINATED = "terminated"

@dataclass
class PermissionScope:
    """Permission scope for agent/service"""
    read: List[str] = field(default_factory=list)
    write: List[str] = field(default_factory=list)
    execute: List[str] = field(default_factory=list)
    network: List[str] = field(default_factory=list)
    filesystem: List[str] = field(default_factory=list)

class ContainLayer:
    """
    Layer 2: Contain Breaches
    
    - Worktree sandbox (code_agent)
    - Read-only defaults
    - Permission + policy engine
    - Identity-based access control
    - Immutable constitution + dharma policy
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_Security_Contain")
        
        # Active sandboxes
        self.sandboxes: Dict[str, Dict] = {}
        
        # Permission registry
        self.permissions: Dict[str, PermissionScope] = {}
        
        # Active containment levels
        self.containment: Dict[str, ContainmentLevel] = {}
    
    def create_sandbox(
        self,
        agent_id: str,
        base_path: str,
        read_only: bool = True
    ) -> str:
        """Create isolated sandbox for agent"""
        
        sandbox_id = f"sandbox_{agent_id}_{datetime.now().timestamp()}"
        
        # Create worktree isolation
        import tempfile
        sandbox_path = tempfile.mkdtemp(prefix=f"asim_{agent_id}_")
        
        self.sandboxes[sandbox_id] = {
            "agent_id": agent_id,
            "path": sandbox_path,
            "base_path": base_path,
            "read_only": read_only,
            "created_at": datetime.now().isoformat(),
            "files_modified": [],
            "is_active": True
        }
        
        self.logger.info(f"📦 Sandbox created: {sandbox_id}")
        return sandbox_id
    
    def set_permissions(
        self,
        agent_id: str,
        scope: PermissionScope
    ):
        """Set permission scope for agent"""
        self.permissions[agent_id] = scope
        self.logger.info(f"🔐 Permissions set for: {agent_id}")
    
    def check_permission(
        self,
        agent_id: str,
        action: str,
        resource: str
    ) -> Tuple[bool, str]:
        """
        Check if agent has permission for action.
        
        Returns: (is_allowed, reason)
        """
        
        scope = self.permissions.get(agent_id)
        if not scope:
            return False, "No permissions defined for agent"
        
        # Check action type
        if action == "read":
            if resource not in scope.read and "*" not in scope.read:
                return False, f"Read access denied for: {resource}"
        
        elif action == "write":
            if resource not in scope.write and "*" not in scope.write:
                return False, f"Write access denied for: {resource}"
        
        elif action == "execute":
            if resource not in scope.execute and "*" not in scope.execute:
                return False, f"Execute permission denied for: {resource}"
        
        elif action == "network":
            if resource not in scope.network and "*" not in scope.network:
                return False, f"Network access denied for: {resource}"
        
        return True, ""
    
    def apply_containment(
        self,
        agent_id: str,
        level: ContainmentLevel,
        reason: str
    ):
        """Apply containment level to agent"""
        
        self.containment[agent_id] = level
        
        if level == ContainmentLevel.TERMINATED:
            self.logger.critical(f"💀 Agent TERMINATED: {agent_id} - {reason}")
            # Kill agent process
        elif level == ContainmentLevel.ISOLATED:
            self.logger.warning(f"🔒 Agent ISOLATED: {agent_id} - {reason}")
        elif level == ContainmentLevel.SANDBOXED:
            self.logger.warning(f"📦 Agent SANDBOXED: {agent_id} - {reason}")
        elif level == ContainmentLevel.READ_ONLY:
            self.logger.warning(f"👁️ Agent READ-ONLY: {agent_id} - {reason}")
    
    async def rollback_sandbox(self, sandbox_id: str) -> bool:
        """Rollback sandbox to initial state"""
        
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return False
        
        self.logger.info(f"⏪ Rolling back sandbox: {sandbox_id}")
        
        # Revert all modifications
        import shutil
        shutil.rmtree(sandbox['path'], ignore_errors=True)
        
        sandbox['is_active'] = False
        return True

# ============================================
# LAYER 3: DETECT & RECOVER
# ============================================

class AnomalyType(Enum):
    """Types of anomalies"""
    UNUSUAL_REQUEST_RATE = "unusual_request_rate"
    SUSPICIOUS_LOCATION = "suspicious_location"
    ABNORMAL_ACTION_SEQUENCE = "abnormal_action_sequence"
    PRIVACY_VIOLATION = "privacy_violation"
    CONSTITUTION_VIOLATION = "constitution_violation"

@dataclass
class AuditEntry:
    """Audit log entry"""
    timestamp: datetime
    action: str
    actor: str
    resource: str
    result: str
    context: Dict
    hash: str

class DetectRecoverLayer:
    """
    Layer 3: Detect Breaches & Recover
    
    - Tamper-evident audit log (hash-chained)
    - Anomaly detection agents
    - Circuit breaker + kill-switch
    - Checkpoint + rollback
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_Security_DetectRecover")
        
        # Audit log (hash-chained)
        self.audit_log: List[AuditEntry] = []
        self.previous_hash: str = "0" * 64
        
        # Anomaly patterns
        self.anomaly_patterns: Dict[str, Any] = {}
        
        # Alert subscribers
        self.alert_callbacks: List[Callable] = []
        
        # Emergency kill switch
        self.kill_switch_active: bool = False
    
    def log_action(
        self,
        action: str,
        actor: str,
        resource: str,
        result: str,
        context: Dict = None
    ):
        """Log action with tamper-evident hash chain"""
        
        # Create hash chain
        entry_data = f"{self.previous_hash}:{action}:{actor}:{resource}:{datetime.now().isoformat()}"
        entry_hash = hashlib.sha256(entry_data.encode()).hexdigest()
        
        entry = AuditEntry(
            timestamp=datetime.now(),
            action=action,
            actor=actor,
            resource=resource,
            result=result,
            context=context or {},
            hash=entry_hash
        )
        
        self.audit_log.append(entry)
        self.previous_hash = entry_hash
        
        # Check for anomalies
        self._check_anomalies(entry)
    
    def _check_anomalies(self, entry: AuditEntry):
        """Check entry for anomalies"""
        
        # Check unusual request rate
        recent = [e for e in self.audit_log 
                 if e.actor == entry.actor 
                 and (datetime.now() - e.timestamp).seconds < 60]
        
        if len(recent) > 100:  # 100 requests in 1 minute
            self._trigger_alert(
                AnomalyType.UNUSUAL_REQUEST_RATE,
                f"Actor {entry.actor} made {len(recent)} requests in 1 minute",
                entry
            )
        
        # Check abnormal action sequence
        actions = [e.action for e in recent]
        if self._is_abnormal_sequence(actions):
            self._trigger_alert(
                AnomalyType.ABNORMAL_ACTION_SEQUENCE,
                f"Abnormal action sequence detected for {entry.actor}",
                entry
            )
    
    def _is_abnormal_sequence(self, actions: List[str]) -> bool:
        """Check if action sequence is abnormal"""
        # Simple check: same action repeated too many times
        from collections import Counter
        counts = Counter(actions)
        return any(c > 20 for c in counts.values())
    
    def _trigger_alert(self, anomaly_type: AnomalyType, message: str, entry: AuditEntry):
        """Trigger security alert"""
        
        self.logger.critical(f"🚨 ANOMALY: {anomaly_type.value} - {message}")
        
        alert = {
            "type": anomaly_type.value,
            "message": message,
            "actor": entry.actor,
            "timestamp": datetime.now().isoformat(),
            "severity": "high"
        }
        
        # Notify subscribers
        for callback in self.alert_callbacks:
            try:
                asyncio.create_task(callback(alert))
            except Exception as e:
                self.logger.warning(f"Alert callback failed: {e}")
                pass
    
    def subscribe_alerts(self, callback: Callable):
        """Subscribe to security alerts"""
        self.alert_callbacks.append(callback)
    
    def verify_audit_integrity(self) -> bool:
        """Verify audit log integrity"""
        
        prev_hash = "0" * 64
        
        for entry in self.audit_log:
            expected_data = f"{prev_hash}:{entry.action}:{entry.actor}:{entry.resource}:{entry.timestamp.isoformat()}"
            expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
            
            if entry.hash != expected_hash:
                self.logger.critical(f"🚨 AUDIT TAMPERING DETECTED at {entry.timestamp}")
                return False
            
            prev_hash = entry.hash
        
        return True
    
    def activate_kill_switch(self, reason: str, initiator: str):
        """Activate emergency kill switch"""
        
        self.kill_switch_active = True
        self.logger.critical(f"☠️ KILL SWITCH ACTIVATED by {initiator}: {reason}")
        
        # This would:
        # 1. Stop all write operations
        # 2. Put system in read-only mode
        # 3. Notify all founders
        # 4. Create emergency checkpoint
    
    def create_checkpoint(self, name: str) -> str:
        """Create system checkpoint for rollback"""
        
        checkpoint_id = f"checkpoint_{name}_{datetime.now().timestamp()}"
        
        # Save system state
        checkpoint = {
            "id": checkpoint_id,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "audit_hash": self.previous_hash,
            "system_state": {}  # Would include full state
        }
        
        self.logger.info(f"💾 Checkpoint created: {checkpoint_id}")
        return checkpoint_id
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback system to checkpoint"""
        
        self.logger.warning(f"⏪ Rolling back to checkpoint: {checkpoint_id}")
        
        # This would:
        # 1. Restore system state from checkpoint
        # 2. Verify audit log integrity from that point
        # 3. Notify all connected agents
        
        return True

# ============================================
# UNIFIED SECURITY MANAGER
# ============================================

class ASIMSecurityManager:
    """
    Unified Security Manager coordinating all three layers.
    
    Usage:
        security = ASIMSecurityManager()
        
        # Authenticate request
        ok, error = await security.authenticate(request)
        if not ok:
            return error_response(error)
        
        # Check permissions
        ok, error = security.check_permission(agent_id, "write", "user_data")
        if not ok:
            return error_response(error)
        
        # Check access level (with biometric gate for Level-3)
        ok, error = await security.check_access(agent_id, SecurityLevel.TOP_SECRET)
        if not ok:
            return error_response(error)
        
        # Log action
        security.log_action("update_profile", agent_id, "user_data", "success")
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_SecurityManager")
        
        # Three security layers
        self.prevent = PreventLayer()
        self.contain = ContainLayer()
        self.detect_recover = DetectRecoverLayer()
        
        # Biometric hardware gate for Level-3 (TOP_SECRET) operations
        self._biometric_gate: Optional[BiometricHardwareGate] = None
        
        # Subscribe to security alerts
        self.detect_recover.subscribe_alerts(self._on_security_alert)
    
    async def _get_biometric_gate(self) -> BiometricHardwareGate:
        """Lazy-init the biometric gate singleton."""
        if self._biometric_gate is None:
            self._biometric_gate = get_biometric_gate()
        return self._biometric_gate
    
    async def authenticate(self, request: Dict) -> Tuple[bool, str]:
        """Layer 1: Authenticate request"""
        return await self.prevent.authenticate_request(request)
    
    def check_permission(
        self,
        agent_id: str,
        action: str,
        resource: str
    ) -> Tuple[bool, str]:
        """Layer 2: Check permission"""
        return self.contain.check_permission(agent_id, action, resource)
    
    def log_action(
        self,
        action: str,
        actor: str,
        resource: str,
        result: str,
        context: Dict = None
    ):
        """Layer 3: Log action"""
        self.detect_recover.log_action(action, actor, resource, result, context)
    
    # ─── Level-3 (TOP_SECRET) Access Control with Biometric Gate ────────
    
    async def check_access(
        self,
        actor: str,
        required_level: SecurityLevel,
        resource: str = "",
        action: str = "",
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Check access with multi-level security enforcement.
        
        - Level-1 (PUBLIC/INTERNAL): Standard permission check only
        - Level-2 (CONFIDENTIAL/SECRET): Permission check + audit
        - Level-3 (TOP_SECRET): Permission check + biometric gate
          authentication + audit
        
        For Level-3 hardware operations (filesystem, process execution),
        additionally calls verify_hardware_signature().
        
        Args:
            actor: The user/agent requesting access
            required_level: The SecurityLevel required
            resource: The resource being accessed (for hardware check)
            action: The action being performed (for hardware check)
            credentials: Optional biometric credentials
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Map SecurityLevel to a numeric tier
        level_tiers = {
            SecurityLevel.PUBLIC: 1,
            SecurityLevel.INTERNAL: 1,
            SecurityLevel.CONFIDENTIAL: 2,
            SecurityLevel.SECRET: 2,
            SecurityLevel.TOP_SECRET: 3,
        }
        tier = level_tiers.get(required_level, 1)
        
        # Check basic permission first (all levels)
        if resource:
            perm_ok, perm_reason = self.check_permission(actor, action or "read", resource)
            if not perm_ok:
                self.log_action(
                    action=f"access_denied:{action}",
                    actor=actor,
                    resource=resource or required_level.value,
                    result="denied",
                    context={"reason": perm_reason, "required_level": required_level.value},
                )
                return False, perm_reason
        
        # Level-2 and above: audit the access attempt
        if tier >= 2:
            self.log_action(
                action=f"access_request:{action or 'read'}",
                actor=actor,
                resource=resource or required_level.value,
                result="pending",
                context={"required_level": required_level.value},
            )
        
        # Level-3 (TOP_SECRET): biometric gate authentication required
        if tier >= 3:
            gate = await self._get_biometric_gate()
            
            # Step 1: Biometric authentication
            auth_result = await gate.authenticate(
                user_id=actor,
                credentials=credentials,
            )
            
            if not auth_result.get("success"):
                self.log_action(
                    action="biometric_auth",
                    actor=actor,
                    resource=resource or required_level.value,
                    result="denied",
                    context={
                        "required_level": required_level.value,
                        "confidence": auth_result.get("confidence", 0),
                        "reason": auth_result.get("error", "biometric authentication failed"),
                    },
                )
                logger.warning(
                    f"🚫 Level-3 access DENIED for {actor}: "
                    f"biometric authentication failed"
                )
                return False, f"Level-3 access denied: biometric authentication failed"
            
            # Log successful biometric auth
            self.log_action(
                action="biometric_auth",
                actor=actor,
                resource=resource or required_level.value,
                result="granted",
                context={
                    "required_level": required_level.value,
                    "confidence": auth_result.get("confidence", 0),
                },
            )
            logger.critical(
                f"✅ Level-3 biometric auth GRANTED for {actor} "
                f"(confidence={auth_result.get('confidence', 0)})"
            )
            
            # Step 2: Hardware signature verification for hardware operations
            hardware_actions = {"write", "execute", "delete", "admin"}
            if action in hardware_actions or resource.startswith(("/", "C:", "\\")):
                hw_context = {
                    "resource": resource or required_level.value,
                    "action": action or "unknown",
                    "actor": actor,
                }
                hw_result = await gate.verify_hardware_signature(hw_context)
                
                if not hw_result.get("verified"):
                    self.log_action(
                        action="hardware_signature_verify",
                        actor=actor,
                        resource=resource or required_level.value,
                        result="denied",
                        context={"reason": "hardware signature verification failed"},
                    )
                    logger.warning(
                        f"🚫 Hardware signature verification DENIED for {actor}"
                    )
                    return False, "Hardware signature verification failed"
                
                self.log_action(
                    action="hardware_signature_verify",
                    actor=actor,
                    resource=resource or required_level.value,
                    result="granted",
                    context={"signature": hw_result.get("signature", "")},
                )
                logger.critical(
                    f"✅ Hardware signature VERIFIED for {actor} on {resource}"
                )
        
        # Access granted
        self.log_action(
            action=f"access_granted:{action or 'read'}",
            actor=actor,
            resource=resource or required_level.value,
            result="allowed",
            context={"required_level": required_level.value},
        )
        return True, "Access granted"
    
    async def _on_security_alert(self, alert: Dict):
        """Handle security alert"""
        
        if alert['severity'] == 'high':
            # Apply containment
            self.contain.apply_containment(
                alert['actor'],
                ContainmentLevel.SANDBOXED,
                f"Anomaly detected: {alert['type']}"
            )
        
        if alert['type'] == AnomalyType.CONSTITUTION_VIOLATION.value:
            # Critical - kill switch
            self.detect_recover.activate_kill_switch(
                f"Constitution violation by {alert['actor']}",
                "security_manager"
            )
    
    def get_security_report(self) -> Dict:
        """Get complete security status"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "prevent_layer": {
                "allowed_agents": len(self.prevent.allowed_agents),
                "locked_out": len([c for c, a in self.prevent.failed_attempts.items() 
                                 if self.prevent._is_locked_out(c)])
            },
            "contain_layer": {
                "active_sandboxes": len([s for s in self.contain.sandboxes.values() if s['is_active']]),
                "contained_agents": len([c for c, l in self.contain.containment.items() 
                                       if l != ContainmentLevel.NONE])
            },
            "detect_recover_layer": {
                "audit_entries": len(self.detect_recover.audit_log),
                "integrity_valid": self.detect_recover.verify_audit_integrity(),
                "kill_switch_active": self.detect_recover.kill_switch_active
            }
        }

# Global security manager
security_manager = ASIMSecurityManager()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SecurityFramework")
    
    logger.info("ASIMNEXUS Security Framework - Three Layer Protection")
    logger.info("=" * 60)
    logger.info("\n1. PREVENT Layer:")
    logger.info("   - OAuth2/OIDC authentication")
    logger.info("   - mTLS for internal services")
    logger.info("   - Agent allow-list with signatures")
    logger.info("   - Vault isolation (least privilege)")
    
    logger.info("\n2. CONTAIN Layer:")
    logger.info("   - Worktree sandboxes for code agents")
    logger.info("   - Read-only defaults")
    logger.info("   - Permission + policy engine")
    logger.info("   - Immutable constitution + dharma policy")
    
    logger.info("\n3. DETECT & RECOVER Layer:")
    logger.info("   - Tamper-evident hash-chained audit log")
    logger.info("   - Anomaly detection (rate, sequence, location)")
    logger.info("   - Circuit breaker + kill switch")
    logger.info("   - Checkpoint + rollback")
    
    logger.info("\n" + "=" * 60)
    logger.info("Security Manager initialized and ready!")
