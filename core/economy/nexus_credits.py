
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Nexus Credits Token System
===================================
Token system for the ASIMNEXUS economy
Includes: Token minting, transfers, burning, staking rewards
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os

logger = logging.getLogger("NexusCredits")


class TransactionType(Enum):
    """Transaction types"""
    MINT = "mint"
    TRANSFER = "transfer"
    BURN = "burn"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"


@dataclass
class Transaction:
    """Token transaction"""
    tx_id: str
    tx_type: TransactionType
    from_address: str
    to_address: str
    amount: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenBalance:
    """Token balance for an address"""
    address: str
    balance: float
    staked: float = 0.0
    total_earned: float = 0.0


class NexusCreditsSystem:
    """Nexus Credits Token System"""
    
    def __init__(self):
        self.balances: Dict[str, TokenBalance] = {}
        self.transactions: List[Transaction] = []
        self.total_supply: float = 0.0
        self.staking_rate: float = 0.05  # 5% annual reward
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize token system"""
        logger.info("💎 Initializing Nexus Credits Token System...")
        logger.info("🪙 Setting up token minting")
        logger.info("💸 Setting up transfers")
        logger.info("🔥 Setting up burning")
        logger.info("📈 Setting up staking rewards")
        logger.info("✅ Nexus Credits Token System initialized")
    
    def mint_tokens(self, address: str, amount: float) -> bool:
        """Mint new tokens to address"""
        if amount <= 0:
            return False
        
        if address not in self.balances:
            self.balances[address] = TokenBalance(address=address, balance=0.0)
        
        self.balances[address].balance += amount
        self.total_supply += amount
        
        tx = Transaction(
            tx_id=f"tx_{uuid.uuid4().hex[:8]}",
            tx_type=TransactionType.MINT,
            from_address="SYSTEM",
            to_address=address,
            amount=amount
        )
        self.transactions.append(tx)
        
        logger.info(f"✅ Minted {amount} tokens to {address}")
        return True
    
    def transfer_tokens(self, from_address: str, to_address: str, amount: float) -> bool:
        """Transfer tokens between addresses"""
        if amount <= 0:
            return False
        
        if from_address not in self.balances or self.balances[from_address].balance < amount:
            return False
        
        if to_address not in self.balances:
            self.balances[to_address] = TokenBalance(address=to_address, balance=0.0)
        
        self.balances[from_address].balance -= amount
        self.balances[to_address].balance += amount
        
        tx = Transaction(
            tx_id=f"tx_{uuid.uuid4().hex[:8]}",
            tx_type=TransactionType.TRANSFER,
            from_address=from_address,
            to_address=to_address,
            amount=amount
        )
        self.transactions.append(tx)
        
        logger.info(f"✅ Transferred {amount} tokens from {from_address} to {to_address}")
        return True
    
    def burn_tokens(self, address: str, amount: float) -> bool:
        """Burn tokens from address"""
        if amount <= 0:
            return False
        
        if address not in self.balances or self.balances[address].balance < amount:
            return False
        
        self.balances[address].balance -= amount
        self.total_supply -= amount
        
        tx = Transaction(
            tx_id=f"tx_{uuid.uuid4().hex[:8]}",
            tx_type=TransactionType.BURN,
            from_address=address,
            to_address="SYSTEM",
            amount=amount
        )
        self.transactions.append(tx)
        
        logger.info(f"✅ Burned {amount} tokens from {address}")
        return True
    
    def stake_tokens(self, address: str, amount: float) -> bool:
        """Stake tokens for rewards"""
        if amount <= 0:
            return False
        
        if address not in self.balances or self.balances[address].balance < amount:
            return False
        
        self.balances[address].balance -= amount
        self.balances[address].staked += amount
        
        tx = Transaction(
            tx_id=f"tx_{uuid.uuid4().hex[:8]}",
            tx_type=TransactionType.STAKE,
            from_address=address,
            to_address="STAKE_CONTRACT",
            amount=amount
        )
        self.transactions.append(tx)
        
        logger.info(f"✅ Staked {amount} tokens from {address}")
        return True
    
    def unstake_tokens(self, address: str, amount: float) -> bool:
        """Unstake tokens"""
        if amount <= 0:
            return False
        
        if address not in self.balances or self.balances[address].staked < amount:
            return False
        
        self.balances[address].staked -= amount
        self.balances[address].balance += amount
        
        tx = Transaction(
            tx_id=f"tx_{uuid.uuid4().hex[:8]}",
            tx_type=TransactionType.UNSTAKE,
            from_address="STAKE_CONTRACT",
            to_address=address,
            amount=amount
        )
        self.transactions.append(tx)
        
        logger.info(f"✅ Unstaked {amount} tokens to {address}")
        return True
    
    def distribute_rewards(self) -> None:
        """Distribute staking rewards"""
        for address, balance in self.balances.items():
            if balance.staked > 0:
                reward = balance.staked * self.staking_rate / 365  # Daily reward
                balance.balance += reward
                balance.total_earned += reward
                
                tx = Transaction(
                    tx_id=f"tx_{uuid.uuid4().hex[:8]}",
                    tx_type=TransactionType.REWARD,
                    from_address="STAKE_CONTRACT",
                    to_address=address,
                    amount=reward
                )
                self.transactions.append(tx)
        
        logger.info("✅ Distributed staking rewards")
    
    def get_balance(self, address: str) -> Optional[TokenBalance]:
        """Get balance for address"""
        return self.balances.get(address)
    
    def get_total_supply(self) -> float:
        """Get total token supply"""
        return self.total_supply
    
    def get_transaction_history(self, address: str, limit: int = 10) -> List[Transaction]:
        """Get transaction history for address"""
        related = [
            tx for tx in self.transactions
            if tx.from_address == address or tx.to_address == address
        ]
        return related[-limit:]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        total_staked = sum(b.staked for b in self.balances.values())
        total_earned = sum(b.total_earned for b in self.balances.values())
        
        tx_counts = {}
        for tx in self.transactions:
            tx_counts[tx.tx_type.value] = tx_counts.get(tx.tx_type.value, 0) + 1
        
        return {
            "total_supply": self.total_supply,
            "total_addresses": len(self.balances),
            "total_staked": total_staked,
            "total_rewards_distributed": total_earned,
            "transaction_counts": tx_counts,
            "staking_rate": self.staking_rate
        }


# Global instance
_nexus_credits: Optional[NexusCreditsSystem] = None


def get_nexus_credits() -> NexusCreditsSystem:
    """Get singleton instance"""
    global _nexus_credits
    if _nexus_credits is None:
        _nexus_credits = NexusCreditsSystem()
    return _nexus_credits
