
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test ASIMNEXUS Microkernel
==========================

Tests for seL4-inspired microkernel:
- Capability-based security
- Process isolation
- Message passing (IPC)
- Real-time scheduling
"""

import time

from core.kernel.microkernel import (
    ASIMMicrokernel,
    CapabilityManager,
    ProcessManager,
    IPCManager,
    RealTimeScheduler,
    Capability,
    CapabilityRight,
    Process,
    ProcessState
)

def test_microkernel_initialization():
    """Test microkernel initialization"""
    microkernel = ASIMMicrokernel()
    assert microkernel is not None
    assert not microkernel.running
    print("✅ Microkernel initialization test passed")

def test_capability_manager():
    """Test capability manager"""
    cap_manager = CapabilityManager()
    
    # Register resource
    cap_manager.register_resource("test_resource", "Test resource for testing")
    assert "test_resource" in cap_manager.resources
    
    # Grant capability
    cap = cap_manager.grant_capability(
        process_id="process_1",
        resource_id="test_resource",
        rights=[CapabilityRight.READ, CapabilityRight.WRITE]
    )
    assert cap is not None
    assert cap.id in cap_manager.capabilities
    
    # Check capability
    assert cap_manager.check_capability(
        "process_1",
        cap.id,
        CapabilityRight.READ
    )
    assert not cap_manager.check_capability(
        "process_1",
        cap.id,
        CapabilityRight.DELETE
    )
    
    # Revoke capability
    assert cap_manager.revoke_capability(cap.id)
    assert cap.revoked
    assert not cap_manager.check_capability(
        "process_1",
        cap.id,
        CapabilityRight.READ
    )
    
    print("✅ Capability manager test passed")

def test_process_manager():
    """Test process manager"""
    cap_manager = CapabilityManager()
    proc_manager = ProcessManager(cap_manager)
    
    # Create simple target function
    def simple_task():
        time.sleep(0.1)
        return "task completed"
    
    # Spawn process
    process = proc_manager.spawn_process(
        name="test_process",
        target=simple_task,
        priority=5
    )
    assert process is not None
    assert process.name == "test_process"
    assert process.priority == 5
    assert process.state == ProcessState.RUNNING
    
    # Get process
    retrieved = proc_manager.get_process(process.id)
    assert retrieved is not None
    assert retrieved.id == process.id
    
    # Kill process
    assert proc_manager.kill_process(process.id)
    assert process.state == ProcessState.TERMINATED
    
    print("✅ Process manager test passed")

def test_ipc_manager():
    """Test IPC manager"""
    cap_manager = CapabilityManager()
    ipc_manager = IPCManager(cap_manager)
    
    # Register handler
    def test_handler(message):
        return {"response": "handled", "data": message.payload}
    
    ipc_manager.register_handler("test_type", test_handler)
    
    # Send message
    message = ipc_manager.send_message(
        from_process="process_1",
        to_process="process_2",
        payload={"type": "test_type", "data": "test data"}
    )
    assert message is not None
    assert message.from_process == "process_1"
    assert message.to_process == "process_2"
    
    # Handle message
    response = ipc_manager.handle_message(message)
    assert response is not None
    assert response["response"] == "handled"
    
    print("✅ IPC manager test passed")

def test_real_time_scheduler():
    """Test real-time scheduler"""
    scheduler = RealTimeScheduler()
    
    # Create test processes
    process1 = Process(id="1", name="low_priority", priority=1)
    process2 = Process(id="2", name="high_priority", priority=10)
    process3 = Process(id="3", name="medium_priority", priority=5)
    
    # Add processes
    scheduler.add_process(process1)
    scheduler.add_process(process2)
    scheduler.add_process(process3)
    
    # Check scheduling (highest priority first)
    next_process = scheduler.schedule()
    assert next_process is not None
    assert next_process.priority == 10
    assert next_process.name == "high_priority"
    
    # Update CPU time
    scheduler.update_cpu_time("2", 0.5)
    assert process2.cpu_time == 0.5
    
    # Remove process
    assert scheduler.remove_process("2")
    next_process = scheduler.schedule()
    assert next_process.priority == 5  # Now medium priority
    
    print("✅ Real-time scheduler test passed")

def test_microkernel_integration():
    """Test microkernel integration"""
    microkernel = ASIMMicrokernel()
    microkernel.start()
    assert microkernel.running
    
    # Create process
    def test_task():
        return "test"
    
    process = microkernel.create_process(
        name="integration_test",
        target=test_task,
        priority=5
    )
    assert process is not None
    
    # Grant capability
    microkernel.capability_manager.register_resource("integration_resource", "Integration test resource")
    cap = microkernel.grant_capability(
        process_id=process.id,
        resource_id="integration_resource",
        rights=[CapabilityRight.READ]
    )
    assert cap is not None
    
    # Send message
    msg = microkernel.send_message(
        from_process=process.id,
        to_process="another_process",
        payload={"data": "test"}
    )
    assert msg is not None
    
    # Check status
    status = microkernel.get_status()
    assert status["running"]
    assert status["processes"] >= 1
    
    microkernel.stop()
    assert not microkernel.running
    
    print("✅ Microkernel integration test passed")

if __name__ == "__main__":
    test_microkernel_initialization()
    test_capability_manager()
    test_process_manager()
    test_ipc_manager()
    test_real_time_scheduler()
    test_microkernel_integration()
    print("\n🎉 All microkernel tests passed!")
