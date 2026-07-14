"""
STATUS: REAL — Base Driver Interface for Hardware Mesh Communication
ASIMNEXUS Base Hardware Driver
===============================
Abstract base class for all hardware mesh communication drivers.
Provides a unified interface for Bluetooth, WiFi Direct, LoRaWAN, and NFC.

Each driver implementation must implement:
  - discover() -> List[HardwarePeer]
  - connect(peer) -> bool
  - send(peer, data) -> bool
  - receive() -> Optional[HardwareMessage]
  - disconnect(peer) -> bool
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod


class DriverStatus(str, Enum):
    """Status of a hardware driver."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


class HardwareProtocol(str, Enum):
    """Supported hardware protocols."""
    BLUETOOTH = "bluetooth"
    BLUETOOTH_LE = "ble"
    WIFI_DIRECT = "wifi_direct"
    LORA = "lora"
    LORAWAN = "lorawan"
    NFC = "nfc"
    ZIGBEE = "zigbee"


@dataclass
class HardwarePeer:
    """A peer discovered via hardware protocol."""
    peer_id: str
    name: str
    protocol: HardwareProtocol
    address: str  # MAC address or device address
    signal_strength: float = 0.0  # dBm
    last_seen: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "name": self.name,
            "protocol": self.protocol.value,
            "address": self.address,
            "signal_strength": self.signal_strength,
            "last_seen": self.last_seen,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
        }


@dataclass
class HardwareMessage:
    """A message received via hardware protocol."""
    message_id: str = field(default_factory=lambda: f"hwmsg_{uuid.uuid4().hex[:12]}")
    sender_id: str = ""
    protocol: HardwareProtocol = HardwareProtocol.BLUETOOTH
    payload: bytes = b""
    timestamp: float = field(default_factory=time.time)
    rssi: float = 0.0  # Received signal strength
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "protocol": self.protocol.value,
            "payload_size": len(self.payload),
            "timestamp": self.timestamp,
            "rssi": self.rssi,
            "metadata": self.metadata,
        }


class BaseDriver(ABC):
    """
    Abstract base class for hardware mesh drivers.
    
    All hardware drivers (Bluetooth, WiFi Direct, LoRaWAN, NFC)
    must implement this interface.
    """
    
    def __init__(self, protocol: HardwareProtocol, name: str):
        self.protocol = protocol
        self.name = name
        self.status = DriverStatus.UNINITIALIZED
        self._peers: Dict[str, HardwarePeer] = {}
        self._message_handlers: List[Callable[[HardwareMessage], None]] = []
        self._error_handlers: List[Callable[[str], None]] = []
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the hardware driver."""
        pass
    
    @abstractmethod
    async def discover(self, timeout_sec: float = 5.0) -> List[HardwarePeer]:
        """Discover nearby peers."""
        pass
    
    @abstractmethod
    async def connect(self, peer: HardwarePeer) -> bool:
        """Connect to a discovered peer."""
        pass
    
    @abstractmethod
    async def send(self, peer: HardwarePeer, data: bytes) -> bool:
        """Send data to a connected peer."""
        pass
    
    @abstractmethod
    async def receive(self, timeout_sec: float = 1.0) -> Optional[HardwareMessage]:
        """Receive data from any connected peer."""
        pass
    
    @abstractmethod
    async def disconnect(self, peer: HardwarePeer) -> bool:
        """Disconnect from a peer."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the driver and release hardware resources."""
        pass
    
    def on_message(self, handler: Callable[[HardwareMessage], None]) -> None:
        """Register a message handler."""
        self._message_handlers.append(handler)
    
    def on_error(self, handler: Callable[[str], None]) -> None:
        """Register an error handler."""
        self._error_handlers.append(handler)
    
    def _notify_message(self, message: HardwareMessage) -> None:
        """Notify all message handlers."""
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as e:
                self._notify_error(f"Message handler error: {e}")
    
    def _notify_error(self, error: str) -> None:
        """Notify all error handlers."""
        for handler in self._error_handlers:
            try:
                handler(error)
            except Exception:
                pass
    
    def get_peers(self) -> List[HardwarePeer]:
        """Get all discovered peers."""
        return list(self._peers.values())
    
    def get_status(self) -> Dict[str, Any]:
        """Get driver status."""
        return {
            "name": self.name,
            "protocol": self.protocol.value,
            "status": self.status.value,
            "peers_count": len(self._peers),
            "connected_peers": sum(1 for p in self._peers.values() 
                                   if p.metadata.get("connected", False)),
        }
