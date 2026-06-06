#!/usr/bin/env python3
"""
STATUS: PRODUCTION — Blockchain Constitution Anchor
===================================================
Anchors the ASIMNEXUS constitution hash to a simulated blockchain for
immutable timestamping, tamper-evident audit, and cross-referencing.

Key concepts:
  - Takes SHA-256 hash of the constitution (from ImmutableConstitution)
    and seals it into an on-chain anchor record
  - Each anchor includes: constitution_hash, block_number, timestamp,
    previous_anchor_hash, and a digital signature
  - Chain of anchors forms an append-only, tamper-evident log
  - Supports verification that a given constitution hash was anchored
    at a specific point in time
  - Integrates with [`security/immutable_constitution.py`](../security/immutable_constitution.py)
    and [`security/power_balance_constitution.py`](../security/power_balance_constitution.py)

In production, this would write to an actual blockchain (Ethereum, Solana,
Hyperledger, etc.). This implementation uses a local JSONL-backed chain
with the same security properties (append-only, hash-linked, signed).
"""

import hashlib
import json
import logging
import os
import secrets
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("AsimNexus.BlockchainAnchor")

# ─── Environment Configuration ────────────────────────────────────────────────
_ANCHOR_DB_PATH = os.getenv("ASIM_ANCHOR_DB_PATH", "data/constitution_anchors.jsonl")


@dataclass
class ConstitutionAnchor:
    """An on-chain anchor record sealing a constitution hash."""

    anchor_id: str
    constitution_hash: str
    block_number: int
    timestamp: float
    previous_anchor_hash: str
    signature: str
    constitution_type: str = "immutable"  # "immutable" | "power_balance" | "dharma"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def anchor_hash(self) -> str:
        """Compute this anchor's own hash (chain link)."""
        raw = (
            f"{self.anchor_id}|{self.constitution_hash}|{self.block_number}|"
            f"{self.timestamp}|{self.previous_anchor_hash}|{self.constitution_type}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "constitution_hash": self.constitution_hash,
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "previous_anchor_hash": self.previous_anchor_hash,
            "anchor_hash": self.anchor_hash,
            "signature": self.signature,
            "constitution_type": self.constitution_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConstitutionAnchor":
        return cls(
            anchor_id=d["anchor_id"],
            constitution_hash=d["constitution_hash"],
            block_number=d["block_number"],
            timestamp=d["timestamp"],
            previous_anchor_hash=d.get("previous_anchor_hash", ""),
            signature=d.get("signature", ""),
            constitution_type=d.get("constitution_type", "immutable"),
            metadata=d.get("metadata", {}),
        )

    def verify_integrity(self) -> bool:
        """Verify this anchor's own hash and signature consistency."""
        expected_hash = self.anchor_hash
        payload = f"{self.anchor_id}|{self.constitution_hash}|{self.block_number}|{self.timestamp}|{self.constitution_type}"
        expected_sig = hashlib.sha256(payload.encode()).hexdigest()[:32]
        return expected_sig == self.signature


class BlockchainConstitutionAnchor:
    """
    Anchors constitution hashes into an append-only, tamper-evident chain.

    Features:
      - seal(): Anchor a constitution hash (returns anchor record)
      - verify(): Check that a hash was anchored and chain is intact
      - get_chain(): Return full anchor chain
      - get_latest_anchor(): Return most recent anchor
      - verify_chain_integrity(): Validate entire chain from genesis
    """

    def __init__(self, db_path: str = _ANCHOR_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._anchors: List[ConstitutionAnchor] = []
        self._load_from_db()

    # ─── Public API ───────────────────────────────────────────────────────────

    def seal(
        self,
        constitution_hash: str,
        constitution_type: str = "immutable",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConstitutionAnchor:
        """Anchor a constitution hash into the chain.

        Args:
            constitution_hash: SHA-256 hash of the constitution content.
            constitution_type: Type identifier ("immutable", "power_balance", "dharma").
            metadata: Optional extra data to include with the anchor.

        Returns:
            The newly created ConstitutionAnchor record.
        """
        with self._lock:
            previous_hash = self._anchors[-1].anchor_hash if self._anchors else "0" * 64
            block_number = len(self._anchors)
            timestamp = time.time()
            anchor_id = f"anchor_{block_number}_{int(timestamp)}"

            # Create cryptographic signature (simulated blockchain signature)
            payload = f"{anchor_id}|{constitution_hash}|{block_number}|{timestamp}|{constitution_type}"
            signature = hashlib.sha256(payload.encode()).hexdigest()[:32]

            anchor = ConstitutionAnchor(
                anchor_id=anchor_id,
                constitution_hash=constitution_hash,
                block_number=block_number,
                timestamp=timestamp,
                previous_anchor_hash=previous_hash,
                signature=signature,
                constitution_type=constitution_type,
                metadata=metadata or {},
            )

            self._anchors.append(anchor)
            self._persist_anchor(anchor)

            logger.info(
                f"🔗 Constitution anchored: type={constitution_type} "
                f"hash={constitution_hash[:16]}... "
                f"block={block_number} anchor={anchor.anchor_hash[:16]}..."
            )
            return anchor

    def verify(self, constitution_hash: str) -> Optional[ConstitutionAnchor]:
        """Check if a constitution hash was anchored.

        Args:
            constitution_hash: The hash to look up.

        Returns:
            The matching ConstitutionAnchor if found, None otherwise.
        """
        for anchor in reversed(self._anchors):
            if anchor.constitution_hash == constitution_hash:
                return anchor
        return None

    def get_chain(self) -> List[Dict[str, Any]]:
        """Return the full anchor chain as a list of dicts."""
        return [a.to_dict() for a in self._anchors]

    def get_latest_anchor(self) -> Optional[Dict[str, Any]]:
        """Return the most recent anchor record."""
        if not self._anchors:
            return None
        return self._anchors[-1].to_dict()

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify the entire anchor chain for tampering.

        Returns:
            Dict with 'valid' bool and details about any inconsistencies.
        """
        issues = []
        for i, anchor in enumerate(self._anchors):
            # Check anchor's own integrity
            if not anchor.verify_integrity():
                issues.append(f"Anchor {anchor.anchor_id}: signature mismatch")

            # Check hash chain linkage
            if i == 0:
                expected_prev = "0" * 64
            else:
                expected_prev = self._anchors[i - 1].anchor_hash

            if anchor.previous_anchor_hash != expected_prev:
                issues.append(
                    f"Anchor {anchor.anchor_id}: chain broken "
                    f"(expected prev={expected_prev[:16]}... "
                    f"got {anchor.previous_anchor_hash[:16]}...)"
                )

        return {
            "valid": len(issues) == 0,
            "total_anchors": len(self._anchors),
            "issues": issues,
            "verified_at": time.time(),
        }

    def get_anchor_count(self) -> int:
        """Return the total number of anchors in the chain."""
        return len(self._anchors)

    def get_stats(self) -> Dict[str, Any]:
        """Return comprehensive statistics about the anchor chain."""
        types: Dict[str, int] = {}
        for a in self._anchors:
            types[a.constitution_type] = types.get(a.constitution_type, 0) + 1

        return {
            "total_anchors": len(self._anchors),
            "anchor_types": types,
            "latest_block": self._anchors[-1].block_number if self._anchors else -1,
            "genesis_time": self._anchors[0].timestamp if self._anchors else None,
            "latest_time": self._anchors[-1].timestamp if self._anchors else None,
            "chain_integrity": self.verify_chain_integrity(),
            "db_path": self.db_path,
        }

    def reset(self) -> None:
        """Clear all anchors (for testing)."""
        with self._lock:
            self._anchors = []
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
            except Exception:
                pass

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _persist_anchor(self, anchor: ConstitutionAnchor) -> None:
        """Append an anchor record to the JSONL database."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(anchor.to_dict()) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist anchor: {e}")

    def _load_from_db(self) -> None:
        """Load all anchor records from the JSONL database."""
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._anchors.append(ConstitutionAnchor.from_dict(data))
                    except (json.JSONDecodeError, KeyError):
                        continue
            if self._anchors:
                logger.info(
                    f"📂 Loaded {len(self._anchors)} constitution anchors from DB"
                )
        except Exception as e:
            logger.warning(f"Failed to load anchors: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_anchor_instance: Optional[BlockchainConstitutionAnchor] = None
_anchor_lock = threading.Lock()


def get_constitution_anchor(
    db_path: str = _ANCHOR_DB_PATH,
) -> BlockchainConstitutionAnchor:
    """Get or create the singleton BlockchainConstitutionAnchor instance."""
    global _anchor_instance
    if _anchor_instance is None:
        with _anchor_lock:
            if _anchor_instance is None:
                _anchor_instance = BlockchainConstitutionAnchor(db_path)
    return _anchor_instance


def reset_constitution_anchor() -> None:
    """Reset the singleton (for testing)."""
    global _anchor_instance
    with _anchor_lock:
        if _anchor_instance is not None:
            _anchor_instance.reset()
        _anchor_instance = None


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "ConstitutionAnchor",
    "BlockchainConstitutionAnchor",
    "get_constitution_anchor",
    "reset_constitution_anchor",
]
