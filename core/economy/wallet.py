"""
AsimNexus — Wallet Engine
=========================
Multi-currency wallet management for the AsimNexus economy.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "wallet_ledger.jsonl"
)

TRANSACTIONS_LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "wallet_transactions.jsonl"
)


class TokenType(str, Enum):
    NEXUS = "nexus"
    SVT = "svt"
    HDT = "hdt"
    CREDIT = "credit"


class WalletStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


SUPPORTED_TOKENS = {"nexus", "svt", "hdt", "credit"}


@dataclass
class Balance:
    available: float = 0.0
    locked: float = 0.0
    total: float = 0.0


@dataclass
class WalletEntry:
    wallet_id: str
    owner_id: str
    owner_type: str
    balances: Dict[str, Balance] = field(default_factory=lambda: {
        "nexus": Balance(),
        "svt": Balance(),
        "hdt": Balance(),
        "credit": Balance(),
    })
    status: str = "active"
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "owner_id": self.owner_id,
            "owner_type": self.owner_type,
            "balances": {k: asdict(v) for k, v in self.balances.items()},
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletEntry":
        balances = {}
        for k, v in data.get("balances", {}).items():
            balances[k] = Balance(**v)
        return cls(
            wallet_id=data["wallet_id"],
            owner_id=data["owner_id"],
            owner_type=data["owner_type"],
            balances=balances,
            status=data.get("status", "active"),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
        )


@dataclass
class WalletTransaction:
    tx_id: str
    wallet_id: str
    token_type: str
    amount: float
    tx_type: str  # deposit, withdrawal, transfer, lock, unlock
    reference: str = ""
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    status: str = "confirmed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "wallet_id": self.wallet_id,
            "token_type": self.token_type,
            "amount": self.amount,
            "tx_type": self.tx_type,
            "reference": self.reference,
            "timestamp": self.timestamp,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletTransaction":
        return cls(
            tx_id=data["tx_id"],
            wallet_id=data["wallet_id"],
            token_type=data["token_type"],
            amount=data["amount"],
            tx_type=data["tx_type"],
            reference=data.get("reference", ""),
            timestamp=data.get("timestamp", 0.0),
            status=data.get("status", "confirmed"),
        )


class WalletEngine:
    """Multi-currency wallet engine."""

    LEDGER_PATH = LEDGER_PATH

    def __init__(self):
        self._wallets: Dict[str, WalletEntry] = {}
        self._transactions: Dict[str, WalletTransaction] = {}
        self._transaction_order: List[str] = []  # insertion order of tx_ids
        self._lock = threading.Lock()
        self._load()

    async def create_wallet(
        self, owner_id: str, owner_type: str = "user"
    ) -> WalletEntry:
        """Create a new wallet."""
        # Check for duplicate owner_id
        existing = await self.get_wallet_by_owner(owner_id)
        if existing is not None:
            raise ValueError(f"Wallet already exists for owner: {owner_id}")
        wallet = WalletEntry(
            wallet_id=f"wal_{uuid.uuid4().hex[:16]}",
            owner_id=owner_id,
            owner_type=owner_type,
        )
        with self._lock:
            self._wallets[wallet.wallet_id] = wallet
            self._persist(wallet)
        return wallet

    async def get_wallet(self, wallet_id: str) -> Optional[WalletEntry]:
        """Get wallet by ID."""
        with self._lock:
            return self._wallets.get(wallet_id)

    async def get_wallet_by_owner(self, owner_id: str) -> Optional[WalletEntry]:
        """Get wallet by owner ID."""
        with self._lock:
            for w in self._wallets.values():
                if w.owner_id == owner_id:
                    return w
        return None

    async def deposit(
        self, wallet_id: str, token_type: str, amount: float, reference: str = ""
    ) -> tuple:
        """Deposit tokens to a wallet. Returns (success, tx_id_or_msg)."""
        if amount <= 0:
            return (False, "Amount must be positive")

        if token_type not in SUPPORTED_TOKENS:
            return (False, f"Unsupported token type: {token_type}")

        with self._lock:
            wallet = self._wallets.get(wallet_id)
            if not wallet:
                return (False, f"Wallet not found: {wallet_id}")
            if wallet.status == "frozen":
                return (False, "Wallet is frozen")
            if wallet.status == "closed":
                return (False, "Wallet is closed")

            balance = wallet.balances.get(token_type)
            if not balance:
                return (False, f"Unsupported token type: {token_type}")

            balance.available += amount
            balance.total += amount
            wallet.updated_at = datetime.utcnow().timestamp()
            tx = WalletTransaction(
                tx_id=f"tx_{uuid.uuid4().hex[:16]}",
                wallet_id=wallet_id,
                token_type=token_type,
                amount=amount,
                tx_type="deposit",
                reference=reference,
            )
            self._transactions[tx.tx_id] = tx
            self._transaction_order.append(tx.tx_id)
            self._persist(wallet)
            self._persist_transaction(tx)
        return (True, tx.tx_id)

    async def withdraw(
        self, wallet_id: str, token_type: str, amount: float, reference: str = "",
        destination: str = ""
    ) -> tuple:
        """Withdraw tokens from a wallet. Returns (success, tx_id_or_msg)."""
        if amount <= 0:
            return (False, "Amount must be positive")

        if token_type not in SUPPORTED_TOKENS:
            return (False, f"Unsupported token type: {token_type}")

        with self._lock:
            wallet = self._wallets.get(wallet_id)
            if not wallet:
                return (False, f"Wallet not found: {wallet_id}")
            if wallet.status == "frozen":
                return (False, "Wallet is frozen")
            if wallet.status == "closed":
                return (False, "Wallet is closed")

            balance = wallet.balances.get(token_type)
            if not balance:
                return (False, f"Unsupported token type: {token_type}")
            if balance.available < amount:
                return (False, f"Insufficient {token_type} balance")

            balance.available -= amount
            balance.total -= amount
            wallet.updated_at = datetime.utcnow().timestamp()
            tx = WalletTransaction(
                tx_id=f"tx_{uuid.uuid4().hex[:16]}",
                wallet_id=wallet_id,
                token_type=token_type,
                amount=amount,
                tx_type="withdrawal",
                reference=reference,
            )
            self._transactions[tx.tx_id] = tx
            self._transaction_order.append(tx.tx_id)
            self._persist(wallet)
            self._persist_transaction(tx)
        return (True, tx.tx_id)

    async def transfer(
        self,
        from_wallet_id: str,
        to_wallet_id: str,
        token_type: str,
        amount: float,
        reference: str = "",
        description: str = "",
    ) -> tuple:
        """Transfer tokens between wallets. Returns (success, tx_id_or_msg)."""
        if from_wallet_id == to_wallet_id:
            return (False, "Cannot transfer to self")

        if amount <= 0:
            return (False, "Amount must be positive")

        if token_type not in SUPPORTED_TOKENS:
            return (False, f"Unsupported token type: {token_type}")

        with self._lock:
            from_wallet = self._wallets.get(from_wallet_id)
            to_wallet = self._wallets.get(to_wallet_id)
            if not from_wallet:
                return (False, f"Source wallet not found: {from_wallet_id}")
            if not to_wallet:
                return (False, f"Destination wallet not found: {to_wallet_id}")
            if from_wallet.status == "frozen":
                return (False, "Source wallet is frozen")
            if to_wallet.status == "frozen":
                return (False, "Destination wallet is frozen")

            from_balance = from_wallet.balances.get(token_type)
            if not from_balance:
                return (False, f"Unsupported token type: {token_type}")
            if from_balance.available < amount:
                return (False, f"Insufficient {token_type} balance")

            to_balance = to_wallet.balances.get(token_type)
            if not to_balance:
                return (False, f"Unsupported token type: {token_type}")

            # Perform transfer
            from_balance.available -= amount
            from_balance.total -= amount
            to_balance.available += amount
            to_balance.total += amount
            from_wallet.updated_at = datetime.utcnow().timestamp()
            to_wallet.updated_at = datetime.utcnow().timestamp()

            tx = WalletTransaction(
                tx_id=f"tx_{uuid.uuid4().hex[:16]}",
                wallet_id=from_wallet_id,
                token_type=token_type,
                amount=amount,
                tx_type="transfer",
                reference=reference,
            )
            self._transactions[tx.tx_id] = tx
            self._transaction_order.append(tx.tx_id)
            self._persist(from_wallet)
            self._persist(to_wallet)
            self._persist_transaction(tx)
        return (True, tx.tx_id)

    async def get_balance(
        self, wallet_id: str, token_type: str
    ) -> Optional[Balance]:
        """Get balance for a specific token type."""
        wallet = await self.get_wallet(wallet_id)
        if wallet:
            return wallet.balances.get(token_type)
        return None

    async def freeze_wallet(self, wallet_id: str, reason: str = "") -> bool:
        """Freeze a wallet, blocking transactions."""
        with self._lock:
            wallet = self._wallets.get(wallet_id)
            if not wallet:
                return False
            wallet.status = "frozen"
            wallet.updated_at = datetime.utcnow().timestamp()
            self._persist(wallet)
        return True

    async def close_wallet(self, wallet_id: str) -> bool:
        """Close a wallet."""
        with self._lock:
            wallet = self._wallets.get(wallet_id)
            if not wallet:
                return False
            wallet.status = "closed"
            wallet.updated_at = datetime.utcnow().timestamp()
            self._persist(wallet)
        return True

    async def list_transactions(
        self, wallet_id: str, limit: int = 50
    ) -> List[WalletTransaction]:
        """List transactions for a wallet, newest first."""
        with self._lock:
            txns = [
                tx for tx in self._transactions.values()
                if tx.wallet_id == wallet_id
            ]
            # Build order index for stable sort when timestamps are equal
            order_index = {
                tx_id: i for i, tx_id in enumerate(self._transaction_order)
            }
            txns.sort(
                key=lambda t: (-t.timestamp, -order_index.get(t.tx_id, 0)),
            )
            return txns[:limit]

    async def get_transaction(self, tx_id: str) -> Optional[WalletTransaction]:
        """Get a specific transaction by ID."""
        with self._lock:
            return self._transactions.get(tx_id)

    async def get_total_supply(self, token_type: str) -> float:
        """Calculate total supply of a token across all wallets."""
        total = 0.0
        with self._lock:
            for wallet in self._wallets.values():
                balance = wallet.balances.get(token_type)
                if balance:
                    total += balance.total
        return total

    async def get_stats(self) -> Dict[str, Any]:
        """Get wallet system statistics."""
        with self._lock:
            total_wallets = len(self._wallets)
            active_wallets = sum(
                1 for w in self._wallets.values() if w.status == "active"
            )
            frozen_wallets = sum(
                1 for w in self._wallets.values() if w.status == "frozen"
            )
            closed_wallets = sum(
                1 for w in self._wallets.values() if w.status == "closed"
            )
            total_transactions = len(self._transactions)
            nexus_supply = sum(
                w.balances.get("nexus", Balance()).total
                for w in self._wallets.values()
            )
            return {
                "total_wallets": total_wallets,
                "active_wallets": active_wallets,
                "frozen_wallets": frozen_wallets,
                "closed_wallets": closed_wallets,
                "total_transactions": total_transactions,
                "nexus_supply": nexus_supply,
            }

    async def _ensure_loaded(self) -> None:
        """Ensure all persisted data is loaded (for testing)."""
        self._load()

    def _persist(self, wallet: WalletEntry) -> None:
        """Persist wallet to JSONL."""
        try:
            os.makedirs(os.path.dirname(self.LEDGER_PATH), exist_ok=True)
            with open(self.LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(wallet.to_dict()) + "\n")
        except Exception:
            pass

    def _persist_transaction(self, tx: WalletTransaction) -> None:
        """Persist transaction to JSONL."""
        try:
            os.makedirs(os.path.dirname(TRANSACTIONS_LEDGER_PATH), exist_ok=True)
            with open(TRANSACTIONS_LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(tx.to_dict()) + "\n")
        except Exception:
            pass

    def _load(self) -> None:
        """Load wallets and transactions from JSONL."""
        try:
            if os.path.exists(self.LEDGER_PATH):
                with open(self.LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                wallet = WalletEntry.from_dict(data)
                                self._wallets[wallet.wallet_id] = wallet
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass

        try:
            if os.path.exists(TRANSACTIONS_LEDGER_PATH):
                with open(TRANSACTIONS_LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                tx = WalletTransaction.from_dict(data)
                                self._transactions[tx.tx_id] = tx
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass


# Singleton support
_wallet_engine: Optional[WalletEngine] = None
_wallet_engine_lock = threading.Lock()


def get_wallet_engine() -> WalletEngine:
    global _wallet_engine
    if _wallet_engine is None:
        with _wallet_engine_lock:
            if _wallet_engine is None:
                _wallet_engine = WalletEngine()
    return _wallet_engine


def reset_wallet_engine() -> None:
    global _wallet_engine
    _wallet_engine = None
