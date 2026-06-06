#!/usr/bin/env python3
"""
ASIMNEXUS Observability Middleware Integration Tests
=====================================================
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.middleware import ObservabilityMiddleware
from core.observability import get_collector
from core.audit_bus import fetch_audit


def test_middleware_request_latency_and_headers():
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/test-endpoint")
    def read_test():
        return {"status": "ok"}

    client = TestClient(app)
    collector = get_collector()
    collector.events_buffer.clear()

    resp = client.get("/test-endpoint")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert "X-Trace-ID" in resp.headers

    # Verify collector received request event
    events = collector.get_telemetry()
    assert len(events) >= 1
    req_event = [e for e in events if e.get("action") == "request"][0]
    assert req_event["status"] == "ok"
    assert req_event["latency_ms"] > 0
    assert req_event["request_id"] == resp.headers["X-Request-ID"]


def test_middleware_error_path_logging():
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/error-endpoint")
    def error_path():
        raise RuntimeError("Something went wrong inside")

    client = TestClient(app)
    collector = get_collector()
    collector.events_buffer.clear()

    with pytest.raises(RuntimeError):
        client.get("/error-endpoint")

    events = collector.get_telemetry()
    err_events = [e for e in events if e.get("action") == "error"]
    assert len(err_events) >= 1
    assert "RuntimeError" in err_events[0]["message"]
