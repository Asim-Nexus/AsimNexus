
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Tavily Search Integration
===================================
Tavily API for web search
Includes: Real-time search, news search, academic search
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("TavilySearch")


class SearchType(Enum):
    """Types of search"""
    GENERAL = "general"
    NEWS = "news"
    ACADEMIC = "academic"
    IMAGES = "images"


@dataclass
class SearchResult:
    """Search result item"""
    result_id: str
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[datetime]
    source: str


@dataclass
class SearchQuery:
    """Search query"""
    query_id: str
    query: str
    search_type: SearchType
    max_results: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TavilySearch:
    """Tavily search integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"
        self.queries: Dict[str, SearchQuery] = {}
        self.results: Dict[str, List[SearchResult]] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Tavily search"""
        logger.info("🔍 Initializing Tavily Search Integration...")
        logger.info("🌐 Setting up real-time search")
        logger.info("📰 Setting up news search")
        logger.info("📚 Setting up academic search")
        logger.info("✅ Tavily Search Integration initialized")
    
    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.GENERAL,
        max_results: int = 10
    ) -> List[SearchResult]:
        """Perform search query"""
        if not self.api_key:
            logger.warning("Tavily API key not configured")
            return []
        
        search_query = SearchQuery(
            query_id=f"query_{uuid.uuid4().hex[:8]}",
            query=query,
            search_type=search_type,
            max_results=max_results
        )
        
        self.queries[search_query.query_id] = search_query
        
        # Prepare request
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced"
        }
        
        # Add search type specific parameters
        if search_type == SearchType.NEWS:
            payload["include_domains"] = ["news.google.com", "bbc.com", "cnn.com"]
        elif search_type == SearchType.ACADEMIC:
            payload["include_domains"] = ["scholar.google.com", "arxiv.org", "researchgate.net"]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_results(data)
                        self.results[search_query.query_id] = results
                        logger.info(f"✅ Search completed: {len(results)} results")
                        return results
                    else:
                        logger.error(f"Search failed with status: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _parse_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse search results"""
        results = []
        
        for item in data.get("results", []):
            result = SearchResult(
                result_id=f"res_{uuid.uuid4().hex[:8]}",
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                score=item.get("score", 0.0),
                published_date=None,
                source="tavily"
            )
            results.append(result)
        
        return results
    
    def get_query_results(self, query_id: str) -> Optional[List[SearchResult]]:
        """Get results for a query"""
        return self.results.get(query_id)
    
    def get_recent_queries(self, limit: int = 10) -> List[SearchQuery]:
        """Get recent queries"""
        sorted_queries = sorted(self.queries.values(), key=lambda x: x.timestamp, reverse=True)
        return sorted_queries[:limit]


# Global instance
_tavily_search: Optional[TavilySearch] = None


def get_tavily_search() -> TavilySearch:
    """Get singleton instance"""
    global _tavily_search
    if _tavily_search is None:
        _tavily_search = TavilySearch()
    return _tavily_search
