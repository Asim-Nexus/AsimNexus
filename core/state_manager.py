
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

import logging
logger = logging.getLogger(__name__)
"""Central State Manager: Unified state management with Redis + DB fallback."""
import json
import pickle
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from dataclasses import dataclass, asdict


class StateNamespace(Enum):
    """State namespaces for different components."""
    CONVERSATION = "conversation"
    AGENT = "agent"
    TASK = "task"
    SYSTEM = "system"
    TOOL = "tool"
    CACHE = "cache"
    SESSION = "session"


@dataclass
class StateEntry:
    """Represents a state entry with metadata."""
    key: str
    namespace: str
    data: Any
    created_at: datetime
    updated_at: datetime
    ttl: Optional[int] = None  # seconds
    version: int = 1


class InMemoryBackend:
    """In-memory state backend (fallback when Redis unavailable)."""
    
    def __init__(self, max_size: int = 10000):
        self._store: Dict[str, StateEntry] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[StateEntry]:
        async with self._lock:
            entry = self._store.get(key)
            if entry and entry.ttl:
                # Check if expired
                if datetime.now() > entry.updated_at + timedelta(seconds=entry.ttl):
                    del self._store[key]
                    return None
            return entry
    
    async def set(self, entry: StateEntry) -> bool:
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._store) >= self._max_size:
                oldest = min(self._store.keys(), 
                           key=lambda k: self._store[k].updated_at)
                del self._store[oldest]
            
            self._store[entry.key] = entry
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        async with self._lock:
            import fnmatch
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
    
    async def clear_namespace(self, namespace: str) -> int:
        async with self._lock:
            keys_to_delete = [k for k in self._store.keys() 
                            if k.startswith(f"{namespace}:")]
            for k in keys_to_delete:
                del self._store[k]
            return len(keys_to_delete)


class RedisBackend:
    """Redis state backend for production."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        try:
            import redis as redis_lib
            self._client = redis_lib.Redis(
                host=host, port=port, db=db, 
                decode_responses=False,
                socket_connect_timeout=5
            )
            self._available = self._client.ping()
        except Exception as e:
            print(f"Redis not available: {e}")
            self._client = None
            self._available = False
    
    @property
    def available(self) -> bool:
        if not self._available or not self._client:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False
    
    async def get(self, key: str) -> Optional[StateEntry]:
        if not self.available:
            return None
        try:
            data = self._client.get(key)
            if data:
                entry_dict = pickle.loads(data)
                return StateEntry(**entry_dict)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(self, entry: StateEntry) -> bool:
        if not self.available:
            return False
        try:
            data = pickle.dumps(asdict(entry))
            if entry.ttl:
                self._client.setex(entry.key, entry.ttl, data)
            else:
                self._client.set(entry.key, data)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            return self._client.delete(key) > 0
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        if not self.available:
            return []
        try:
            return [k.decode() if isinstance(k, bytes) else k 
                   for k in self._client.keys(pattern)]
        except Exception as e:
            print(f"Redis keys error: {e}")
            return []
    
    async def clear_namespace(self, namespace: str) -> int:
        if not self.available:
            return 0
        try:
            pattern = f"{namespace}:*"
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis clear error: {e}")
            return 0


class CentralStateManager:
    """
    Centralized state management for all ASIMNEXUS components.
    
    Features:
    - Unified interface for all state operations
    - Automatic Redis → In-memory fallback
    - Namespaced state isolation
    - TTL support for automatic cleanup
    - Async operations throughout
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        if hasattr(self, '_initialized'):
            return
        
        self._redis_host = redis_host
        self._redis_port = redis_port
        
        # Initialize backends
        self._redis = RedisBackend(redis_host, redis_port)
        self._memory = InMemoryBackend()
        
        # Use Redis if available, otherwise memory
        self._primary = self._redis if self._redis.available else self._memory
        self._fallback = self._memory
        
        self._stats = {
            'reads': 0,
            'writes': 0,
            'cache_hits': 0,
            'redis_fallbacks': 0
        }
        
        self._initialized = True
    
    def initialize(self) -> bool:
        """Initialize or reinitialize state manager (for Redis restart recovery)"""
        try:
            # Reinitialize Redis backend
            self._redis = RedisBackend(self._redis_host, self._redis_port)
            
            # Update primary backend
            self._primary = self._redis if self._redis.available else self._memory
            
            print(f"✅ State Manager reinitialized - Redis available: {self._redis.available}")
            return True
            
        except Exception as e:
            print(f"❌ State Manager reinitialization failed: {e}")
            self._primary = self._memory
            return False
    
    def _make_key(self, namespace, key: str) -> str:
        """Create full key with namespace - handles both string and enum."""
        if isinstance(namespace, str):
            return f"asim:{namespace}:{key}"
        elif hasattr(namespace, 'value'):
            return f"asim:{namespace.value}:{key}"
        else:
            return f"asim:{str(namespace)}:{key}"
    
    async def get(self, namespace, key: str) -> Optional[Any]:
        """Get state value."""
        full_key = self._make_key(namespace, key)
        self._stats['reads'] += 1
        
        # Try primary backend
        entry = await self._primary.get(full_key)
        
        # Fallback to memory if Redis fails
        if entry is None and self._primary != self._fallback:
            entry = await self._fallback.get(full_key)
            if entry:
                self._stats['redis_fallbacks'] += 1
        
        if entry:
            self._stats['cache_hits'] += 1
            return entry.data
        
        return None
    
    async def set(self, namespace, key: str, 
                  data: Any, ttl: Optional[int] = None) -> bool:
        """Set state value."""
        full_key = self._make_key(namespace, key)
        now = datetime.now()
        
        # Handle namespace for StateEntry
        namespace_value = namespace.value if hasattr(namespace, 'value') else str(namespace)
        
        entry = StateEntry(
            key=full_key,
            namespace=namespace_value,
            data=data,
            created_at=now,
            updated_at=now,
            ttl=ttl
        )
        
        self._stats['writes'] += 1
        
        # Write to primary
        success = await self._primary.set(entry)
        
        # Also write to fallback for redundancy (if different)
        if self._primary != self._fallback:
            await self._fallback.set(entry)
        
        return success
    
    async def delete(self, namespace: StateNamespace, key: str) -> bool:
        """Delete state value."""
        full_key = self._make_key(namespace, key)
        
        success = await self._primary.delete(full_key)
        if self._primary != self._fallback:
            await self._fallback.delete(full_key)
        
        return success
    
    async def get_many(self, namespace: StateNamespace, 
                       keys: List[str]) -> Dict[str, Any]:
        """Get multiple state values efficiently."""
        tasks = [self.get(namespace, k) for k in keys]
        results = await asyncio.gather(*tasks)
        
        return {k: v for k, v in zip(keys, results) if v is not None}
    
    async def set_many(self, namespace: StateNamespace,
                       items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple state values efficiently."""
        tasks = [self.set(namespace, k, v, ttl) for k, v in items.items()]
        results = await asyncio.gather(*tasks)
        
        return all(results)
    
    async def list_keys(self, namespace: StateNamespace, 
                        pattern: str = "*") -> List[str]:
        """List keys in namespace matching pattern."""
        full_pattern = f"asim:{namespace.value}:{pattern}"
        keys = await self._primary.keys(full_pattern)
        
        # Remove namespace prefix
        prefix_len = len(f"asim:{namespace.value}:")
        return [k[prefix_len:] for k in keys]
    
    async def clear_namespace(self, namespace: StateNamespace) -> int:
        """Clear all state in namespace."""
        count = await self._primary.clear_namespace(f"asim:{namespace.value}")
        if self._primary != self._fallback:
            await self._fallback.clear_namespace(f"asim:{namespace.value}")
        return count
    
    async def get_stats(self) -> Dict[str, int]:
        """Get operation statistics."""
        return self._stats.copy()
    
    # Convenience methods for specific namespaces
    
    async def get_conversation(self, session_id: str) -> Optional[List[Dict]]:
        """Get conversation history."""
        return await self.get(StateNamespace.CONVERSATION, session_id)
    
    async def append_message(self, session_id: str, message: Dict) -> bool:
        """Append message to conversation."""
        history = await self.get_conversation(session_id) or []
        history.append({
            **message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 messages
        if len(history) > 50:
            history = history[-50:]
        
        return await self.set(
            StateNamespace.CONVERSATION, 
            session_id, 
            history,
            ttl=86400 * 7  # 7 days
        )
    
    async def get_agent_state(self, agent_id: str) -> Optional[Dict]:
        """Get agent state."""
        return await self.get(StateNamespace.AGENT, agent_id)
    
    async def set_agent_state(self, agent_id: str, state: Dict) -> bool:
        """Set agent state."""
        return await self.set(
            StateNamespace.AGENT,
            agent_id,
            state,
            ttl=3600  # 1 hour
        )
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status."""
        return await self.get(StateNamespace.TASK, task_id)
    
    async def update_task_status(self, task_id: str, status: str, 
                                  result: Any = None) -> bool:
        """Update task status."""
        current = await self.get_task_status(task_id) or {}
        current.update({
            'status': status,
            'result': result,
            'updated_at': datetime.now().isoformat()
        })
        return await self.set(
            StateNamespace.TASK,
            task_id,
            current,
            ttl=86400  # 24 hours
        )
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache namespace."""
        return await self.get(StateNamespace.CACHE, key)
    
    async def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set in cache namespace with TTL."""
        return await self.set(StateNamespace.CACHE, key, value, ttl)


# Global instance
_state_manager = None

def get_state_manager() -> CentralStateManager:
    """Get global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = CentralStateManager()
    return _state_manager
