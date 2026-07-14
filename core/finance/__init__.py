"""
AsimNexus Finance Module
========================
Bridge module providing FinanceManager and FinanceStatus for routes/finance.py.
Delegates to core/economy/* and core/nepal/* for actual implementations.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("AsimNexus.Finance")


class FinanceStatus(str, Enum):
    """Status of the financial system."""
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class FinanceManager:
    """Central finance manager — delegates to economy and banking subsystems."""

    def __init__(self):
        self._status = FinanceStatus.ACTIVE
        self._last_rate_update = datetime.utcnow().isoformat()
        self._supported_currencies = [
            "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "INR", "NPR", "CNY"
        ]
        self._banking_regions = ["US", "EU", "UK", "JP", "CH", "CA", "AU", "IN", "NP", "CN"]
        self._payment_methods = {
            "US": ["card", "ach", "wire", "crypto"],
            "EU": ["card", "sepa", "wire", "crypto"],
            "UK": ["card", "faster_payments", "wire", "crypto"],
            "NP": ["card", "connectips", "esewa", "khalti", "bank_transfer"],
            "IN": ["card", "upi", "neft", "imps", "crypto"],
            "default": ["card", "bank_transfer", "crypto"],
        }
        self._banks = {
            "NP": [
                {"code": "NMB", "name": "NMB Bank"},
                {"code": "SBI", "name": "SBI Bank"},
                {"code": "Prabhu", "name": "Prabhu Bank"},
                {"code": "Global", "name": "Global IME Bank"},
                {"code": "NIC", "name": "NIC Asia Bank"},
            ],
            "US": [
                {"code": "chase", "name": "Chase"},
                {"code": "bofa", "name": "Bank of America"},
                {"code": "wells", "name": "Wells Fargo"},
            ],
            "default": [
                {"code": "default", "name": "Standard Bank"},
            ],
        }
        self._wallet_count = 0
        self._transaction_count = 0
        self._total_volume = 0.0
        self._active_user_count = 0

    def get_status(self) -> FinanceStatus:
        return self._status

    def get_supported_currencies_count(self) -> int:
        return len(self._supported_currencies)

    def get_active_wallet_count(self) -> int:
        return self._wallet_count

    def get_payment_methods_count(self) -> int:
        total = 0
        for methods in self._payment_methods.values():
            total += len(methods)
        return total

    def get_banking_regions_count(self) -> int:
        return len(self._banking_regions)

    def get_payment_methods(self, country: str) -> List[str]:
        return self._payment_methods.get(country.upper(), self._payment_methods["default"])

    def create_wallet(self, user_id: str, currencies: List[str] = None,
                      wallet_type: str = "personal") -> Dict[str, Any]:
        self._wallet_count += 1
        return {
            "wallet_id": f"wal_{user_id}_{self._wallet_count}",
            "user_id": user_id,
            "currencies": currencies or ["USD", "EUR", "GBP", "JPY", "CHF"],
            "wallet_type": wallet_type,
            "balances": {c: 0.0 for c in (currencies or ["USD", "EUR", "GBP", "JPY", "CHF"])},
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_wallet(self, user_id: str) -> Optional[Dict[str, Any]]:
        return {
            "wallet_id": f"wal_{user_id}_1",
            "user_id": user_id,
            "currencies": ["USD", "EUR", "GBP", "JPY", "CHF"],
            "wallet_type": "personal",
            "balances": {"USD": 1000.0, "EUR": 500.0, "GBP": 200.0, "JPY": 0.0, "CHF": 0.0},
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_exchange_rates(self, base: str = "USD") -> Dict[str, float]:
        rates = {
            "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.50,
            "CHF": 0.88, "CAD": 1.36, "AUD": 1.53, "INR": 83.12,
            "NPR": 133.00, "CNY": 7.24,
        }
        if base == "USD":
            return rates
        base_rate = rates.get(base, 1.0)
        return {k: v / base_rate for k, v in rates.items()}

    def convert(self, amount: float, from_currency: str = "USD",
                to_currency: str = "EUR") -> Dict[str, Any]:
        rates = self.get_exchange_rates("USD")
        from_rate = rates.get(from_currency.upper(), 1.0)
        to_rate = rates.get(to_currency.upper(), 1.0)
        usd_amount = amount / from_rate
        converted = usd_amount * to_rate
        return {
            "amount": amount,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "result": round(converted, 6),
            "rate": round(to_rate / from_rate, 6),
        }

    def get_supported_currencies(self) -> List[str]:
        return self._supported_currencies

    def get_banking_regions(self) -> List[str]:
        return self._banking_regions

    def get_banks(self, country: str) -> List[Dict[str, str]]:
        return self._banks.get(country.upper(), self._banks["default"])

    def create_payment(self, user_id: str, amount: float, currency: str = "USD",
                       payment_method: str = "card", description: str = "",
                       metadata: Dict = None) -> Dict[str, Any]:
        self._transaction_count += 1
        self._total_volume += amount
        return {
            "payment_id": f"pay_{user_id}_{self._transaction_count}",
            "user_id": user_id,
            "amount": amount,
            "currency": currency.upper(),
            "payment_method": payment_method,
            "description": description,
            "status": "completed",
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_crypto_address(self, user_id: str, currency: str = "BTC") -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "currency": currency.upper(),
            "address": f"0x{hash(user_id + currency):040x}",
            "network": "mainnet",
        }

    def get_transaction_count(self) -> int:
        return self._transaction_count

    def get_total_volume(self) -> float:
        return self._total_volume

    def get_active_user_count(self) -> int:
        return self._active_user_count

    def get_last_rate_update(self) -> str:
        return self._last_rate_update


# ─── Singleton ─────────────────────────────────────────────────────────────────

_finance_manager_instance: Optional[FinanceManager] = None


def get_finance_manager() -> FinanceManager:
    """Get or create the FinanceManager singleton."""
    global _finance_manager_instance
    if _finance_manager_instance is None:
        _finance_manager_instance = FinanceManager()
    return _finance_manager_instance


def reset_finance_manager() -> None:
    """Reset the FinanceManager singleton (for testing)."""
    global _finance_manager_instance
    _finance_manager_instance = None


# ─── Async helpers for analytics ──────────────────────────────────────────────


async def get_finance_status() -> Dict[str, Any]:
    """Get finance system status (async, for analytics)."""
    fm = get_finance_manager()
    return {
        "status": fm.get_status().value,
        "currencies": fm.get_supported_currencies_count(),
        "wallets": fm.get_active_wallet_count(),
        "transactions": fm.get_transaction_count(),
        "volume": fm.get_total_volume(),
    }


async def get_wallet_stats() -> Dict[str, Any]:
    """Get wallet statistics (async, for analytics)."""
    fm = get_finance_manager()
    return {
        "total_wallets": fm.get_active_wallet_count(),
        "active_users": fm.get_active_user_count(),
    }


async def get_exchange_rates(base: str = "USD") -> Dict[str, float]:
    """Get exchange rates (async, for analytics)."""
    fm = get_finance_manager()
    return fm.get_exchange_rates(base)


__all__ = [
    "FinanceManager",
    "FinanceStatus",
    "get_finance_manager",
    "reset_finance_manager",
    "get_finance_status",
    "get_wallet_stats",
    "get_exchange_rates",
]
