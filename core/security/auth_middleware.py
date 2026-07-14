
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Authentication & Authorization Middleware for ASIMNEXUS
Implements JWT-based authentication, RBAC, and session management
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .jwt import create_access_token, create_refresh_token, decode_token
import jwt as pyjwt
import bcrypt
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_active: bool = True

class Token(BaseModel):
    """Token model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token data model"""
    user_id: str
    username: str
    roles: List[str]
    exp: datetime

class AuthManager:
    """
    Authentication and Authorization Manager
    Handles JWT tokens, user authentication, and permission checks
    """
    
    def __init__(self):
        # In-memory user store (replace with database in production)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Role-based access control (RBAC)
        self.role_permissions = {
            "admin": [
                "read", "write", "delete", "manage_users", "manage_systems",
                "api_keys", "founders", "autonomous", "all"
            ],
            "developer": [
                "read", "write", "api_keys", "founders", "autonomous"
            ],
            "user": [
                "read", "chat", "basic_features"
            ],
            "guest": [
                "read", "public_only"
            ]
        }
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_id = "admin_001"
        self.users[admin_id] = {
            "id": admin_id,
            "username": "admin",
            "email": "admin@asimnexus.ai",
            "password_hash": self._hash_password("admin123"),  # Change in production
            "roles": ["admin"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        logger.info("Default admin user created")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token using shared utility"""
        return create_access_token(
            user_id=user.id,
            username=user.username,
            roles=user.roles,
            org_id=getattr(user, "org_id", None),
            permissions=getattr(user, "permissions", []),
            email=user.email,
        )
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token using shared utility"""
        return create_refresh_token(
            user_id=user.id,
            username=user.username,
            roles=user.roles,
            org_id=getattr(user, "org_id", None),
            permissions=getattr(user, "permissions", []),
            email=user.email,
        )
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and validate JWT token using shared utility"""
        return decode_token(token)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        for user_data in self.users.values():
            if user_data["username"] == username:
                if self._verify_password(password, user_data["password_hash"]):
                    if not user_data["is_active"]:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="User account is disabled"
                        )
                    
                    return User(
                        id=user_data["id"],
                        username=user_data["username"],
                        email=user_data["email"],
                        roles=user_data["roles"],
                        permissions=self._get_permissions(user_data["roles"]),
                        is_active=user_data["is_active"]
                    )
        
        return None
    
    def _get_permissions(self, roles: List[str]) -> List[str]:
        """Get all permissions for given roles"""
        permissions = set()
        for role in roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        return list(permissions)
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in user.permissions or "all" in user.permissions
    
    def has_role(self, user: User, role: str) -> bool:
        """Check if user has specific role"""
        return role in user.roles
    
    def create_user(self, username: str, email: str, password: str, roles: List[str]) -> User:
        """Create new user"""
        user_id = f"user_{len(self.users) + 1:04d}"
        
        if username in [u["username"] for u in self.users.values()]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        self.users[user_id] = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "roles": roles,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        return User(
            id=user_id,
            username=username,
            email=email,
            roles=roles,
            permissions=self._get_permissions(roles),
            is_active=True
        )
    
    def login(self, username: str, password: str) -> Token:
        """Login user and return tokens"""
        user = self.authenticate_user(username, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        # Store session
        self.sessions[access_token] = {
            "user_id": user.id,
            "username": user.username,
            "refresh_token": refresh_token,
            "created_at": datetime.now().isoformat()
        }
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        try:
            payload = pyjwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user_id = payload["user_id"]
            username = payload["username"]
            
            if user_id not in self.users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            user_data = self.users[user_id]
            user = User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                roles=user_data["roles"],
                permissions=self._get_permissions(user_data["roles"]),
                is_active=user_data["is_active"]
            )
            
            access_token = self.create_access_token(user)
            new_refresh_token = self.create_refresh_token(user)
            
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        except pyjwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )
    
    def logout(self, access_token: str):
        """Logout user by removing session"""
        if access_token in self.sessions:
            del self.sessions[access_token]


# Global auth manager instance
auth_manager = AuthManager()

# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    token_data = auth_manager.decode_token(token)
    
    user_id = token_data.user_id
    if user_id not in auth_manager.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user_data = auth_manager.users[user_id]
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        roles=user_data["roles"],
        permissions=auth_manager._get_permissions(user_data["roles"]),
        is_active=user_data["is_active"]
    )


# Permission checker decorator
def require_permission(permission: str):
    """Decorator to require specific permission"""
    async def permission_checker(user: User = Depends(get_current_user)):
        if not auth_manager.has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    return permission_checker


# Role checker decorator
def require_role(role: str):
    """Decorator to require specific role"""
    async def role_checker(user: User = Depends(get_current_user)):
        if not auth_manager.has_role(user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return user
    return role_checker


if __name__ == "__main__":
    # Test authentication
    print("Testing Authentication Manager...")
    
    # Test login
    token = auth_manager.login("admin", "admin123")
    print(f"Login successful: {token.access_token[:20]}...")
    
    # Test token decode
    token_data = auth_manager.decode_token(token.access_token)
    print(f"Token data: {token_data}")
    
    # Test permission check
    user = User(
        id="admin_001",
        username="admin",
        email="admin@asimnexus.ai",
        roles=["admin"],
        permissions=auth_manager._get_permissions(["admin"]),
        is_active=True
    )
    print(f"Has 'all' permission: {auth_manager.has_permission(user, 'all')}")
    print(f"Has 'admin' role: {auth_manager.has_role(user, 'admin')}")

from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = [
            # Auth endpoints (must be public so users can log in)
            "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh",
            "/auth/login", "/auth/register", "/auth/me",
            # Health & monitoring
            "/health", "/health/live", "/health/ready", "/health/status",
            "/metrics", "/healthz", "/status",
            # Version / build / status
            "/api/version", "/api/build", "/api/status", "/api/system/complete",
            # Dharma / compliance
            "/api/dharma/status", "/api/compliance/vapt-status",
            # Disaster recovery
            "/api/disaster-recovery/backup", "/api/disaster-recovery/backups", "/api/disaster-recovery/restore",
            # Microkernel / DePIN / Constitution
            "/api/microkernel/status", "/api/depin/stats", "/api/constitution/status",
            # Language
            "/api/language/status", "/api/language/set",
            # Federation
            "/api/federation/status",
            # Marketplace
            "/api/marketplace/apps",
            # AI
            "/api/ai/status",
            # Nepal government data
            "/api/nepal/ministries", "/api/nepal/provinces", "/api/nepal/districts",
            "/api/nepal/gov-layer/status", "/api/nepal/gov-layer/submit",
            # Consensus
            "/api/consensus/vote", "/api/consensus/status",
            # Memory / DB / Sync / Agent / Universe / Personal / DHT / Mesh
            "/api/memory/stats", "/api/db/health", "/api/sync/status",
            "/api/agent/status", "/api/universe/status",
            "/personal/status", "/api/dht/status",
            "/api/mesh/status", "/api/mesh/nodes",
            # Additional public GET endpoints
            "/api/analytics/overview", "/api/analytics/activity",
            "/api/local-llm/health", "/api/v1/operator/status",
            "/api/dreaming/briefing", "/api/dreaming/status",
            "/api/integration/health", "/api/apis/status",
            "/api/universal/status", "/api/universal/countries",
            "/api/universal/currencies", "/api/universal/languages",
            "/api/universal/timezones", "/api/universal/meeting-times",
            "/api/universe/stats", "/api/universe/list",
            "/api/universe/containers",
            "/api/personal/status", "/api/personal/universe",
            "/api/personal/contracts", "/api/personal/resource-sharing",
            "/personal/clones",
            "/api/identity/stats", "/api/identity/list",
            "/api/identity/status",
            "/api/svt/stats", "/api/svt/wallet",
            "/api/hdt/status",
            "/api/quad/status",
            "/api/firewall/status",
            "/api/events/stats", "/api/events/recent", "/api/events/dlq",
            "/api/healing/status", "/api/healing/balance",
            "/api/healing/bugs", "/api/healing/connection",
            "/api/government/status", "/api/government/identity/countries",
            "/api/government/eresidency/programs",
            "/api/government/tax/countries",
            "/api/government/signatures/regions",
            "/api/government/stats",
            "/api/finance/status", "/api/finance/exchange-rates",
            "/api/finance/currencies", "/api/finance/banking/regions",
            "/api/finance/stats",
            "/api/consensus/stats", "/api/consensus/list",
            "/api/consensus/pending", "/api/v1/consensus/status",
            "/api/dharma/veto-status", "/api/dharma/production/status",
            "/api/evolution/stats", "/api/depin/status",
            "/api/pq/status",
            "/api/mcp/tools", "/api/mcp/status",
            "/api/os/status", "/api/os/metrics", "/api/os/pending",
            "/api/os/audit", "/api/os/clipboard/status",
            "/api/tools", "/api/tools/list", "/api/tools/pending",
            "/api/tools/audit", "/api/tools/catalog",
            "/api/v1/sandbox/status",
            "/api/clones/specs", "/api/clones",
            "/api/runtime/status", "/api/runtime/principals",
            "/api/runtime/violations",
            "/api/v1/np/ministries", "/api/v1/np/provinces",
            "/api/v1/np/districts", "/api/v1/np/banks",
            "/api/v1/np/isps", "/api/v1/np/palikas",
            "/api/v1/education/universities", "/api/v1/education/schools",
            "/api/v1/health/hospitals",
            "/api/v1/tourism/hotels",
            "/api/v1/mesh/peers", "/api/v1/mesh/status",
            "/api/mesh/air-gap/check", "/api/mesh/discovery/status",
            "/api/mesh/peers", "/api/mesh/nodes/discover",
            "/api/mesh/stats", "/api/mesh/federation/map",
            "/api/sync/queue",
            "/api/dht/find",
            "/api/federation/sync-packet",
            "/api/infrastructure/status",
            "/api/infrastructure/cdn/locations",
            "/api/infrastructure/mesh/status",
            "/api/infrastructure/mesh/nodes",
            "/api/infrastructure/mesh/sovereign-nodes",
            "/api/platform/status", "/api/platform/downloads",
            "/api/marketplace/global-stats", "/api/marketplace/search",
            "/api/marketplace/listings", "/api/marketplace/stats",
            "/api/marketplace/reviews",
            "/api/jobs/stats", "/api/jobs/list",
            "/api/contracts",
            "/api/reputation/stats", "/api/reputation/leaderboard",
            "/api/bridge/stats", "/api/bridge/pools",
            "/api/bridge/transactions", "/api/bridge/fee",
            "/api/hybrid-economy/summary", "/api/hybrid-economy/mode",
            "/api/hybrid-economy/accounts",
            "/api/task-bus/status", "/api/task-bus/agents",
            "/api/task-bus/tasks",
            "/api/sovereignty/airgap/status",
            "/api/sovereignty/airgap/history",
            "/api/sovereignty/countries",
            "/api/sovereignty/report",
            "/api/dharma/influence/status", "/api/dharma/influence/history",
            "/api/dharma/mesh/status", "/api/dharma/veto/config",
            "/api/dharma/veto/pending", "/api/dharma/veto/history",
            "/api/dharma/enforcement/status",
            "/api/compliance/gov-standards", "/api/compliance/security",
            "/api/integration/pending", "/api/integration/veto-stats",
            "/api/integration/audit-log",
            "/api/agent/sessions", "/api/agent/stats",
            "/api/v1/orchestrator/status",
            "/api/user/profile",
            "/api/permissions",
            "/api/memory/recent", "/api/memory/search",
            "/api/quad",
            # Self-awareness / introspection
            "/api/self/knowledge/summary", "/api/self/knowledge/modules",
            "/api/self/knowledge/routes", "/api/self/knowledge/issues",
            "/api/self/scan/status", "/api/self/build/history",
            "/api/self/build/stats", "/api/self/report",
        ]
        if request.url.path in public_paths:
            return await call_next(request)

        # Allow OPTIONS for CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})

        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)  # HSM-aware verification
            # Make sure request.state has user info
            request.state.user = payload
            request.state.user_id = getattr(payload, 'user_id', None)
            request.state.role = getattr(payload, 'roles', [])
            request.state.permissions = getattr(payload, 'permissions', [])
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=403, content={"detail": f"Token verification failed: {str(e)}"})

        return await call_next(request)


