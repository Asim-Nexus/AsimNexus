
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""Role-Based Access Control (RBAC) for ASIMNEXUS."""
from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import secrets


class Role(Enum):
    """User roles with different permission levels."""
    ADMIN = "admin"           # Full system access
    DEVELOPER = "developer"   # Code tools, system access
    USER = "user"             # General usage
    GUEST = "guest"           # Limited access
    RESTRICTED = "restricted" # Read-only, high oversight


class Permission(Enum):
    """System permissions."""
    # Tool permissions
    TOOL_FILE_READ = "tool:file:read"
    TOOL_FILE_WRITE = "tool:file:write"
    TOOL_FILE_DELETE = "tool:file:delete"
    TOOL_SYSTEM_COMMAND = "tool:system:command"
    TOOL_SYSTEM_SCAN = "tool:system:scan"
    TOOL_API_CONNECT = "tool:api:connect"
    TOOL_AGENT_SPAWN = "tool:agent:spawn"
    TOOL_CODE_EXECUTE = "tool:code:execute"
    TOOL_BROWSER_AUTOMATION = "tool:browser:automation"
    TOOL_DB_ACCESS = "tool:db:access"
    
    # Feature permissions
    FEATURE_RAG = "feature:rag"
    FEATURE_MULTI_AGENT = "feature:multi_agent"
    FEATURE_WORKFLOW = "feature:workflow"
    FEATURE_CUSTOM_TOOLS = "feature:custom_tools"
    
    # Admin permissions
    ADMIN_USER_MANAGE = "admin:user_manage"
    ADMIN_SYSTEM_CONFIG = "admin:system_config"
    ADMIN_AUDIT_LOGS = "admin:audit_logs"
    ADMIN_RATE_LIMITS = "admin:rate_limits"


# Role-Permission mappings
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    
    Role.DEVELOPER: {
        Permission.TOOL_FILE_READ,
        Permission.TOOL_FILE_WRITE,
        Permission.TOOL_SYSTEM_COMMAND,
        Permission.TOOL_SYSTEM_SCAN,
        Permission.TOOL_API_CONNECT,
        Permission.TOOL_AGENT_SPAWN,
        Permission.TOOL_CODE_EXECUTE,
        Permission.TOOL_BROWSER_AUTOMATION,
        Permission.TOOL_DB_ACCESS,
        Permission.FEATURE_RAG,
        Permission.FEATURE_MULTI_AGENT,
        Permission.FEATURE_WORKFLOW,
        Permission.FEATURE_CUSTOM_TOOLS,
    },
    
    Role.USER: {
        Permission.TOOL_FILE_READ,
        Permission.TOOL_API_CONNECT,
        Permission.TOOL_AGENT_SPAWN,
        Permission.FEATURE_RAG,
        Permission.FEATURE_WORKFLOW,
    },
    
    Role.GUEST: {
        Permission.TOOL_FILE_READ,
        Permission.FEATURE_RAG,
    },
    
    Role.RESTRICTED: {
        Permission.TOOL_FILE_READ,
        Permission.FEATURE_RAG,
    },
}


@dataclass
class User:
    """User entity with RBAC."""
    user_id: str
    username: str
    email: str
    role: Role
    api_key_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    rate_limit: int = 100  # requests per hour
    permissions_override: Set[Permission] = field(default_factory=set)
    permissions_revoked: Set[Permission] = field(default_factory=set)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        if permission in self.permissions_revoked:
            return False
        if permission in self.permissions_override:
            return True
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def can_use_tool(self, tool_name: str) -> bool:
        """Check if user can use a specific tool."""
        tool_permission_map = {
            "file_read": Permission.TOOL_FILE_READ,
            "file_write": Permission.TOOL_FILE_WRITE,
            "file_delete": Permission.TOOL_FILE_DELETE,
            "execute_command": Permission.TOOL_SYSTEM_COMMAND,
            "system_scan": Permission.TOOL_SYSTEM_SCAN,
            "api_connect": Permission.TOOL_API_CONNECT,
            "agent_spawn": Permission.TOOL_AGENT_SPAWN,
            "browser_automation": Permission.TOOL_BROWSER_AUTOMATION,
            "db_query": Permission.TOOL_DB_ACCESS,
        }
        
        permission = tool_permission_map.get(tool_name)
        if not permission:
            return False
        
        return self.has_permission(permission)
    
    def requires_confirmation(self, tool_name: str) -> bool:
        """Check if tool requires user confirmation."""
        high_risk_tools = {
            "file_delete", "execute_command", "browser_automation",
            "db_query", "api_connect"
        }
        return tool_name in high_risk_tools


class RBACManager:
    """Manage users, roles, and permissions."""
    
    def __init__(self, state_manager=None):
        self.state_manager = state_manager
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, str] = {}  # key_hash -> user_id
        self._load_users()
    
    def _load_users(self):
        """Load users from state manager."""
        if self.state_manager:
            # Load from persistent storage
            pass  # Implementation depends on state_manager interface
    
    def create_user(self, username: str, email: str, role: Role = Role.USER) -> User:
        """Create new user with API key."""
        import uuid
        
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        api_key = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            api_key_hash=api_key_hash,
            created_at=datetime.now()
        )
        
        self.users[user_id] = user
        self.api_keys[api_key_hash] = user_id
        
        # Store API key securely (only returned once)
        return user, api_key
    
    def authenticate(self, api_key: str) -> Optional[User]:
        """Authenticate user by API key."""
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        user_id = self.api_keys.get(api_key_hash)
        
        if user_id and user_id in self.users:
            user = self.users[user_id]
            if user.is_active:
                user.last_login = datetime.now()
                return user
        
        return None
    
    def authorize_tool_use(self, user: User, tool_name: str) -> Dict:
        """Authorize tool usage with checks."""
        can_use = user.can_use_tool(tool_name)
        requires_confirmation = user.requires_confirmation(tool_name)
        
        return {
            "authorized": can_use,
            "requires_confirmation": requires_confirmation,
            "reason": None if can_use else f"Role '{user.role.value}' cannot use tool '{tool_name}'"
        }
    
    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        """Grant additional permission to user."""
        if user_id not in self.users:
            return False
        
        self.users[user_id].permissions_override.add(permission)
        return True
    
    def revoke_permission(self, user_id: str, permission: Permission) -> bool:
        """Revoke permission from user."""
        if user_id not in self.users:
            return False
        
        self.users[user_id].permissions_revoked.add(permission)
        return True
    
    def change_role(self, user_id: str, new_role: Role) -> bool:
        """Change user role."""
        if user_id not in self.users:
            return False
        
        self.users[user_id].role = new_role
        # Clear overrides when changing role
        self.users[user_id].permissions_override.clear()
        self.users[user_id].permissions_revoked.clear()
        return True
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        if user_id not in self.users:
            return False
        
        self.users[user_id].is_active = False
        return True
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for user."""
        if user_id not in self.users:
            return []
        
        user = self.users[user_id]
        permissions = ROLE_PERMISSIONS.get(user.role, set()).copy()
        permissions.update(user.permissions_override)
        permissions.difference_update(user.permissions_revoked)
        
        return [p.value for p in permissions]


class RateLimiter:
    """Rate limiting for users."""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, user: User) -> bool:
        """Check if user can make request."""
        now = datetime.now()
        user_id = user.user_id
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Clean old requests (older than 1 hour)
        cutoff = now - __import__('datetime').timedelta(hours=1)
        self.requests[user_id] = [
            r for r in self.requests[user_id] if r > cutoff
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= user.rate_limit:
            return False
        
        # Record request
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user: User) -> int:
        """Get remaining requests for user."""
        now = datetime.now()
        user_id = user.user_id
        
        if user_id not in self.requests:
            return user.rate_limit
        
        cutoff = now - __import__('datetime').timedelta(hours=1)
        recent = [r for r in self.requests[user_id] if r > cutoff]
        
        return max(0, user.rate_limit - len(recent))


# Permission decorator
def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def decorator(func):
        async def wrapper(self, user: User, *args, **kwargs):
            if not user.has_permission(permission):
                raise PermissionError(f"User lacks permission: {permission.value}")
            return await func(self, user, *args, **kwargs)
        return wrapper
    return decorator


# Global instances
_rbac_manager = None
_rate_limiter = None

def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
