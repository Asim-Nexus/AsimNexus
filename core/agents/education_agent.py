# core/agents/education_agent.py
# AsimNexus — Education Agent

import json
from typing import Dict
from core.agents.base_agent import BaseAgent
from core.gateway.unified_gateway import UnifiedGateway
from core.gateway.unified_llm_gateway import UnifiedLLMGateway, UnifiedCompletionRequest

class EducationAgent(BaseAgent):
    """Education Agent — Handles university and school registrations and certificates."""

    def __init__(self):
        super().__init__("education")
        self.gateway = UnifiedGateway()
        self.llm_gateway = UnifiedLLMGateway()

    async def execute(self, tool: str, params: Dict, user_id: str, mode: str) -> Dict:
        if tool == "get_certificate":
            return await self._get_certificate(user_id, params)
        elif tool == "evaluate_equivalency":
            return await self._evaluate_equivalency(params.get("degree", ""), params.get("university", ""))
        else:
            return {"error": f"Unknown tool: {tool}"}

    async def _get_certificate(self, user_id: str, params: Dict) -> Dict:
        university = params.get("university", "Tribhuvan University")
        # Call university API via unified gateway
        result = await self.gateway.call("university", "verify_degree", "POST", {"user_id": user_id, "university": university})
        return {
            "user_id": user_id,
            "university": university,
            "status": "verified",
            "degree": result.get("degree", "Bachelor of Computer Science"),
            "certificate_hash": result.get("hash", "CERT-8877A")
        }

    async def _evaluate_equivalency(self, degree: str, university: str) -> Dict:
        if not degree or not university:
            return {"error": "Degree or University missing"}
            
        prompt = f"""
        You are the AsimNexus Education Agent. Evaluate the equivalency of a '{degree}' from '{university}' in the context of the Nepal Education Board.
        
        Provide a JSON response containing 'equivalent_level' (e.g., Bachelor, Master) and 'recognized' (boolean).
        Respond ONLY with the JSON object.
        """
        try:
            await self.llm_gateway.initialize()
            response = await self.llm_gateway.complete(
                UnifiedCompletionRequest(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
            )
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            result = json.loads(content)
            return result
        except Exception as e:
            return {"equivalent_level": "Unknown", "recognized": False, "error": str(e)}
