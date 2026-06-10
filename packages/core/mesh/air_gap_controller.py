#!/usr/bin/env python3
"""
core/mesh/air_gap_controller.py
AsimNexus — Air Gap Controller with 5-level state machine.

Provides:
  - AirGapLevel enum (NORMAL=0 → REDUCED=1 → LAN_ONLY=2 → ISOLATED=3 → EMERGENCY=4)
  - AirGapEvent dataclass for audit trail entries
  - AirGapController: engage/disengage/escalate, traffic rules, network blocking,
    connection counting, audit logging
  - Singleton factory: get_air_gap() / reset_air_gap()
  - LEVEL_LABELS dict and LEVEL_RULES dict
"""

import os
import time
import json
import subprocess
import logging
from enum import IntEnum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


# ── AirGapLevel Enum ──────────────────────────────────────────────────────────

class AirGapLevel(IntEnum):
    """Five air-gap levels with increasing restriction."""
    NORMAL = 0
    REDUCED = 1
    LAN_ONLY = 2
    ISOLATED = 3
    EMERGENCY = 4


# ── Level Labels ──────────────────────────────────────────────────────────────

LEVEL_LABELS: Dict[AirGapLevel, str] = {
    AirGapLevel.NORMAL: "🟢 Normal",
    AirGapLevel.REDUCED: "🟡 Reduced",
    AirGapLevel.LAN_ONLY: "🟠 LAN Only",
    AirGapLevel.ISOLATED: "🔴 Isolated",
    AirGapLevel.EMERGENCY: "⛔ Emergency",
}


# ── Level Rules ───────────────────────────────────────────────────────────────

LEVEL_RULES: Dict[AirGapLevel, Dict[str, bool]] = {
    AirGapLevel.NORMAL: {
        "cloud": True,
        "lan": True,
        "loopback": True,
        "outbound": True,
    },
    AirGapLevel.REDUCED: {
        "cloud": False,
        "lan": True,
        "loopback": True,
        "outbound": True,
    },
    AirGapLevel.LAN_ONLY: {
        "cloud": False,
        "lan": True,
        "loopback": True,
        "outbound": False,
    },
    AirGapLevel.ISOLATED: {
        "cloud": False,
        "lan": False,
        "loopback": True,
        "outbound": False,
    },
    AirGapLevel.EMERGENCY: {
        "cloud": False,
        "lan": False,
        "loopback": False,
        "outbound": False,
    },
}


# ── AirGapEvent Dataclass ─────────────────────────────────────────────────────

@dataclass
class AirGapEvent:
    """An audit-log entry for air-gap state transitions."""
    timestamp: float
    event_type: str  # "engage" | "disengage" | "escalate"
    level_from: int
    level_to: int
    reason: str
    triggered_by: str  # "human" | "auto_dharma" | "system"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── AirGapController ──────────────────────────────────────────────────────────

class AirGapController:
    """
    Five-level air-gap state machine with traffic rule enforcement,
    network blocking, connection counting, and audit logging.

    Levels: NORMAL (0) → REDUCED (1) → LAN_ONLY (2) → ISOLATED (3) → EMERGENCY (4)
    """

    def __init__(self):
        self._level: AirGapLevel = AirGapLevel.NORMAL
        self._engaged: bool = False
        self._engaged_at: Optional[float] = None
        self._history: List[AirGapEvent] = []
        self._blocked_rules: Dict[str, Dict[str, Any]] = {}
        self._firewall_available: Optional[bool] = None

    # ── Public API ─────────────────────────────────────────────────────────

    def engage(self, level: AirGapLevel, reason: str = "",
               triggered_by: str = "human") -> Dict[str, Any]:
        """
        Engage air-gap at the specified level.
        If already at a higher level, this is a no-op (no downgrade).
        """
        if level < self._level:
            # Cannot downgrade via engage
            return {
                "status": "noop",
                "level": int(self._level),
                "detail": f"Already at higher level ({self._level.name})",
            }

        self._level = level
        self._engaged = True
        if self._engaged_at is None:
            self._engaged_at = time.time()

        event = AirGapEvent(
            timestamp=time.time(),
            event_type="engage",
            level_from=int(self._level),
            level_to=int(level),
            reason=reason,
            triggered_by=triggered_by,
        )
        self._history.append(event)

        # Apply network rules
        self._apply_rules(level)

        return {
            "status": "engaged",
            "level": int(level),
            "detail": f"Air-gap engaged at {level.name}",
        }

    def disengage(self, triggered_by: str = "human") -> Dict[str, Any]:
        """Disengage air-gap and return to NORMAL. Only humans can disengage."""
        if triggered_by != "human":
            return {
                "status": "refused",
                "level": int(self._level),
                "detail": "Air-gap can only be disengaged by human",
            }

        event = AirGapEvent(
            timestamp=time.time(),
            event_type="disengage",
            level_from=int(self._level),
            level_to=0,
            reason="Manual disengage",
            triggered_by=triggered_by,
        )
        self._history.append(event)

        self._level = AirGapLevel.NORMAL
        self._engaged = False
        self._engaged_at = None

        return {
            "status": "normal",
            "level": 0,
            "detail": "Air-gap disengaged, returned to NORMAL",
        }

    def escalate(self, reason: str = "Auto-escalation",
                 triggered_by: str = "auto_dharma") -> Dict[str, Any]:
        """Step up one level. Cannot escalate past EMERGENCY."""
        if self._level >= AirGapLevel.EMERGENCY:
            return {
                "status": "noop",
                "level": int(self._level),
                "detail": "Already at maximum level (EMERGENCY)",
            }

        next_level = AirGapLevel(self._level + 1)
        self._level = next_level
        self._engaged = True
        if self._engaged_at is None:
            self._engaged_at = time.time()

        event = AirGapEvent(
            timestamp=time.time(),
            event_type="escalate",
            level_from=int(self._level) - 1,
            level_to=int(next_level),
            reason=reason,
            triggered_by=triggered_by,
        )
        self._history.append(event)

        self._apply_rules(next_level)

        return {
            "status": "engaged",
            "level": int(next_level),
            "detail": f"Escalated to {next_level.name}",
        }

    # ── Traffic Rules ──────────────────────────────────────────────────────

    def is_allowed(self, traffic_type: str) -> bool:
        """Check if a traffic type is allowed at the current level."""
        rules = LEVEL_RULES.get(self._level, {})
        return rules.get(traffic_type, False)

    def check_request(self, ip: str, port: int) -> Dict[str, Any]:
        """Check if a specific request is allowed."""
        # Loopback is always allowed at ISOLATED, blocked at EMERGENCY
        if ip.startswith("127.") or ip == "::1" or ip == "localhost":
            if self._level == AirGapLevel.EMERGENCY:
                return {"allowed": False, "reason": "Blocked — EMERGENCY level"}
            if self._level <= AirGapLevel.ISOLATED:
                return {"allowed": True, "reason": "Loopback allowed"}
            return {"allowed": True, "reason": "Loopback allowed"}

        # Cloud check
        if not self.is_allowed("cloud"):
            return {"allowed": False, "reason": "Blocked — Cloud traffic restricted"}

        # LAN check
        if not self.is_allowed("lan"):
            return {"allowed": False, "reason": "Blocked — LAN traffic restricted"}

        return {"allowed": True, "reason": "Allowed"}

    # ── Network Blocking ───────────────────────────────────────────────────

    def _block_network(self, ip: str, port: int) -> Tuple[bool, str]:
        """Block a specific IP:port. Uses simulated fallback."""
        key = f"{ip}:{port}"
        if key in self._blocked_rules:
            return True, f"Already blocked: {key}"

        self._blocked_rules[key] = {
            "ip": ip,
            "port": port,
            "blocked_at": time.time(),
        }
        return True, f"Simulated block: {key}"

    def _unblock_network(self, ip: str, port: int) -> Tuple[bool, str]:
        """Remove a block for a specific IP:port."""
        key = f"{ip}:{port}"
        if key not in self._blocked_rules:
            return False, f"Not blocked: {key}"

        del self._blocked_rules[key]
        return True, f"Block removed: {key}"

    def is_network_blocked(self, ip: Optional[str] = None,
                           port: Optional[int] = None) -> bool:
        """Check if a specific IP:port is blocked, or if any blocks exist."""
        if ip is not None and port is not None:
            key = f"{ip}:{port}"
            return key in self._blocked_rules
        return len(self._blocked_rules) > 0

    def get_blocked_rules(self) -> Dict[str, Dict[str, Any]]:
        """Return all active blocked rules."""
        return dict(self._blocked_rules)

    # ── Connection Counting ────────────────────────────────────────────────

    def get_connection_count(self) -> int:
        """Count ESTABLISHED connections via netstat."""
        try:
            result = subprocess.run(
                ["netstat", "-n"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return -1

            count = 0
            for line in result.stdout.splitlines():
                if "ESTABLISHED" in line:
                    count += 1
            return count
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return -1

    # ── Audit Logging ─────────────────────────────────────────────────────

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Return the full audit trail of state transitions."""
        return [e.to_dict() for e in self._history]

    def history(self) -> List[Dict[str, Any]]:
        """Alias for get_audit_trail()."""
        return self.get_audit_trail()

    # ── Status ─────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return current status snapshot."""
        engaged_for = 0.0
        if self._engaged and self._engaged_at is not None:
            engaged_for = time.time() - self._engaged_at

        return {
            "level": int(self._level),
            "label": LEVEL_LABELS.get(self._level, "Unknown"),
            "engaged": self._engaged,
            "engaged_for_s": round(engaged_for, 1),
            "blocked_rules": len(self._blocked_rules),
            "active_connections": self.get_connection_count(),
            "firewall_available": self._check_firewall_available(),
        }

    # ── Internal Helpers ───────────────────────────────────────────────────

    def _apply_rules(self, level: AirGapLevel) -> None:
        """Apply network rules for the given level (simulated)."""
        rules = LEVEL_RULES.get(level, {})
        logger.debug(f"Applied rules for {level.name}: {rules}")

    def _check_firewall_available(self) -> bool:
        """Check if real firewall commands are available."""
        if self._firewall_available is not None:
            return self._firewall_available

        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles"],
                    capture_output=True, text=True, timeout=3,
                )
                self._firewall_available = result.returncode == 0
            else:
                result = subprocess.run(
                    ["iptables", "-L", "-n"],
                    capture_output=True, text=True, timeout=3,
                )
                self._firewall_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._firewall_available = False

        return self._firewall_available


# ── Singleton Factory ─────────────────────────────────────────────────────────

_air_gap_instance: Optional[AirGapController] = None


def get_air_gap() -> AirGapController:
    """Return the singleton AirGapController instance."""
    global _air_gap_instance
    if _air_gap_instance is None:
        _air_gap_instance = AirGapController()
    return _air_gap_instance


def reset_air_gap() -> None:
    """Reset the singleton (for testing)."""
    global _air_gap_instance
    _air_gap_instance = None
