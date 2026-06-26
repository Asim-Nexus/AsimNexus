"""AsimNexus File Edit Tool"""
import asyncio
from pathlib import Path
from typing import Dict, Any

class FileEditTool:
    async def write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = params.get("path")
        content = params.get("content", "")
        
        try:
            fp = Path(path)
            fp.write_text(content, encoding="utf-8")
            return {"success": True, "bytes_written": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def append(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = params.get("path")
        content = params.get("content", "")
        
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "bytes_appended": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

file_edit_tool = FileEditTool()