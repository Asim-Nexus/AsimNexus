"""
STATUS: PARTIAL — Routing logic real, _execute_on_device uses asyncio.sleep (simulated)
                  See mesh_routing_agent_v2.py for P2P-wired version

Mesh Routing Agent - Intelligent Task Routing in Tree + Star + Ring Topology
Handles fallback paths, load balancing, and resilient task distribution
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time
import logging

class RoutingStrategy(Enum):
    PRIMARY = "primary"        # Use primary device
    FALLBACK = "fallback"      # Use backup device
    LOAD_BALANCE = "load_balance"  # Distribute across multiple
    ANY_AVAILABLE = "any_available"  # First available device

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class RoutingDecision:
    target_device: str
    strategy: RoutingStrategy
    backup_devices: List[str]
    estimated_latency: float
    confidence_score: float
    reason: str

class MeshRoutingAgent:
    """
    Intelligent routing agent for mesh topology.
    Routes tasks through Tree -> Star -> Ring fallback paths.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_MeshRouting")
        self.route_history = []
        self.device_load = {}  # Current load per device
        self.routing_stats = {
            'primary_routes': 0,
            'fallback_routes': 0,
            'failed_routes': 0
        }
        
    async def initialize(self, device_registry):
        """Initialize routing agent with device registry"""
        self.device_registry = device_registry
        self.logger.info("🌐 Mesh Routing Agent initialized")
        
    async def route_task(self, task: Dict, priority: TaskPriority = TaskPriority.NORMAL) -> RoutingDecision:
        """
        Route a task to the optimal device using mesh topology.
        
        Strategy:
        1. Try primary device (Tree topology)
        2. If busy/offline, use Star topology (AsimCore routing)
        3. If still fails, use Ring topology (backup devices)
        4. Load balance across available devices
        """
        task_type = task.get('type', 'general')
        required_capabilities = task.get('capabilities', ['compute'])
        preferred_device = task.get('preferred_device', None)
        
        # Step 1: Try primary/preferred device
        if preferred_device:
            device = await self.device_registry.get_device(preferred_device)
            if device and device.status == "online" and self._has_capabilities(device, required_capabilities):
                if not self._is_overloaded(preferred_device):
                    return RoutingDecision(
                        target_device=preferred_device,
                        strategy=RoutingStrategy.PRIMARY,
                        backup_devices=self._get_backup_devices(preferred_device),
                        estimated_latency=0.1,
                        confidence_score=0.95,
                        reason="Primary device available and capable"
                    )
        
        # Step 2: Find capable devices via Star topology
        capable_devices = []
        for cap in required_capabilities:
            devices_with_cap = await self.device_registry.get_devices_by_capability(cap)
            capable_devices.extend([d.id for d in devices_with_cap if d.status == "online"])
            
        # Remove duplicates and filter by load
        capable_devices = list(set(capable_devices))
        available_devices = [d for d in capable_devices if not self._is_overloaded(d)]
        
        if not available_devices:
            # No capable devices available - try any online device as last resort
            all_online = [d.id for d in self.device_registry.list_devices() if d.status == "online"]
            if all_online:
                return RoutingDecision(
                    target_device=all_online[0],
                    strategy=RoutingStrategy.ANY_AVAILABLE,
                    backup_devices=[],
                    estimated_latency=0.5,
                    confidence_score=0.5,
                    reason="No capable devices - using any available"
                )
            else:
                raise Exception("No devices available for task routing")
                
        # Step 3: Load balancing - pick least loaded device
        target_device = self._select_least_loaded(available_devices)
        
        # Step 4: Get Ring topology backup paths
        backup_devices = self._get_backup_devices(target_device)
        
        strategy = RoutingStrategy.LOAD_BALANCE if len(available_devices) > 1 else RoutingStrategy.PRIMARY
        
        return RoutingDecision(
            target_device=target_device,
            strategy=strategy,
            backup_devices=backup_devices,
            estimated_latency=self._estimate_latency(target_device),
            confidence_score=0.85,
            reason=f"Routed via Star topology, {len(available_devices)} capable devices available"
        )
        
    async def execute_with_fallback(self, task: Dict, priority: TaskPriority = TaskPriority.NORMAL) -> Tuple[bool, Any, str]:
        """
        Execute task with automatic fallback to backup devices.
        
        Returns: (success, result, device_used)
        """
        routing_decision = await self.route_task(task, priority)
        
        devices_to_try = [routing_decision.target_device] + routing_decision.backup_devices
        
        for device_id in devices_to_try:
            try:
                result = await self._execute_on_device(task, device_id)
                
                # Update routing stats
                if device_id == routing_decision.target_device:
                    self.routing_stats['primary_routes'] += 1
                else:
                    self.routing_stats['fallback_routes'] += 1
                    
                self.logger.info(f"✅ Task executed on {device_id} ({routing_decision.strategy.value})")
                return True, result, device_id
                
            except Exception as e:
                self.logger.warning(f"❌ Failed on {device_id}: {e}")
                continue
                
        self.routing_stats['failed_routes'] += 1
        raise Exception(f"Task failed on all devices: {devices_to_try}")
        
    async def _execute_on_device(self, task: Dict, device_id: str) -> Any:
        """Execute a task on a specific device"""
        device = await self.device_registry.get_device(device_id)
        if not device:
            raise Exception(f"Device {device_id} not found")
            
        if device.status != "online":
            raise Exception(f"Device {device_id} is offline")
            
        # Update device load
        self.device_load[device_id] = self.device_load.get(device_id, 0) + 1
        
        try:
            # Simulate task execution (replace with actual execution)
            await asyncio.sleep(0.1)  # Simulate processing time
            
            result = {
                'device_id': device_id,
                'task_type': task.get('type'),
                'status': 'completed',
                'timestamp': time.time()
            }
            
            return result
            
        finally:
            # Decrement load
            self.device_load[device_id] = max(0, self.device_load.get(device_id, 1) - 1)
            
    def _has_capabilities(self, device, required_caps: List[str]) -> bool:
        """Check if device has all required capabilities"""
        return all(cap in device.capabilities for cap in required_caps)
        
    def _is_overloaded(self, device_id: str) -> bool:
        """Check if device is overloaded"""
        return self.device_load.get(device_id, 0) > 5  # Max 5 concurrent tasks
        
    def _get_backup_devices(self, device_id: str) -> List[str]:
        """Get backup devices from Ring topology"""
        device = self.device_registry.devices.get(device_id)
        if device and device.backup_paths:
            # Filter to only online devices
            return [
                backup_id for backup_id in device.backup_paths
                if backup_id in self.device_registry.devices and
                self.device_registry.devices[backup_id].status == "online"
            ]
        return []
        
    def _select_least_loaded(self, device_ids: List[str]) -> str:
        """Select least loaded device for load balancing"""
        if not device_ids:
            raise Exception("No devices to select from")
            
        loads = [(d, self.device_load.get(d, 0)) for d in device_ids]
        loads.sort(key=lambda x: x[1])
        return loads[0][0]
        
    def _estimate_latency(self, device_id: str) -> float:
        """Estimate latency to device"""
        device = self.device_registry.devices.get(device_id)
        if not device:
            return 1.0
            
        # Base latency by connection type
        latency_map = {
            'local': 0.01,
            'ssh': 0.1,
            'api': 0.2,
            'bluetooth': 0.3
        }
        
        return latency_map.get(device.connection.value, 0.5)
        
    async def get_routing_report(self) -> Dict:
        """Generate routing statistics report"""
        return {
            'stats': self.routing_stats,
            'current_load': self.device_load,
            'total_routes': sum(self.routing_stats.values()),
            'fallback_success_rate': (
                self.routing_stats['fallback_routes'] / 
                (self.routing_stats['fallback_routes'] + self.routing_stats['failed_routes'])
                if (self.routing_stats['fallback_routes'] + self.routing_stats['failed_routes']) > 0 
                else 1.0
            ),
            'topology_health': await self._check_topology_health()
        }
        
    async def _check_topology_health(self) -> Dict:
        """Check health of mesh topology"""
        mesh_status = await self.device_registry.get_mesh_status()
        
        health_score = 1.0
        issues = []
        
        # Check if we have enough online devices
        online_ratio = mesh_status['online_devices'] / max(mesh_status['total_devices'], 1)
        if online_ratio < 0.5:
            health_score -= 0.3
            issues.append("Less than 50% devices online")
            
        # Check backup path coverage
        if mesh_status['ring_backup_paths'] < mesh_status['total_devices']:
            health_score -= 0.2
            issues.append("Incomplete ring backup coverage")
            
        # Check tree depth (shouldn't be too deep)
        if mesh_status['tree_depth'] > 5:
            health_score -= 0.1
            issues.append("Tree topology depth exceeds 5 levels")
            
        return {
            'health_score': max(0, health_score),
            'issues': issues,
            'recommendations': self._generate_topology_recommendations(mesh_status, issues)
        }
        
    def _generate_topology_recommendations(self, mesh_status: Dict, issues: List[str]) -> List[str]:
        """Generate recommendations for topology improvement"""
        recommendations = []
        
        if mesh_status['online_devices'] < 2:
            recommendations.append("Add more devices for redundancy")
            
        if mesh_status['ring_backup_paths'] == 0:
            recommendations.append("Enable ring topology for critical devices")
            
        if 'compute' not in mesh_status['capabilities_index'] or mesh_status['capabilities_index']['compute'] < 2:
            recommendations.append("Add compute-capable devices for processing redundancy")
            
        if not issues:
            recommendations.append("Topology healthy - maintain current configuration")
            
        return recommendations
        
    async def optimize_topology(self) -> Dict:
        """Analyze and suggest topology optimizations"""
        mesh_status = await self.device_registry.get_mesh_status()
        
        optimizations = {
            'add_backup_paths': [],
            'rebalance_load': [],
            'remove_unused': []
        }
        
        # Identify devices without backup paths
        for device_id, device in self.device_registry.devices.items():
            if not device.backup_paths and device.capabilities:
                similar = []
                for cap in device.capabilities:
                    for other_id in self.device_registry.device_capabilities.get(cap, []):
                        if other_id != device_id:
                            similar.append(other_id)
                            
                if similar:
                    optimizations['add_backup_paths'].append({
                        'device': device_id,
                        'suggested_backups': similar[:2]
                    })
                    
        # Check load imbalance
        if self.device_load:
            avg_load = sum(self.device_load.values()) / len(self.device_load)
            for device_id, load in self.device_load.items():
                if load > avg_load * 2:
                    optimizations['rebalance_load'].append({
                        'device': device_id,
                        'current_load': load,
                        'suggested_max': int(avg_load * 1.5)
                    })
                    
        return optimizations


# Singleton instance
mesh_routing_agent = MeshRoutingAgent()

async def initialize_mesh_routing(device_registry):
    """Initialize mesh routing agent"""
    await mesh_routing_agent.initialize(device_registry)
    return mesh_routing_agent
