#!/usr/bin/env python3
"""
STATUS: INTEGRATED — STUN/TURN NAT Traversal (Phase 1B)
ASIMNEXUS STUN/TURN Client
===========================
STUN (RFC 5389) client for public IP/port discovery.
TURN (RFC 5766) client for relayed transport on restrictive NATs.
NAT type detection via STUN classification.

Integrates with:
  - [`mesh/hole_punching.py`](hole_punching.py) — Coordinates punching with mapped addresses
  - [`mesh/relay.py`](relay.py) — Fallback relay when TURN is too costly
  - [`mesh/p2p_transport.py`](p2p_transport.py) — Uses UDP transport for port-consistent NAT detection
"""

import os
import io
import time
import json
import struct
import socket
import logging
import asyncio
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("AsimNexus.Mesh.STUNTURN")

# ─── Environment Configuration ────────────────────────────────────────────────
_STUN_SERVERS_DEFAULT = json.dumps([
    "stun.l.google.com:19302",
    "stun1.l.google.com:19302",
    "stun2.l.google.com:19302",
    "stun3.l.google.com:19302",
    "stun4.l.google.com:19302"
])
_STUN_SERVERS = json.loads(os.getenv("ASIM_MESH_STUN_SERVERS", _STUN_SERVERS_DEFAULT))
_TURN_SERVERS = json.loads(os.getenv("ASIM_MESH_TURN_SERVERS", '[]'))
_STUN_TIMEOUT_SEC = int(os.getenv("ASIM_MESH_STUN_TIMEOUT", "5"))
_TURN_ALLOCATE_TIMEOUT_SEC = int(os.getenv("ASIM_MESH_TURN_ALLOCATE_TIMEOUT", "10"))
_STUN_RETRIES = int(os.getenv("ASIM_MESH_STUN_RETRIES", "2"))


# ─── STUN Protocol Constants (RFC 5389) ─────────────────────────────────────

STUN_MAGIC_COOKIE = 0x2112A442

# STUN Message Types
class STUNMessageType(Enum):
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101
    BINDING_ERROR_RESPONSE = 0x0111
    ALLOCATE_REQUEST = 0x0003      # TURN
    ALLOCATE_RESPONSE = 0x0103     # TURN
    REFRESH_REQUEST = 0x0004       # TURN
    REFRESH_RESPONSE = 0x0104      # TURN
    SEND_INDICATION = 0x0016       # TURN
    DATA_INDICATION = 0x0017       # TURN
    CREATE_PERMISSION_REQUEST = 0x0008  # TURN
    CREATE_PERMISSION_RESPONSE = 0x0108 # TURN
    CHANNEL_BIND_REQUEST = 0x0009  # TURN
    CHANNEL_BIND_RESPONSE = 0x0109 # TURN

# STUN Attribute Types
class STUNAttributeType(Enum):
    MAPPED_ADDRESS = 0x0001
    XOR_MAPPED_ADDRESS = 0x0020
    RESPONSE_ORIGIN = 0x802B
    OTHER_ADDRESS = 0x802C
    SOFTWARE = 0x8022
    FINGERPRINT = 0x8028
    ERROR_CODE = 0x0009
    REALM = 0x0014
    NONCE = 0x0015
    LIFETIME = 0x000D           # TURN
    XOR_RELAYED_ADDRESS = 0x0016  # TURN
    REQUESTED_TRANSPORT = 0x0019  # TURN
    XOR_PEER_ADDRESS = 0x0012    # TURN
    DATA = 0x0013                # TURN
    EVEN_PORT = 0x0018           # TURN
    RESERVATION_TOKEN = 0x0022   # TURN

# Address families
class AddressFamily(Enum):
    IPV4 = 0x01
    IPV6 = 0x02


class NATType(Enum):
    """Types of NAT detected via STUN classification."""
    UNKNOWN = "unknown"
    OPEN_INTERNET = "open_internet"          # No NAT — direct public IP
    FULL_CONE = "full_cone"                  # Any external host can send to mapped port
    RESTRICTED_CONE = "restricted_cone"      # Only if internal host sent to that IP
    PORT_RESTRICTED_CONE = "port_restricted" # Only if internal host sent to that IP:port
    SYMMETRIC = "symmetric"                  # Different mapping per destination
    UDP_BLOCKED = "udp_blocked"              # UDP completely blocked
    SYMMETRIC_FIREWALL = "symmetric_firewall" # Firewall without NAT


@dataclass
class MappedAddress:
    """Discovered public address mapping."""
    ip_address: str
    port: int
    family: AddressFamily = AddressFamily.IPV4

    def to_tuple(self) -> Tuple[str, int]:
        return (self.ip_address, self.port)

    def __str__(self) -> str:
        return f"{self.ip_address}:{self.port}"


@dataclass
class STUNResult:
    """Result of a STUN binding request."""
    mapped_address: MappedAddress
    latency_ms: float
    server: str
    other_address: Optional[MappedAddress] = None
    software: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TURNAllocation:
    """TURN relayed transport address."""
    relayed_address: MappedAddress
    mapped_address: MappedAddress
    lifetime: int = 600          # Seconds until expiry (TURN default)
    username: Optional[str] = None
    password: Optional[str] = None
    realm: Optional[str] = None
    server: str = ""
    allocated_at: float = field(default_factory=time.time)

    def is_expired(self, buffer_sec: int = 30) -> bool:
        return time.time() - self.allocated_at > (self.lifetime - buffer_sec)

    @property
    def remaining_lifetime(self) -> int:
        remaining = int(self.lifetime - (time.time() - self.allocated_at))
        return max(0, remaining)


@dataclass
class NATClassification:
    """Result of NAT type classification."""
    nat_type: NATType
    public_address: Optional[MappedAddress] = None
    local_address: Optional[MappedAddress] = None
    confidence: float = 1.0  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_hole_punchable(self) -> bool:
        """Whether UDP hole punching is likely to succeed with this NAT type."""
        return self.nat_type in (
            NATType.OPEN_INTERNET,
            NATType.FULL_CONE,
            NATType.RESTRICTED_CONE,
            NATType.PORT_RESTRICTED_CONE,
        )

    @property
    def requires_relay(self) -> bool:
        """Whether TURN/relay is required for this NAT type."""
        return self.nat_type in (
            NATType.SYMMETRIC,
            NATType.UDP_BLOCKED,
            NATType.SYMMETRIC_FIREWALL,
            NATType.UNKNOWN,
        )


# ─── STUN Protocol Helpers ──────────────────────────────────────────────────

def _encode_stun_message(
    msg_type: STUNMessageType,
    transaction_id: bytes,
    attributes: Dict[int, bytes],
) -> bytes:
    """Encode a STUN message (RFC 5389 Section 6)."""
    # Message header: type (2) + length (2) + magic cookie (4) + transaction ID (12)
    attribute_data = b"".join(
        struct.pack("!HH", attr_type, len(attr_value)) + attr_value
        for attr_type, attr_value in attributes.items()
    )
    length = len(attribute_data)
    header = struct.pack("!HH", msg_type.value, length)
    header += struct.pack("!I", STUN_MAGIC_COOKIE)
    header += transaction_id
    return header + attribute_data


def _decode_stun_message(data: bytes) -> Optional[Dict[str, Any]]:
    """Decode a STUN message."""
    if len(data) < 20:
        return None

    msg_type = struct.unpack("!H", data[0:2])[0]
    length = struct.unpack("!H", data[2:4])[0]
    magic_cookie = struct.unpack("!I", data[4:8])[0]
    transaction_id = data[8:20]

    if magic_cookie != STUN_MAGIC_COOKIE:
        return None

    # Parse attributes
    attributes = {}
    pos = 20
    while pos + 4 <= len(data) and pos < 20 + length:
        attr_type = struct.unpack("!H", data[pos:pos+2])[0]
        attr_length = struct.unpack("!H", data[pos+2:pos+4])[0]
        attr_value = data[pos+4:pos+4+attr_length]
        # Pad to 4-byte boundary
        attributes[attr_type] = attr_value
        pos += 4 + attr_length
        if attr_length % 4 != 0:
            pos += 4 - (attr_length % 4)

    return {
        "msg_type": msg_type,
        "transaction_id": transaction_id,
        "attributes": attributes,
    }


def _parse_xor_mapped_address(attr_value: bytes, transaction_id: bytes) -> MappedAddress:
    """Parse XOR-MAPPED-ADDRESS attribute."""
    family = attr_value[1]
    # XOR the port with the last 2 bytes of magic cookie (0x2112A442 → big-endian)
    port_bytes = struct.unpack("!H", attr_value[2:4])[0]
    port = port_bytes ^ (STUN_MAGIC_COOKIE >> 16)

    if family == AddressFamily.IPV4.value:
        # XOR IP with magic cookie (first 4 bytes)
        ip_bytes = attr_value[4:8]
        magic_bytes = struct.pack("!I", STUN_MAGIC_COOKIE)
        xored_ip = bytes(a ^ b for a, b in zip(ip_bytes, magic_bytes))
        ip = socket.inet_ntoa(xored_ip)
        return MappedAddress(ip, port, AddressFamily.IPV4)
    else:
        # IPv6: XOR with transaction ID (first 12 bytes of 16-byte key)
        ip_bytes = attr_value[4:20]
        xored_ip = bytes(a ^ b for a, b in zip(ip_bytes, transaction_id[:12]))
        ip = socket.inet_ntop(socket.AF_INET6, xored_ip)
        return MappedAddress(ip, port, AddressFamily.IPV6)


def _parse_mapped_address(attr_value: bytes) -> MappedAddress:
    """Parse MAPPED-ADDRESS attribute (not XOR'd)."""
    family = attr_value[1]
    port = struct.unpack("!H", attr_value[2:4])[0]
    if family == AddressFamily.IPV4.value:
        ip = socket.inet_ntoa(attr_value[4:8])
        return MappedAddress(ip, port, AddressFamily.IPV4)
    else:
        ip = socket.inet_ntop(socket.AF_INET6, attr_value[4:20])
        return MappedAddress(ip, port, AddressFamily.IPV6)


# ─── STUN Client ────────────────────────────────────────────────────────────

class _STUNQueryProtocol(asyncio.DatagramProtocol):
    """Internal protocol for single STUN query with response future."""

    def __init__(self, response_future: asyncio.Future[bytes]):
        self._response_future = response_future

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        if not self._response_future.done():
            self._response_future.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self._response_future.done():
            self._response_future.set_exception(exc)


class STUNClient:
    """
    STUN client for NAT traversal.
    
    Discovers public IP/port mapping by querying STUN servers.
    Supports RFC 5389 binding requests.
    
    If `transport_port` is provided, the STUN query socket will bind to
    the same port as the P2PTransport's UDP socket for consistent NAT mapping.
    """

    def __init__(self, timeout: float = _STUN_TIMEOUT_SEC, transport_port: Optional[int] = None):
        self.timeout = timeout
        self.transport_port = transport_port

    async def query(
        self,
        server: str = "stun.l.google.com:19302",
        change_ip: bool = False,
        change_port: bool = False,
    ) -> Optional[STUNResult]:
        """
        Perform a STUN binding request using proper asyncio DatagramProtocol.
         
        Args:
            server: STUN server address (host:port)
            change_ip: Request CHANGE-IP (for NAT type detection)
            change_port: Request CHANGE-PORT (for NAT type detection)
         
        Returns:
            STUNResult with mapped address, or None on failure.
        """
        host, port_str = server.split(":")
        port = int(port_str)

        # Resolve hostname
        try:
            addresses = await asyncio.get_event_loop().getaddrinfo(host, port, type=socket.SOCK_DGRAM)
            if not addresses:
                logger.warning(f"Could not resolve STUN server: {server}")
                return None
            addr = addresses[0][4]  # (host, port)
        except Exception as e:
            logger.warning(f"DNS resolution failed for {server}: {e}")
            return None

        transaction_id = os.urandom(12)
        attributes: Dict[int, bytes] = {}

        # SOFTWARE attribute (optional)
        soft_bytes = b"AsimNexus/1.0.0"
        attributes[STUNAttributeType.SOFTWARE.value] = soft_bytes

        data = _encode_stun_message(
            STUNMessageType.BINDING_REQUEST,
            transaction_id,
            attributes,
        )

        # Use transport_port if set, otherwise ephemeral port
        local_addr = ("0.0.0.0", self.transport_port or 0)

        loop = asyncio.get_event_loop()

        # Create a future to receive the STUN response
        response_future: asyncio.Future[bytes] = loop.create_future()
        protocol_factory = lambda: _STUNQueryProtocol(response_future)

        transport, protocol = await loop.create_datagram_endpoint(
            protocol_factory,
            local_addr=local_addr,
        )

        try:
            start = time.time()
            transport.sendto(data, addr)

            # Wait for response with timeout
            try:
                resp_data = await asyncio.wait_for(response_future, timeout=self.timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.debug(f"STUN query to {server} timed out after {self.timeout}s")
                return None

            elapsed = time.time() - start
            result = _decode_stun_message(resp_data)
            if result is None:
                logger.debug(f"STUN response decode failed from {server}")
                return None

            attrs = result["attributes"]

            # Try XOR-MAPPED-ADDRESS first (preferred), fallback to MAPPED-ADDRESS
            mapped = None
            if STUNAttributeType.XOR_MAPPED_ADDRESS.value in attrs:
                mapped = _parse_xor_mapped_address(
                    attrs[STUNAttributeType.XOR_MAPPED_ADDRESS.value],
                    transaction_id,
                )
            elif STUNAttributeType.MAPPED_ADDRESS.value in attrs:
                mapped = _parse_mapped_address(
                    attrs[STUNAttributeType.MAPPED_ADDRESS.value]
                )

            other = None
            if STUNAttributeType.OTHER_ADDRESS.value in attrs:
                other = _parse_xor_mapped_address(
                    attrs[STUNAttributeType.OTHER_ADDRESS.value],
                    transaction_id,
                )

            software = None
            if STUNAttributeType.SOFTWARE.value in attrs:
                software = attrs[STUNAttributeType.SOFTWARE.value].decode("utf-8", errors="replace")

            if mapped:
                return STUNResult(
                    mapped_address=mapped,
                    latency_ms=round(elapsed * 1000, 1),
                    server=server,
                    other_address=other,
                    software=software,
                )

            return None

        except Exception as e:
            logger.debug(f"STUN query to {server} failed: {e}")
            return None
        finally:
            transport.close()

    async def query_multiple(
        self,
        servers: Optional[List[str]] = None,
    ) -> Optional[STUNResult]:
        """Query multiple STUN servers and return the first successful result."""
        if servers is None:
            servers = _STUN_SERVERS

        # Randomize order for load balancing
        shuffled = list(servers)
        random.shuffle(shuffled)

        for server in shuffled:
            result = await self.query(server)
            if result is not None:
                return result

        return None


# ─── NAT Type Detector ──────────────────────────────────────────────────────

class NATDetector:
    """
    Detects NAT type using STUN classification algorithm.
    
    Algorithm (RFC 3489-style with RFC 5389):
    1. Test I: Query primary STUN server → get mapped address
       - No response → UDP blocked
    2. Test II: Query with CHANGE-PORT → different port on same IP
       - Same mapped address → Open Internet
    3. Test III: Query with CHANGE-IP AND CHANGE-PORT → different server
       - Same mapped address → Full Cone NAT
    4. Compare mapped addresses across destinations
       - Different per destination → Symmetric NAT
       - Same per destination → Restricted/Port-Restricted Cone
    
    If `transport_port` is provided, STUN queries will bind to that port
    so NAT mapping is consistent with the P2PTransport's UDP socket.
    """

    def __init__(self, timeout: float = _STUN_TIMEOUT_SEC, transport_port: Optional[int] = None, local_ip: Optional[str] = None):
        self.client = STUNClient(timeout, transport_port=transport_port)
        self.timeout = timeout
        self.transport_port = transport_port
        self.local_ip = local_ip

    async def classify(self) -> NATClassification:
        """
        Classify the NAT type behind this node.

        Short-circuits on localhost — no NAT detected on 127.0.0.1/::1.

        Returns:
            NATClassification with detected type and confidence.
        """
        # Short-circuit on localhost — no NAT on loopback
        if self.local_ip is not None and self.local_ip in ("127.0.0.1", "::1", "localhost", "0.0.0.0"):
            return NATClassification(
                nat_type=NATType.OPEN_INTERNET,
                details={"reason": f"Localhost ({self.local_ip}) — no NAT"},
                confidence=1.0,
            )

        if not _STUN_SERVERS:
            return NATClassification(
                nat_type=NATType.UNKNOWN,
                details={"reason": "No STUN servers configured"},
                confidence=0.0,
            )

        primary_server = _STUN_SERVERS[0]
        secondary_server = _STUN_SERVERS[-1] if len(_STUN_SERVERS) > 1 else _STUN_SERVERS[0]

        # Test I: Basic binding request
        result1 = await self.client.query(primary_server)
        if result1 is None:
            # UDP might be blocked — try other servers
            for server in _STUN_SERVERS[1:]:
                result1 = await self.client.query(server)
                if result1 is not None:
                    primary_server = server
                    break

            if result1 is None:
                return NATClassification(
                    nat_type=NATType.UDP_BLOCKED,
                    details={"reason": "No STUN response received"},
                )

        # Test II: Query with different port (if same server supports CHANGE-PORT)
        # Google STUN servers support this
        result2 = None
        primary_host, primary_port_str = primary_server.split(":")
        primary_base_port = int(primary_port_str)
        alt_port_used = 0
        if primary_server == secondary_server:
            # Try CHANGE-PORT by using a different server port
            for alt_port in [primary_base_port + 1, primary_base_port - 1, primary_base_port + 2]:
                if alt_port > 0 and alt_port < 65536:
                    alt_server = f"{primary_host}:{alt_port}"
                    result2 = await self.client.query(alt_server)
                    if result2 is not None:
                        alt_port_used = alt_port
                        break
        else:
            result2 = await self.client.query(secondary_server)

        # Test III: Query a different STUN server (different IP)
        result3 = None
        alt_server_str = f"{primary_host}:{alt_port_used}" if alt_port_used else ""
        for server in _STUN_SERVERS:
            if server != primary_server and server != alt_server_str:
                result3 = await self.client.query(server)
                if result3 is not None:
                    break

        mapped1 = result1.mapped_address.to_tuple() if result1 else None
        mapped2 = result2.mapped_address.to_tuple() if result2 else None
        mapped3 = result3.mapped_address.to_tuple() if result3 else None

        details: Dict[str, Any] = {
            "test1": str(result1.mapped_address) if result1 else "N/A",
            "test2": str(result2.mapped_address) if result2 else "N/A",
            "test3": str(result3.mapped_address) if result3 else "N/A",
            "server1": primary_server,
        }

        # Determine NAT type
        if mapped1 is None:
            nat_type = NATType.UDP_BLOCKED
        elif mapped2 is None and mapped3 is None:
            nat_type = NATType.UDP_BLOCKED
        else:
            # Check if mapped address matches our local address
            local_ip = self._get_local_ip()
            local_ip_match = mapped1[0] == local_ip

            # Check if mapping changes with destination
            same_test2 = mapped2 == mapped1 if mapped2 else True
            same_test3 = mapped3 == mapped1 if mapped3 else True

            if local_ip_match:
                nat_type = NATType.OPEN_INTERNET
                details["reason"] = "Public IP matches local IP — no NAT"
            elif not same_test2 and mapped2 is not None:
                # Port changed with destination change → Symmetric
                nat_type = NATType.SYMMETRIC
                details["reason"] = "Mapping differs per destination"
            elif same_test3 and mapped3 is not None:
                # Same mapping across different IPs → Full Cone
                nat_type = NATType.FULL_CONE
                details["reason"] = "Same mapping across different destinations"
            elif mapped2 is not None:
                # Same mapping on same IP, different port → Port Restricted
                nat_type = NATType.PORT_RESTRICTED_CONE
                details["reason"] = "Mapping stable on same IP, varies by port"
            else:
                nat_type = NATType.RESTRICTED_CONE
                details["reason"] = "Likely restricted cone NAT"

        return NATClassification(
            nat_type=nat_type,
            public_address=result1.mapped_address if result1 else None,
            local_address=MappedAddress(
                ip_address=self._get_local_ip(),
                port=result1.mapped_address.port if result1 else 0,
            ) if result1 else None,
            confidence=0.8 if nat_type != NATType.UNKNOWN else 0.3,
            details=details,
        )

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


# ─── TURN Client ────────────────────────────────────────────────────────────

class TURNClient:
    """
    TURN (RFC 5766) client for relayed transport.
    
    Allocates a relayed transport address when direct P2P
    connectivity (STUN + hole punching) is not possible.
    """

    def __init__(self, timeout: float = _TURN_ALLOCATE_TIMEOUT_SEC):
        self.timeout = timeout
        self._allocation: Optional[TURNAllocation] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False

    async def allocate(
        self,
        server: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        lifetime: int = 600,
    ) -> Optional[TURNAllocation]:
        """
        Allocate a TURN relayed transport address.
        
        Args:
            server: TURN server address (host:port)
            username: TURN credentials username
            password: TURN credentials password
            lifetime: Requested allocation lifetime in seconds
        
        Returns:
            TURNAllocation with relayed address, or None on failure.
        """
        import socket as sock_mod

        # Use configured servers if not specified
        if not server and _TURN_SERVERS:
            server = _TURN_SERVERS[0]

        if not server:
            logger.warning("No TURN server configured")
            return None

        # Strip protocol prefix (e.g. "turn:" → "") so split(":") works correctly
        clean_server = server
        for prefix in ("turn:", "turns:"):
            if clean_server.startswith(prefix):
                clean_server = clean_server[len(prefix):]
                break

        host, port_str = clean_server.rsplit(":", 1)
        port = int(port_str)

        # TURN allocation is a complex multi-step protocol
        # This implementation provides the core RFC 5766 flow
        # For production, consider using aio-turn or coTURN client

        transaction_id = os.urandom(12)
        attributes: Dict[int, bytes] = {}

        # REQUESTED-TRANSPORT: UDP (value 17)
        attributes[STUNAttributeType.REQUESTED_TRANSPORT.value] = struct.pack("!IB", 17, 0) + b"\x00\x00\x00"

        # LIFETIME (optional)
        attributes[STUNAttributeType.LIFETIME.value] = struct.pack("!I", lifetime)

        # SOFTWARE
        attributes[STUNAttributeType.SOFTWARE.value] = b"AsimNexus/1.0.0"

        data = _encode_stun_message(
            STUNMessageType.ALLOCATE_REQUEST,
            transaction_id,
            attributes,
        )

        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)

        try:
            # Resolve server
            addr_info = await asyncio.get_event_loop().getaddrinfo(
                host, port, type=socket.SOCK_DGRAM
            )
            if not addr_info:
                logger.warning(f"Could not resolve TURN server: {server}")
                sock.close()
                return None
            addr = addr_info[0][4]

            start = time.time()
            sock.sendto(data, addr)

            resp_data, resp_addr = sock.recvfrom(4096)
            elapsed = time.time() - start

            result = _decode_stun_message(resp_data)
            if result is None:
                sock.close()
                return None

            attrs = result["attributes"]

            # Check for error
            if STUNAttributeType.ERROR_CODE.value in attrs:
                err_value = attrs[STUNAttributeType.ERROR_CODE.value]
                err_code = struct.unpack("!I", b"\x00" + err_value[0:3])[0] if len(err_value) >= 4 else 0
                err_msg = err_value[4:].decode("utf-8", errors="replace") if len(err_value) > 4 else ""
                logger.warning(f"TURN allocate error {err_code}: {err_msg}")
                sock.close()
                return None

            # Parse XOR-RELAYED-ADDRESS
            relayed = None
            if STUNAttributeType.XOR_RELAYED_ADDRESS.value in attrs:
                relayed = _parse_xor_mapped_address(
                    attrs[STUNAttributeType.XOR_RELAYED_ADDRESS.value],
                    transaction_id,
                )

            # Parse XOR-MAPPED-ADDRESS
            mapped = None
            if STUNAttributeType.XOR_MAPPED_ADDRESS.value in attrs:
                mapped = _parse_xor_mapped_address(
                    attrs[STUNAttributeType.XOR_MAPPED_ADDRESS.value],
                    transaction_id,
                )

            # Parse LIFETIME
            alloc_lifetime = lifetime
            if STUNAttributeType.LIFETIME.value in attrs:
                alloc_lifetime = struct.unpack("!I", attrs[STUNAttributeType.LIFETIME.value])[0]

            if relayed is None:
                logger.warning("TURN allocation response missing relayed address")
                sock.close()
                return None

            allocation = TURNAllocation(
                relayed_address=relayed,
                mapped_address=mapped or MappedAddress("0.0.0.0", 0),
                lifetime=alloc_lifetime,
                username=username,
                password=password,
                server=server,
            )

            self._allocation = allocation
            logger.info(
                f"🔄 TURN allocation — Relay: {relayed}, "
                f"Lifetime: {alloc_lifetime}s, Latency: {round(elapsed * 1000, 1)}ms"
            )

            sock.close()
            return allocation

        except socket.timeout:
            logger.warning(f"TURN allocate timeout to {server}")
        except Exception as e:
            logger.warning(f"TURN allocate error: {e}")
        finally:
            sock.close()

        return None

    async def refresh_allocation(self) -> bool:
        """Refresh the current TURN allocation to keep it alive."""
        if self._allocation is None or self._allocation.is_expired():
            return False

        # Re-allocate
        new_alloc = await self.allocate(
            server=self._allocation.server,
            username=self._allocation.username,
            password=self._allocation.password,
            lifetime=self._allocation.lifetime,
        )
        return new_alloc is not None

    def get_allocation(self) -> Optional[TURNAllocation]:
        """Get the current TURN allocation."""
        if self._allocation and self._allocation.is_expired():
            self._allocation = None
        return self._allocation

    def release_allocation(self):
        """Release the current TURN allocation."""
        self._allocation = None
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    async def start_auto_refresh(self):
        """Start automatic refresh of TURN allocation."""
        self._running = True
        while self._running:
            if self._allocation and self._allocation.is_expired(buffer_sec=60):
                logger.info("🔄 Refreshing TURN allocation...")
                await self.refresh_allocation()
            await asyncio.sleep(30)

    async def stop_auto_refresh(self):
        """Stop automatic refresh."""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None


# ─── Connection Strategy ────────────────────────────────────────────────────

class ConnectionStrategy(Enum):
    """Preferred P2P connection strategy based on NAT/network conditions."""
    DIRECT = "direct"            # Direct IP:port connection (same LAN or public IP)
    STUN_PUNCH = "stun_punch"    # STUN-discovered addresses + hole punch
    RENDEZVOUS = "rendezvous"    # Bootstrap/relay coordinated punch
    TURN_RELAY = "turn_relay"    # TURN relay (most expensive, most compatible)
    RELAY = "relay"              # Custom relay (fallback)


def select_connection_strategy(
    local_nat: NATClassification,
    remote_nat: NATClassification,
) -> ConnectionStrategy:
    """
    Select the best connection strategy based on both peers' NAT types.
    
    Priority: DIRECT → STUN_PUNCH → RENDEZVOUS → TURN_RELAY → RELAY
    """

    def _is_symmetric(nat_type: NATType) -> bool:
        """Check if a NAT type is symmetric (changes port per destination)."""
        return nat_type in (NATType.SYMMETRIC, NATType.SYMMETRIC_FIREWALL)

    # Both on open internet or same LAN → direct
    if (local_nat.nat_type == NATType.OPEN_INTERNET and
            remote_nat.nat_type == NATType.OPEN_INTERNET):
        return ConnectionStrategy.DIRECT

    # Both are hole-punchable → STUN punch
    if local_nat.is_hole_punchable and remote_nat.is_hole_punchable:
        return ConnectionStrategy.STUN_PUNCH

    # One is hole-punchable, other is symmetric → rendezvous with port prediction
    if local_nat.is_hole_punchable and _is_symmetric(remote_nat.nat_type):
        return ConnectionStrategy.RENDEZVOUS
    if remote_nat.is_hole_punchable and _is_symmetric(local_nat.nat_type):
        return ConnectionStrategy.RENDEZVOUS

    # One is hole-punchable, other is UDP blocked → relay (TCP)
    if local_nat.is_hole_punchable or remote_nat.is_hole_punchable:
        return ConnectionStrategy.RELAY

    # Both unknown → try rendezvous first
    if (local_nat.nat_type == NATType.UNKNOWN and
            remote_nat.nat_type == NATType.UNKNOWN):
        return ConnectionStrategy.RENDEZVOUS

    # At least one requires relay → TURN relay
    if local_nat.requires_relay or remote_nat.requires_relay:
        return ConnectionStrategy.TURN_RELAY

    # Worst case → fallback relay
    return ConnectionStrategy.RELAY


# ─── Global Instances ───────────────────────────────────────────────────────

_STUN_CLIENT: Optional[STUNClient] = None
_NAT_DETECTOR: Optional[NATDetector] = None
_TURN_CLIENT: Optional[TURNClient] = None


def get_stun_client(transport_port: Optional[int] = None) -> STUNClient:
    """Get or create global STUN client."""
    global _STUN_CLIENT
    if _STUN_CLIENT is None:
        _STUN_CLIENT = STUNClient(timeout=_STUN_TIMEOUT_SEC, transport_port=transport_port)
    return _STUN_CLIENT


def get_nat_detector(transport_port: Optional[int] = None) -> NATDetector:
    """Get or create global NAT detector."""
    global _NAT_DETECTOR
    if _NAT_DETECTOR is None:
        _NAT_DETECTOR = NATDetector(timeout=_STUN_TIMEOUT_SEC, transport_port=transport_port)
    return _NAT_DETECTOR


def get_turn_client() -> TURNClient:
    """Get or create global TURN client."""
    global _TURN_CLIENT
    if _TURN_CLIENT is None:
        _TURN_CLIENT = TURNClient()
    return _TURN_CLIENT


def reset_stun_turn():
    """Reset global instances (for testing)."""
    global _STUN_CLIENT, _NAT_DETECTOR, _TURN_CLIENT
    _STUN_CLIENT = None
    _NAT_DETECTOR = None
    _TURN_CLIENT = None
