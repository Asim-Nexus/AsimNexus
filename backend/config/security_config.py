#!/usr/bin/env python3
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
🔒 ASIMNEXUS Security Configuration
Phase 2: Security & Database Optimization
Backend Hardening with Rate Limiting & API Key Encryption
"""

import os
import hashlib
import secrets
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from cryptography.fernet import Fernet
import redis
import json

@dataclass
class SecurityConfig:
    """Security configuration data structure"""
    api_rate_limit: int = 100  # requests per minute
    session_timeout: int = 3600  # 1 hour
    max_concurrent_connections: int = 1000
    encryption_key_rotation: int = 24  # hours
    allowed_origins: List[str] = None
    jwt_secret: str = None
    redis_config: Dict[str, Any] = None

class SecurityManager:
    """ASIMNEXUS Security Manager - Enterprise-grade Security"""
    
    def __init__(self):
        self.logger = logging.getLogger("ASIMNEXUS_SecurityManager")
        self.config = self._load_security_config()
        self.encryption_key = self._generate_encryption_key()
        self.rate_limiter = {}
        self.active_sessions = {}
        self.redis_client = self._init_redis()
        
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment and defaults"""
        return SecurityConfig(
            api_rate_limit=int(os.getenv('API_RATE_LIMIT', '100')),
            session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600')),
            max_concurrent_connections=int(os.getenv('MAX_CONNECTIONS', '1000')),
            encryption_key_rotation=int(os.getenv('KEY_ROTATION_HOURS', '24')),
            allowed_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
            jwt_secret=os.getenv('JWT_SECRET', None),
            redis_config={
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0')),
                'password': os.getenv('REDIS_PASSWORD', None),
                'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
            }
        )
        
    def _generate_encryption_key(self) -> str:
        """Generate or load encryption key"""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
                self.logger.info("🔑 Loaded existing encryption key")
                return key
        
        # Generate new key
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
            
        self.logger.info("🔑 Generated new encryption key")
        return key
        
    def _init_redis(self):
        """Initialize Redis connection for rate limiting and caching"""
        try:
            config = self.config.redis_config
            if config['password']:
                return redis.Redis(
                    host=config['host'],
                    port=config['port'],
                    db=config['db'],
                    password=config['password'],
                    ssl=config['ssl'],
                    decode_responses=True
                )
            else:
                return redis.Redis(
                    host=config['host'],
                    port=config['port'],
                    db=config['db'],
                    ssl=config['ssl'],
                    decode_responses=True
                )
        except Exception as e:
            self.logger.error(f"🚨 Redis connection failed: {e}")
            return None
            
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            self.logger.error(f"🚨 Encryption failed: {e}")
            return data
            
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"🚨 Decryption failed: {e}")
            return encrypted_data
            
    def check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """Check if client exceeded rate limit"""
        key = f"{client_ip}:{endpoint}"
        current_time = datetime.now()
        
        if key not in self.rate_limiter:
            self.rate_limiter[key] = []
            
        # Clean old requests (older than 1 minute)
        self.rate_limiter[key] = [
            req_time for req_time in self.rate_limiter[key]
            if (current_time - req_time).total_seconds() < 60
        ]
        
        # Check current rate
        if len(self.rate_limiter[key]) >= self.config.api_rate_limit:
            self.logger.warning(f"⚠️ Rate limit exceeded for {client_ip} on {endpoint}")
            return False
            
        # Add current request
        self.rate_limiter[key].append(current_time)
        return True
        
    def create_session(self, user_id: str, client_ip: str) -> str:
        """Create secure user session"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'client_ip': client_ip,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=self.config.session_timeout)).isoformat(),
            'encrypted': True
        }
        
        # Store session
        self.active_sessions[session_id] = session_data
        
        # Cache in Redis
        if self.redis_client:
            self.redis_client.setex(
                f"session:{session_id}",
                json.dumps(session_data),
                self.config.session_timeout
            )
        
        self.logger.info(f"🔐 Created session for user {user_id}")
        return session_id
        
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate and return session data"""
        if session_id not in self.active_sessions:
            return None
            
        session = self.active_sessions[session_id]
        
        # Check expiration
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            del self.active_sessions[session_id]
            if self.redis_client:
                self.redis_client.delete(f"session:{session_id}")
            return None
            
        return session
        
    def revoke_session(self, session_id: str) -> bool:
        """Revoke user session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")
            
        self.logger.info(f"🔐 Revoked session {session_id}")
        return True
        
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'X-ASIMNEXUS-Security': 'Enterprise-Grade',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        }
        
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': self._get_event_severity(event_type)
        }
        
        self.logger.info(f"🔒 Security Event: {event_type} - {details}")
        
        # Store in Redis for analysis
        if self.redis_client:
            self.redis_client.lpush('security_events', json.dumps(event_data))
            self.redis_client.expire('security_events', 86400)  # 24 hours
            
    def _get_event_severity(self, event_type: str) -> str:
        """Get security event severity"""
        severity_map = {
            'rate_limit_exceeded': 'high',
            'session_created': 'info',
            'session_revoked': 'info',
            'authentication_failed': 'high',
            'unauthorized_access': 'critical',
            'encryption_error': 'medium'
        }
        return severity_map.get(event_type, 'info')
        
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        return {
            'active_sessions': len(self.active_sessions),
            'rate_limits': len(self.rate_limiter),
            'redis_connected': self.redis_client is not None,
            'encryption_active': True,
            'security_headers_enabled': True,
            'config': {
                'rate_limit': self.config.api_rate_limit,
                'session_timeout': self.config.session_timeout,
                'max_connections': self.config.max_concurrent_connections
            },
            'timestamp': datetime.now().isoformat()
        }

# Global security manager instance
security_manager = SecurityManager()

if __name__ == "__main__":
    print("🔒 ASIMNEXUS Security Manager Starting...")
    status = security_manager.get_security_status()
    print(f"🛡️ Security Status: {status}")
