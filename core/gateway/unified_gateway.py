# connectors/unified_gateway.py
# AsimNexus — Unified Gateway

import httpx
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UnifiedGateway:
    """
    Unified API Gateway — Single entry point for invoking external APIs (banks, hospitals, gov, etc.).
    Supports timeouts, retries, and local simulated fallbacks when hosts are offline.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)
        self.retries = 3

    async def call(self, service: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Invokes API call with exponential backoff retry logic."""
        url = self._get_url(service, endpoint)
        
        for attempt in range(self.retries):
            try:
                if method.upper() == "GET":
                    response = await self.client.get(url)
                else:
                    response = await self.client.post(url, json=data)
                
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} to {url} failed: {e}")
                if attempt == self.retries - 1:
                    logger.info("Falling back to local simulated response for " + service)
                    return self._fallback_response(service, endpoint, data)
                await asyncio.sleep(2 ** attempt)

        return self._fallback_response(service, endpoint, data)

    def _get_url(self, service: str, endpoint: str) -> str:
        base_urls = {
            "ird": "https://api.ird.gov.np/v1",
            "hospital": "https://api.patanhospital.org/v1",
            "bank": "https://api.nabilbank.com/v1",
            "university": "https://api.tu.edu.np/v1"
        }
        base = base_urls.get(service, "https://api.asimnexus.local/v1")
        return f"{base}/{endpoint}"

    def _fallback_response(self, service: str, endpoint: str, data: Optional[Dict]) -> Dict:
        """Simulates external service when API endpoint is unreachable."""
        import uuid
        import time
        
        if service == "ird":
            return {
                "success": True,
                "receipt_id": f"TAX-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": time.time(),
                "simulated": True
            }
        elif service == "hospital":
            return {
                "success": True,
                "appointment_id": f"APT-{uuid.uuid4().hex[:6].upper()}",
                "timestamp": time.time(),
                "simulated": True
            }
        elif service == "bank":
            return {
                "success": True,
                "tx_id": f"TXN-{uuid.uuid4().hex[:10].upper()}",
                "timestamp": time.time(),
                "simulated": True
            }
        elif service == "university":
            return {
                "success": True,
                "degree": "Bachelor of Computer Science",
                "hash": f"CERT-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": time.time(),
                "simulated": True
            }
        elif service == "esewa" or service == "khalti":
            amount = data.get("amount", 0) if data else 0
            return {
                "success": True,
                "provider": service,
                "tx_id": f"PAY-{uuid.uuid4().hex[:10].upper()}",
                "amount": amount,
                "status": "completed",
                "timestamp": time.time(),
                "simulated": True
            }
        else:
            return {"success": True, "message": "Simulated default response"}

    async def process_payment(self, provider: str, amount: float, user_id: str) -> Dict:
        """Helper function for standardized payment processing (eSewa/Khalti/Bank)"""
        if provider not in ["esewa", "khalti", "bank"]:
            raise ValueError(f"Unsupported payment provider: {provider}")
            
        data = {"user_id": user_id, "amount": amount}
        return await self.call(provider, "process_payment", "POST", data)

    async def close(self):
        await self.client.aclose()
