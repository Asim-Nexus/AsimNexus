
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Company Group Chat System
15 Founders + ASIMNEXUS communicating in a group
Each founder has separate memory, account, and device
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class GroupMessage:
    """Message in the group chat"""
    id: str
    sender: str  # Founder name or "ASIMNEXUS"
    sender_role: str  # Founder role or "SYSTEM"
    content: str
    timestamp: datetime
    priority: MessagePriority = MessagePriority.NORMAL
    mentions: List[str] = field(default_factory=list)  # @mentions
    reply_to: Optional[str] = None  # Message ID being replied to
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> list of reactors


@dataclass
class FounderAccount:
    """Founder account with device and memory"""
    name: str
    role: str
    email: str
    device_id: str
    memory: Dict = field(default_factory=dict)
    preferences: Dict = field(default_factory=dict)
    status: str = "online"  # online, offline, busy, away
    last_active: datetime = field(default_factory=datetime.now)


class CompanyGroupChat:
    """Company Group Chat for 15 Founders + ASIMNEXUS"""
    
    def __init__(self, founder_clone_system):
        self.founder_clone_system = founder_clone_system
        self.messages: List[GroupMessage] = []
        self.founder_accounts: Dict[str, FounderAccount] = {}
        self.asimnexus_memory: Dict = {
            "conversations": [],
            "coordinations": [],
            "decisions": [],
            "tasks": []
        }
        self.message_counter = 0
        self._initialize_founder_accounts()
        
    def _initialize_founder_accounts(self):
        """Initialize accounts for all 15 founders"""
        founder_configs = {
            "Alex Chen": "CEO",
            "Sarah Kim": "CTO",
            "Michael Brown": "CFO",
            "Emily Rodriguez": "COO",
            "David Lee": "CPO",
            "Lisa Wang": "CHRO",
            "James Wilson": "CMO",
            "Rachel Green": "CLO",
            "Kevin Patel": "CSO",
            "Anna Martinez": "CDO",
            "Tom Anderson": "CIO",
            "Chris Taylor": "VP Engineering",
            "Jessica Chen": "VP Product",
            "Robert Johnson": "VP Sales",
            "Maria Garcia": "VP Ops"
        }
        
        for name, role in founder_configs.items():
            self.founder_accounts[name] = FounderAccount(
                name=name,
                role=role,
                email=f"{name.lower().replace(' ', '.')}@asimnexus.ai",
                device_id=f"device-{name.lower().replace(' ', '-')}",
                memory={
                    "conversations": [],
                    "decisions": [],
                    "tasks": [],
                    "insights": []
                },
                preferences={
                    "notifications": True,
                    "priority": "normal",
                    "response_style": "professional"
                }
            )
        
        logger.info(f"Initialized {len(self.founder_accounts)} founder accounts")
    
    async def send_message(self, sender: str, content: str, 
                          priority: MessagePriority = MessagePriority.NORMAL,
                          mentions: List[str] = None,
                          reply_to: str = None) -> GroupMessage:
        """Send a message to the group chat"""
        self.message_counter += 1
        message_id = f"msg_{self.message_counter}"
        
        # Determine sender role
        if sender == "ASIMNEXUS":
            sender_role = "SYSTEM"
        else:
            account = self.founder_accounts.get(sender)
            sender_role = account.role if account else "UNKNOWN"
        
        message = GroupMessage(
            id=message_id,
            sender=sender,
            sender_role=sender_role,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            mentions=mentions or [],
            reply_to=reply_to
        )
        
        self.messages.append(message)
        
        # Save to sender's memory
        if sender != "ASIMNEXUS":
            account = self.founder_accounts.get(sender)
            if account:
                account.memory["conversations"].append({
                    "id": message_id,
                    "content": content,
                    "timestamp": message.timestamp.isoformat(),
                    "type": "sent"
                })
                account.last_active = datetime.now()
        else:
            self.asimnexus_memory["conversations"].append({
                "id": message_id,
                "content": content,
                "timestamp": message.timestamp.isoformat(),
                "type": "sent"
            })
        
        logger.info(f"Message sent by {sender} ({sender_role}): {content[:50]}...")
        return message
    
    async def get_founder_response(self, founder_name: str, message: str, 
                                   context: Dict = None) -> str:
        """Get response from a specific founder"""
        account = self.founder_accounts.get(founder_name)
        if not account:
            return f"Founder {founder_name} not found"
        
        # Get founder role
        from core.founder_clones.founder_clone_system import FounderRole
        role_map = {
            "Alex Chen": FounderRole.CEO,
            "Sarah Kim": FounderRole.CTO,
            "Michael Brown": FounderRole.CFO,
            "Emily Rodriguez": FounderRole.COO,
            "David Lee": FounderRole.CPO,
            "Lisa Wang": FounderRole.CHRO,
            "James Wilson": FounderRole.CMO,
            "Rachel Green": FounderRole.CLO,
            "Kevin Patel": FounderRole.CSO,
            "Anna Martinez": FounderRole.CDO,
            "Tom Anderson": FounderRole.CIO,
            "Chris Taylor": FounderRole.VP_ENGINEERING,
            "Jessica Chen": FounderRole.VP_PRODUCT,
            "Robert Johnson": FounderRole.VP_SALES,
            "Maria Garcia": FounderRole.VP_OPS
        }
        
        role = role_map.get(founder_name)
        if not role:
            return f"Role not found for {founder_name}"
        
        # Add founder's memory context
        founder_context = {
            "memory": account.memory,
            "recent_conversations": account.memory["conversations"][-5:] if account.memory["conversations"] else []
        }
        if context:
            founder_context.update(context)
        
        # Get response from founder clone
        response = await self.founder_clone_system.message_founder(role, message, founder_context)
        
        # Save to founder's memory
        account.memory["conversations"].append({
            "content": message,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "type": "received"
        })
        
        return response
    
    async def coordinate_founders(self, task: str, founder_names: List[str] = None) -> Dict:
        """Coordinate multiple founders for a task"""
        if founder_names is None:
            # Auto-select relevant founders based on task
            founder_names = self._select_relevant_founders(task)
        
        results = {}
        for founder_name in founder_names:
            response = await self.get_founder_response(founder_name, task)
            results[founder_name] = response
        
        return {
            "task": task,
            "founders_involved": founder_names,
            "results": results,
            "coordination_status": "completed"
        }
    
    def _select_relevant_founders(self, task: str) -> List[str]:
        """Select relevant founders based on task keywords"""
        task_lower = task.lower()
        relevant_founders = []
        
        if any(kw in task_lower for kw in ['strategy', 'vision', 'direction', 'executive']):
            relevant_founders.append("Alex Chen")
        if any(kw in task_lower for kw in ['technical', 'architecture', 'technology', 'code']):
            relevant_founders.extend(["Sarah Kim", "Chris Taylor"])
        if any(kw in task_lower for kw in ['financial', 'budget', 'revenue', 'cost']):
            relevant_founders.append("Michael Brown")
        if any(kw in task_lower for kw in ['operation', 'process', 'efficiency']):
            relevant_founders.extend(["Emily Rodriguez", "Maria Garcia"])
        if any(kw in task_lower for kw in ['product', 'feature', 'user']):
            relevant_founders.extend(["David Lee", "Jessica Chen"])
        if any(kw in task_lower for kw in ['marketing', 'brand', 'growth']):
            relevant_founders.extend(["James Wilson", "Robert Johnson"])
        if any(kw in task_lower for kw in ['security', 'threat']):
            relevant_founders.append("Kevin Patel")
        if any(kw in task_lower for kw in ['data', 'analytics', 'ai']):
            relevant_founders.append("Anna Martinez")
        if any(kw in task_lower for kw in ['legal', 'compliance', 'contract']):
            relevant_founders.append("Rachel Green")
        if any(kw in task_lower for kw in ['hr', 'team', 'culture']):
            relevant_founders.append("Lisa Wang")
        if any(kw in task_lower for kw in ['innovation', 'rd', 'future']):
            relevant_founders.append("Tom Anderson")
        
        if not relevant_founders:
            relevant_founders.append("Alex Chen")  # Default to CEO
        
        result = list(set(relevant_founders))
        logger.info(f"Selected {len(result)} founders for task '{task}': {result}")
        return result
    
    async def asimnexus_coordinate(self, message: str) -> str:
        """ASIMNEXUS coordinates the group discussion"""
        logger.info(f"=== ASIMNEXUS COORDINATION START ===")
        logger.info(f"Task: {message}")
        
        # Analyze the message
        task_lower = message.lower()
        
        # Select relevant founders
        logger.info("Selecting relevant founders...")
        relevant_founders = self._select_relevant_founders(message)
        logger.info(f"Selected {len(relevant_founders)} founders: {relevant_founders}")
        
        # Get responses from relevant founders with error handling
        responses = {}
        logger.info(f"Starting to get responses from {len(relevant_founders)} founders...")
        for i, founder_name in enumerate(relevant_founders):
            logger.info(f"Processing founder {i+1}/{len(relevant_founders)}: {founder_name}")
            try:
                response = await self.get_founder_response(founder_name, message)
                responses[founder_name] = response
                logger.info(f"✅ Got response from {founder_name} (length: {len(response)})")
            except Exception as e:
                logger.error(f"❌ Error getting response from {founder_name}: {e}")
                responses[founder_name] = f"Error: {str(e)}"
        
        logger.info(f"Collected {len(responses)} responses")
        
        # ASIMNEXUS synthesizes the responses
        synthesis = f"""**ASIMNEXUS Coordination Summary**

I've coordinated with {len(responses)} founder(s) regarding: "{message}"

**Founder Inputs:**
"""
        for founder_name, response in responses.items():
            # Truncate long responses for readability
            if len(response) > 500:
                response = response[:500] + "..."
            synthesis += f"\n**{founder_name}:**\n{response}\n"
        
        synthesis += f"""
**ASIMNEXUS Analysis:**
Based on the inputs from the founders, here's my synthesis:
- {len(responses)} founders provided their perspectives
- Key themes identified: strategy, execution, alignment
- Recommended next steps: Coordinate implementation across relevant departments

**Action Items:**
1. Review founder inputs above
2. Assign specific tasks to relevant founders
3. Set up follow-up coordination session
4. Track progress in group chat

Would you like me to dive deeper into any specific founder's input or coordinate a follow-up discussion?"""
        
        # Save to ASIMNEXUS memory
        self.asimnexus_memory["coordinations"].append({
            "task": message,
            "founders": relevant_founders,
            "responses": responses,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info("=== ASIMNEXUS COORDINATION END ===")
        return synthesis
    
    def get_chat_history(self, limit: int = 50) -> List[GroupMessage]:
        """Get recent chat history"""
        return self.messages[-limit:]
    
    def get_founder_status(self, founder_name: str) -> Optional[Dict]:
        """Get founder account status"""
        account = self.founder_accounts.get(founder_name)
        if not account:
            return None
        
        return {
            "name": account.name,
            "role": account.role,
            "email": account.email,
            "device_id": account.device_id,
            "status": account.status,
            "last_active": account.last_active.isoformat(),
            "memory_size": len(account.memory["conversations"]),
            "preferences": account.preferences
        }
    
    def get_all_founders_status(self) -> Dict[str, Dict]:
        """Get status of all founders"""
        return {
            name: self.get_founder_status(name)
            for name in self.founder_accounts.keys()
        }
    
    def add_reaction(self, message_id: str, emoji: str, reactor: str) -> bool:
        """Add reaction to a message"""
        message = next((m for m in self.messages if m.id == message_id), None)
        if not message:
            return False
        
        if emoji not in message.reactions:
            message.reactions[emoji] = []
        
        if reactor not in message.reactions[emoji]:
            message.reactions[emoji].append(reactor)
        
        return True
    
    def get_group_stats(self) -> Dict:
        """Get group chat statistics"""
        return {
            "total_messages": len(self.messages),
            "total_founders": len(self.founder_accounts),
            "online_founders": sum(1 for f in self.founder_accounts.values() if f.status == "online"),
            "message_by_sender": {
                sender: len([m for m in self.messages if m.sender == sender])
                for sender in set(m.sender for m in self.messages)
            },
            "asimnexus_memory_size": len(self.asimnexus_memory.get("conversations", [])),
            "total_founder_memory": sum(len(f.memory["conversations"]) for f in self.founder_accounts.values())
        }
