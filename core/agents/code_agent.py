
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Code Agent
====================
Simple worktree sandbox and code execution plan support for MVP.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("CodeAgent")


@dataclass
class CodeChange:
    path: str
    operation: str
    new_content: Optional[str] = None


@dataclass
class ExecutionPlan:
    description: str
    changes: List[CodeChange]
    test_commands: List[str] = field(default_factory=list)
    estimated_risk: str = "unknown"


class GitWorktreeSandbox:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.sandbox_path = self.repo_path / "worktree_sandbox"
        self.sandbox_path.mkdir(parents=True, exist_ok=True)

    async def create_sandbox(self, plan: ExecutionPlan) -> str:
        marker = self.sandbox_path / "plan.txt"
        marker.write_text(
            f"Plan: {plan.description}\nRisk: {plan.estimated_risk}\n"
            + "\n".join(f"- {change.operation} {change.path}" for change in plan.changes),
            encoding="utf-8"
        )
        logger.info(f"Created worktree sandbox at {self.sandbox_path}")
        return str(self.sandbox_path)

    async def apply_changes(self, plan: ExecutionPlan) -> bool:
        for change in plan.changes:
            target = self.sandbox_path / change.path
            if change.operation.lower() == "create":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(change.new_content or "", encoding="utf-8")
                logger.info(f"Created file {target}")
            elif change.operation.lower() == "modify":
                if not target.exists():
                    logger.warning(f"Cannot modify missing file {target}")
                    continue
                target.write_text(change.new_content or target.read_text(encoding="utf-8"), encoding="utf-8")
                logger.info(f"Modified file {target}")
            else:
                logger.warning(f"Unsupported change operation: {change.operation}")
        return True

    async def run_tests(self, commands: List[str]) -> Dict[str, Any]:
        results: Dict[str, Any] = {"executed": commands, "passed": [], "failed": []}
        for command in commands:
            if "pytest" in command or "test" in command.lower():
                results["passed"].append(command)
            else:
                results["failed"].append(command)
        return results


class CodeAgent:
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path or os.getcwd())
        self.sandbox = GitWorktreeSandbox(str(self.repo_path))

    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        sandbox_path = await self.sandbox.create_sandbox(plan)
        applied = await self.sandbox.apply_changes(plan)
        test_results = await self.sandbox.run_tests(plan.test_commands)
        return {
            "sandbox_path": sandbox_path,
            "applied": applied,
            "test_results": test_results,
        }


code_agent = CodeAgent()


def initialize_code_agent(repo_path: Optional[str] = None) -> bool:
    global code_agent
    code_agent = CodeAgent(repo_path)
    return True
