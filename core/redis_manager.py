"""
AsimNexus — Redis Manager (Memory Fallback)
=========================================
Integrated Redis for Cache, Session, Queue, Pub/Sub, Rate Limiting
Memory-only fallback when Redis server unavailable
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List, Callable
from threading import Lock

logger = logging.getLogger("AsimNexus.Redis")

class MemoryRedis:
    """Pure Python memory fallback for Redis"""
    def __init__(self):
        self._data = {}
        self._expiry = {}
        self._lock = Lock()
        self.subscribed = False
    
    def get(self, key):
        with self._lock:
            if key in self._data:
                if key in self._expiry and self._expiry[key] < time.time():
                    del self._data[key]
                    del self._expiry[key]
                    return None
                return self._data[key]
            return None
    
    def setex(self, key, ttl, value):
        with self._lock:
            self._data[key] = value
            self._expiry[key] = time.time() + ttl
    
    def incr(self, key):
        with self._lock:
            current = int(self._data.get(key, 0)) + 1
            self._data[key] = current
            return current
    
    def expire(self, key, ttl):
        with self._lock:
            self._expiry[key] = time.time() + ttl
    
    def delete(self, key):
        with self._lock:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
    
    def publish(self, channel, message):
        pass
    
    def ping(self):
        return True

class AsimRedisManager:
    """
    Unified Redis manager for AsimNexus
    - Cache Layer
    - Session Layer
    - Queue Layer
    - Pub/Sub Layer
    - Rate Limiter
    """
    
    _instance = None
    
    def __init__(self):
        try:
            import redis
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                decode_responses=True,
                max_connections=50
            )
            self.redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.info(f"Redis fallback: {e}")
            self.redis = MemoryRedis()
        self._subscribers = {}
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ─── Cache Operations ───────────────────────────────────────────────
    
    def cache_get(self, key: str) -> Optional[str]:
        return self.redis.get(f"cache:{key}")
    
    def cache_set(self, key: str, value: str, ttl: int = 300):
        self.redis.setex(f"cache:{key}", ttl, value)
    
    def cache_json_get(self, key: str) -> Optional[Dict]:
        data = self.cache_get(key)
        return json.loads(data) if data else None
    
    def cache_json_set(self, key: str, value: Dict, ttl: int = 300):
        self.cache_set(key, json.dumps(value), ttl)
    
    # ─── Session Operations ───────────────────────────────────────────────
    
    def session_create(self, user_id: str, data: Dict) -> str:
        session_id = f"sess:{user_id}:{int(time.time())}"
        self.redis.setex(f"session:{session_id}", 86400, json.dumps(data))
        return session_id
    
    def session_get(self, session_id: str) -> Optional[Dict]:
        data = self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    def session_update(self, session_id: str, data: Dict):
        existing = self.session_get(session_id)
        if existing:
            existing.update(data)
            self.redis.setex(f"session:{session_id}", 86400, json.dumps(existing))
    
    # ─── Queue Operations ─────────────────────────────────────────────────
    
    def queue_push(self, queue: str, task: Dict, priority: bool = False):
        key = f"queue:{queue}"
        task_json = json.dumps(task)
        if priority:
            self.redis.lpush(key, task_json)
        else:
            self.redis.rpush(key, task_json)
    
    def queue_pop(self, queue: str, timeout: int = 5) -> Optional[Dict]:
        key = f"queue:{queue}"
        result = self.redis.blpop(key, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None
    
    # ─── Pub/Sub Operations ──────────────────────────────────────────────
    
    def publish(self, channel: str, message: Dict):
        self.redis.publish(channel, json.dumps(message))
    
    def subscribe(self, channel: str, callback: Callable):
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)
        
        def listen():
            for msg in self.pubsub.listen():
                if msg['type'] == 'message' and msg['channel'] in self._subscribers:
                    for cb in self._subscribers[msg['channel']]:
                        cb(json.loads(msg['data']))
        
        if not self.pubsub.subscribed:
            thread = threading.Thread(target=listen, daemon=True)
            thread.start()
            self.pubsub.subscribe(channel)
    
    # ─── Rate Limiter ───────────────────────────────────────────────────
    
    def rate_check(self, key: str, limit: int = 100, window: int = 60) -> tuple:
        window_key = f"rate:{key}:{int(time.time()) // window}"
        count = self.redis.incr(window_key)
        if count == 1:
            self.redis.expire(window_key, window)
        remaining = max(0, limit - count)
        return count <= limit, remaining, 0 if count <= limit else window

redis_manager = AsimRedisManager.get_instance()