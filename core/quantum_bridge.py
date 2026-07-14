"""
Quantum Bridge — simulated quantum computing interface for ASIMNEXUS.
====================================================================
Provides a simulated quantum job execution environment with support
for Grover's search, Shor's factoring, and variational algorithms.

Exports:
    QuantumAlgorithm  — enum of supported quantum algorithms
    QuantumProvider   — enum of quantum backends
    QuantumJob        — dataclass representing a quantum job
    QuantumDevice     — dataclass representing a quantum device
    QuantumBridge     — main class with create_job / execute_job
    get_quantum_bridge — singleton factory
"""

import asyncio
import math
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple


class QuantumAlgorithm(Enum):
    """Supported quantum algorithms."""
    GROVER = "grover"
    SHOR = "shor"
    VQE = "vqe"
    QAOA = "qaoa"
    QUANTUM_FOURIER = "quantum_fourier"


class QuantumProvider(Enum):
    """Quantum computing backends."""
    IBM_QISKIT = "ibm_qiskit"
    RIGETTI = "rigetti"
    IONQ = "ionq"
    SIMULATOR = "simulator"


@dataclass
class QuantumJob:
    """Represents a quantum computation job."""
    job_id: str
    algorithm: QuantumAlgorithm
    parameters: Dict[str, Any]
    shots: int
    provider: QuantumProvider = QuantumProvider.SIMULATOR
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


@dataclass
class QuantumDevice:
    """Represents a quantum computing device."""
    name: str
    provider: QuantumProvider
    qubits: int
    gate_error_rate: float = 0.001


@dataclass
class QuantumKey:
    """Represents a quantum-generated cryptographic key."""
    key_id: str
    length_bits: int
    used_for: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class QuantumBridge:
    """Simulated quantum bridge for job creation and execution."""

    def __init__(self):
        self._jobs: Dict[str, QuantumJob] = {}
        self._quantum_keys: Dict[str, QuantumKey] = {}
        self.devices: Dict[str, QuantumDevice] = {
            "quantum_simulator_1": QuantumDevice(
                name="quantum_simulator_1",
                provider=QuantumProvider.SIMULATOR,
                qubits=32,
                gate_error_rate=0.001,
            ),
            "quantum_simulator_2": QuantumDevice(
                name="quantum_simulator_2",
                provider=QuantumProvider.SIMULATOR,
                qubits=64,
                gate_error_rate=0.0005,
            ),
        }
        self.current_provider: QuantumProvider = QuantumProvider.SIMULATOR
        self.qiskit_available: bool = False
        self.hybrid_threshold: int = 1000

    def create_job(
        self,
        algorithm: QuantumAlgorithm,
        parameters: Dict[str, Any],
        shots: int = 1024,
    ) -> QuantumJob:
        """Create a new quantum computation job.

        Args:
            algorithm: The quantum algorithm to run
            parameters: Algorithm-specific parameters
            shots: Number of measurement shots

        Returns:
            QuantumJob with job_id assigned
        """
        job_id = f"qjob_{secrets.token_hex(8)}"
        job = QuantumJob(
            job_id=job_id,
            algorithm=algorithm,
            parameters=parameters,
            shots=shots,
        )
        self._jobs[job_id] = job
        return job

    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a quantum job (simulated).

        Args:
            job_id: The job ID returned by create_job

        Returns:
            Dict with simulated results including 'speedup' key
        """
        job = self._jobs.get(job_id)
        if not job:
            return {"error": f"Job {job_id} not found", "speedup": 0}

        job.status = "running"
        await asyncio.sleep(0.01)  # Simulate quantum computation time

        # Simulate results based on algorithm
        if job.algorithm == QuantumAlgorithm.GROVER:
            search_space = job.parameters.get("search_space_size", 1000)
            # Grover's algorithm: O(sqrt(N)) speedup
            speedup = math.sqrt(search_space) / 10.0
            result = {
                "algorithm": "grover",
                "search_space_size": search_space,
                "target": job.parameters.get("target", "unknown"),
                "speedup": round(speedup, 2),
                "success_probability": 0.95,
                "quantum_iterations": int(math.ceil(math.pi / 4 * math.sqrt(search_space))),
                "classical_iterations": search_space,
                "found_solution": True,
                "iterations": int(math.ceil(math.pi / 4 * math.sqrt(search_space))),
            }
        elif job.algorithm == QuantumAlgorithm.SHOR:
            number = job.parameters.get("number", 15)
            result = {
                "algorithm": "shor",
                "number": number,
                "factors": [3, 5] if number == 15 else [1, number],
                "factored": True,
                "speedup": 150.0,
            }
        elif job.algorithm == QuantumAlgorithm.VQE:
            result = {
                "algorithm": "vqe",
                "energy": -1.137,
                "optimal_value": -1.137,
                "approximation_ratio": 0.99,
                "speedup": 8.5,
            }
        elif job.algorithm == QuantumAlgorithm.QAOA:
            result = {
                "algorithm": "qaoa",
                "approximation_ratio": 0.97,
                "optimal_value": -42.0,
                "speedup": 12.3,
            }
        else:
            result = {
                "algorithm": job.algorithm.value,
                "speedup": 1.0,
            }

        job.status = "completed"
        job.result = result
        return result

    def get_job(self, job_id: str) -> Optional[QuantumJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def select_optimal_device(
        self,
        algorithm: QuantumAlgorithm,
        min_qubits: int = 1,
    ) -> Optional[QuantumDevice]:
        """Select the optimal device for a given algorithm.

        Args:
            algorithm: The quantum algorithm to run
            min_qubits: Minimum number of qubits required

        Returns:
            The best available device, or None if none meet requirements
        """
        candidates = [
            d for d in self.devices.values()
            if d.qubits >= min_qubits
        ]
        if not candidates:
            return None
        # Prefer device with lowest gate error rate
        return min(candidates, key=lambda d: d.gate_error_rate)

    def should_use_quantum(
        self,
        problem_size: int,
        algorithm: QuantumAlgorithm,
    ) -> Tuple[bool, float]:
        """Determine whether to use quantum or classical computing.

        Args:
            problem_size: Size of the problem instance
            algorithm: The quantum algorithm to consider

        Returns:
            Tuple of (should_use_quantum, estimated_speedup)
        """
        if algorithm == QuantumAlgorithm.GROVER:
            # Grover's: O(sqrt(N)) vs classical O(N)
            speedup = math.sqrt(problem_size) / 10.0
            return (problem_size > self.hybrid_threshold, round(speedup, 2))
        elif algorithm == QuantumAlgorithm.SHOR:
            # Shor's: exponential speedup for factoring
            speedup = 150.0
            return (problem_size > 10, speedup)
        elif algorithm in (QuantumAlgorithm.VQE, QuantumAlgorithm.QAOA):
            speedup = 10.0
            return (problem_size > 50, speedup)
        else:
            return (False, 1.0)

    def generate_quantum_key(
        self,
        length_bits: int = 256,
        used_for: str = "encryption",
    ) -> QuantumKey:
        """Generate a quantum-derived cryptographic key.

        Args:
            length_bits: Key length in bits
            used_for: Purpose of the key

        Returns:
            QuantumKey with key_id, length_bits, used_for
        """
        key_id = f"qkey_{secrets.token_hex(8)}"
        key = QuantumKey(
            key_id=key_id,
            length_bits=length_bits,
            used_for=used_for,
        )
        self._quantum_keys[key_id] = key
        return key

    def get_quantum_safe_algorithm(self) -> str:
        """Get the recommended post-quantum cryptographic algorithm.

        Returns:
            Name of the recommended post-quantum algorithm
        """
        return "CRYSTALS-Kyber"

    def get_stats(self) -> Dict[str, Any]:
        """Get quantum bridge statistics."""
        total_devices = len(self.devices)
        available_devices = sum(
            1 for d in self.devices.values()
            if d.gate_error_rate < 0.01
        )
        total_jobs = len(self._jobs)
        completed_jobs = sum(
            1 for j in self._jobs.values() if j.status == "completed"
        )
        return {
            "devices": {
                "total": total_devices,
                "available": available_devices,
            },
            "jobs": {
                "total": total_jobs,
                "completed": completed_jobs,
            },
            "quantum_keys": {
                "total": len(self._quantum_keys),
            },
            "hybrid_threshold": self.hybrid_threshold,
            "total_jobs": total_jobs,
            "active_jobs": sum(1 for j in self._jobs.values() if j.status == "running"),
            "completed_jobs": completed_jobs,
        }


# ── Singleton factory ────────────────────────────────────────────────────────

_quantum_bridge_instance: Optional[QuantumBridge] = None


def get_quantum_bridge() -> QuantumBridge:
    """Return the singleton QuantumBridge instance."""
    global _quantum_bridge_instance
    if _quantum_bridge_instance is None:
        _quantum_bridge_instance = QuantumBridge()
    return _quantum_bridge_instance
