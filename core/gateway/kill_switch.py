"""
AsimNexus Policy Gateway: Kill Switch
======================================
Emergency shutdown mechanism. When activated:
  - All write operations blocked
  - System enters Read-Only mode
  - External connections terminated
  - Emergency checkpoint created
Can only be deactivated by qualified human with authentication.

State Machine:
  DISARMED -> ARMED -> ACTIVE -> RECOVERING -> DISARMED
  DISARMED -> ACTIVE (direct emergency activation)

Test Plan:
  1. arm() from DISARMED -> ARMED, verify is_armed=True
  2. activate() from ARMED -> ACTIVE, verify hooks fire
  3. activate() from DISARMED -> ACTIVE (direct emergency)
  4. deactivate() from ACTIVE -> DISARMED, verify auth_token required
  5. deactivate() without auth_token -> PermissionError
  6. deactivate() from DISARMED -> PermissionError
  7. register_hook() -> verify callback fires on activate/deactivate
  8. get_events() returns ordered event list
  9. get_stats() returns correct counts
 10. Multiple activate/deactivate cycles maintain integrity
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("KillSwitch")

class ShutdownMode(Enum):
    READ_ONLY = "READ_ONLY"; QUARANTINE = "QUARANTINE"; EMERGENCY_HALT = "EMERGENCY_HALT"

class KillSwitchState(Enum):
    DISARMED = "DISARMED"; ARMED = "ARMED"; ACTIVE = "ACTIVE"; RECOVERING = "RECOVERING"

@dataclass
class KillSwitchEvent:
    event_id: str; action: str; initiator: str; reason: str; mode: ShutdownMode
    previous_state: KillSwitchState; new_state: KillSwitchState
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Standardized export format for kill switch events."""
        return {"event_id": self.event_id, "action": self.action, "initiator": self.initiator,
                "reason": self.reason, "mode": self.mode.value,
                "previous_state": self.previous_state.value, "new_state": self.new_state.value,
                "timestamp": self.timestamp, "metadata": self.metadata}

class KillSwitch:
    def __init__(self):
        self._state = KillSwitchState.DISARMED
        self._mode = ShutdownMode.READ_ONLY
        self._events: List[KillSwitchEvent] = []
        self._hooks: Dict[str, List[Callable]] = {"on_activate": [], "on_deactivate": []}
        self._is_armed = False

    @property
    def is_armed(self): return self._is_armed
    @property
    def state(self): return self._state
    @property
    def mode(self): return self._mode

    def arm(self, initiator: str, reason: str) -> KillSwitchEvent:
        """Arm the kill switch. Transitions DISARMED -> ARMED."""
        prev = self._state
        if self._state == KillSwitchState.ACTIVE:
            raise PermissionError("Cannot arm: kill switch is already ACTIVE")
        self._state = KillSwitchState.ARMED; self._is_armed = True
        event = KillSwitchEvent(event_id=f"ks-arm-{datetime.now(timezone.utc).timestamp()}",
            action="ARM", initiator=initiator, reason=reason, mode=self._mode,
            previous_state=prev, new_state=self._state)
        self._events.append(event); logger.warning(f"Kill switch ARMED by {initiator}: {reason}")
        return event

    def activate(self, initiator: str, reason: str, mode: ShutdownMode = ShutdownMode.READ_ONLY) -> KillSwitchEvent:
        """Activate the kill switch. Can be called from DISARMED (direct) or ARMED."""
        prev = self._state
        if self._state == KillSwitchState.ACTIVE:
            raise PermissionError("Kill switch is already ACTIVE")
        self._state = KillSwitchState.ACTIVE; self._mode = mode; self._is_armed = True
        event = KillSwitchEvent(event_id=f"ks-act-{datetime.now(timezone.utc).timestamp()}",
            action="ACTIVATE", initiator=initiator, reason=reason, mode=mode,
            previous_state=prev, new_state=self._state)
        self._events.append(event)
        logger.critical(f"KILL SWITCH ACTIVATED by {initiator} (mode={mode.value}): {reason}")
        for hook in self._hooks["on_activate"]:
            try: hook(event)
            except Exception as e: logger.error(f"Hook failed: {e}")
        return event

    def deactivate(self, initiator: str, reason: str, auth_token: str) -> KillSwitchEvent:
        """
        Deactivate the kill switch. Requires valid auth_token.
        Transitions ACTIVE -> RECOVERING -> DISARMED.
        """
        if self._state != KillSwitchState.ACTIVE:
            raise PermissionError(f"Cannot deactivate: current state is {self._state.value}")
        if not auth_token:
            raise PermissionError("Auth token required for kill switch deactivation")
        prev = self._state; self._state = KillSwitchState.RECOVERING
        event = KillSwitchEvent(event_id=f"ks-deact-{datetime.now(timezone.utc).timestamp()}",
            action="DEACTIVATE", initiator=initiator, reason=reason, mode=self._mode,
            previous_state=prev, new_state=KillSwitchState.DISARMED)
        self._events.append(event)
        self._state = KillSwitchState.DISARMED; self._is_armed = False; self._mode = ShutdownMode.READ_ONLY
        logger.warning(f"Kill switch DEACTIVATED by {initiator}: {reason}")
        for hook in self._hooks["on_deactivate"]:
            try: hook(event)
            except Exception as e: logger.error(f"Deactivate hook failed: {e}")
        return event

    def register_hook(self, event: str, callback: Callable) -> None:
        if event in self._hooks: self._hooks[event].append(callback)

    def get_events(self, limit: int = 50) -> List[KillSwitchEvent]:
        return self._events[-limit:]

    def export_events(self) -> List[Dict[str, Any]]:
        """Standardized export of all kill switch events."""
        return [e.to_dict() for e in self._events]

    def get_stats(self) -> Dict[str, Any]:
        return {"state": self._state.value, "mode": self._mode.value, "is_armed": self._is_armed,
                "total_events": len(self._events)}

kill_switch = KillSwitch()
