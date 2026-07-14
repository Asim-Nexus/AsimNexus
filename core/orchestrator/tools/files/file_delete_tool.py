"""AsimNexus File Delete Tool"""
import asyncio
from pathlib import Path
from typing import Dict, Any

class FileDeleteTool:
    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = params.get("path")
        confirm = params.get("confirm", False)
        
        if not confirm:
            return {"success": False, "error": "Confirmation required"}
        
        try:
            fp = Path(path)
            if fp.exists():
                fp.unlink()
                return {"success": True, "deleted": str(path)}
            return {"success": False, "error": "File not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

file_delete_tool = FileDeleteTool()