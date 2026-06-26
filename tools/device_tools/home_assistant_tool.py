"""AsimNexus Home Assistant Tool"""
import aiohttp
from typing import Dict, Any, Optional

class HomeAssistantTool:
    def __init__(self, api_url: str = "http://localhost:8123", token: str = ""):
        self.api_url = api_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async def control_entity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = params.get("entity_id")
        action = params.get("action", "turn_on")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/api/services/{entity_id.split('.')[0]}/{action}"
                async with session.post(url, headers=self.headers, json={}) as resp:
                    return {"success": resp.status == 200, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_state(self, params: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = params.get("entity_id")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/api/states/{entity_id}"
                async with session.get(url, headers=self.headers) as resp:
                    data = await resp.json()
                    return {"success": True, "state": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

home_assistant_tool = HomeAssistantTool()