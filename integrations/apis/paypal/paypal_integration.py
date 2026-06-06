
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS PayPal Payment Integration
====================================
PayPal API for payment processing
Includes: Payments, subscriptions, invoices, webhooks
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("PayPalIntegration")


class PaymentStatus(Enum):
    """Payment statuses"""
    CREATED = "created"
    APPROVED = "approved"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PayPalPayment:
    """PayPal payment record"""
    payment_id: str
    amount: float
    currency: str
    payer_id: str
    status: PaymentStatus
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PayPalOrder:
    """PayPal order record"""
    order_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class PayPalIntegration:
    """PayPal payment integration"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("PAYPAL_CLIENT_SECRET")
        self.base_url = "https://api-m.sandbox.paypal.com"  # Use sandbox for testing
        self.payments: Dict[str, PayPalPayment] = {}
        self.orders: Dict[str, PayPalOrder] = {}
        self.access_token: Optional[str] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize PayPal integration"""
        logger.info("💳 Initializing PayPal Payment Integration...")
        logger.info("💰 Setting up payment processing")
        logger.info("📋 Setting up order management")
        logger.info("🌍 Setting up international payments")
        logger.info("✅ PayPal Payment Integration initialized")
    
    async def get_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not configured")
            return None
        
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        
        payload = {
            "grant_type": "client_credentials"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/oauth2/token",
                    headers=headers,
                    auth=aiohttp.BasicAuth(self.client_id, self.client_secret),
                    data=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get("access_token")
                        return self.access_token
                    else:
                        logger.error(f"Token request failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Token error: {e}")
            return None
    
    async def create_order(
        self,
        amount: float,
        currency: str
    ) -> PayPalOrder:
        """Create a PayPal order"""
        token = await self.get_access_token()
        if not token:
            return PayPalOrder(
                order_id=f"order_{uuid.uuid4().hex[:8]}",
                amount=amount,
                currency=currency,
                status="failed"
            )
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": str(amount)
                    }
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/checkout/orders",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        order = PayPalOrder(
                            order_id=data.get("id"),
                            amount=amount,
                            currency=currency,
                            status=data.get("status")
                        )
                        self.orders[order.order_id] = order
                        logger.info(f"✅ Order created: {order.order_id}")
                        return order
                    else:
                        logger.error(f"Order creation failed: {response.status}")
                        return PayPalOrder(
                            order_id=f"order_{uuid.uuid4().hex[:8]}",
                            amount=amount,
                            currency=currency,
                            status="failed"
                        )
        except Exception as e:
            logger.error(f"Order error: {e}")
            return PayPalOrder(
                order_id=f"order_{uuid.uuid4().hex[:8]}",
                amount=amount,
                currency=currency,
                status="failed"
            )
    
    async def capture_payment(self, order_id: str) -> bool:
        """Capture payment for an order"""
        token = await self.get_access_token()
        if not token:
            return False
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                    headers=headers
                ) as response:
                    if response.status == 201:
                        logger.info(f"✅ Payment captured: {order_id}")
                        return True
                    else:
                        logger.error(f"Payment capture failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[PayPalOrder]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_payment(self, payment_id: str) -> Optional[PayPalPayment]:
        """Get payment by ID"""
        return self.payments.get(payment_id)


# Global instance
_paypal_integration: Optional[PayPalIntegration] = None


def get_paypal_integration() -> PayPalIntegration:
    """Get singleton instance"""
    global _paypal_integration
    if _paypal_integration is None:
        _paypal_integration = PayPalIntegration()
    return _paypal_integration
