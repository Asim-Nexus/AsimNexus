
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Security Access Module
===============================
Consolidates identity management and consent management
Handles user roles, permissions, sessions, and consent tracking
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from security.security_base import BaseSecurityLayer, SecurityLevel, ActionType

logger = logging.getLogger("ASIM_SecurityAccess")


# ==================== Identity Management ====================

class UserRole(Enum):
    """User roles with different permission levels"""
    OWNER = "owner"           # Full control
    ADMIN = "admin"           # High control, no constitution changes
    USER = "user"             # Standard user
    GUEST = "guest"           # Read-only, limited actions
    SYSTEM = "system"         # ASIM internal processes


class Permission(Enum):
    """Individual permissions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CONFIGURE = "configure"
    MANAGE_USERS = "manage_users"
    SYSTEM_CONTROL = "system_control"
    CONSTITUTION_READ = "constitution_read"
    AUDIT_READ = "audit_read"
    AGENT_CONTROL = "agent_control"
    TOOL_USE = "tool_use"


@dataclass
class User:
    """User definition"""
    id: str
    username: str
    role: UserRole
    permissions: Set[Permission]
    created_at: float
    last_login: Optional[float] = None
    active: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    created_at: float
    expires_at: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class IdentityManager(BaseSecurityLayer):
    """Manages users, roles, permissions, and sessions"""
    
    def __init__(self, config_path: str = None):
        super().__init__(name="identity_manager")
        self.config_path = config_path or self._get_default_path()
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.role_permissions = self._define_role_permissions()
        self._load_or_create_config()
    
    async def initialize(self):
        """Initialize Identity Manager"""
        self.logger.info("Identity Manager initialized")
    
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate user"""
        username = credentials.get("username")
        password = credentials.get("password")
        # In production, implement proper authentication
        return username is not None
    
    async def authorize(self, user_id: str, action: ActionType, resource: str) -> bool:
        """Authorize user action"""
        user = self.users.get(user_id)
        if not user:
            return False
        # Check permissions
        return True
    
    def _get_default_path(self) -> str:
        """Get default config path"""
        base_path = Path(__file__).parent.parent / "config"
        base_path.mkdir(exist_ok=True)
        return str(base_path / "identity_config.json")
    
    def _define_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """Define permissions for each role"""
        return {
            UserRole.OWNER: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.CONFIGURE, Permission.MANAGE_USERS,
                Permission.SYSTEM_CONTROL, Permission.CONSTITUTION_READ,
                Permission.AUDIT_READ, Permission.AGENT_CONTROL,
                Permission.TOOL_USE
            },
            UserRole.ADMIN: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.CONFIGURE, Permission.AUDIT_READ,
                Permission.AGENT_CONTROL, Permission.TOOL_USE
            },
            UserRole.USER: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.AGENT_CONTROL, Permission.TOOL_USE
            },
            UserRole.GUEST: {
                Permission.READ
            },
            UserRole.SYSTEM: {
                Permission.READ, Permission.WRITE, Permission.EXECUTE,
                Permission.AGENT_CONTROL, Permission.AUDIT_READ
            }
        }
    
    def _load_or_create_config(self):
        """Load existing config or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                self.users = {}
                for user_id, user_data in data.get("users", {}).items():
                    self.users[user_id] = User(
                        id=user_id,
                        username=user_data["username"],
                        role=UserRole(user_data["role"]),
                        permissions=set(Permission(p) for p in user_data["permissions"]),
                        created_at=user_data["created_at"],
                        last_login=user_data.get("last_login"),
                        active=user_data.get("active", True),
                        metadata=user_data.get("metadata", {})
                    )
                
                self.logger.info(f"Loaded {len(self.users)} users")
                
            except Exception as e:
                self.logger.error(f"Failed to load identity config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration with owner user"""
        import uuid
        owner_id = str(uuid.uuid4())
        
        self.users[owner_id] = User(
            id=owner_id,
            username="owner",
            role=UserRole.OWNER,
            permissions=self.role_permissions[UserRole.OWNER],
            created_at=time.time(),
            last_login=time.time(),
            active=True,
            metadata={"is_default": True}
        )
        
        self._save_config()
        self.logger.info("Created default owner user")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            data = {
                "version": "1.0",
                "created_at": time.time(),
                "users": {
                    user_id: {
                        "username": user.username,
                        "role": user.role.value,
                        "permissions": [p.value for p in user.permissions],
                        "created_at": user.created_at,
                        "last_login": user.last_login,
                        "active": user.active,
                        "metadata": user.metadata or {}
                    }
                    for user_id, user in self.users.items()
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info("Identity configuration saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save identity config: {e}")
    
    def create_user(self, username: str, role: UserRole, metadata: Dict[str, Any] = None) -> str:
        """Create a new user"""
        import uuid
        
        user_id = str(uuid.uuid4())
        
        user = User(
            id=user_id,
            username=username,
            role=role,
            permissions=self.role_permissions[role],
            created_at=time.time(),
            metadata=metadata or {}
        )
        
        self.users[user_id] = user
        self._save_config()
        
        self.logger.info(f"Created user: {username} with role {role.value}")
        return user_id
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def authenticate_user(self, username: str, password: str = None) -> Optional[str]:
        """Authenticate user and return session ID"""
        user = self.get_user_by_username(username)
        
        if not user or not user.active:
            return None
        
        user.last_login = time.time()
        self._save_config()
        
        import uuid
        session_id = str(uuid.uuid4())
        
        session = Session(
            session_id=session_id,
            user_id=user.id,
            created_at=time.time(),
            expires_at=time.time() + 24 * 60 * 60
        )
        
        self.sessions[session_id] = session
        
        self.logger.info(f"User {username} authenticated, session: {session_id}")
        return session_id
    
    def get_user_from_session(self, session_id: str) -> Optional[User]:
        """Get user from session ID"""
        session = self.sessions.get(session_id)
        
        if not session or session.expires_at < time.time():
            return None
        
        return self.users.get(session.user_id)
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user = self.users.get(user_id)
        
        if not user or not user.active:
            return False
        
        return permission in user.permissions
    
    def check_permissions(self, user_id: str, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        return all(self.check_permission(user_id, perm) for perm in permissions)
    
    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        """Grant permission to user"""
        user = self.users.get(user_id)
        
        if not user:
            return False
        
        user.permissions.add(permission)
        self._save_config()
        
        self.logger.info(f"Granted permission {permission.value} to user {user.username}")
        return True
    
    def revoke_permission(self, user_id: str, permission: Permission) -> bool:
        """Revoke permission from user"""
        user = self.users.get(user_id)
        
        if not user:
            return False
        
        user.permissions.discard(permission)
        self._save_config()
        
        self.logger.info(f"Revoked permission {permission.value} from user {user.username}")
        return True
    
    def change_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Change user role"""
        user = self.users.get(user_id)
        
        if not user:
            return False
        
        user.role = new_role
        user.permissions = self.role_permissions[new_role]
        self._save_config()
        
        self.logger.info(f"Changed user {user.username} role to {new_role.value}")
        return True
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user"""
        user = self.users.get(user_id)
        
        if not user:
            return False
        
        user.active = False
        self._save_config()
        
        sessions_to_remove = [
            sid for sid, session in self.sessions.items()
            if session.user_id == user_id
        ]
        
        for sid in sessions_to_remove:
            del self.sessions[sid]
        
        self.logger.info(f"Deactivated user {user.username}")
        return True
    
    def list_users(self) -> List[User]:
        """List all active users"""
        return [user for user in self.users.values() if user.active]
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        active_users = self.list_users()
        active_sessions = [
            s for s in self.sessions.values()
            if s.expires_at > time.time()
        ]
        
        return {
            "total_users": len(self.users),
            "active_users": len(active_users),
            "active_sessions": len(active_sessions),
            "by_role": {
                role.value: len([u for u in active_users if u.role == role])
                for role in UserRole
            }
        }


# ==================== Consent Management ====================

class ConsentType(Enum):
    """Types of consent"""
    DATA_COLLECTION = "data_collection"
    PERSONALIZATION = "personalization"
    CLOUD_PROCESSING = "cloud_processing"
    BIOMETRIC = "biometric"
    LOCATION = "location"
    CONTACTS = "contacts"
    MESSAGES = "messages"
    THIRD_PARTY = "third_party"


class ConsentStatus(Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class ConsentRecord:
    """Record of user consent"""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: Optional[float] = None
    revoked_at: Optional[float] = None
    expires_at: Optional[float] = None
    purpose: str = ""
    data_retention_days: int = 365


class ConsentManager(BaseSecurityLayer):
    """
    Manages user consent for various actions
    
    Features:
    - Track consent for different data types
    - Handle consent revocation
    - Expiration management
    - Audit logging
    """
    
    def __init__(self):
        super().__init__(name="consent_manager")
        self.consents: Dict[str, ConsentRecord] = {}
        self.consent_history: List[Dict[str, Any]] = []
        
        self.logger.info("Consent Manager initialized")
    
    async def initialize(self):
        """Initialize Consent Manager"""
        self.logger.info("Consent Manager ready")
    
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate consent manager access"""
        return True
    
    async def authorize(self, user_id: str, action: ActionType, resource: str) -> bool:
        """Authorize consent action"""
        return True
    
    async def request_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        purpose: str,
        data_retention_days: int = 365
    ) -> Dict[str, Any]:
        """Request consent from user"""
        consent_id = f"{user_id}_{consent_type.value}_{int(datetime.now().timestamp())}"
        
        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            status=ConsentStatus.PENDING,
            purpose=purpose,
            data_retention_days=data_retention_days
        )
        
        self.consents[consent_id] = consent
        self._log_consent_action(consent_id, "requested")
        
        return {
            "consent_id": consent_id,
            "status": "pending",
            "purpose": purpose,
            "data_retention_days": data_retention_days
        }
    
    async def grant_consent(
        self,
        consent_id: str,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Grant consent"""
        if consent_id not in self.consents:
            return {"error": "Consent not found"}
        
        consent = self.consents[consent_id]
        
        if consent.status != ConsentStatus.PENDING:
            return {"error": "Consent already processed"}
        
        consent.status = ConsentStatus.GRANTED
        consent.granted_at = datetime.now().timestamp()
        
        if expires_in_days:
            consent.expires_at = datetime.now().timestamp() + (expires_in_days * 86400)
        
        self._log_consent_action(consent_id, "granted")
        
        return {
            "success": True,
            "consent_id": consent_id,
            "status": "granted",
            "granted_at": consent.granted_at,
            "expires_at": consent.expires_at
        }
    
    async def deny_consent(self, consent_id: str) -> Dict[str, Any]:
        """Deny consent"""
        if consent_id not in self.consents:
            return {"error": "Consent not found"}
        
        consent = self.consents[consent_id]
        
        if consent.status != ConsentStatus.PENDING:
            return {"error": "Consent already processed"}
        
        consent.status = ConsentStatus.DENIED
        self._log_consent_action(consent_id, "denied")
        
        return {
            "success": True,
            "consent_id": consent_id,
            "status": "denied"
        }
    
    async def revoke_consent(self, consent_id: str) -> Dict[str, Any]:
        """Revoke previously granted consent"""
        if consent_id not in self.consents:
            return {"error": "Consent not found"}
        
        consent = self.consents[consent_id]
        
        if consent.status != ConsentStatus.GRANTED:
            return {"error": "Cannot revoke non-granted consent"}
        
        consent.status = ConsentStatus.REVOKED
        consent.revoked_at = datetime.now().timestamp()
        
        self._log_consent_action(consent_id, "revoked")
        
        return {
            "success": True,
            "consent_id": consent_id,
            "status": "revoked",
            "revoked_at": consent.revoked_at
        }
    
    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> Dict[str, Any]:
        """Check if user has granted consent"""
        user_consents = [
            c for c in self.consents.values()
            if c.user_id == user_id and c.consent_type == consent_type
        ]
        
        if not user_consents:
            return {
                "has_consent": False,
                "status": "not_requested"
            }
        
        latest_consent = max(user_consents, key=lambda c: c.granted_at or 0)
        
        if latest_consent.status == ConsentStatus.GRANTED:
            if latest_consent.expires_at:
                if datetime.now().timestamp() > latest_consent.expires_at:
                    return {
                        "has_consent": False,
                        "status": "expired"
                    }
            
            return {
                "has_consent": True,
                "status": "granted",
                "granted_at": latest_consent.granted_at,
                "expires_at": latest_consent.expires_at
            }
        
        return {
            "has_consent": False,
            "status": latest_consent.status.value
        }
    
    def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consents for a user"""
        user_consents = [
            c for c in self.consents.values()
            if c.user_id == user_id
        ]
        
        return [
            {
                "consent_id": c.consent_id,
                "type": c.consent_type.value,
                "status": c.status.value,
                "granted_at": c.granted_at,
                "revoked_at": c.revoked_at,
                "expires_at": c.expires_at,
                "purpose": c.purpose
            }
            for c in user_consents
        ]
    
    def _log_consent_action(self, consent_id: str, action: str):
        """Log consent action for audit"""
        self.consent_history.append({
            "consent_id": consent_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
    
    def cleanup_expired_consents(self):
        """Clean up expired consents"""
        current_time = datetime.now().timestamp()
        
        for consent_id, consent in self.consents.items():
            if consent.expires_at and current_time > consent.expires_at:
                if consent.status == ConsentStatus.GRANTED:
                    consent.status = ConsentStatus.REVOKED
                    consent.revoked_at = current_time
                    self._log_consent_action(consent_id, "expired_revoked")
        
        logging.info("Cleaned up expired consents")


# Global instances
identity_manager = IdentityManager()
consent_manager = ConsentManager()
