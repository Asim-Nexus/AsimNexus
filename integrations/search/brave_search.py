
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Brave Search Integration
===================================
Brave Search API for private web search
Includes: Private search, no tracking, real-time results
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("BraveSearch")


class SearchFreshness(Enum):
    """Search freshness options"""
    ALL = "all"
    DAY = "pd"
    WEEK = "pw"
    MONTH = "pm"


@dataclass
class BraveResult:
    """Brave search result"""
    result_id: str
    title: str
    url: str
    description: str
    published_date: Optional[datetime]
    source: str


@dataclass
class BraveQuery:
    """Brave search query"""
    query_id: str
    query: str
    freshness: SearchFreshness
    count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BraveSearch:
    """Brave search integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.queries: Dict[str, BraveQuery] = {}
        self.results: Dict[str, List[BraveResult]] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Brave search"""
        logger.info("🦁 Initializing Brave Search Integration...")
        logger.info("🔍 Setting up private search")
        logger.info("🛡️  Setting up no-tracking search")
        logger.info("⚡ Setting up real-time results")
        logger.info("✅ Brave Search Integration initialized")
    
    async def search(
        self,
        query: str,
        freshness: SearchFreshness = SearchFreshness.ALL,
        count: int = 10
    ) -> List[BraveResult]:
        """Perform private search"""
        if not self.api_key:
            logger.warning("Brave API key not configured")
            return []
        
        search_query = BraveQuery(
            query_id=f"query_{uuid.uuid4().hex[:8]}",
            query=query,
            freshness=freshness,
            count=count
        )
        
        self.queries[search_query.query_id] = search_query
        
        # Prepare request
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": count,
            "freshness": freshness.value
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_results(data)
                        self.results[search_query.query_id] = results
                        logger.info(f"✅ Brave search completed: {len(results)} results")
                        return results
                    else:
                        logger.error(f"Search failed with status: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _parse_results(self, data: Dict[str, Any]) -> List[BraveResult]:
        """Parse search results"""
        results = []
        
        for item in data.get("web", {}).get("results", []):
            result = BraveResult(
                result_id=f"res_{uuid.uuid4().hex[:8]}",
                title=item.get("title", ""),
                url=item.get("url", ""),
                description=item.get("description", ""),
                published_date=None,
                source="brave"
            )
            results.append(result)
        
        return results
    
    def get_query_results(self, query_id: str) -> Optional[List[BraveResult]]:
        """Get results for a query"""
        return self.results.get(query_id)
    
    def get_recent_queries(self, limit: int = 10) -> List[BraveQuery]:
        """Get recent queries"""
        sorted_queries = sorted(self.queries.values(), key=lambda x: x.timestamp, reverse=True)
        return sorted_queries[:limit]


# Global instance
_brave_search: Optional[BraveSearch] = None


def get_brave_search() -> BraveSearch:
    """Get singleton instance"""
    global _brave_search
    if _brave_search is None:
        _brave_search = BraveSearch()
    return _brave_search
