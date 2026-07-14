"""
DIMO Connector — Connected Vehicles and IoT.
==============================================
Simulates a DePIN connector for DIMO, a decentralized network
for connected vehicles and IoT devices.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


class VehicleState(Enum):
    """Operational state of a vehicle."""
    PARKED = "parked"
    DRIVING = "driving"
    CHARGING = "charging"
    IDLE = "idle"
    OFFLINE = "offline"


class DataType(Enum):
    """Types of vehicle telemetry data."""
    SPEED = "speed"
    LOCATION = "location"
    BATTERY = "battery"
    FUEL = "fuel"
    ODOMETER = "odometer"
    TEMPERATURE = "temperature"
    TIRE_PRESSURE = "tire_pressure"
    ENGINE_STATUS = "engine_status"


@dataclass
class Vehicle:
    """A vehicle registered in the DIMO network."""
    id: str
    vin: str
    make: str
    model: str
    year: int
    state: VehicleState = VehicleState.PARKED
    rewards_earned: float = 0.0
    _telemetry: Dict[str, float] = field(default_factory=dict)
    _permissions: Dict[str, List[str]] = field(default_factory=dict)

    def add_telemetry(self, data_type: DataType, value: float) -> None:
        """Add a telemetry data point."""
        self._telemetry[data_type.value] = value

    def get_telemetry(self, data_type: DataType) -> Optional[float]:
        """Get a telemetry data point."""
        return self._telemetry.get(data_type.value)


class DIMOConnector:
    """Connector for the DIMO decentralized vehicle network."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.connected = False
        self._vehicles: Dict[str, Vehicle] = {}

    async def connect(self) -> bool:
        """Connect to the DIMO network."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from the DIMO network."""
        self.connected = False
        return True

    async def register_vehicle(
        self,
        vehicle_id: str,
        vin: str,
        make: str,
        model: str,
        year: int,
    ) -> Vehicle:
        """Register a new vehicle.

        Args:
            vehicle_id: Unique vehicle identifier
            vin: Vehicle Identification Number
            make: Vehicle manufacturer
            model: Vehicle model
            year: Model year

        Returns:
            The registered Vehicle
        """
        vehicle = Vehicle(
            id=vehicle_id,
            vin=vin,
            make=make,
            model=model,
            year=year,
        )
        self._vehicles[vehicle_id] = vehicle
        return vehicle

    async def update_telemetry(self, vehicle_id: str, data_type: DataType, value: float) -> bool:
        """Update vehicle telemetry data.

        Args:
            vehicle_id: Vehicle identifier
            data_type: Type of telemetry data
            value: Telemetry value

        Returns:
            True if successful
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return False
        vehicle.add_telemetry(data_type, value)
        return True

    async def share_data(
        self,
        vehicle_id: str,
        data_types: List[DataType],
        duration_minutes: int,
    ) -> Dict[str, Any]:
        """Share vehicle data with the network.

        Args:
            vehicle_id: Vehicle identifier
            data_types: Types of data to share
            duration_minutes: Duration of data sharing

        Returns:
            Dict with success status and details
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "data_types": [dt.value for dt in data_types],
            "duration_minutes": duration_minutes,
        }

    async def grant_permission(self, vehicle_id: str, data_type: str, grantee: str) -> bool:
        """Grant data access permission to a third party.

        Args:
            vehicle_id: Vehicle identifier
            data_type: Type of data to grant access to
            grantee: Entity receiving permission

        Returns:
            True if successful
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return False
        if data_type not in vehicle._permissions:
            vehicle._permissions[data_type] = []
        if grantee not in vehicle._permissions[data_type]:
            vehicle._permissions[data_type].append(grantee)
        return True

    async def revoke_permission(self, vehicle_id: str, data_type: str, grantee: str) -> bool:
        """Revoke data access permission from a third party.

        Args:
            vehicle_id: Vehicle identifier
            data_type: Type of data to revoke access to
            grantee: Entity losing permission

        Returns:
            True if successful
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return False
        if data_type in vehicle._permissions and grantee in vehicle._permissions[data_type]:
            vehicle._permissions[data_type].remove(grantee)
            return True
        return False

    async def claim_rewards(self, vehicle_id: str) -> float:
        """Claim accumulated rewards for a vehicle.

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            Reward amount
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return 0.0
        # Simulate reward calculation
        reward = 5.0
        vehicle.rewards_earned += reward
        return reward

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics.

        Returns:
            Dict with network stats
        """
        makes = set(v.make for v in self._vehicles.values())
        return {
            "total_vehicles": len(self._vehicles),
            "vehicle_makes": list(makes),
            "connected": self.connected,
        }
