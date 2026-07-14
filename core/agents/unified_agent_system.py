
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified Agent System
===================================
Minimal checkpoint and restore support for agent state management.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("UnifiedAgentSystem")


@dataclass
class AgentCheckpoint:
    checkpoint_id: str
    agent_id: str
    agent_type: str
    state_data: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state_data": self.state_data,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCheckpoint":
        return cls(
            checkpoint_id=data["checkpoint_id"],
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            state_data=data["state_data"],
            created_at=data["created_at"],
        )


class UnifiedAgentSystem:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_path = Path(storage_dir or Path.cwd() / "agent_checkpoints")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.checkpoints: Dict[str, AgentCheckpoint] = {}

    async def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"UnifiedAgentSystem initialized with storage: {self.storage_path}")

    async def checkpoint(self, agent_id: str, agent_type: str, state_data: Dict[str, Any]) -> str:
        checkpoint_id = f"{agent_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        checkpoint = AgentCheckpoint(
            checkpoint_id=checkpoint_id,
            agent_id=agent_id,
            agent_type=agent_type,
            state_data=state_data,
            created_at=datetime.utcnow().isoformat(),
        )
        file_path = self.storage_path / f"{checkpoint_id}.json"
        file_path.write_text(json.dumps(checkpoint.to_dict(), indent=2), encoding="utf-8")
        self.checkpoints[checkpoint_id] = checkpoint
        logger.info(f"Saved checkpoint {checkpoint_id} for {agent_id}")
        return checkpoint_id

    async def restore(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        if checkpoint_id in self.checkpoints:
            return self.checkpoints[checkpoint_id]

        file_path = self.storage_path / f"{checkpoint_id}.json"
        if not file_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return None

        data = json.loads(file_path.read_text(encoding="utf-8"))
        checkpoint = AgentCheckpoint.from_dict(data)
        self.checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    async def restore_latest(self, agent_id: str) -> Optional[AgentCheckpoint]:
        matching = []
        for file_path in sorted(self.storage_path.glob(f"{agent_id}_*.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                matching.append(AgentCheckpoint.from_dict(data))
            except Exception as exc:
                logger.warning(f"Failed to load checkpoint {file_path}: {exc}")

        if not matching:
            return None

        latest = sorted(matching, key=lambda cp: cp.created_at)[-1]
        self.checkpoints[latest.checkpoint_id] = latest
        return latest
