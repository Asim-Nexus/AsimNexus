#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Mesh Network Tools for Agent System

Tool functions for mesh network operations: peer discovery, messaging,
network status, and broadcasting.

Each function has a TOOL_DEFINITION dict for OpenAI-compatible function calling,
proper error handling, and structured JSON-serializable return values.

Security: These are SECURE-level tools (read-only mesh operations) except
mesh_send and mesh_broadcast which are SENSITIVE (network writes).
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.Tools.Mesh")

# ─── Constants ─────────────────────────────────────────────────────────────────

_MESH_PEERS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "quad_mesh", "peers.json"
)
_MESH_STATUS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "mesh_status.json"
)
_LOCAL_NODE_ID = os.environ.get("ASIM_NODE_ID", "node_asim_default")


# ─── Helper ────────────────────────────────────────────────────────────────────

def _safe_result(success: bool, data: Any = None,
                 error: Optional[str] = None, **extra) -> Dict:
    """Build a standardized result dict."""
    result = {"success": success, "error": error}
    if data is not None:
        result["data"] = data
    result.update(extra)
    return result


def _load_peers() -> List[Dict]:
    """Load mesh peers from the peers registry file."""
    if not os.path.exists(_MESH_PEERS_PATH):
        return []
    try:
        with open(_MESH_PEERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("peers", [])
        return []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load mesh peers: {e}")
        return []


def _save_peers(peers: List[Dict]):
    """Save mesh peers to the peers registry file."""
    try:
        os.makedirs(os.path.dirname(_MESH_PEERS_PATH), exist_ok=True)
        with open(_MESH_PEERS_PATH, "w", encoding="utf-8") as f:
            json.dump({"peers": peers, "updated_at": datetime.utcnow().isoformat()}, f, indent=2)
    except OSError as e:
        logger.error(f"Failed to save mesh peers: {e}")
        raise


# ─── TOOL: mesh_discover ───────────────────────────────────────────────────────

TOOL_DEFINITION_MESH_DISCOVER = {
    "name": "mesh_discover",
    "description": "Discover mesh network peers. Returns a list of online peers with their capabilities and metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "timeout": {
                "type": "integer",
                "description": "Discovery timeout in seconds (default: 5).",
                "default": 5
            }
        }
    }
}


def mesh_discover(timeout: int = 5) -> Dict[str, Any]:
    """Discover mesh network peers.

    Attempts to discover peers via:
    1. Reading the local peer registry
    2. Broadcasting discovery request (if mesh module available)

    Args:
        timeout: Discovery timeout in seconds.

    Returns:
        Dict with keys: success, peers (list of peer dicts), count
    """
    logger.info(f"Mesh discover (timeout={timeout}s)")

    peers = []
    discovery_method = "registry"

    # Try active discovery via mesh module
    try:
        from mesh.unified_mesh import get_mesh_coordinator
        coordinator = get_mesh_coordinator()
        if coordinator and hasattr(coordinator, 'discover_peers'):
            discovered = coordinator.discover_peers(timeout=timeout)
            if discovered:
                peers = discovered
                discovery_method = "active"
                logger.info(f"Active discovery found {len(peers)} peers")
    except ImportError:
        logger.debug("mesh.unified_mesh not available")
    except Exception as e:
        logger.warning(f"Active mesh discovery failed: {e}")

    # Fallback to registry
    if not peers:
        peers = _load_peers()
        discovery_method = "registry"
        logger.info(f"Registry discovery found {len(peers)} peers")

    # Annotate peers with status
    current_time = time.time()
    for peer in peers:
        # Check if peer is "online" based on last_seen (within 5 minutes)
        last_seen = peer.get("last_seen", 0)
        if isinstance(last_seen, str):
            try:
                last_seen_dt = datetime.fromisoformat(last_seen)
                last_seen = last_seen_dt.timestamp()
            except (ValueError, TypeError):
                last_seen = 0
        peer["online"] = (current_time - last_seen) < 300 if last_seen else False

    return _safe_result(
        success=True,
        data={
            "peers": peers,
            "count": len(peers),
            "discovery_method": discovery_method,
            "local_node_id": _LOCAL_NODE_ID,
        }
    )


# ─── TOOL: mesh_send ───────────────────────────────────────────────────────────

TOOL_DEFINITION_MESH_SEND = {
    "name": "mesh_send",
    "description": "Send a message to a specific mesh peer by node ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "node_id": {
                "type": "string",
                "description": "Target node ID to send the message to."
            },
            "message": {
                "type": "string",
                "description": "Message content to send."
            },
            "message_type": {
                "type": "string",
                "description": "Type of message (e.g., 'text', 'command', 'data').",
                "default": "text"
            }
        },
        "required": ["node_id", "message"]
    }
}


def mesh_send(node_id: str, message: str, message_type: str = "text") -> Dict[str, Any]:
    """Send a message to a specific mesh peer.

    Args:
        node_id: Target node ID.
        message: Message content.
        message_type: Message type classification.

    Returns:
        Dict with keys: success, message_id, delivered_to, timestamp
    """
    logger.info(f"Mesh send: -> {node_id} (type={message_type}, {len(message)} chars)")

    message_id = f"msg_{int(time.time())}_{hash(node_id) % 10000}"

    # Try to send via mesh module
    try:
        from mesh.unified_mesh import get_mesh_coordinator
        coordinator = get_mesh_coordinator()
        if coordinator and hasattr(coordinator, 'send_message'):
            result = coordinator.send_message(
                target_node=node_id,
                message=message,
                message_type=message_type,
            )
            if result.get("success"):
                logger.info(f"Message sent to {node_id} via mesh module")
                return _safe_result(
                    success=True,
                    data={
                        "message_id": message_id,
                        "delivered_to": node_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "delivery_method": "mesh",
                    }
                )
    except ImportError:
        logger.debug("mesh.unified_mesh not available")
    except Exception as e:
        logger.warning(f"Mesh send failed via coordinator: {e}")

    # Fallback: save to message queue file
    try:
        msg_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "mesh_messages"
        )
        os.makedirs(msg_dir, exist_ok=True)

        msg_file = os.path.join(msg_dir, f"{message_id}.json")
        msg_data = {
            "message_id": message_id,
            "from_node": _LOCAL_NODE_ID,
            "to_node": node_id,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "queued",
        }

        with open(msg_file, "w", encoding="utf-8") as f:
            json.dump(msg_data, f, indent=2)

        logger.info(f"Message queued for {node_id}: {message_id}")
        return _safe_result(
            success=True,
            data={
                "message_id": message_id,
                "delivered_to": node_id,
                "timestamp": msg_data["timestamp"],
                "delivery_method": "queued",
                "note": "Message queued for delivery. Target may be offline.",
            }
        )

    except Exception as e:
        logger.error(f"Failed to queue message for {node_id}: {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: mesh_status ─────────────────────────────────────────────────────────

TOOL_DEFINITION_MESH_STATUS = {
    "name": "mesh_status",
    "description": "Get the current mesh network status, including connected peers, network health, and latency.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}


def mesh_status() -> Dict[str, Any]:
    """Get mesh network status.

    Returns:
        Dict with keys: success, local_node_id, peers_online, peers_total,
                        network_healthy, uptime, status
    """
    logger.info("Mesh status check")

    peers = _load_peers()
    current_time = time.time()

    online_peers = []
    offline_peers = []

    for peer in peers:
        last_seen = peer.get("last_seen", 0)
        if isinstance(last_seen, str):
            try:
                last_seen_dt = datetime.fromisoformat(last_seen)
                last_seen = last_seen_dt.timestamp()
            except (ValueError, TypeError):
                last_seen = 0

        is_online = (current_time - last_seen) < 300 if last_seen else False
        peer_info = {
            "node_id": peer.get("node_id", peer.get("id", "unknown")),
            "name": peer.get("name", peer.get("hostname", "")),
            "online": is_online,
            "last_seen": last_seen,
            "capabilities": peer.get("capabilities", []),
            "latency_ms": peer.get("latency_ms"),
        }

        if is_online:
            online_peers.append(peer_info)
        else:
            offline_peers.append(peer_info)

    # Try to get system-level mesh status
    mesh_module_available = False
    try:
        from mesh.unified_mesh import get_mesh_coordinator
        coordinator = get_mesh_coordinator()
        mesh_module_available = coordinator is not None
    except ImportError:
        pass

    network_healthy = len(online_peers) > 0 or len(peers) == 0
    status = "healthy" if network_healthy else "degraded"
    if not peers:
        status = "standalone"

    return _safe_result(
        success=True,
        data={
            "local_node_id": _LOCAL_NODE_ID,
            "peers_online": len(online_peers),
            "peers_total": len(peers),
            "peers": online_peers + offline_peers,
            "offline_peers": len(offline_peers),
            "network_healthy": network_healthy,
            "status": status,
            "mesh_module_available": mesh_module_available,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ─── TOOL: mesh_broadcast ──────────────────────────────────────────────────────

TOOL_DEFINITION_MESH_BROADCAST = {
    "name": "mesh_broadcast",
    "description": "Broadcast a message to all peers on the mesh network. Returns the number of peers the message was sent to.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message content to broadcast to all peers."
            },
            "message_type": {
                "type": "string",
                "description": "Type of message (e.g., 'announcement', 'query', 'alert').",
                "default": "announcement"
            }
        },
        "required": ["message"]
    }
}


def mesh_broadcast(message: str, message_type: str = "announcement") -> Dict[str, Any]:
    """Broadcast a message to all mesh peers.

    Args:
        message: Message content.
        message_type: Type classification.

    Returns:
        Dict with keys: success, recipients (number of peers messaged), failed
    """
    logger.info(f"Mesh broadcast (type={message_type}, {len(message)} chars)")

    peers = _load_peers()
    broadcast_id = f"bcast_{int(time.time())}_{hash(message) % 10000}"
    timestamp = datetime.utcnow().isoformat()

    # Try active broadcast via mesh module
    try:
        from mesh.unified_mesh import get_mesh_coordinator
        coordinator = get_mesh_coordinator()
        if coordinator and hasattr(coordinator, 'broadcast'):
            result = coordinator.broadcast(
                message=message,
                message_type=message_type,
            )
            if result.get("success"):
                recipients = result.get("recipients", len(peers))
                logger.info(f"Broadcast sent to {recipients} peers via mesh module")
                return _safe_result(
                    success=True,
                    data={
                        "broadcast_id": broadcast_id,
                        "recipients": recipients,
                        "failed": 0,
                        "timestamp": timestamp,
                        "method": "mesh",
                    }
                )
    except ImportError:
        logger.debug("mesh.unified_mesh not available")
    except Exception as e:
        logger.warning(f"Mesh broadcast failed via coordinator: {e}")

    # Fallback: queue messages for each peer
    successful = 0
    failed = 0

    for peer in peers:
        node_id = peer.get("node_id", peer.get("id"))
        if not node_id:
            continue
        try:
            result = mesh_send(node_id, message, message_type)
            if result.get("success"):
                successful += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    logger.info(f"Broadcast queued: {successful} sent, {failed} failed")
    return _safe_result(
        success=True,
        data={
            "broadcast_id": broadcast_id,
            "recipients": successful,
            "failed": failed,
            "timestamp": timestamp,
            "method": "queued",
            "note": "Messages queued for delivery. Offline peers will receive on reconnect.",
        }
    )
