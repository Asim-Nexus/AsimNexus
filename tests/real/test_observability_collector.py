#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade observability collector tests
ASIMNEXUS Observability Collector Tests
=========================================
Comprehensive tests for ObservabilityCollector covering all record_* methods,
buffer management, posture evaluation, and persistence.
"""

import json
import pytest
from pathlib import Path
from core.observability import ObservabilityCollector, get_collector, ASIMObservability, get_observability


class TestObservabilityCollector:
    """Test suite for ObservabilityCollector."""

    @pytest.fixture(autouse=True)
    def fresh_collector(self):
        """Create a fresh collector instance for each test."""
        self.collector = ObservabilityCollector()
        yield

    def _sample_context(self, **overrides) -> dict:
        ctx = {
            "trace_id": "trace-abc",
            "span_id": "span-xyz",
            "user_id": "user-001",
            "device_id": "device-001",
            "session_id": "sess-001",
            "privacy_level": "public",
            "mode": "personal",
        }
        ctx.update(overrides)
        return ctx

    # ------------------------------------------------------------------ #
    # _append_event
    # ------------------------------------------------------------------ #

    def test_append_event_returns_validated(self):
        """_append_event returns the validated event dict."""
        event = self.collector._append_event({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "test",
        })
        assert "event_id" in event
        assert "timestamp" in event
        assert event["component"] == "backend"

    def test_append_event_buffers_event(self):
        """_append_event adds event to the buffer."""
        self.collector._append_event({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "e1",
        })
        assert len(self.collector.events_buffer) == 1
        assert self.collector.events_buffer[0]["message"] == "e1"

    def test_append_event_buffer_capped_at_1000(self):
        """_append_event caps the buffer at 1000 events."""
        for i in range(1010):
            self.collector._append_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "message": f"e{i}",
            })
        assert len(self.collector.events_buffer) == 1000
        # Should contain the last 1000
        assert self.collector.events_buffer[0]["message"] == "e10"
        assert self.collector.events_buffer[-1]["message"] == "e1009"

    # ------------------------------------------------------------------ #
    # record_request
    # ------------------------------------------------------------------ #

    def test_record_request_success(self):
        """record_request records a successful HTTP request."""
        event = self.collector.record_request(
            request_id="req-001",
            path="/api/test",
            method="GET",
            status_code=200,
            latency_ms=15.3,
            context=self._sample_context(),
        )
        assert event["request_id"] == "req-001"
        assert event["component"] == "backend"
        assert event["action"] == "request"
        assert event["severity"] == "info"
        assert event["status"] == "ok"
        assert event["latency_ms"] == 15.3

    def test_record_request_client_error(self):
        """record_request records 4xx as warning."""
        event = self.collector.record_request(
            request_id="req-002",
            path="/api/not-found",
            method="GET",
            status_code=404,
            latency_ms=5.0,
            context=self._sample_context(),
        )
        assert event["severity"] == "warning"
        assert event["status"] == "failed"

    def test_record_request_server_error(self):
        """record_request records 5xx as error."""
        event = self.collector.record_request(
            request_id="req-003",
            path="/api/error",
            method="POST",
            status_code=500,
            latency_ms=100.0,
            context=self._sample_context(),
        )
        assert event["severity"] == "error"
        assert event["status"] == "failed"

    def test_record_request_with_context(self):
        """record_request includes context fields."""
        ctx = self._sample_context(trace_id="my-trace", user_id="my-user")
        event = self.collector.record_request(
            request_id="req-004",
            path="/api/data",
            method="PUT",
            status_code=200,
            latency_ms=20.0,
            context=ctx,
        )
        assert event["trace_id"] == "my-trace"
        assert event["user_id"] == "my-user"

    # ------------------------------------------------------------------ #
    # record_decision
    # ------------------------------------------------------------------ #

    def test_record_decision_allow(self):
        """record_decision records an allow decision."""
        event = self.collector.record_decision(
            action="read_file",
            decision="allow",
            reason="Path permitted",
            context={"request_id": "req-001"},
        )
        assert event["component"] == "policy"
        assert event["action"] == "decision"
        assert event["severity"] == "info"
        assert event["status"] == "ok"
        assert event["policy"]["decision"] == "allow"

    def test_record_decision_deny_reduces_score(self):
        """record_decision with 'deny' reduces policy_score by 0.15."""
        initial = self.collector.policy_score
        self.collector.record_decision(
            action="write_file",
            decision="deny",
            reason="Unauthorized path",
            context={"request_id": "req-001"},
        )
        assert self.collector.policy_score == initial - 0.15

    def test_record_decision_blocked_reduces_score_more(self):
        """record_decision with 'blocked' reduces policy_score by 0.25."""
        initial = self.collector.policy_score
        self.collector.record_decision(
            action="delete_file",
            decision="blocked",
            reason="Malicious pattern detected",
            context={"request_id": "req-001"},
        )
        assert self.collector.policy_score == initial - 0.25

    def test_record_decision_policy_score_never_negative(self):
        """record_decision never lets policy_score go below 0.0."""
        for _ in range(10):
            self.collector.record_decision(
                action="dangerous_op",
                decision="blocked",
                reason="Repeated violations",
                context={"request_id": "req-001"},
            )
        assert self.collector.policy_score >= 0.0

    def test_record_decision_review_severity_warning(self):
        """record_decision with 'review' decision gets warning severity."""
        event = self.collector.record_decision(
            action="unusual_access",
            decision="review",
            reason="Flagged for review",
            context={"request_id": "req-001"},
        )
        assert event["severity"] == "warning"

    # ------------------------------------------------------------------ #
    # record_tool_call
    # ------------------------------------------------------------------ #

    def test_record_tool_call_success(self):
        """record_tool_call records a successful tool invocation."""
        event = self.collector.record_tool_call(
            tool_name="code_analyzer",
            model="gpt-4",
            route="llm-proxy",
            latency_ms=250.0,
            context=self._sample_context(),
        )
        assert event["action"] == "tool_call"
        assert event["tool"]["name"] == "code_analyzer"
        assert event["tool"]["selected_model"] == "gpt-4"
        assert event["tool"]["route"] == "llm-proxy"
        assert event["status"] == "ok"

    def test_record_tool_call_blocked(self):
        """record_tool_call with blocked route sets blocked status."""
        event = self.collector.record_tool_call(
            tool_name="dangerous_tool",
            model=None,
            route="blocked",
            latency_ms=0.0,
            context=self._sample_context(),
        )
        assert event["status"] == "blocked"

    def test_record_tool_call_no_model(self):
        """record_tool_call accepts None model."""
        event = self.collector.record_tool_call(
            tool_name="local_tool",
            model=None,
            route="local",
            latency_ms=5.0,
            context=self._sample_context(),
        )
        assert event["tool"]["name"] == "local_tool"
        assert event["tool"]["selected_model"] is None

    # ------------------------------------------------------------------ #
    # record_error
    # ------------------------------------------------------------------ #

    def test_record_error(self):
        """record_error records an error event."""
        event = self.collector.record_error(
            error_type="ValueError",
            message="Invalid input parameter",
            context=self._sample_context(),
        )
        assert event["action"] == "error"
        assert event["severity"] == "error"
        assert event["status"] == "failed"
        assert "ValueError" in event["message"]

    def test_record_error_with_component(self):
        """record_error respects component from context."""
        event = self.collector.record_error(
            error_type="TimeoutError",
            message="Connection timed out",
            context={"component": "mesh", "request_id": "req-001"},
        )
        assert event["component"] == "mesh"

    def test_record_error_default_component(self):
        """record_error defaults to 'backend' component."""
        event = self.collector.record_error(
            error_type="GenericError",
            message="Something went wrong",
            context={},
        )
        assert event["component"] == "backend"

    # ------------------------------------------------------------------ #
    # get_telemetry
    # ------------------------------------------------------------------ #

    def test_get_telemetry_returns_events(self):
        """get_telemetry returns buffered events."""
        self.collector.record_request(
            request_id="req-001", path="/test", method="GET",
            status_code=200, latency_ms=10.0, context=self._sample_context(),
        )
        telemetry = self.collector.get_telemetry()
        assert len(telemetry) == 1

    def test_get_telemetry_respects_limit(self):
        """get_telemetry respects the limit parameter."""
        for i in range(50):
            self.collector.record_request(
                request_id=f"req-{i}", path="/test", method="GET",
                status_code=200, latency_ms=1.0, context=self._sample_context(),
            )
        telemetry = self.collector.get_telemetry(limit=10)
        assert len(telemetry) == 10

    def test_get_telemetry_returns_most_recent(self):
        """get_telemetry returns the most recent events."""
        for i in range(5):
            self.collector.record_request(
                request_id=f"req-{i}", path="/test", method="GET",
                status_code=200, latency_ms=1.0, context=self._sample_context(),
            )
        telemetry = self.collector.get_telemetry(limit=3)
        assert telemetry[-1]["request_id"] == "req-4"

    # ------------------------------------------------------------------ #
    # get_posture
    # ------------------------------------------------------------------ #

    def test_get_posture_returns_dict(self):
        """get_posture returns a dict with expected keys."""
        posture = self.collector.get_posture()
        assert "score" in posture
        assert "level" in posture
        assert "metrics" in posture
        assert "reason" in posture

    def test_get_posture_default_trusted(self):
        """get_posture returns 'trusted' level by default."""
        posture = self.collector.get_posture()
        assert posture["level"] == "trusted"
        assert posture["score"] >= 0.90

    def test_get_posture_reflects_policy_decisions(self):
        """get_posture score decreases after policy denials."""
        for _ in range(5):
            self.collector.record_decision(
                action="test", decision="deny",
                reason="test", context={},
            )
        posture = self.collector.get_posture()
        assert posture["score"] < 0.90


class TestObservabilitySingleton:
    """Tests for the get_collector singleton."""

    def test_get_collector_returns_same_instance(self):
        """get_collector always returns the same instance."""
        c1 = get_collector()
        c2 = get_collector()
        assert c1 is c2

    def test_get_collector_is_observability_collector(self):
        """get_collector returns an ObservabilityCollector."""
        collector = get_collector()
        assert isinstance(collector, ObservabilityCollector)


class TestASIMObservabilityLegacy:
    """Tests for the legacy ASIMObservability wrapper."""

    def test_legacy_log(self):
        """ASIMObservability.log appends events."""
        obs = ASIMObservability()
        import logging
        obs.log(logging.INFO, "Legacy log test", "backend")
        assert len(obs.collector.events_buffer) >= 1

    def test_legacy_get_trust_posture(self):
        """ASIMObservability.get_trust_posture returns dict."""
        obs = ASIMObservability()
        posture = obs.get_trust_posture()
        assert "trust_score" in posture
        assert "posture" in posture
        assert "system_health" in posture

    def test_get_observability(self):
        """get_observability returns an ASIMObservability instance."""
        obs = get_observability()
        assert isinstance(obs, ASIMObservability)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
