
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Health Agent
======================
Minimal health tracking and reminder support for MVP.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger("HealthAgent")


@dataclass
class HealthCheck:
    metric: str
    value: Any
    note: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "note": self.note,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HealthReminder:
    medication: str
    dose: str
    reminder_time: datetime
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication": self.medication,
            "dose": self.dose,
            "reminder_time": self.reminder_time.isoformat(),
            "note": self.note,
        }


class HealthAgent:
    """Basic health agent for MVP."""

    def __init__(self) -> None:
        self.checkins: List[HealthCheck] = []
        self.reminders: List[HealthReminder] = []

    def record_checkin(self, metric: str, value: Any, note: str = "") -> None:
        self.checkins.append(HealthCheck(metric=metric, value=value, note=note))
        logger.info(f"Recorded health checkin: {metric}={value}")

    def schedule_medication(self, medication: str, dose: str, reminder_time: datetime, note: str = "") -> bool:
        reminder = HealthReminder(medication=medication, dose=dose, reminder_time=reminder_time, note=note)
        if any(existing.medication == reminder.medication and existing.reminder_time == reminder.reminder_time for existing in self.reminders):
            logger.warning(f"Duplicate medication reminder ignored: {medication} at {reminder_time}")
            return False
        self.reminders.append(reminder)
        logger.info(f"Scheduled medication reminder: {medication} at {reminder_time.isoformat()}")
        return True

    def get_status_summary(self) -> Dict[str, Any]:
        last_checkin = self.checkins[-1] if self.checkins else None
        return {
            "total_checkins": len(self.checkins),
            "total_reminders": len(self.reminders),
            "last_checkin": last_checkin.to_dict() if last_checkin else None,
        }

    def get_reminders(self) -> List[Dict[str, Any]]:
        return [reminder.to_dict() for reminder in sorted(self.reminders, key=lambda r: r.reminder_time)]


health_agent: HealthAgent = HealthAgent()


def initialize_health_agent() -> bool:
    global health_agent
    if health_agent is None:
        health_agent = HealthAgent()
    return True
