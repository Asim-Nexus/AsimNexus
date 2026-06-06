# P1A: Transport Foundation — Detailed Implementation Plan

> **Phase:** P1A (Transport Foundation)
> **Parent:** [v1.2 Roadmap](v12_roadmap.md)
> **Theme:** Production-harden the existing real-asyncio P2P transport layer with TLS, observability, resilience, and benchmarking

---

## ⚠️ Correction: Current State Assessment

After thorough code review, the v1.2 roadmap's claim that `p2p_transport.py` and `bootstrap.py` use "simulation/loopback" is **incorrect**. Both files already use **real asyncio transports**:

| Component | Status | Lines | Evidence |
|-----------|--------|-------|----------|
| [`mesh/p2p_transport.py`](../mesh/p2p_transport.py) | **REAL** | 1095 | Uses `asyncio.DatagramProtocol` for UDP, `asyncio.start_server()` for WebSocket/TCP, `asyncio.open_connection()` for outbound. Full handshake (HELLO/ACK), PING/PONG, session state machine, exponential backoff. |
| [`mesh/bootstrap.py`](../mesh/bootstrap.py) | **REAL** | 684 | Uses `asyncio.start_server()` for bootstrap TCP, `asyncio.open_connection()` for client requests. Full registration/discovery protocol. |
| [`tests/real/test_mesh_transport.py`](../tests/real/test_mesh_transport.py) | **REAL** | 764 | 11 test classes covering lifecycle, UDP RPC, WebSocket handshake, state machine, PING/PONG, bootstrap integration, full end-to-end flow. |
| [`tests/real/test_mesh_kademlia.py`](../tests/real/test_mesh_kademlia.py) | **REAL** | 984 | DHT with real P2PTransport integration. |
| [`tests/real/test_mesh_sync.py`](../tests/real/test_mesh_sync.py) | **REAL** | 996 | CRDT sync over real WebSocket transport. |

**P1A is therefore a hardening/polish phase, not a "wire to real sockets" phase.**

---

## Files to Modify

### 1. `mesh/p2p_transport.py` — Transport Hardening

#### 1a. TLS/mTLS Support for WebSocket Connections

**Goal:** Allow WebSocket connections to be secured with TLS (WSS), optionally with mutual TLS (mTLS) using the existing [`security/security_mtls.py`](../security/security_mtls.py) infrastructure.

**Changes:**

1. **Add `ssl_context` parameter to `__init__`** (line 206):
   ```python
   def __init__(
       self,
       node_id: str,
       host: str = "0.0.0.0",
       port_udp: int = 7332,
       port_ws: int = 7333,
       ssl_context: Optional[ssl.SSLContext] = None,
   ):
       self._ssl_context = ssl_context
   ```

2. **Modify `start()` method** (line 877): Pass `ssl_context` to `asyncio.start_server()`:
   ```python
   # Current (line 920):
   self._ws_server = await asyncio.start_server(
       self._handle_ws_connection,
       self.host,
       self.port_ws,
   )
   # New:
   self._ws_server = await asyncio.start_server(
       self._handle_ws_connection,
       self.host,
       self.port_ws,
       ssl=self._ssl_context,
   )
   ```

3. **Modify `connect_peer()` method** (line 661): Pass `ssl_context` to `asyncio.open_connection()`:
   ```python
   # Current (line 670):
   reader, writer = await asyncio.wait_for(
       asyncio.open_connection(host, port_ws),
       timeout=timeout,
   )
   # New:
   reader, writer = await asyncio.wait_for(
       asyncio.open_connection(host, port_ws, ssl=self._ssl_context),
       timeout=timeout,
   )
   ```

4. **Add `is_secure` property**:
   ```python
   @property
   def is_secure(self) -> bool:
       return self._ssl_context is not None
   ```

5. **Update `get_stats()`** (line 1030): Add `"tls_enabled": self.is_secure` to the stats dict.

6. **Add `ssl` import** at top of file.

#### 1b. Transport Event Emission

**Goal:** Emit structured events for observability via the event bus, enabling the dashboard to track transport health.

**Changes:**

1. **Add event import** (top of file):
   ```python
   from core.event_bus import event_bus, ASIMEvent, EventType
   ```

2. **Emit events at key lifecycle points:**
   - **After successful peer connection** (in `_handle_peer_hello`, line 658):
     ```python
     await event_bus.publish(ASIMEvent(
         event_type=EventType.PEER_CONNECTED,
         source="P2PTransport",
         data={
             "peer_id": peer_id,
             "host": host,
             "port_ws": port_ws,
             "version": version,
             "transport_secure": self.is_secure,
         }
     ))
     ```
   - **On peer disconnection** (in `_handle_ws_connection` finally block, line 602):
     ```python
     if peer_id:
         await event_bus.publish(ASIMEvent(
             event_type=EventType.PEER_DISCONNECTED,
             source="P2PTransport",
             data={"peer_id": peer_id, "reason": "connection_closed"}
         ))
     ```
   - **On RPC timeout** (in `rpc_call`, line 507):
     ```python
     await event_bus.publish(ASIMEvent(
         event_type=EventType.RPC_TIMEOUT,
         source="P2PTransport",
         data={"peer_id": peer.node_id, "msg_type": msg_type, "timeout": timeout}
     ))
     ```
   - **On transport start/stop** (in `start()`/`stop()`):
     ```python
     await event_bus.publish(ASIMEvent(
         event_type=EventType.TRANSPORT_STATE_CHANGE,
         source="P2PTransport",
         data={"state": "started", "node_id": self.node_id}
     ))
     ```

3. **Check if `EventType` has these values** — if not, add them:
   ```python
   # In core/event_bus.py EventType enum:
   PEER_CONNECTED = "peer_connected"
   PEER_DISCONNECTED = "peer_disconnected"
   RPC_TIMEOUT = "rpc_timeout"
   TRANSPORT_STATE_CHANGE = "transport_state_change"
   ```

#### 1c. Message Fragmentation for Large Payloads

**Goal:** Support payloads larger than 1MB by implementing chunked transfer.

**Changes:**

1. **Add a message chunking protocol** (new section, after `WSMessageType` enum, ~line 86):
   ```python
   MAX_MESSAGE_SIZE = 1_000_000  # 1MB (current hard limit)
   CHUNK_SIZE = 256_000          # 256KB per chunk
   
   def chunk_message(msg: P2PMessage) -> List[P2PMessage]:
       """Split a large message into chunks."""
       body = msg.to_bytes()
       if len(body) <= MAX_MESSAGE_SIZE:
           return [msg]
       chunks = []
       total_chunks = (len(body) + CHUNK_SIZE - 1) // CHUNK_SIZE
       for i in range(0, len(body), CHUNK_SIZE):
           chunk_payload = {
               "msg_id": msg.msg_id,
               "chunk_index": i // CHUNK_SIZE,
               "total_chunks": total_chunks,
               "data": base64.b64encode(body[i:i+CHUNK_SIZE]).decode(),
           }
           chunks.append(P2PMessage(
               msg_type="CHUNK",
               sender_id=msg.sender_id,
               msg_id=f"{msg.msg_id}:chunk{i//CHUNK_SIZE}",
               payload=chunk_payload,
           ))
       return chunks
   
   def reassemble_chunks(chunks: List[P2PMessage]) -> Optional[P2PMessage]:
       """Reassemble chunked messages into original."""
       if not chunks:
           return None
       chunks.sort(key=lambda c: c.payload["chunk_index"])
       raw = b"".join(
           base64.b64decode(c.payload["data"]) for c in chunks
       )
       return P2PMessage.from_bytes(raw)
   ```

2. **Modify `_handle_ws_connection()`** (line 525): Add chunk reassembly buffer:
   ```python
   self._chunk_buffers: Dict[str, List[P2PMessage]] = {}
   ```
   And in the message loop, intercept `CHUNK` type messages for reassembly.

3. **Modify `send_ws()`** (line 750): Auto-chunk messages larger than `MAX_MESSAGE_SIZE`.

#### 1d. Auto-Reconnect for Dropped WebSocket Connections

**Goal:** When a persistent WebSocket connection drops, automatically attempt reconnection with exponential backoff.

**Changes:**

1. **Add reconnection logic in `_handle_ws_connection` finally block** (line 602):
   ```python
   if peer_id and self._running:
       # Schedule reconnection attempt with backoff
       peer = self.peers.get(peer_id)
       if peer and not peer.is_bad():
           delay = min(peer.retry_delay, MAX_RETRY_DELAY)
           asyncio.create_task(self._reconnect_peer(peer_id, delay))
   ```

2. **Add `_reconnect_peer()` method**:
   ```python
   async def _reconnect_peer(self, peer_id: str, delay: float):
       """Attempt to reconnect to a peer after a dropped connection."""
       await asyncio.sleep(delay)
       async with self._lock:
           peer = self.peers.get(peer_id)
           if not peer or peer.connection_state == ConnectionState.CONNECTED:
               return
           peer.connection_state = ConnectionState.CONNECTING
       try:
       new_id = await self.connect_peer(peer.host, peer.port_ws)
       if new_id:
           logger.info(f"🔄 Reconnected to peer {peer_id}")
   except Exception as e:
           logger.debug(f"Reconnection to {peer_id} failed: {e}")
           peer.record_failure()
   ```

#### 1e. Connection Rate Limiting

**Goal:** Prevent connection storms and resource exhaustion.

**Changes:**

1. **Add rate limit constants** (near line 50):
   ```python
   MAX_CONNECTIONS_PER_MINUTE = int(os.getenv("ASIM_MESH_MAX_CONNECTIONS_PER_MIN", "30"))
   MAX_PEERS_TOTAL = int(os.getenv("ASIM_MESH_MAX_PEERS", "500"))
   ```

2. **Add rate limiter to `__init__`** (line 206):
   ```python
   self._connection_timestamps: List[float] = []
   ```

3. **Guard `connect_peer()`** (line 661) with rate check:
   ```python
   now = time.time()
   self._connection_timestamps = [t for t in self._connection_timestamps if now - t < 60]
   if len(self._connection_timestamps) >= MAX_CONNECTIONS_PER_MINUTE:
       logger.warning("Connection rate limit exceeded, throttling...")
       await asyncio.sleep(2.0)
   self._connection_timestamps.append(now)
   ```

#### 1f. Structured Error Types

**Goal:** Replace generic `Exception` with typed transport errors.

**Changes:**

1. **Add error class hierarchy** (after imports, ~line 33):
   ```python
   class TransportError(Exception):
       """Base transport error."""
   class ConnectionError(TransportError):
       """Connection-level failure."""
   class HandshakeError(TransportError):
       """Peer handshake failed."""
   class MessageTooLargeError(TransportError):
       """Message exceeds maximum size."""
   class RateLimitError(TransportError):
       """Connection rate limit exceeded."""
   class SecurityError(TransportError):
       """TLS/mTLS authentication failure."""
   ```

2. **Replace bare `except Exception` with specific error types** throughout the file (affects ~15 locations).

#### 1g. Configuration via Environment Variables

**Goal:** Make all hardcoded constants configurable at runtime.

**Changes:**

Replace constants at lines 43-50 with env-var-backed values:
```python
INITIAL_RETRY_DELAY = float(os.getenv("ASIM_MESH_INITIAL_RETRY_DELAY", "1.0"))
MAX_RETRY_DELAY = float(os.getenv("ASIM_MESH_MAX_RETRY_DELAY", "60.0"))
RETRY_BACKOFF_MULTIPLIER = float(os.getenv("ASIM_MESH_RETRY_BACKOFF", "2.0"))
HEALTH_PING_INTERVAL = float(os.getenv("ASIM_MESH_HEALTH_PING_INTERVAL", "30.0"))
HEALTH_PING_TIMEOUT = float(os.getenv("ASIM_MESH_HEALTH_PING_TIMEOUT", "5.0"))
PEER_STALE_TIMEOUT = float(os.getenv("ASIM_MESH_PEER_STALE_TIMEOUT", "300.0"))
PEER_BAD_THRESHOLD = int(os.getenv("ASIM_MESH_PEER_BAD_THRESHOLD", "3"))
```

---

### 2. `mesh/bootstrap.py` — Bootstrap Hardening

#### 2a. TLS Support for Bootstrap Connections

**Goal:** Allow bootstrap TCP connections to use TLS.

**Changes:**

1. **Add `ssl_context` parameter to `__init__`** (line 133):
   ```python
   def __init__(self, node_id: str, is_bootstrap: bool = False, 
                port: Optional[int] = None, ssl_context: Optional[ssl.SSLContext] = None):
       self._ssl_context = ssl_context
   ```

2. **Modify `start()` method** (line 181): Pass `ssl_context` to `asyncio.start_server()`:
   ```python
   self._server = await asyncio.start_server(
       self._handle_bootstrap_request,
       "0.0.0.0",
       self.port,
       ssl=self._ssl_context,
   )
   ```

3. **Modify `request_bootstrap()` method** (line 375): Pass `ssl_context` to `asyncio.open_connection()`:
   ```python
   reader, writer = await asyncio.open_connection(
       bootstrap_address, bootstrap_port,
       ssl=self._ssl_context,
   )
   ```

#### 2b. DNS-Based Seed Discovery

**Goal:** Dynamically resolve bootstrap seed nodes instead of relying on hardcoded IPs.

**Changes:**

1. **Modify `_load_default_bootstraps()` method** (line 168): Add async DNS resolution:
   ```python
   async def _load_default_bootstraps(self):
       """Load default bootstrap nodes with DNS resolution."""
       for config in DEFAULT_BOOTSTRAPS:
           try:
               # Resolve hostname to IP
               ips = await asyncio.get_event_loop().getaddrinfo(
                   config["ip_address"], config["port"]
               )
               resolved_ip = ips[0][4][0]
               node = BootstrapNode(
                   node_id=config["node_id"],
                   ip_address=resolved_ip,
                   port=config["port"],
                   region=BootstrapRegion(config["region"]),
               )
               self.bootstrap_nodes[node.node_id] = node
           except Exception as e:
               logger.warning(f"DNS resolution failed for {config['node_id']}: {e}")
   ```

2. **Make bootstrap list configurable via env var** (add near line 81):
   ```python
   _CUSTOM_BOOTSTRAP = os.getenv("ASIM_MESH_BOOTSTRAP_SEEDS", "")
   # Format: "node_id1:host1:port1:region1,node_id2:host2:port2:region2"
   ```

#### 2c. Bootstrap Retry with Backoff

**Goal:** Retry bootstrap connections with exponential backoff on failure.

**Changes:**

1. **Modify `bootstrap()` method** (line 461): Add retry loop:
   ```python
   async def bootstrap(self, register_self: bool = False, ...):
       max_retries = 3
       for attempt in range(max_retries):
           for bootstrap_node in self.bootstrap_nodes.values():
               if bootstrap_node.node_id == self.node_id:
                   continue
               response = await self.request_bootstrap(...)
               if response and response.success:
                   return nodes
           if attempt < max_retries - 1:
               delay = 2.0 ** attempt  # 1s, 2s, 4s
               logger.info(f"Bootstrap retry {attempt+1}/{max_retries} in {delay}s...")
               await asyncio.sleep(delay)
   ```

#### 2d. Bootstrap Event Emission

**Changes:**

1. **Emit events on bootstrap lifecycle:**
   - On successful bootstrap: `EventType.BOOTSTRAP_COMPLETE`
   - On bootstrap failure: `EventType.BOOTSTRAP_FAILED`
   - On peer registration: `EventType.PEER_REGISTERED`

2. **Add imports and emit events** at appropriate locations in `start()`, `bootstrap()`, `register_peer()`.

#### 2e. Bootstrap Response Caching

**Goal:** Cache bootstrap responses to avoid redundant requests.

**Changes:**

1. **Add cache dict to `__init__`** (line 133):
   ```python
   self._bootstrap_cache: Dict[str, Tuple[BootstrapResponse, float]] = {}
   self._bootstrap_cache_ttl = int(os.getenv("ASIM_MESH_BOOTSTRAP_CACHE_TTL", "300"))
   ```

2. **Check cache before making request** in `request_bootstrap()`:
   ```python
   cache_key = f"{bootstrap_address}:{bootstrap_port}"
   if cache_key in self._bootstrap_cache:
       cached, timestamp = self._bootstrap_cache[cache_key]
       if time.time() - timestamp < self._bootstrap_cache_ttl:
           return cached
   ```

---

### 3. `tests/real/test_mesh_transport.py` — Add Missing Test Coverage

#### 3a. TLS Connection Tests

**Goal:** Verify that TLS-secured WebSocket connections work.

**New test class** (append to file):
```python
class TestTLSConnections:
    """WebSocket connections with TLS."""

    @pytest.mark.asyncio
    async def test_tls_handshake(self):
        """Two transports connect with self-signed TLS certs."""
        # Generate temporary self-signed cert
        # Create transport A (server) with SSL context
        # Create transport B (client) with SSL context (verify_mode=CERT_NONE for test)
        # Connect B -> A via WebSocket
        # Verify HELLO/ACK succeeds over TLS
        pass
```

**Requires:** `pytest` fixture to generate temporary self-signed certificates (or use `trustme` library).

#### 3b. Concurrent Connection Tests

**Goal:** Verify many peers can connect simultaneously.

**New test class:**
```python
class TestConcurrentConnections:
    """Multiple peers connecting simultaneously."""

    @pytest.mark.asyncio
    async def test_10_peers_connect(self):
        """10 transports connect to a single server transport."""
        # Start 1 server transport
        # Start 10 client transports
        # All clients connect to server simultaneously
        # Verify all 10 connections are established
        # Verify broadcasts reach all peers
        pass
```

#### 3c. Message Fragmentation Tests

```python
class TestMessageFragmentation:
    """Large message chunking and reassembly."""

    @pytest.mark.asyncio
    async def test_large_payload_chunking(self):
        """A 2MB payload is chunked, sent, and reassembled."""
        pass
```

#### 3d. Auto-Reconnect Tests

```python
class TestAutoReconnect:
    """Automatic reconnection after connection drop."""

    @pytest.mark.asyncio
    async def test_peer_reconnects_after_drop(self):
        """After server stops and restarts, client reconnects."""
        pass
```

#### 3e. Rate Limiting Tests

```python
class TestRateLimiting:
    """Connection rate limiting prevents abuse."""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Exceeding connection rate triggers throttling."""
        pass
```

#### 3f. Bootstrap DNS Resolution Tests

```python
class TestBootstrapDNS:
    """Bootstrap DNS-based seed discovery."""

    @pytest.mark.asyncio
    async def test_dns_resolution(self):
        """Bootstrap seeds resolve DNS addresses."""
        pass
```

---

### 4. `mesh/p2p_integration.py` — Observability Wiring

**Goal:** Wire P2PIntegration to use the new transport event emission for mesh health tracking.

**Changes:**

1. **In `start()` method**: Subscribe to transport events:
   ```python
   event_bus.subscribe(EventType.PEER_CONNECTED, self._on_peer_connected)
   event_bus.subscribe(EventType.PEER_DISCONNECTED, self._on_peer_disconnected)
   ```

2. **Add event handlers** that update `MultiMeshRouter` mesh profiles based on peer connectivity.

---

### 5. `scripts/run_benchmarks.py` — Transport Benchmark

**Goal:** Add P2P transport benchmarks to the existing benchmark suite.

**New benchmark function** (add to `bench_mesh_layer()`):
```python
def bench_p2p_transport():
    """Benchmark P2P message serialization and round-trip."""
    iterations = 10000
    
    # Benchmark P2PMessage serialization
    msg = P2PMessage(...)
    def serialize():
        return msg.to_bytes()
    yield run_benchmark("P2PMessage serialization", serialize, iterations)
    
    # Benchmark P2PMessage deserialization
    raw = msg.to_bytes()
    def deserialize():
        return P2PMessage.from_bytes(raw)
    yield run_benchmark("P2PMessage deserialization", deserialize, iterations)
```

---

## New Files

### 6. `tests/real/test_mesh_transport_tls.py` — TLS Test File

**Purpose:** Separate TLS-specific tests that require certificate generation.

**Structure:**
```python
"""TLS integration tests for P2P Transport Layer (Phase 1A)."""

import ssl
import tempfile
import os
from pathlib import Path

class TestTLSConnections:
    # Uses pytest fixtures for temporary certs
    ...

class TestmTLSConnections:
    # Tests mutual TLS with client cert verification
    ...
```

### 7. `docs/operations/MESH_CONFIG.md` — Configuration Reference

**Purpose:** Document all environment variables for mesh transport configuration.

**Content categories:**
- Port configuration (`ASIM_MESH_UDP_PORT`, `ASIM_MESH_WS_PORT`, `ASIM_MESH_BOOTSTRAP_PORT`)
- Timeout/retry configuration (`ASIM_MESH_INITIAL_RETRY_DELAY`, `ASIM_MESH_PEER_STALE_TIMEOUT`, etc.)
- TLS configuration (`ASIM_MESH_TLS_CERT_PATH`, `ASIM_MESH_TLS_KEY_PATH`, `ASIM_MESH_MTLS_REQUIRED`)
- Rate limits (`ASIM_MESH_MAX_CONNECTIONS_PER_MIN`, `ASIM_MESH_MAX_PEERS`)
- Bootstrap configuration (`ASIM_MESH_BOOTSTRAP_SEEDS`, `ASIM_MESH_BOOTSTRAP_CACHE_TTL`)
- Discovery configuration (`ASIM_MESH_DISCOVERY_PORT`, `ASIM_MESH_DISCOVERY_INTERVAL`)

---

## Implementation Order

The work should be done in this order to minimize merge conflicts and maximize testability:

| Step | File | Change | Risk | Testable In Isolation? |
|------|------|--------|------|----------------------|
| 1 | `mesh/p2p_transport.py` | Environment variable configuration (1g) | Low | Yes |
| 2 | `mesh/p2p_transport.py` | Structured error types (1f) | Low | Yes |
| 3 | `mesh/p2p_transport.py` | Rate limiting (1e) | Low | Yes |
| 4 | `mesh/p2p_transport.py` | Message fragmentation (1c) | Medium | Yes |
| 5 | `mesh/p2p_transport.py` | Auto-reconnect (1d) | Medium | Yes |
| 6 | `mesh/p2p_transport.py` | TLS/mTLS support (1a) | Medium | Yes |
| 7 | `mesh/p2p_transport.py` | Transport event emission (1b) | Low | Partial (needs event_bus) |
| 8 | `mesh/bootstrap.py` | Bootstrap retry with backoff (2c) | Low | Yes |
| 9 | `mesh/bootstrap.py` | Bootstrap response caching (2e) | Low | Yes |
| 10 | `mesh/bootstrap.py` | DNS-based seed discovery (2b) | Medium | Yes |
| 11 | `mesh/bootstrap.py` | TLS support (2a) | Medium | Yes |
| 12 | `mesh/bootstrap.py` | Bootstrap event emission (2d) | Low | Partial (needs event_bus) |
| 13 | `mesh/p2p_integration.py` | Observability wiring (4) | Low | Partial (needs event_bus) |
| 14 | `scripts/run_benchmarks.py` | Transport benchmark (5) | Low | Yes |
| 15 | `tests/real/test_mesh_transport.py` | New test coverage (3) | Low | Yes |
| 16 | New: `tests/real/test_mesh_transport_tls.py` | TLS tests (6) | Low | Yes (with certs) |
| 17 | New: `docs/operations/MESH_CONFIG.md` | Configuration reference (7) | Low | Docs only |

---

## Exit Criteria Verification

Run these commands to verify P1A completion:

```powershell
# 1. Existing transport tests still pass
python -m pytest tests/real/test_mesh_transport.py -v --timeout=60

# 2. TLS tests pass (requires cert fixture)
python -m pytest tests/real/test_mesh_transport_tls.py -v --timeout=60

# 3. Kademlia integration tests still pass (regression)
python -m pytest tests/real/test_mesh_kademlia.py -v --timeout=120

# 4. CRDT sync tests still pass (regression)
python -m pytest tests/real/test_mesh_sync.py -v --timeout=120

# 5. Benchmarks complete without regression
python scripts/run_benchmarks.py

# 6. No TransportError/Exception bare except warnings
python -W error::DeprecationWarning -c "from mesh.p2p_transport import *"

# 7. Event bus integration: verify events fire (manual or integration test)
python -c "
import asyncio
from core.event_bus import event_bus
from mesh.p2p_transport import P2PTransport
async def test():
    t = P2PTransport('test', '127.0.0.1', 0, 0)
    await t.start()
    await t.stop()
asyncio.run(test())
"
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TLS cert generation complexity in tests | Medium | Medium | Use `trustme` library or write a fixture that generates self-signed certs with `cryptography` |
| Event bus imports causing circular deps | Low | High | Use lazy import or late-binding in event emission code paths |
| Chunking protocol breaking existing integrations | Low | Medium | Keep chunking opt-in at the transport level; existing message flows under 1MB unaffected |
| Auto-reconnect causing connection storms | Low | Medium | Rate limiter (1e) acts as circuit breaker; reconnection uses exponential backoff |
| DNS resolution blocking event loop | Medium | Low | Use `asyncio.get_event_loop().getaddrinfo()` (already async); add timeout |

---

## Dependencies on Other Phases

| Component | Depends On | Delivers To |
|-----------|-----------|-------------|
| TLS/mTLS support (1a) | Security layer `security_mtls.py` | P2 (OS control remote connections), P4 (multi-user), P5 (platform clients) |
| Event emission (1b) | `core/event_bus.py` | P1B-P1D (observability during NAT/routing/sync), P2 (device health monitoring) |
| Message fragmentation (1c) | None | P1D (large CRDT sync states), P4 (file sharing), P5 (media sync) |
| Auto-reconnect (1d) | None | P1B (hole-punched connections are fragile), P1C (DHT routing stability) |
| DNS seed discovery (2b) | None | Production deployment (no hardcoded IPs) |
| Transport benchmarks (5) | Existing `run_benchmarks.py` | All future phases (regression detection) |

---

## Summary of Effort

| Category | Files Modified | New Files | Lines Changed (Est.) |
|----------|---------------|-----------|---------------------|
| Transport hardening | 1 | 0 | ~200-300 added |
| Bootstrap hardening | 1 | 0 | ~100-150 added |
| Tests expanded | 1 | 1 | ~400-500 added |
| Observability wiring | 1 | 0 | ~50 added |
| Benchmarks | 1 | 0 | ~50 added |
| Documentation | 0 | 1 | ~100 added |
| **Total** | **5 modified** | **2 new** | **~900-1150 added** |
