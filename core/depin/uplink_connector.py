"""
Uplink Connector — Decentralized Internet Connectivity.
========================================================
Simulates a DePIN connector for Uplink, a decentralized wireless network
where nodes provide internet bandwidth and earn rewards.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


class UplinkNodeState(Enum):
    """Operational state of an Uplink node."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    SYNCING = "syncing"


@dataclass
class UplinkNode:
    """A node in the Uplink decentralized wireless network."""
    id: str
    address: str
    bandwidth_capacity: float
    current_usage: float = 0.0
    state: UplinkNodeState = UplinkNodeState.ONLINE
    rewards_earned: float = 0.0
    location: str = ""

    def available_bandwidth(self) -> float:
        """Return remaining bandwidth capacity."""
        return self.bandwidth_capacity - self.current_usage

    def utilization_rate(self) -> float:
        """Return current utilization as a percentage."""
        if self.bandwidth_capacity == 0:
            return 0.0
        return (self.current_usage / self.bandwidth_capacity) * 100.0


class UplinkConnector:
    """Connector for the Uplink decentralized wireless network."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.connected = False
        self._nodes: Dict[str, UplinkNode] = {}

    async def connect(self) -> bool:
        """Connect to the Uplink network."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the Uplink network."""
        self.connected = False
        return True

    async def register_node(
        self,
        node_id: str,
        address: str,
        bandwidth_capacity: float,
        location: str = "",
    ) -> UplinkNode:
        """Register a new node in the network.

        Args:
            node_id: Unique node identifier
            address: IP address or endpoint
            bandwidth_capacity: Maximum bandwidth in Mbps
            location: Optional geographic location

        Returns:
            The registered UplinkNode
        """
        node = UplinkNode(
            id=node_id,
            address=address,
            bandwidth_capacity=bandwidth_capacity,
            location=location,
        )
        self._nodes[node_id] = node
        return node

    async def offload_traffic(self, node_id: str, amount_mbps: float) -> bool:
        """Offload traffic to a node.

        Args:
            node_id: Target node identifier
            amount_mbps: Bandwidth amount in Mbps

        Returns:
            True if successful
        """
        node = self._nodes.get(node_id)
        if not node:
            return False
        if node.current_usage + amount_mbps > node.bandwidth_capacity:
            return False
        node.current_usage += amount_mbps
        return True

    async def release_traffic(self, node_id: str, amount_mbps: float) -> bool:
        """Release traffic from a node.

        Args:
            node_id: Target node identifier
            amount_mbps: Bandwidth amount in Mbps

        Returns:
            True if successful
        """
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.current_usage = max(0.0, node.current_usage - amount_mbps)
        return True

    async def claim_rewards(self, node_id: str) -> float:
        """Claim accumulated rewards for a node.

        Args:
            node_id: Node identifier

        Returns:
            Reward amount
        """
        node = self._nodes.get(node_id)
        if not node:
            return 0.0
        # Simulate reward calculation based on usage
        reward = node.current_usage * 0.01 + 10.0
        node.rewards_earned += reward
        return reward

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics.

        Returns:
            Dict with network stats
        """
        total_capacity = sum(n.bandwidth_capacity for n in self._nodes.values())
        total_usage = sum(n.current_usage for n in self._nodes.values())
        return {
            "total_nodes": len(self._nodes),
            "total_bandwidth_capacity_mbps": total_capacity,
            "total_bandwidth_usage_mbps": total_usage,
            "average_utilization_pct": (
                (total_usage / total_capacity * 100.0) if total_capacity > 0 else 0.0
            ),
            "connected": self.connected,
        }
