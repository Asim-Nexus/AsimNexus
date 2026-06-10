
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Uplink DePIN Connector
======================

Connector for Uplink decentralized internet connectivity network.
Uplink enables telecoms to offload traffic and helps enterprises
reduce capital and operational expenses through community participation.

Based on research:
- Uplink is a DePIN platform on Avalanche blockchain
- Provides decentralized wireless (DeWi) capabilities
- Incentivizes community participation in network infrastructure
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class UplinkNodeState(Enum):
    """Uplink node states"""
    IDLE = "idle"
    ACTIVE = "active"
    OFFLOADING = "offloading"
    MAINTENANCE = "maintenance"


@dataclass
class UplinkNode:
    """Uplink network node"""
    id: str
    address: str
    bandwidth_capacity: float  # Mbps
    current_usage: float = 0.0
    state: UplinkNodeState = UplinkNodeState.IDLE
    rewards_earned: float = 0.0
    connected_devices: int = 0
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def available_bandwidth(self) -> float:
        """Calculate available bandwidth"""
        return max(0, self.bandwidth_capacity - self.current_usage)
    
    def utilization_rate(self) -> float:
        """Calculate utilization rate"""
        if self.bandwidth_capacity == 0:
            return 0.0
        return (self.current_usage / self.bandwidth_capacity) * 100


class UplinkConnector:
    """
    Uplink DePIN Connector
    
    Provides interface to Uplink decentralized network:
    - Node registration and management
    - Traffic offloading
    - Reward tracking
    - Network monitoring
    """
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        self.api_key = api_key
        self.api_endpoint = api_endpoint or "https://api.uplink.network/v1"
        self.nodes: Dict[str, UplinkNode] = {}
        self.connected = False
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        logger.info("Uplink Connector initialized")
    
    async def connect(self) -> bool:
        """Connect to Uplink network"""
        try:
            # Simulate connection check
            response = self.session.get(f"{self.api_endpoint}/health", timeout=5)
            self.connected = response.status_code == 200
            if self.connected:
                logger.info("Connected to Uplink network")
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect to Uplink: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Uplink network"""
        self.connected = False
        logger.info("Disconnected from Uplink network")
    
    async def register_node(
        self,
        node_id: str,
        address: str,
        bandwidth_capacity: float
    ) -> UplinkNode:
        """Register a new node with Uplink"""
        node = UplinkNode(
            id=node_id,
            address=address,
            bandwidth_capacity=bandwidth_capacity
        )
        
        self.nodes[node_id] = node
        logger.info(f"Node registered: {node_id} with {bandwidth_capacity} Mbps")
        
        return node
    
    async def offload_traffic(
        self,
        node_id: str,
        traffic_amount: float  # Mbps
    ) -> bool:
        """Offload traffic through node"""
        node = self.nodes.get(node_id)
        if not node:
            logger.warning(f"Node {node_id} not found")
            return False
        
        if node.available_bandwidth() < traffic_amount:
            logger.warning(f"Insufficient bandwidth on node {node_id}")
            return False
        
        node.current_usage += traffic_amount
        node.state = UplinkNodeState.OFFLOADING
        
        # Simulate reward calculation
        reward = traffic_amount * 0.01  # $0.01 per Mbps
        node.rewards_earned += reward
        
        logger.info(f"Offloaded {traffic_amount} Mbps through node {node_id}, earned ${reward:.2f}")
        return True
    
    async def release_traffic(self, node_id: str, traffic_amount: float) -> bool:
        """Release traffic from node"""
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        node.current_usage = max(0, node.current_usage - traffic_amount)
        if node.current_usage == 0:
            node.state = UplinkNodeState.IDLE
        
        logger.info(f"Released {traffic_amount} Mbps from node {node_id}")
        return True
    
    def get_node(self, node_id: str) -> Optional[UplinkNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[UplinkNode]:
        """Get all registered nodes"""
        return list(self.nodes.values())
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        total_bandwidth = sum(node.bandwidth_capacity for node in self.nodes.values())
        total_usage = sum(node.current_usage for node in self.nodes.values())
        total_rewards = sum(node.rewards_earned for node in self.nodes.values())
        
        active_nodes = sum(1 for node in self.nodes.values() if node.state == UplinkNodeState.ACTIVE)
        offloading_nodes = sum(1 for node in self.nodes.values() if node.state == UplinkNodeState.OFFLOADING)
        
        return {
            "connected": self.connected,
            "total_nodes": len(self.nodes),
            "active_nodes": active_nodes,
            "offloading_nodes": offloading_nodes,
            "total_bandwidth_capacity_mbps": total_bandwidth,
            "total_current_usage_mbps": total_usage,
            "total_rewards_earned_usd": total_rewards,
            "network_utilization_percent": (total_usage / total_bandwidth * 100) if total_bandwidth > 0 else 0
        }
    
    async def heartbeat(self, node_id: str) -> bool:
        """Send heartbeat for node"""
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        node.last_heartbeat = datetime.now().isoformat()
        logger.debug(f"Heartbeat sent for node {node_id}")
        return True
    
    async def claim_rewards(self, node_id: str) -> float:
        """Claim rewards for node"""
        node = self.nodes.get(node_id)
        if not node:
            return 0.0
        
        rewards = node.rewards_earned
        node.rewards_earned = 0.0  # Reset after claiming
        
        logger.info(f"Claimed ${rewards:.2f} for node {node_id}")
        return rewards


# Global Uplink connector instance
_uplink_connector: Optional[UplinkConnector] = None


def get_uplink_connector(
    api_key: Optional[str] = None,
    api_endpoint: Optional[str] = None
) -> UplinkConnector:
    """Get global Uplink connector instance (lazy load)"""
    global _uplink_connector
    if _uplink_connector is None:
        _uplink_connector = UplinkConnector(api_key, api_endpoint)
    return _uplink_connector
