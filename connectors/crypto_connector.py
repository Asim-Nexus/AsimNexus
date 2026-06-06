
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS CoinGecko Connector
============================
Connector for CoinGecko API
Provides integration with CoinGecko for cryptocurrency prices and data
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("CryptoConnector")

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed. Install with: pip install requests")


class Currency(Enum):
    """Fiat currencies"""
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    JPY = "jpy"
    INR = "inr"
    NPR = "npr"


class CryptoConnector:
    """
    CoinGecko Connector
    
    Provides:
    - Get cryptocurrency prices
    - Get market data
    - Get historical data
    - Get exchange rates
    - Search cryptocurrencies
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("CryptoConnector")
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.default_currency = Currency.USD
        
        if REQUESTS_AVAILABLE:
            self.logger.info("CoinGecko connector initialized")
        else:
            self.logger.warning("CoinGecko connector not available")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return REQUESTS_AVAILABLE
    
    async def get_price(
        self,
        coin_id: str,
        currency: Optional[Currency] = None
    ) -> Optional[float]:
        """
        Get current price of a cryptocurrency
        
        Args:
            coin_id: Coin ID (e.g., 'bitcoin', 'ethereum')
            currency: Fiat currency
            
        Returns:
            Current price
        """
        if not self.is_available():
            self.logger.warning("CoinGecko connector not available")
            return None
        
        try:
            params = {
                "ids": coin_id,
                "vs_currencies": (currency or self.default_currency).value
            }
            
            if self.api_key:
                params["x_cg_demo_api_key"] = self.api_key
            
            response = requests.get(f"{self.base_url}/simple/price", params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get(coin_id, {}).get((currency or self.default_currency).value)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch price: {e}")
            return None
    
    async def get_prices(
        self,
        coin_ids: List[str],
        currency: Optional[Currency] = None
    ) -> Optional[Dict]:
        """
        Get current prices of multiple cryptocurrencies
        
        Args:
            coin_ids: List of coin IDs
            currency: Fiat currency
            
        Returns:
            Dictionary with prices
        """
        if not self.is_available():
            self.logger.warning("CoinGecko connector not available")
            return None
        
        try:
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": (currency or self.default_currency).value
            }
            
            if self.api_key:
                params["x_cg_demo_api_key"] = self.api_key
            
            response = requests.get(f"{self.base_url}/simple/price", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch prices: {e}")
            return None
    
    async def get_market_data(
        self,
        coin_id: str,
        currency: Optional[Currency] = None
    ) -> Optional[Dict]:
        """
        Get market data for a cryptocurrency
        
        Args:
            coin_id: Coin ID
            currency: Fiat currency
            
        Returns:
            Market data dictionary
        """
        if not self.is_available():
            self.logger.warning("CoinGecko connector not available")
            return None
        
        try:
            params = {
                "vs_currency": (currency or self.default_currency).value
            }
            
            if self.api_key:
                params["x_cg_demo_api_key"] = self.api_key
            
            response = requests.get(f"{self.base_url}/coins/{coin_id}", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch market data: {e}")
            return None
    
    async def get_top_coins(
        self,
        limit: int = 100,
        currency: Optional[Currency] = None
    ) -> Optional[List[Dict]]:
        """
        Get top cryptocurrencies by market cap
        
        Args:
            limit: Number of coins to return
            currency: Fiat currency
            
        Returns:
            List of coin data
        """
        if not self.is_available():
            self.logger.warning("CoinGecko connector not available")
            return None
        
        try:
            params = {
                "vs_currency": (currency or self.default_currency).value,
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false"
            }
            
            if self.api_key:
                params["x_cg_demo_api_key"] = self.api_key
            
            response = requests.get(f"{self.base_url}/coins/markets", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch top coins: {e}")
            return None
    
    async def search_coins(self, query: str) -> Optional[List[Dict]]:
        """
        Search for cryptocurrencies
        
        Args:
            query: Search query
            
        Returns:
            List of matching coins
        """
        if not self.is_available():
            self.logger.warning("CoinGecko connector not available")
            return None
        
        try:
            response = requests.get(f"{self.base_url}/search", params={"query": query})
            response.raise_for_status()
            
            data = response.json()
            return data.get("coins", [])
            
        except Exception as e:
            self.logger.error(f"Failed to search coins: {e}")
            return None
    
    async def get_historical_data(
        self,
        coin_id: str,
        days: int = 30,
        currency: Optional[Currency] = None
    ) -> Optional[Dict]:
        """
        Get historical price data
        
        Args:
            coin_id: Coin ID
            days: Number of days
            currency: Fiat currency
            
        Returns:
            Historical data
        """
        if not self.is_available():
            self.logger.warning("CoinGecko connector not available")
            return None
        
        try:
            params = {
                "vs_currency": (currency or self.default_currency).value,
                "days": days
            }
            
            if self.api_key:
                params["x_cg_demo_api_key"] = self.api_key
            
            response = requests.get(f"{self.base_url}/coins/{coin_id}/market_chart", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to fetch historical data: {e}")
            return None
    
    def format_coin_data(self, coin: Dict) -> Dict:
        """Format coin data for display"""
        return {
            "id": coin.get("id", ""),
            "name": coin.get("name", ""),
            "symbol": coin.get("symbol", "").upper(),
            "current_price": coin.get("current_price", 0),
            "market_cap": coin.get("market_cap", 0),
            "market_cap_rank": coin.get("market_cap_rank", 0),
            "price_change_24h": coin.get("price_change_percentage_24h", 0),
            "price_change_7d": coin.get("price_change_percentage_7d_in_currency", 0),
            "image": coin.get("image", ""),
            "last_updated": coin.get("last_updated", "")
        }
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "requests_installed": REQUESTS_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "default_currency": self.default_currency.value
        }
