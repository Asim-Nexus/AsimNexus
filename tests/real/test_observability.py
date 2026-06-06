#!/usr/bin/env python3
"""
ASIMNEXUS Observability Collector Unit Tests
============================================
"""

import pytest
from core.observability import ObservabilityCollector
from core.telemetry_schema import validate_event


def test_validate_valid_envelope():
    raw = {
        "component": "backend",
        "action": "request",
        "severity": "info",
        "status": "ok",
        "message": "Valid request"
    }
    validated = validate_event(raw)
    assert validated["event_id"] is not None
    assert validated["timestamp"] is not None


def test_validate_invalid_envelope():
    raw = {
        "component": "invalid_component",
        "action": "request"
    }
    with pytest.raises(ValueError, match="Invalid component"):
        validate_event(raw)


def test_collector_records_request():
    collector = ObservabilityCollector()
    context = {
        "trace_id": "trace-123",
        "span_id": "span-123",
        "user_id": "user-456",
        "device_id": "device-789",
        "session_id": "sess-abc",
        "privacy_level": "public",
        "mode": "personal"
    }
    event = collector.record_request(
        request_id="req-123",
        path="/api/test",
        method="GET",
        status_code=200,
        latency_ms=10.5,
        context=context
    )
    
    assert event["request_id"] == "req-123"
    assert event["component"] == "backend"
    assert event["action"] == "request"
    assert event["latency_ms"] == 10.5
    assert len(collector.get_telemetry()) == 1


def test_collector_records_policy_decision():
    collector = ObservabilityCollector()
    context = {"request_id": "req-123", "mode": "company"}
    
    # Check deny deduction
    assert collector.policy_score == 1.0
    collector.record_decision(action="write_file", decision="deny", reason="Unauthorized path", context=context)
    assert collector.policy_score < 1.0
    
    telemetry = collector.get_telemetry()
    assert len(telemetry) == 1
    assert telemetry[0]["component"] == "policy"
    assert telemetry[0]["policy"]["decision"] == "deny"
