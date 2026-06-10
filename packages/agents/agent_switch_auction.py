
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Agent-Switch Task Auction System
==========================================
5/15/30 Day Package Activation
Task Auction for Agent Mode
Clone-to-Agent Communication
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("AgentSwitchAuction")

class PackageType(Enum):
    """Agent mode package types"""
    FIVE_DAYS = 5
    FIFTEEN_DAYS = 15
    THIRTY_DAYS = 30

class TaskStatus(Enum):
    """Task status in auction"""
    LISTED = "listed"
    BIDDING = "bidding"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class BidStatus(Enum):
    """Bid status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

@dataclass
class AgentPackage:
    """Agent mode package"""
    package_id: str
    agent_id: str
    package_type: PackageType
    start_time: datetime
    end_time: datetime
    status: str  # "active", "expired", "paused"
    price: float
    earnings: float = 0.0
    tasks_completed: int = 0
    performance_score: float = 0.0

@dataclass
class TaskListing:
    """Task listing in auction"""
    task_id: str
    title: str
    description: str
    task_type: str
    required_skills: List[str]
    budget: float
    deadline: datetime
    posted_by: str
    posted_at: datetime
    status: TaskStatus
    bids: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None

@dataclass
class TaskBid:
    """Bid on a task"""
    bid_id: str
    task_id: str
    agent_id: str
    bid_amount: float
    estimated_completion_time: str
    proposal: str
    bid_time: datetime
    status: BidStatus

class AgentSwitchAuctionSystem:
    """
    Agent-Switch Task Auction System
    5/15/30 Day Package Activation
    Task Auction for Agent Mode
    """
    
    def __init__(self):
        self.packages: Dict[str, AgentPackage] = {}
        self.task_listings: Dict[str, TaskListing] = {}
        self.task_bids: Dict[str, TaskBid] = {}
        self.agent_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Package pricing
        self.package_prices = {
            PackageType.FIVE_DAYS: 500.0,
            PackageType.FIFTEEN_DAYS: 1200.0,
            PackageType.THIRTY_DAYS: 2000.0
        }
        
        # Initialize auction system
        self._initialize_auction_system()
        
    def _initialize_auction_system(self) -> None:
        """Initialize the agent switch auction system"""
        logger.info("🔄 Initializing Agent-Switch Task Auction System...")
        logger.info("📦 Packages: 5 Days (NPR 500), 15 Days (NPR 1,200), 30 Days (NPR 2,000)")
        logger.info("🔨 Task Auction: Agents bid on tasks, best bid wins")
        logger.info("✅ Agent-Switch Auction System initialized")
    
    async def activate_agent_package(
        self,
        agent_id: str,
        package_type: PackageType,
        payment_method: str = "nexus_wallet"
    ) -> AgentPackage:
        """Activate agent mode package for an agent"""
        try:
            logger.info(f"📦 Activating agent package: {package_type.value} days for agent: {agent_id}")
            
            # Check if agent already has active package
            if agent_id in self.packages:
                existing_package = self.packages[agent_id]
                if existing_package.status == "active":
                    raise Exception("Agent already has active package")
            
            # Calculate price
            price = self.package_prices[package_type]
            
            # Create package
            package = AgentPackage(
                package_id=f"pkg_{uuid.uuid4().hex[:12]}",
                agent_id=agent_id,
                package_type=package_type,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(days=package_type.value),
                status="active",
                price=price
            )
            
            self.packages[agent_id] = package
            
            logger.info(f"✅ Agent package activated: {package.package_id}")
            logger.info(f"💰 Price: NPR {price}")
            logger.info(f"📅 Valid until: {package.end_time}")
            
            return package
            
        except Exception as e:
            logger.error(f"❌ Agent package activation error: {e}")
            raise
    
    async def list_task(
        self,
        posted_by: str,
        title: str,
        description: str,
        task_type: str,
        required_skills: List[str],
        budget: float,
        deadline: datetime
    ) -> TaskListing:
        """List a task in the auction"""
        try:
            logger.info(f"📋 Listing task: {title}")
            
            task = TaskListing(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                title=title,
                description=description,
                task_type=task_type,
                required_skills=required_skills,
                budget=budget,
                deadline=deadline,
                posted_by=posted_by,
                posted_at=datetime.utcnow(),
                status=TaskStatus.LISTED
            )
            
            self.task_listings[task.task_id] = task
            
            logger.info(f"✅ Task listed: {task.task_id}")
            logger.info(f"💰 Budget: NPR {budget}")
            
            return task
            
        except Exception as e:
            logger.error(f"❌ Task listing error: {e}")
            raise
    
    async def place_bid(
        self,
        task_id: str,
        agent_id: str,
        bid_amount: float,
        estimated_completion_time: str,
        proposal: str
    ) -> TaskBid:
        """Place a bid on a task"""
        try:
            # Check if task exists and is open for bidding
            task = self.task_listings.get(task_id)
            
            if not task:
                raise Exception("Task not found")
            
            if task.status not in [TaskStatus.LISTED, TaskStatus.BIDDING]:
                raise Exception("Task not open for bidding")
            
            # Check if agent has active package
            if agent_id not in self.packages:
                raise Exception("Agent does not have active package")
            
            package = self.packages[agent_id]
            if package.status != "active":
                raise Exception("Agent package not active")
            
            logger.info(f"💰 Placing bid on task: {task_id} by agent: {agent_id}")
            
            # Create bid
            bid = TaskBid(
                bid_id=f"bid_{uuid.uuid4().hex[:12]}",
                task_id=task_id,
                agent_id=agent_id,
                bid_amount=bid_amount,
                estimated_completion_time=estimated_completion_time,
                proposal=proposal,
                bid_time=datetime.utcnow(),
                status=BidStatus.PENDING
            )
            
            self.task_bids[bid.bid_id] = bid
            task.bids.append(bid.bid_id)
            
            # Update task status to bidding
            if task.status == TaskStatus.LISTED:
                task.status = TaskStatus.BIDDING
            
            logger.info(f"✅ Bid placed: {bid.bid_id}")
            logger.info(f"💵 Amount: NPR {bid_amount}")
            
            return bid
            
        except Exception as e:
            logger.error(f"❌ Bid placement error: {e}")
            raise
    
    async def accept_bid(
        self,
        task_id: str,
        bid_id: str
    ) -> bool:
        """Accept a bid and assign task to agent"""
        try:
            task = self.task_listings.get(task_id)
            
            if not task:
                raise Exception("Task not found")
            
            bid = self.task_bids.get(bid_id)
            
            if not bid:
                raise Exception("Bid not found")
            
            logger.info(f"✅ Accepting bid: {bid_id} for task: {task_id}")
            
            # Update bid status
            bid.status = BidStatus.ACCEPTED
            
            # Reject other bids
            for other_bid_id in task.bids:
                if other_bid_id != bid_id:
                    other_bid = self.task_bids.get(other_bid_id)
                    if other_bid:
                        other_bid.status = BidStatus.REJECTED
            
            # Update task status
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent = bid.agent_id
            
            # Update agent package stats
            if bid.agent_id in self.packages:
                package = self.packages[bid.agent_id]
                package.earnings += bid.bid_amount
            
            logger.info(f"✅ Task assigned to agent: {bid.agent_id}")
            logger.info(f"💰 Agent earnings: NPR {bid.bid_amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Bid acceptance error: {e}")
            return False
    
    async def complete_task(
        self,
        task_id: str,
        agent_id: str,
        result: str,
        quality_score: float
    ) -> bool:
        """Complete a task and update agent stats"""
        try:
            task = self.task_listings.get(task_id)
            
            if not task:
                raise Exception("Task not found")
            
            if task.assigned_agent != agent_id:
                raise Exception("Task not assigned to this agent")
            
            logger.info(f"✅ Completing task: {task_id} by agent: {agent_id}")
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            
            # Update agent package stats
            if agent_id in self.packages:
                package = self.packages[agent_id]
                package.tasks_completed += 1
                
                # Update performance score
                package.performance_score = self._calculate_performance_score(package, quality_score)
            
            logger.info(f"✅ Task completed successfully")
            logger.info(f"⭐ Quality Score: {quality_score}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Task completion error: {e}")
            return False
    
    def _calculate_performance_score(self, package: AgentPackage, quality_score: float) -> float:
        """Calculate agent performance score"""
        try:
            if package.tasks_completed == 0:
                return 0.0
            
            # Base score from quality
            score = quality_score * 0.7
            
            # Bonus for task completion rate
            completion_bonus = min(package.tasks_completed * 0.01, 0.3)
            
            total_score = score + completion_bonus
            
            return round(total_score * 100, 2)
            
        except Exception as e:
            logger.error(f"❌ Performance score calculation error: {e}")
            return 0.0
    
    async def get_available_tasks(
        self,
        agent_id: str,
        skills: List[str]
    ) -> List[Dict[str, Any]]:
        """Get available tasks for an agent based on skills"""
        try:
            available_tasks = []
            
            for task in self.task_listings.values():
                if task.status not in [TaskStatus.LISTED, TaskStatus.BIDDING]:
                    continue
                
                # Check if task matches agent's skills
                skill_match = any(skill in task.required_skills for skill in skills)
                
                if skill_match:
                    available_tasks.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "task_type": task.task_type,
                        "budget": task.budget,
                        "deadline": task.deadline.isoformat(),
                        "required_skills": task.required_skills,
                        "bid_count": len(task.bids)
                    })
            
            logger.info(f"📋 Found {len(available_tasks)} available tasks for agent: {agent_id}")
            return available_tasks
            
        except Exception as e:
            logger.error(f"❌ Available tasks error: {e}")
            return []
    
    async def get_agent_package_status(self, agent_id: str) -> Dict[str, Any]:
        """Get agent package status"""
        try:
            package = self.packages.get(agent_id)
            
            if not package:
                return {"success": False, "error": "No active package"}
            
            # Check if package is expired
            if datetime.utcnow() > package.end_time:
                package.status = "expired"
            
            return {
                "success": True,
                "package_id": package.package_id,
                "package_type": package.package_type.value,
                "start_time": package.start_time.isoformat(),
                "end_time": package.end_time.isoformat(),
                "status": package.status,
                "price": package.price,
                "earnings": package.earnings,
                "tasks_completed": package.tasks_completed,
                "performance_score": package.performance_score,
                "days_remaining": max(0, (package.end_time - datetime.utcnow()).days)
            }
            
        except Exception as e:
            logger.error(f"❌ Package status error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_auction_system_status(self) -> Dict[str, Any]:
        """Get auction system status"""
        return {
            "total_packages": len(self.packages),
            "active_packages": len([p for p in self.packages.values() if p.status == "active"]),
            "total_tasks": len(self.task_listings),
            "open_tasks": len([t for t in self.task_listings.values() if t.status in [TaskStatus.LISTED, TaskStatus.BIDDING]]),
            "assigned_tasks": len([t for t in self.task_listings.values() if t.status == TaskStatus.ASSIGNED]),
            "completed_tasks": len([t for t in self.task_listings.values() if t.status == TaskStatus.COMPLETED]),
            "total_bids": len(self.task_bids),
            "pending_bids": len([b for b in self.task_bids.values() if b.status == BidStatus.PENDING]),
            "total_earnings": sum(p.earnings for p in self.packages.values())
        }

# Global agent switch auction system instance
_agent_switch_auction = AgentSwitchAuctionSystem()

async def main():
    """Main entry point for testing"""
    # Activate agent package
    package = await _agent_switch_auction.activate_agent_package(
        agent_id="agent_001",
        package_type=PackageType.THIRTY_DAYS
    )
    
    print(f"Package activated: {package.package_id}")
    
    # List a task
    task = await _agent_switch_auction.list_task(
        posted_by="user_001",
        title="Document Verification",
        description="Verify medical documents for hospital",
        task_type="document_verification",
        required_skills=["healthcare", "medical"],
        budget=500.0,
        deadline=datetime.utcnow() + timedelta(days=3)
    )
    
    print(f"Task listed: {task.task_id}")
    
    # Place bid
    bid = await _agent_switch_auction.place_bid(
        task_id=task.task_id,
        agent_id="agent_001",
        bid_amount=450.0,
        estimated_completion_time="2 days",
        proposal="I have medical certification and can verify documents efficiently"
    )
    
    print(f"Bid placed: {bid.bid_id}")
    
    # Accept bid
    await _agent_switch_auction.accept_bid(task.task_id, bid.bid_id)
    
    # Complete task
    await _agent_switch_auction.complete_task(
        task_id=task.task_id,
        agent_id="agent_001",
        result="Documents verified successfully",
        quality_score=0.95
    )
    
    # Get package status
    status = await _agent_switch_auction.get_agent_package_status("agent_001")
    print(f"Package status: {status}")
    
    # Get auction system status
    auction_status = _agent_switch_auction.get_auction_system_status()
    print(f"Auction system status: {auction_status}")

if __name__ == "__main__":
    asyncio.run(main())
