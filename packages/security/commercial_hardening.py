
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Commercial Security Hardening
=======================================
Enterprise-grade security for production deployment
Protects against common vulnerabilities and attacks
"""

import asyncio
import logging
import json
import hashlib
import secrets
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import bcrypt
import re
import ipaddress

logger = logging.getLogger("CommercialSecurity")

class CommercialSecurityHardening:
    """Enterprise-grade security implementation"""
    
    def __init__(self):
        self.encryption_key = None
        self.security_config = {
            "encryption_enabled": True,
            "rate_limiting_enabled": True,
            "input_validation_enabled": True,
            "sql_injection_protection": True,
            "xss_protection": True,
            "csrf_protection": True,
            "security_headers_enabled": True,
            "audit_logging_enabled": True,
            "session_security_enabled": True,
            "file_upload_security": True,
            "api_rate_limits": {
                "default": 100,  # requests per minute
                "auth": 10,      # auth requests per minute
                "admin": 50,     # admin requests per minute
                "api": 1000      # general API requests per minute
            }
        }
        
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
        }
        
        self.blocked_ip_addresses = set()
        self.failed_login_attempts = {}
        self.security_events = []
        self.csrf_tokens = {}
        
    async def initialize_security(self, master_key: str) -> bool:
        """Initialize security systems"""
        try:
            logger.info("🔒 Initializing Commercial Security Hardening...")
            
            # Generate encryption key
            self.encryption_key = self._derive_encryption_key(master_key)
            
            # Load security rules
            await self._load_security_rules()
            
            # Initialize audit logging
            await self._initialize_audit_logging()
            
            logger.info("✅ Commercial Security Hardening initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize security: {e}")
            return False
    
    def _derive_encryption_key(self, master_key: str) -> bytes:
        """Derive encryption key from master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'asimnexus_security_salt_2024',
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(master_key.encode())
        return key
    
    async def _load_security_rules(self) -> None:
        """Load security rules and patterns"""
        # SQL Injection patterns
        self.sql_injection_patterns = [
            r"('|(\\')|(;|(\-\-)|(\s+(or|and)\s+.*\s*=\s*.*)",
            r"(\s+(union|select|insert|update|delete|drop|create|alter|exec|execute)\s)",
            r"(\s+(where|having)\s+.*\s*(=|like|in|between)\s)",
            r"(\/\*.*\*\/)",
            r"(\b(0x[0-9a-fA-F]+)\b)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"(<script[^>]*>.*?</script>)",
            r"(javascript:)",
            r"(on\w+\s*=)",
            r"(<iframe[^>]*>)",
            r"(<object[^>]*>)",
            r"(<embed[^>]*>)",
            r"(<link[^>]*>)",
            r"(<meta[^>]*>)"
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"(\.\./)",
            r"(\.\.\\)",
            r"(%2e%2e%2f)",
            r"(%2e%2e\\)",
            r"(\.\.%2f)",
            r"(\.\.%5c)"
        ]
        
        # Command injection patterns
        self.command_injection_patterns = [
            r"(;|\||&)",
            r"(\$\()",
            r"`[^`]*`",
            r"(\${[^}]*})",
            r"(curl|wget|nc|netcat|telnet)",
            r"(rm|mv|cp|cat|ls|ps|kill)"
        ]
    
    async def _initialize_audit_logging(self) -> None:
        """Initialize audit logging system"""
        self.audit_log = {
            "security_events": [],
            "failed_logins": [],
            "blocked_requests": [],
            "suspicious_activities": [],
            "data_access_logs": []
        }
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            if not self.security_config["encryption_enabled"]:
                return data
            
            fernet = Fernet(Fernet.generate_key())
            encrypted_data = fernet.encrypt(data.encode())
            return encrypted_data.decode()
            
        except Exception as e:
            logger.error(f"❌ Failed to encrypt data: {e}")
            return data
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            if not self.security_config["encryption_enabled"]:
                return encrypted_data
            
            fernet = Fernet(Fernet.generate_key())
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"❌ Failed to decrypt data: {e}")
            return encrypted_data
    
    async def validate_input(self, input_data: str, input_type: str = "general") -> Dict[str, Any]:
        """Validate input against security patterns"""
        try:
            if not self.security_config["input_validation_enabled"]:
                return {"valid": True, "reason": "Validation disabled"}
            
            validation_result = {
                "valid": True,
                "threats_detected": [],
                "sanitized_data": input_data
            }
            
            # Check for SQL injection
            if self.security_config["sql_injection_protection"]:
                for pattern in self.sql_injection_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        validation_result["valid"] = False
                        validation_result["threats_detected"].append("SQL_INJECTION")
                        await self._log_security_event("SQL_INJECTION_ATTEMPT", input_data)
                        break
            
            # Check for XSS
            if self.security_config["xss_protection"]:
                for pattern in self.xss_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        validation_result["valid"] = False
                        validation_result["threats_detected"].append("XSS")
                        await self._log_security_event("XSS_ATTEMPT", input_data)
                        break
            
            # Check for path traversal
            for pattern in self.path_traversal_patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    validation_result["valid"] = False
                    validation_result["threats_detected"].append("PATH_TRAVERSAL")
                    await self._log_security_event("PATH_TRAVERSAL_ATTEMPT", input_data)
                    break
            
            # Check for command injection
            for pattern in self.command_injection_patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    validation_result["valid"] = False
                    validation_result["threats_detected"].append("COMMAND_INJECTION")
                    await self._log_security_event("COMMAND_INJECTION_ATTEMPT", input_data)
                    break
            
            # Sanitize input if validation passed
            if validation_result["valid"]:
                validation_result["sanitized_data"] = self._sanitize_input(input_data)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Input validation error: {e}")
            return {"valid": False, "reason": str(e)}
    
    def _sanitize_input(self, input_data: str) -> str:
        """Sanitize input data"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'&;]', '', input_data)
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized
    
    async def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        try:
            token = secrets.token_urlsafe(32)
            timestamp = datetime.now().isoformat()
            
            self.csrf_tokens[session_id] = {
                "token": token,
                "timestamp": timestamp,
                "used": False
            }
            
            return token
            
        except Exception as e:
            logger.error(f"❌ Failed to generate CSRF token: {e}")
            return ""
    
    async def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token"""
        try:
            if session_id not in self.csrf_tokens:
                return False
            
            stored_token = self.csrf_tokens[session_id]
            
            # Check if token matches
            if stored_token["token"] != token:
                return False
            
            # Check if token has been used
            if stored_token["used"]:
                return False
            
            # Check token age (1 hour expiry)
            token_time = datetime.fromisoformat(stored_token["timestamp"])
            if datetime.now() - token_time > timedelta(hours=1):
                del self.csrf_tokens[session_id]
                return False
            
            # Mark token as used
            stored_token["used"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ CSRF token validation error: {e}")
            return False
    
    async def check_rate_limit(self, client_ip: str, endpoint: str = "default") -> Dict[str, Any]:
        """Check if client has exceeded rate limits"""
        try:
            if not self.security_config["rate_limiting_enabled"]:
                return {"allowed": True, "remaining": float('inf')}
            
            current_time = datetime.now()
            minute_key = current_time.strftime("%Y%m%d%H%M")
            
            rate_limit_key = f"{client_ip}:{endpoint}:{minute_key}"
            
            if rate_limit_key not in self.failed_login_attempts:
                self.failed_login_attempts[rate_limit_key] = {
                    "count": 0,
                    "first_request": current_time
                }
            
            request_data = self.failed_login_attempts[rate_limit_key]
            request_data["count"] += 1
            
            limit = self.security_config["api_rate_limits"].get(endpoint, 100)
            remaining = max(0, limit - request_data["count"])
            
            if request_data["count"] > limit:
                await self._log_security_event("RATE_LIMIT_EXCEEDED", f"{client_ip}:{endpoint}")
                await self._block_ip_temporarily(client_ip, 300)  # Block for 5 minutes
                return {"allowed": False, "remaining": 0}
            
            return {"allowed": True, "remaining": remaining}
            
        except Exception as e:
            logger.error(f"❌ Rate limiting error: {e}")
            return {"allowed": True, "remaining": float('inf')}
    
    async def _block_ip_temporarily(self, ip_address: str, duration_seconds: int) -> None:
        """Block IP address temporarily"""
        try:
            self.blocked_ip_addresses.add(ip_address)
            
            # Schedule unblock (in production, use a proper job scheduler)
            await asyncio.sleep(duration_seconds)
            self.blocked_ip_addresses.discard(ip_address)
            
            logger.info(f"🔒 IP {ip_address} blocked for {duration_seconds} seconds")
            
        except Exception as e:
            logger.error(f"❌ Failed to block IP: {e}")
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ip_addresses
    
    async def validate_file_upload(self, file_data: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Validate uploaded files for security"""
        try:
            if not self.security_config["file_upload_security"]:
                return {"valid": True, "reason": "File validation disabled"}
            
            validation_result = {
                "valid": True,
                "threats_detected": [],
                "file_info": {
                    "size": len(file_data),
                    "filename": filename,
                    "content_type": content_type
                }
            }
            
            # Check file size (max 10MB)
            if len(file_data) > 10 * 1024 * 1024:
                validation_result["valid"] = False
                validation_result["threats_detected"].append("FILE_TOO_LARGE")
                await self._log_security_event("LARGE_FILE_UPLOAD", f"{filename}: {len(file_data)} bytes")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.csv', '.json']
            file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
            
            if f'.{file_extension}' not in allowed_extensions:
                validation_result["valid"] = False
                validation_result["threats_detected"].append("INVALID_FILE_TYPE")
                await self._log_security_event("INVALID_FILE_TYPE", filename)
            
            # Check for malicious content in file
            file_content = file_data.decode('utf-8', errors='ignore')
            
            for pattern in self.xss_patterns + self.command_injection_patterns:
                if re.search(pattern, file_content, re.IGNORECASE):
                    validation_result["valid"] = False
                    validation_result["threats_detected"].append("MALICIOUS_FILE_CONTENT")
                    await self._log_security_event("MALICIOUS_FILE_CONTENT", filename)
                    break
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ File validation error: {e}")
            return {"valid": False, "reason": str(e)}
    
    async def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses"""
        if not self.security_config["security_headers_enabled"]:
            return {}
        
        return self.security_headers.copy()
    
    async def _log_security_event(self, event_type: str, details: str) -> None:
        """Log security event"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details,
                "severity": self._get_event_severity(event_type)
            }
            
            self.security_events.append(event)
            self.audit_log["security_events"].append(event)
            
            # Keep only last 1000 events
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
            
            logger.warning(f"🚨 Security Event: {event_type} - {details}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log security event: {e}")
    
    def _get_event_severity(self, event_type: str) -> str:
        """Get severity level for event type"""
        high_severity_events = [
            "SQL_INJECTION_ATTEMPT",
            "XSS_ATTEMPT", 
            "COMMAND_INJECTION_ATTEMPT",
            "MALICIOUS_FILE_CONTENT",
            "RATE_LIMIT_EXCEEDED"
        ]
        
        return "HIGH" if event_type in high_severity_events else "MEDIUM"
    
    async def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        try:
            current_time = datetime.now()
            last_24h = current_time - timedelta(hours=24)
            
            recent_events = [
                event for event in self.security_events
                if datetime.fromisoformat(event["timestamp"]) > last_24h
            ]
            
            high_severity_events = [
                event for event in recent_events
                if event["severity"] == "HIGH"
            ]
            
            event_types = {}
            for event in recent_events:
                event_type = event["event_type"]
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            return {
                "report_timestamp": current_time.isoformat(),
                "security_config": self.security_config,
                "blocked_ips": len(self.blocked_ip_addresses),
                "csrf_tokens_active": len(self.csrf_tokens),
                "events_last_24h": len(recent_events),
                "high_severity_events": len(high_severity_events),
                "event_types": event_types,
                "most_common_threat": max(event_types.items(), key=lambda x: x[1])[0] if event_types else None,
                "security_score": self._calculate_security_score(recent_events),
                "recommendations": self._generate_security_recommendations(recent_events)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate security report: {e}")
            return {"error": str(e)}
    
    def _calculate_security_score(self, events: List[Dict[str, Any]]) -> int:
        """Calculate security score (0-100)"""
        try:
            base_score = 100
            
            # Deduct points for security events
            for event in events:
                if event["severity"] == "HIGH":
                    base_score -= 5
                else:
                    base_score -= 1
            
            return max(0, base_score)
            
        except Exception:
            return 50
    
    def _generate_security_recommendations(self, events: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on events"""
        recommendations = []
        
        event_types = [event["event_type"] for event in events]
        
        if "SQL_INJECTION_ATTEMPT" in event_types:
            recommendations.append("Consider implementing additional SQL injection protection")
        
        if "XSS_ATTEMPT" in event_types:
            recommendations.append("Review and strengthen XSS protection measures")
        
        if "RATE_LIMIT_EXCEEDED" in event_types:
            recommendations.append("Consider tightening rate limits for vulnerable endpoints")
        
        if len(events) > 100:
            recommendations.append("High volume of security events detected - consider additional monitoring")
        
        if not recommendations:
            recommendations.append("Security posture looks good - continue monitoring")
        
        return recommendations
    
    async def cleanup_expired_data(self) -> int:
        """Clean up expired security data"""
        try:
            cleaned_count = 0
            
            # Clean up old CSRF tokens
            current_time = datetime.now()
            expired_tokens = []
            
            for session_id, token_data in self.csrf_tokens.items():
                token_time = datetime.fromisoformat(token_data["timestamp"])
                if current_time - token_time > timedelta(hours=1):
                    expired_tokens.append(session_id)
            
            for token_id in expired_tokens:
                del self.csrf_tokens[token_id]
                cleaned_count += 1
            
            # Clean up old rate limit data
            expired_rate_limits = []
            for key, data in self.failed_login_attempts.items():
                if current_time - data["first_request"] > timedelta(hours=1):
                    expired_rate_limits.append(key)
            
            for key in expired_rate_limits:
                del self.failed_login_attempts[key]
                cleaned_count += 1
            
            logger.info(f"🧹 Cleaned up {cleaned_count} expired security data items")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired data: {e}")
            return 0

# Global security instance
_commercial_security = CommercialSecurityHardening()

async def main():
    """Main entry point for testing"""
    # Initialize security
    success = await _commercial_security.initialize_security("master-security-key-2024")
    print(f"Security initialization: {success}")
    
    if success:
        # Test input validation
        result = await _commercial_security.validate_input("'; DROP TABLE users; --", "general")
        print(f"Input validation result: {result}")
        
        # Test CSRF token
        token = await _commercial_security.generate_csrf_token("session123")
        print(f"CSRF token: {token}")
        
        validation = await _commercial_security.validate_csrf_token("session123", token)
        print(f"CSRF validation: {validation}")
        
        # Get security report
        report = await _commercial_security.get_security_report()
        print(f"Security report: {report}")

if __name__ == "__main__":
    asyncio.run(main())
