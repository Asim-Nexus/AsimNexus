# core/agents/tax_agent.py
# AsimNexus — Tax Agent

import json
from typing import Dict
from core.agents.base_agent import BaseAgent
from core.gateway.unified_gateway import UnifiedGateway
from core.gateway.unified_llm_gateway import UnifiedLLMGateway, UnifiedCompletionRequest

class TaxAgent(BaseAgent):
    """Tax Agent — Calculates tax and files it via government services."""
    
    def __init__(self):
        super().__init__("tax")
        self.gateway = UnifiedGateway()
        self.llm_gateway = UnifiedLLMGateway()
        
    async def execute(self, tool: str, params: Dict, user_id: str, mode: str) -> Dict:
        if tool == "calculate":
            return await self._calculate(user_id, params, mode)
        elif tool == "file":
            return await self._file_tax(user_id, params)
        else:
            return {"error": f"Unknown tool: {tool}"}
            
    async def _calculate(self, user_id: str, params: Dict, mode: str) -> Dict:
        income = params.get("income", 50000)
        
        # Use LLM to calculate tax based on complex logic and rules
        prompt = f"""
        You are the AsimNexus Tax Agent for Nepal. Calculate the tax for an income of {income} NPR. 
        If the mode is 'company', apply a flat 25% corporate tax. 
        If the mode is 'citizen', apply a 1% social security tax for the first 500k, and 10% for the rest.
        Current mode: {mode}.
        
        Respond ONLY with a valid JSON object containing: 'tax_amount' (number) and 'breakdown' (string explanation).
        """
        
        try:
            await self.llm_gateway.initialize()
            response = await self.llm_gateway.complete(
                UnifiedCompletionRequest(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
            )
            
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            
            result = json.loads(content)
            tax = result.get("tax_amount", 0)
            breakdown = result.get("breakdown", "Tax calculation")
        except Exception as e:
            # Fallback
            tax = float(income) * 0.1
            breakdown = f"Fallback calculation error: {str(e)}"
            
        return {"income": income, "tax_amount": tax, "currency": "NPR", "breakdown": breakdown}
        
    async def _file_tax(self, user_id: str, params: Dict) -> Dict:
        # File via UnifiedGateway simulated government call
        result = await self.gateway.call("ird", "tax_file", "POST", {"user_id": user_id, "amount": params.get("tax_amount", 5000)})
        return {"status": "filed", "receipt_id": result.get("receipt_id", "TAX-2026-001"), "details": result}
