#!/usr/bin/env python3
"""
Performance Benchmark Suite
===========================
Measures and validates performance characteristics of critical AsimNexus
components: API response times, scanner throughput, builder operations,
and knowledge base query performance.

Run: pytest tests/real/test_performance_benchmarks.py -v --benchmark
     pytest tests/real/test_performance_benchmarks.py -v (skip benchmarks)
"""

import pytest
import time
import os
import sys
import tempfile
from typing import Dict, Any

# ── Configuration ────────────────────────────────────────────────

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 30
BENCHMARK_ENABLED = os.environ.get("BENCHMARK", "0") == "1"

# ── Helpers ──────────────────────────────────────────────────────

def skip_unless_benchmark():
    """Skip test unless BENCHMARK=1 is set."""
    if not BENCHMARK_ENABLED:
        pytest.skip("Set BENCHMARK=1 to run performance benchmarks")

# ══════════════════════════════════════════════════════════════════
# 1. API RESPONSE TIME BENCHMARKS
# ══════════════════════════════════════════════════════════════════

class TestAPIResponseTimes:
    """Benchmark API endpoint response times."""

    @pytest.mark.benchmark
    def test_health_response_time(self):
        """Health endpoint should respond in < 100ms."""
        skip_unless_benchmark()
        import requests
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert resp.status_code == 200

        avg = sum(times) / len(times)
        p99 = sorted(times)[int(len(times) * 0.99)]
        print(f"\n  /health: avg={avg:.1f}ms, p99={p99:.1f}ms, min={min(times):.1f}ms, max={max(times):.1f}ms")
        assert avg < 100, f"Average response time {avg:.1f}ms exceeds 100ms"

    @pytest.mark.benchmark
    def test_self_awareness_summary_response_time(self):
        """Self-awareness summary should respond in < 500ms."""
        skip_unless_benchmark()
        import requests
        times = []
        for _ in range(5):
            start = time.perf_counter()
            resp = requests.get(f"{BASE_URL}/api/self/knowledge/summary", timeout=TIMEOUT)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert resp.status_code == 200

        avg = sum(times) / len(times)
        print(f"\n  /api/self/knowledge/summary: avg={avg:.1f}ms")
        assert avg < 500, f"Average response time {avg:.1f}ms exceeds 500ms"

    @pytest.mark.benchmark
    def test_scan_trigger_response_time(self):
        """Scan trigger should respond in < 2000ms."""
        skip_unless_benchmark()
        import requests
        start = time.perf_counter()
        resp = requests.post(f"{BASE_URL}/api/self/scan", timeout=30)
        elapsed = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        print(f"\n  POST /api/self/scan: {elapsed:.0f}ms")
        assert elapsed < 2000, f"Scan trigger took {elapsed:.0f}ms, exceeds 2000ms"

# ══════════════════════════════════════════════════════════════════
# 2. SCANNER THROUGHPUT BENCHMARKS
# ══════════════════════════════════════════════════════════════════

class TestScannerThroughput:
    """Benchmark codebase scanner performance."""

    @pytest.mark.benchmark
    def test_scanner_throughput(self):
        """Scanner should process at least 100 files/second."""
        skip_unless_benchmark()
        from core.self_awareness.codebase_scanner import CodebaseScanner

        scanner = CodebaseScanner()
        start = time.perf_counter()
        result = scanner.scan()
        elapsed = time.perf_counter() - start

        files_scanned = len(result.modules)
        throughput = files_scanned / elapsed if elapsed > 0 else 0

        print(f"\n  Scanner: {files_scanned} files in {elapsed:.1f}s ({throughput:.0f} files/s)")
        assert throughput >= 50, f"Scanner throughput {throughput:.0f} files/s below 50 files/s"

    @pytest.mark.benchmark
    def test_scanner_memory_usage(self):
        """Scanner should not leak memory across multiple scans."""
        skip_unless_benchmark()
        from core.self_awareness.codebase_scanner import CodebaseScanner
        import psutil

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        scanner = CodebaseScanner()
        for _ in range(3):
            scanner.scan()

        mem_after = process.memory_info().rss / 1024 / 1024
        mem_delta = mem_after - mem_before

        print(f"\n  Scanner memory: {mem_before:.1f}MB → {mem_after:.1f}MB (delta: {mem_delta:.1f}MB)")
        assert mem_delta < 50, f"Memory grew by {mem_delta:.1f}MB across 3 scans, exceeds 50MB"

# ══════════════════════════════════════════════════════════════════
# 3. SELF-BUILDER OPERATION BENCHMARKS
# ══════════════════════════════════════════════════════════════════

class TestBuilderPerformance:
    """Benchmark SelfBuilder operations."""

    @pytest.mark.benchmark
    def test_fix_bare_excepts_performance(self, tmp_path):
        """fix_bare_excepts should process files in < 100ms."""
        skip_unless_benchmark()
        from core.self_awareness.self_builder import SelfBuilder

        # Create a test file with bare excepts
        test_file = tmp_path / "test_bare_except.py"
        test_file.write_text("""def foo():
    try:
        return 1
    except:
        return 0

def bar():
    try:
        x = 1
    except:
        x = 0
""")

        builder = SelfBuilder()
        start = time.perf_counter()
        result = builder.fix_bare_excepts(str(test_file))
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  fix_bare_excepts: {elapsed:.1f}ms, fixed={result.modified_count}")
        assert elapsed < 100, f"fix_bare_excepts took {elapsed:.1f}ms, exceeds 100ms"

    @pytest.mark.benchmark
    def test_add_missing_docstrings_performance(self, tmp_path):
        """add_missing_docstrings should process files in < 100ms."""
        skip_unless_benchmark()
        from core.self_awareness.self_builder import SelfBuilder

        test_file = tmp_path / "test_docstring.py"
        test_file.write_text("""class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass

def top_level_func():
    pass
""")

        builder = SelfBuilder()
        start = time.perf_counter()
        result = builder.add_missing_docstrings(str(test_file))
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  add_missing_docstrings: {elapsed:.1f}ms, added={result.modified_count}")
        assert elapsed < 100, f"add_missing_docstrings took {elapsed:.1f}ms, exceeds 100ms"

    @pytest.mark.benchmark
    def test_remove_unused_imports_performance(self, tmp_path):
        """remove_unused_imports should process files in < 100ms."""
        skip_unless_benchmark()
        from core.self_awareness.self_builder import SelfBuilder

        test_file = tmp_path / "test_unused_imports.py"
        test_file.write_text("""import os
import sys
import json
from typing import Dict, List, Optional

def foo() -> str:
    return os.path.join("a", "b")
""")

        builder = SelfBuilder()
        start = time.perf_counter()
        result = builder.remove_unused_imports(str(test_file))
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  remove_unused_imports: {elapsed:.1f}ms, removed={result.modified_count}")
        assert elapsed < 100, f"remove_unused_imports took {elapsed:.1f}ms, exceeds 100ms"

    @pytest.mark.benchmark
    def test_resolve_todos_performance(self, tmp_path):
        """resolve_todos should process files in < 100ms."""
        skip_unless_benchmark()
        from core.self_awareness.self_builder import SelfBuilder

        test_file = tmp_path / "test_todos.py"
        test_file.write_text("""# TODO: implement this function
def foo():
    # FIXME: this is broken
    pass

# HACK: temporary workaround
def bar():
    # TODO: optimize later
    pass
""")

        builder = SelfBuilder()
        start = time.perf_counter()
        result = builder.resolve_todos(str(test_file))
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  resolve_todos: {elapsed:.1f}ms, found={result.modified_count}")
        assert elapsed < 100, f"resolve_todos took {elapsed:.1f}ms, exceeds 100ms"

# ══════════════════════════════════════════════════════════════════
# 4. KNOWLEDGE BASE QUERY PERFORMANCE
# ══════════════════════════════════════════════════════════════════

class TestKnowledgePerformance:
    """Benchmark SelfKnowledge query performance."""

    @pytest.mark.benchmark
    def test_knowledge_summary_query_time(self):
        """Knowledge summary should be computable in < 50ms."""
        skip_unless_benchmark()
        from core.self_awareness import get_knowledge

        knowledge = get_knowledge()
        start = time.perf_counter()
        summary = knowledge.get_summary()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  get_summary(): {elapsed:.1f}ms")
        assert elapsed < 50, f"get_summary() took {elapsed:.1f}ms, exceeds 50ms"

    @pytest.mark.benchmark
    def test_knowledge_serialization_time(self):
        """Knowledge serialization should complete in < 100ms."""
        skip_unless_benchmark()
        from core.self_awareness import get_knowledge

        knowledge = get_knowledge()
        start = time.perf_counter()
        data = knowledge.to_dict()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  to_dict(): {elapsed:.1f}ms")
        assert elapsed < 100, f"to_dict() took {elapsed:.1f}ms, exceeds 100ms"

# ══════════════════════════════════════════════════════════════════
# 5. CONCURRENT OPERATION BENCHMARKS
# ══════════════════════════════════════════════════════════════════

class TestConcurrentPerformance:
    """Benchmark system under concurrent load."""

    @pytest.mark.benchmark
    def test_concurrent_health_checks(self):
        """System should handle 50 concurrent health checks."""
        skip_unless_benchmark()
        import requests
        import concurrent.futures

        def check_health():
            resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
            return resp.status_code

        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed = time.perf_counter() - start

        success_rate = sum(1 for r in results if r == 200) / len(results) * 100
        throughput = len(results) / elapsed

        print(f"\n  50 concurrent /health: {elapsed:.1f}s total, {throughput:.0f} req/s, {success_rate:.0f}% success")
        assert success_rate >= 95, f"Success rate {success_rate:.0f}% below 95%"
        assert throughput >= 10, f"Throughput {throughput:.0f} req/s below 10 req/s"

# ══════════════════════════════════════════════════════════════════
# 6. STARTUP TIME BENCHMARK
# ══════════════════════════════════════════════════════════════════

class TestStartupPerformance:
    """Benchmark module import and initialization times."""

    @pytest.mark.benchmark
    def test_core_import_time(self):
        """Core self-awareness modules should import in < 500ms."""
        skip_unless_benchmark()
        import importlib

        modules = [
            "core.self_awareness",
            "core.self_awareness.codebase_scanner",
            "core.self_awareness.self_knowledge",
            "core.self_awareness.self_builder",
            "core.self_awareness.evolution_bridge",
        ]

        for mod_name in modules:
            start = time.perf_counter()
            importlib.import_module(mod_name)
            elapsed = (time.perf_counter() - start) * 1000
            print(f"\n  import {mod_name}: {elapsed:.1f}ms")
            assert elapsed < 500, f"Import {mod_name} took {elapsed:.1f}ms, exceeds 500ms"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
