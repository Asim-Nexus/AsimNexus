
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Global Identity Lock
=============================
JWT Authentication + IP Whitelisting System
Commercial-grade security for Founder access
"""

import asyncio
import logging
import json
import jwt
import hashlib
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import bcrypt
import aiohttp
from fastapi import HTTPException, status
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets

logger = logging.getLogger("CentralVault")

class GlobalIdentityLock:
    """Central authentication and authorization system"""
    
    def __init__(self):
        self.jwt_secret = None
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_hours = 24
        self.whitelist_ips = set()
        self.founder_sessions = {}
        self.failed_attempts = {}
        self.security_config = {
            "max_failed_attempts": 5,
            "lockout_duration_minutes": 30,
            "session_timeout_hours": 12,
            "require_ip_whitelist": True,
            "enable_2fa": False,
            "nepal_time_zone": "Asia/Kathmandu"
        }
        
        # Pre-configured founder accounts
        self.founder_accounts = {
            "founder_001": {
                "username": "asim_founder",
                "password_hash": None,  # Will be set during initialization
                "email": "founder@asimnexus.com",
                "role": "super_admin",
                "permissions": ["all"],
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            },
            "founder_002": {
                "username": "nexus_clone_01",
                "password_hash": None,
                "email": "clone01@asimnexus.com", 
                "role": "admin",
                "permissions": ["system_control", "agent_management", "monitoring"],
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            }
        }
        
        # Nepal IP ranges for auto-whitelisting
        self.nepal_ip_ranges = [
            "202.70.0.0/16",    # Nepal Telecom
            "110.44.0.0/16",    # WorldLink
            "49.244.0.0/16",    # Ncell
            "202.166.0.0/16",   # Broadlink
            "103.4.0.0/16",     # Vianet
            "202.52.0.0/16",    # ClassicTech
            "203.110.0.0/16"    # Subisu
        ]
        
    async def initialize_vault(self, jwt_secret: str, master_password: str) -> bool:
        """Initialize the central identity vault"""
        try:
            logger.info("🔐 Initializing Global Identity Lock...")
            
            # Set JWT secret
            self.jwt_secret = jwt_secret
            
            # Initialize founder passwords
            await self._initialize_founder_passwords(master_password)
            
            # Auto-whitelist Nepal IP ranges
            await self._auto_whitelist_nepal_ips()
            
            logger.info("✅ Global Identity Lock initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Identity Lock: {e}")
            return False
    
    async def _initialize_founder_passwords(self, master_password: str) -> None:
        """Initialize founder account passwords"""
        # Generate password hashes for founder accounts
        for founder_id, account in self.founder_accounts.items():
            # Use different salts for each account
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(master_password.encode(), salt)
            account["password_hash"] = password_hash.decode()
    
    async def _auto_whitelist_nepal_ips(self) -> None:
        """Auto-whitelist Nepal IP ranges"""
        for ip_range in self.nepal_ip_ranges:
            self.whitelist_ips.add(ip_range)
        
        logger.info(f"🇳🇵 Auto-whitelisted {len(self.nepal_ip_ranges)} Nepal IP ranges")
    
    async def authenticate_founder(self, username: str, password: str, client_ip: str) -> Dict[str, Any]:
        """Authenticate founder credentials"""
        try:
            # Check IP whitelist
            if self.security_config["require_ip_whitelist"]:
                if not await self._is_ip_whitelisted(client_ip):
                    await self._record_failed_attempt(username, client_ip, "ip_not_whitelisted")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="IP address not authorized"
                    )
            
            # Check lockout status
            if await self._is_account_locked(username, client_ip):
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account temporarily locked due to failed attempts"
                )
            
            # Find founder account
            founder_account = None
            for account in self.founder_accounts.values():
                if account["username"] == username and account["active"]:
                    founder_account = account
                    break
            
            if not founder_account:
                await self._record_failed_attempt(username, client_ip, "user_not_found")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not bcrypt.checkpw(password.encode(), founder_account["password_hash"].encode()):
                await self._record_failed_attempt(username, client_ip, "invalid_password")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Clear failed attempts on successful login
            await self._clear_failed_attempts(username, client_ip)
            
            # Generate JWT token
            token = await self._generate_jwt_token(founder_account, client_ip)
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            session_data = {
                "founder_id": next(k for k, v in self.founder_accounts.items() if v["username"] == username),
                "username": username,
                "client_ip": client_ip,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "active": True
            }
            
            self.founder_sessions[session_id] = session_data
            
            # Update last login
            founder_account["last_login"] = datetime.now().isoformat()
            
            logger.info(f"🔓 Founder authenticated: {username} from {client_ip}")
            
            return {
                "success": True,
                "token": token,
                "session_id": session_id,
                "user_info": {
                    "username": username,
                    "role": founder_account["role"],
                    "permissions": founder_account["permissions"],
                    "expires_at": (datetime.now() + timedelta(hours=self.jwt_expiry_hours)).isoformat()
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable"
            )
    
    async def _is_ip_whitelisted(self, client_ip: str) -> bool:
        """Check if IP is in whitelist"""
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for ip_range in self.whitelist_ips:
                if "/" in ip_range:
                    network = ipaddress.ip_network(ip_range)
                    if client_addr in network:
                        return True
                else:
                    if str(client_addr) == ip_range:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ IP whitelist check error: {e}")
            return False
    
    async def _is_account_locked(self, username: str, client_ip: str) -> bool:
        """Check if account is locked due to failed attempts"""
        lockout_key = f"{username}:{client_ip}"
        
        if lockout_key in self.failed_attempts:
            attempts = self.failed_attempts[lockout_key]
            if attempts["count"] >= self.security_config["max_failed_attempts"]:
                lockout_time = datetime.fromisoformat(attempts["last_attempt"])
                lockout_duration = timedelta(minutes=self.security_config["lockout_duration_minutes"])
                
                if datetime.now() < lockout_time + lockout_duration:
                    return True
                else:
                    # Lockout expired, clear attempts
                    del self.failed_attempts[lockout_key]
        
        return False
    
    async def _record_failed_attempt(self, username: str, client_ip: str, reason: str) -> None:
        """Record failed authentication attempt"""
        lockout_key = f"{username}:{client_ip}"
        
        if lockout_key not in self.failed_attempts:
            self.failed_attempts[lockout_key] = {
                "count": 0,
                "first_attempt": datetime.now().isoformat(),
                "last_attempt": datetime.now().isoformat(),
                "reasons": []
            }
        
        self.failed_attempts[lockout_key]["count"] += 1
        self.failed_attempts[lockout_key]["last_attempt"] = datetime.now().isoformat()
        self.failed_attempts[lockout_key]["reasons"].append({
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        logger.warning(f"🚨 Failed attempt #{self.failed_attempts[lockout_key]['count']} for {username} from {client_ip}: {reason}")
    
    async def _clear_failed_attempts(self, username: str, client_ip: str) -> None:
        """Clear failed authentication attempts"""
        lockout_key = f"{username}:{client_ip}"
        if lockout_key in self.failed_attempts:
            del self.failed_attempts[lockout_key]
    
    async def _generate_jwt_token(self, founder_account: Dict[str, Any], client_ip: str) -> str:
        """Generate JWT token for authenticated founder"""
        payload = {
            "sub": founder_account["username"],
            "role": founder_account["role"],
            "permissions": founder_account["permissions"],
            "client_ip": client_ip,
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(hours=self.jwt_expiry_hours),
            "jti": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    async def verify_token(self, token: str, client_ip: str) -> Dict[str, Any]:
        """Verify JWT token and return user info"""
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if token is expired
            if datetime.now() > datetime.fromisoformat(payload["exp"].replace("Z", "+00:00")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            # Verify client IP matches
            if payload["client_ip"] != client_ip:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token IP mismatch"
                )
            
            # Check if session is still active
            session_found = False
            for session_id, session_data in self.founder_sessions.items():
                if (session_data["username"] == payload["sub"] and 
                    session_data["client_ip"] == client_ip and
                    session_data["active"]):
                    
                    # Update last activity
                    session_data["last_activity"] = datetime.now().isoformat()
                    session_found = True
                    break
            
            if not session_found:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session not found or inactive"
                )
            
            return {
                "valid": True,
                "username": payload["sub"],
                "role": payload["role"],
                "permissions": payload["permissions"]
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token verification failed"
            )
    
    async def logout_founder(self, session_id: str) -> bool:
        """Logout founder and invalidate session"""
        try:
            if session_id in self.founder_sessions:
                session_data = self.founder_sessions[session_id]
                session_data["active"] = False
                del self.founder_sessions[session_id]
                
                logger.info(f"🔒 Founder logged out: {session_data['username']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Logout error: {e}")
            return False
    
    async def add_whitelist_ip(self, ip_address: str, description: str = "") -> bool:
        """Add IP address to whitelist"""
        try:
            # Validate IP address
            ipaddress.ip_address(ip_address)
            
            self.whitelist_ips.add(ip_address)
            
            logger.info(f"🔓 Added IP to whitelist: {ip_address} ({description})")
            return True
            
        except ValueError:
            logger.error(f"❌ Invalid IP address: {ip_address}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to add IP to whitelist: {e}")
            return False
    
    async def remove_whitelist_ip(self, ip_address: str) -> bool:
        """Remove IP address from whitelist"""
        try:
            if ip_address in self.whitelist_ips:
                self.whitelist_ips.remove(ip_address)
                logger.info(f"🔒 Removed IP from whitelist: {ip_address}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to remove IP from whitelist: {e}")
            return False
    
    async def get_whitelist_ips(self) -> List[Dict[str, str]]:
        """Get all whitelisted IPs"""
        return [
            {"ip": ip, "type": "range" if "/" in ip else "single"}
            for ip in sorted(self.whitelist_ips)
        ]
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active founder sessions"""
        active_sessions = []
        
        for session_id, session_data in self.founder_sessions.items():
            if session_data["active"]:
                # Check if session has timed out
                last_activity = datetime.fromisoformat(session_data["last_activity"])
                timeout = timedelta(hours=self.security_config["session_timeout_hours"])
                
                if datetime.now() < last_activity + timeout:
                    active_sessions.append({
                        "session_id": session_id,
                        "username": session_data["username"],
                        "client_ip": session_data["client_ip"],
                        "created_at": session_data["created_at"],
                        "last_activity": session_data["last_activity"],
                        "expires_at": (last_activity + timeout).isoformat()
                    })
                else:
                    # Session expired, deactivate
                    session_data["active"] = False
        
        return active_sessions
    
    async def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            "active_sessions": len(await self.get_active_sessions()),
            "whitelisted_ips": len(self.whitelist_ips),
            "failed_attempts": len(self.failed_attempts),
            "founder_accounts": len([acc for acc in self.founder_accounts.values() if acc["active"]]),
            "security_config": self.security_config,
            "last_updated": datetime.now().isoformat()
        }
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        cleaned_count = 0
        timeout = timedelta(hours=self.security_config["session_timeout_hours"])
        
        for session_id, session_data in list(self.founder_sessions.items()):
            if session_data["active"]:
                last_activity = datetime.fromisoformat(session_data["last_activity"])
                if datetime.now() >= last_activity + timeout:
                    session_data["active"] = False
                    del self.founder_sessions[session_id]
                    cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count
    
    async def create_founder_invite(self, permissions: List[str], expires_hours: int = 24) -> Dict[str, Any]:
        """Create founder invitation token"""
        try:
            invite_token = secrets.token_urlsafe(32)
            invite_data = {
                "token": invite_token,
                "permissions": permissions,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
                "used": False
            }
            
            # Store invite (in production, this would be in a database)
            if not hasattr(self, 'invites'):
                self.invites = {}
            
            self.invites[invite_token] = invite_data
            
            logger.info(f"📧 Created founder invite: {invite_token[:8]}...")
            return invite_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create invite: {e}")
            return {"success": False, "error": str(e)}

# Global identity lock instance
_identity_lock = GlobalIdentityLock()

async def main():
    """Main entry point for testing"""
    # Initialize vault
    success = await _identity_lock.initialize_vault(
        jwt_secret="asimnexus-super-secret-jwt-key-2024",
        master_password="founder123"
    )
    print(f"Identity lock initialization: {success}")
    
    # Test authentication
    try:
        result = await _identity_lock.authenticate_founder(
            username="asim_founder",
            password="founder123",
            client_ip="202.70.1.100"
        )
        print(f"Authentication result: {result}")
        
        # Verify token
        token_result = await _identity_lock.verify_token(result["token"], "202.70.1.100")
        print(f"Token verification: {token_result}")
        
    except Exception as e:
        print(f"Authentication error: {e}")
    
    # Get security stats
    stats = await _identity_lock.get_security_stats()
    print(f"Security stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
