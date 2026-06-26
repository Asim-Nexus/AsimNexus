"""AsimNexus File Read Tool"""
import asyncio
from pathlib import Path
from typing import Dict, Any

class FileReadTool:
    async def read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = params.get("path")
        max_lines = params.get("max_lines", 1000)
        
        try:
            fp = Path(path)
            if not fp.exists():
                return {"success": False, "error": "File not found"}
            
            text = fp.read_text(encoding="utf-8", errors="ignore")
            lines = text.split("\n")[:max_lines]
            return {"success": True, "content": "\n".join(lines), "lines": len(lines)}
        except Exception as e:
            return {"success": False, "error": str(e)}

file_read_tool = FileReadTool()