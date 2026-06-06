
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Nexus Cloud Tunnel
=============================
Cloudflare Tunnel Integration for Global Access
Secure Public URL for Local ASIMNEXUS Instance
"""

import asyncio
import logging
import json
import subprocess
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import websockets

logger = logging.getLogger("CloudflareTunnel")

class CloudflareTunnelManager:
    """Manages Cloudflare Tunnel for secure global access"""
    
    def __init__(self):
        self.tunnel_id = None
        self.tunnel_token = None
        self.public_url = None
        self.tunnel_status = "inactive"
        self.config = {
            "account_tag": None,
            "tunnel_name": "asimnexus-global",
            "domain": "nexus.asim.com",  # Your custom domain
            "local_port": 3000,  # Frontend port
            "api_port": 8000,    # Backend API port
            "ws_port": 8000,     # WebSocket port
            "whitelist_ips": [
                # Nepal IP ranges for security
                "202.70.0.0/16",
                "110.44.0.0/16", 
                "49.244.0.0/16",
                # Add your specific IPs
                "YOUR_HOME_IP",
                "YOUR_MOBILE_IP"
            ]
        }
        
    async def initialize_tunnel(self, cloudflare_token: str) -> Dict[str, Any]:
        """Initialize Cloudflare Tunnel"""
        try:
            logger.info("🌐 Initializing Cloudflare Tunnel...")
            
            # Store token
            self.tunnel_token = cloudflare_token
            
            # Create tunnel configuration
            tunnel_config = {
                "account_tag": await self._get_account_tag(cloudflare_token),
                "tunnel_name": self.config["tunnel_name"],
                "config_src": "cloudflare"
            }
            
            # Create tunnel
            result = await self._create_tunnel(cloudflare_token, tunnel_config)
            
            if result["success"]:
                self.tunnel_id = result["tunnel_id"]
                self.tunnel_status = "created"
                
                # Configure DNS
                await self._configure_dns(cloudflare_token, result["tunnel_id"])
                
                # Start tunnel
                await self._start_tunnel()
                
                return {
                    "success": True,
                    "tunnel_id": self.tunnel_id,
                    "public_url": self.public_url,
                    "status": self.tunnel_status
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"❌ Tunnel initialization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_account_tag(self, token: str) -> str:
        """Get Cloudflare account tag"""
        headers = {"Authorization": f"Bearer {token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["result"]["id"]
                else:
                    raise Exception("Failed to verify Cloudflare token")
    
    async def _create_tunnel(self, token: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Cloudflare tunnel"""
        headers = {"Authorization": f"Bearer {token}"}
        
        tunnel_data = {
            "name": config["tunnel_name"],
            "config_src": config["config_src"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.cloudflare.com/client/v4/accounts/{config['account_tag']}/tunnels",
                headers=headers,
                json=tunnel_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tunnel_id": data["result"]["id"],
                        "tunnel_token": data["result"]["token"]
                    }
                else:
                    error_data = await response.json()
                    return {"success": False, "error": error_data.get("errors", "Unknown error")}
    
    async def _configure_dns(self, token: str, tunnel_id: str) -> bool:
        """Configure DNS for tunnel"""
        headers = {"Authorization": f"Bearer {token}"}
        
        dns_data = {
            "type": "CNAME",
            "name": self.config["domain"],
            "content": f"{tunnel_id}.cfargotunnel.com",
            "ttl": 120,
            "proxied": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records",
                headers=headers,
                json=dns_data
            ) as response:
                return response.status == 200
    
    async def _start_tunnel(self) -> bool:
        """Start Cloudflare tunnel daemon"""
        try:
            # Create tunnel configuration file
            config_file = "/tmp/cloudflared-config.yml"
            config_content = f"""
tunnel: {self.tunnel_id}
credentials-file: /tmp/cloudflared-credentials.json

ingress:
  - hostname: {self.config['domain']}
    service: http://localhost:{self.config['local_port']}
  - hostname: {self.config['domain']}
    path: /api
    service: http://localhost:{self.config['api_port']}
  - hostname: {self.config['domain']}
    path: /ws
    service: http://localhost:{self.config['ws_port']}
  - service: http_status:404
"""
            
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Start cloudflared daemon
            process = subprocess.Popen([
                "cloudflared", "tunnel", "run",
                "--config", config_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for tunnel to start
            await asyncio.sleep(5)
            
            if process.poll() is None:
                self.tunnel_status = "active"
                self.public_url = f"https://{self.config['domain']}"
                logger.info(f"✅ Tunnel active at: {self.public_url}")
                return True
            else:
                self.tunnel_status = "failed"
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start tunnel: {e}")
            self.tunnel_status = "failed"
            return False
    
    async def get_tunnel_status(self) -> Dict[str, Any]:
        """Get current tunnel status"""
        return {
            "tunnel_id": self.tunnel_id,
            "status": self.tunnel_status,
            "public_url": self.public_url,
            "domain": self.config["domain"],
            "local_ports": {
                "frontend": self.config["local_port"],
                "api": self.config["api_port"],
                "websocket": self.config["ws_port"]
            },
            "whitelist_ips": self.config["whitelist_ips"],
            "last_check": datetime.now().isoformat()
        }
    
    async def add_whitelist_ip(self, ip_address: str) -> bool:
        """Add IP to whitelist"""
        if ip_address not in self.config["whitelist_ips"]:
            self.config["whitelist_ips"].append(ip_address)
            logger.info(f"🔒 Added {ip_address} to whitelist")
            return True
        return False
    
    async def remove_whitelist_ip(self, ip_address: str) -> bool:
        """Remove IP from whitelist"""
        if ip_address in self.config["whitelist_ips"]:
            self.config["whitelist_ips"].remove(ip_address)
            logger.info(f"🔓 Removed {ip_address} from whitelist")
            return True
        return False
    
    async def stop_tunnel(self) -> bool:
        """Stop Cloudflare tunnel"""
        try:
            # Kill cloudflared process
            subprocess.run(["pkill", "-f", "cloudflared"], check=False)
            
            self.tunnel_status = "stopped"
            self.public_url = None
            
            logger.info("🛑 Cloudflare tunnel stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop tunnel: {e}")
            return False
    
    async def update_domain(self, new_domain: str) -> bool:
        """Update tunnel domain"""
        try:
            old_domain = self.config["domain"]
            self.config["domain"] = new_domain
            
            # Reconfigure DNS
            if self.tunnel_token and self.tunnel_id:
                await self._configure_dns(self.tunnel_token, self.tunnel_id)
            
            logger.info(f"🔄 Domain updated: {old_domain} → {new_domain}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update domain: {e}")
            return False

# Global tunnel manager instance
_tunnel_manager = CloudflareTunnelManager()

async def main():
    """Main entry point for testing"""
    # Example usage
    result = await _tunnel_manager.initialize_tunnel("your-cloudflare-token")
    print(f"Tunnel result: {result}")
    
    status = await _tunnel_manager.get_tunnel_status()
    print(f"Tunnel status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
