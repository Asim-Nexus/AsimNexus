"""
AsimNexus — Hybrid Router
==========================
Multi-tier intent classification and routing system with keyword, embedding,
and LLM fallback mechanisms.
"""

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class IntentType(Enum):
    SYSTEM_CONTROL = "system_control"
    PERSONAL = "personal"
    TECHNICAL = "technical"
    COMMUNICATION = "communication"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of intent classification."""
    intent: IntentType
    confidence: float
    matched_keywords: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteDecision:
    """Decision from the hybrid router."""
    model: str
    intent: IntentType
    score: float
    tier: int
    reason: str
    requires_veto: bool = False
    requires_human: bool = False
    sector: str = "general"


# Intent keyword mappings
INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
    IntentType.SYSTEM_CONTROL: [
        "open", "close", "run", "start", "stop", "restart", "execute",
        "launch", "terminate", "kill", "boot", "shutdown", "command",
    ],
    IntentType.PERSONAL: [
        "my", "me", "mine", "personal", "profile", "account", "settings",
        "preferences", "private",
    ],
    IntentType.TECHNICAL: [
        "code", "function", "api", "database", "debug", "compile",
        "deploy", "config", "algorithm", "query", "find", "search",
        "locate", "where", "authentication", "login", "connection",
    ],
    IntentType.COMMUNICATION: [
        "send", "email", "message", "chat", "call", "notify",
        "broadcast", "share", "contact",
    ],
}


class KeywordClassifier:
    """Classifies intent using keyword matching."""

    def classify(self, query: str) -> ClassificationResult:
        """Classify a query by matching keywords."""
        if not query or not query.strip():
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                matched_keywords=[]
            )

        query_lower = query.lower()
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        best_keywords: List[str] = []

        for intent, keywords in INTENT_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in query_lower]
            if matched:
                score = len(matched) / max(len(keywords), 1)
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    best_keywords = matched

        # Boost confidence for exact matches
        confidence = min(best_score + 0.1, 1.0)

        return ClassificationResult(
            intent=best_intent,
            confidence=confidence,
            matched_keywords=best_keywords
        )


class EmbeddingClassifier:
    """Fallback classifier using embedding similarity."""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the embedding model."""
        self._initialized = True

    def classify(self, query: str) -> ClassificationResult:
        """Classify using embedding similarity (simulated)."""
        if not query or not query.strip():
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0
            )

        query_lower = query.lower()

        # Simple semantic matching
        semantic_patterns = {
            IntentType.SYSTEM_CONTROL: [
                r"\b(?:system|process|application|task)\b",
                r"\b(?:start|stop|run|execute)\b",
            ],
            IntentType.PERSONAL: [
                r"\b(?:my|mine|personal|own)\b",
                r"\b(?:profile|account|settings)\b",
            ],
            IntentType.TECHNICAL: [
                r"\b(?:code|program|software|tech)\b",
                r"\b(?:analyze|debug|compile|deploy)\b",
            ],
            IntentType.COMMUNICATION: [
                r"\b(?:send|message|email|contact)\b",
                r"\b(?:notify|broadcast|share)\b",
            ],
        }

        best_intent = IntentType.UNKNOWN
        best_score = 0.0

        for intent, patterns in semantic_patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 0.3
            if score > best_score:
                best_score = score
                best_intent = intent

        return ClassificationResult(
            intent=best_intent,
            confidence=min(best_score, 1.0)
        )


class HybridRouter:
    """Multi-tier router combining keyword, embedding, and LLM classification."""

    def __init__(self):
        self.keyword_classifier = KeywordClassifier()
        self.embedding_classifier = EmbeddingClassifier()

    def route(self, query: str) -> RouteDecision:
        """Route a query through the hybrid classification tiers."""
        if not query or not query.strip():
            return RouteDecision(
                model="keyword",
                intent=IntentType.UNKNOWN,
                score=0.0,
                tier=1,
                reason="Empty query"
            )

        # Tier 1: Fast keyword matching
        keyword_result = self.keyword_classifier.classify(query)
        if keyword_result.confidence >= 0.5:
            return RouteDecision(
                model="keyword",
                intent=keyword_result.intent,
                score=keyword_result.confidence,
                tier=1,
                reason=f"Keyword match: {', '.join(keyword_result.matched_keywords)}"
            )

        # Tier 2: Embedding-based classification
        if self.embedding_classifier:
            embedding_result = self.embedding_classifier.classify(query)
            if embedding_result.confidence >= 0.3:
                return RouteDecision(
                    model="embedding",
                    intent=embedding_result.intent,
                    score=embedding_result.confidence,
                    tier=2,
                    reason="Semantic embedding match"
                )

        # Tier 3: LLM fallback (simulated)
        return RouteDecision(
            model="llm",
            intent=keyword_result.intent,
            score=max(keyword_result.confidence, 0.1),
            tier=3,
            reason="LLM fallback classification"
        )
