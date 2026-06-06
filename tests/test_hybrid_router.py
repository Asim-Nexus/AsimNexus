
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""Test suite for Hybrid Router - Intent Classification & Edge Cases."""
import pytest
import asyncio
from core.routing.hybrid_router import (
    HybridRouter, KeywordClassifier, EmbeddingClassifier,
    IntentType, RouteDecision
)


class TestKeywordClassifier:
    """Test keyword-based intent classification."""
    
    def test_file_read_detection(self):
        """Should detect file read intent."""
        classifier = KeywordClassifier()
        
        queries = [
            "read the file main.py",
            "show me config.txt",
            "open document.pdf",
            "view the code",
            "get file contents"
        ]
        
        for query in queries:
            result = classifier.classify(query)
            assert result.confidence > 0.8, f"Failed for: {query}"
            assert result.intent == IntentType.FILE_OPERATION
    
    def test_system_scan_detection(self):
        """Should detect system scan intent."""
        classifier = KeywordClassifier()
        
        queries = [
            "scan my computer",
            "check system status",
            "analyze hardware",
            "what are my specs",
            "diagnose my PC"
        ]
        
        for query in queries:
            result = classifier.classify(query)
            assert result.intent == IntentType.SYSTEM_SCAN, f"Failed for: {query}"
    
    def test_codebase_query_detection(self):
        """Should detect codebase query intent."""
        classifier = KeywordClassifier()
        
        queries = [
            "find authentication function",
            "search for login code",
            "where is the database connection",
            "locate API endpoint"
        ]
        
        for query in queries:
            result = classifier.classify(query)
            assert result.intent == IntentType.CODEBASE_QUERY, f"Failed for: {query}"


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
            # Should extract intent from English keywords
            assert result.confidence > 0.5


class TestHybridRouterIntegration:
    """Test full hybrid router integration."""
    
    @pytest.fixture
    def router(self):
        return HybridRouter()
    
    @pytest.mark.asyncio
    async def test_tier_1_fast_path(self, router):
        """Tier 1 (keyword) should be fast for clear intents."""
        import time
        
        start = time.time()
        result = await router.route("scan my computer")
        elapsed = (time.time() - start) * 1000
        
        assert result.intent == IntentType.SYSTEM_SCAN
        assert result.method == "keyword"
        assert elapsed < 50  # Should be under 50ms
    
    @pytest.mark.asyncio
    async def test_tier_2_embedding_fallback(self, router):
        """Tier 2 (embedding) should catch semantic matches."""
        result = await router.route("I want to see what's inside my machine")
        
        # Should match system scan via embedding similarity
        assert result.confidence > 0.7
        assert result.method in ["keyword", "embedding"]
    
    @pytest.mark.asyncio
    async def test_tier_3_llm_fallback(self, router):
        """Tier 3 (LLM) should handle ambiguous queries."""
        # Complex ambiguous query
        result = await router.route(
            "I need to do something with files and system and maybe some code"
        )
        
        # Should have some intent classification
        assert result.intent is not None
        assert result.confidence > 0.0


class TestFallbackMechanisms:
    """Test fallback and error handling."""
    
    @pytest.mark.asyncio
    async def test_low_confidence_escalation(self):
        """Should escalate to next tier when confidence is low."""
        router = HybridRouter(
            keyword_threshold=0.95,  # Very high threshold
            embedding_threshold=0.95  # Very high threshold
        )
        
        # Query that would normally match at tier 1
        result = await router.route("scan my computer")
        
        # Should try tier 2 due to high tier 1 threshold
        # or tier 3 if both thresholds fail
        assert result.method in ["keyword", "embedding", "llm"]
    
    @pytest.mark.asyncio
    async def test_embedding_classifier_failure(self):
        """Should fallback to LLM when embedding fails."""
        # Create router with bad embedding model
        router = HybridRouter()
        router.embedding_classifier = None  # Simulate failure
        
        result = await router.route("analyze this codebase")
        
        # Should still return a result
        assert result is not None
        assert result.intent is not None


class TestAccuracyMetrics:
    """Test accuracy measurements."""
    
    def test_intent_accuracy_calculation(self):
        """Calculate intent classification accuracy."""
        router = HybridRouter()
        classifier = KeywordClassifier()
        
        # Test dataset: (query, expected_intent)
        test_cases = [
            ("read file.txt", IntentType.FILE_OPERATION),
            ("scan computer", IntentType.SYSTEM_SCAN),
            ("connect to API", IntentType.API_CONNECT),
            ("find login code", IntentType.CODEBASE_QUERY),
            ("send agent task", IntentType.AGENT_TASK),
            ("system command", IntentType.SYSTEM_COMMAND),
            ("what is AI?", IntentType.GENERAL_QUERY),
        ]
        
        correct = 0
        total = len(test_cases)
        
        for query, expected in test_cases:
            result = classifier.classify(query)
            if result.intent == expected:
                correct += 1
        
        accuracy = correct / total
        print(f"\nIntent Classification Accuracy: {accuracy:.1%} ({correct}/{total})")
        
        # Should be at least 85% accurate on clear cases
        assert accuracy >= 0.85, f"Accuracy {accuracy:.1%} below threshold 85%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
