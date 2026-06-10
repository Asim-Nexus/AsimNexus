
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Event Bus
==================
Event bus for system-wide event communication
Provides pub/sub messaging for components
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger("EventBus")


class EventType(Enum):
    """Types of events"""
    SYSTEM_ALERT = "system_alert"
    HARDWARE_UPDATE = "hardware_update"
    NETWORK_UPDATE = "network_update"
    AGENT_MESSAGE = "agent_message"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    STATE_CHANGED = "state_changed"
    # Transport events
    PEER_CONNECTED = "peer_connected"
    PEER_DISCONNECTED = "peer_disconnected"
    RPC_TIMEOUT = "rpc_timeout"
    TRANSPORT_STATE_CHANGE = "transport_state_change"
    # Bootstrap events
    BOOTSTRAP_COMPLETE = "bootstrap_complete"
    BOOTSTRAP_FAILED = "bootstrap_failed"
    PEER_REGISTERED = "peer_registered"
    CUSTOM = "custom"


class AllocationPriority(Enum):
    """Priority levels for event delivery."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ASIMEvent:
    """An event in the ASIMNEXUS system"""
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = ""  # Will be auto-generated
    
    def __post_init__(self):
        if not self.event_id:
            import hashlib
            self.event_id = hashlib.sha256(
                f"{self.event_type.value}:{self.source}:{self.timestamp.timestamp()}".encode()
            ).hexdigest()[:16]


class ASIMEventBus:
    """
    ASIMNEXUS Event Bus
    
    Provides:
    - Event publishing
    - Event subscription
    - Event filtering
    - Event history
    """
    
    def __init__(self, use_redis: bool = False, redis_url: str = "redis://localhost:6379"):
        self.logger = logging.getLogger("ASIMEventBus")
        self.subscribers: Dict[EventType, List[tuple[Callable, AllocationPriority]]] = {}
        self.event_history: List[ASIMEvent] = []
        self.max_history = 1000
        self.is_active = False
        self.use_redis = use_redis
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self._priority_order = {
            AllocationPriority.HIGH: 2,
            AllocationPriority.NORMAL: 1,
            AllocationPriority.LOW: 0,
        }
    
    async def start(self):
        """Start the event bus"""
        self.logger.info("Starting ASIM Event Bus...")
        
        if self.use_redis:
            try:
                import aioredis
                self.redis_client = await aioredis.from_url(self.redis_url)
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe("asim_events")
                self.logger.info("Event bus connected to Redis")
            except Exception as e:
                self.logger.warning(f"Redis not available, using in-memory: {e}")
                self.use_redis = False
        
        self.is_active = True
        self.logger.info("ASIM Event Bus started")
    
    async def stop(self):
        """Stop the event bus"""
        self.logger.info("Stopping ASIM Event Bus...")
        
        if self.pubsub:
            await self.pubsub.unsubscribe("asim_events")
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.is_active = False
        self.logger.info("ASIM Event Bus stopped")
    
    def subscribe(self, event_type: EventType, callback: Callable, priority: AllocationPriority = AllocationPriority.NORMAL):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to call when event occurs
            priority: Delivery priority for the callback
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append((callback, priority))
        self.logger.info(f"Subscribed to {event_type.value} with priority {priority.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """
        Unsubscribe from an event type
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self.subscribers:
            self.subscribers[event_type] = [pair for pair in self.subscribers[event_type] if pair[0] != callback]
            self.logger.info(f"Unsubscribed from {event_type.value}")
    
    async def publish(self, event: ASIMEvent):
        """
        Publish an event
        
        Args:
            event: Event to publish
        """
        if not self.is_active:
            self.logger.warning("Event bus not active, event not published")
            return
        
        # Add to history
        self.event_history.append(event)
        
        # Keep history limited
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Publish to Redis if enabled
        if self.use_redis and self.redis_client:
            event_data = {
                "event_type": event.event_type.value,
                "data": event.data,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "event_id": event.event_id
            }
            await self.redis_client.publish("asim_events", json.dumps(event_data))
            
            # Store in Redis for persistence
            await self.redis_client.lpush("asim_events_history", json.dumps(event_data))
            await self.redis_client.ltrim("asim_events_history", 0, 10000)
        
        # Notify local subscribers in priority order
        if event.event_type in self.subscribers:
            sorted_subscribers = sorted(
                self.subscribers[event.event_type],
                key=lambda item: self._priority_order.get(item[1], 1),
                reverse=True,
            )
            for callback, _priority in sorted_subscribers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")
        
        self.logger.debug(f"Published event: {event.event_type.value} ({event.event_id})")
    
    async def publish_sync(self, event_type: EventType, data: Dict[str, Any], source: str = "unknown"):
        """
        Publish an event synchronously (helper method)
        
        Args:
            event_type: Type of event
            data: Event data
            source: Event source
        """
        event = ASIMEvent(
            event_type=event_type,
            data=data,
            source=source
        )
        await self.publish(event)
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get event history
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events
            
        Returns:
            List of events
        """
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "source": e.source,
                "timestamp": e.timestamp.isoformat(),
                "data": e.data
            }
            for e in events[-limit:]
        ]
    
    def get_stats(self) -> Dict:
        """Get event bus statistics"""
        priority_counts = {
            "high": 0,
            "normal": 0,
            "low": 0,
        }
        for subs in self.subscribers.values():
            for _, priority in subs:
                priority_counts[priority.value] += 1

        return {
            "is_active": self.is_active,
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "event_types": len(self.subscribers),
            "events_in_history": len(self.event_history),
            "subscription_priorities": priority_counts,
        }


# Global event bus instance
event_bus = ASIMEventBus()
