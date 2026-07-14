"""
Daylight Connector — Decentralized Energy Distribution.
=========================================================
Simulates a DePIN connector for Daylight, a decentralized energy network
where devices produce, consume, and trade energy.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


class DeviceType(Enum):
    """Types of energy devices."""
    SOLAR_INVERTER = "solar_inverter"
    WIND_TURBINE = "wind_turbine"
    BATTERY_STORAGE = "battery_storage"
    SMART_METER = "smart_meter"
    EV_CHARGER = "ev_charger"


class EnergyState(Enum):
    """Operational state of an energy device."""
    PRODUCING = "producing"
    CONSUMING = "consuming"
    IDLE = "idle"
    OFFLINE = "offline"
    CHARGING = "charging"
    DISCHARGING = "discharging"


@dataclass
class EnergyDevice:
    """An energy device in the Daylight network."""
    id: str
    device_type: DeviceType
    capacity_kwh: float
    current_output_kwh: float = 0.0
    state: EnergyState = EnergyState.IDLE
    carbon_credits_earned: float = 0.0
    location: str = ""

    def available_capacity(self) -> float:
        """Return remaining energy capacity."""
        return self.capacity_kwh - self.current_output_kwh

    def utilization_rate(self) -> float:
        """Return current utilization as a percentage."""
        if self.capacity_kwh == 0:
            return 0.0
        return (self.current_output_kwh / self.capacity_kwh) * 100.0


class DaylightConnector:
    """Connector for the Daylight decentralized energy network."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.connected = False
        self._devices: Dict[str, EnergyDevice] = {}
        self._energy_balance: float = 0.0

    async def connect(self) -> bool:
        """Connect to the Daylight network."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the Daylight network."""
        self.connected = False
        return True

    async def register_device(
        self,
        device_id: str,
        device_type: DeviceType,
        capacity_kwh: float,
        location: str = "",
    ) -> EnergyDevice:
        """Register a new energy device.

        Args:
            device_id: Unique device identifier
            device_type: Type of energy device
            capacity_kwh: Maximum capacity in kWh
            location: Optional geographic location

        Returns:
            The registered EnergyDevice
        """
        device = EnergyDevice(
            id=device_id,
            device_type=device_type,
            capacity_kwh=capacity_kwh,
            location=location,
        )
        self._devices[device_id] = device
        return device

    async def update_energy_output(
        self,
        device_id: str,
        output_kwh: float,
        state: EnergyState,
    ) -> bool:
        """Update the energy output of a device.

        Args:
            device_id: Device identifier
            output_kwh: Current output in kWh
            state: Current operational state

        Returns:
            True if successful
        """
        device = self._devices.get(device_id)
        if not device:
            return False
        device.current_output_kwh = output_kwh
        device.state = state
        return True

    async def sell_energy(self, device_id: str, amount_kwh: float, price_per_kwh: float) -> Dict[str, Any]:
        """Sell energy from a device to the grid.

        Args:
            device_id: Device identifier
            amount_kwh: Amount of energy to sell
            price_per_kwh: Price per kWh

        Returns:
            Dict with success status and details
        """
        device = self._devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}
        if device.current_output_kwh < amount_kwh:
            return {"success": False, "error": "Insufficient energy output"}
        revenue = amount_kwh * price_per_kwh
        device.current_output_kwh -= amount_kwh
        self._energy_balance += revenue
        return {"success": True, "revenue": revenue, "amount_kwh": amount_kwh}

    async def buy_energy(self, amount_kwh: float, max_price_per_kwh: float) -> Dict[str, Any]:
        """Buy energy from the grid.

        Args:
            amount_kwh: Amount of energy to buy
            max_price_per_kwh: Maximum acceptable price per kWh

        Returns:
            Dict with success status and details
        """
        cost = amount_kwh * max_price_per_kwh
        self._energy_balance -= cost
        return {"success": True, "cost": cost, "amount_kwh": amount_kwh}

    async def claim_carbon_credits(self, device_id: str) -> float:
        """Claim carbon credits for a device.

        Args:
            device_id: Device identifier

        Returns:
            Carbon credits earned
        """
        device = self._devices.get(device_id)
        if not device:
            return 0.0
        # Simulate carbon credit calculation
        credits = device.current_output_kwh * 0.5
        device.carbon_credits_earned += credits
        return credits

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics.

        Returns:
            Dict with network stats
        """
        total_capacity = sum(d.capacity_kwh for d in self._devices.values())
        total_output = sum(d.current_output_kwh for d in self._devices.values())
        return {
            "total_devices": len(self._devices),
            "total_capacity_kwh": total_capacity,
            "total_output_kwh": total_output,
            "energy_balance": self._energy_balance,
            "connected": self.connected,
        }
