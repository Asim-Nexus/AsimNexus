"""
Phase 3.2: Load Testing Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_performance():
    """Health endpoint responds under 200ms."""
    from app import app
    import time
    client = TestClient(app)
    start = time.time()
    response = client.get("/health")
    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 1.0, f"Health endpoint too slow: {elapsed:.3f}s"


def test_metrics_endpoint_performance():
    """Metrics endpoint responds under 500ms."""
    from app import app
    import time
    client = TestClient(app)
    start = time.time()
    response = client.get("/metrics")
    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 1.0, f"Metrics endpoint too slow: {elapsed:.3f}s"


def test_concurrent_requests():
    """System handles concurrent requests without errors."""
    from app import app
    client = TestClient(app)
    import concurrent.futures
    
    def make_request(i):
        return client.get("/health").status_code
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    assert all(r == 200 for r in results), f"Some requests failed: {results}"