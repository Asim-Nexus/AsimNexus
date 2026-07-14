"""
Phase 4.1: Microkernel Architecture Tests
"""
import pytest
from fastapi.testclient import TestClient

def test_microkernel_exists():
    """Microkernel module exists."""
    from core.kernel.microkernel import ASIMMicrokernel
    assert ASIMMicrokernel is not None

def test_microkernel_capability_manager():
    """CapabilityManager grants and checks capabilities."""
    from core.kernel.microkernel import ASIMMicrokernel, CapabilityRight
    kernel = ASIMMicrokernel()
    cap = kernel.grant_capability("proc1", "res1", [CapabilityRight.READ, CapabilityRight.WRITE])
    assert cap.process_id == "proc1"
    assert cap.resource_id == "res1"

def test_microkernel_ipc():
    """IPCManager sends messages between processes."""
    from core.kernel.microkernel import ASIMMicrokernel
    kernel = ASIMMicrokernel()
    msg = kernel.send_message("p1", "p2", {"type": "test", "data": "hello"})
    assert msg.from_process == "p1"
    assert msg.to_process == "p2"

def test_microkernel_status_endpoint():
    """Microkernel status endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/microkernel/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "data" in data