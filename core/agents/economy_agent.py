
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Economy Agent
=======================
Simple financial tracking and budget summary support for MVP.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("EconomyAgent")


@dataclass
class Transaction:
    amount: float
    category: str
    transaction_type: str
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "category": self.category,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
        }


class EconomyAgent:
    """Basic economy agent for MVP."""

    def __init__(self) -> None:
        self.transactions: List[Transaction] = []

    def add_income(self, amount: float, category: str = "income", description: str = "") -> None:
        self.transactions.append(Transaction(amount=amount, category=category, transaction_type="income", description=description))
        logger.info(f"Recorded income: {amount} ({category})")

    def add_expense(self, amount: float, category: str = "expense", description: str = "") -> None:
        self.transactions.append(Transaction(amount=-abs(amount), category=category, transaction_type="expense", description=description))
        logger.info(f"Recorded expense: {amount} ({category})")

    def get_balance(self) -> float:
        return sum(t.amount for t in self.transactions)

    def get_budget_summary(self) -> Dict[str, Any]:
        income = sum(t.amount for t in self.transactions if t.amount >= 0)
        expense = -sum(t.amount for t in self.transactions if t.amount < 0)
        categories: Dict[str, float] = {}

        for t in self.transactions:
            categories.setdefault(t.category, 0.0)
            categories[t.category] += t.amount

        return {
            "balance": self.get_balance(),
            "total_income": income,
            "total_expense": expense,
            "category_breakdown": categories,
            "transaction_count": len(self.transactions),
        }


economy_agent: EconomyAgent = EconomyAgent()


def initialize_economy_agent() -> bool:
    global economy_agent
    if economy_agent is None:
        economy_agent = EconomyAgent()
    return True
