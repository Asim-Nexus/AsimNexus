"""
AsimNexus — Token Registry
===========================
Manages token definitions, holdings, minting, and burning.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "token_registry.jsonl"
)

HOLDINGS_LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "token_holdings.jsonl"
)


class TokenStandard(str, Enum):
    NEXUS = "nexus"
    SVT = "svt"
    HDT = "hdt"
    ERC20 = "erc20"
    ERC721 = "erc721"


class TokenStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


@dataclass
class TokenDefinition:
    token_id: str
    standard: str
    name: str
    symbol: str
    total_supply: float = 0.0
    circulating_supply: float = 0.0
    decimals: int = 18
    is_transferable: bool = True
    is_soul_bound: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "standard": self.standard,
            "name": self.name,
            "symbol": self.symbol,
            "total_supply": self.total_supply,
            "circulating_supply": self.circulating_supply,
            "decimals": self.decimals,
            "is_transferable": self.is_transferable,
            "is_soul_bound": self.is_soul_bound,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenDefinition":
        return cls(
            token_id=data["token_id"],
            standard=data["standard"],
            name=data["name"],
            symbol=data["symbol"],
            total_supply=data.get("total_supply", 0.0),
            circulating_supply=data.get("circulating_supply", 0.0),
            decimals=data.get("decimals", 18),
            is_transferable=data.get("is_transferable", True),
            is_soul_bound=data.get("is_soul_bound", False),
            metadata=data.get("metadata", {}),
            status=data.get("status", "active"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class TokenHolding:
    holder_id: str
    token_id: str
    amount: float = 0.0
    locked_amount: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def available(self) -> float:
        return self.amount - self.locked_amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "holder_id": self.holder_id,
            "token_id": self.token_id,
            "amount": self.amount,
            "locked_amount": self.locked_amount,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenHolding":
        return cls(
            holder_id=data["holder_id"],
            token_id=data["token_id"],
            amount=data.get("amount", 0.0),
            locked_amount=data.get("locked_amount", 0.0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class TokenMintEvent:
    event_id: str
    token_id: str
    amount: float
    recipient: str
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "token_id": self.token_id,
            "amount": self.amount,
            "recipient": self.recipient,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenMintEvent":
        return cls(
            event_id=data["event_id"],
            token_id=data["token_id"],
            amount=data["amount"],
            recipient=data["recipient"],
            reason=data.get("reason", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


# Default token definitions
DEFAULT_TOKENS = [
    {
        "standard": "nexus",
        "name": "Nexus Token",
        "symbol": "NEXUS",
        "total_supply": 1_000_000_000,
        "is_transferable": True,
        "is_soul_bound": False,
    },
    {
        "standard": "svt",
        "name": "Sovereign Token",
        "symbol": "SVT",
        "total_supply": 1_000_000,
        "is_transferable": False,
        "is_soul_bound": True,
    },
    {
        "standard": "hdt",
        "name": "Human DNA Token",
        "symbol": "HDT",
        "total_supply": 1_000_000,
        "is_transferable": False,
        "is_soul_bound": True,
    },
]


class TokenRegistry:
    """Manages token definitions and holdings."""

    LEDGER_PATH = LEDGER_PATH

    def __init__(self):
        self._tokens: Dict[str, TokenDefinition] = {}
        self._holdings: Dict[str, TokenHolding] = {}  # key: f"{holder_id}:{token_id}"
        self._mint_events: List[TokenMintEvent] = []
        self._lock = threading.Lock()
        self._load()

    async def register_token(
        self,
        standard: str,
        name: str,
        symbol: str,
        total_supply: float = 0.0,
        decimals: int = 18,
        is_soul_bound: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TokenDefinition:
        """Register a new token definition."""
        token = TokenDefinition(
            token_id=f"tok_{uuid.uuid4().hex[:16]}",
            standard=standard,
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            decimals=decimals,
            is_soul_bound=is_soul_bound,
            is_transferable=not is_soul_bound,
            metadata=metadata or {},
        )
        with self._lock:
            self._tokens[token.token_id] = token
            self._persist(token)
        return token

    async def get_token(self, token_id: str) -> Optional[TokenDefinition]:
        """Get token by ID."""
        with self._lock:
            return self._tokens.get(token_id)

    async def get_token_by_symbol(self, symbol: str) -> Optional[TokenDefinition]:
        """Get token by symbol (case-insensitive)."""
        symbol_lower = symbol.lower()
        with self._lock:
            for token in self._tokens.values():
                if token.symbol.lower() == symbol_lower:
                    return token
        return None

    async def list_tokens(
        self, standard: Optional[str] = None
    ) -> List[TokenDefinition]:
        """List all registered tokens, optionally filtered by standard."""
        with self._lock:
            results = list(self._tokens.values())
        if standard:
            results = [t for t in results if t.standard == standard]
        return results

    async def mint(
        self, token_id: str, amount: float, recipient: str, reason: str = ""
    ) -> tuple:
        """Mint new tokens to a recipient."""
        if amount <= 0:
            return (False, "Amount must be positive")
        with self._lock:
            token = self._tokens.get(token_id)
            if not token:
                return (False, "Token not found")
            token.total_supply += amount
            token.circulating_supply += amount
            # Update or create holding
            holding_key = f"{recipient}:{token_id}"
            holding = self._holdings.get(holding_key)
            if holding:
                holding.amount += amount
            else:
                holding = TokenHolding(
                    holder_id=recipient,
                    token_id=token_id,
                    amount=amount,
                )
                self._holdings[holding_key] = holding
            event = TokenMintEvent(
                event_id=f"mint_{uuid.uuid4().hex[:16]}",
                token_id=token_id,
                amount=amount,
                recipient=recipient,
                reason=reason,
            )
            self._mint_events.append(event)
            self._persist(token)
            self._persist_holding(holding)
        return (True, event.event_id)

    async def burn(
        self, holder: str, token_id: str, amount: float, reason: str = ""
    ) -> tuple:
        """Burn tokens from a holding."""
        if amount <= 0:
            return (False, "Amount must be positive")
        with self._lock:
            token = self._tokens.get(token_id)
            if not token:
                return (False, "Token not found")
            holding_key = f"{holder}:{token_id}"
            holding = self._holdings.get(holding_key)
            if not holding or holding.amount < amount:
                return (False, "Insufficient balance")
            holding.amount -= amount
            token.total_supply -= amount
            token.circulating_supply -= amount
            event_id = f"burn_{uuid.uuid4().hex[:16]}"
            self._persist(token)
            self._persist_holding(holding)
        return (True, event_id)

    async def get_holding(
        self, holder_id: str, token_id: str
    ) -> Optional[TokenHolding]:
        """Get holding for a specific holder and token."""
        with self._lock:
            return self._holdings.get(f"{holder_id}:{token_id}")

    async def list_holdings(
        self, holder_id: Optional[str] = None
    ) -> List[TokenHolding]:
        """List holdings, optionally filtered by holder."""
        with self._lock:
            if holder_id:
                return [
                    h for h in self._holdings.values() if h.holder_id == holder_id
                ]
            return list(self._holdings.values())

    async def get_owner_holdings(self, owner_id: str) -> List[TokenHolding]:
        """Get all holdings for an owner."""
        return await self.list_holdings(holder_id=owner_id)

    async def get_owner_balance(self, owner_id: str, token_id: str) -> float:
        """Get balance for an owner and token."""
        holding = await self.get_holding(owner_id, token_id)
        return holding.amount if holding else 0.0

    async def lock_tokens(
        self, holder_id: str, token_id: str, amount: float
    ) -> tuple:
        """Lock tokens in a holding."""
        if amount <= 0:
            return (False, "Amount must be positive")
        with self._lock:
            holding_key = f"{holder_id}:{token_id}"
            holding = self._holdings.get(holding_key)
            if not holding:
                return (False, "Holding not found")
            if holding.available < amount:
                return (False, "Insufficient available balance")
            holding.locked_amount += amount
            self._persist_holding(holding)
        return (True, "Tokens locked")

    async def unlock_tokens(
        self, holder_id: str, token_id: str, amount: float
    ) -> tuple:
        """Unlock tokens in a holding."""
        if amount <= 0:
            return (False, "Amount must be positive")
        with self._lock:
            holding_key = f"{holder_id}:{token_id}"
            holding = self._holdings.get(holding_key)
            if not holding:
                return (False, "Holding not found")
            if holding.locked_amount < amount:
                return (False, "Insufficient locked balance")
            holding.locked_amount -= amount
            self._persist_holding(holding)
        return (True, "Tokens unlocked")

    async def get_stats(self) -> Dict[str, Any]:
        """Get token registry statistics."""
        with self._lock:
            total_tokens = len(self._tokens)
            total_holdings = len(self._holdings)
            nexus_supply = 0.0
            for token in self._tokens.values():
                if token.symbol == "NEXUS":
                    nexus_supply = token.total_supply
                    break
            return {
                "total_tokens": total_tokens,
                "total_holdings": total_holdings,
                "nexus_supply": nexus_supply,
            }

    async def _ensure_loaded(self) -> None:
        """Ensure data is loaded (for testing)."""
        self._load()

    def _persist(self, token: TokenDefinition) -> None:
        try:
            os.makedirs(os.path.dirname(self.LEDGER_PATH), exist_ok=True)
            with open(self.LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(token.to_dict()) + "\n")
        except Exception:
            pass

    def _persist_holding(self, holding: TokenHolding) -> None:
        try:
            os.makedirs(os.path.dirname(HOLDINGS_LEDGER_PATH), exist_ok=True)
            with open(HOLDINGS_LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(holding.to_dict()) + "\n")
        except Exception:
            pass

    def _load(self) -> None:
        try:
            if os.path.exists(self.LEDGER_PATH):
                with open(self.LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                token = TokenDefinition.from_dict(data)
                                self._tokens[token.token_id] = token
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass
        try:
            if os.path.exists(HOLDINGS_LEDGER_PATH):
                with open(HOLDINGS_LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                holding = TokenHolding.from_dict(data)
                                key = f"{holding.holder_id}:{holding.token_id}"
                                self._holdings[key] = holding
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass


async def initialize_default_tokens(registry: TokenRegistry) -> TokenRegistry:
    """Initialize default tokens (NEXUS, SVT, HDT)."""
    for token_def in DEFAULT_TOKENS:
        existing = await registry.get_token_by_symbol(token_def["symbol"])
        if existing is None:
            await registry.register_token(
                standard=token_def["standard"],
                name=token_def["name"],
                symbol=token_def["symbol"],
                total_supply=token_def["total_supply"],
                is_soul_bound=token_def["is_soul_bound"],
            )
    return registry


# Singleton support
_token_registry: Optional[TokenRegistry] = None
_token_registry_lock = threading.Lock()


def get_token_registry() -> TokenRegistry:
    global _token_registry
    if _token_registry is None:
        with _token_registry_lock:
            if _token_registry is None:
                _token_registry = TokenRegistry()
    return _token_registry


def reset_token_registry() -> None:
    global _token_registry
    _token_registry = None
