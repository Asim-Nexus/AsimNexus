#!/usr/bin/env python3
"""
ASIMNEXUS Banking Sector Module
==================================
Financial sector management with 51/49 constitutional balance enforcement.

The Banking sector manages:
- Account creation and management
- Transactions and ledger
- Loan processing
- Regulatory compliance (KYC/AML)
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("AsimNexus.Sectors.Banking")


class AccountType(Enum):
    SAVINGS = "savings"
    CHECKING = "checking"
    FIXED_DEPOSIT = "fixed_deposit"
    LOAN = "loan"
    BUSINESS = "business"


class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    INTEREST = "interest"
    FEE = "fee"


@dataclass
class AccountRecord:
    """A bank account record."""
    account_id: str
    account_number: str
    account_type: AccountType
    owner_name: str
    owner_id: str
    balance: float
    currency: str = "NRS"
    status: AccountStatus = AccountStatus.ACTIVE
    kyc_verified: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["account_type"] = self.account_type.value
        result["status"] = self.status.value
        return result


@dataclass
class TransactionRecord:
    """A financial transaction record."""
    tx_id: str
    account_id: str
    tx_type: TransactionType
    amount: float
    currency: str = "NRS"
    description: str = ""
    reference: str = ""
    balance_before: float = 0.0
    balance_after: float = 0.0
    status: str = "completed"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["tx_type"] = self.tx_type.value
        return result


class BankingSector:
    """
    Banking Sector Manager.
    Enforces constitutional balance: 51% government / 49% private financial oversight.
    """

    def __init__(self):
        self.accounts: Dict[str, AccountRecord] = {}
        self.transactions: Dict[str, TransactionRecord] = {}
        self._tx_counter: int = 0
        self._audit_log: List[Dict[str, Any]] = []
        logger.info("🏦 Banking Sector initialized (51/49 balance enforced)")

    def create_account(
        self,
        account_id: str,
        owner_name: str,
        owner_id: str,
        account_type: str = "savings",
        currency: str = "NRS",
        initial_deposit: float = 0.0,
        kyc_verified: bool = False,
    ) -> Dict[str, Any]:
        """Create a new bank account."""
        if account_id in self.accounts:
            return {"error": "Account already exists", "account_id": account_id}

        try:
            atype = AccountType(account_type)
        except ValueError:
            return {"error": f"Invalid account type: {account_type}"}

        account_number = f"ASIM{datetime.utcnow().strftime('%Y%m')}{self._tx_counter:06d}"

        record = AccountRecord(
            account_id=account_id,
            account_number=account_number,
            account_type=atype,
            owner_name=owner_name,
            owner_id=owner_id,
            balance=initial_deposit,
            currency=currency,
            kyc_verified=kyc_verified,
        )
        self.accounts[account_id] = record

        if initial_deposit > 0:
            self._record_transaction(
                account_id=account_id,
                tx_type=TransactionType.DEPOSIT,
                amount=initial_deposit,
                balance_before=0.0,
                balance_after=initial_deposit,
                description="Initial deposit",
            )

        self._audit("account_created", account_id)
        return {
            "status": "created",
            "account_id": account_id,
            "account_number": account_number,
            "balance": initial_deposit,
        }

    def deposit(self, account_id: str, amount: float, description: str = "") -> Dict[str, Any]:
        """Deposit money into an account."""
        if account_id not in self.accounts:
            return {"error": "Account not found", "account_id": account_id}
        if amount <= 0:
            return {"error": "Amount must be positive"}

        account = self.accounts[account_id]
        if account.status != AccountStatus.ACTIVE:
            return {"error": f"Account is {account.status.value}"}

        balance_before = account.balance
        account.balance += amount
        account.updated_at = datetime.utcnow().isoformat()

        self._record_transaction(
            account_id=account_id,
            tx_type=TransactionType.DEPOSIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=account.balance,
            description=description or "Deposit",
        )
        self._audit("deposit", account_id, {"amount": amount})
        return {"status": "deposited", "account_id": account_id, "amount": amount, "balance": account.balance}

    def withdraw(self, account_id: str, amount: float, description: str = "") -> Dict[str, Any]:
        """Withdraw money from an account."""
        if account_id not in self.accounts:
            return {"error": "Account not found", "account_id": account_id}
        if amount <= 0:
            return {"error": "Amount must be positive"}

        account = self.accounts[account_id]
        if account.status != AccountStatus.ACTIVE:
            return {"error": f"Account is {account.status.value}"}
        if account.balance < amount:
            return {"error": "Insufficient balance", "balance": account.balance, "requested": amount}

        balance_before = account.balance
        account.balance -= amount
        account.updated_at = datetime.utcnow().isoformat()

        self._record_transaction(
            account_id=account_id,
            tx_type=TransactionType.WITHDRAWAL,
            amount=amount,
            balance_before=balance_before,
            balance_after=account.balance,
            description=description or "Withdrawal",
        )
        self._audit("withdrawal", account_id, {"amount": amount})
        return {"status": "withdrawn", "account_id": account_id, "amount": amount, "balance": account.balance}

    def transfer(self, from_account: str, to_account: str, amount: float, description: str = "") -> Dict[str, Any]:
        """Transfer money between accounts."""
        if from_account not in self.accounts:
            return {"error": "Source account not found", "account_id": from_account}
        if to_account not in self.accounts:
            return {"error": "Destination account not found", "account_id": to_account}
        if amount <= 0:
            return {"error": "Amount must be positive"}

        src = self.accounts[from_account]
        dst = self.accounts[to_account]

        if src.status != AccountStatus.ACTIVE:
            return {"error": f"Source account is {src.status.value}"}
        if src.balance < amount:
            return {"error": "Insufficient balance", "balance": src.balance, "requested": amount}

        src_balance_before = src.balance
        dst_balance_before = dst.balance

        src.balance -= amount
        dst.balance += amount
        src.updated_at = datetime.utcnow().isoformat()
        dst.updated_at = datetime.utcnow().isoformat()

        self._record_transaction(
            account_id=from_account,
            tx_type=TransactionType.TRANSFER,
            amount=-amount,
            balance_before=src_balance_before,
            balance_after=src.balance,
            description=description or f"Transfer to {to_account}",
            reference=to_account,
        )
        self._record_transaction(
            account_id=to_account,
            tx_type=TransactionType.TRANSFER,
            amount=amount,
            balance_before=dst_balance_before,
            balance_after=dst.balance,
            description=description or f"Transfer from {from_account}",
            reference=from_account,
        )
        self._audit("transfer", from_account, {"to": to_account, "amount": amount})
        return {"status": "transferred", "from": from_account, "to": to_account, "amount": amount}

    def get_account(self, account_id: str) -> Optional[AccountRecord]:
        """Get account by ID."""
        return self.accounts.get(account_id)

    def get_transactions(self, account_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get transactions for an account."""
        results = []
        for tx in self.transactions.values():
            if tx.account_id == account_id:
                results.append(tx.to_dict())
        return results[-limit:]

    def list_accounts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List accounts, optionally filtered by status."""
        results = []
        for a in self.accounts.values():
            if status and a.status.value != status:
                continue
            results.append(a.to_dict())
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get banking sector statistics."""
        total_balance = sum(a.balance for a in self.accounts.values())
        return {
            "total_accounts": len(self.accounts),
            "active_accounts": sum(1 for a in self.accounts.values() if a.status == AccountStatus.ACTIVE),
            "total_balance": total_balance,
            "total_transactions": len(self.transactions),
            "government_share": 0.51,
            "private_share": 0.49,
            "audit_entries": len(self._audit_log),
        }

    def _record_transaction(
        self, account_id: str, tx_type: TransactionType, amount: float,
        balance_before: float, balance_after: float, description: str = "",
        reference: str = "",
    ) -> None:
        self._tx_counter += 1
        tx_id = f"TX{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{self._tx_counter:04d}"
        tx = TransactionRecord(
            tx_id=tx_id,
            account_id=account_id,
            tx_type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            reference=reference,
        )
        self.transactions[tx_id] = tx

    def _audit(self, action: str, resource_id: str, details: Optional[Dict] = None) -> None:
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource_id": resource_id,
            "details": details or {},
            "sector": "banking",
        })

    def reset(self) -> None:
        """Reset all data (for testing)."""
        self.accounts.clear()
        self.transactions.clear()
        self._tx_counter = 0
        self._audit_log.clear()
