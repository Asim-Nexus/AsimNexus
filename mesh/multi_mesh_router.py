#!/usr/bin/env python3
"""
STATUS: NEW — Gap 6 Implementation
ASIMNEXUS Multi-Mesh Router
============================
Routes between local/personal/cloud/public mesh networks.
Auto-switches based on connectivity, trust, context, and data classification.

Extends existing mesh infrastructure:
  - [`mesh/kademlia_dht.py`](kademlia_dht.py) — DHT discovery per mesh type
  - [`mesh/p2p_transport.py`](p2p_transport.py) — Transport per mesh type
  - [`mesh/autodiscovery.py`](autodiscovery.py) — Discovery strategies per type
  - [`mesh/network_intelligence.py`](network_intelligence.py) — Connectivity detection
  - [`mesh/node_registry.py`](node_registry.py) — Peer trust levels
  - [`core/routing/hybrid_router.py`](../core/routing/hybrid_router.py) — Extends model routing
"""

import os
import time
import json
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime

logger = logging.getLogger("AsimNexus.Mesh.MultiMeshRouter")

# ─── Environment Configuration ────────────────────────────────────────────────
_AUTO_SWITCH_INTERVAL_SEC = int(os.getenv("ASIM_MESH_AUTO_SWITCH_INTERVAL", "30"))
_DEFAULT_MESH = os.getenv("ASIM_MESH_DEFAULT", "local")
_MESH_DB_PATH = os.getenv("ASIM_MESH_DB_PATH", "data/mesh_routing.jsonl")
_MESH_HEALTH_TIMEOUT_SEC = int(os.getenv("ASIM_MESH_HEALTH_TIMEOUT", "10"))


class MeshType(Enum):
    """Types of mesh networks in the multi-mesh topology."""
    LOCAL = "local"           # Same device, loopback — highest trust, lowest latency
    PERSONAL = "personal"     # User's own devices (phone, laptop, home server)
    CLOUD = "cloud"           # User's cloud/VPS instance
    PUBLIC = "public"         # Global mesh network — lowest trust, variable latency


class MeshConnectionState(Enum):
    """Connection state for a specific mesh type."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    ERROR = "error"


class DataClassification(Enum):
    """Data classification levels for mesh routing decisions."""
    PUBLIC = "public"          # Can go anywhere
    INTERNAL = "internal"      # Restricted to personal/cloud
    SENSITIVE = "sensitive"    # Restricted to personal only
    SECRET = "secret"          # Local mesh only


@dataclass
class MeshProfile:
    """Runtime profile of a mesh network's current state."""
    mesh_type: MeshType
    trust_level: float            # 0.0 (untrusted) to 1.0 (fully trusted)
    max_latency_ms: float         # Current max observed latency
    avg_latency_ms: float         # Average observed latency
    bandwidth_kbps: float         # Estimated available bandwidth
    peers_available: int          # Number of reachable peers
    is_connected: bool            # Whether mesh is reachable
    connection_state: MeshConnectionState = MeshConnectionState.DISCONNECTED
    priority: int = 0             # Lower = preferred (0 = most preferred)
    last_health_check: float = 0.0
    error_count: int = 0
    data_classifications_allowed: Set[DataClassification] = field(default_factory=lambda: {
        DataClassification.PUBLIC,
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mesh_type": self.mesh_type.value,
            "trust_level": self.trust_level,
            "max_latency_ms": self.max_latency_ms,
            "avg_latency_ms": self.avg_latency_ms,
            "bandwidth_kbps": self.bandwidth_kbps,
            "peers_available": self.peers_available,
            "is_connected": self.is_connected,
            "connection_state": self.connection_state.value,
            "priority": self.priority,
            "last_health_check": self.last_health_check,
            "error_count": self.error_count,
            "data_classifications_allowed": [c.value for c in self.data_classifications_allowed],
        }


@dataclass
class MeshRequirements:
    """Routing requirements for a particular data/task routing request."""
    data_classification: DataClassification = DataClassification.PUBLIC
    max_accepted_latency_ms: float = float("inf")
    min_bandwidth_kbps: float = 0.0
    min_trust_level: float = 0.0
    preferred_mesh_types: Optional[List[MeshType]] = None
    requires_connected: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data_classification": self.data_classification.value,
            "max_accepted_latency_ms": self.max_accepted_latency_ms,
            "min_bandwidth_kbps": self.min_bandwidth_kbps,
            "min_trust_level": self.min_trust_level,
            "preferred_mesh_types": [m.value for m in self.preferred_mesh_types]
            if self.preferred_mesh_types else None,
            "requires_connected": self.requires_connected,
        }


@dataclass
class MeshRoutingRule:
    """A rule binding data/task characteristics to a preferred mesh type."""
    id: str
    description: str
    data_classification: Optional[DataClassification] = None
    mesh_type: Optional[MeshType] = None
    priority: int = 0
    active: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "data_classification": self.data_classification.value if self.data_classification else None,
            "mesh_type": self.mesh_type.value if self.mesh_type else None,
            "priority": self.priority,
            "active": self.active,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MeshRoutingRule":
        data = dict(data)
        if data.get("data_classification"):
            data["data_classification"] = DataClassification(data["data_classification"])
        if data.get("mesh_type"):
            data["mesh_type"] = MeshType(data["mesh_type"])
        return cls(**data)


@dataclass
class MeshSwitchEvent:
    """Audit trail entry for mesh switching events."""
    timestamp: float
    from_mesh: Optional[MeshType]
    to_mesh: MeshType
    reason: str
    initiated_by: str  # "auto" or "human"
    success: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "from_mesh": self.from_mesh.value if self.from_mesh else None,
            "to_mesh": self.to_mesh.value,
            "reason": self.reason,
            "initiated_by": self.initiated_by,
            "success": self.success,
        }


# ─── Default Mesh Profiles — static baseline ─────────────────────────────────
_MESH_BASELINES: Dict[MeshType, Dict[str, Any]] = {
    MeshType.LOCAL: {
        "trust_level": 1.0,
        "max_latency_ms": 1.0,
        "avg_latency_ms": 0.5,
        "bandwidth_kbps": 100000.0,    # Loopback — very high
        "priority": 0,
        "data_classifications_allowed": {DataClassification.PUBLIC, DataClassification.INTERNAL,
                                          DataClassification.SENSITIVE, DataClassification.SECRET},
    },
    MeshType.PERSONAL: {
        "trust_level": 0.9,
        "max_latency_ms": 50.0,
        "avg_latency_ms": 10.0,
        "bandwidth_kbps": 50000.0,
        "priority": 1,
        "data_classifications_allowed": {DataClassification.PUBLIC, DataClassification.INTERNAL,
                                          DataClassification.SENSITIVE},
    },
    MeshType.CLOUD: {
        "trust_level": 0.6,
        "max_latency_ms": 200.0,
        "avg_latency_ms": 50.0,
        "bandwidth_kbps": 100000.0,
        "priority": 2,
        "data_classifications_allowed": {DataClassification.PUBLIC, DataClassification.INTERNAL},
    },
    MeshType.PUBLIC: {
        "trust_level": 0.3,
        "max_latency_ms": 500.0,
        "avg_latency_ms": 150.0,
        "bandwidth_kbps": 10000.0,
        "priority": 3,
        "data_classifications_allowed": {DataClassification.PUBLIC},
    },
}


class MultiMeshRouter:
    """
    Routes between local/personal/cloud/public mesh networks.
    Auto-switches based on connectivity, trust, and data context.

    Default mesh preferences (by priority):
        LOCAL (0) → PERSONAL (1) → CLOUD (2) → PUBLIC (3)

    Key methods:
        [`get_available_meshes()`](:370) — scan all mesh types
        [`select_mesh()`](:400) — best mesh for requirements
        [`switch_mesh()`](:430) — explicit human-initiated switch
        [`route_through_mesh()`](:470) — route data via selected mesh
        [`get_active_mesh()`](:500) — currently active mesh
        [`auto_switch_loop()`](:520) — background connectivity monitor
        [`add_routing_rule()`](:580) — custom routing rules
        [`get_switch_history()`](:610) — audit trail
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._active_mesh: MeshType = MeshType(_DEFAULT_MESH)
        self._profiles: Dict[MeshType, MeshProfile] = {}
        self._routing_rules: List[MeshRoutingRule] = []
        self._switch_history: List[MeshSwitchEvent] = []
        self._health_checkers: Dict[MeshType, Callable[[], bool]] = {}
        self._auto_switch_enabled: bool = True
        self._auto_switch_thread: Optional[threading.Thread] = None
        self._stop_auto_switch: threading.Event = threading.Event()

        # Initialize baseline profiles
        now = time.time()
        for mtype, baseline in _MESH_BASELINES.items():
            self._profiles[mtype] = MeshProfile(
                mesh_type=mtype,
                trust_level=baseline["trust_level"],
                max_latency_ms=baseline["max_latency_ms"],
                avg_latency_ms=baseline["avg_latency_ms"],
                bandwidth_kbps=baseline["bandwidth_kbps"],
                peers_available=0,
                is_connected=(mtype == MeshType.LOCAL),  # LOCAL always available
                connection_state=MeshConnectionState.CONNECTED if mtype == MeshType.LOCAL
                else MeshConnectionState.DISCONNECTED,
                priority=baseline["priority"],
                last_health_check=now,
                data_classifications_allowed=baseline["data_classifications_allowed"],
            )

        # Default routing rules
        self._init_default_rules()
        logger.info(
            f"🌐 MultiMeshRouter initialized — active={self._active_mesh.value}"
        )

    def _init_default_rules(self) -> None:
        """Set up default routing rules based on data classification."""
        self._routing_rules = [
            MeshRoutingRule(
                id="rule_secret_local",
                description="SECRET data must use LOCAL mesh",
                data_classification=DataClassification.SECRET,
                mesh_type=MeshType.LOCAL,
                priority=100,
            ),
            MeshRoutingRule(
                id="rule_sensitive_personal",
                description="SENSITIVE data prefers PERSONAL mesh",
                data_classification=DataClassification.SENSITIVE,
                mesh_type=MeshType.PERSONAL,
                priority=90,
            ),
            MeshRoutingRule(
                id="rule_internal_cloud",
                description="INTERNAL data can use CLOUD mesh",
                data_classification=DataClassification.INTERNAL,
                mesh_type=MeshType.CLOUD,
                priority=80,
            ),
            MeshRoutingRule(
                id="rule_public_any",
                description="PUBLIC data can use any mesh",
                data_classification=DataClassification.PUBLIC,
                mesh_type=None,  # any
                priority=10,
            ),
        ]

    # ─── Public API ──────────────────────────────────────────────────────────

    def get_available_meshes(self) -> Dict[MeshType, MeshProfile]:
        """
        Scan and return profiles for all mesh network types.

        Returns:
            Dict mapping MeshType to its current MeshProfile.
        """
        with self._lock:
            return dict(self._profiles)

    def get_connected_meshes(self) -> Dict[MeshType, MeshProfile]:
        """Return only meshes that are currently connected."""
        with self._lock:
            return {
                mtype: profile
                for mtype, profile in self._profiles.items()
                if profile.is_connected
            }

    def select_mesh(self, requirements: Optional[MeshRequirements] = None) -> Tuple[MeshType, MeshProfile]:
        """
        Select the best mesh type for given requirements.

        Evaluates in order:
          1. Connected meshes only (unless requires_connected=False)
          2. Meshes that meet data classification restrictions
          3. Meshes meeting latency/bandwidth/trust thresholds
          4. Priority order (lower = better)
          5. Custom routing rules

        Args:
            requirements: Optional routing requirements. If None, uses defaults
                          for PUBLIC data.

        Returns:
            Tuple of (selected MeshType, corresponding MeshProfile).

        Raises:
            RuntimeError: If no mesh meets the requirements.
        """
        req = requirements or MeshRequirements()
        with self._lock:
            candidates: List[Tuple[MeshType, MeshProfile]] = []

            for mtype, profile in self._profiles.items():
                # Must be connected (unless not required)
                if req.requires_connected and not profile.is_connected:
                    continue

                # Must allow this data classification
                if req.data_classification not in profile.data_classifications_allowed:
                    continue

                # Must meet latency requirement
                if profile.avg_latency_ms > req.max_accepted_latency_ms:
                    continue

                # Must meet bandwidth requirement
                if profile.bandwidth_kbps < req.min_bandwidth_kbps:
                    continue

                # Must meet trust requirement
                if profile.trust_level < req.min_trust_level:
                    continue

                # Preferred mesh types filter
                if req.preferred_mesh_types and mtype not in req.preferred_mesh_types:
                    continue

                candidates.append((mtype, profile))

            if not candidates:
                raise RuntimeError(
                    f"No mesh meets requirements (classification={req.data_classification.value}, "
                    f"latency<={req.max_accepted_latency_ms}, trust>={req.min_trust_level})"
                )

            # Sort by priority (lower = better), then trust (higher = better), then latency
            candidates.sort(key=lambda x: (x[1].priority, -x[1].trust_level, x[1].avg_latency_ms))

            # Apply custom routing rules (higher priority rules override default ordering)
            if self._routing_rules:
                for rule in sorted(self._routing_rules, key=lambda r: -r.priority):
                    if not rule.active:
                        continue
                    if rule.data_classification and rule.data_classification != req.data_classification:
                        continue
                    if rule.mesh_type:
                        # If this rule specifies a mesh, check if it's a candidate
                        for i, (mtype, profile) in enumerate(candidates):
                            if mtype == rule.mesh_type:
                                # Move this candidate to the front
                                candidates.insert(0, candidates.pop(i))
                                break

            return candidates[0]

    def switch_mesh(self, target: MeshType, reason: str = "",
                    initiated_by: str = "human") -> bool:
        """
        Switch the active mesh to a different type.

        Args:
            target: The MeshType to switch to.
            reason: Human-readable reason for the switch.
            initiated_by: "human" or "auto".

        Returns:
            True if switch was successful.

        Raises:
            ValueError: If target mesh is not connected.
        """
        with self._lock:
            if target == self._active_mesh:
                return True  # Already on this mesh

            profile = self._profiles.get(target)
            if not profile or not profile.is_connected:
                raise ValueError(
                    f"Cannot switch to {target.value}: mesh not connected"
                )

            old_mesh = self._active_mesh
            self._active_mesh = target

            event = MeshSwitchEvent(
                timestamp=time.time(),
                from_mesh=old_mesh,
                to_mesh=target,
                reason=reason or f"Manual switch to {target.value}",
                initiated_by=initiated_by,
                success=True,
            )
            self._switch_history.append(event)
            self._persist_event(event)

            logger.info(
                f"🔄 Mesh switch: {old_mesh.value} → {target.value} "
                f"(by {initiated_by}: {reason})"
            )
            return True

    def route_through_mesh(self, mesh: MeshType, data: bytes,
                           destination: str) -> bool:
        """
        Route data through a specified mesh type.

        This is a routing-layer decision. Actual transport is handled by
        [`mesh/p2p_transport.py`](p2p_transport.py).

        Args:
            mesh: The mesh type to route through.
            data: The data payload.
            destination: Destination peer/node identifier.

        Returns:
            True if routing was accepted (actual send is delegated).
        """
        with self._lock:
            profile = self._profiles.get(mesh)
            if not profile or not profile.is_connected:
                logger.warning(
                    f"⛔ Cannot route through {mesh.value}: not connected"
                )
                return False

            logger.debug(
                f"📡 Routing {len(data)} bytes through {mesh.value} → {destination}"
            )
            # Actual transport delegation happens at the integration layer.
            # The router validates that routing is allowed and returns approval.
            return True

    def get_active_mesh(self) -> MeshType:
        """Get the currently active mesh type."""
        with self._lock:
            return self._active_mesh

    def get_active_profile(self) -> MeshProfile:
        """Get the profile of the currently active mesh."""
        with self._lock:
            return self._profiles[self._active_mesh]

    # ─── Health & Auto-Switch ────────────────────────────────────────────────

    def register_health_checker(self, mesh_type: MeshType,
                                 checker: Callable[[], bool]) -> None:
        """
        Register a health-check function for a mesh type.

        The checker should return True if the mesh is reachable/healthy.
        Used by [`auto_switch_loop()`](:520).
        """
        with self._lock:
            self._health_checkers[mesh_type] = checker

    def update_mesh_health(self, mesh_type: MeshType,
                           is_connected: bool,
                           latency_ms: Optional[float] = None,
                           bandwidth_kbps: Optional[float] = None,
                           peers: Optional[int] = None) -> None:
        """
        Update the health/connectivity status of a mesh.

        Called by external monitors or health checkers.
        """
        with self._lock:
            profile = self._profiles.get(mesh_type)
            if not profile:
                return

            now = time.time()
            profile.last_health_check = now
            profile.is_connected = is_connected
            profile.connection_state = (
                MeshConnectionState.CONNECTED if is_connected
                else MeshConnectionState.DISCONNECTED
            )

            if latency_ms is not None:
                # Exponential moving average
                profile.avg_latency_ms = profile.avg_latency_ms * 0.7 + latency_ms * 0.3
                profile.max_latency_ms = max(profile.max_latency_ms, latency_ms)

            if bandwidth_kbps is not None:
                profile.bandwidth_kbps = bandwidth_kbps

            if peers is not None:
                profile.peers_available = peers

            if not is_connected:
                profile.error_count += 1

    def start_auto_switch(self) -> None:
        """
        Start the background auto-switch monitoring loop.

        Runs in a daemon thread. Checks connectivity at
        [`_AUTO_SWITCH_INTERVAL_SEC`](:25) intervals.
        """
        if self._auto_switch_thread and self._auto_switch_thread.is_alive():
            logger.warning("Auto-switch loop already running")
            return

        self._stop_auto_switch.clear()
        self._auto_switch_thread = threading.Thread(
            target=self._auto_switch_loop,
            daemon=True,
            name="mesh-auto-switch",
        )
        self._auto_switch_thread.start()
        logger.info("▶️ Auto-switch monitoring started")

    def stop_auto_switch(self) -> None:
        """Stop the background auto-switch loop."""
        self._stop_auto_switch.set()
        if self._auto_switch_thread:
            self._auto_switch_thread.join(timeout=5)
        logger.info("⏹️ Auto-switch monitoring stopped")

    def _auto_switch_loop(self) -> None:
        """Background loop: monitor connectivity and auto-switch if needed."""
        while not self._stop_auto_switch.is_set():
            try:
                self._run_health_checks()
                self._evaluate_auto_switch()
            except Exception as e:
                logger.error(f"Auto-switch error: {e}")
            self._stop_auto_switch.wait(_AUTO_SWITCH_INTERVAL_SEC)

    def _run_health_checks(self) -> None:
        """Run all registered health checkers and update profiles."""
        for mtype, checker in list(self._health_checkers.items()):
            try:
                is_healthy = checker()
                self.update_mesh_health(mtype, is_healthy)
            except Exception as e:
                logger.warning(f"Health check failed for {mtype.value}: {e}")
                self.update_mesh_health(mtype, False)

    def _evaluate_auto_switch(self) -> None:
        """
        Evaluate whether to auto-switch to a better mesh.

        Rules:
          1. If active mesh is disconnected, switch to next best connected mesh.
          2. If a higher-priority mesh becomes available, switch to it.
        """
        if not self._auto_switch_enabled:
            return

        with self._lock:
            active = self._profiles.get(self._active_mesh)
            if not active:
                return

            # If active mesh is disconnected, find best alternative
            if not active.is_connected:
                connected = [
                    (mtype, profile) for mtype, profile in self._profiles.items()
                    if profile.is_connected
                ]
                if connected:
                    connected.sort(key=lambda x: (x[1].priority, -x[1].trust_level))
                    best_mesh, best_profile = connected[0]
                    if best_mesh != self._active_mesh:
                        old_mesh = self._active_mesh
                        self._active_mesh = best_mesh
                        event = MeshSwitchEvent(
                            timestamp=time.time(),
                            from_mesh=old_mesh,
                            to_mesh=best_mesh,
                            reason=f"Auto-switch: {old_mesh.value} disconnected, "
                                   f"falling back to {best_mesh.value}",
                            initiated_by="auto",
                            success=True,
                        )
                        self._switch_history.append(event)
                        self._persist_event(event)
                        logger.info(
                            f"🔄 Auto-switch: {old_mesh.value} → {best_mesh.value} "
                            f"(disconnected fallback)"
                        )
                return

            # If a higher-priority mesh (lower priority number) becomes available
            for mtype, profile in sorted(
                self._profiles.items(), key=lambda x: x[1].priority
            ):
                if (
                    profile.is_connected
                    and profile.priority < active.priority
                    and mtype != self._active_mesh
                ):
                    old_mesh = self._active_mesh
                    self._active_mesh = mtype
                    event = MeshSwitchEvent(
                        timestamp=time.time(),
                        from_mesh=old_mesh,
                        to_mesh=mtype,
                        reason=f"Auto-switch: better mesh {mtype.value} "
                               f"(priority {profile.priority}) became available",
                        initiated_by="auto",
                        success=True,
                    )
                    self._switch_history.append(event)
                    self._persist_event(event)
                    logger.info(
                        f"🔄 Auto-switch: {old_mesh.value} → {mtype.value} "
                        f"(better mesh available)"
                    )
                    break

    # ─── Routing Rules ───────────────────────────────────────────────────────

    def add_routing_rule(self, rule: MeshRoutingRule) -> None:
        """Add a custom routing rule (higher priority rules take precedence)."""
        with self._lock:
            # Remove existing rule with same ID if present
            self._routing_rules = [r for r in self._routing_rules if r.id != rule.id]
            self._routing_rules.append(rule)
            self._persist_rule(rule)

    def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove a routing rule by ID. Returns True if found and removed."""
        with self._lock:
            initial_len = len(self._routing_rules)
            self._routing_rules = [r for r in self._routing_rules if r.id != rule_id]
            return len(self._routing_rules) < initial_len

    def get_routing_rules(self) -> List[MeshRoutingRule]:
        """Get all current routing rules."""
        with self._lock:
            return list(self._routing_rules)

    def set_auto_switch_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic mesh switching."""
        with self._lock:
            self._auto_switch_enabled = enabled

    # ─── Audit / History ─────────────────────────────────────────────────────

    def get_switch_history(self, limit: int = 50) -> List[MeshSwitchEvent]:
        """Get the mesh switch audit trail, most recent first."""
        with self._lock:
            return list(reversed(self._switch_history[-limit:]))

    def get_mesh_stats(self) -> Dict[str, Any]:
        """Get comprehensive mesh routing statistics."""
        with self._lock:
            connected = sum(1 for p in self._profiles.values() if p.is_connected)
            total_switches = len(self._switch_history)
            auto_switches = sum(
                1 for e in self._switch_history if e.initiated_by == "auto"
            )
            human_switches = total_switches - auto_switches
            return {
                "active_mesh": self._active_mesh.value,
                "connected_meshes": connected,
                "total_meshes": len(self._profiles),
                "total_switches": total_switches,
                "auto_switches": auto_switches,
                "human_switches": human_switches,
                "auto_switch_enabled": self._auto_switch_enabled,
                "health_checkers_registered": len(self._health_checkers),
                "routing_rules": len(self._routing_rules),
                "profiles": {
                    mtype.value: profile.to_dict()
                    for mtype, profile in self._profiles.items()
                },
            }

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _persist_event(self, event: MeshSwitchEvent) -> None:
        """Append switch event to JSONL audit trail."""
        try:
            os.makedirs(os.path.dirname(_MESH_DB_PATH), exist_ok=True)
            with open(_MESH_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist mesh switch event: {e}")

    def _persist_rule(self, rule: MeshRoutingRule) -> None:
        """Persist a routing rule to the audit trail."""
        try:
            os.makedirs(os.path.dirname(_MESH_DB_PATH), exist_ok=True)
            with open(_MESH_DB_PATH.replace(".jsonl", "_rules.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(rule.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist routing rule: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_multi_mesh_router_instance: Optional[MultiMeshRouter] = None
_multi_mesh_router_lock = threading.Lock()


def get_multi_mesh_router() -> MultiMeshRouter:
    """
    Get or create the singleton MultiMeshRouter instance.

    Usage:
        ```python
        router = get_multi_mesh_router()
        available = router.get_available_meshes()
        best_mesh, profile = router.select_mesh(requirements)
        ```
    """
    global _multi_mesh_router_instance
    if _multi_mesh_router_instance is None:
        with _multi_mesh_router_lock:
            if _multi_mesh_router_instance is None:
                _multi_mesh_router_instance = MultiMeshRouter()
    return _multi_mesh_router_instance


def reset_multi_mesh_router() -> None:
    """Reset the singleton (for testing)."""
    global _multi_mesh_router_instance
    with _multi_mesh_router_lock:
        if _multi_mesh_router_instance:
            _multi_mesh_router_instance.stop_auto_switch()
        _multi_mesh_router_instance = None


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "MeshType",
    "MeshConnectionState",
    "DataClassification",
    "MeshProfile",
    "MeshRequirements",
    "MeshRoutingRule",
    "MeshSwitchEvent",
    "MultiMeshRouter",
    "get_multi_mesh_router",
    "reset_multi_mesh_router",
]
