
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS MVP smoke tests
=========================
Basic validations for MVP components implemented by autopilot.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from core.context_router import initialize_context_router, get_context_router
from core.event_bus import ASIMEventBus, EventType, AllocationPriority
from agents.economy_agent import economy_agent, initialize_economy_agent
from agents.health_agent import health_agent, initialize_health_agent
from agents.schedule_agent import schedule_agent, initialize_schedule_agent
from ui.asim_unified_server import app


def _sort_event_order(events):
    return [e[0].__name__ if hasattr(e[0], '__name__') else str(e[0]) for e in events]


class TestMVP(unittest.TestCase):
    def test_context_router_switch_and_route(self):
        initialize_context_router()
        router = get_context_router()

        self.assertEqual(router.get_mode()["mode"], "EMPIRE")
        self.assertTrue(router.set_mode("GUARDIAN"))
        self.assertEqual(router.get_mode()["mode"], "GUARDIAN")
        self.assertFalse(router.is_agent_allowed("economy_agent"))

        with self.assertRaises(PermissionError):
            router.route_request("economy_agent", "Review budget")

        self.assertTrue(router.set_mode("EMPIRE"))
        route = router.route_request("economy_agent", "Review budget")
        self.assertTrue(route["allowed"])
        self.assertEqual(route["agent"], "economy_agent")

    def test_event_bus_priority_order(self):
        bus = ASIMEventBus()
        bus.is_active = True
        received = []

        async def capture(event):
            received.append(("async", event.data.get("order")))

        def capture_sync(event):
            received.append(("sync", event.data.get("order")))

        bus.subscribe(EventType.SYSTEM_ALERT, capture, priority=AllocationPriority.LOW)
        bus.subscribe(EventType.SYSTEM_ALERT, capture_sync, priority=AllocationPriority.HIGH)
        bus.subscribe(EventType.SYSTEM_ALERT, capture, priority=AllocationPriority.NORMAL)

        import asyncio
        event = type("E", (), {"event_type": EventType.SYSTEM_ALERT, "data": {"order": 1}, "event_id": "test"})()
        asyncio.run(bus.publish(event))

        self.assertGreaterEqual(len(received), 2)
        self.assertEqual(received[0][0], "sync")

    def test_economy_agent_basic_tracking(self):
        initialize_economy_agent()
        economy_agent.transactions.clear()
        economy_agent.add_income(200.0, category="salary")
        economy_agent.add_expense(50.0, category="food")
        summary = economy_agent.get_budget_summary()
        self.assertEqual(summary["balance"], 150.0)
        self.assertEqual(summary["total_income"], 200.0)
        self.assertEqual(summary["total_expense"], 50.0)

    def test_health_agent_tracking(self):
        initialize_health_agent()
        health_agent.checkins.clear()
        health_agent.reminders.clear()
        health_agent.record_checkin("blood_pressure", "120/80", note="Morning check")
        now = datetime.utcnow()
        self.assertTrue(health_agent.schedule_medication("Vitamin D", "1000 IU", now, note="daily"))
        summary = health_agent.get_status_summary()
        self.assertEqual(summary["total_checkins"], 1)
        self.assertEqual(summary["total_reminders"], 1)
        reminders = health_agent.get_reminders()
        self.assertEqual(reminders[0]["medication"], "Vitamin D")

    def test_permission_matrix_tool_restriction(self):
        initialize_context_router()
        router = get_context_router()
        self.assertTrue(router.set_mode("GUARDIAN"))
        with self.assertRaises(PermissionError):
            router.route_request("health_agent", "Access code editor", metadata={"tool": "code_edit"})
        request = router.route_request("health_agent", "Check health status", metadata={"tool": "health_data"})
        self.assertTrue(request["allowed"])
        self.assertEqual(request["agent"], "health_agent")

    def test_schedule_agent_conflict(self):
        initialize_schedule_agent()
        schedule_agent.events.clear()
        first_start = datetime.utcnow()
        second_start = first_start + timedelta(minutes=15)

        self.assertTrue(schedule_agent.add_event("Standup", first_start, duration_minutes=30))
        self.assertFalse(schedule_agent.add_event("Interview", second_start, duration_minutes=20))
        conflicts = schedule_agent.find_conflicts()
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(len(schedule_agent.get_schedule()), 1)

    def test_unified_server_app(self):
        self.assertEqual(app.title, "ASIMNEXUS Unified Server")
        self.assertTrue(hasattr(app, "routes"))


if __name__ == "__main__":
    unittest.main()
