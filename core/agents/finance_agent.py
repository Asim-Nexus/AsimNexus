# core/agents/finance_agent.py
# AsimNexus — Finance Agent

from typing import Dict
from core.agents.base_agent import BaseAgent
from core.gateway.unified_gateway import UnifiedGateway

class FinanceAgent(BaseAgent):
    """Finance Agent — Processes payments and token transfers."""

    def __init__(self):
        super().__init__("finance")
        self.gateway = UnifiedGateway()

    async def execute(self, tool: str, params: Dict, user_id: str, mode: str) -> Dict:
        if tool == "transfer":
            return await self._transfer(user_id, params)
        else:
            return {"error": f"Unknown tool: {tool}"}

    async def _transfer(self, user_id: str, params: Dict) -> Dict:
        amount = params.get("amount", 1000)
        bank = params.get("bank", "Nabil Bank")
        # Call bank api via unified gateway
        result = await self.gateway.call("bank", "process_transfer", "POST", {"user_id": user_id, "amount": amount, "bank": bank})
        return {
            "status": "success",
            "transaction_id": result.get("tx_id", "TXN-8812739"),
            "amount": amount,
            "bank": bank,
            "currency": "NPR"
        }
