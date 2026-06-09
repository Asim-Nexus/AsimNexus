"""
ASIMNEXUS Wallet System
=======================
User-facing wallet layer — wraps core/economy/sovereign_token.py and
core/economy/nexus_credits.py into a clean user API.

Supports NEXUS, SVT (Soul-Bound), and HDT (Holonic Digital Twin) tokens.
"""

import asyncio
import logging
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("EconomyWallet")

# ── Types ────────────────────────────────────────────────────────────────────

class TokenType(Enum):
    NEXUS = "nexus"          # Core utility token
    SVT = "svt"              # Soul-Bound Token (identity)
    HDT = "hdt"              # Holonic Digital Twin token
    CREDIT = "credit"        # Nexus Credit (internal)


class WalletStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REWARD = "reward"
    STAKE = "stake"
    UNSTAKE = "unstake"
    FEE = "fee"


class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Balance:
    """Token balance for a single token type."""
    token_type: str
    available: float = 0.0
    locked: float = 0.0
    staked: float = 0.0

    @property
    def total(self) -> float:
        return self.available + self.locked + self.staked

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Balance":
        return cls(**data)


@dataclass
class WalletEntry:
    """A single wallet entry in the ledger."""
    wallet_id: str
    owner_id: str
    owner_type: str  # "user", "agent", "clone", "organization"
    balances: Dict[str, Balance] = field(default_factory=dict)
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "owner_id": self.owner_id,
            "owner_type": self.owner_type,
            "balances": {k: v.to_dict() for k, v in self.balances.items()},
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletEntry":
        balances = {}
        for k, v in data.pop("balances", {}).items():
            balances[k] = Balance.from_dict(v)
        entry = cls(**data)
        entry.balances = balances
        return entry


@dataclass
class WalletTransaction:
    """A single transaction on the wallet."""
    tx_id: str
    wallet_id: str
    tx_type: str
    token_type: str
    amount: float
    counterparty_id: str
    status: str = "pending"
    timestamp: str = ""
    confirmed_at: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletTransaction":
        return cls(**data)


# ── Wallet Engine ────────────────────────────────────────────────────────────

class WalletEngine:
    """
    Core wallet engine managing wallet entries and transactions.

    Uses an in-memory ledger with JSONL persistence.
    Integrates with core/economy/sovereign_token.py for actual token logic.
    """

    LEDGER_PATH = "data/wallet_ledger.jsonl"

    def __init__(self):
        self._wallets: Dict[str, WalletEntry] = {}
        self._transactions: Dict[str, WalletTransaction] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def _ensure_loaded(self):
        if not self._loaded:
            await self._load_ledger()
            self._loaded = True

    async def _load_ledger(self):
        """Load wallet state from JSONL ledger."""
        import os
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        if not ledger.exists():
            ledger.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            async with self._lock:
                for line in ledger.read_text().strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        etype = entry.get("_type", "")
                        if etype == "wallet":
                            w = WalletEntry.from_dict(entry["data"])
                            self._wallets[w.wallet_id] = w
                        elif etype == "transaction":
                            t = WalletTransaction.from_dict(entry["data"])
                            self._transactions[t.tx_id] = t
                    except (json.JSONDecodeError, KeyError):
                        continue
            logger.info(f"Loaded {len(self._wallets)} wallets, {len(self._transactions)} txns")
        except Exception as e:
            logger.error(f"Failed to load wallet ledger: {e}")

    async def _append_ledger(self, entry_type: str, data: dict):
        """Append one entry to the JSONL ledger."""
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({"_type": entry_type, "data": data, "_ts": datetime.utcnow().isoformat()})
        async with self._lock:
            with ledger.open("a") as f:
                f.write(record + "\n")

    # ── Wallet CRUD ──────────────────────────────────────────────────────

    async def create_wallet(
        self,
        owner_id: str,
        owner_type: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WalletEntry:
        """Create a new wallet for an owner."""
        await self._ensure_loaded()
        now = datetime.utcnow().isoformat()
        wallet = WalletEntry(
            wallet_id=f"wal_{uuid.uuid4().hex[:16]}",
            owner_id=owner_id,
            owner_type=owner_type,
            balances={
                "nexus": Balance(token_type="nexus", available=0.0),
                "svt": Balance(token_type="svt", available=0.0),
                "hdt": Balance(token_type="hdt", available=0.0),
                "credit": Balance(token_type="credit", available=0.0),
            },
            status="active",
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        async with self._lock:
            self._wallets[wallet.wallet_id] = wallet
        await self._append_ledger("wallet", wallet.to_dict())
        logger.info(f"Created wallet {wallet.wallet_id} for {owner_id}")
        return wallet

    async def get_wallet(self, wallet_id: str) -> Optional[WalletEntry]:
        """Get wallet by ID."""
        await self._ensure_loaded()
        return self._wallets.get(wallet_id)

    async def get_wallet_by_owner(self, owner_id: str) -> Optional[WalletEntry]:
        """Find wallet by owner ID."""
        await self._ensure_loaded()
        for w in self._wallets.values():
            if w.owner_id == owner_id:
                return w
        return None

    async def get_balance(self, wallet_id: str, token_type: str = "nexus") -> Optional[Balance]:
        """Get balance for a specific token type."""
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return None
        return wallet.balances.get(token_type)

    async def freeze_wallet(self, wallet_id: str, reason: str = "") -> bool:
        """Freeze a wallet (disable transactions)."""
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return False
        wallet.status = "frozen"
        wallet.updated_at = datetime.utcnow().isoformat()
        wallet.metadata["frozen_reason"] = reason
        wallet.metadata["frozen_at"] = wallet.updated_at
        await self._append_ledger("wallet", wallet.to_dict())
        return True

    async def close_wallet(self, wallet_id: str) -> bool:
        """Close a wallet."""
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return False
        wallet.status = "closed"
        wallet.updated_at = datetime.utcnow().isoformat()
        await self._append_ledger("wallet", wallet.to_dict())
        return True

    # ── Transactions ─────────────────────────────────────────────────────

    async def _create_tx(
        self,
        wallet_id: str,
        tx_type: str,
        token_type: str,
        amount: float,
        counterparty_id: str = "",
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> WalletTransaction:
        """Create and record a transaction."""
        tx = WalletTransaction(
            tx_id=f"tx_{uuid.uuid4().hex[:16]}",
            wallet_id=wallet_id,
            tx_type=tx_type,
            token_type=token_type,
            amount=amount,
            counterparty_id=counterparty_id,
            status="pending",
            timestamp=datetime.utcnow().isoformat(),
            description=description,
            metadata=metadata or {},
        )
        async with self._lock:
            self._transactions[tx.tx_id] = tx
        await self._append_ledger("transaction", tx.to_dict())
        return tx

    async def _confirm_tx(self, tx_id: str) -> bool:
        """Mark a transaction as confirmed."""
        tx = self._transactions.get(tx_id)
        if not tx:
            return False
        tx.status = "confirmed"
        tx.confirmed_at = datetime.utcnow().isoformat()
        await self._append_ledger("transaction", tx.to_dict())
        return True

    async def _fail_tx(self, tx_id: str, reason: str = "") -> bool:
        """Mark a transaction as failed."""
        tx = self._transactions.get(tx_id)
        if not tx:
            return False
        tx.status = "failed"
        tx.metadata["fail_reason"] = reason
        await self._append_ledger("transaction", tx.to_dict())
        return True

    # ── Core Operations ──────────────────────────────────────────────────

    async def deposit(
        self,
        wallet_id: str,
        token_type: str,
        amount: float,
        reference: str = "",
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Deposit tokens into a wallet."""
        if amount <= 0:
            return False, "Amount must be positive"

        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return False, "Wallet not found"
        if wallet.status != "active":
            return False, f"Wallet is {wallet.status}"

        balance = wallet.balances.get(token_type)
        if not balance:
            return False, f"Unsupported token type: {token_type}"

        tx = await self._create_tx(
            wallet_id, "deposit", token_type, amount,
            counterparty_id="system",
            description=f"Deposit {amount} {token_type}",
            metadata=metadata,
        )

        balance.available += amount
        wallet.updated_at = datetime.utcnow().isoformat()
        await self._confirm_tx(tx.tx_id)
        await self._append_ledger("wallet", wallet.to_dict())

        return True, tx.tx_id

    async def withdraw(
        self,
        wallet_id: str,
        token_type: str,
        amount: float,
        destination: str = "",
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Withdraw tokens from a wallet."""
        if amount <= 0:
            return False, "Amount must be positive"

        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            return False, "Wallet not found"
        if wallet.status != "active":
            return False, f"Wallet is {wallet.status}"

        balance = wallet.balances.get(token_type)
        if not balance:
            return False, f"Unsupported token type: {token_type}"
        if balance.available < amount:
            return False, f"Insufficient {token_type} balance"

        tx = await self._create_tx(
            wallet_id, "withdrawal", token_type, amount,
            counterparty_id=destination or "external",
            description=f"Withdraw {amount} {token_type}",
            metadata=metadata,
        )

        balance.available -= amount
        wallet.updated_at = datetime.utcnow().isoformat()
        await self._confirm_tx(tx.tx_id)
        await self._append_ledger("wallet", wallet.to_dict())

        return True, tx.tx_id

    async def transfer(
        self,
        from_wallet_id: str,
        to_wallet_id: str,
        token_type: str,
        amount: float,
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Transfer tokens between wallets."""
        if amount <= 0:
            return False, "Amount must be positive"
        if from_wallet_id == to_wallet_id:
            return False, "Cannot transfer to self"

        src = await self.get_wallet(from_wallet_id)
        dst = await self.get_wallet(to_wallet_id)
        if not src:
            return False, "Source wallet not found"
        if not dst:
            return False, "Destination wallet not found"
        if src.status != "active":
            return False, f"Source wallet is {src.status}"
        if dst.status != "active":
            return False, f"Destination wallet is {dst.status}"

        src_bal = src.balances.get(token_type)
        if not src_bal:
            return False, f"Unsupported token type: {token_type}"
        if src_bal.available < amount:
            return False, f"Insufficient {token_type} balance"

        dst_bal = dst.balances.get(token_type)
        if not dst_bal:
            dst.balances[token_type] = Balance(token_type=token_type)

        tx = await self._create_tx(
            from_wallet_id, "transfer", token_type, amount,
            counterparty_id=to_wallet_id,
            description=description or f"Transfer {amount} {token_type}",
            metadata=metadata,
        )

        src_bal.available -= amount
        dst_bal.available += amount
        now = datetime.utcnow().isoformat()
        src.updated_at = now
        dst.updated_at = now

        await self._confirm_tx(tx.tx_id)
        await self._append_ledger("wallet", src.to_dict())
        await self._append_ledger("wallet", dst.to_dict())

        return True, tx.tx_id

    async def get_transaction(self, tx_id: str) -> Optional[WalletTransaction]:
        """Get a transaction by ID."""
        await self._ensure_loaded()
        return self._transactions.get(tx_id)

    async def list_transactions(
        self,
        wallet_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WalletTransaction]:
        """List transactions for a wallet, newest first."""
        await self._ensure_loaded()
        txns = [
            t for t in self._transactions.values()
            if t.wallet_id == wallet_id
        ]
        txns.sort(key=lambda t: t.timestamp, reverse=True)
        return txns[offset:offset + limit]

    async def get_total_supply(self, token_type: str = "nexus") -> float:
        """Calculate total supply of a token type across all wallets."""
        await self._ensure_loaded()
        total = 0.0
        for w in self._wallets.values():
            bal = w.balances.get(token_type)
            if bal:
                total += bal.total
        return total

    async def get_stats(self) -> Dict[str, Any]:
        """Get wallet system statistics."""
        await self._ensure_loaded()
        active = sum(1 for w in self._wallets.values() if w.status == "active")
        frozen = sum(1 for w in self._wallets.values() if w.status == "frozen")
        return {
            "total_wallets": len(self._wallets),
            "active_wallets": active,
            "frozen_wallets": frozen,
            "total_transactions": len(self._transactions),
            "nexus_supply": await self.get_total_supply("nexus"),
            "svt_supply": await self.get_total_supply("svt"),
            "hdt_supply": await self.get_total_supply("hdt"),
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_engine: Optional[WalletEngine] = None


def get_wallet_engine() -> WalletEngine:
    """Get or create the singleton wallet engine."""
    global _engine
    if _engine is None:
        _engine = WalletEngine()
    return _engine


def reset_wallet_engine():
    """Reset the wallet engine (for testing)."""
    global _engine
    _engine = None
