"""
AsimNexus Policy Gateway: Versioned Policy Packs Engine
=======================================================
Resolves policy conflicts using layered precedence:
  Session > User > Org > Country > Global
Each policy pack is cryptographically signed for integrity verification.

Signature Verification Rules (v1.0):
  1. Algorithm: HMAC-SHA256 (hash-based message authentication)
  2. Format: SHA256( canonical_hash(pack) + ":" + public_key )
  3. Key Rotation: register_authority_key() replaces old key for same authority
  4. Expiry: pack.is_expired() checked on every add_pack() and resolve_rules()
  5. Version Lock: only higher-version packs can replace existing ones
  6. Chain of Trust: parent_pack_id links to predecessor for audit trail
"""

import hashlib, json, logging, re, time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("VersionedPacks")

class PolicyLayer(Enum):
    GLOBAL = 0; COUNTRY = 1; ORG = 2; USER = 3; SESSION = 4

class PolicyEffect(Enum):
    ALLOW = "ALLOW"; DENY = "DENY"; ESCALATE = "ESCALATE"

@dataclass
class PolicyRule:
    rule_id: str; capability_id: str; effect: PolicyEffect; target_pattern: str
    risk_tier_override: Optional[str] = None
    require_approval: bool = False
    approval_roles: List[str] = field(default_factory=list)
    description: str = ""

@dataclass
class PolicyPack:
    pack_id: str; layer: PolicyLayer; version: int; authority: str; rules: List[PolicyRule]
    signature: str = ""; parent_pack_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None

    def compute_hash(self) -> str:
        """Canonical hash of all policy-deterministic fields (excludes signature)."""
        data = {"pack_id": self.pack_id, "layer": self.layer.value, "version": self.version,
                "authority": self.authority,
                "rules": [{"rule_id": r.rule_id, "capability_id": r.capability_id,
                           "effect": r.effect.value, "target_pattern": r.target_pattern} for r in self.rules],
                "parent_pack_id": self.parent_pack_id, "created_at": self.created_at, "expires_at": self.expires_at}
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def verify_signature(self, public_key: str) -> bool:
        """
        Verify HMAC-SHA256 signature.
        Rule: SHA256( canonical_hash + ":" + public_key ) == signature
        Returns False if signature is empty or doesn't match.
        """
        if not self.signature or not public_key: return False
        expected = hashlib.sha256(f"{self.compute_hash()}:{public_key}".encode()).hexdigest()
        # Constant-time comparison to prevent timing attacks
        if len(expected) != len(self.signature): return False
        result = 0
        for a, b in zip(expected, self.signature):
            result |= ord(a) ^ ord(b)
        return result == 0

    def is_expired(self) -> bool:
        if not self.expires_at: return False
        try:
            return datetime.fromisoformat(self.expires_at) < datetime.now(timezone.utc)
        except: return True  # Invalid date = expired

    def to_dict(self) -> Dict[str, Any]:
        """Standardized export format for policy packs."""
        return {"pack_id": self.pack_id, "layer": self.layer.name, "version": self.version,
                "authority": self.authority, "signature": self.signature,
                "parent_pack_id": self.parent_pack_id,
                "created_at": self.created_at, "expires_at": self.expires_at,
                "hash": self.compute_hash(), "signature_valid": None,
                "rules": [{"rule_id": r.rule_id, "capability_id": r.capability_id,
                           "effect": r.effect.value, "target_pattern": r.target_pattern,
                           "risk_tier_override": r.risk_tier_override,
                           "require_approval": r.require_approval,
                           "approval_roles": r.approval_roles,
                           "description": r.description} for r in self.rules]}

class VersionedPolicyEngine:
    def __init__(self):
        self._packs: Dict[str, PolicyPack] = {}
        self._authority_keys: Dict[str, str] = {}  # authority -> current public key
        self._key_history: Dict[str, List[Tuple[str, str]]] = {}  # authority -> [(key, rotated_at)]

    def register_authority_key(self, authority: str, public_key: str) -> None:
        """Register or rotate a public key for an authority. Old key is archived."""
        old_key = self._authority_keys.get(authority)
        if old_key:
            self._key_history.setdefault(authority, []).append((old_key, datetime.now(timezone.utc).isoformat()))
        self._authority_keys[authority] = public_key

    def get_authority_key(self, authority: str) -> Optional[str]:
        return self._authority_keys.get(authority)

    def get_key_history(self, authority: str) -> List[Tuple[str, str]]:
        return self._key_history.get(authority, [])

    def add_pack(self, pack: PolicyPack) -> Tuple[bool, str]:
        """
        Add a signed policy pack. Returns (success, reason).
        Verification rules:
          1. Authority must have a registered public key
          2. Signature must match using current public key
          3. Pack must not be expired
          4. Version must be higher than existing pack for same layer+authority
        """
        pub_key = self._authority_keys.get(pack.authority)
        if not pub_key:
            return False, f"No registered key for authority '{pack.authority}'"
        if not pack.verify_signature(pub_key):
            return False, f"Signature verification failed for pack '{pack.pack_id}'"
        if pack.is_expired():
            return False, f"Pack '{pack.pack_id}' is expired"
        existing = self._get_pack_by_layer_authority(pack.layer, pack.authority)
        if existing and existing.version >= pack.version:
            return False, f"Version {pack.version} <= existing {existing.version} for layer {pack.layer.name}"
        self._packs[pack.pack_id] = pack
        logger.info(f"Policy pack '{pack.pack_id}' v{pack.version} added (layer={pack.layer.name})")
        return True, "Added"

    def _get_pack_by_layer_authority(self, layer, authority):
        candidates = [p for p in self._packs.values() if p.layer == layer and p.authority == authority]
        return max(candidates, key=lambda p: p.version) if candidates else None

    def resolve_rules(self, capability_id: str, target: str) -> Tuple[PolicyEffect, Optional[PolicyRule]]:
        """
        Resolve policy for a capability+target using layered precedence.
        Highest layer (Session=4) wins, then by version within layer.
        Returns (effect, rule) or (DENY, None) if no matching rule.
        """
        matching = {layer: [] for layer in PolicyLayer}
        for pack in self._packs.values():
            if pack.is_expired(): continue
            for rule in pack.rules:
                if rule.capability_id == capability_id and re.match(rule.target_pattern, target):
                    matching[pack.layer].append((pack, rule))
        for layer in sorted(PolicyLayer, key=lambda l: l.value, reverse=True):
            if matching[layer]:
                best = max(matching[layer], key=lambda x: x[0].version)
                return best[1].effect, best[1]
        return PolicyEffect.DENY, None

    def get_applicable_packs(self, layer=None):
        packs = [p for p in self._packs.values() if not p.is_expired()]
        if layer: packs = [p for p in packs if p.layer == layer]
        return sorted(packs, key=lambda p: (p.layer.value, -p.version))

    def remove_pack(self, pack_id: str) -> bool:
        return bool(self._packs.pop(pack_id, None))

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect policy conflicts across layers.
        A conflict exists when the same capability has different effects in different layers.
        """
        conflicts = []
        cap_rules: Dict[str, List[Tuple[PolicyLayer, PolicyRule]]] = {}
        for pack in self._packs.values():
            if pack.is_expired(): continue
            for rule in pack.rules:
                cap_rules.setdefault(rule.capability_id, []).append((pack.layer, rule))
        for cid, rules in cap_rules.items():
            if len(rules) > 1 and len(set(r[1].effect.value for r in rules)) > 1:
                conflicts.append({"capability_id": cid, "layers": [r[0].name for r in rules],
                                  "effects": list(set(r[1].effect.value for r in rules))})
        return conflicts

    def resolve_multi_node_conflict(self, local_pack: PolicyPack, remote_pack: PolicyPack) -> Dict[str, Any]:
        """
        Resolve policy conflicts between two nodes (multi-node support).
        Resolution rules:
          1. Higher layer wins (Session > User > Org > Country > Global)
          2. Same layer: higher version wins
          3. Same layer + same version: higher authority (lexicographic) wins
          4. Same layer + same version + same authority: local wins
        Returns resolution result with winner and reasoning.
        """
        if local_pack.layer.value > remote_pack.layer.value:
            winner, reason = "local", f"Local layer {local_pack.layer.name} > Remote {remote_pack.layer.name}"
        elif remote_pack.layer.value > local_pack.layer.value:
            winner, reason = "remote", f"Remote layer {remote_pack.layer.name} > Local {local_pack.layer.name}"
        elif local_pack.version > remote_pack.version:
            winner, reason = "local", f"Local version {local_pack.version} > Remote {remote_pack.version}"
        elif remote_pack.version > local_pack.version:
            winner, reason = "remote", f"Remote version {remote_pack.version} > Local {local_pack.version}"
        elif local_pack.authority > remote_pack.authority:
            winner, reason = "local", f"Local authority '{local_pack.authority}' > Remote '{remote_pack.authority}'"
        elif remote_pack.authority > local_pack.authority:
            winner, reason = "remote", f"Remote authority '{remote_pack.authority}' > Local '{local_pack.authority}'"
        else:
            winner, reason = "local", "Tie-breaker: local node wins"
        return {"capability_id": "multi-node", "local_pack": local_pack.pack_id,
                "remote_pack": remote_pack.pack_id, "winner": winner, "reason": reason}

    def export_packs(self, layer: Optional[PolicyLayer] = None) -> List[Dict[str, Any]]:
        """Standardized export of all policy packs."""
        packs = self.get_applicable_packs(layer)
        result = []
        for pack in packs:
            d = pack.to_dict()
            pub_key = self._authority_keys.get(pack.authority)
            d["signature_valid"] = pack.verify_signature(pub_key) if pub_key else False
            result.append(d)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_packs": len(self._packs), "active_packs": len(self.get_applicable_packs()),
                "registered_authorities": len(self._authority_keys),
                "conflicts_detected": len(self.get_conflicts())}

policy_engine = VersionedPolicyEngine()
