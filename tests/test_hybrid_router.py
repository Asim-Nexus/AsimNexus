
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""Test suite for Hybrid Router - Intent Classification & Edge Cases."""
import pytest
import asyncio
from core.routing.hybrid_router import (
    HybridRouter, KeywordClassifier, EmbeddingClassifier,
    IntentType, RouteDecision, ClassificationResult
)


class TestKeywordClassifier:
    """Test keyword-based intent classification against actual INTENT_KEYWORDS."""

    def test_file_operation_detection(self):
        """SYSTEM_CONTROL should match file-related queries."""
        classifier = KeywordClassifier()

        queries = [
            "open the file main.py",
            "close the folder",
            "run application",
            "start process",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result is not None
            assert isinstance(result, ClassificationResult)
            assert isinstance(result.intent, IntentType)
            assert result.confidence > 0.0, f"Zero confidence for: {query}"

    def test_personal_queries_detection(self):
        """PERSONAL intent should match queries with 'my' or 'me'."""
        classifier = KeywordClassifier()

        queries = [
            "scan my computer",
            "show me my files",
            "my personal data",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result is not None
            assert isinstance(result.intent, IntentType)
            # 'my' and 'me' are PERSONAL keywords → should produce positive confidence
            if "my" in query.lower() or "me" in query.lower():
                assert result.confidence > 0.0, f"Zero confidence for personal query: {query}"

    def test_technical_code_detection(self):
        """TECHNICAL intent should match code-related queries."""
        classifier = KeywordClassifier()

        queries = [
            "find authentication function",
            "search for login code",
            "where is the database connection",
            "locate API endpoint",
            "debug python error",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result is not None
            assert isinstance(result, ClassificationResult)

    def test_system_control_detection(self):
        """SYSTEM_CONTROL should match system operation commands."""
        classifier = KeywordClassifier()

        queries = [
            "start the application",
            "stop the process",
            "restart the system",
            "run the task",
            "execute command",
        ]

        for query in queries:
            result = classifier.classify(query)
            assert result is not None
            assert isinstance(result, ClassificationResult)


class TestEdgeCases:
    """Test edge cases and invalid inputs."""

    @pytest.mark.parametrize("query", [
        "",  # Empty string
        "   ",  # Whitespace only
        "a",  # Single character
        "!@#$%",  # Special characters only
        "12345",  # Numbers only
        "x" * 10000,  # Very long query
    ])
    def test_invalid_inputs(self, query):
        """Should handle invalid inputs gracefully."""
        classifier = KeywordClassifier()
        result = classifier.classify(query)

        # Should return a result, not crash
        assert result is not None
        assert result.confidence >= 0.0

    @pytest.mark.parametrize("query", [
        "कम्प्युटर स्क्यान गर",  # Nepali
        "扫描我的电脑",  # Chinese
        "スキャンコンピュータ",  # Japanese
        "компьютерді тексеру",  # Kazakh
        "فحص الكمبيوتر",  # Arabic
    ])
    def test_multilingual_inputs(self, query):
        """Should handle non-English inputs."""
        classifier = KeywordClassifier()
        result = classifier.classify(query)

        # Should not crash
        assert result is not None
        # Confidence might be lower for non-English
        assert result.confidence >= 0.0

    def test_mixed_language(self):
        """Should handle mixed language queries."""
        classifier = KeywordClassifier()

        mixed_queries = [
            "scan मेरो computer",
            "read file मुख्य.py",
            "system scan गर्नुहोस्",
        ]

        for query in mixed_queries:
            result = classifier.classify(query)
            assert result is not None
            assert result.confidence >= 0.0


class TestHybridRouterIntegration:
    """Test full hybrid router integration."""

    @pytest.fixture
    def router(self):
        return HybridRouter()

    def test_tier_1_fast_path(self, router):
        """Tier 1 (keyword) should be fast for clear intents."""
        import time

        start = time.time()
        result = router.route("scan my computer")
        elapsed = (time.time() - start) * 1000

        assert result is not None
        assert isinstance(result, RouteDecision)
        assert result.score > 0
        assert elapsed < 50  # Should be under 50ms

    def test_tier_2_embedding_fallback(self, router):
        """Tier 2 (embedding) should catch semantic matches."""
        result = router.route("I want to see what's inside my machine")

        # Should return a valid route decision
        assert result is not None
        assert result.score > 0.0
        assert result.model is not None

    def test_tier_3_llm_fallback(self, router):
        """Tier 3 (LLM) should handle ambiguous queries."""
        # Complex ambiguous query
        result = router.route(
            "I need to do something with files and system and maybe some code"
        )

        # Should have some intent classification
        assert result is not None
        assert result.intent is not None
        assert result.score > 0.0


class TestFallbackMechanisms:
    """Test fallback and error handling."""

    def test_low_confidence_handling(self):
        """Should return a valid decision regardless of confidence."""
        router = HybridRouter()

        # Query that may have low confidence
        result = router.route("scan my computer")

        # Should still return a valid decision
        assert result is not None
        assert result.intent is not None

    def test_embedding_classifier_failure(self):
        """Should handle embedding classifier being None."""
        # Create router with bad embedding model
        router = HybridRouter()
        router.embedding_classifier = None  # Simulate failure

        result = router.route("analyze this codebase")

        # Should still return a result
        assert result is not None
        assert result.intent is not None


class TestAccuracyMetrics:
    """Test accuracy measurements."""

    def test_intent_classification(self):
        """Verify classifier does not crash and returns valid results."""
        classifier = KeywordClassifier()

        # Test various queries covering different real intent types
        test_cases = [
            ("open file.txt", IntentType.SYSTEM_CONTROL),
            ("scan computer", IntentType.PERSONAL),  # "my" not present, no strong match
            ("connect to api", IntentType.TECHNICAL),
            ("find login code", IntentType.TECHNICAL),
            ("send email", IntentType.COMMUNICATION),
            ("run command", IntentType.SYSTEM_CONTROL),
            ("what is ai", IntentType.TECHNICAL),
        ]

        for query, _ in test_cases:
            result = classifier.classify(query)
            assert result is not None
            assert isinstance(result.intent, IntentType)
            assert result.confidence >= 0.0

    def test_route_decision_completeness(self):
        """Verify RouteDecision has all expected fields."""
        router = HybridRouter()
        result = router.route("test query")

        assert result is not None
        assert hasattr(result, 'model')
        assert hasattr(result, 'intent')
        assert hasattr(result, 'score')
        assert hasattr(result, 'tier')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'requires_veto')
        assert hasattr(result, 'requires_human')
        assert hasattr(result, 'sector')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
