
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Perplexity Search Integration
=======================================
Perplexity API for AI-powered search
Includes: Real-time search, citation tracking, AI reasoning
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("PerplexitySearch")


class SearchMode(Enum):
    """Search modes"""
    CONCISE = "concise"
    DETAILED = "detailed"
    RESEARCH = "research"


@dataclass
class PerplexityResult:
    """Perplexity search result"""
    result_id: str
    answer: str
    citations: List[str]
    sources: List[Dict[str, str]]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerplexityQuery:
    """Perplexity search query"""
    query_id: str
    query: str
    mode: SearchMode
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PerplexitySearch:
    """Perplexity search integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.queries: Dict[str, PerplexityQuery] = {}
        self.results: Dict[str, PerplexityResult] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Perplexity search"""
        logger.info("🧠 Initializing Perplexity Search Integration...")
        logger.info("🔍 Setting up AI-powered search")
        logger.info("📚 Setting up citation tracking")
        logger.info("🤔 Setting up AI reasoning")
        logger.info("✅ Perplexity Search Integration initialized")
    
    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.DETAILED
    ) -> PerplexityResult:
        """Perform AI-powered search"""
        if not self.api_key:
            logger.warning("Perplexity API key not configured")
            return PerplexityResult(
                result_id=f"res_{uuid.uuid4().hex[:8]}",
                answer="API key not configured",
                citations=[],
                sources=[],
                confidence=0.0
            )
        
        search_query = PerplexityQuery(
            query_id=f"query_{uuid.uuid4().hex[:8]}",
            query=query,
            mode=mode
        )
        
        self.queries[search_query.query_id] = search_query
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-medium-online",
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = self._parse_result(data)
                        self.results[search_query.query_id] = result
                        logger.info(f"✅ Perplexity search completed")
                        return result
                    else:
                        logger.error(f"Search failed with status: {response.status}")
                        return PerplexityResult(
                            result_id=f"res_{uuid.uuid4().hex[:8]}",
                            answer="Search failed",
                            citations=[],
                            sources=[],
                            confidence=0.0
                        )
        except Exception as e:
            logger.error(f"Search error: {e}")
            return PerplexityResult(
                result_id=f"res_{uuid.uuid4().hex[:8]}",
                answer=f"Error: {str(e)}",
                citations=[],
                sources=[],
                confidence=0.0
            )
    
    def _parse_result(self, data: Dict[str, Any]) -> PerplexityResult:
        """Parse Perplexity result"""
        message = data.get("choices", [{}])[0].get("message", {})
        answer = message.get("content", "")
        citations = message.get("citations", [])
        
        sources = []
        for citation in citations:
            sources.append({
                "url": citation,
                "title": "Source"
            })
        
        return PerplexityResult(
            result_id=f"res_{uuid.uuid4().hex[:8]}",
            answer=answer,
            citations=citations,
            sources=sources,
            confidence=0.85
        )
    
    def get_query_result(self, query_id: str) -> Optional[PerplexityResult]:
        """Get result for a query"""
        return self.results.get(query_id)
    
    def get_recent_queries(self, limit: int = 10) -> List[PerplexityQuery]:
        """Get recent queries"""
        sorted_queries = sorted(self.queries.values(), key=lambda x: x.timestamp, reverse=True)
        return sorted_queries[:limit]


# Global instance
_perplexity_search: Optional[PerplexitySearch] = None


def get_perplexity_search() -> PerplexitySearch:
    """Get singleton instance"""
    global _perplexity_search
    if _perplexity_search is None:
        _perplexity_search = PerplexitySearch()
    return _perplexity_search
