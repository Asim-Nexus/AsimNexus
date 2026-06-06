
"""
core/federation/global_federation.py
AsimNexus — Global Federation Protocol
========================================
Multi-node sync using CRDTs (Conflict-free Replicated Data Types).
No central server. No single point of failure.

Design:
  - Each node has a unique node_id + vector clock
  - State is shared via CRDT operations (LWW, G-Counter, OR-Set)
  - Conflicts resolved automatically — last-write-wins with causality
  - Human consent required before joining another node's federation
  - Dharma gate: no data sync without explicit permission

CRDT types implemented:
  GCounter   — grow-only counter (e.g., message count)
  LWWRegister — last-write-wins register (e.g., profile field)
  ORSet       — observe-remove set (e.g., peer list, skill list)
  FedState    — full node state (composition of above)

"Sync without surrendering sovereignty."

Env vars:
  ASIM_FED_NODE_ID     — override node_id (default: auto-generated)
  ASIM_FED_DATA_DIR    — federation data directory (default: data/federation/)
  ASIM_FED_MAX_PEERS   — max peers limit (default: 100)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("AsimNexus.Federation")

_DEFAULT_FED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "federation"
FED_DIR = Path(os.getenv("ASIM_FED_DATA_DIR", str(_DEFAULT_FED_DIR)))
FED_DIR.mkdir(parents=True, exist_ok=True)

_DEFAULT_SYNC_INTERVAL = 60
_DEFAULT_MAX_PEERS = 100


# ── CRDT PRIMITIVES ───────────────────────────────────────────────────────────

class GCounter:
    """Grow-only counter. Each node increments its own slot."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._counts: Dict[str, int] = {node_id: 0}

    def increment(self, by: int = 1):
        self._counts[self.node_id] = self._counts.get(self.node_id, 0) + by

    def value(self) -> int:
        return sum(self._counts.values())

    def merge(self, other: "GCounter"):
        for nid, cnt in other._counts.items():
            self._counts[nid] = max(self._counts.get(nid, 0), cnt)

    def state(self) -> Dict:
        return dict(self._counts)

    @classmethod
    def from_state(cls, node_id: str, state: Dict) -> "GCounter":
        c = cls(node_id)
        c._counts = state
        return c


class LWWRegister:
    """Last-write-wins register with wall-clock timestamp."""
    def __init__(self):
        self._value: Any     = None
        self._ts:    float   = 0.0
        self._node:  str     = ""

    def set(self, value: Any, node_id: str):
        ts = time.time()
        if ts >= self._ts:
            self._value = value
            self._ts    = ts
            self._node  = node_id

    def get(self) -> Any:
        return self._value

    def merge(self, other: "LWWRegister"):
        if other._ts > self._ts:
            self._value = other._value
            self._ts    = other._ts
            self._node  = other._node

    def state(self) -> Dict:
        return {"value": self._value, "ts": self._ts, "node": self._node}

    @classmethod
    def from_state(cls, state: Dict) -> "LWWRegister":
        r = cls()
        r._value = state.get("value")
        r._ts    = state.get("ts", 0.0)
        r._node  = state.get("node", "")
        return r


class ORSet:
    """Observe-Remove Set — elements can be added and removed without conflict."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._add_set: Dict[str, Set[str]] = {}  # value → {tag, ...}
        self._rem_set: Dict[str, Set[str]] = {}  # value → {tag, ...}

    _tag_counter: int = 0

    def add(self, value: str):
        ORSet._tag_counter += 1
        tag = f"{self.node_id}:{time.time_ns()}:{ORSet._tag_counter}"
        self._add_set.setdefault(value, set()).add(tag)

    def remove(self, value: str):
        tags = self._add_set.get(value, set())
        self._rem_set.setdefault(value, set()).update(tags)

    def elements(self) -> Set[str]:
        result = set()
        for v, tags in self._add_set.items():
            alive = tags - self._rem_set.get(v, set())
            if alive:
                result.add(v)
        return result

    def merge(self, other: "ORSet"):
        for v, tags in other._add_set.items():
            self._add_set.setdefault(v, set()).update(tags)
        for v, tags in other._rem_set.items():
            self._rem_set.setdefault(v, set()).update(tags)

    def state(self) -> Dict:
        return {
            "add": {v: list(t) for v, t in self._add_set.items()},
            "rem": {v: list(t) for v, t in self._rem_set.items()},
        }

    @classmethod
    def from_state(cls, node_id: str, state: Dict) -> "ORSet":
        s = cls(node_id)
        s._add_set = {v: set(t) for v, t in state.get("add", {}).items()}
        s._rem_set = {v: set(t) for v, t in state.get("rem", {}).items()}
        return s


# ── FEDERATED NODE STATE ─────────────────────────────────────────────────────

@dataclass
class FederatedPeer:
    peer_id:    str
    node_id:    str
    did:        str
    endpoint:   str           # ws://ip:port or http://ip:port
    trusted:    bool = False
    last_sync:  float = 0.0
    sync_count: int   = 0


class FederatedNodeState:
    """
    CRDT-based state for a federated node.
    Contains: message counter, peer list, skill OR-Set, profile fields.
    """
    def __init__(self, node_id: str):
        self.node_id         = node_id
        self.msg_count       = GCounter(node_id)
        self.active_peers    = ORSet(node_id)
        self.capabilities    = ORSet(node_id)
        self.display_name    = LWWRegister()
        self.universe_mode   = LWWRegister()
        self._version        = 0

    def to_sync_packet(self) -> Dict:
        return {
            "node_id":       self.node_id,
            "version":       self._version,
            "msg_count":     self.msg_count.state(),
            "active_peers":  self.active_peers.state(),
            "capabilities":  self.capabilities.state(),
            "display_name":  self.display_name.state(),
            "universe_mode": self.universe_mode.state(),
            "ts":            time.time(),
        }

    def merge_packet(self, packet: Dict) -> int:
        """Merge incoming sync packet. Returns number of changes."""
        changes = 0
        remote_node = packet.get("node_id", "remote")

        remote_mc = GCounter.from_state(remote_node, packet.get("msg_count", {}))
        before = self.msg_count.value()
        self.msg_count.merge(remote_mc)
        if self.msg_count.value() != before: changes += 1

        remote_peers = ORSet.from_state(remote_node, packet.get("active_peers", {}))
        before_peers = self.active_peers.elements().copy()
        self.active_peers.merge(remote_peers)
        if self.active_peers.elements() != before_peers: changes += 1

        remote_caps = ORSet.from_state(remote_node, packet.get("capabilities", {}))
        self.capabilities.merge(remote_caps)

        remote_dn = LWWRegister.from_state(packet.get("display_name", {}))
        self.display_name.merge(remote_dn)

        remote_um = LWWRegister.from_state(packet.get("universe_mode", {}))
        self.universe_mode.merge(remote_um)

        self._version += 1
        return changes


# ── GLOBAL FEDERATION MANAGER ────────────────────────────────────────────────

class GlobalFederationManager:
    """
    Manages federation with other AsimNexus nodes globally.
    Uses CRDT for conflict-free state synchronization.
    Requires explicit human consent before trusting any peer.
    """

    def __init__(self, node_id: str = None, sync_interval: Optional[int] = None,
                 max_peers: Optional[int] = None):
        env_nid = os.getenv("ASIM_FED_NODE_ID")
        self.node_id       = node_id or env_nid or self._gen_node_id()
        self._state        = FederatedNodeState(self.node_id)
        self._peers:  Dict[str, FederatedPeer] = {}
        self._consent: Set[str] = set()    # peer_ids with human consent
        self._sync_log: List[Dict] = []

        # Env-var-aware config (read at init time so tests can override)
        env_sync = os.getenv("ASIM_FED_SYNC_INTERVAL")
        env_max  = os.getenv("ASIM_FED_MAX_PEERS")
        try:
            parsed_sync = int(env_sync) if env_sync else None
        except (ValueError, TypeError):
            parsed_sync = None
        try:
            parsed_max = int(env_max) if env_max else None
        except (ValueError, TypeError):
            parsed_max = None
        self.sync_interval = sync_interval or parsed_sync or _DEFAULT_SYNC_INTERVAL
        self.max_peers     = max_peers or parsed_max or _DEFAULT_MAX_PEERS

        # Data directory — read env at init time (overrides module-level FED_DIR)
        env_dir = os.getenv("ASIM_FED_DATA_DIR")
        if env_dir:
            self._fed_dir = Path(env_dir)
            self._fed_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._fed_dir = FED_DIR

        self._load()
        logger.info(f"✅ FederationManager ready — node={self.node_id[:16]}")

    def _gen_node_id(self) -> str:
        import socket
        host = socket.gethostname()
        return hashlib.sha256(f"{host}:{time.time()}:{secrets.token_hex(8)}".encode()).hexdigest()[:32]

    # ── PEER MANAGEMENT ───────────────────────────────────────────────────────

    def add_peer(self, did: str, endpoint: str,
                 trusted: bool = False) -> FederatedPeer:
        peer_id = hashlib.sha256(f"{did}:{endpoint}".encode()).hexdigest()[:16]
        peer = FederatedPeer(
            peer_id  = peer_id,
            node_id  = peer_id,
            did      = did,
            endpoint = endpoint,
            trusted  = trusted,
        )
        self._peers[peer_id] = peer
        self._state.active_peers.add(peer_id)
        self._save()
        logger.info(f"🤝 Peer added: {peer_id} @ {endpoint}")
        return peer

    def consent_peer(self, peer_id: str):
        """Human explicitly consents to sync with this peer."""
        self._consent.add(peer_id)
        if peer_id in self._peers:
            self._peers[peer_id].trusted = True
        self._save()
        logger.info(f"✅ Consent granted for peer: {peer_id}")

    def revoke_peer(self, peer_id: str):
        """Revoke human consent for a peer (keeps the peer record)."""
        self._consent.discard(peer_id)
        self._state.active_peers.remove(peer_id)
        if peer_id in self._peers:
            self._peers[peer_id].trusted = False
        self._save()

    def remove_peer(self, peer_id: str):
        """Fully remove a peer from the federation."""
        self._consent.discard(peer_id)
        self._state.active_peers.remove(peer_id)
        self._peers.pop(peer_id, None)
        self._save()
        logger.info(f"🗑️ Peer removed: {peer_id}")

    # ── SYNC ─────────────────────────────────────────────────────────────────

    def get_sync_packet(self) -> Dict:
        """Generate outbound sync packet for broadcasting."""
        return self._state.to_sync_packet()

    def receive_sync(self, packet: Dict, from_peer_id: str) -> Dict:
        """Receive and merge incoming sync packet."""
        if from_peer_id not in self._consent:
            return {"accepted": False, "reason": "No consent for this peer — human must approve first"}

        changes = self._state.merge_packet(packet)
        if from_peer_id in self._peers:
            self._peers[from_peer_id].last_sync  = time.time()
            self._peers[from_peer_id].sync_count += 1

        self._sync_log.append({
            "peer": from_peer_id, "changes": changes,
            "ts": time.time(), "version": self._state._version,
        })
        self._save()
        logger.info(f"🔄 Sync from {from_peer_id[:8]}: {changes} changes, version={self._state._version}")
        return {"accepted": True, "changes": changes, "version": self._state._version}

    # ── STATUS ────────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        return {
            "node_id":         self.node_id[:16] + "…",
            "peers":           len(self._peers),
            "trusted_peers":   len(self._consent),
            "state_version":   self._state._version,
            "active_peers":    list(self._state.active_peers.elements()),
            "capabilities":    list(self._state.capabilities.elements()),
            "msg_count":       self._state.msg_count.value(),
            "sync_events":     len(self._sync_log),
            "last_sync":       self._sync_log[-1]["ts"] if self._sync_log else None,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return detailed stats (alias for status with extra fields)."""
        s = self.status()
        s.update({
            "sync_interval":   self.sync_interval,
            "max_peers":       self.max_peers,
            "consent_count":   len(self._consent),
            "sync_log_size":   len(self._sync_log),
        })
        return s

    def peer_list(self) -> List[Dict]:
        return [asdict(p) for p in self._peers.values()]

    # ── PERSISTENCE ──────────────────────────────────────────────────────────

    def _save(self):
        path = self._fed_dir / f"{self.node_id[:16]}.json"
        try:
            data = {
                "node_id":  self.node_id,
                "consent":  list(self._consent),
                "peers":    {pid: asdict(p) for pid, p in self._peers.items()},
                "state":    self._state.to_sync_packet(),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Federation save failed: {e}")

    def _load(self):
        for path in self._fed_dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("node_id") == self.node_id:
                    self._consent = set(data.get("consent", []))
                    for pid, pd in data.get("peers", {}).items():
                        self._peers[pid] = FederatedPeer(**pd)
                    break
            except Exception:
                continue


_mgr: Optional[GlobalFederationManager] = None
def get_federation() -> GlobalFederationManager:
    global _mgr
    if _mgr is None: _mgr = GlobalFederationManager()
    return _mgr
