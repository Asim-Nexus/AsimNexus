"""
Nepal Banking Integrations
==========================
Supported payment gateways and financial services in Nepal.

Key providers:
    - eSewa (esewa.com.np)
    - Khalti (khalti.com)
    - ConnectIPS (connectips.com)
    - NIBL Ace Pay
    - Prabhu Pay
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("AsimNexus.Nepal.Banking")

_SUPPORTED_METHODS = {
    "esewa": {
        "name": "eSewa",
        "type": "digital_wallet",
        "currencies": ["NPR"],
        "status": "active",
        "fee_pct": 1.5,
    },
    "khalti": {
        "name": "Khalti",
        "type": "digital_wallet",
        "currencies": ["NPR"],
        "status": "active",
        "fee_pct": 1.0,
    },
    "connectips": {
        "name": "ConnectIPS",
        "type": "bank_transfer",
        "currencies": ["NPR"],
        "status": "active",
        "fee_pct": 0.0,
    },
    "nibl_acepay": {
        "name": "NIBL Ace Pay",
        "type": "mobile_banking",
        "currencies": ["NPR"],
        "status": "active",
        "fee_pct": 0.5,
    },
    "prabhu_pay": {
        "name": "Prabhu Pay",
        "type": "digital_wallet",
        "currencies": ["NPR"],
        "status": "active",
        "fee_pct": 1.2,
    },
    "fonepay": {
        "name": "FonePay",
        "type": "qr_banking",
        "currencies": ["NPR"],
        "status": "active",
        "fee_pct": 0.8,
    },
}


def get_banking_status() -> Dict:
    """Return overall Nepal banking integration status."""
    available = sum(1 for m in _SUPPORTED_METHODS.values() if m["status"] == "active")
    return {
        "country": "Nepal",
        "providers_available": available,
        "total_providers": len(_SUPPORTED_METHODS),
        "providers": list(_SUPPORTED_METHODS.keys()),
        "currencies_supported": ["NPR"],
        "status": "active",
    }


def get_supported_payment_methods() -> List[Dict]:
    """Return list of supported payment methods with details."""
    return list(_SUPPORTED_METHODS.values())


def process_payment(method: str, amount: float, currency: str = "NPR",
                    metadata: Optional[Dict] = None) -> Dict:
    """Simulate processing a payment through a Nepal payment gateway.

    Args:
        method: Payment method key (e.g. "esewa", "khalti")
        amount: Transaction amount
        currency: Currency code (default: NPR)
        metadata: Optional payment metadata

    Returns:
        Transaction result dict.
    """
    method_key = method.lower().replace(" ", "_")
    if method_key not in _SUPPORTED_METHODS:
        return {
            "success": False,
            "error": f"Unsupported payment method: {method}",
            "supported_methods": list(_SUPPORTED_METHODS.keys()),
        }

    provider = _SUPPORTED_METHODS[method_key]
    fee = round(amount * provider["fee_pct"] / 100, 2)
    total = round(amount + fee, 2)

    logger.info(
        "Processing %s payment: NPR %.2f (fee: NPR %.2f, total: NPR %.2f)",
        provider["name"], amount, fee, total,
    )

    return {
        "success": True,
        "provider": provider["name"],
        "amount": amount,
        "currency": currency,
        "fee": fee,
        "total": total,
        "transaction_id": f"NPL-{method_key}-{hash(str(metadata)) % 10**8:08d}",
        "status": "completed",
    }
