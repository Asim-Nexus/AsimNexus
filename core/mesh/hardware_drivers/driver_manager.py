"""
STATUS: REAL — Hardware Driver Manager for Mesh Communication
ASIMNEXUS Hardware Driver Manager
==================================
Manages all hardware mesh drivers (Bluetooth, WiFi Direct, LoRaWAN, NFC).
Provides a unified interface for the mesh layer to use any available hardware.

The driver manager:
  - Discovers available hardware drivers
  - Manages driver lifecycle (init/start/stop/shutdown)
  - Routes data through the best available driver
  - Falls back between drivers automatically
"""

import asyncio
import logging
import threading
from typing import Dict, List, Any, Optional, Callable

from .base_driver import (
    BaseDriver, HardwarePeer, HardwareMessage,
    DriverStatus, HardwareProtocol,
)

logger = logging.getLogger("AsimNexus.Mesh.Hardware.DriverManager")


class HardwareDriverManager:
    """
    Manages all hardware mesh drivers.
    
    Provides automatic fallback: if Bluetooth is unavailable,
    try WiFi Direct, then LoRaWAN, then NFC.
    """
    
    def __init__(self):
        self._drivers: Dict[str, BaseDriver] = {}
        self._lock = threading.Lock()
        self._initialized = False
        self._message_handlers: List[Callable[[HardwareMessage], None]] = []
    
    def register_driver(self, name: str, driver: BaseDriver) -> None:
        """Register a hardware driver."""
        with self._lock:
            self._drivers[name] = driver
            logger.info(f"  📟 Registered driver: {name} ({driver.protocol.value})")
    
    def unregister_driver(self, name: str) -> None:
        """Unregister a hardware driver."""
        with self._lock:
            self._drivers.pop(name, None)
    
    async def initialize_all(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, bool]:
        """Initialize all registered drivers."""
        configs = configs or {}
        results = {}
        
        for name, driver in self._drivers.items():
            try:
                config = configs.get(name, {})
                success = await driver.initialize(config)
                results[name] = success
                if success:
                    logger.info(f"  ✅ Driver '{name}' initialized")
                else:
                    logger.warning(f"  ⚠️  Driver '{name}' failed to initialize")
            except Exception as e:
                results[name] = False
                logger.error(f"  ❌ Driver '{name}' initialization error: {e}")
        
        self._initialized = any(results.values())
        return results
    
    async def discover_all(self, timeout_sec: float = 5.0) -> Dict[str, List[HardwarePeer]]:
        """Discover peers using all available drivers."""
        results = {}
        
        for name, driver in self._drivers.items():
            if driver.status == DriverStatus.READY or driver.status == DriverStatus.CONNECTED:
                try:
                    peers = await driver.discover(timeout_sec)
                    results[name] = peers
                except Exception as e:
                    logger.warning(f"Discovery failed for {name}: {e}")
                    results[name] = []
        
        return results
    
    async def send_via_best_driver(
        self, data: bytes, preferred_protocol: Optional[HardwareProtocol] = None
    ) -> bool:
        """
        Send data using the best available driver.
        
        Priority: preferred_protocol > WiFi Direct > Bluetooth > LoRaWAN > NFC
        """
        # Try preferred protocol first
        if preferred_protocol:
            for name, driver in self._drivers.items():
                if driver.protocol == preferred_protocol and driver.status == DriverStatus.CONNECTED:
                    peers = driver.get_peers()
                    connected = [p for p in peers if p.metadata.get("connected")]
                    if connected:
                        for peer in connected:
                            if await driver.send(peer, data):
                                return True
        
        # Fallback: try all connected drivers
        priority = [
            HardwareProtocol.WIFI_DIRECT,
            HardwareProtocol.BLUETOOTH,
            HardwareProtocol.BLUETOOTH_LE,
            HardwareProtocol.LORAWAN,
            HardwareProtocol.NFC,
        ]
        
        for proto in priority:
            for name, driver in self._drivers.items():
                if driver.protocol == proto and driver.status == DriverStatus.CONNECTED:
                    peers = driver.get_peers()
                    connected = [p for p in peers if p.metadata.get("connected")]
                    if connected:
                        for peer in connected:
                            if await driver.send(peer, data):
                                return True
        
        logger.warning("No connected driver available to send data")
        return False

    async def send_via_protocol(
        self,
        protocol: str,
        node_id: str,
        message: Any,
    ) -> Dict[str, Any]:
        """Send a message via a specific protocol to a node.
        
        This method is used by the chaos/fallback test suite to simulate
        protocol-level failures and verify automatic fallback behavior.
        """
        # Find the driver matching the requested protocol
        for name, driver in self._drivers.items():
            if driver.protocol.value == protocol.lower() or name == protocol.lower():
                if driver.status == DriverStatus.READY or driver.status == DriverStatus.CONNECTED:
                    try:
                        # Find the target peer
                        peers = driver.get_peers()
                        target = None
                        for p in peers:
                            if p.peer_id == node_id or p.metadata.get("node_id") == node_id:
                                target = p
                                break
                        if target is None:
                            # Create a virtual peer for the target node
                            from .base_driver import HardwarePeer
                            target = HardwarePeer(
                                peer_id=node_id,
                                protocol=driver.protocol,
                                metadata={"node_id": node_id, "connected": True},
                            )
                        success = await driver.send(target, message if isinstance(message, bytes) else str(message).encode())
                        if success:
                            return {"status": "sent", "protocol": protocol, "node_id": node_id}
                        return {"status": "error", "error": f"Failed to send via {protocol}"}
                    except Exception as e:
                        return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": f"No driver available for protocol: {protocol}"}

    def get_available_drivers(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all drivers."""
        return {
            name: driver.get_status()
            for name, driver in self._drivers.items()
        }
    
    def get_connected_peers(self) -> List[HardwarePeer]:
        """Get all connected peers across all drivers."""
        peers = []
        for driver in self._drivers.values():
            peers.extend([
                p for p in driver.get_peers()
                if p.metadata.get("connected")
            ])
        return peers
    
    def on_message(self, handler: Callable[[HardwareMessage], None]) -> None:
        """Register a global message handler."""
        self._message_handlers.append(handler)
        # Register with all drivers
        for driver in self._drivers.values():
            driver.on_message(handler)
    
    async def shutdown_all(self) -> None:
        """Shutdown all drivers."""
        for name, driver in self._drivers.items():
            try:
                await driver.shutdown()
                logger.info(f"  ✅ Driver '{name}' shutdown")
            except Exception as e:
                logger.error(f"  ❌ Driver '{name}' shutdown error: {e}")
        self._initialized = False


# ── Singleton Factory ─────────────────────────────────────────────────────

_driver_manager: Optional[HardwareDriverManager] = None
_driver_manager_lock = threading.Lock()


def get_driver_manager() -> HardwareDriverManager:
    """Get or create the global HardwareDriverManager singleton."""
    global _driver_manager
    if _driver_manager is None:
        with _driver_manager_lock:
            if _driver_manager is None:
                _driver_manager = HardwareDriverManager()
                # Register default drivers
                _driver_manager.register_driver("bluetooth", BluetoothDriver())
                _driver_manager.register_driver("wifi_direct", WiFiDirectDriver())
                _driver_manager.register_driver("lorawan", LoRaWANDriver())
                _driver_manager.register_driver("nfc", NFCDriver())
    return _driver_manager


def reset_driver_manager() -> None:
    """Reset the singleton (for testing)."""
    global _driver_manager
    _driver_manager = None


# Alias for backward compatibility with test imports
DriverManager = HardwareDriverManager


# Import here to avoid circular imports
from .bluetooth_driver import BluetoothDriver
from .wifi_direct_driver import WiFiDirectDriver
from .lorawan_driver import LoRaWANDriver
from .nfc_driver import NFCDriver
