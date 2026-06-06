
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIM NEXUS Redis Integration Module
====================================
Provides Redis caching, session management, rate limiting, and real-time events
"""

import redis
import json
import logging
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
import hashlib
import os

logger = logging.getLogger("RedisIntegration")


class RedisConnector:
    """Redis integration for ASIM NEXUS caching, sessions, real-time state"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 db: int = 0,
                 password: str = None):
        """Initialize Redis connector"""
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", 6379))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.db = db
        self.prefix = "asim:"
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Redis connected: {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            return self.client.ping() if self.client else False
        except:
            return False
    
    # ===== METRICS CACHE =====
    
    def cache_model_metrics(self, model_id: str, metrics: dict, ttl: int = 3600) -> bool:
        """Cache model metrics with TTL (default 1 hour)"""
        if not self.client:
            logger.warning("Redis not available, skipping metric cache")
            return False
        try:
            key = f"{self.prefix}metrics:{model_id}"
            self.client.setex(key, ttl, json.dumps(metrics))
            logger.debug(f"Cached metrics for {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache metrics: {e}")
            return False
    
    def get_model_metrics(self, model_id: str) -> Optional[dict]:
        """Retrieve cached model metrics"""
        if not self.client:
            return None
        try:
            key = f"{self.prefix}metrics:{model_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None
    
    def invalidate_model_metrics(self, model_id: str) -> bool:
        """Invalidate cached metrics for a model"""
        if not self.client:
            return False
        try:
            key = f"{self.prefix}metrics:{model_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate metrics: {e}")
            return False
    
    # ===== INFERENCE RESULTS =====
    
    def store_inference_result(self, request_id: str, result: dict, ttl: int = 86400) -> bool:
        """Store inference result for quick retrieval (TTL 24h default)"""
        if not self.client:
            return False
        try:
            key = f"{self.prefix}inference:{request_id}"
            self.client.setex(key, ttl, json.dumps(result))
            return True
        except Exception as e:
            logger.error(f"Failed to store inference result: {e}")
            return False
    
    def get_inference_result(self, request_id: str) -> Optional[dict]:
        """Retrieve cached inference result"""
        if not self.client:
            return None
        try:
            key = f"{self.prefix}inference:{request_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get inference result: {e}")
            return None
    
    # ===== CONVERSATIONS =====
    
    def cache_conversation(self, user_id: str, conversation: list, ttl: int = 604800) -> bool:
        """Cache user conversation (TTL 7 days default)"""
        if not self.client:
            return False
        try:
            key = f"{self.prefix}conversation:{user_id}"
            self.client.setex(key, ttl, json.dumps(conversation))
            return True
        except Exception as e:
            logger.error(f"Failed to cache conversation: {e}")
            return False
    
    def get_conversation(self, user_id: str) -> Optional[list]:
        """Retrieve cached conversation"""
        if not self.client:
            return None
        try:
            key = f"{self.prefix}conversation:{user_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    # ===== SESSIONS =====
    
    def create_session(self, user_id: str, session_data: dict, ttl: int = 86400) -> str:
        """Create or update user session"""
        if not self.client:
            return ""
        try:
            session_id = hashlib.sha256(f"{user_id}{datetime.now()}".encode()).hexdigest()[:32]
            key = f"{self.prefix}session:{session_id}"
            session_data["user_id"] = user_id
            session_data["created_at"] = datetime.now().isoformat()
            self.client.setex(key, ttl, json.dumps(session_data))
            logger.debug(f"Created session {session_id} for user {user_id}")
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return ""
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data"""
        if not self.client:
            return None
        try:
            key = f"{self.prefix}session:{session_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        if not self.client:
            return False
        try:
            key = f"{self.prefix}session:{session_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False
    
    def get_active_sessions(self) -> Dict[str, dict]:
        """Get all active user sessions"""
        if not self.client:
            return {}
        try:
            keys = self.client.keys(f"{self.prefix}session:*")
            sessions = {}
            for key in keys:
                session_id = key.split(":")[-1]
                session_data = self.client.get(key)
                if session_data:
                    sessions[session_id] = json.loads(session_data)
            return sessions
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return {}
    
    # ===== RATE LIMITING =====
    
    def check_rate_limit(self, api_key: str, limit: int = 100, window: int = 3600) -> bool:
        """Check and enforce API rate limit (requests per window)"""
        if not self.client:
            return True  # Allow if Redis unavailable
        try:
            key = f"{self.prefix}ratelimit:{api_key}"
            current = self.client.incr(key)
            
            if current == 1:
                self.client.expire(key, window)
            
            allowed = current <= limit
            if not allowed:
                logger.warning(f"Rate limit exceeded for {api_key}: {current}/{limit}")
            return allowed
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow on error
    
    def get_rate_limit_status(self, api_key: str, limit: int = 100, window: int = 3600) -> dict:
        """Get rate limit status for an API key"""
        if not self.client:
            return {"current": 0, "limit": limit, "remaining": limit}
        try:
            key = f"{self.prefix}ratelimit:{api_key}"
            current = int(self.client.get(key) or 0)
            ttl = self.client.ttl(key)
            return {
                "current": current,
                "limit": limit,
                "remaining": max(0, limit - current),
                "reset_in_seconds": ttl if ttl > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"current": 0, "limit": limit, "remaining": limit}
    
    def reset_rate_limit(self, api_key: str) -> bool:
        """Reset rate limit for an API key"""
        if not self.client:
            return False
        try:
            key = f"{self.prefix}ratelimit:{api_key}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False
    
    # ===== REAL-TIME EVENTS =====
    
    def publish_event(self, channel: str, event: dict) -> int:
        """Publish real-time event to channel"""
        if not self.client:
            logger.warning("Redis not available, event not published")
            return 0
        try:
            full_channel = f"{self.prefix}{channel}"
            subscribers = self.client.publish(full_channel, json.dumps(event))
            logger.debug(f"Published event to {channel}, {subscribers} subscribers")
            return subscribers
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return 0
    
    def subscribe_to_events(self, channel: str, callback: Callable):
        """Subscribe to real-time events (blocking)"""
        if not self.client:
            logger.error("Redis not available, cannot subscribe")
            return
        try:
            pubsub = self.client.pubsub()
            full_channel = f"{self.prefix}{channel}"
            pubsub.subscribe(full_channel)
            logger.info(f"Subscribed to channel: {channel}")
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        event_data = json.loads(message['data'])
                        callback(event_data)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
        except Exception as e:
            logger.error(f"Subscription error: {e}")
    
    # ===== GENERAL KEY-VALUE =====
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair"""
        if not self.client:
            return False
        try:
            full_key = f"{self.prefix}{key}"
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                self.client.setex(full_key, ttl, value)
            else:
                self.client.set(full_key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """Get a value by key"""
        if not self.client:
            return None
        try:
            full_key = f"{self.prefix}{key}"
            return self.client.get(full_key)
        except Exception as e:
            logger.error(f"Failed to get {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.client:
            return False
        try:
            full_key = f"{self.prefix}{key}"
            self.client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")
            return False
    
    # ===== UTILITIES =====
    
    def get_stats(self) -> dict:
        """Get Redis statistics"""
        if not self.client:
            return {}
        try:
            info = self.client.info()
            keys = self.client.dbsize()
            return {
                "connected": True,
                "used_memory_mb": info.get("used_memory_human", "N/A"),
                "total_keys": keys,
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def flush_all_asim_keys(self) -> int:
        """DANGEROUS: Flush all ASIM NEXUS keys from Redis"""
        if not self.client:
            return 0
        try:
            keys = self.client.keys(f"{self.prefix}*")
            if keys:
                self.client.delete(*keys)
            logger.warning(f"Flushed {len(keys)} ASIM NEXUS keys")
            return len(keys)
        except Exception as e:
            logger.error(f"Failed to flush keys: {e}")
            return 0


# Singleton instance
_redis_connector: Optional[RedisConnector] = None


def get_redis_connector() -> RedisConnector:
    """Get singleton Redis connector instance"""
    global _redis_connector
    if _redis_connector is None:
        _redis_connector = RedisConnector()
    return _redis_connector


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    redis = get_redis_connector()
    
    if redis.is_connected():
        # Cache model metrics
        redis.cache_model_metrics("model_001", {"accuracy": 0.95, "latency_ms": 100})
        print("Metrics cached")
        
        # Create session
        session_id = redis.create_session("user_123", {"role": "admin"})
        print(f"Session created: {session_id}")
        
        # Check rate limit
        passed = redis.check_rate_limit("api_key_456", limit=10, window=60)
        print(f"Rate limit passed: {passed}")
        
        # Get stats
        stats = redis.get_stats()
        print(f"Redis stats: {stats}")
    else:
        print("❌ Redis not available")
