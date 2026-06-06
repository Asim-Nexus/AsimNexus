
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS NewsAPI Connector
============================
Connector for NewsAPI
Provides integration with NewsAPI for fetching news articles
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("NewsConnector")

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed. Install with: pip install requests")


class NewsCategory(Enum):
    """News categories"""
    GENERAL = "general"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    SCIENCE = "science"
    SPORTS = "sports"
    TECHNOLOGY = "technology"


class NewsConnector:
    """
    NewsAPI Connector
    
    Provides:
    - Fetch latest news
    - Search news by topic
    - Filter by category
    - Filter by country
    - Filter by source
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("NewsConnector")
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.default_country = "us"
        self.default_language = "en"
        
        if REQUESTS_AVAILABLE and api_key:
            self.logger.info("NewsAPI connector initialized")
        else:
            self.logger.warning("NewsAPI connector not available")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return REQUESTS_AVAILABLE and self.api_key is not None
    
    async def get_top_headlines(
        self,
        country: Optional[str] = None,
        category: Optional[NewsCategory] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict]:
        """
        Get top headlines
        
        Args:
            country: Country code (e.g., 'us', 'uk', 'np')
            category: News category
            page: Page number
            page_size: Number of articles per page
            
        Returns:
            Dictionary with articles
        """
        if not self.is_available():
            self.logger.warning("NewsAPI connector not available")
            return None
        
        try:
            params = {
                "apiKey": self.api_key,
                "country": country or self.default_country,
                "page": page,
                "pageSize": page_size
            }
            
            if category:
                params["category"] = category.value
            
            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch top headlines: {e}")
            return None
    
    async def search_news(
        self,
        query: str,
        language: Optional[str] = None,
        sort_by: str = "publishedAt",
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict]:
        """
        Search news by query
        
        Args:
            query: Search query
            language: Language code (e.g., 'en', 'ne')
            sort_by: Sort order (publishedAt, popularity, relevancy)
            page: Page number
            page_size: Number of articles per page
            
        Returns:
            Dictionary with articles
        """
        if not self.is_available():
            self.logger.warning("NewsAPI connector not available")
            return None
        
        try:
            params = {
                "apiKey": self.api_key,
                "q": query,
                "language": language or self.default_language,
                "sortBy": sort_by,
                "page": page,
                "pageSize": page_size
            }
            
            response = requests.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to search news: {e}")
            return None
    
    async def get_sources(
        self,
        category: Optional[NewsCategory] = None,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get available news sources
        
        Args:
            category: Filter by category
            language: Filter by language
            country: Filter by country
            
        Returns:
            Dictionary with sources
        """
        if not self.is_available():
            self.logger.warning("NewsAPI connector not available")
            return None
        
        try:
            params = {
                "apiKey": self.api_key,
                "language": language or self.default_language,
                "country": country or self.default_country
            }
            
            if category:
                params["category"] = category.value
            
            response = requests.get(f"{self.base_url}/top-headlines/sources", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch sources: {e}")
            return None
    
    async def get_news_by_source(
        self,
        sources: List[str],
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict]:
        """
        Get news from specific sources
        
        Args:
            sources: List of source IDs
            page: Page number
            page_size: Number of articles per page
            
        Returns:
            Dictionary with articles
        """
        if not self.is_available():
            self.logger.warning("NewsAPI connector not available")
            return None
        
        try:
            params = {
                "apiKey": self.api_key,
                "sources": ",".join(sources),
                "page": page,
                "pageSize": page_size
            }
            
            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch news by source: {e}")
            return None
    
    def format_article(self, article: Dict) -> Dict:
        """Format article for display"""
        return {
            "title": article.get("title", "No title"),
            "description": article.get("description", "No description"),
            "url": article.get("url", ""),
            "url_to_image": article.get("urlToImage", ""),
            "published_at": article.get("publishedAt", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "author": article.get("author", "Unknown")
        }
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "requests_installed": REQUESTS_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "default_country": self.default_country,
            "default_language": self.default_language
        }
