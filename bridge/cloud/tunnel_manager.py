
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Zero-Trust Access System
================================
Cloudflare Tunnel + JWT Authentication
Secure access from anywhere in Nepal
"""

import asyncio
import logging
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import cloudflare
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import jwt
import bcrypt
import ipaddress

logger = logging.getLogger("TunnelManager")

class ZeroTrustTunnelManager:
    """Zero-Trust Access System for ASIMNEXUS"""
    
    def __init__(self):
        self.tunnel_config = {
            "domain": "nexus.asim.com",
            "protocol": "https",
            "port": 443,
            "local_port": 8000,
            "region": "ap-south-1",
            "nepal_mode": True
        }
        
        self.jwt_config = {
            "secret_key": None,
            "algorithm": "HS256",
            "token_expiry": 24,  # hours
            "refresh_expiry": 168  # 7 days
        }
        
        self.nepal_ip_ranges = [
            "202.70.0.0/20",
            "202.79.32.0/20", 
            "202.80.192.0/20",
            "202.94.64.0/20",
            "203.80.16.0/20",
            "210.7.48.0/20",
            "210.87.16.0/20",
            "110.34.0.0/16",
            "111.119.128.0/18",
            "114.130.0.0/16",
            "117.55.192.0/18",
            "122.0.0.0/14",
            "124.40.0.0/16",
            "125.16.0.0/16",
            "175.100.0.0/16",
            "202.0.0.0/15"
        ]
        
        self.active_sessions = {}
        self.access_logs = []
        self.blocked_ips = set()
        self.cloudflare_client = None
        
    async def initialize_zero_trust(self, cloudflare_token: str, jwt_secret: str) -> bool:
        """Initialize Zero-Trust system"""
        try:
            logger.info("🔒 Initializing Zero-Trust Access System...")
            
            # Initialize JWT secret
            self.jwt_config["secret_key"] = jwt_secret
            
            # Initialize Cloudflare client
            self.cloudflare_client = cloudflare.Cloudflare(cloudflare_token)
            
            # Create tunnel configuration
            await self._setup_tunnel_config()
            
            # Initialize Nepal IP whitelisting
            await self._setup_nepal_whitelist()
            
            logger.info("✅ Zero-Trust Access System initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Zero-Trust: {e}")
            return False
    
    async def _setup_tunnel_config(self) -> None:
        """Setup Cloudflare tunnel configuration"""
        tunnel_config = {
            "tunnel": {
                "protocol": "http",
                "credentials-file": "/etc/cloudflared/cert.pem",
                "ingress": [
                    {
                        "hostname": self.tunnel_config["domain"],
                        "service": f"http://localhost:{self.tunnel_config['local_port']}",
                        "originRequest": {
                            "noTLSVerify": True
                        }
                    },
                    {
                        "service": "http_status:404"
                    }
                ]
            }
        }
        
        # Save tunnel configuration
        import os
        os.makedirs("/etc/cloudflared", exist_ok=True)
        
        with open("/etc/cloudflared/config.yml", "w") as f:
            import yaml
            yaml.dump(tunnel_config, f)
        
        logger.info("🔧 Cloudflare tunnel configuration created")
    
    async def _setup_nepal_whitelist(self) -> None:
        """Setup Nepal IP whitelist"""
        nepal_networks = []
        
        for ip_range in self.nepal_ip_ranges:
            try:
                network = ipaddress.ip_network(ip_range)
                nepal_networks.append(network)
            except Exception as e:
                logger.warning(f"⚠️ Invalid Nepal IP range: {ip_range} - {e}")
        
        self.nepal_networks = nepal_networks
        logger.info(f"🇳🇵 Nepal IP whitelist configured with {len(nepal_networks)} networks")
    
    async def create_tunnel(self) -> Dict[str, Any]:
        """Create Cloudflare tunnel"""
        try:
            # Create tunnel via Cloudflare API
            tunnel_data = {
                "name": "asimnexus-tunnel",
                "secret": secrets.token_urlsafe(32),
                "config_src": "cloudflare"
            }
            
            if self.cloudflare_client:
                tunnel = self.cloudflare_client.tunnels.create(data=tunnel_data)
                tunnel_id = tunnel.id
                
                # Create DNS record
                dns_data = {
                    "type": "CNAME",
                    "name": self.tunnel_config["domain"],
                    "content": f"{tunnel_id}.cfargotunnel.com",
                    "ttl": 1
                }
                
                zone = self.cloudflare_client.zones.get(params={"name": "asim.com"})
                if zone:
                    self.cloudflare_client.dns_records.post(zone.id, data=dns_data)
                
                logger.info(f"🌐 Tunnel created: {self.tunnel_config['domain']}")
                return {
                    "success": True,
                    "tunnel_id": tunnel_id,
                    "domain": self.tunnel_config["domain"],
                    "url": f"https://{self.tunnel_config['domain']}"
                }
            else:
                # Fallback: use cloudflared command
                import subprocess
                result = subprocess.run([
                    "cloudflared", "tunnel", "create",
                    "--name", "asimnexus-tunnel",
                    "--secret", secrets.token_urlsafe(32)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    tunnel_info = json.loads(result.stdout)
                    return {
                        "success": True,
                        "tunnel_id": tunnel_info["uuid"],
                        "domain": self.tunnel_config["domain"],
                        "url": f"https://{self.tunnel_config['domain']}"
                    }
                else:
                    raise Exception(f"Cloudflared failed: {result.stderr}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to create tunnel: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_tunnel(self, tunnel_id: str = None) -> bool:
        """Start Cloudflare tunnel"""
        try:
            import subprocess
            
            if tunnel_id:
                # Start specific tunnel
                cmd = [
                    "cloudflared", "tunnel", "run",
                    "--tunnel-id", tunnel_id,
                    "--config", "/etc/cloudflared/config.yml"
                ]
            else:
                # Start default tunnel
                cmd = [
                    "cloudflared", "tunnel", "run",
                    "--config", "/etc/cloudflared/config.yml"
                ]
            
            # Start tunnel in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel to start
            await asyncio.sleep(5)
            
            if process.poll() is None:
                logger.info("🚀 Cloudflare tunnel started successfully")
                return True
            else:
                stdout, stderr = process.communicate()
                raise Exception(f"Tunnel failed to start: {stderr}")
                
        except Exception as e:
            logger.error(f"❌ Failed to start tunnel: {e}")
            return False
    
    async def generate_jwt_token(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Generate JWT token for authenticated user"""
        try:
            # Validate IP is from Nepal (if Nepal mode is enabled)
            if self.tunnel_config["nepal_mode"]:
                if not await self._is_nepal_ip(ip_address):
                    logger.warning(f"🚫 Non-Nepal IP access attempt: {ip_address}")
                    return {"success": False, "error": "Access restricted to Nepal IP addresses"}
            
            # Generate token
            payload = {
                "user_id": user_id,
                "ip_address": ip_address,
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=self.jwt_config["token_expiry"])).isoformat(),
                "nepal_access": self.tunnel_config["nepal_mode"]
            }
            
            token = jwt.encode(
                payload,
                self.jwt_config["secret_key"],
                algorithm=self.jwt_config["algorithm"]
            )
            
            # Log access
            await self._log_access_event("token_generated", user_id, ip_address)
            
            logger.info(f"🔑 JWT token generated for user: {user_id}")
            return {
                "success": True,
                "token": token,
                "expires_in": self.jwt_config["token_expiry"] * 3600,
                "user_id": user_id,
                "nepal_access": self.tunnel_config["nepal_mode"]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate JWT token: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_jwt_token(self, token: str, ip_address: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                return {"success": False, "error": "IP address blocked"}
            
            # Decode token
            payload = jwt.decode(
                token,
                self.jwt_config["secret_key"],
                algorithms=[self.jwt_config["algorithm"]]
            )
            
            # Check token expiry
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                return {"success": False, "error": "Token expired"}
            
            # Validate IP address (if Nepal mode)
            if self.tunnel_config["nepal_mode"]:
                if not await self._is_nepal_ip(ip_address):
                    logger.warning(f"🚫 Invalid IP for token: {ip_address}")
                    return {"success": False, "error": "Access restricted to Nepal IP addresses"}
            
            # Update session
            session_id = f"{payload['user_id']}_{ip_address}"
            self.active_sessions[session_id] = {
                "user_id": payload["user_id"],
                "ip_address": ip_address,
                "last_activity": datetime.utcnow(),
                "token_issued": datetime.fromisoformat(payload["issued_at"])
            }
            
            # Log access
            await self._log_access_event("token_verified", payload["user_id"], ip_address)
            
            logger.info(f"✅ JWT token verified for user: {payload['user_id']}")
            return {
                "success": True,
                "user_id": payload["user_id"],
                "nepal_access": payload.get("nepal_access", False),
                "session_id": session_id
            }
            
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}
        except Exception as e:
            logger.error(f"❌ Failed to verify JWT token: {e}")
            return {"success": False, "error": str(e)}
    
    async def _is_nepal_ip(self, ip_address: str) -> bool:
        """Check if IP address is from Nepal"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for network in self.nepal_networks:
                if ip in network:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking Nepal IP: {e}")
            return False
    
    async def block_ip_address(self, ip_address: str, reason: str = "Security violation") -> bool:
        """Block IP address"""
        try:
            self.blocked_ips.add(ip_address)
            
            # Remove active sessions for this IP
            sessions_to_remove = []
            for session_id, session_data in self.active_sessions.items():
                if session_data["ip_address"] == ip_address:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            # Log blocking event
            await self._log_access_event("ip_blocked", "system", ip_address, reason)
            
            logger.warning(f"🚫 IP blocked: {ip_address} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to block IP: {e}")
            return False
    
    async def _log_access_event(self, event_type: str, user_id: str, ip_address: str, details: str = None) -> None:
        """Log access event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "nepal_access": self.tunnel_config["nepal_mode"]
        }
        
        self.access_logs.append(event)
        
        # Keep only last 1000 events
        if len(self.access_logs) > 1000:
            self.access_logs = self.access_logs[-1000:]
    
    async def get_tunnel_status(self) -> Dict[str, Any]:
        """Get current tunnel status"""
        try:
            # Check if tunnel is running
            import subprocess
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared"],
                capture_output=True,
                text=True
            )
            
            tunnel_running = result.returncode == 0
            
            return {
                "tunnel_running": tunnel_running,
                "domain": self.tunnel_config["domain"],
                "nepal_mode": self.tunnel_config["nepal_mode"],
                "active_sessions": len(self.active_sessions),
                "blocked_ips": len(self.blocked_ips),
                "access_events_24h": len([
                    log for log in self.access_logs
                    if datetime.fromisoformat(log["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
                ]),
                "nepal_networks": len(self.nepal_networks)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get tunnel status: {e}")
            return {"error": str(e)}
    
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

# Global Zero-Trust tunnel manager
_zero_trust_manager = ZeroTrustTunnelManager()

async def main():
    """Main entry point for testing"""
    # Initialize Zero-Trust system
    success = await _zero_trust_manager.initialize_zero_trust(
        "your-cloudflare-token",
        "your-super-secret-jwt-key-2024"
    )
    print(f"Zero-Trust initialization: {success}")
    
    if success:
        # Create tunnel
        tunnel_result = await _zero_trust_manager.create_tunnel()
        print(f"Tunnel creation: {tunnel_result}")
        
        # Generate JWT token
        token_result = await _zero_trust_manager.generate_jwt_token(
            "founder_user",
            "202.70.0.1"  # Nepal IP
        )
        print(f"JWT token: {token_result}")
        
        # Get tunnel status
        status = await _zero_trust_manager.get_tunnel_status()
        print(f"Tunnel status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
