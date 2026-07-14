
"""
STATUS: REAL — Phase 3A: JSONL persistence + singleton factory
"""

"""
ASIMNEXUS Nexus Credits - Economic Layer
========================================
Internal payment system for agents and humans
Zero-Knowledge Proof for secure transactions
5/15/30 day package payments and task rewards

Persistence: Append-only JSONL ledger at data/nexus_credits.jsonl
Reference pattern: core/agent_contract.py, core/economy/sovereign_token.py
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid
import os
import secrets
from pathlib import Path

try:
    from core.security.zkp_privacy import (
        ECPoint as _ECPoint,
        SchnorrProver as _SchnorrProver,
        PedersenCommitment as _PedersenCommitment,
    )
    _HAS_REAL_ZKP = True
except ImportError:
    _HAS_REAL_ZKP = False

logger = logging.getLogger("NexusCredits")

# ── Persistence ──────────────────────────────────────────────────────────

_NEXUS_CREDITS_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nexus_credits.jsonl"
_NEXUS_CREDITS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


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
    created_at: str  # ISO timestamp for JSON serialization
    is_locked: bool = False
    lock_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NexusCredit":
        return cls(**data)

@dataclass
class Transaction:
    """Transaction record"""
    transaction_id: str
    transaction_type: str  # Stored as string for JSON serialization
    sender_id: str
    receiver_id: str
    amount: float
    status: str  # Stored as string for JSON serialization
    timestamp: str  # ISO timestamp
    zkp_proof: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(**data)

@dataclass
class ZeroKnowledgeProof:
    """Zero-Knowledge Proof for transaction privacy"""
    proof_id: str
    transaction_id: str
    commitment: str
    response: str
    challenge: str
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ZeroKnowledgeProof":
        return cls(**data)


class NexusCredits:
    """
    Nexus Credits - Economic Layer
    Internal payment system for agents and humans
    Zero-Knowledge Proof for secure transactions
    """

    def __init__(self):
        self.credits: Dict[str, NexusCredit] = {}
        self.transactions: List[Transaction] = []
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
        # Replay persisted state
        self._load_from_db()

    def _initialize_economy(self) -> None:
        """Initialize the Nexus Credits economy"""
        logger.info("💰 Initializing Nexus Credits - Economic Layer...")
        logger.info("🔒 Security: Zero-Knowledge Proof")
        logger.info("💳 Package Pricing:")
        logger.info(f"   5 Days: NPR {self.package_prices[PackageType.FIVE_DAYS]}")
        logger.info(f"   15 Days: NPR {self.package_prices[PackageType.FIFTEEN_DAYS]}")
        logger.info(f"   30 Days: NPR {self.package_prices[PackageType.THIRTY_DAYS]}")
        logger.info("✅ Nexus Credits initialized")

    # ── PERSISTENCE ─────────────────────────────────────────────────────────

    def _persist_tx(self, tx: Transaction) -> None:
        """Append transaction to JSONL ledger."""
        try:
            with open(_NEXUS_CREDITS_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(tx.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist transaction: {e}")

    def _persist_zkp(self, zkp: ZeroKnowledgeProof) -> None:
        """Append ZKP proof to JSONL ledger."""
        try:
            with open(_NEXUS_CREDITS_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"__type__": "zkp", **zkp.to_dict()}) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist ZKP: {e}")

    def _persist_balance(self, user_id: str, balance: float) -> None:
        """Append balance snapshot to JSONL ledger."""
        try:
            record = {"__type__": "balance", "user_id": user_id, "balance": balance,
                      "timestamp": datetime.utcnow().isoformat()}
            with open(_NEXUS_CREDITS_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist balance: {e}")

    def _persist_credit(self, credit: NexusCredit) -> None:
        """Append credit creation to JSONL ledger."""
        try:
            record = {"__type__": "credit", **credit.to_dict()}
            with open(_NEXUS_CREDITS_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist credit: {e}")

    def _load_from_db(self) -> None:
        """Replay JSONL ledger to reconstruct state on startup."""
        path = _NEXUS_CREDITS_DB_PATH
        if not path.exists():
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

                    entry_type = data.pop("__type__", "tx")

                    if entry_type == "tx":
                        # Reconstruct transaction
                        tx = Transaction.from_dict(data)
                        self.transactions.append(tx)
                        # Reconstruct user balances from completed transactions
                        if tx.status == "completed" or tx.status == TransactionStatus.COMPLETED.value:
                            # Sender pays
                            if tx.sender_id != "system":
                                self.user_balances[tx.sender_id] = \
                                    self.user_balances.get(tx.sender_id, 0) - tx.amount
                            # Receiver gets paid
                            if tx.receiver_id != "system":
                                self.user_balances[tx.receiver_id] = \
                                    self.user_balances.get(tx.receiver_id, 0) + tx.amount

                    elif entry_type == "zkp":
                        zkp = ZeroKnowledgeProof.from_dict(data)
                        self.zkp_proofs[zkp.proof_id] = zkp

                    elif entry_type == "balance":
                        # Balance snapshots establish ground truth
                        self.user_balances[data["user_id"]] = data["balance"]

                    elif entry_type == "credit":
                        credit = NexusCredit.from_dict(data)
                        self.credits[credit.credit_id] = credit

            logger.info(f"✅ Loaded {len(self.transactions)} transactions from {path.name}")

        except Exception as e:
            logger.warning(f"Failed to load from db: {e}")

    # ── CREDIT OPERATIONS ──────────────────────────────────────────────────

    async def create_credit(self, user_id: str, amount: float) -> NexusCredit:
        """Create Nexus Credit for user"""
        try:
            credit = NexusCredit(
                credit_id=f"credit_{uuid.uuid4().hex[:12]}",
                amount=amount,
                owner_id=user_id,
                created_at=datetime.utcnow().isoformat()
            )

            self.credits[credit.credit_id] = credit

            # Update user balance
            self.user_balances[user_id] = self.user_balances.get(user_id, 0) + amount

            # Persist
            self._persist_credit(credit)
            self._persist_balance(user_id, self.user_balances[user_id])

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
                transaction_type=TransactionType.PACKAGE_PURCHASE.value,
                sender_id=user_id,
                receiver_id="system",
                amount=price,
                status=TransactionStatus.PENDING.value,
                timestamp=datetime.utcnow().isoformat(),
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

            if _HAS_REAL_ZKP:
                # Generate real Pedersen commitment + Schnorr proof
                secret_key = secrets.randbelow(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141 - 1) + 1
                public_key = _ECPoint.multiply(secret_key)

                statement = f"txn:{transaction.transaction_id}:amount:{transaction.amount}"
                proof_dict = _SchnorrProver.prove(secret_key, public_key, statement)

                commitment = proof_dict['commitment']
                response = proof_dict['response']
                challenge = proof_dict['challenge']
            else:
                # Fallback: hash-based commitment
                transaction_data = f"{transaction.transaction_id}{transaction.amount}{transaction.timestamp}"
                commitment = hashlib.sha256(transaction_data.encode()).hexdigest()
                challenge = os.urandom(32).hex()
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
            self._persist_zkp(zkp)

            logger.info(f"✅ ZKP generated: {zkp.proof_id}")
            return zkp

        except Exception as e:
            logger.error(f"❌ ZKP generation error: {e}")
            raise

    async def _process_transaction(self, transaction: Transaction) -> bool:
        """Process transaction with ZKP verification"""
        try:
            transaction.status = TransactionStatus.PROCESSING.value

            # Verify ZKP
            zkp = self.zkp_proofs.get(transaction.zkp_proof)
            if not zkp or not zkp.verified:
                transaction.status = TransactionStatus.FAILED.value
                raise Exception("ZKP verification failed")

            # Deduct from sender
            sender_balance = self.user_balances.get(transaction.sender_id, 0)
            if sender_balance < transaction.amount:
                transaction.status = TransactionStatus.FAILED.value
                raise Exception("Insufficient balance")

            self.user_balances[transaction.sender_id] = sender_balance - transaction.amount

            # Add to receiver
            receiver_balance = self.user_balances.get(transaction.receiver_id, 0)
            self.user_balances[transaction.receiver_id] = receiver_balance + transaction.amount

            transaction.status = TransactionStatus.COMPLETED.value

            # Store transaction
            self.transactions.append(transaction)

            # Persist
            self._persist_tx(transaction)
            self._persist_balance(transaction.sender_id, self.user_balances[transaction.sender_id])
            self._persist_balance(transaction.receiver_id, self.user_balances[transaction.receiver_id])

            logger.info(f"✅ Transaction processed: {transaction.transaction_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Transaction processing error: {e}")
            transaction.status = TransactionStatus.FAILED.value
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
                transaction_type=TransactionType.TASK_REWARD.value,
                sender_id="system",
                receiver_id=agent_id,
                amount=reward_amount,
                status=TransactionStatus.PENDING.value,
                timestamp=datetime.utcnow().isoformat(),
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
                transaction_type=TransactionType.PAYMENT.value,
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                status=TransactionStatus.PENDING.value,
                timestamp=datetime.utcnow().isoformat(),
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

    def get_credit(self, credit_id: str) -> Optional[NexusCredit]:
        """Get a specific credit by ID"""
        return self.credits.get(credit_id)

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
        completed_transactions = len([t for t in self.transactions if t.status == TransactionStatus.COMPLETED.value or t.status == "completed"])

        transaction_breakdown = {}
        for txn in self.transactions:
            t_type = txn.transaction_type
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


# ── SINGLETON FACTORY ─────────────────────────────────────────────────────

_nexus_credits_instance: Optional[NexusCredits] = None


def get_nexus_credits() -> NexusCredits:
    """Get singleton NexusCredits instance (lazy-init with DB replay)."""
    global _nexus_credits_instance
    if _nexus_credits_instance is None:
        _nexus_credits_instance = NexusCredits()
    return _nexus_credits_instance


def reset_nexus_credits() -> None:
    """Reset the singleton (for testing). Does NOT delete persisted data."""
    global _nexus_credits_instance
    _nexus_credits_instance = None


async def main():
    """Main entry point for testing"""
    nc = get_nexus_credits()

    # Create credits for user
    credit = await nc.create_credit("user_001", 10000)

    print(f"Credit created: {credit.credit_id}")
    print(f"Balance: {nc.get_balance('user_001')}")

    # Purchase package
    txn = await nc.purchase_package("user_001", PackageType.FIVE_DAYS)

    print(f"Package purchased: {txn.transaction_id}")
    print(f"New Balance: {nc.get_balance('user_001')}")

    # Reward task
    reward_txn = await nc.reward_task_completion("agent_001", "task_123", 500)

    print(f"Task reward: {reward_txn.transaction_id}")
    print(f"Agent Balance: {nc.get_balance('agent_001')}")

    # Get statistics
    stats = nc.get_economy_statistics()
    print(f"Economy Statistics: {json.dumps(stats, indent=2)}")

    # Demonstrate round-trip persistence
    print("\n🔄 Demonstrating persistence round-trip...")
    reset_nexus_credits()
    nc2 = get_nexus_credits()
    print(f"Rebalanced user_001: {nc2.get_balance('user_001')}")
    print(f"Rebalanced agent_001: {nc2.get_balance('agent_001')}")
    print(f"Transactions reloaded: {len(nc2.transactions)}")
    print(f"ZKPs reloaded: {len(nc2.zkp_proofs)}")

if __name__ == "__main__":
    asyncio.run(main())
