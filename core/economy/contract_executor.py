
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Contract Execution Engine
=====================================
Manages contract lifecycle: matching, execution, completion, payment
5/15/30 day agent mode contracts
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger("ASIM_CONTRACT_EXECUTOR")

class ContractStatus(Enum):
    """Contract lifecycle states"""
    PENDING = "pending"           # Created, awaiting acceptance
    ACCEPTED = "accepted"         # Worker accepted
    ACTIVE = "active"             # Work in progress
    COMPLETED = "completed"       # Work done, awaiting review
    APPROVED = "approved"         # Approved, payment pending
    PAID = "paid"                 # Payment complete
    DISPUTED = "disputed"         # Under dispute
    CANCELLED = "cancelled"       # Cancelled

class ContractType(Enum):
    """Contract types for agent agreements"""
    SHORT_TERM = "short_term"     # 5-day contract
    MEDIUM_TERM = "medium_term"   # 15-day contract
    LONG_TERM = "long_term"       # 30-day contract
    PERMANENT = "permanent"       # Ongoing contract
    MILESTONE = "milestone"       # Milestone-based contract

class ContractDuration(Enum):
    """Agent mode durations"""
    SHORT = 5     # 5 days
    MEDIUM = 15   # 15 days
    LONG = 30     # 30 days

@dataclass
class Contract:
    """Job contract"""
    id: str
    job_id: str
    client_id: str
    worker_id: str
    title: str
    description: str
    payment_amount: float
    payment_currency: str
    duration_days: int
    status: ContractStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    milestones: List[Dict]
    deliverables: List[str]
    escrow_released: bool

class ContractExecutor:
    """
    Contract Execution Engine
    - Matches clones to jobs
    - Tracks progress
    - Manages escrow
    - Handles disputes
    """
    
    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.active_contracts: Dict[str, str] = {}  # worker_id -> contract_id
        self.completed_contracts: List[str] = []
        self.disputes: Dict[str, Dict] = {}
        self.escrow: Dict[str, float] = {}  # contract_id -> amount
    
    async def create_contract(self, job_id: str, client_id: str, 
                             worker_id: str, duration: ContractDuration,
                             job_details: Dict) -> Contract:
        """Create new contract"""
        
        contract_id = f"contract_{uuid.uuid4().hex[:12]}"
        
        contract = Contract(
            id=contract_id,
            job_id=job_id,
            client_id=client_id,
            worker_id=worker_id,
            title=job_details.get('title', 'Untitled Contract'),
            description=job_details.get('description', ''),
            payment_amount=job_details.get('payment', 0.0),
            payment_currency=job_details.get('currency', 'USD'),
            duration_days=duration.value,
            status=ContractStatus.PENDING,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            milestones=self._generate_milestones(duration.value),
            deliverables=job_details.get('deliverables', []),
            escrow_released=False
        )
        
        self.contracts[contract_id] = contract
        
        # Lock escrow
        self.escrow[contract_id] = contract.payment_amount
        
        logger.info(f"📋 Contract created: {contract_id} "
                   f"({duration.value} days, ${contract.payment_amount})")
        
        return contract
    
    def _generate_milestones(self, duration_days: int) -> List[Dict]:
        """Generate milestones based on duration"""
        milestones = []
        
        if duration_days == 5:
            # Short contract: 2 milestones
            milestones = [
                {"day": 2, "name": "Initial Progress", "completed": False},
                {"day": 5, "name": "Final Delivery", "completed": False}
            ]
        elif duration_days == 15:
            # Medium contract: 3 milestones
            milestones = [
                {"day": 5, "name": "Planning Complete", "completed": False},
                {"day": 10, "name": "Progress Review", "completed": False},
                {"day": 15, "name": "Final Delivery", "completed": False}
            ]
        else:  # 30 days
            # Long contract: 4 milestones
            milestones = [
                {"day": 7, "name": "Planning Complete", "completed": False},
                {"day": 14, "name": "Mid-Point Review", "completed": False},
                {"day": 21, "name": "Progress Check", "completed": False},
                {"day": 30, "name": "Final Delivery", "completed": False}
            ]
        
        return milestones
    
    async def accept_contract(self, contract_id: str, worker_id: str) -> bool:
        """Worker accepts contract"""
        if contract_id not in self.contracts:
            return False
        
        contract = self.contracts[contract_id]
        
        if contract.worker_id != worker_id:
            return False
        
        if contract.status != ContractStatus.PENDING:
            return False
        
        contract.status = ContractStatus.ACTIVE
        contract.started_at = datetime.now()
        self.active_contracts[worker_id] = contract_id
        
        logger.info(f"✅ Contract accepted: {contract_id} by {worker_id}")
        return True
    
    async def update_milestone(self, contract_id: str, milestone_index: int) -> bool:
        """Mark milestone as completed"""
        if contract_id not in self.contracts:
            return False
        
        contract = self.contracts[contract_id]
        
        if milestone_index < len(contract.milestones):
            contract.milestones[milestone_index]['completed'] = True
            contract.milestones[milestone_index]['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"🎯 Milestone {milestone_index + 1} completed for {contract_id}")
            return True
        
        return False
    
    async def complete_contract(self, contract_id: str) -> bool:
        """Worker marks contract as complete"""
        if contract_id not in self.contracts:
            return False
        
        contract = self.contracts[contract_id]
        
        if contract.status != ContractStatus.ACTIVE:
            return False
        
        contract.status = ContractStatus.COMPLETED
        contract.completed_at = datetime.now()
        
        # Remove from active
        if contract.worker_id in self.active_contracts:
            del self.active_contracts[contract.worker_id]
        
        logger.info(f"🎉 Contract completed: {contract_id}")
        return True
    
    async def approve_and_pay(self, contract_id: str, client_id: str) -> Dict:
        """Client approves work and releases payment"""
        if contract_id not in self.contracts:
            return {'success': False, 'error': 'Contract not found'}
        
        contract = self.contracts[contract_id]
        
        if contract.client_id != client_id:
            return {'success': False, 'error': 'Not authorized'}
        
        if contract.status != ContractStatus.COMPLETED:
            return {'success': False, 'error': 'Contract not completed'}
        
        # Release escrow
        contract.status = ContractStatus.PAID
        contract.escrow_released = True
        
        amount = self.escrow.get(contract_id, 0)
        if contract_id in self.escrow:
            del self.escrow[contract_id]
        
        self.completed_contracts.append(contract_id)
        
        logger.info(f"💰 Payment released: ${amount} for {contract_id}")
        
        return {
            'success': True,
            'amount': amount,
            'currency': contract.payment_currency,
            'worker_id': contract.worker_id,
            'contract_id': contract_id
        }
    
    async def auto_match_jobs(self, worker_id: str, worker_skills: List[str],
                             available_jobs: List[Dict]) -> List[Dict]:
        """AI matching: find best jobs for worker"""
        matches = []
        
        for job in available_jobs:
            # Calculate match score
            score = 0
            
            # Skill match
            job_skills = job.get('skills_required', [])
            matching_skills = set(worker_skills) & set(job_skills)
            skill_score = len(matching_skills) / len(job_skills) if job_skills else 0
            score += skill_score * 0.4  # 40% weight
            
            # Reputation match (simplified)
            score += 0.3  # Assume good reputation
            
            # Price match (worker rate vs job budget)
            budget = job.get('budget', 0)
            if budget > 0:
                score += 0.3  # Assume acceptable
            
            if score > 0.6:  # 60% threshold
                matches.append({
                    'job': job,
                    'score': round(score, 2),
                    'matching_skills': list(matching_skills)
                })
        
        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:5]  # Top 5 matches
    
    def get_worker_contracts(self, worker_id: str) -> Dict[str, Any]:
        """Get all contracts for a worker"""
        worker_contracts = [
            c for c in self.contracts.values()
            if c.worker_id == worker_id
        ]
        
        active = [c for c in worker_contracts if c.status == ContractStatus.ACTIVE]
        completed = [c for c in worker_contracts if c.status == ContractStatus.PAID]
        pending = [c for c in worker_contracts if c.status == ContractStatus.PENDING]
        
        total_earned = sum(
            c.payment_amount for c in worker_contracts
            if c.status == ContractStatus.PAID
        )
        
        return {
            'active_count': len(active),
            'completed_count': len(completed),
            'pending_count': len(pending),
            'total_earned': total_earned,
            'active_contracts': [
                {
                    'id': c.id,
                    'title': c.title,
                    'progress': self._calculate_progress(c),
                    'days_remaining': self._days_remaining(c),
                    'payment': c.payment_amount
                }
                for c in active
            ]
        }
    
    def _calculate_progress(self, contract: Contract) -> int:
        """Calculate contract progress percentage"""
        if not contract.milestones:
            return 0
        
        completed = sum(1 for m in contract.milestones if m['completed'])
        return int((completed / len(contract.milestones)) * 100)
    
    def _days_remaining(self, contract: Contract) -> int:
        """Calculate days remaining in contract"""
        if not contract.started_at:
            return contract.duration_days
        
        end_date = contract.started_at + timedelta(days=contract.duration_days)
        remaining = (end_date - datetime.now()).days
        return max(0, remaining)
    
    async def check_expired_contracts(self):
        """Check and handle expired contracts"""
        expired = []
        
        for contract in self.contracts.values():
            if contract.status != ContractStatus.ACTIVE:
                continue
            
            if self._days_remaining(contract) == 0:
                # Contract expired
                expired.append(contract.id)
                
                # Auto-complete or flag for review
                if all(m['completed'] for m in contract.milestones):
                    await self.complete_contract(contract.id)
                else:
                    contract.status = ContractStatus.DISPUTED
                    self.disputes[contract.id] = {
                        'reason': 'incomplete_at_deadline',
                        'created_at': datetime.now().isoformat()
                    }
        
        return expired
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        total = len(self.contracts)
        active = sum(1 for c in self.contracts.values() if c.status == ContractStatus.ACTIVE)
        completed = len(self.completed_contracts)
        disputed = len(self.disputes)
        
        total_escrow = sum(self.escrow.values())
        
        return {
            'total_contracts': total,
            'active_contracts': active,
            'completed_contracts': completed,
            'disputed_contracts': disputed,
            'total_escrow_locked': total_escrow,
            'success_rate': completed / (completed + disputed) if (completed + disputed) > 0 else 1.0
        }

_executor = None

def get_contract_executor() -> ContractExecutor:
    """Get contract executor singleton"""
    global _executor
    if _executor is None:
        _executor = ContractExecutor()
    return _executor

if __name__ == "__main__":
    import sys
    
    executor = get_contract_executor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(executor.get_stats(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test contract creation
        async def test():
            contract = await executor.create_contract(
                "job_001", "client_001", "worker_001",
                ContractDuration.SHORT,
                {
                    'title': 'Website Development',
                    'payment': 500.0,
                    'currency': 'USD',
                    'deliverables': ['homepage', 'about page']
                }
            )
            print(f"Created: {contract.id}")
            
            # Accept
            await executor.accept_contract(contract.id, "worker_001")
            print("Contract accepted")
            
            # Update milestones
            await executor.update_milestone(contract.id, 0)
            await executor.update_milestone(contract.id, 1)
            
            # Complete
            await executor.complete_contract(contract.id)
            print("Contract completed")
            
            # Pay
            result = await executor.approve_and_pay(contract.id, "client_001")
            print(f"Payment: {result}")
            
            # Stats
            print(json.dumps(executor.get_stats(), indent=2))
        
        asyncio.run(test())
    else:
        print("Usage: python contract_executor.py [stats|test]")
