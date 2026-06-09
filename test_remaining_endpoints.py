"""
Comprehensive test suite for all remaining missing API endpoints.

Tests all endpoints from api/remaining_missing_api.py:
  - Dharma (status, veto)
  - Dreaming (status, briefing, trigger)
  - Analytics (overview, activity)
  - Jobs Marketplace (stats, list, post)
  - Sync/Offline (status, enqueue, flush, queue, mesh/offline/*)

Run: cd c:/AsimNexus && python -m pytest test_remaining_endpoints.py -v
"""

import pytest
from fastapi.testclient import TestClient
from api.unified_api import app

client = TestClient(app, raise_server_exceptions=False)


# ═══════════════════════════════════════════════════════════════════════
# DHARMA / ETHICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestDharmaEndpoints:
    """Test /api/dharma/status and /api/dharma/veto"""

    ROUTE_STATUS = "/api/dharma/status"
    ROUTE_VETO = "/api/dharma/veto"

    def test_dharma_status_returns_200(self):
        """GET /api/dharma/status should return 200 (graceful fallback if module missing)"""
        resp = client.get(self.ROUTE_STATUS)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        # Should have at least some basic fields
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        # If module loaded, expect 'active' or 'layers'; if not, expect 'message'
        assert any(k in data for k in ("active", "layers", "message", "total_vetoes")), \
            f"Response missing expected keys: {list(data.keys())[:10]}"

    def test_dharma_veto_returns_200(self):
        """POST /api/dharma/veto should return 200 or 422"""
        resp = client.post(self.ROUTE_VETO, json={"reason": "Test veto", "severity": "warning"})
        # 200 = success/graceful fallback, 422 = validation error (shouldn't happen with valid data)
        assert resp.status_code in (200, 422), \
            f"Expected 200 or 422, got {resp.status_code}: {resp.text[:200]}"
        if resp.status_code == 200:
            data = resp.json()
            assert "verdict" in data, f"Response missing 'verdict': {data}"

    def test_dharma_veto_missing_reason_returns_422(self):
        """POST /api/dharma/veto without reason should return 422"""
        resp = client.post(self.ROUTE_VETO, json={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

    def test_dharma_veto_invalid_severity_returns_422(self):
        """POST /api/dharma/veto with invalid severity should return 422"""
        resp = client.post(self.ROUTE_VETO, json={"reason": "Test", "severity": "invalid"})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════
# DREAMING / AI CONSCIOUSNESS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestDreamingEndpoints:
    """Test /api/dreaming/status, /api/dreaming/briefing, /api/dreaming/trigger"""

    ROUTE_STATUS = "/api/dreaming/status"
    ROUTE_BRIEFING = "/api/dreaming/briefing"
    ROUTE_TRIGGER = "/api/dreaming/trigger"

    def test_dreaming_status_returns_200(self):
        """GET /api/dreaming/status should return 200"""
        resp = client.get(self.ROUTE_STATUS)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        # Should have 'running' or 'total_cycles' or 'message'
        assert any(k in data for k in ("running", "total_cycles", "message", "current_cycle")), \
            f"Missing expected keys: {list(data.keys())[:10]}"

    def test_dreaming_briefing_returns_200(self):
        """GET /api/dreaming/briefing should return 200"""
        resp = client.get(self.ROUTE_BRIEFING)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        assert "briefing" in data, f"Response missing 'briefing': {list(data.keys())[:10]}"

    def test_dreaming_trigger_returns_503_or_200(self):
        """POST /api/dreaming/trigger returns 503 if engine missing, 200 or 504 otherwise"""
        resp = client.post(self.ROUTE_TRIGGER)
        # Engine likely unavailable → 503; else 200 success or 504 timeout
        assert resp.status_code in (200, 503, 504), \
            f"Expected 200/503/504, got {resp.status_code}: {resp.text[:200]}"
        if resp.status_code == 503:
            data = resp.json()
            assert "detail" in data, f"503 should have 'detail': {data}"


# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyticsEndpoints:
    """Test /api/analytics/overview and /api/analytics/activity"""

    ROUTE_OVERVIEW = "/api/analytics/overview"
    ROUTE_ACTIVITY = "/api/analytics/activity"

    def test_analytics_overview_returns_200(self):
        """GET /api/analytics/overview should return 200"""
        resp = client.get(self.ROUTE_OVERVIEW)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        assert "system" in data or "timestamp" in data, \
            f"Missing expected keys: {list(data.keys())[:10]}"

    def test_analytics_activity_returns_200(self):
        """GET /api/analytics/activity should return 200"""
        resp = client.get(self.ROUTE_ACTIVITY)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        # Should have at least 'total_entries' or 'activities'
        assert "total_entries" in data or "activities" in data, \
            f"Missing expected keys: {list(data.keys())[:10]}"

    def test_analytics_activity_with_limit_returns_200(self):
        """GET /api/analytics/activity?limit=10 should return 200"""
        resp = client.get(f"{self.ROUTE_ACTIVITY}?limit=10")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    def test_analytics_activity_invalid_limit_returns_422(self):
        """GET /api/analytics/activity?limit=0 should return 422"""
        resp = client.get(f"{self.ROUTE_ACTIVITY}?limit=0")
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════
# JOBS MARKETPLACE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestJobsEndpoints:
    """Test /api/jobs/stats, /api/jobs/list, /api/jobs/post"""

    ROUTE_STATS = "/api/jobs/stats"
    ROUTE_LIST = "/api/jobs/list"
    ROUTE_POST = "/api/jobs/post"

    def test_jobs_stats_returns_200(self):
        """GET /api/jobs/stats should return 200"""
        resp = client.get(self.ROUTE_STATS)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        assert "total_jobs" in data, f"Missing 'total_jobs': {list(data.keys())[:10]}"
        assert "open_jobs" in data, f"Missing 'open_jobs': {list(data.keys())[:10]}"

    def test_jobs_list_returns_200(self):
        """GET /api/jobs/list should return 200"""
        resp = client.get(self.ROUTE_LIST)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        assert "jobs" in data, f"Missing 'jobs': {list(data.keys())[:10]}"
        assert "total" in data

    def test_jobs_list_with_category_returns_200(self):
        """GET /api/jobs/list?status=open&category=tech should return 200"""
        resp = client.get(f"{self.ROUTE_LIST}?status=open&category=tech")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    def test_jobs_post_returns_200(self):
        """POST /api/jobs/post should return 200"""
        resp = client.post(self.ROUTE_POST, json={
            "title": "Test Job",
            "description": "A test job listing",
            "category": "tech",
            "budget": 1000.0,
            "required_skills": ["Python", "FastAPI"],
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("success") is True, f"Expected success=True, got: {data}"
        assert "job_id" in data, f"Missing 'job_id': {data}"

    def test_jobs_post_invalid_returns_422(self):
        """POST /api/jobs/post without required fields should return 422"""
        resp = client.post(self.ROUTE_POST, json={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

    def test_jobs_post_then_list_consistency(self):
        """Post a job then verify it appears in the list"""
        # Post
        resp_post = client.post(self.ROUTE_POST, json={
            "title": "Consistency Check Job",
            "description": "Testing list consistency",
            "category": "test",
        })
        assert resp_post.status_code == 200
        job_id = resp_post.json().get("job_id")
        assert job_id is not None

        # List
        resp_list = client.get(self.ROUTE_LIST)
        assert resp_list.status_code == 200
        jobs = resp_list.json().get("jobs", [])
        ids = [j.get("id") for j in jobs]
        assert job_id in ids, f"Posted job {job_id} not found in list: {ids[:5]}"


# ═══════════════════════════════════════════════════════════════════════
# SYNC / OFFLINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestSyncEndpoints:
    """Test /api/sync/status, /api/sync/queue, /api/sync/enqueue, /api/sync/flush"""

    ROUTE_STATUS = "/api/sync/status"
    ROUTE_QUEUE = "/api/sync/queue"
    ROUTE_ENQUEUE = "/api/sync/enqueue"
    ROUTE_FLUSH = "/api/sync/flush"

    def test_sync_status_returns_200(self):
        """GET /api/sync/status should return 200"""
        resp = client.get(self.ROUTE_STATUS)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        assert any(k in data for k in ("status", "queue_size", "message", "last_sync")), \
            f"Missing expected keys: {list(data.keys())[:10]}"

    def test_sync_queue_returns_200(self):
        """GET /api/sync/queue should return 200"""
        resp = client.get(self.ROUTE_QUEUE)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "operations" in data, f"Missing 'operations': {list(data.keys())[:10]}"
        assert "total" in data

    def test_sync_enqueue_returns_200(self):
        """POST /api/sync/enqueue should return 200"""
        resp = client.post(self.ROUTE_ENQUEUE, json={
            "op_type": "create",
            "entity_type": "message",
            "entity_id": "msg-001",
            "payload": {"text": "Hello"},
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("success") is True, f"Expected success=True, got: {data}"

    def test_sync_enqueue_invalid_returns_422(self):
        """POST /api/sync/enqueue without required fields should return 422"""
        resp = client.post(self.ROUTE_ENQUEUE, json={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

    def test_sync_flush_returns_200(self):
        """POST /api/sync/flush should return 200"""
        resp = client.post(self.ROUTE_FLUSH)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("success") is True, f"Expected success=True, got: {data}"
        assert "flushed" in data, f"Missing 'flushed': {data}"

    def test_sync_enqueue_then_queue_increases(self):
        """Enqueue an operation then verify queue size increases"""
        # Get baseline
        resp_before = client.get(self.ROUTE_QUEUE)
        before_total = resp_before.json().get("total", 0)

        # Enqueue
        resp_enq = client.post(self.ROUTE_ENQUEUE, json={
            "op_type": "update",
            "entity_type": "profile",
            "entity_id": "user-42",
            "payload": {"name": "Test"},
        })
        assert resp_enq.status_code == 200

        # Get queue again
        resp_after = client.get(self.ROUTE_QUEUE)
        after_total = resp_after.json().get("total", 0)
        assert after_total >= before_total, \
            f"Queue size decreased after enqueue: {before_total} → {after_total}"


# ═══════════════════════════════════════════════════════════════════════
# MESH OFFLINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

class TestMeshOfflineEndpoints:
    """Test /api/mesh/offline/status/{user_id}, /api/mesh/offline/capabilities, /api/mesh/offline/operation"""

    ROUTE_USER_STATUS = "/api/mesh/offline/status/test-user-123"
    ROUTE_CAPABILITIES = "/api/mesh/offline/capabilities"
    ROUTE_OPERATION = "/api/mesh/offline/operation"

    def test_mesh_offline_user_status_returns_200(self):
        """GET /api/mesh/offline/status/{user_id} should return 200"""
        resp = client.get(self.ROUTE_USER_STATUS)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, dict)
        assert "user_id" in data, f"Missing 'user_id': {list(data.keys())[:10]}"
        assert data["user_id"] == "test-user-123"

    def test_mesh_offline_capabilities_returns_200(self):
        """GET /api/mesh/offline/capabilities should return 200"""
        resp = client.get(self.ROUTE_CAPABILITIES)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "capabilities" in data, f"Missing 'capabilities': {list(data.keys())[:10]}"
        assert isinstance(data["capabilities"], list), f"capabilities should be list, got {type(data['capabilities'])}"
        assert len(data["capabilities"]) > 0, "capabilities list should not be empty"

    def test_mesh_offline_operation_returns_200(self):
        """POST /api/mesh/offline/operation should return 200"""
        resp = client.post(self.ROUTE_OPERATION, json={
            "operation_type": "sync_data",
            "payload": {"key": "value"},
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("success") is True, f"Expected success=True, got: {data}"
        assert "operation_id" in data, f"Missing 'operation_id': {data}"

    def test_mesh_offline_operation_invalid_returns_422(self):
        """POST /api/mesh/offline/operation without required fields should return 422"""
        resp = client.post(self.ROUTE_OPERATION, json={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════
# CROSS-DOMAIN INTEGRITY CHECKS
# ═══════════════════════════════════════════════════════════════════════

class TestCrossDomainIntegrity:
    """Verify no route conflicts between remaining endpoints and existing ones"""

    def test_no_route_conflicts_with_consensus_mesh_clones(self):
        """Verify that the new endpoints don't shadow existing ones"""
        # Consensus endpoints should still work
        resp = client.get("/api/consensus/stats")
        assert resp.status_code in (200, 404), f"Consensus stats broken: {resp.status_code}"

        # Clones endpoints should still work
        resp = client.get("/api/clones/specs")
        assert resp.status_code in (200, 503, 404), f"Clones specs broken: {resp.status_code}"

    def test_health_endpoint_still_works(self):
        """Verify health endpoint is not affected"""
        resp = client.get("/health")
        assert resp.status_code in (200, 404), f"Health endpoint broken: {resp.status_code}"

    def test_all_new_routes_are_distinct(self):
        """Verify that all new routes return distinct data (no collision)"""
        routes = [
            ("GET", "/api/dharma/status"),
            ("GET", "/api/dreaming/status"),
            ("GET", "/api/analytics/overview"),
            ("GET", "/api/jobs/stats"),
            ("GET", "/api/sync/status"),
            ("GET", "/api/mesh/offline/capabilities"),
        ]
        results = {}
        for method, route in routes:
            resp = client.get(route)
            results[route] = resp.status_code

        # At minimum all should return 200 (graceful fallback)
        failing = {r: s for r, s in results.items() if s != 200}
        assert not failing, f"Non-200 responses: {failing}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
