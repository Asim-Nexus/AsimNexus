"""
ASIMNEXUS Human-Agent Hybrid Economy
===================================
Full REAL implementation with JSONL persistence.
Supports User Mode, Agent Mode, and Hybrid Mode.

Features:
- Mode switching (User/Agent/Hybrid)
- Task creation and assignment
- Balance management for users and agents
- Revenue sharing between humans and agents
- JSONL append-only persistence
"""

import json
import logging
import uuid
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger("HybridEconomy")

HYBRID_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "hybrid_economy.jsonl"
HYBRID_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class EconomyMode(Enum):
    USER_MODE = "user_mode"
    AGENT_USER_MODE = "agent_user_mode"
    HYBRID = "hybrid"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    task_id: str
    description: str
    requester_id: str
    executor_id: Optional[str]
    reward: float
    reward_currency: str
    status: str
    category: str
    created_at: str
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(**data)


@dataclass
class EconomyAccount:
    account_id: str
    owner_id: str
    owner_type: str
    balance: float = 0.0
    reserved_balance: float = 0.0
    tasks_completed: int = 0
    tasks_created: int = 0
    total_earned: float = 0.0
    total_spent: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EconomyAccount":
        return cls(**data)


@dataclass
class RevenueShareRule:
    rule_id: str
    human_id: str
    agent_id: str
    human_share_pct: float
    agent_share_pct: float
    active: bool = True
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RevenueShareRule":
        return cls(**data)


class HybridEconomy:
    def __init__(self):
        self.current_mode: EconomyMode = EconomyMode.USER_MODE
        self.tasks: Dict[str, Task] = {}
        self.accounts: Dict[str, EconomyAccount] = {}
        self.revenue_rules: Dict[str, RevenueShareRule] = {}
        self._load_from_db()

    def _persist(self, entry_type: str, data: Dict[str, Any]) -> None:
        try:
            record = {"__type__": entry_type, **data}
            with open(HYBRID_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Persist failed: {e}")

    def _load_from_db(self) -> None:
        path = HYBRID_DB_PATH
        if not path.exists():
            logger.info("✅ Hybrid Economy initialized (no existing data)")
            return
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    entry_type = data.pop("__type__", None)
                    if entry_type == "mode":
                        try:
                            self.current_mode = EconomyMode(data.get("mode", "user_mode"))
                        except ValueError:
                            pass
                    elif entry_type == "account":
                        acc = EconomyAccount.from_dict(data)
                        self.accounts[acc.account_id] = acc
                    elif entry_type == "task":
                        task = Task.from_dict(data)
                        self.tasks[task.task_id] = task
                    elif entry_type == "revenue_rule":
                        rule = RevenueShareRule.from_dict(data)
                        self.revenue_rules[rule.rule_id] = rule
            logger.info(f"✅ Hybrid Economy loaded: {len(self.accounts)} accounts, {len(self.tasks)} tasks")
        except Exception as e:
            logger.warning(f"Failed to load hybrid economy: {e}")

    def set_mode(self, mode: EconomyMode) -> Dict[str, Any]:
        old = self.current_mode
        self.current_mode = mode
        self._persist("mode", {"mode": mode.value, "old_mode": old.value, "timestamp": datetime.utcnow().isoformat()})
        logger.info(f"💼 Economy mode: {old.value} -> {mode.value}")
        return {"success": True, "previous_mode": old.value, "current_mode": mode.value}

    def create_account(self, owner_id: str, owner_type: str, initial_balance: float = 0.0) -> EconomyAccount:
        if owner_type not in ("user", "agent"):
            raise ValueError("owner_type must be 'user' or 'agent'")
        for acc in self.accounts.values():
            if acc.owner_id == owner_id and acc.owner_type == owner_type:
                return acc
        account = EconomyAccount(
            account_id=f"acc_{uuid.uuid4().hex[:12]}",
            owner_id=owner_id,
            owner_type=owner_type,
            balance=initial_balance,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        self.accounts[account.account_id] = account
        self._persist("account", account.to_dict())
        logger.info(f"✅ Created {owner_type} account: {owner_id}")
        return account

    def get_account(self, owner_id: str, owner_type: Optional[str] = None) -> Optional[EconomyAccount]:
        for acc in self.accounts.values():
            if acc.owner_id == owner_id:
                if owner_type is None or acc.owner_type == owner_type:
                    return acc
        return None

    def deposit(self, owner_id: str, amount: float, memo: str = "") -> Dict[str, Any]:
        account = self.get_account(owner_id)
        if not account:
            return {"success": False, "error": "Account not found"}
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        account.balance += amount
        account.total_earned += amount
        account.updated_at = datetime.utcnow().isoformat()
        self._persist("account", account.to_dict())
        self._persist("transaction", {
            "type": "deposit", "owner_id": owner_id, "amount": amount,
            "memo": memo, "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"💰 Deposited {amount} to {owner_id}")
        return {"success": True, "owner_id": owner_id, "amount": amount, "new_balance": account.balance}

    def withdraw(self, owner_id: str, amount: float, memo: str = "") -> Dict[str, Any]:
        account = self.get_account(owner_id)
        if not account:
            return {"success": False, "error": "Account not found"}
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        if account.balance - account.reserved_balance < amount:
            return {"success": False, "error": "Insufficient available balance"}
        account.balance -= amount
        account.total_spent += amount
        account.updated_at = datetime.utcnow().isoformat()
        self._persist("account", account.to_dict())
        self._persist("transaction", {
            "type": "withdraw", "owner_id": owner_id, "amount": amount,
            "memo": memo, "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"💸 Withdrew {amount} from {owner_id}")
        return {"success": True, "owner_id": owner_id, "amount": amount, "new_balance": account.balance}

    def transfer(self, from_id: str, to_id: str, amount: float, memo: str = "") -> Dict[str, Any]:
        from_acc = self.get_account(from_id)
        to_acc = self.get_account(to_id)
        if not from_acc:
            return {"success": False, "error": f"Sender {from_id} not found"}
        if not to_acc:
            return {"success": False, "error": f"Receiver {to_id} not found"}
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        if from_acc.balance - from_acc.reserved_balance < amount:
            return {"success": False, "error": "Insufficient available balance"}
        from_acc.balance -= amount
        from_acc.total_spent += amount
        from_acc.updated_at = datetime.utcnow().isoformat()
        to_acc.balance += amount
        to_acc.total_earned += amount
        to_acc.updated_at = datetime.utcnow().isoformat()
        self._persist("account", from_acc.to_dict())
        self._persist("account", to_acc.to_dict())
        self._persist("transaction", {
            "type": "transfer", "from_id": from_id, "to_id": to_id,
            "amount": amount, "memo": memo, "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"🔄 Transferred {amount} from {from_id} to {to_id}")
        return {"success": True, "from_id": from_id, "to_id": to_id, "amount": amount,
                "sender_balance": from_acc.balance, "receiver_balance": to_acc.balance}

    def create_task(self, description: str, requester_id: str, reward: float,
                    category: str = "general", reward_currency: str = "NPR",
                    metadata: Dict[str, Any] = None) -> Task:
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            description=description,
            requester_id=requester_id,
            executor_id=None,
            reward=reward,
            reward_currency=reward_currency,
            status=TaskStatus.PENDING.value,
            category=category,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self.tasks[task.task_id] = task
        account = self.get_account(requester_id)
        if account:
            account.tasks_created += 1
            account.updated_at = datetime.utcnow().isoformat()
            self._persist("account", account.to_dict())
        self._persist("task", task.to_dict())
        logger.info(f"📋 Task created: {task.task_id} — {description[:50]}")
        return task

    def assign_task(self, task_id: str, executor_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        task = self.tasks[task_id]
        if task.status != TaskStatus.PENDING.value:
            return {"success": False, "error": f"Task is {task.status}, not pending"}
        task.executor_id = executor_id
        task.status = TaskStatus.ASSIGNED.value
        self._persist("task", task.to_dict())
        logger.info(f"✅ Task {task_id} assigned to {executor_id}")
        return {"success": True, "task_id": task_id, "executor_id": executor_id}

    def start_task(self, task_id: str, executor_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        task = self.tasks[task_id]
        if task.executor_id != executor_id:
            return {"success": False, "error": "Not assigned to you"}
        if task.status != TaskStatus.ASSIGNED.value:
            return {"success": False, "error": f"Task is {task.status}, not assigned"}
        task.status = TaskStatus.IN_PROGRESS.value
        self._persist("task", task.to_dict())
        logger.info(f"▶️ Task {task_id} started by {executor_id}")
        return {"success": True}

    def complete_task(self, task_id: str, executor_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        task = self.tasks[task_id]
        if task.executor_id != executor_id:
            return {"success": False, "error": "Not assigned to you"}
        if task.status not in (TaskStatus.IN_PROGRESS.value, TaskStatus.ASSIGNED.value):
            return {"success": False, "error": f"Task is {task.status}, cannot complete"}
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.utcnow().isoformat()
        executor_acc = self.get_account(executor_id)
        if executor_acc:
            executor_acc.balance += task.reward
            executor_acc.total_earned += task.reward
            executor_acc.tasks_completed += 1
            executor_acc.updated_at = datetime.utcnow().isoformat()
            self._persist("account", executor_acc.to_dict())
        requester_acc = self.get_account(task.requester_id)
        if requester_acc:
            requester_acc.balance -= task.reward
            requester_acc.total_spent += task.reward
            requester_acc.updated_at = datetime.utcnow().isoformat()
            self._persist("account", requester_acc.to_dict())
        self._persist("task", task.to_dict())
        logger.info(f"🎉 Task {task_id} completed — reward: {task.reward}")
        return {"success": True, "task_id": task_id, "reward": task.reward, "executor_id": executor_id}

    def fail_task(self, task_id: str, reason: str = "") -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED.value
        self._persist("task", task.to_dict())
        logger.info(f"❌ Task {task_id} failed: {reason}")
        return {"success": True, "task_id": task_id}

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED.value
        self._persist("task", task.to_dict())
        logger.info(f"🗑️ Task {task_id} cancelled")
        return {"success": True}

    def set_revenue_share(self, human_id: str, agent_id: str,
                          human_share_pct: float, agent_share_pct: float) -> RevenueShareRule:
        if human_share_pct + agent_share_pct != 100.0:
            raise ValueError("Shares must sum to 100")
        rule = RevenueShareRule(
            rule_id=f"rule_{uuid.uuid4().hex[:12]}",
            human_id=human_id,
            agent_id=agent_id,
            human_share_pct=human_share_pct,
            agent_share_pct=agent_share_pct,
            created_at=datetime.utcnow().isoformat(),
        )
        self.revenue_rules[rule.rule_id] = rule
        self._persist("revenue_rule", rule.to_dict())
        logger.info(f"📊 Revenue share: {human_id} {human_share_pct}% / {agent_id} {agent_share_pct}%")
        return rule

    def get_tasks(self, status: Optional[str] = None, category: Optional[str] = None,
                  requester_id: Optional[str] = None, executor_id: Optional[str] = None,
                  limit: int = 50) -> List[Dict[str, Any]]:
        result = list(self.tasks.values())
        if status:
            result = [t for t in result if t.status == status]
        if category:
            result = [t for t in result if t.category == category]
        if requester_id:
            result = [t for t in result if t.requester_id == requester_id]
        if executor_id:
            result = [t for t in result if t.executor_id == executor_id]
        result.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in result[:limit]]

    def get_accounts(self, owner_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if owner_type:
            return [a.to_dict() for a in self.accounts.values() if a.owner_type == owner_type]
        return [a.to_dict() for a in self.accounts.values()]

    def get_economy_summary(self) -> Dict[str, Any]:
        total_balance = sum(a.balance for a in self.accounts.values())
        total_reserved = sum(a.reserved_balance for a in self.accounts.values())
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED.value)
        pending_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING.value)
        total_earned = sum(a.total_earned for a in self.accounts.values())
        total_spent = sum(a.total_spent for a in self.accounts.values())
        user_accounts = sum(1 for a in self.accounts.values() if a.owner_type == "user")
        agent_accounts = sum(1 for a in self.accounts.values() if a.owner_type == "agent")
        return {
            "current_mode": self.current_mode.value,
            "total_accounts": len(self.accounts),
            "user_accounts": user_accounts,
            "agent_accounts": agent_accounts,
            "total_balance": total_balance,
            "total_reserved": total_reserved,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "active_tasks": sum(1 for t in self.tasks.values() if t.status in (
                TaskStatus.ASSIGNED.value, TaskStatus.IN_PROGRESS.value)),
            "failed_tasks": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED.value),
            "revenue_rules": len(self.revenue_rules),
        }


_hybrid_economy: Optional[HybridEconomy] = None


def get_hybrid_economy() -> HybridEconomy:
    global _hybrid_economy
    if _hybrid_economy is None:
        _hybrid_economy = HybridEconomy()
    return _hybrid_economy


def reset_hybrid_economy() -> None:
    global _hybrid_economy
    _hybrid_economy = None
