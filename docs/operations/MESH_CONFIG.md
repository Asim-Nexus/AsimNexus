# Mesh Layer Configuration Reference

This document describes all environment variables that control the ASIMNEXUS mesh networking layer. Variables are organized by subsystem.

---

## Table of Contents

1. [P2P Transport (`p2p_transport.py`)](#1-p2p-transport)
2. [Bootstrap Service (`bootstrap.py`)](#2-bootstrap-service)
3. [P2P Integration (`p2p_integration.py`)](#3-p2p-integration)
4. [Kademlia DHT (`kademlia_dht.py`)](#4-kademlia-dht)
5. [Multi-Mesh Router (`multi_mesh_router.py`)](#5-multi-mesh-router)
6. [Multi-Hop Router (`multi_hop_router.py`)](#6-multi-hop-router)
7. [Mesh Node (`mesh_node.py`)](#7-mesh-node)
8. [Auto-Discovery (`autodiscovery.py`)](#8-auto-discovery)
9. [Hole Punching (`hole_punching.py`) / NAT Traversal (`nat_traversal.py`)](#9-hole-punching--nat-traversal)
10. [STUN/TURN (`stun_turn.py`)](#10-stunturn)
11. [Relay Service (`relay.py`)](#11-relay-service)
12. [CRDT Sync (`crdt_sync.py`)](#12-crdt-sync)
13. [Offline Sync (`offline_sync_engine.py`)](#13-offline-sync)
14. [Node Registry (`node_registry.py`)](#14-node-registry)
15. [Common Patterns](#15-common-patterns)

---

## 1. P2P Transport

**File:** [`mesh/p2p_transport.py`](../../mesh/p2p_transport.py)

### Retry & Health

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_INITIAL_RETRY_DELAY` | `1.0` | Initial delay (seconds) before reconnecting to a dropped peer. |
| `ASIM_MESH_MAX_RETRY_DELAY` | `60.0` | Maximum delay (seconds) between reconnection attempts (exponential backoff). |
| `ASIM_MESH_RETRY_BACKOFF` | `2.0` | Multiplier applied to retry delay after each failed attempt. |
| `ASIM_MESH_HEALTH_PING_INTERVAL` | `30.0` | Interval (seconds) between periodic PING messages to connected peers. |
| `ASIM_MESH_HEALTH_PING_TIMEOUT` | `5.0` | Timeout (seconds) to wait for a PONG response before marking a peer as TIMEOUT. |
| `ASIM_MESH_PEER_STALE_TIMEOUT` | `300.0` | Time (seconds) after which a peer with no activity is considered stale. |
| `ASIM_MESH_PEER_BAD_THRESHOLD` | `3` | Number of consecutive failures after which a peer is marked bad and excluded from reconnection. |

### Connection Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_MAX_CONNECTIONS_PER_MIN` | `30` | Maximum number of outbound WebSocket connections allowed per 60-second sliding window. |
| `ASIM_MESH_MAX_PEERS` | `500` | Maximum total peers tracked in the routing table. |

### Message Size

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_MAX_MESSAGE_SIZE` | `1048576` | Maximum payload size (bytes) before a message is automatically fragmented into chunks. Default 1 MB. |

---

## 2. Bootstrap Service

**File:** [`mesh/bootstrap.py`](../../mesh/bootstrap.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_BOOTSTRAP_PORT` | `7335` | TCP port for the bootstrap server (also used as default client bootstrap port). |
| `ASIM_MESH_BOOTSTRAP_MAX_NODES` | `50` | Maximum number of bootstrap nodes tracked. |
| `ASIM_MESH_BOOTSTRAP_NODE_TIMEOUT` | `3600` | Time (seconds) after which a bootstrap node is considered stale if not refreshed. Default 1 hour. |
| `ASIM_MESH_BOOTSTRAP_CACHE_TTL` | `300` | Time-to-live (seconds) for cached bootstrap responses. |
| `ASIM_MESH_BOOTSTRAP_SEEDS` | `""` | Comma-separated list of seed bootstrap nodes. Each entry has the format `node_id:hostname:port:region`. **Important:** Use hostnames (e.g., `localhost`), not IP addresses — the colon separator conflicts with IPv4 addresses. Example: `node1:localhost:7335:global,node2:bootstrap.example.com:7335:us-west` |
| `ASIM_MESH_BOOTSTRAP_RESPONSE_LIMIT` | `5` | Maximum number of bootstrap nodes returned in a single bootstrap response. |

---

## 3. P2P Integration

**File:** [`mesh/p2p_integration.py`](../../mesh/p2p_integration.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_P2P_PEER_DISCOVERY_INTERVAL` | `60` | Interval (seconds) between peer discovery rounds. |
| `ASIM_P2P_HEALTH_PING_INTERVAL` | `30` | Interval (seconds) between health PING rounds for all connected peers. |
| `ASIM_P2P_MAX_PEERS_PER_MESH` | `50` | Maximum number of peers tracked per mesh type. |

---

## 4. Kademlia DHT

**File:** [`mesh/kademlia_dht.py`](../../mesh/kademlia_dht.py)

### Core Constants

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_DHT_K` | `20` | Kademlia replication parameter — number of nodes stored per bucket. |
| `ASIM_MESH_DHT_ALPHA` | `3` | Kademlia concurrency parameter — number of parallel lookups. |
| `ASIM_MESH_DHT_ID_LENGTH` | `160` | Node ID length (bits). Uses SHA-1 at 160 bits. |
| `ASIM_MESH_DHT_PORT` | `7332` | Default UDP port for DHT communication. |
| `ASIM_MESH_DHT_NODE_STALE_SEC` | `3600` | Time (seconds) before a DHT node is considered stale. |
| `ASIM_MESH_DHT_MAX_FAILURES` | `3` | PING failures before a DHT node is marked bad. |
| `ASIM_MESH_DHT_REFRESH_INTERVAL` | `3600` | Interval (seconds) between automatic bucket refresh operations. |
| `ASIM_MESH_DHT_TTL` | `86400` | Default TTL (seconds) for stored key-value pairs. Default 24 hours. |
| `ASIM_MESH_DHT_LOOKUP_ITERATIONS` | `5` | Maximum iterations for iterative lookup operations. |

---

## 5. Multi-Mesh Router

**File:** [`mesh/multi_mesh_router.py`](../../mesh/multi_mesh_router.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_AUTO_SWITCH_INTERVAL` | `30` | Interval (seconds) between automatic mesh switching evaluations. |
| `ASIM_MESH_DEFAULT` | `local` | Default mesh type used when no routing rule matches. |
| `ASIM_MESH_DB_PATH` | `data/mesh_routing.jsonl` | Path to the mesh routing audit trail file. |
| `ASIM_MESH_HEALTH_TIMEOUT` | `10` | Timeout (seconds) for mesh health checks. |

---

## 6. Multi-Hop Router

**File:** [`mesh/multi_hop_router.py`](../../mesh/multi_hop_router.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_MAX_HOPS` | `5` | Maximum TTL for multi-hop routing. |
| `ASIM_MESH_PATH_DISCOVERY_TIMEOUT` | `10` | Timeout (seconds) for path discovery requests. |
| `ASIM_MESH_PATH_DISCOVERY_TTL` | `5` | TTL for path discovery query packets. |
| `ASIM_MESH_PATH_REFRESH_INTERVAL` | `120` | Interval (seconds) between path refresh operations. |
| `ASIM_MESH_STORE_FORWARD_EXPIRY` | `3600` | Expiry (seconds) for store-and-forward messages. |
| `ASIM_MESH_MULTIHOP_RETRY` | `30` | Interval (seconds) between multi-hop retry attempts. |
| `ASIM_MESH_MAX_PATH_AGE` | `300` | Maximum age (seconds) before a cached path is evicted. |
| `ASIM_MESH_MAX_STORED_MSGS` | `1000` | Maximum number of store-and-forward messages kept. |

---

## 7. Mesh Node

**File:** [`mesh/mesh_node.py`](../../mesh/mesh_node.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_HEARTBEAT_INTERVAL` | `30` | Interval (seconds) between node heartbeat broadcasts. |
| `ASIM_MESH_NODE_DISCOVERY_INTERVAL` | `60` | Interval (seconds) between node discovery rounds. |
| `ASIM_MESH_NODE_STARTUP_TIMEOUT` | `30` | Timeout (seconds) for node startup sequence. |
| `ASIM_MESH_AUTO_RECOVER` | `true` | Enable automatic recovery of failed mesh components. |
| `ASIM_MESH_ENABLE_RELAY` | `true` | Enable TCP/UDP relay service. |
| `ASIM_MESH_ENABLE_RENDEZVOUS` | `true` | Enable rendezvous server for NAT traversal coordination. |
| `ASIM_MESH_ENABLE_MULTIHOP` | `true` | Enable multi-hop routing capability. |
| `ASIM_MESH_TURN_USERNAME` | `""` | Username for TURN server authentication. |
| `ASIM_MESH_TURN_PASSWORD` | `""` | Password for TURN server authentication. |

---

## 8. Auto-Discovery

**File:** [`mesh/autodiscovery.py`](../../mesh/autodiscovery.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_DISCOVERY_PORT` | `7331` | UDP port for LAN discovery beacons. |
| `ASIM_MESH_DISCOVERY_INTERVAL` | `30` | Interval (seconds) between discovery scans. |
| `ASIM_MESH_BEACON_INTERVAL` | `60` | Interval (seconds) between beacon broadcasts. |
| `ASIM_MESH_DISCOVERY_TIMEOUT` | `5` | Timeout (seconds) for a single discovery scan. |
| `ASIM_MESH_STALE_NODE_AGE` | `300` | Age (seconds) after which a discovered node is considered stale. |

---

## 9. Hole Punching / NAT Traversal

**Files:** [`mesh/hole_punching.py`](../../mesh/hole_punching.py), [`mesh/nat_traversal.py`](../../mesh/nat_traversal.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_HOLE_PUNCH_TIMEOUT` | `10` | Timeout (seconds) for hole-punching operations. |
| `ASIM_MESH_HOLE_PUNCH_RETRIES` | `3` | Number of hole-punch retry attempts. |
| `ASIM_MESH_PUNCH_INTERVAL` | `0.1` | Interval (seconds) between individual punch attempts. |
| `ASIM_MESH_RENDEZVOUS_PORT` | `7336` | UDP port for the rendezvous coordination server. |
| `ASIM_MESH_PUNCH_KEEPALIVE` | `15` | Interval (seconds) for keepalive pings on punched connections. |
| `ASIM_MESH_RELAY_FALLBACK_TIMEOUT` | `10` | Timeout (seconds) before falling back to relay when hole punching fails. |
| `ASIM_MESH_TURN_SERVER` | `turn:localhost:3478` | TURN server URI for relay fallback. |

---

## 10. STUN/TURN

**File:** [`mesh/stun_turn.py`](../../mesh/stun_turn.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_STUN_SERVERS` | See source | JSON array of STUN server URIs. Defaults include Google's public STUN servers. |
| `ASIM_MESH_TURN_SERVERS` | `[]` | JSON array of TURN server URIs. |
| `ASIM_MESH_STUN_TIMEOUT` | `5` | Timeout (seconds) per STUN query. |
| `ASIM_MESH_TURN_ALLOCATE_TIMEOUT` | `10` | Timeout (seconds) for TURN allocation requests. |
| `ASIM_MESH_STUN_RETRIES` | `2` | Number of STUN query retries per server. |

---

## 11. Relay Service

**File:** [`mesh/relay.py`](../../mesh/relay.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_RELAY_PORT` | `7334` | TCP/UDP port for the relay service. |
| `ASIM_MESH_RELAY_SESSION_TIMEOUT` | `300` | Session idle timeout (seconds). Default 5 minutes. |
| `ASIM_MESH_RELAY_MAX_SESSIONS` | `100` | Maximum number of concurrent relay sessions. |

---

## 12. CRDT Sync

**File:** [`mesh/crdt_sync.py`](../../mesh/crdt_sync.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_CRDT_OP_MAX_AGE` | `86400` | Maximum age (seconds) for CRDT operations in the log before pruning. Default 24 hours. |

---

## 13. Offline Sync

**File:** [`mesh/offline_sync_engine.py`](../../mesh/offline_sync_engine.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_SYNC_DB_PATH` | `data/offline_sync.jsonl` | Path to the offline sync queue file. |
| `ASIM_SYNC_INTERVAL` | `15` | Interval (seconds) between sync attempts. |
| `ASIM_SYNC_BATCH_SIZE` | `50` | Maximum number of operations per sync batch. |
| `ASIM_SYNC_MAX_RETRIES` | `5` | Maximum retry attempts for failed sync operations. |
| `ASIM_SYNC_RETRY_BACKOFF` | `30` | Backoff delay (seconds) between sync retries. |
| `ASIM_NODE_ID` | Auto-generated | Override node identifier used across subsystems. |

---

## 14. Node Registry

**File:** [`mesh/node_registry.py`](../../mesh/node_registry.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_MESH_NODE_REGISTRY_DB` | `data/node_registry.db` | Path to the node registry database file. |
| `ASIM_MESH_NODE_REGISTRY_STALE_AGE` | `3600` | Age (seconds) after which a node record is considered stale. |
| `ASIM_MESH_NODE_REGISTRY_EVENT_LIMIT` | `100` | Maximum number of trust events returned per query. |

---

## 15. Common Patterns

### How Env Vars Are Read

Most mesh modules use one of two patterns:

**Pattern A — Module-level constants (read at import time):**
```python
# mesh/p2p_transport.py
MAX_MESSAGE_SIZE = int(os.getenv("ASIM_MESH_MAX_MESSAGE_SIZE", "1048576"))
```
These cannot be overridden after import without reloading the module.

**Pattern B — Read at call time (preferred for testability):**
```python
# mesh/bootstrap.py (inside _load_default_bootstraps)
custom_seeds = os.getenv("ASIM_MESH_BOOTSTRAP_SEEDS", "")
```
These support runtime override, which is essential for tests that modify `os.environ`.

### Format Conventions

- **Numeric values:** Parsed with `int()` or `float()` — use string defaults.
- **Boolean values:** Typically use `os.getenv("VAR", "default").lower() == "true"`.
- **JSON arrays:** Parsed with `json.loads()` for structured values like STUN/TURN server lists.
- **Colon-separated seeds:** The `ASIM_MESH_BOOTSTRAP_SEEDS` format uses colons as delimiters (`node_id:host:port:region`), which means IPv4 addresses cannot be used directly — use hostnames instead.

### Default Ports Summary

| Port | Service |
|------|---------|
| `7331` | LAN Discovery (UDP) |
| `7332` | DHT / UDP RPC |
| `7333` | WebSocket P2P |
| `7334` | Relay Service |
| `7335` | Bootstrap Service |
| `7336` | Rendezvous Service |
