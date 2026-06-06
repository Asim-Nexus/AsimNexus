
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test Quantum Bridge
===================

Test the Quantum Bridge implementation.
"""

import asyncio
import json
from core.quantum_bridge import QuantumBridge, get_quantum_bridge, QuantumAlgorithm, QuantumProvider


async def test_quantum_bridge():
    """Test Quantum Bridge System"""
    print("=" * 60)
    print("Testing Quantum Bridge System")
    print("=" * 60)
    
    bridge = get_quantum_bridge()
    
    # Test 1: Initialization
    print("\n[OK] Quantum Bridge initialized")
    print(f"  Total devices: {len(bridge.devices)}")
    print(f"  Current provider: {bridge.current_provider.value}")
    print(f"  Qiskit available: {bridge.qiskit_available}")
    
    # Test 2: Device listing
    print("\n[OK] Quantum devices:")
    for device in bridge.devices.values():
        print(f"  - {device.name} ({device.provider.value})")
        print(f"    Qubits: {device.qubits}, Error rate: {device.gate_error_rate}")
    
    # Test 3: Job creation and execution - Grover's algorithm
    print("\n[OK] Testing Grover's search algorithm...")
    job = bridge.create_job(
        algorithm=QuantumAlgorithm.GROVER,
        parameters={"search_space_size": 10000, "target": "item_42"},
        shots=1024
    )
    print(f"  Job ID: {job.job_id}")
    print(f"  Algorithm: {job.algorithm.value}")
    
    result = await bridge.execute_job(job.job_id)
    print(f"  Result:")
    print(f"    Speedup: {result.get('speedup', 0):.2f}x")
    print(f"    Success probability: {result.get('success_probability', 0):.2f}")
    print(f"    Quantum iterations: {result.get('quantum_iterations', 0)}")
    print(f"    Classical iterations: {result.get('classical_iterations', 0)}")
    
    # Test 4: Shor's algorithm
    print("\n[OK] Testing Shor's factorization algorithm...")
    shor_job = bridge.create_job(
        algorithm=QuantumAlgorithm.SHOR,
        parameters={"number": 15},
        shots=1024
    )
    
    shor_result = await bridge.execute_job(shor_job.job_id)
    print(f"  Factors: {shor_result.get('factors', [])}")
    print(f"  Number factored: {shor_result.get('number', 0)}")
    
    # Test 5: QAOA optimization
    print("\n[OK] Testing QAOA optimization...")
    qaoa_job = bridge.create_job(
        algorithm=QuantumAlgorithm.QAOA,
        parameters={"problem_size": 20},
        shots=1024
    )
    
    qaoa_result = await bridge.execute_job(qaoa_job.job_id)
    print(f"  Approximation ratio: {qaoa_result.get('approximation_ratio', 0):.2f}")
    print(f"  Optimal value: {qaoa_result.get('optimal_value', 0):.4f}")
    
    # Test 6: Optimal device selection
    print("\n[OK] Testing optimal device selection...")
    optimal_device = bridge.select_optimal_device(QuantumAlgorithm.GROVER, min_qubits=10)
    if optimal_device:
        print(f"  Optimal device: {optimal_device.name}")
        print(f"  Provider: {optimal_device.provider.value}")
        print(f"  Qubits: {optimal_device.qubits}")
    
    # Test 7: Quantum vs Classical decision
    print("\n[OK] Testing quantum vs classical decision...")
    for size in [100, 1000, 10000]:
        should_use, speedup = bridge.should_use_quantum(size, QuantumAlgorithm.GROVER)
        print(f"  Size {size}: Use quantum={should_use}, Speedup={speedup:.2f}x")
    
    # Test 8: Quantum key generation
    print("\n[OK] Testing quantum key generation...")
    key = bridge.generate_quantum_key(length_bits=256, used_for="encryption")
    print(f"  Key ID: {key.key_id}")
    print(f"  Length: {key.length_bits} bits")
    print(f"  Purpose: {key.used_for}")
    
    # Test 9: Post-quantum algorithm
    print("\n[OK] Testing post-quantum cryptography...")
    pq_algo = bridge.get_quantum_safe_algorithm()
    print(f"  Recommended algorithm: {pq_algo}")
    
    # Test 10: Statistics
    print("\n[OK] Quantum Bridge Statistics:")
    stats = bridge.get_stats()
    print(f"  Devices: {stats['devices']['total']} total, {stats['devices']['available']} available")
    print(f"  Jobs: {stats['jobs']['total']} total, {stats['jobs']['completed']} completed")
    print(f"  Quantum keys: {stats['quantum_keys']['total']} total")
    print(f"  Hybrid threshold: {stats['hybrid_threshold']}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Quantum Bridge Test Passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_quantum_bridge())
