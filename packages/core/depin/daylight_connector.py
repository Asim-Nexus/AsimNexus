
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
Daylight DePIN Connector
========================

Connector for Daylight decentralized energy network.
Daylight enables users to connect energy devices (thermostats, batteries,
EVs, solar inverters) to earn rewards and participate in energy marketplace.

Based on research:
- Daylight is a decentralized protocol for distributed energy assets
- Users can sell excess energy and carbon credits directly to buyers
- $75M funding for expanding decentralized solar network
- Built on blockchain for transparent P2P transactions
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


class DeviceType(Enum):
    """Daylight energy device types"""
    SOLAR_INVERTER = "solar_inverter"
    BATTERY = "battery"
    THERMOSTAT = "thermostat"
    ELECTRIC_VEHICLE = "electric_vehicle"
    SMART_METER = "smart_meter"


class EnergyState(Enum):
    """Energy device states"""
    PRODUCING = "producing"
    CONSUMING = "consuming"
    IDLE = "idle"
    CHARGING = "charging"
    DISCHARGING = "discharging"


@dataclass
class EnergyDevice:
    """Daylight energy device"""
    id: str
    device_type: DeviceType
    capacity_kwh: float
    current_output_kwh: float = 0.0
    state: EnergyState = EnergyState.IDLE
    rewards_earned: float = 0.0
    carbon_credits: float = 0.0
    last_sync: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def utilization_rate(self) -> float:
        """Calculate utilization rate"""
        if self.capacity_kwh == 0:
            return 0.0
        return (self.current_output_kwh / self.capacity_kwh) * 100
    
    def available_capacity(self) -> float:
        """Calculate available capacity"""
        return max(0, self.capacity_kwh - self.current_output_kwh)


class DaylightConnector:
    """
    Daylight DePIN Connector
    
    Provides interface to Daylight energy network:
    - Device registration and management
    - Energy production/consumption tracking
    - Carbon credit management
    - Energy marketplace participation
    """
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        self.api_key = api_key
        self.api_endpoint = api_endpoint or "https://api.daylight.energy/v1"
        self.devices: Dict[str, EnergyDevice] = {}
        self.connected = False
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        logger.info("Daylight Connector initialized")
    
    async def connect(self) -> bool:
        """Connect to Daylight network"""
        try:
            response = self.session.get(f"{self.api_endpoint}/health", timeout=5)
            self.connected = response.status_code == 200
            if self.connected:
                logger.info("Connected to Daylight network")
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect to Daylight: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Daylight network"""
        self.connected = False
        logger.info("Disconnected from Daylight network")
    
    async def register_device(
        self,
        device_id: str,
        device_type: DeviceType,
        capacity_kwh: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EnergyDevice:
        """Register energy device with Daylight"""
        device = EnergyDevice(
            id=device_id,
            device_type=device_type,
            capacity_kwh=capacity_kwh,
            metadata=metadata or {}
        )
        
        self.devices[device_id] = device
        logger.info(f"Device registered: {device_id} ({device_type.value}) with {capacity_kwh} kWh capacity")
        
        return device
    
    async def update_energy_output(
        self,
        device_id: str,
        output_kwh: float,
        state: EnergyState
    ) -> bool:
        """Update energy device output"""
        device = self.devices.get(device_id)
        if not device:
            logger.warning(f"Device {device_id} not found")
            return False
        
        device.current_output_kwh = output_kwh
        device.state = state
        device.last_sync = datetime.now().isoformat()
        
        # Calculate rewards based on energy contribution
        if state in [EnergyState.PRODUCING, EnergyState.DISCHARGING]:
            reward = output_kwh * 0.05  # $0.05 per kWh produced
            device.rewards_earned += reward
            
            # Carbon credits (0.5 kg CO2 per kWh renewable energy)
            carbon_credit = output_kwh * 0.5
            device.carbon_credits += carbon_credit
            
            logger.info(f"Device {device_id} produced {output_kwh} kWh, earned ${reward:.2f}, {carbon_credit:.1f} kg CO2 credits")
        
        return True
    
    def get_device(self, device_id: str) -> Optional[EnergyDevice]:
        """Get device by ID"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[EnergyDevice]:
        """Get all registered devices"""
        return list(self.devices.values())
    
    async def sell_energy(
        self,
        device_id: str,
        amount_kwh: float,
        price_per_kwh: float
    ) -> Dict[str, Any]:
        """Sell energy on marketplace"""
        device = self.devices.get(device_id)
        if not device:
            return {"error": "Device not found"}
        
        if device.available_capacity() < amount_kwh:
            return {"error": "Insufficient available energy"}
        
        revenue = amount_kwh * price_per_kwh
        device.rewards_earned += revenue
        
        logger.info(f"Sold {amount_kwh} kWh at ${price_per_kwh}/kWh, revenue: ${revenue:.2f}")
        
        return {
            "success": True,
            "amount_kwh": amount_kwh,
            "price_per_kwh": price_per_kwh,
            "revenue_usd": revenue,
            "device_id": device_id
        }
    
    async def buy_energy(
        self,
        amount_kwh: float,
        max_price_per_kwh: float
    ) -> Dict[str, Any]:
        """Buy energy from marketplace"""
        cost = amount_kwh * max_price_per_kwh
        
        logger.info(f"Buying {amount_kwh} kWh at max ${max_price_per_kwh}/kWh, cost: ${cost:.2f}")
        
        return {
            "success": True,
            "amount_kwh": amount_kwh,
            "price_per_kwh": max_price_per_kwh,
            "cost_usd": cost
        }
    
    async def claim_carbon_credits(self, device_id: str) -> float:
        """Claim carbon credits for device"""
        device = self.devices.get(device_id)
        if not device:
            return 0.0
        
        credits = device.carbon_credits
        device.carbon_credits = 0.0  # Reset after claiming
        
        logger.info(f"Claimed {credits:.1f} kg CO2 credits for device {device_id}")
        return credits
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        total_capacity = sum(device.capacity_kwh for device in self.devices.values())
        total_output = sum(device.current_output_kwh for device in self.devices.values())
        total_rewards = sum(device.rewards_earned for device in self.devices.values())
        total_credits = sum(device.carbon_credits for device in self.devices.values())
        
        producing_devices = sum(1 for d in self.devices.values() if d.state == EnergyState.PRODUCING)
        consuming_devices = sum(1 for d in self.devices.values() if d.state == EnergyState.CONSUMING)
        
        device_types = {}
        for device in self.devices.values():
            dtype = device.device_type.value
            device_types[dtype] = device_types.get(dtype, 0) + 1
        
        return {
            "connected": self.connected,
            "total_devices": len(self.devices),
            "device_types": device_types,
            "producing_devices": producing_devices,
            "consuming_devices": consuming_devices,
            "total_capacity_kwh": total_capacity,
            "total_output_kwh": total_output,
            "total_rewards_earned_usd": total_rewards,
            "total_carbon_credits_kg": total_credits,
            "network_utilization_percent": (total_output / total_capacity * 100) if total_capacity > 0 else 0
        }
    
    async def sync_device(self, device_id: str) -> bool:
        """Sync device state"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        device.last_sync = datetime.now().isoformat()
        logger.debug(f"Synced device {device_id}")
        return True


# Global Daylight connector instance
_daylight_connector: Optional[DaylightConnector] = None


def get_daylight_connector(
    api_key: Optional[str] = None,
    api_endpoint: Optional[str] = None
) -> DaylightConnector:
    """Get global Daylight connector instance (lazy load)"""
    global _daylight_connector
    if _daylight_connector is None:
        _daylight_connector = DaylightConnector(api_key, api_endpoint)
    return _daylight_connector
