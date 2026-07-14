"""
core/federation/federation_manager.py
AsimNexus — Federation Manager

Wraps GlobalFederationManager + GlobalFederationGovernor into a single
interface used by routes/mesh.py for federation join/topology/peers.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from core.federation.global_federation import (
    GlobalFederationManager,
    get_federation,
)
from core.federation.global_federation_governor import (
    GlobalFederationGovernor,
    get_global_federation_governor,
)

logger = logging.getLogger("AsimNexus.Federation.Manager")


class FederationManager:
    """Unified federation manager — wraps CRDT federation + governance.

    Interface consumed by routes/mesh.py:
        join(node_id, credentials) -> dict
        get_topology() -> dict
        get_status() -> dict
        add_peer(peer_id, address) -> dict
        consent(peer_id) -> dict
        get_sync_packet() -> dict
    """

    def __init__(self):
        self._fed: Optional[GlobalFederationManager] = None
        self._gov: Optional[GlobalFederationGovernor] = None
        self._initialized = False
        self._peers: Dict[str, Dict[str, Any]] = {}
        self._node_id: str = ""

    async def initialize(self) -> None:
        """Lazy-init federation and governor."""
        if self._initialized:
            return
        try:
            self._fed = get_federation()
            self._gov = await get_global_federation_governor()
            self._node_id = getattr(self._fed, "node_id", "asim-nexus-node")
            self._initialized = True
            logger.info("FederationManager initialized (node=%s)", self._node_id)
        except Exception as exc:
            logger.warning("FederationManager init deferred: %s", exc)

    # ── Routes interface ────────────────────────────────────────────────

    async def join(self, node_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Join a federation as a peer."""
        await self._ensure()
        self._peers[node_id] = {
            "node_id": node_id,
            "joined_at": time.time(),
            "status": "connected",
            "credentials": credentials,
        }
        logger.info("Peer %s joined federation", node_id)
        return {
            "node_id": node_id,
            "federation_id": self._node_id,
            "status": "connected",
            "peers": list(self._peers.keys()),
        }

    async def get_topology(self) -> Dict[str, Any]:
        """Return current federation topology."""
        await self._ensure()
        return {
            "nodes": [
                {"id": pid, "status": info.get("status", "unknown")}
                for pid, info in self._peers.items()
            ],
            "links": [],
            "node_id": self._node_id,
        }

    async def get_status(self) -> Dict[str, Any]:
        """Return federation status."""
        await self._ensure()
        return {
            "status": "active" if self._initialized else "inactive",
            "node_id": self._node_id,
            "peers": len(self._peers),
            "peer_list": list(self._peers.keys()),
            "uptime": time.time(),
        }

    async def add_peer(self, peer_id: str, address: str) -> Dict[str, Any]:
        """Add a peer to the federation."""
        await self._ensure()
        self._peers[peer_id] = {
            "node_id": peer_id,
            "address": address,
            "added_at": time.time(),
            "status": "pending_consent",
        }
        logger.info("Peer %s added (address=%s)", peer_id, address)
        return {
            "peer_id": peer_id,
            "address": address,
            "status": "pending_consent",
        }

    async def consent(self, peer_id: str) -> Dict[str, Any]:
        """Provide human consent for a federation peer."""
        await self._ensure()
        if peer_id in self._peers:
            self._peers[peer_id]["status"] = "consented"
            self._peers[peer_id]["consented_at"] = time.time()
            logger.info("Consent granted for peer %s", peer_id)
        return {
            "peer_id": peer_id,
            "status": self._peers.get(peer_id, {}).get("status", "unknown"),
            "consented": True,
        }

    async def get_sync_packet(self) -> Dict[str, Any]:
        """Get a sync packet for federation state exchange."""
        await self._ensure()
        return {
            "packet": {
                "node_id": self._node_id,
                "peers": list(self._peers.keys()),
                "timestamp": time.time(),
                "version": "1.0",
            }
        }

    # ── Internals ───────────────────────────────────────────────────────

    async def _ensure(self) -> None:
        if not self._initialized:
            await self.initialize()
