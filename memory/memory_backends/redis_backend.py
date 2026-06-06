
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Redis Memory Backend
High-speed memory storage for agents and sessions
"""

import os
import json
import time
import logging
import pickle
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

@dataclass
class MemoryConfig:
    """Redis memory configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

class RedisMemoryBackend:
    """Redis-based memory backend for ASIMNEXUS"""
    
    def __init__(self, config: MemoryConfig = None):
        self.logger = logging.getLogger("RedisMemoryBackend")
        self.config = config or MemoryConfig()
        self.redis_client = None
        self.connected = False
        
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return REDIS_AVAILABLE and self.connected
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not installed. Install with: pip install redis")
            return False
        
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=False  # Handle binary data
            )
            
            # Test connection
            self.redis_client.ping()
            self.connected = True
            
            self.logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            self.redis_client.close()
            self.connected = False
            self.logger.info("Disconnected from Redis")
    
    def _make_key(self, category: str, key: str) -> str:
        """Create Redis key with category prefix"""
        return f"asim:{category}:{key}"
    
    async def set(self, category: str, key: str, value: Any, 
                  expire_seconds: Optional[int] = None) -> bool:
        """Set a value in Redis"""
        if not self.connected:
            return False
        
        try:
            redis_key = self._make_key(category, key)
            
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized = json.dumps(value, default=str)
            else:
                serialized = str(value)
            
            # Set with optional expiration
            if expire_seconds:
                result = self.redis_client.setex(redis_key, expire_seconds, serialized)
            else:
                result = self.redis_client.set(redis_key, serialized)
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to set {category}:{key}: {e}")
            return False
    
    async def get(self, category: str, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        if not self.connected:
            return None
        
        try:
            redis_key = self._make_key(category, key)
            value = self.redis_client.get(redis_key)
            
            if value is None:
                return None
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value.decode('utf-8') if isinstance(value, bytes) else str(value)
                
        except Exception as e:
            self.logger.error(f"Failed to get {category}:{key}: {e}")
            return None
    
    async def delete(self, category: str, key: str) -> bool:
        """Delete a value from Redis"""
        if not self.connected:
            return False
        
        try:
            redis_key = self._make_key(category, key)
            result = self.redis_client.delete(redis_key)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Failed to delete {category}:{key}: {e}")
            return False
    
    async def exists(self, category: str, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.connected:
            return False
        
        try:
            redis_key = self._make_key(category, key)
            return bool(self.redis_client.exists(redis_key))
            
        except Exception as e:
            self.logger.error(f"Failed to check existence of {category}:{key}: {e}")
            return False
    
    async def keys(self, category: str, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern in category"""
        if not self.connected:
            return []
        
        try:
            redis_pattern = self._make_key(category, pattern)
            keys = self.redis_client.keys(redis_pattern)
            
            # Remove category prefix
            prefix = f"asim:{category}:"
            return [key.decode('utf-8').replace(prefix, "") for key in keys]
            
        except Exception as e:
            self.logger.error(f"Failed to get keys for {category}:{pattern}: {e}")
            return []
    
    async def set_session(self, session_id: str, data: Dict[str, Any], 
                         expire_hours: int = 24) -> bool:
        """Set session data"""
        return await self.set("session", session_id, data, expire_hours * 3600)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return await self.get("session", session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        return await self.delete("session", session_id)
    
    async def set_agent_memory(self, agent_id: str, memory_key: str, 
                              value: Any, expire_hours: Optional[int] = None) -> bool:
        """Set agent-specific memory"""
        full_key = f"{agent_id}:{memory_key}"
        expire_seconds = expire_hours * 3600 if expire_hours else None
        return await self.set("agent_memory", full_key, value, expire_seconds)
    
    async def get_agent_memory(self, agent_id: str, memory_key: str) -> Optional[Any]:
        """Get agent-specific memory"""
        full_key = f"{agent_id}:{memory_key}"
        return await self.get("agent_memory", full_key)
    
    async def set_vector(self, vector_id: str, vector: List[float], 
                        metadata: Dict[str, Any] = None) -> bool:
        """Store vector with metadata"""
        data = {
            "vector": vector,
            "metadata": metadata or {},
            "created_at": time.time()
        }
        return await self.set("vectors", vector_id, data)
    
    async def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector with metadata"""
        return await self.get("vectors", vector_id)
    
    async def search_vectors(self, query_vector: List[float], 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Simple vector search (placeholder - would need proper vector DB)"""
        # This is a simplified implementation
        # In production, use Redisearch or a proper vector database
        
        all_vectors = await self.keys("vectors", "*")
        results = []
        
        for vector_id in all_vectors:
            vector_data = await self.get_vector(vector_id)
            if vector_data and "vector" in vector_data:
                # Simple cosine similarity (placeholder)
                similarity = self._cosine_similarity(query_vector, vector_data["vector"])
                if similarity > 0.5:  # Threshold
                    results.append({
                        "id": vector_id,
                        "similarity": similarity,
                        "metadata": vector_data.get("metadata", {})
                    })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def set_cache(self, cache_key: str, value: Any, 
                       expire_minutes: int = 5) -> bool:
        """Set cache value"""
        return await self.set("cache", cache_key, value, expire_minutes * 60)
    
    async def get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cache value"""
        return await self.get("cache", cache_key)
    
    async def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.connected:
            return 0
        
        try:
            redis_key = self._make_key("counters", counter_name)
            return self.redis_client.incr(redis_key, amount)
        except Exception as e:
            self.logger.error(f"Failed to increment counter {counter_name}: {e}")
            return 0
    
    async def get_counter(self, counter_name: str) -> int:
        """Get counter value"""
        if not self.connected:
            return 0
        
        try:
            redis_key = self._make_key("counters", counter_name)
            value = self.redis_client.get(redis_key)
            return int(value) if value else 0
        except Exception as e:
            self.logger.error(f"Failed to get counter {counter_name}: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        if not self.connected:
            return 0
        
        try:
            # This would require TTL scanning in production
            # For now, just return count of session keys
            session_keys = await self.keys("session", "*")
            return len(session_keys)
        except Exception as e:
            self.logger.error(f"Failed to cleanup sessions: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self.connected:
            return {"connected": False}
        
        try:
            info = self.redis_client.info()
            
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get Redis statistics: {e}")
            return {"connected": True, "error": str(e)}

# Global Redis backend instance
redis_backend = RedisMemoryBackend()

# Alias for compatibility
RedisBackend = RedisMemoryBackend
