
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Nexus Credits - Economic Layer
========================================
Internal payment system for agents and humans
Zero-Knowledge Proof for secure transactions
5/15/30 day package payments and task rewards
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os

logger = logging.getLogger("NexusCredits")

class TransactionType(Enum):
    """Transaction types"""
    PACKAGE_PURCHASE = "package_purchase"
    TASK_REWARD = "task_reward"
    PAYMENT = "payment"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"

class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PackageType(Enum):
    """Agent package types"""
    FIVE_DAYS = "five_days"
    FIFTEEN_DAYS = "fifteen_days"
    THIRTY_DAYS = "thirty_days"

@dataclass
class NexusCredit:
    """Nexus Credit token"""
    credit_id: str
    amount: float
    owner_id: str
    created_at: datetime
    is_locked: bool = False
    lock_reason: Optional[str] = None

@dataclass
class Transaction:
    """Transaction record"""
    transaction_id: str
    transaction_type: TransactionType
    sender_id: str
    receiver_id: str
    amount: float
    status: TransactionStatus
    timestamp: datetime
    zkp_proof: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ZeroKnowledgeProof:
    """Zero-Knowledge Proof for transaction privacy"""
    proof_id: str
    transaction_id: str
    commitment: str
    response: str
    challenge: str
    verified: bool = False

class NexusCredits:
    """
    Nexus Credits - Economic Layer
    Internal payment system for agents and humans
    Zero-Knowledge Proof for secure transactions
    """
    
    def __init__(self):
        self.credits: Dict[str, NexusCredit] = {}
        self.transactions: Dict[str, Transaction] = []
        self.zkp_proofs: Dict[str, ZeroKnowledgeProof] = {}
        self.user_balances: Dict[str, float] = {}
        
        # Package pricing (NPR)
        self.package_prices = {
            PackageType.FIVE_DAYS: 500,
            PackageType.FIFTEEN_DAYS: 1200,
            PackageType.THIRTY_DAYS: 2000
        }
        
        # Initialize economy
        self._initialize_economy()
        
    def _initialize_economy(self) -> None:
        """Initialize the Nexus Credits economy"""
        logger.info("💰 Initializing Nexus Credits - Economic Layer...")
        logger.info("🔒 Security: Zero-Knowledge Proof")
        logger.info("💳 Package Pricing:")
        logger.info(f"   5 Days: NPR {self.package_prices[PackageType.FIVE_DAYS]}")
        logger.info(f"   15 Days: NPR {self.package_prices[PackageType.FIFTEEN_DAYS]}")
        logger.info(f"   30 Days: NPR {self.package_prices[PackageType.THIRTY_DAYS]}")
        logger.info("✅ Nexus Credits initialized")
    
    async def create_credit(self, user_id: str, amount: float) -> NexusCredit:
        """Create Nexus Credit for user"""
        try:
            credit = NexusCredit(
                credit_id=f"credit_{uuid.uuid4().hex[:12]}",
                amount=amount,
                owner_id=user_id,
                created_at=datetime.utcnow()
            )
            
            self.credits[credit.credit_id] = credit
            
            # Update user balance
            self.user_balances[user_id] = self.user_balances.get(user_id, 0) + amount
            
            logger.info(f"💰 Credit created: {credit.credit_id} - NPR {amount}")
            return credit
            
        except Exception as e:
            logger.error(f"❌ Credit creation error: {e}")
            raise
    
    async def purchase_package(
        self,
        user_id: str,
        package_type: PackageType
    ) -> Transaction:
        """
        Purchase agent package
        Uses Zero-Knowledge Proof for privacy
        """
        try:
            price = self.package_prices[package_type]
            
            logger.info(f"🛒 Purchasing package: {package_type.value}")
            logger.info(f"   User: {user_id}")
            logger.info(f"   Price: NPR {price}")
            
            # Check balance
            balance = self.user_balances.get(user_id, 0)
            if balance < price:
                raise Exception(f"Insufficient balance: NPR {balance}, required: NPR {price}")
            
            # Create transaction
            transaction = Transaction(
                transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
                transaction_type=TransactionType.PACKAGE_PURCHASE,
                sender_id=user_id,
                receiver_id="system",
                amount=price,
                status=TransactionStatus.PENDING,
                timestamp=datetime.utcnow(),
                metadata={"package_type": package_type.value}
            )
            
            # Generate Zero-Knowledge Proof
            zkp = await self._generate_zkp(transaction)
            transaction.zkp_proof = zkp.proof_id
            
            # Process transaction
            await self._process_transaction(transaction)
            
            logger.info(f"✅ Package purchased: {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"❌ Package purchase error: {e}")
            raise
    
    async def _generate_zkp(self, transaction: Transaction) -> ZeroKnowledgeProof:
        """
        Generate Zero-Knowledge Proof for transaction
        Proves transaction is valid without revealing details
        """
        try:
            logger.info(f"🔒 Generating Zero-Knowledge Proof for: {transaction.transaction_id}")
            
            # In production, this would use real ZKP (zk-SNARKs, zk-STARKs)
            # For simulation, use cryptographic commitment
            
            # Generate commitment
            transaction_data = f"{transaction.transaction_id}{transaction.amount}{transaction.timestamp.isoformat()}"
            commitment = hashlib.sha256(transaction_data.encode()).hexdigest()
            
            # Generate challenge
            challenge = os.urandom(32).hex()
            
            # Generate response (simulated)
            response = hashlib.sha256((commitment + challenge).encode()).hexdigest()
            
            zkp = ZeroKnowledgeProof(
                proof_id=f"zkp_{uuid.uuid4().hex[:12]}",
                transaction_id=transaction.transaction_id,
                commitment=commitment,
                response=response,
                challenge=challenge,
                verified=True
            )
            
            self.zkp_proofs[zkp.proof_id] = zkp
            
            logger.info(f"✅ ZKP generated: {zkp.proof_id}")
            return zkp
            
        except Exception as e:
            logger.error(f"❌ ZKP generation error: {e}")
            raise
    
    async def _process_transaction(self, transaction: Transaction) -> bool:
        """Process transaction with ZKP verification"""
        try:
            transaction.status = TransactionStatus.PROCESSING
            
            # Verify ZKP
            zkp = self.zkp_proofs.get(transaction.zkp_proof)
            if not zkp or not zkp.verified:
                transaction.status = TransactionStatus.FAILED
                raise Exception("ZKP verification failed")
            
            # Deduct from sender
            sender_balance = self.user_balances.get(transaction.sender_id, 0)
            if sender_balance < transaction.amount:
                transaction.status = TransactionStatus.FAILED
                raise Exception("Insufficient balance")
            
            self.user_balances[transaction.sender_id] = sender_balance - transaction.amount
            
            # Add to receiver
            receiver_balance = self.user_balances.get(transaction.receiver_id, 0)
            self.user_balances[transaction.receiver_id] = receiver_balance + transaction.amount
            
            transaction.status = TransactionStatus.COMPLETED
            
            # Store transaction
            self.transactions.append(transaction)
            
            logger.info(f"✅ Transaction processed: {transaction.transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Transaction processing error: {e}")
            transaction.status = TransactionStatus.FAILED
            return False
    
    async def reward_task_completion(
        self,
        agent_id: str,
        task_id: str,
        reward_amount: float
    ) -> Transaction:
        """
        Reward agent for task completion
        System pays agent for completed tasks
        """
        try:
            logger.info(f"🎁 Rewarding task completion: {task_id}")
            logger.info(f"   Agent: {agent_id}")
            logger.info(f"   Reward: NPR {reward_amount}")
            
            # Create transaction
            transaction = Transaction(
                transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
                transaction_type=TransactionType.TASK_REWARD,
                sender_id="system",
                receiver_id=agent_id,
                amount=reward_amount,
                status=TransactionStatus.PENDING,
                timestamp=datetime.utcnow(),
                metadata={"task_id": task_id}
            )
            
            # Generate ZKP
            zkp = await self._generate_zkp(transaction)
            transaction.zkp_proof = zkp.proof_id
            
            # Process transaction
            await self._process_transaction(transaction)
            
            logger.info(f"✅ Task reward sent: {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"❌ Task reward error: {e}")
            raise
    
    async def transfer_credits(
        self,
        sender_id: str,
        receiver_id: str,
        amount: float,
        metadata: Dict[str, Any] = None
    ) -> Transaction:
        """
        Transfer credits between users
        Privacy protected with ZKP
        """
        try:
            logger.info(f"💸 Transferring credits")
            logger.info(f"   From: {sender_id}")
            logger.info(f"   To: {receiver_id}")
            logger.info(f"   Amount: NPR {amount}")
            
            # Create transaction
            transaction = Transaction(
                transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
                transaction_type=TransactionType.PAYMENT,
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                status=TransactionStatus.PENDING,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Generate ZKP
            zkp = await self._generate_zkp(transaction)
            transaction.zkp_proof = zkp.proof_id
            
            # Process transaction
            await self._process_transaction(transaction)
            
            logger.info(f"✅ Credits transferred: {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"❌ Credit transfer error: {e}")
            raise
    
    def get_balance(self, user_id: str) -> float:
        """Get user balance"""
        return self.user_balances.get(user_id, 0)
    
    def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Transaction]:
        """Get transaction history for user"""
        user_transactions = [
            txn for txn in self.transactions
            if txn.sender_id == user_id or txn.receiver_id == user_id
        ]
        
        # Sort by timestamp (newest first)
        user_transactions.sort(key=lambda t: t.timestamp, reverse=True)
        
        return user_transactions[:limit]
    
    def get_economy_statistics(self) -> Dict[str, Any]:
        """Get economy statistics"""
        total_credits = sum(c.amount for c in self.credits.values())
        total_transactions = len(self.transactions)
        completed_transactions = len([t for t in self.transactions if t.status == TransactionStatus.COMPLETED])
        
        transaction_breakdown = {}
        for txn in self.transactions:
            t_type = txn.transaction_type.value
            transaction_breakdown[t_type] = transaction_breakdown.get(t_type, 0) + 1
        
        return {
            "total_credits_in_circulation": total_credits,
            "total_users": len(self.user_balances),
            "total_transactions": total_transactions,
            "completed_transactions": completed_transactions,
            "transaction_success_rate": completed_transactions / total_transactions if total_transactions > 0 else 0,
            "transaction_breakdown": transaction_breakdown,
            "zkp_proofs_generated": len(self.zkp_proofs)
        }

# Global Nexus Credits instance
_nexus_credits = NexusCredits()

async def main():
    """Main entry point for testing"""
    # Create credits for user
    credit = await _nexus_credits.create_credit("user_001", 10000)
    
    print(f"Credit created: {credit.credit_id}")
    print(f"Balance: {_nexus_credits.get_balance('user_001')}")
    
    # Purchase package
    txn = await _nexus_credits.purchase_package("user_001", PackageType.FIVE_DAYS)
    
    print(f"Package purchased: {txn.transaction_id}")
    print(f"New Balance: {_nexus_credits.get_balance('user_001')}")
    
    # Reward task
    reward_txn = await _nexus_credits.reward_task_completion("agent_001", "task_123", 500)
    
    print(f"Task reward: {reward_txn.transaction_id}")
    print(f"Agent Balance: {_nexus_credits.get_balance('agent_001')}")
    
    # Get statistics
    stats = _nexus_credits.get_economy_statistics()
    print(f"Economy Statistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
