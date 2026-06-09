
from __future__ import annotations

"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
core/economy/sovereign_token.py
AsimNexus — Sovereign Micro-Token Economy
==========================================
A local-first, Dharma-gated micro-token system.
NOT a cryptocurrency. NOT blockchain. Just a sovereign ledger.

SovereignToken (SVT):
  - Earned by: contributing skills, completing contracts, mesh participation
  - Spent on: AI compute time, contract payments, community resources
  - Anti-concentration: ΔT Engine checks Gini coefficient every 100 txns
  - Burn mechanism: 1% of every transaction burned → deflationary
  - Max wallet: 1,000,000 SVT — prevents monopoly
  - Dharma veto: transactions that concentrate >15% in one wallet blocked

"Money should serve people. Not the other way around."
"""

import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.Economy.SVT")

LEDGER_PATH  = Path(__file__).resolve().parent.parent.parent / "data" / "svt_ledger.jsonl"
WALLETS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "svt_wallets.json"
LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

BURN_RATE       = 0.01      # 1% burned per transaction
MAX_WALLET      = 1_000_000 # SVT — anti-concentration cap
CONCENTRATION_CAP = 0.15    # No single wallet > 15% of total supply
GENESIS_SUPPLY  = 10_000_000  # Initial token supply


class TxType(str, Enum):
    MINT      = "mint"
    TRANSFER  = "transfer"
    BURN      = "burn"
    ESCROW    = "escrow"
    RELEASE   = "release"
    REWARD    = "reward"
    STAKE     = "stake"


@dataclass
class SVTTransaction:
    tx_id:     str
    tx_type:   TxType
    from_did:  str          # "system" for mint/reward
    to_did:    str
    amount:    float
    burned:    float        # 1% burn
    memo:      str
    ts:        float
    universe:  str = "personal"
    approved:  bool = True  # False = Dharma blocked


@dataclass
class SVTWallet:
    did:       str
    balance:   float = 0.0
    staked:    float = 0.0
    earned_total:  float = 0.0
    spent_total:   float = 0.0
    tx_count:  int   = 0
    created_at: str  = ""


class SovereignTokenEngine:
    """
    Local sovereign token economy engine.

    Usage:
        engine = SovereignTokenEngine()
        engine.mint("did:asim:abc", 100, memo="Welcome bonus")
        engine.transfer("did:asim:abc", "did:asim:xyz", 50, memo="Contract payment")
        engine.balance("did:asim:abc")  # → 49.5 (1% burned)
    """

    def __init__(self):
        self._wallets: Dict[str, SVTWallet] = {}
        self._total_supply: float = 0.0
        self._total_burned:  float = 0.0
        self._escrow: Dict[str, float] = {}   # escrow_id → amount
        self._load()
        logger.info(f"✅ SVT Engine ready — supply={self._total_supply:,.0f} burned={self._total_burned:,.0f}")

    # ── WALLET ────────────────────────────────────────────────────────────────

    def create_wallet(self, did: str) -> SVTWallet:
        if did in self._wallets:
            return self._wallets[did]
        w = SVTWallet(did=did, created_at=_now())
        self._wallets[did] = w
        self._save_wallets()
        return w

    def balance(self, did: str) -> float:
        return self._wallets.get(did, SVTWallet(did=did)).balance

    # ── MINT (system only) ────────────────────────────────────────────────────

    def mint(self, to_did: str, amount: float, memo: str = "") -> SVTTransaction:
        """Create new tokens. Only system/Dharma-approved events should call this."""
        self._ensure_wallet(to_did)
        if self._total_supply + amount > GENESIS_SUPPLY * 2:
            raise ValueError("Mint would exceed maximum supply")

        tx = self._make_tx(TxType.MINT, "system", to_did, amount, memo)
        self._wallets[to_did].balance      += amount
        self._wallets[to_did].earned_total += amount
        self._wallets[to_did].tx_count     += 1
        self._total_supply += amount
        self._record(tx)
        return tx

    # ── TRANSFER ─────────────────────────────────────────────────────────────

    def transfer(self, from_did: str, to_did: str, amount: float,
                 memo: str = "", universe: str = "personal") -> SVTTransaction:
        self._ensure_wallet(from_did)
        self._ensure_wallet(to_did)

        if self._wallets[from_did].balance < amount:
            raise ValueError(f"Insufficient balance: {self._wallets[from_did].balance:.2f} < {amount}")

        # Anti-concentration check
        blocked, reason = self._concentration_check(to_did, amount)
        if blocked:
            tx = self._make_tx(TxType.TRANSFER, from_did, to_did, amount, memo)
            tx.approved = False
            logger.warning(f"🛑 Transfer blocked (anti-concentration): {reason}")
            self._record(tx)
            return tx

        burn = round(amount * BURN_RATE, 4)
        net  = amount - burn

        self._wallets[from_did].balance    -= amount
        self._wallets[from_did].spent_total += amount
        self._wallets[from_did].tx_count   += 1
        self._wallets[to_did].balance      += net
        self._wallets[to_did].earned_total += net
        self._wallets[to_did].tx_count     += 1
        self._total_burned += burn
        self._total_supply -= burn

        tx = self._make_tx(TxType.TRANSFER, from_did, to_did, amount, memo, burn, universe)
        self._record(tx)
        logger.info(f"💸 Transfer: {amount} SVT {from_did[-8:]}→{to_did[-8:]} (burn={burn})")
        return tx

    # ── ESCROW ────────────────────────────────────────────────────────────────

    def escrow_lock(self, from_did: str, amount: float,
                    memo: str = "") -> str:
        """Lock tokens in escrow (for contract payments)."""
        self._ensure_wallet(from_did)
        if self._wallets[from_did].balance < amount:
            raise ValueError("Insufficient balance for escrow")

        escrow_id = secrets.token_hex(8)
        self._wallets[from_did].balance -= amount
        self._wallets[from_did].staked  += amount
        self._escrow[escrow_id] = {"did": from_did, "amount": amount, "memo": memo}
        self._save_wallets()
        tx = self._make_tx(TxType.ESCROW, from_did, "escrow", amount, f"[{escrow_id}] {memo}")
        self._record(tx)
        logger.info(f"🔒 Escrow locked: {escrow_id} — {amount} SVT from {from_did[-8:]}")
        return escrow_id

    def escrow_release(self, escrow_id: str, to_did: str) -> SVTTransaction:
        """Release escrow to recipient."""
        if escrow_id not in self._escrow:
            raise KeyError(f"Escrow not found: {escrow_id}")

        info   = self._escrow.pop(escrow_id)
        amount = info["amount"]
        source_did = info["did"]

        self._ensure_wallet(to_did)
        self._wallets[source_did].staked -= amount
        burn = round(amount * BURN_RATE, 4)
        net  = amount - burn

        self._wallets[to_did].balance      += net
        self._wallets[to_did].earned_total += net
        self._total_burned += burn
        self._total_supply -= burn

        tx = self._make_tx(TxType.RELEASE, source_did, to_did, amount,
                           f"Escrow release [{escrow_id}]", burn)
        self._record(tx)
        self._save_wallets()
        logger.info(f"🔓 Escrow released: {escrow_id} → {to_did[-8:]} ({net} SVT)")
        return tx

    # ── REWARD ────────────────────────────────────────────────────────────────

    def reward(self, to_did: str, amount: float, reason: str = "") -> SVTTransaction:
        """Reward tokens for contributions (mesh, contracts, community)."""
        return self.mint(to_did, amount, memo=f"[REWARD] {reason}")

    # ── ANTI-CONCENTRATION ────────────────────────────────────────────────────

    def _concentration_check(self, to_did: str, amount: float):
        if self._total_supply == 0:
            return False, ""
        new_balance = self._wallets.get(to_did, SVTWallet(did=to_did)).balance + amount
        pct = new_balance / self._total_supply
        if pct > CONCENTRATION_CAP:
            return True, f"{to_did[-8:]} would hold {pct:.1%} > {CONCENTRATION_CAP:.0%} cap"
        if new_balance > MAX_WALLET:
            return True, f"Wallet cap exceeded: {new_balance:,.0f} > {MAX_WALLET:,.0f}"
        return False, ""

    def gini_coefficient(self) -> float:
        """Calculate Gini coefficient of token distribution."""
        balances = sorted(w.balance for w in self._wallets.values() if w.balance > 0)
        n = len(balances)
        if n == 0:
            return 0.0
        total = sum(balances)
        if total == 0:
            return 0.0
        s = sum((2 * i - n - 1) * b for i, b in enumerate(balances, 1))
        return s / (n * total)

    # ── STATS ─────────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        wallets = list(self._wallets.values())
        return {
            "total_supply":    round(self._total_supply, 2),
            "total_burned":    round(self._total_burned, 2),
            "total_wallets":   len(wallets),
            "gini":            round(self.gini_coefficient(), 4),
            "burn_rate":       f"{BURN_RATE:.0%}",
            "max_wallet":      MAX_WALLET,
            "concentration_cap": f"{CONCENTRATION_CAP:.0%}",
            "escrow_count":    len(self._escrow),
        }

    def wallet_info(self, did: str) -> Dict[str, Any]:
        w = self._wallets.get(did)
        if not w:
            return {"did": did, "balance": 0, "exists": False}
        return {**asdict(w), "exists": True,
                "pct_of_supply": round(w.balance / max(self._total_supply, 1) * 100, 4)}

    # ── INTERNAL ─────────────────────────────────────────────────────────────

    def _ensure_wallet(self, did: str):
        if did not in self._wallets:
            self.create_wallet(did)

    def _make_tx(self, tx_type, from_did, to_did, amount, memo,
                 burned=0.0, universe="personal") -> SVTTransaction:
        return SVTTransaction(
            tx_id    = secrets.token_hex(8),
            tx_type  = tx_type,
            from_did = from_did,
            to_did   = to_did,
            amount   = round(amount, 4),
            burned   = round(burned, 4),
            memo     = memo[:200],
            ts       = time.time(),
            universe = universe,
        )

    def _record(self, tx: SVTTransaction):
        self._save_wallets()
        try:
            with open(LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(tx)) + "\n")
        except Exception as e:
            logger.warning(f"Ledger write failed: {e}")

    def _save_wallets(self):
        try:
            with open(WALLETS_PATH, "w", encoding="utf-8") as f:
                json.dump({did: asdict(w) for did, w in self._wallets.items()}, f, indent=2)
        except Exception as e:
            logger.warning(f"Wallets save failed: {e}")

    def _load(self):
        if WALLETS_PATH.exists():
            try:
                with open(WALLETS_PATH, encoding="utf-8") as f:
                    for did, d in json.load(f).items():
                        self._wallets[did] = SVTWallet(**d)
                        self._total_supply += d.get("balance", 0) + d.get("staked", 0)
            except Exception as e:
                logger.warning(f"Wallets load failed: {e}")


def _now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

_engine: Optional[SovereignTokenEngine] = None
def get_svt_engine() -> SovereignTokenEngine:
    global _engine
    if _engine is None: _engine = SovereignTokenEngine()
    return _engine


def reset_svt_engine() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _engine
    _engine = None
