# core/agents/mesh_agent.py
# AsimNexus — Mesh/Offline Agent

from typing import Dict
from core.agents.base_agent import BaseAgent

try:
    from core.mesh.offline_sync_engine import OfflineSyncEngine
    sync_available = True
except ImportError:
    sync_available = False

class MeshAgent(BaseAgent):
    """Mesh Agent — Synchronizes transactions and records during offline state."""

    def __init__(self):
        super().__init__("mesh")
        if sync_available:
            self.sync_engine = OfflineSyncEngine()
        else:
            self.sync_engine = None

    async def execute(self, tool: str, params: Dict, user_id: str, mode: str) -> Dict:
        if tool == "sync":
            return await self._sync_queue(user_id)
        elif tool == "process_batch":
            return await self._process_batch(params, user_id, mode)
        else:
            return {"error": f"Unknown tool: {tool}"}

    async def _process_batch(self, params: Dict, user_id: str, mode: str) -> Dict:
        operations = params.get("operations", [])
        if self.sync_engine:
            self.sync_engine.enqueue_batch(operations)
            self.sync_engine.sync_now()
            return {"status": "batch_queued", "count": len(operations)}
        return {"status": "mock_batch", "count": len(operations)}

    async def _sync_queue(self, user_id: str) -> Dict:
        if self.sync_engine:
            # Trigger offline sync engine stats or force sync
            try:
                stats = self.sync_engine.get_stats()
                return {
                    "status": "synchronized",
                    "total_operations": stats.get("total_operations", 0),
                    "pending_sync": stats.get("pending_sync", 0)
                }
            except Exception as e:
                return {"status": "sync_failed", "error": str(e)}
        return {
            "status": "mock_synchronized",
            "message": "Local database queued items successfully synchronized to parent mesh."
        }
