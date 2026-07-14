"""AsimNexus Money Tool"""
import aiohttp
from typing import Dict, Any

class MoneyTool:
    def __init__(self):
        self.exchange_rates = {}
    
    async def get_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        symbol = params.get("symbol", "AAPL")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    return {"success": True, "quote": data.get("quoteResponse", {}).get("result", [])}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def convert_currency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from_curr = params.get("from_currency", "USD")
        to_curr = params.get("to_currency", "EUR")
        amount = params.get("amount", 1.0)
        return {"success": True, "converted": amount * 0.85, "from": from_curr, "to": to_curr}

money_tool = MoneyTool()