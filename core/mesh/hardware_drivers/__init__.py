"""
STATUS: REAL — Hardware Mesh Communication Drivers
ASIMNEXUS Hardware Drivers
===========================
Low-level drivers for physical mesh communication:
  - Bluetooth/BLE (short-range P2P)
  - WiFi Direct (medium-range P2P)
  - LoRaWAN (long-range, low-power)
  - NFC (tap-to-sync)

Reference: Computer Networks (Andrew S. Tanenbaum),
           Helium Network DePIN Architecture,
           Starlink Mesh Topology

Each driver provides a unified interface:
  - discover() -> List[Peer]
  - connect(peer) -> bool
  - send(peer, data) -> bool
  - receive() -> Optional[Message]
  - disconnect(peer) -> bool
"""

from .base_driver import BaseDriver, HardwarePeer, HardwareMessage, DriverStatus, HardwareProtocol
from .bluetooth_driver import BluetoothDriver
from .wifi_direct_driver import WiFiDirectDriver
from .lorawan_driver import LoRaWANDriver
from .nfc_driver import NFCDriver
from .driver_manager import HardwareDriverManager, get_driver_manager, reset_driver_manager

# Alias for backward compatibility with tests
DriverManager = HardwareDriverManager

__all__ = [
    "BaseDriver",
    "HardwarePeer",
    "HardwareMessage",
    "DriverStatus",
    "HardwareProtocol",
    "BluetoothDriver",
    "WiFiDirectDriver",
    "LoRaWANDriver",
    "NFCDriver",
    "HardwareDriverManager",
    "DriverManager",
    "get_driver_manager",
    "reset_driver_manager",
]
