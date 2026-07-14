# core/agents/general_agent.py
import logging
from typing import Dict, Any

try:
    from core.gateway.unified_llm_gateway import unified_llm_gateway, UnifiedCompletionRequest
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

class GeneralAgent:
    """
    General Agent — Uses the Unified LLM Gateway to respond to general conversational inputs.
    """
    async def execute(self, action: str, params: Dict[str, Any], user_id: str, mode: str) -> Dict[str, Any]:
        message = params.get("message", "")
        if not message:
            return {"status": "error", "message": "No message provided."}
            
        if not LLM_AVAILABLE or not unified_llm_gateway:
            return {
                "status": "success", 
                "response": f"I am AsimNexus (LLM Gateway Offline). I received your message: '{message}' in {mode} mode."
            }

        try:
            req = UnifiedCompletionRequest(
                messages=[
                    {"role": "system", "content": f"You are AsimNexus, the World OS of Nepal. You are currently talking to a {mode}. Be helpful, extremely futuristic, but concise."},
                    {"role": "user", "content": message}
                ],
                max_tokens=500
            )
            response = await unified_llm_gateway.generate_completion(req)
            return {"status": "success", "response": response.content}
        except Exception as e:
            logger.error(f"GeneralAgent LLM error: {e}")
            return {
                "status": "error",
                "response": f"I am AsimNexus. I encountered a neural core error: {e}"
            }
