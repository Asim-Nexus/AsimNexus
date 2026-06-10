
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Agent Mailbox
=======================
Mailbox system for agent communication
Provides message queuing and delivery between agents
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("AgentMailbox")


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(Enum):
    """Message status"""
    QUEUED = "queued"
    DELIVERED = "delivered"
    READ = "read"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """Message between agents"""
    message_id: str
    from_agent: str
    to_agent: str
    subject: str
    content: Any
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentMailbox:
    """
    Agent Mailbox System
    
    Manages agent communication:
    - Message queuing
    - Priority-based delivery
    - Message tracking
    - Read receipts
    """
    
    def __init__(self):
        self.logger = logging.getLogger("AgentMailbox")
        self.is_active = False
        self.mailboxes: Dict[str, List[AgentMessage]] = {}
        self.messages: Dict[str, AgentMessage] = {}
        self.metrics = {
            "total_messages": 0,
            "delivered_messages": 0,
            "failed_messages": 0
        }
    
    async def start(self):
        """Start the mailbox system"""
        self.logger.info("Starting Agent Mailbox...")
        self.is_active = True
        asyncio.create_task(self._delivery_loop())
        self.logger.info("Agent Mailbox started")
    
    async def stop(self):
        """Stop the mailbox system"""
        self.logger.info("Stopping Agent Mailbox...")
        self.is_active = False
        self.logger.info("Agent Mailbox stopped")
    
    async def _delivery_loop(self):
        """Background message delivery loop"""
        while self.is_active:
            try:
                await self._process_pending_messages()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Delivery loop error: {e}")
    
    async def _process_pending_messages(self):
        """Process pending messages"""
        for agent_id, messages in self.mailboxes.items():
            pending = [m for m in messages if m.status == MessageStatus.QUEUED]
            
            # Sort by priority
            priority_order = {
                MessagePriority.URGENT: 0,
                MessagePriority.HIGH: 1,
                MessagePriority.NORMAL: 2,
                MessagePriority.LOW: 3
            }
            pending.sort(key=lambda m: priority_order[m.priority])
            
            for message in pending:
                await self._deliver_message(message)
    
    async def _deliver_message(self, message: AgentMessage):
        """Deliver a message"""
        try:
            message.status = MessageStatus.DELIVERED
            message.delivered_at = datetime.now()
            self.metrics["delivered_messages"] += 1
            
            self.logger.info(f"Delivered message: {message.message_id} to {message.to_agent}")
            
        except Exception as e:
            message.status = MessageStatus.FAILED
            self.metrics["failed_messages"] += 1
            self.logger.error(f"Message delivery failed: {e}")
    
    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        subject: str,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Send a message
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            subject: Message subject
            content: Message content
            priority: Message priority
            metadata: Optional metadata
            
        Returns:
            Message ID
        """
        message_id = f"msg_{datetime.now().timestamp()}_{from_agent[:8]}"
        
        message = AgentMessage(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            subject=subject,
            content=content,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Add to recipient's mailbox
        if to_agent not in self.mailboxes:
            self.mailboxes[to_agent] = []
        self.mailboxes[to_agent].append(message)
        
        # Track message
        self.messages[message_id] = message
        self.metrics["total_messages"] += 1
        
        self.logger.info(f"Sent message: {message_id} from {from_agent} to {to_agent}")
        
        return message_id
    
    def get_messages(
        self,
        agent_id: str,
        status: Optional[MessageStatus] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get messages for an agent"""
        if agent_id not in self.mailboxes:
            return []
        
        messages = self.mailboxes[agent_id]
        
        filtered = []
        for message in messages:
            if status and message.status != status:
                continue
            filtered.append(message)
        
        # Sort by created_at (newest first)
        filtered.sort(key=lambda m: m.created_at, reverse=True)
        
        return [
            {
                "message_id": m.message_id,
                "from_agent": m.from_agent,
                "subject": m.subject,
                "priority": m.priority.value,
                "status": m.status.value,
                "created_at": m.created_at.isoformat()
            }
            for m in filtered[:limit]
        ]
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """Get a specific message"""
        if message_id not in self.messages:
            return None
        
        message = self.messages[message_id]
        return {
            "message_id": message.message_id,
            "from_agent": message.from_agent,
            "to_agent": message.to_agent,
            "subject": message.subject,
            "content": message.content,
            "priority": message.priority.value,
            "status": message.status.value,
            "created_at": message.created_at.isoformat(),
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None
        }
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        message.status = MessageStatus.READ
        message.read_at = datetime.now()
        
        return True
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Remove from mailbox
        if message.to_agent in self.mailboxes:
            self.mailboxes[message.to_agent] = [
                m for m in self.mailboxes[message.to_agent]
                if m.message_id != message_id
            ]
        
        # Remove from tracking
        del self.messages[message_id]
        
        return True
    
    def get_metrics(self) -> Dict:
        """Get mailbox metrics"""
        return {
            "is_active": self.is_active,
            "total_messages": self.metrics["total_messages"],
            "delivered_messages": self.metrics["delivered_messages"],
            "failed_messages": self.metrics["failed_messages"],
            "mailboxes": len(self.mailboxes),
            "pending_messages": sum(
                len([m for m in mbox if m.status == MessageStatus.QUEUED])
                for mbox in self.mailboxes.values()
            )
        }
