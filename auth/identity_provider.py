
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Identity Provider
==========================
JWT-based authentication system
Secure access for 15 founder clones
"""

import asyncio
import logging
import json
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import jwt
import bcrypt
from cryptography.fernet import Fernet

logger = logging.getLogger("IdentityProvider")

class ASIMNexusIdentityProvider:
    """Identity Provider for ASIMNEXUS"""
    
    def __init__(self):
        self.jwt_config = {
            "secret_key": os.getenv("ASIM_JWT_SECRET", None),
            "algorithm": "HS256",
            "token_expiry": int(os.getenv("ASIM_TOKEN_EXPIRY_HOURS", "24")),  # hours
            "refresh_expiry": int(os.getenv("ASIM_REFRESH_EXPIRY_HOURS", "168")),  # 7 days
            "issuer": "asimnexus",
            "audience": "founder-clones"
        }
        
        self.founder_clones = {
            "founder_01": {
                "name": "Founder Prime",
                "role": "admin",
                "permissions": ["all"],
                "created": "2024-01-01",
                "status": "active",
                "last_access": None
            },
            "founder_02": {
                "name": "Founder Alpha",
                "role": "operator", 
                "permissions": ["read", "write", "execute"],
                "created": "2024-01-02",
                "status": "active",
                "last_access": None
            },
            "founder_03": {
                "name": "Founder Beta",
                "role": "operator",
                "permissions": ["read", "write", "execute"],
                "created": "2024-01-03",
                "status": "active",
                "last_access": None
            },
            "founder_04": {
                "name": "Founder Gamma",
                "role": "analyst",
                "permissions": ["read", "analyze"],
                "created": "2024-01-04",
                "status": "active",
                "last_access": None
            },
            "founder_05": {
                "name": "Founder Delta",
                "role": "analyst",
                "permissions": ["read", "analyze"],
                "created": "2024-01-05",
                "status": "active",
                "last_access": None
            },
            "founder_06": {
                "name": "Founder Epsilon",
                "role": "monitor",
                "permissions": ["read", "monitor"],
                "created": "2024-01-06",
                "status": "active",
                "last_access": None
            },
            "founder_07": {
                "name": "Founder Zeta",
                "role": "monitor",
                "permissions": ["read", "monitor"],
                "created": "2024-01-07",
                "status": "active",
                "last_access": None
            },
            "founder_08": {
                "name": "Founder Eta",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-08",
                "status": "active",
                "last_access": None
            },
            "founder_09": {
                "name": "Founder Theta",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-09",
                "status": "active",
                "last_access": None
            },
            "founder_10": {
                "name": "Founder Iota",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-10",
                "status": "active",
                "last_access": None
            },
            "founder_11": {
                "name": "Founder Kappa",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-11",
                "status": "active",
                "last_access": None
            },
            "founder_12": {
                "name": "Founder Lambda",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-12",
                "status": "active",
                "last_access": None
            },
            "founder_13": {
                "name": "Founder Mu",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-13",
                "status": "active",
                "last_access": None
            },
            "founder_14": {
                "name": "Founder Nu",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-14",
                "status": "active",
                "last_access": None
            },
            "founder_15": {
                "name": "Founder Xi",
                "role": "agent",
                "permissions": ["execute", "monitor"],
                "created": "2024-01-15",
                "status": "active",
                "last_access": None
            }
        }
        
        self.active_sessions = {}
        self.access_logs = []
        self.failed_attempts = {}
        self.encryption_key = None
        
    async def initialize_identity_provider(self, jwt_secret: str) -> bool:
        """Initialize identity provider"""
        try:
            logger.info("🔐 Initializing ASIMNEXUS Identity Provider...")
            
            # Set JWT secret
            self.jwt_config["secret_key"] = jwt_secret
            
            # Generate encryption key
            self.encryption_key = Fernet.generate_key()
            
            # Initialize founder clone passwords
            await self._initialize_clone_passwords()
            
            logger.info("✅ Identity Provider initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Identity Provider: {e}")
            return False
    
    async def _initialize_clone_passwords(self) -> None:
        """Initialize passwords for founder clones"""
        # Default passwords (should be changed in production)
        default_passwords = {
            "founder_01": "NexusPrime2024!",
            "founder_02": "NexusAlpha2024!",
            "founder_03": "NexusBeta2024!",
            "founder_04": "NexusGamma2024!",
            "founder_05": "NexusDelta2024!",
            "founder_06": "NexusEpsilon2024!",
            "founder_07": "NexusZeta2024!",
            "founder_08": "NexusEta2024!",
            "founder_09": "NexusTheta2024!",
            "founder_10": "NexusIota2024!",
            "founder_11": "NexusKappa2024!",
            "founder_12": "NexusLambda2024!",
            "founder_13": "NexusMu2024!",
            "founder_14": "NexusNu2024!",
            "founder_15": "NexusXi2024!"
        }
        
        for clone_id, password in default_passwords.items():
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.founder_clones[clone_id]["password_hash"] = hashed_password
    
    async def authenticate_clone(self, clone_id: str, password: str, ip_address: str) -> Dict[str, Any]:
        """Authenticate founder clone"""
        try:
            # Check if clone exists
            if clone_id not in self.founder_clones:
                await self._log_failed_attempt(clone_id, ip_address, "Invalid clone ID")
                return {"success": False, "error": "Invalid clone ID"}
            
            # Check if clone is active
            if self.founder_clones[clone_id]["status"] != "active":
                await self._log_failed_attempt(clone_id, ip_address, "Clone not active")
                return {"success": False, "error": "Clone not active"}
            
            # Check failed attempts
            if await self._is_rate_limited(clone_id, ip_address):
                return {"success": False, "error": "Too many failed attempts. Try again later."}
            
            # Verify password
            stored_hash = self.founder_clones[clone_id].get("password_hash")
            if stored_hash and bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                # Authentication successful
                token = await self._generate_jwt_token(clone_id, ip_address)
                
                # Update last access
                self.founder_clones[clone_id]["last_access"] = datetime.utcnow().isoformat()
                
                # Clear failed attempts
                if clone_id in self.failed_attempts:
                    del self.failed_attempts[clone_id]
                
                await self._log_access_event("login_success", clone_id, ip_address)
                
                logger.info(f"✅ Clone authenticated: {clone_id}")
                return {
                    "success": True,
                    "token": token,
                    "clone_info": {
                        "id": clone_id,
                        "name": self.founder_clones[clone_id]["name"],
                        "role": self.founder_clones[clone_id]["role"],
                        "permissions": self.founder_clones[clone_id]["permissions"]
                    }
                }
            else:
                # Authentication failed
                await self._log_failed_attempt(clone_id, ip_address, "Invalid password")
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    async def _generate_jwt_token(self, clone_id: str, ip_address: str) -> str:
        """Generate JWT token for authenticated clone"""
        clone_info = self.founder_clones[clone_id]
        
        payload = {
            "clone_id": clone_id,
            "clone_name": clone_info["name"],
            "role": clone_info["role"],
            "permissions": clone_info["permissions"],
            "ip_address": ip_address,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_config["token_expiry"]),
            "iss": self.jwt_config["issuer"],
            "aud": self.jwt_config["audience"]
        }
        
        token = jwt.encode(
            payload,
            self.jwt_config["secret_key"],
            algorithm=self.jwt_config["algorithm"]
        )
        
        # Store session
        session_id = f"{clone_id}_{ip_address}_{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        self.active_sessions[session_id] = {
            "clone_id": clone_id,
            "ip_address": ip_address,
            "token": token,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "permissions": clone_info["permissions"]
        }
        
        return token
    
    async def verify_jwt_token(self, token: str, ip_address: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.jwt_config["secret_key"],
                algorithms=[self.jwt_config["algorithm"]],
                audience=self.jwt_config["audience"],
                issuer=self.jwt_config["issuer"]
            )
            
            # Check if session exists
            session_id = f"{payload['clone_id']}_{ip_address}_{hashlib.sha256(token.encode()).hexdigest()[:16]}"
            
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            # Update last activity
            session["last_activity"] = datetime.utcnow()
            
            await self._log_access_event("token_verified", payload["clone_id"], ip_address)
            
            return {
                "success": True,
                "clone_id": payload["clone_id"],
                "clone_name": payload["clone_name"],
                "role": payload["role"],
                "permissions": payload["permissions"],
                "session_id": session_id
            }
            
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"success": False, "error": f"Invalid token: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Token verification error: {e}")
            return {"success": False, "error": "Token verification failed"}
    
    async def _is_rate_limited(self, clone_id: str, ip_address: str) -> bool:
        """Check if clone is rate limited"""
        key = f"{clone_id}_{ip_address}"
        
        if key not in self.failed_attempts:
            return False
        
        failed_data = self.failed_attempts[key]
        
        # Check if there are 5+ failed attempts in last 15 minutes
        recent_attempts = [
            attempt for attempt in failed_data["attempts"]
            if datetime.fromisoformat(attempt["timestamp"]) > datetime.utcnow() - timedelta(minutes=15)
        ]
        
        return len(recent_attempts) >= 5
    
    async def _log_failed_attempt(self, clone_id: str, ip_address: str, reason: str) -> None:
        """Log failed authentication attempt"""
        key = f"{clone_id}_{ip_address}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {"attempts": []}
        
        self.failed_attempts[key]["attempts"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        })
        
        # Keep only last 20 attempts
        if len(self.failed_attempts[key]["attempts"]) > 20:
            self.failed_attempts[key]["attempts"] = self.failed_attempts[key]["attempts"][-20:]
        
        await self._log_access_event("login_failed", clone_id, ip_address, reason)
    
    async def _log_access_event(self, event_type: str, clone_id: str, ip_address: str, details: str = None) -> None:
        """Log access event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "clone_id": clone_id,
            "ip_address": ip_address,
            "details": details
        }
        
        self.access_logs.append(event)
        
        # Keep only last 1000 events
        if len(self.access_logs) > 1000:
            self.access_logs = self.access_logs[-1000:]
    
    async def get_clone_status(self, clone_id: str) -> Dict[str, Any]:
        """Get status of specific clone"""
        try:
            if clone_id not in self.founder_clones:
                return {"success": False, "error": "Clone not found"}
            
            clone_info = self.founder_clones[clone_id].copy()
            
            # Check if clone has active session
            active_sessions = [
                session for session in self.active_sessions.values()
                if session["clone_id"] == clone_id
            ]
            
            clone_info["active_sessions"] = len(active_sessions)
            clone_info["last_access"] = clone_info.get("last_access", "Never")
            
            return {"success": True, "clone_info": clone_info}
            
        except Exception as e:
            logger.error(f"❌ Failed to get clone status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_all_clones_status(self) -> Dict[str, Any]:
        """Get status of all founder clones"""
        try:
            clones_status = {}
            
            for clone_id in self.founder_clones:
                status_result = await self.get_clone_status(clone_id)
                if status_result["success"]:
                    clones_status[clone_id] = status_result["clone_info"]
            
            return {
                "success": True,
                "total_clones": len(self.founder_clones),
                "active_clones": len([c for c in self.founder_clones.values() if c["status"] == "active"]),
                "clones": clones_status,
                "active_sessions": len(self.active_sessions)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get all clones status: {e}")
            return {"success": False, "error": str(e)}
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke specific session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                await self._log_access_event("session_revoked", session["clone_id"], session["ip_address"])
                del self.active_sessions[session_id]
                logger.info(f"🔒 Session revoked: {session_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to revoke session: {e}")
            return False
    
    async def revoke_all_sessions(self, clone_id: str) -> int:
        """Revoke all sessions for a clone"""
        try:
            sessions_to_revoke = []
            
            for session_id, session_data in self.active_sessions.items():
                if session_data["clone_id"] == clone_id:
                    sessions_to_revoke.append(session_id)
            
            for session_id in sessions_to_revoke:
                await self.revoke_session(session_id)
            
            logger.info(f"🔒 Revoked {len(sessions_to_revoke)} sessions for clone: {clone_id}")
            return len(sessions_to_revoke)
            
        except Exception as e:
            logger.error(f"❌ Failed to revoke all sessions: {e}")
            return 0
    
    async def update_clone_permissions(self, clone_id: str, permissions: List[str]) -> bool:
        """Update clone permissions (admin only)"""
        try:
            if clone_id not in self.founder_clones:
                return False
            
            self.founder_clones[clone_id]["permissions"] = permissions
            
            # Update active sessions
            for session_data in self.active_sessions.values():
                if session_data["clone_id"] == clone_id:
                    session_data["permissions"] = permissions
            
            logger.info(f"🔐 Updated permissions for clone: {clone_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update clone permissions: {e}")
            return False
    
    async def get_access_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get access logs for specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            recent_logs = [
                log for log in self.access_logs
                if datetime.fromisoformat(log["timestamp"]) > cutoff_time
            ]
            
            return recent_logs
            
        except Exception as e:
            logger.error(f"❌ Failed to get access logs: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            expired_sessions = []
            cutoff_time = datetime.utcnow() - timedelta(hours=self.jwt_config["token_expiry"])
            
            for session_id, session_data in self.active_sessions.items():
                if session_data["last_activity"] < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup sessions: {e}")
            return 0

# Global identity provider
_identity_provider = ASIMNexusIdentityProvider()

async def main():
    """Main entry point for testing"""
    # Initialize identity provider
    success = await _identity_provider.initialize_identity_provider("asimnexus-super-secret-jwt-key-2024")
    print(f"Identity provider initialization: {success}")
    
    if success:
        # Test authentication
        auth_result = await _identity_provider.authenticate_clone(
            "founder_01",
            "NexusPrime2024!",
            "202.70.0.1"
        )
        print(f"Authentication result: {auth_result}")
        
        # Get all clones status
        status = await _identity_provider.get_all_clones_status()
        print(f"All clones status: {len(status.get('clones', {}))}")

if __name__ == "__main__":
    asyncio.run(main())
