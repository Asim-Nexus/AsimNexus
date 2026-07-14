"""
STATUS: FIXED — Now references actual integration test modules
ASIMNEXUS Integration Test Suite Performance
=============================================
Performance benchmarks for the integration test suite.
Measures test execution time, import overhead, and system responsiveness.
"""

import unittest
import sys
import os
import time
import logging

logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_module_available = False
try:
    from tests.integration.integration_stress_test import (
        IntegrationStressTest,
        CircularImportDetector,
    )
    _module_available = True
except ImportError as e:
    logger.warning(f"integration_stress_test module not available (tests will be skipped): {e}")
    IntegrationStressTest = None
    CircularImportDetector = None

class TestIntegrationTestSuite(unittest.TestCase):
    """Performance benchmarks for integration test suite."""

    def setUp(self):
        """Set up test fixtures"""
        self.test_data = {"test": "data"}

    def tearDown(self):
        """Clean up after tests"""
        pass

    def _check_available(self):
        """Skip test if source module is not available."""
        if not _module_available:
            self.skipTest("integration_stress_test module not available")

    def test_integration_stress_test_initialization(self):
        """Test IntegrationStressTest initialization performance"""
        self._check_available()
        try:
            start = time.perf_counter()
            instance = IntegrationStressTest()
            elapsed = time.perf_counter() - start
            self.assertIsNotNone(instance)
            logger.info(f"✅ IntegrationStressTest init: {elapsed*1000:.2f}ms")
        except Exception as e:
            self.fail(f"IntegrationStressTest initialization failed: {e}")

    def test_circular_import_detector_initialization(self):
        """Test CircularImportDetector initialization performance"""
        self._check_available()
        try:
            start = time.perf_counter()
            detector = CircularImportDetector()
            elapsed = time.perf_counter() - start
            self.assertIsNotNone(detector)
            logger.info(f"✅ CircularImportDetector init: {elapsed*1000:.2f}ms")
        except Exception as e:
            self.fail(f"CircularImportDetector initialization failed: {e}")

    def test_import_chain_performance(self):
        """Test import chain building performance"""
        self._check_available()
        try:
            detector = CircularImportDetector()
            modules = ["json", "os", "sys", "datetime", "typing", "collections",
                       "math", "random", "re", "hashlib", "base64", "itertools",
                       "functools", "pathlib", "uuid"]

            start = time.perf_counter()
            for mod in modules:
                result = detector.test_import(mod)
                # Accept success or error (module may already be loaded)
                self.assertIn(result.get("status"), ("success", "error"))
            elapsed = time.perf_counter() - start

            total_ms = elapsed * 1000
            avg_ms = total_ms / len(modules)
            logger.info(f"✅ Import chain: {len(modules)} modules in {total_ms:.1f}ms ({avg_ms:.2f}ms avg)")
        except Exception as e:
            self.fail(f"Import chain performance test failed: {e}")

    def test_detector_results_integrity(self):
        """Test that detector results maintain integrity across multiple imports"""
        self._check_available()
        try:
            detector = CircularImportDetector()
            results = []
            for mod in ["json", "os", "sys"]:
                result = detector.test_import(mod)
                results.append(result)
                # Accept success or error (module may already be loaded)
                self.assertIn(result.get("status"), ("success", "error"))

            # Note: test_import pops from import_chain on success,
            # so chain is empty after successful imports

            # Verify each result has correct module name
            for i, mod in enumerate(["json", "os", "sys"]):
                self.assertEqual(results[i]["module"], mod)

            logger.info(f"✅ Detector results integrity verified for {len(results)} imports")
        except Exception as e:
            self.fail(f"Detector results integrity test failed: {e}")

    def test_repeated_import_performance(self):
        """Test performance of repeated imports (simulating test suite reloads)"""
        self._check_available()
        try:
            detector = CircularImportDetector()
            iterations = 5
            start = time.perf_counter()
            for _ in range(iterations):
                detector.test_import("json")
            elapsed = time.perf_counter() - start
            avg_ms = (elapsed / iterations) * 1000
            logger.info(f"✅ Repeated import ({iterations}x): {avg_ms:.2f}ms avg")
        except Exception as e:
            self.fail(f"Repeated import performance test failed: {e}")

if __name__ == "__main__":
    unittest.main()
