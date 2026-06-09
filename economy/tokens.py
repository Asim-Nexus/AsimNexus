"""
ASIMNEXUS Token System
======================
Token registry and management for NEXUS (core), SVT (soul-bound), HDT (identity).

Integrates with core/economy/sovereign_token.py for mint/burn logic
and wallet.py for balance management.
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("TokenSystem")

# ── Types ────────────────────────────────────────────────────────────────────

class TokenStandard(Enum):
    NEXUS = "nexus"       # Fungible utility token
    SVT = "svt"           # Soul-Bound Token (non-transferable)
    HDT = "hdt"           # Holonic Digital Twin (semi-fungible)
    NFT = "nft"           # Non-Fungible Token


class TokenStatus(Enum):
    ACTIVE = "active"
    BURNED = "burned"
    SUSPENDED = "suspended"
    MINTING = "minting"


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class TokenDefinition:
    """Definition of a token type/standard."""
    token_id: str
    standard: str
    name: str
    symbol: str
    total_supply: float = 0.0
    circulating_supply: float = 0.0
    decimals: int = 18
    is_transferable: bool = True
    is_soul_bound: bool = False
    metadata_uri: Optional[str] = None
    created_at: str = ""
    owner_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenDefinition":
        return cls(**data)


@dataclass
class TokenHolding:
    """A user's holding of a specific token."""
    holding_id: str
    token_id: str
    owner_id: str
    standard: str
    amount: float = 0.0
    locked_amount: float = 0.0
    acquired_at: str = ""
    soul_bound_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> float:
        return self.amount - self.locked_amount

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenHolding":
        return cls(**data)


@dataclass
class TokenMintEvent:
    """Record of a minting event."""
    event_id: str
    token_id: str
    standard: str
    amount: float
    recipient_id: str
    reason: str = ""
    timestamp: str = ""
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenMintEvent":
        return cls(**data)


# ── Token Registry ───────────────────────────────────────────────────────────

class TokenRegistry:
    """
    Central registry for all token types and holdings.

    Manages:
    - Token definitions (NEXUS, SVT, HDT, NFT)
    - Mint/burn operations
    - Holdings per owner
    - Soul-bound token constraints
    """

    LEDGER_PATH = "data/token_registry.jsonl"

    def __init__(self):
        self._tokens: Dict[str, TokenDefinition] = {}
        self._holdings: Dict[str, TokenHolding] = {}       # holding_id -> holding
        self._owner_holdings: Dict[str, List[str]] = {}    # owner_id -> [holding_ids]
        self._mint_events: List[TokenMintEvent] = []
        self._lock = asyncio.Lock()
        self._loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def _ensure_loaded(self):
        if not self._loaded:
            await self._load_ledger()
            self._loaded = True

    async def _load_ledger(self):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        if not ledger.exists():
            ledger.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            for line in ledger.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    etype = entry.get("_type", "")
                    if etype == "token_def":
                        td = TokenDefinition.from_dict(entry["data"])
                        self._tokens[td.token_id] = td
                    elif etype == "holding":
                        h = TokenHolding.from_dict(entry["data"])
                        self._holdings[h.holding_id] = h
                        self._owner_holdings.setdefault(h.owner_id, []).append(h.holding_id)
                    elif etype == "mint":
                        me = TokenMintEvent.from_dict(entry["data"])
                        self._mint_events.append(me)
                except (json.JSONDecodeError, KeyError):
                    continue
            logger.info(f"Loaded {len(self._tokens)} tokens, {len(self._holdings)} holdings")
        except Exception as e:
            logger.error(f"Failed to load token registry: {e}")

    async def _append_ledger(self, entry_type: str, data: dict):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({"_type": entry_type, "data": data, "_ts": datetime.utcnow().isoformat()})
        async with self._lock:
            with ledger.open("a") as f:
                f.write(record + "\n")

    # ── Token Definitions ────────────────────────────────────────────────

    async def register_token(
        self,
        standard: str,
        name: str,
        symbol: str,
        total_supply: float = 0.0,
        decimals: int = 18,
        is_soul_bound: bool = False,
        metadata: Optional[Dict] = None,
    ) -> TokenDefinition:
        """Register a new token type."""
        await self._ensure_loaded()
        token = TokenDefinition(
            token_id=f"tok_{uuid.uuid4().hex[:16]}",
            standard=standard,
            name=name,
            symbol=symbol,
            total_supply=total_supply,
            decimals=decimals,
            is_transferable=not is_soul_bound,
            is_soul_bound=is_soul_bound,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        async with self._lock:
            self._tokens[token.token_id] = token
        await self._append_ledger("token_def", token.to_dict())
        logger.info(f"Registered token {token.symbol} ({token.token_id})")
        return token

    async def get_token(self, token_id: str) -> Optional[TokenDefinition]:
        """Get token definition by ID."""
        await self._ensure_loaded()
        return self._tokens.get(token_id)

    async def get_token_by_symbol(self, symbol: str) -> Optional[TokenDefinition]:
        """Find token by symbol."""
        await self._ensure_loaded()
        for t in self._tokens.values():
            if t.symbol.lower() == symbol.lower():
                return t
        return None

    async def list_tokens(self, standard: Optional[str] = None) -> List[TokenDefinition]:
        """List all registered tokens, optionally filtered by standard."""
        await self._ensure_loaded()
        if standard:
            return [t for t in self._tokens.values() if t.standard == standard]
        return list(self._tokens.values())

    # ── Minting ──────────────────────────────────────────────────────────

    async def mint(
        self,
        token_id: str,
        amount: float,
        recipient_id: str,
        reason: str = "",
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Mint new tokens to a recipient."""
        if amount <= 0:
            return False, "Amount must be positive"

        token = await self.get_token(token_id)
        if not token:
            return False, f"Token {token_id} not found"

        event = TokenMintEvent(
            event_id=f"mint_{uuid.uuid4().hex[:16]}",
            token_id=token_id,
            standard=token.standard,
            amount=amount,
            recipient_id=recipient_id,
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )

        token.total_supply += amount
        token.circulating_supply += amount

        # Create or update holding
        holding = await self._get_or_create_holding(recipient_id, token_id, token.standard)
        holding.amount += amount

        async with self._lock:
            self._mint_events.append(event)
        await self._append_ledger("mint", event.to_dict())
        await self._append_ledger("token_def", token.to_dict())
        await self._append_ledger("holding", holding.to_dict())

        logger.info(f"Minted {amount} {token.symbol} -> {recipient_id}")
        return True, event.event_id

    async def burn(
        self,
        owner_id: str,
        token_id: str,
        amount: float,
        reason: str = "",
    ) -> Tuple[bool, str]:
        """Burn tokens from an owner's holding."""
        if amount <= 0:
            return False, "Amount must be positive"

        token = await self.get_token(token_id)
        if not token:
            return False, f"Token {token_id} not found"

        holding = await self.get_holding(owner_id, token_id)
        if not holding:
            return False, "No holding found for this owner/token"
        if holding.available < amount:
            return False, f"Insufficient available balance (have {holding.available}, need {amount})"

        holding.amount -= amount
        token.total_supply -= amount
        token.circulating_supply -= amount

        event = TokenMintEvent(
            event_id=f"burn_{uuid.uuid4().hex[:16]}",
            token_id=token_id,
            standard=token.standard,
            amount=-amount,
            recipient_id=owner_id,
            reason=reason or "burn",
            timestamp=datetime.utcnow().isoformat(),
        )

        async with self._lock:
            self._mint_events.append(event)
        await self._append_ledger("mint", event.to_dict())
        await self._append_ledger("token_def", token.to_dict())
        await self._append_ledger("holding", holding.to_dict())

        logger.info(f"Burned {amount} {token.symbol} from {owner_id}")
        return True, event.event_id

    # ── Holdings ─────────────────────────────────────────────────────────

    async def _get_or_create_holding(
        self, owner_id: str, token_id: str, standard: str
    ) -> TokenHolding:
        """Get or create a holding for an owner/token pair."""
        existing = await self.get_holding(owner_id, token_id)
        if existing:
            return existing

        holding = TokenHolding(
            holding_id=f"hold_{uuid.uuid4().hex[:16]}",
            token_id=token_id,
            owner_id=owner_id,
            standard=standard,
            amount=0.0,
            acquired_at=datetime.utcnow().isoformat(),
        )
        async with self._lock:
            self._holdings[holding.holding_id] = holding
            self._owner_holdings.setdefault(owner_id, []).append(holding.holding_id)
        return holding

    async def get_holding(self, owner_id: str, token_id: str) -> Optional[TokenHolding]:
        """Get a specific holding for an owner and token."""
        await self._ensure_loaded()
        for hid in self._owner_holdings.get(owner_id, []):
            h = self._holdings.get(hid)
            if h and h.token_id == token_id:
                return h
        return None

    async def get_owner_holdings(self, owner_id: str) -> List[TokenHolding]:
        """Get all holdings for an owner."""
        await self._ensure_loaded()
        return [
            self._holdings[hid] for hid in self._owner_holdings.get(owner_id, [])
            if hid in self._holdings
        ]

    async def get_owner_balance(self, owner_id: str, token_id: str) -> float:
        """Get available balance for an owner-token pair."""
        holding = await self.get_holding(owner_id, token_id)
        return holding.available if holding else 0.0

    async def lock_tokens(
        self, owner_id: str, token_id: str, amount: float
    ) -> Tuple[bool, str]:
        """Lock tokens (for staking, escrow, etc.)."""
        holding = await self.get_holding(owner_id, token_id)
        if not holding:
            return False, "Holding not found"
        if holding.available < amount:
            return False, "Insufficient available balance"
        holding.locked_amount += amount
        await self._append_ledger("holding", holding.to_dict())
        return True, holding.holding_id

    async def unlock_tokens(
        self, owner_id: str, token_id: str, amount: float
    ) -> Tuple[bool, str]:
        """Unlock previously locked tokens."""
        holding = await self.get_holding(owner_id, token_id)
        if not holding:
            return False, "Holding not found"
        if holding.locked_amount < amount:
            return False, "Insufficient locked balance"
        holding.locked_amount -= amount
        await self._append_ledger("holding", holding.to_dict())
        return True, holding.holding_id

    # ── Stats ────────────────────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """Get token registry statistics."""
        await self._ensure_loaded()
        return {
            "total_tokens": len(self._tokens),
            "total_holdings": len(self._holdings),
            "total_mint_events": len(self._mint_events),
            "nexus_supply": sum(
                t.total_supply for t in self._tokens.values()
                if t.standard == "nexus"
            ),
            "svt_count": sum(
                1 for t in self._tokens.values() if t.standard == "svt"
            ),
            "hdt_count": sum(
                1 for t in self._tokens.values() if t.standard == "hdt"
            ),
        }


# ── Default Tokens ───────────────────────────────────────────────────────────

DEFAULT_TOKENS = [
    {"standard": "nexus", "name": "Nexus Core Token", "symbol": "NEXUS", "total_supply": 1_000_000_000},
    {"standard": "svt", "name": "Soul-Bound Token", "symbol": "SVT", "total_supply": 0, "is_soul_bound": True},
    {"standard": "hdt", "name": "Holonic Digital Twin", "symbol": "HDT", "total_supply": 0, "is_soul_bound": True},
]


async def initialize_default_tokens(registry: Optional[TokenRegistry] = None) -> TokenRegistry:
    """Initialize the token registry with default tokens."""
    reg = registry or get_token_registry()
    for tdef in DEFAULT_TOKENS:
        existing = await reg.get_token_by_symbol(tdef["symbol"])
        if not existing:
            await reg.register_token(**tdef)
    logger.info("Default tokens initialized")
    return reg


# ── Singleton ────────────────────────────────────────────────────────────────

_registry: Optional[TokenRegistry] = None


def get_token_registry() -> TokenRegistry:
    """Get or create the singleton token registry."""
    global _registry
    if _registry is None:
        _registry = TokenRegistry()
    return _registry


def reset_token_registry():
    """Reset the token registry (for testing)."""
    global _registry
    _registry = None
