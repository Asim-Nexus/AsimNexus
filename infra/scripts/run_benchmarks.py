#!/usr/bin/env python3
"""
AsimNexus v1.0.1 — Performance Benchmarks

Measures latency and memory footprint of key system operations.
Outputs results in markdown format for docs/operations/PERFORMANCE_BENCHMARKS.md.
"""

import sys
import os
import time
import math
import statistics

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# ============================================================
#  Benchmark utilities
# ============================================================


@dataclass
class BenchmarkResult:
    name: str
    samples: int
    times: List[float]

    @property
    def avg_us(self) -> float:
        """Average time in microseconds."""
        return (sum(self.times) / len(self.times)) * 1e6

    @property
    def p95_us(self) -> float:
        """p95 time in microseconds."""
        sorted_t = sorted(self.times)
        idx = int(len(sorted_t) * 0.95)
        return sorted_t[idx] * 1e6

    @property
    def avg_ms(self) -> float:
        return self.avg_us / 1000

    @property
    def p95_ms(self) -> float:
        return self.p95_us / 1000

    def is_slow(self, threshold_ms: float = 100.0) -> bool:
        return self.avg_ms > threshold_ms

    def summary(self, layer: str = "") -> str:
        flag = " ⚠️ **SLOW** — optimization target for v1.2" if self.is_slow() else ""
        return (
            f"| {layer}{self.name} | {self.avg_us:.2f} µs | {self.p95_us:.2f} µs | {self.samples} |{flag}"
        )


def run_benchmark(name: str, fn, iterations: int = 10000, warmup: int = 100) -> BenchmarkResult:
    """Run a benchmark function `iterations` times and collect timings."""
    # Warmup
    for _ in range(warmup):
        fn()

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)

    return BenchmarkResult(name=name, samples=iterations, times=times)


# ============================================================
#  1. Mesh Layer Benchmarks
# ============================================================

def bench_mesh_layer():
    """Benchmark P2P message and DHT operations."""
    results = []

    # 1a. P2PMessage serialize/deserialize round-trip
    from mesh.p2p_transport import P2PMessage

    msg = P2PMessage(
        msg_type="PING",
        sender_id="bench_node",
        msg_id="bench_001",
        payload={"seq": 42, "data": "benchmark-payload"},
    )

    def p2p_roundtrip():
        raw = msg.to_bytes()
        P2PMessage.from_bytes(raw)

    results.append(run_benchmark("P2PMessage round-trip", p2p_roundtrip))

    # 1a2. P2PMessage serialization (separate from deserialization)
    def p2p_serialize():
        return msg.to_bytes()

    results.append(run_benchmark("P2PMessage serialization", p2p_serialize))

    # 1a3. P2PMessage deserialization (separate from serialization)
    raw = msg.to_bytes()
    def p2p_deserialize():
        return P2PMessage.from_bytes(raw)

    results.append(run_benchmark("P2PMessage deserialization", p2p_deserialize))

    # 1b. DHT find_closest_nodes (with 100 nodes in routing table)
    from mesh.kademlia_dht import KademliaDHT, NodeID

    dht = KademliaDHT()
    # Populate routing table with 100 nodes
    for i in range(100):
        nid = NodeID.random()
        # Add via internal routing table directly for speed
        from mesh.kademlia_dht import DHTNode
        node = DHTNode(node_id=nid, ip_address=f"10.0.0.{i % 255}", port=7332 + i)
        dht.add_node(node)

    target = NodeID.random()

    def dht_find_closest():
        dht.find_closest_nodes(target, count=20)

    results.append(run_benchmark("DHT find_closest_nodes (100 nodes)", dht_find_closest))

    # 1c. CRDT GCounter increment + value()
    from mesh.crdt_sync import GCounter

    counter = GCounter(crdt_id="bench_counter")

    def crdt_gcounter():
        op = counter.increment("bench_node", amount=1)
        _ = counter.value()

    results.append(run_benchmark("CRDT GCounter increment+value", crdt_gcounter))

    return results


# ============================================================
#  2. Consensus Layer Benchmarks
# ============================================================

def bench_consensus_layer():
    """Benchmark consensus engine majority vote tally."""
    results = []

    # Use the consensus engine from core/consensus
    try:
        from core.consensus.consensus_engine import (
            ConsensusEngine, Proposal, Vote, VoteChoice, VotingMode,
        )
        import uuid

        engine = ConsensusEngine()

        # Register 15 voters
        for i in range(15):
            engine.register_voter(
                voter_id=f"clone_{i:02d}",
                name=f"Clone {i}",
                domain=f"domain_{i % 5}",
                weight=min(1.0, 0.5 + (i * 0.05)),
            )

        # Pre-create votes for the benchmark
        votes = [
            Vote(
                voter_id=f"clone_{i:02d}",
                choice=VoteChoice.APPROVE if i < 10 else VoteChoice.REJECT,
                confidence=0.8 + (i * 0.01),
                reasoning=f"Benchmark vote {i}",
            )
            for i in range(15)
        ]

        def consensus_tally():
            proposal = Proposal(
                proposal_id=str(uuid.uuid4()),
                title="Benchmark Proposal",
                description="Testing vote tally performance",
                proposed_by="benchmark",
                mode=VotingMode.MAJORITY_VOTE,
            )
            proposal.votes = votes
            engine._resolve_majority(proposal)

        results.append(run_benchmark("Consensus majority vote (15 voters)", consensus_tally))

    except ImportError as e:
        print(f"⚠️  Consensus engine import failed ({e}) — skipping benchmark")
        results.append(BenchmarkResult(
            name="Consensus majority vote (15 voters)",
            samples=0,
            times=[],
        ))

    return results


# ============================================================
#  3. Security Layer Benchmarks
# ============================================================

def bench_security_layer():
    """Benchmark security framework Level-3 check_access."""
    results = []

    try:
        # Suppress anomaly detector logging during benchmark
        import logging
        logging.getLogger("security.security_framework").setLevel(logging.ERROR)

        from security.security_framework import ASIMSecurityManager, SecurityLevel
        import asyncio

        sf = ASIMSecurityManager()

        # Create event loop once and reuse
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_check():
            allowed, reason = await sf.check_access(
                actor="bench_user",
                required_level=SecurityLevel.TOP_SECRET,
                resource="/bench/resource",
                action="read",
                credentials={"biometric": "mocked", "hardware_token": "mocked"},
            )
            return allowed

        # Prime the security layer with one call to warm up
        loop.run_until_complete(run_check())

        def check_access_sync():
            loop.run_until_complete(run_check())

        # Use fewer iterations for security (event loop overhead is significant)
        results.append(run_benchmark(
            "Security Level-3 check_access (mocked)",
            check_access_sync,
            iterations=500,
            warmup=10,
        ))

        loop.close()

    except ImportError as e:
        print(f"⚠️  Security framework import failed ({e}) — skipping benchmark")
        results.append(BenchmarkResult(
            name="Security Level-3 check_access (mocked)",
            samples=0,
            times=[],
        ))

    return results


# ============================================================
#  4. Startup Time
# ============================================================

def bench_startup_time():
    """Measure how long it takes to import all major modules."""
    results = []

    modules = [
        "mesh.p2p_transport",
        "mesh.kademlia_dht",
        "mesh.crdt_sync",
        "security.security_framework",
        "core.consensus.consensus_engine",
    ]

    def measure_import(mod_name: str) -> float:
        t0 = time.perf_counter()
        # Fresh import by removing from sys.modules if already there
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        __import__(mod_name)
        t1 = time.perf_counter()
        return t1 - t0

    # Clear cached imports for measurement
    saved_modules = {}
    for mod in modules:
        if mod in sys.modules:
            saved_modules[mod] = sys.modules[mod]

    times = []
    for mod in modules:
        if mod in sys.modules:
            del sys.modules[mod]
        t0 = time.perf_counter()
        __import__(mod)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    # Restore
    for mod, cached in saved_modules.items():
        sys.modules[mod] = cached

    total_time = sum(times)
    results.append(BenchmarkResult(
        name=f"Import all major modules ({len(modules)} modules)",
        samples=1,
        times=[total_time],
    ))

    return results


# ============================================================
#  5. Memory Footprint
# ============================================================

def bench_memory_footprint():
    """Measure memory footprint of key data structures."""
    results = []

    try:
        import tracemalloc

        tracemalloc.start()

        # Measure P2PMessage memory
        from mesh.p2p_transport import P2PMessage
        msg = P2PMessage(
            msg_type="PING",
            sender_id="bench_node",
            msg_id="bench_001",
            payload={"key": "value" * 10},
        )
        snapshot = tracemalloc.take_snapshot()
        # The snapshot shows current memory; we'll report it

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n📊 Memory Snapshot:")
        print(f"   Current: {current / 1024:.1f} KB")
        print(f"   Peak:    {peak / 1024:.1f} KB")

        # Create a benchmark result from the snapshot
        results.append(BenchmarkResult(
            name="Memory footprint (key data structures)",
            samples=1,
            times=[current / 1e6],  # Store as fraction of second for formatting
        ))

    except ImportError:
        # tracemalloc is stdlib — should be available
        print("⚠️  tracemalloc not available, skipping memory benchmark")

    return results


# ============================================================
#  Main
# ============================================================

def print_markdown_report(all_results: List[Tuple[str, List[BenchmarkResult]]]):
    """Print benchmark results in markdown format."""
    from datetime import date

    print("# Performance Benchmarks — v1.0.1")
    print(f"Date: {date.today().isoformat()}")
    print()

    for section_name, results in all_results:
        if not results:
            continue

        print(f"## {section_name}")
        print()
        print("| Operation | Avg | p95 | Samples |")
        print("|-----------|-----|-----|---------|")

        for r in results:
            if r.samples == 0:
                print(f"| {r.name} | N/A | N/A | 0 |")
            else:
                print(r.summary())

        print()

    # Optimization targets note
    print("---")
    print()
    print("### Notes")
    print("- Benchmarks run on developer machine; results are relative, not absolute.")
    print("- Slow operations (>100ms avg) flagged with ⚠️ as potential optimization targets for v1.2.")
    print("- All benchmarks run with 10,000 iterations (except startup time and memory).")
    print()


def main():
    print("🚀 AsimNexus v1.0.1 Performance Benchmarks")
    print("=" * 60)
    print()

    all_results = []

    # Mesh Layer
    print("📡 Mesh Layer Benchmarks...")
    mesh_results = bench_mesh_layer()
    all_results.append(("Mesh Layer", mesh_results))

    # Consensus Layer
    print("🏛️  Consensus Layer Benchmarks...")
    consensus_results = bench_consensus_layer()
    all_results.append(("Consensus Layer", consensus_results))

    # Security Layer
    print("🔒 Security Layer Benchmarks...")
    security_results = bench_security_layer()
    all_results.append(("Security Layer", security_results))

    # Startup Time
    print("⏱️  Startup Time...")
    startup_results = bench_startup_time()
    all_results.append(("Startup", startup_results))

    # Memory
    print("💾 Memory Footprint...")
    memory_results = bench_memory_footprint()
    all_results.append(("Memory", memory_results))

    # Print markdown report
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS (Markdown)")
    print("=" * 60)
    print()
    print_markdown_report(all_results)

    # Save to file
    import io
    buf = io.StringIO()
    # Redirect stdout to capture
    old_stdout = sys.stdout
    sys.stdout = buf
    print_markdown_report(all_results)
    sys.stdout = old_stdout
    report = buf.getvalue()

    report_path = os.path.join(os.path.dirname(__file__), "..", "docs", "operations", "PERFORMANCE_BENCHMARKS.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Report saved to {report_path}")


if __name__ == "__main__":
    main()
