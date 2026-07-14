"""
AsimNexus Finance Route Module
===============================
Finance, wallet, payments, crypto, banking, and exchange endpoints.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Finance")

router = APIRouter(tags=["Finance"])

# Module-level globals (set via init_finance)
orchestrator = None


def init_finance(app_globals: dict) -> None:
    """Initialize finance module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Finance Status ──────────────────────────────────────────────────────────


@router.get("/api/finance/status")
async def finance_status():
    """Get financial system status"""
    try:
        from core.finance import (
            get_finance_manager, FinanceStatus
        )
        fm = get_finance_manager()
        status = fm.get_status()
        return ok(data={
            "status": status.value if hasattr(status, 'value') else str(status),
            "supported_currencies": fm.get_supported_currencies_count(),
            "active_wallets": fm.get_active_wallet_count(),
            "payment_methods_available": fm.get_payment_methods_count(),
            "banking_regions": fm.get_banking_regions_count()
        })
    except Exception as e:
        logger.error(f"Finance status error: {e}")
        return error(str(e))


@router.get("/api/finance/payment-methods/{country}")
async def payment_methods(country: str):
    """Get payment methods for a country"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        methods = fm.get_payment_methods(country)
        return ok(data={
            "country": country,
            "methods": methods,
            "count": len(methods)
        })
    except Exception as e:
        logger.error(f"Payment methods error: {e}")
        return error(str(e))


# ─── Wallet ──────────────────────────────────────────────────────────────────


@router.post("/api/finance/wallet/create")
async def create_wallet(data: dict = Body(...)):
    """Create a multi-currency wallet for user"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        wallet = fm.create_wallet(
            user_id=data.get("user_id"),
            currencies=data.get("currencies", ["USD", "EUR", "GBP", "JPY", "CHF"]),
            wallet_type=data.get("wallet_type", "personal")
        )
        return ok(data=wallet)
    except Exception as e:
        logger.error(f"Create wallet error: {e}")
        return error(str(e))


@router.get("/api/finance/wallet/{user_id}")
async def get_wallet(user_id: str):
    """Get wallet details"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        wallet = fm.get_wallet(user_id)
        if not wallet:
            return error(f"Wallet not found for user {user_id}")
        return ok(data=wallet)
    except Exception as e:
        logger.error(f"Get wallet error: {e}")
        return error(str(e))


# ─── Exchange Rates ──────────────────────────────────────────────────────────


@router.get("/api/finance/exchange-rates")
async def exchange_rates(base: str = "USD"):
    """Get current exchange rates"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        rates = fm.get_exchange_rates(base)
        return ok(data={
            "base": base,
            "rates": rates,
            "updated": fm.get_last_rate_update()
        })
    except Exception as e:
        logger.error(f"Exchange rates error: {e}")
        return error(str(e))


@router.post("/api/finance/convert")
async def convert_currency(data: dict = Body(...)):
    """Convert between currencies"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        result = fm.convert(
            amount=data.get("amount", 0),
            from_currency=data.get("from", "USD"),
            to_currency=data.get("to", "EUR")
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Currency convert error: {e}")
        return error(str(e))


@router.get("/api/finance/currencies")
async def supported_currencies():
    """Get all supported currencies"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        currencies = fm.get_supported_currencies()
        return ok(data={
            "currencies": currencies,
            "count": len(currencies)
        })
    except Exception as e:
        logger.error(f"Supported currencies error: {e}")
        return error(str(e))


# ─── Banking ─────────────────────────────────────────────────────────────────


@router.get("/api/finance/banking/regions")
async def banking_regions():
    """Get supported banking regions"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        regions = fm.get_banking_regions()
        return ok(data={
            "regions": regions,
            "count": len(regions)
        })
    except Exception as e:
        logger.error(f"Banking regions error: {e}")
        return error(str(e))


@router.get("/api/finance/banking/banks/{country}")
async def get_banks(country: str):
    """Get banks for a country"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        banks = fm.get_banks(country)
        return ok(data={
            "country": country,
            "banks": banks,
            "count": len(banks)
        })
    except Exception as e:
        logger.error(f"Get banks error: {e}")
        return error(str(e))


# ─── Payments ────────────────────────────────────────────────────────────────


@router.post("/api/finance/payment/create")
async def create_payment(data: dict = Body(...)):
    """Create a payment intent"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        payment = fm.create_payment(
            user_id=data.get("user_id"),
            amount=data.get("amount", 0),
            currency=data.get("currency", "USD"),
            payment_method=data.get("payment_method", "card"),
            description=data.get("description", ""),
            metadata=data.get("metadata", {})
        )
        return ok(data=payment)
    except Exception as e:
        logger.error(f"Create payment error: {e}")
        return error(str(e))


# ─── Crypto ──────────────────────────────────────────────────────────────────


@router.post("/api/finance/crypto/address")
async def get_crypto_address(data: dict = Body(...)):
    """Get cryptocurrency receiving address"""
    try:
        from core.finance import get_finance_manager
        fm = get_finance_manager()
        address = fm.get_crypto_address(
            user_id=data.get("user_id"),
            currency=data.get("currency", "BTC")
        )
        return ok(data=address)
    except Exception as e:
        logger.error(f"Crypto address error: {e}")
        return error(str(e))


# ─── Finance Stats ───────────────────────────────────────────────────────────


@router.get("/api/finance/stats")
async def finance_stats():
    """Get comprehensive financial stats"""
    try:
        from core.finance import (
            get_finance_manager, FinanceStatus
        )
        fm = get_finance_manager()
        return ok(data={
            "status": fm.get_status().value if hasattr(fm.get_status(), 'value') else str(fm.get_status()),
            "total_wallets": fm.get_active_wallet_count(),
            "total_transactions": fm.get_transaction_count(),
            "total_volume": fm.get_total_volume(),
            "supported_currencies": fm.get_supported_currencies_count(),
            "payment_methods": fm.get_payment_methods_count(),
            "banking_regions": fm.get_banking_regions_count(),
            "active_users": fm.get_active_user_count(),
            "last_updated": fm.get_last_rate_update()
        })
    except Exception as e:
        logger.error(f"Finance stats error: {e}")
        return error(str(e))


# ─── Phase 4: Ledger Engine ─────────────────────────────────────────────────


@router.get("/api/finance/ledger/balance/{account}")
async def ledger_balance(account: str, currency: str = "NCR"):
    """Get ledger balance for an account (Phase 4 — Double-Entry Ledger)."""
    try:
        from core.economy.ledger_engine import get_ledger_engine
        ledger = get_ledger_engine()
        balance = ledger.get_balance(account, currency)
        if not balance:
            return ok(data={"account": account, "currency": currency, "balance": 0.0})
        return ok(data=balance.to_dict())
    except Exception as e:
        logger.error(f"Ledger balance error: {e}")
        return error(str(e))


@router.get("/api/finance/ledger/user/{user_id}")
async def ledger_user_balance(user_id: str, currency: str = "NCR"):
    """Get user's ledger balance (Phase 4 — Double-Entry Ledger)."""
    try:
        from core.economy.ledger_engine import get_ledger_engine
        ledger = get_ledger_engine()
        balance = ledger.get_user_balance(user_id, currency)
        return ok(data={"user_id": user_id, "currency": currency, "balances": balance})
    except Exception as e:
        logger.error(f"Ledger user balance error: {e}")
        return error(str(e))


@router.get("/api/finance/ledger/verify")
async def ledger_verify():
    """Verify ledger chain integrity and balance (Phase 4)."""
    try:
        from core.economy.ledger_engine import get_ledger_engine
        ledger = get_ledger_engine()
        chain = ledger.verify_chain_integrity()
        balance = ledger.verify_balances()
        return ok(data={
            "chain_integrity": chain,
            "balance_integrity": balance,
            "dual_verified": chain.get("valid") and balance.get("balanced"),
        })
    except Exception as e:
        logger.error(f"Ledger verify error: {e}")
        return error(str(e))


@router.get("/api/finance/ledger/transactions/{user_id}")
async def ledger_transactions(user_id: str, limit: int = 50):
    """Get transaction history for a user (Phase 4)."""
    try:
        from core.economy.ledger_engine import get_ledger_engine
        ledger = get_ledger_engine()
        txs = ledger.get_transaction_history(user_id, limit)
        return ok(data={"user_id": user_id, "transactions": txs, "count": len(txs)})
    except Exception as e:
        logger.error(f"Ledger transactions error: {e}")
        return error(str(e))


@router.get("/api/finance/ledger/stats")
async def ledger_stats():
    """Get ledger engine statistics (Phase 4)."""
    try:
        from core.economy.ledger_engine import get_ledger_engine
        ledger = get_ledger_engine()
        stats = ledger.get_stats()
        return ok(data=stats)
    except Exception as e:
        logger.error(f"Ledger stats error: {e}")
        return error(str(e))


# ─── Phase 4: Nepal Banking Integration ─────────────────────────────────────


@router.get("/api/finance/nepal/providers")
async def nepal_payment_providers():
    """Get supported Nepal payment providers (Phase 4)."""
    try:
        from core.nepal.banking_integrations import (
            NepalBankingIntegration, PaymentProvider,
            get_banking_integration,
        )
        banking = get_banking_integration()
        providers = banking.get_supported_providers()
        return ok(data={"providers": providers, "count": len(providers)})
    except Exception as e:
        logger.error(f"Nepal providers error: {e}")
        return error(str(e))


@router.post("/api/finance/nepal/payment/initiate")
async def nepal_initiate_payment(data: dict = Body(...)):
    """Initiate a payment via Nepal payment provider (Phase 4)."""
    try:
        from core.nepal.banking_integrations import get_banking_integration
        banking = get_banking_integration()
        result = await banking.initiate_payment(
            provider=data.get("provider"),
            amount=data.get("amount", 0),
            currency=data.get("currency", "NPR"),
            user_id=data.get("user_id"),
            description=data.get("description", ""),
            idempotency_key=data.get("idempotency_key"),
            metadata=data.get("metadata"),
            callback_url=data.get("callback_url"),
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Nepal payment initiate error: {e}")
        return error(str(e))


@router.post("/api/finance/nepal/webhook")
async def nepal_webhook(data: dict = Body(...)):
    """Handle Nepal payment provider webhook (Phase 4)."""
    try:
        from core.nepal.banking_integrations import get_banking_integration
        banking = get_banking_integration()
        result = await banking.handle_webhook(
            provider=data.get("provider"),
            raw_body=data.get("raw_body", ""),
            signature=data.get("signature", ""),
            headers=data.get("headers"),
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Nepal webhook error: {e}")
        return error(str(e))


@router.get("/api/finance/nepal/tax-breakdown")
async def nepal_tax_breakdown():
    """Get Nepal tax rates (13% VAT, 1% TDS) (Phase 4)."""
    try:
        from core.nepal.banking_integrations import (
            NEPAL_VAT_RATE, NEPAL_TDS_RATE, NEPAL_SERVICE_CHARGE,
        )
        return ok(data={
            "vat_rate": NEPAL_VAT_RATE,
            "vat_label": f"{NEPAL_VAT_RATE * 100:.0f}% VAT",
            "tds_rate": NEPAL_TDS_RATE,
            "tds_label": f"{NEPAL_TDS_RATE * 100:.0f}% TDS",
            "service_charge_rate": NEPAL_SERVICE_CHARGE,
            "service_charge_label": f"{NEPAL_SERVICE_CHARGE * 100:.0f}% Service Charge",
            "country": "Nepal",
            "reference": "Nepal IT Act 2063",
        })
    except Exception as e:
        logger.error(f"Nepal tax breakdown error: {e}")
        return error(str(e))


@router.get("/api/finance/nepal/status")
async def nepal_banking_status():
    """Get Nepal banking integration status (Phase 4)."""
    try:
        from core.nepal.banking_integrations import get_banking_integration
        banking = get_banking_integration()
        status = banking.get_status()
        return ok(data=status)
    except Exception as e:
        logger.error(f"Nepal banking status error: {e}")
        return error(str(e))
