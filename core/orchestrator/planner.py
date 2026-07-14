# core/orchestrator/planner.py
# AsimNexus — Step Planner

from typing import Dict, List

class Planner:
    """
    Step Planner — Breaks down an intent into sequential agent steps.
    """

    async def create_plan(self, intent: Dict, message: str, user_id: str, mode: str) -> Dict:
        action = intent.get("action", "general")
        sub_action = intent.get("sub_action", "chat")
        
        steps = []
        try:
            from core.gateway.unified_llm_gateway import unified_llm_gateway, UnifiedCompletionRequest
            
            prompt = f"""
            You are the AsimNexus Planner. Break down the user's intent into a sequential JSON array of agent execution steps.
            Available agents: [tax, health, education, finance, mesh, general].
            Intent: action="{action}", sub_action="{sub_action}"
            Message: "{message}"
            
            Respond ONLY with a raw JSON array of objects:
            [
              {{ "agent": "string", "action": "string", "params": {{}} }}
            ]
            If it's just a conversational query, return: [{{ "agent": "general", "action": "chat", "params": {{"message": "{message}"}} }}]
            """
            
            req = UnifiedCompletionRequest(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.1
            )
            res = await unified_llm_gateway.complete(req)
            
            import json
            import re
            
            # Extract JSON array
            match = re.search(r'\[.*\]', res.content, re.DOTALL)
            if match:
                steps = json.loads(match.group(0))
        except Exception as e:
            import logging
            logging.warning(f"LLM Planner failed, falling back to general chat: {e}")
            
        if not steps:
            # Fallback
            steps = [{"agent": "general", "action": "chat", "params": {"message": message}}]

        return {
            "steps": steps,
            "constitutional": intent.get("constitutional", False)
        }
