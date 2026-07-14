
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Schedule Agent
========================
Basic calendar and meeting scheduling support for MVP.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger("ScheduleAgent")


@dataclass
class CalendarEvent:
    title: str
    start: datetime
    duration_minutes: int
    description: str = ""

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_minutes)

    def overlaps(self, other: "CalendarEvent") -> bool:
        return self.start < other.end and other.start < self.end

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_minutes": self.duration_minutes,
            "description": self.description,
        }


class ScheduleAgent:
    """Basic schedule/calendar agent for MVP."""

    def __init__(self) -> None:
        self.events: List[CalendarEvent] = []

    def add_event(self, title: str, start: datetime, duration_minutes: int = 30, description: str = "") -> bool:
        new_event = CalendarEvent(title=title, start=start, duration_minutes=duration_minutes, description=description)
        if self.has_conflict(new_event):
            logger.warning(f"Schedule conflict detected for event: {title}")
            return False
        self.events.append(new_event)
        logger.info(f"Added event: {title} at {start.isoformat()}")
        return True

    def has_conflict(self, new_event: CalendarEvent) -> bool:
        return any(existing.overlaps(new_event) for existing in self.events)

    def get_schedule(self, start: datetime = None, end: datetime = None) -> List[Dict[str, Any]]:
        filtered = self.events
        if start:
            filtered = [event for event in filtered if event.end >= start]
        if end:
            filtered = [event for event in filtered if event.start <= end]
        return [event.to_dict() for event in sorted(filtered, key=lambda e: e.start)]

    def find_conflicts(self) -> List[Dict[str, Any]]:
        conflicts: List[Dict[str, Any]] = []
        for i, event in enumerate(self.events):
            for other in self.events[i + 1:]:
                if event.overlaps(other):
                    conflicts.append({"event": event.title, "conflict_with": other.title})
        return conflicts


schedule_agent: ScheduleAgent = ScheduleAgent()


def initialize_schedule_agent() -> bool:
    global schedule_agent
    if schedule_agent is None:
        schedule_agent = ScheduleAgent()
    return True
