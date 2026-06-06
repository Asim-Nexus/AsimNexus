#!/usr/bin/env python3
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
🗄️ ASIMNEXUS Database Pool Manager
Phase 2: Security & Database Optimization
SQLAlchemy Connection Pool with Redis Caching for Maximum Performance
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import redis
import threading

@dataclass
class PoolConfig:
    """Database pool configuration"""
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    recycle_time: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    pool_recycle: int = 100

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    avg_response_time: float = 0.0
    errors_count: int = 0
    last_reset: datetime = None

class DatabasePoolManager:
    """ASIMNEXUS Database Pool Manager - Enterprise-grade Performance"""
    
    def __init__(self, database_url: str):
        self.logger = logging.getLogger("ASIMNEXUS_DatabasePool")
        self.database_url = database_url
        self.config = PoolConfig()
        self.metrics = ConnectionMetrics()
        self.metrics.last_reset = datetime.now()
        
        # Initialize SQLAlchemy pool
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.config.max_connections,
            max_overflow=self.config.max_connections,
            pool_pre_ping=self.config.pool_pre_ping,
            pool_recycle=self.config.pool_recycle,
            echo=False
        )
        
        self.session_factory = sessionmaker(bind=self.engine)
        
        # Initialize Redis for caching
        self.redis_client = self._init_redis()
        
        # Performance monitoring thread
        self.monitoring_active = False
        self.monitor_thread = None
        
    def _init_redis(self):
        """Initialize Redis for connection caching and metrics"""
        try:
            return redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
        except Exception as e:
            self.logger.error(f"🚨 Redis initialization failed: {e}")
            return None
            
    def get_connection(self, read_only: bool = False) -> Any:
        """Get database connection from pool with caching"""
        start_time = time.time()
        
        try:
            # Try Redis cache first
            if self.redis_client and read_only:
                cache_key = f"db_connection_{read_only}"
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    self.logger.debug("📋 Using cached connection")
                    return json.loads(cached_data)
            
            # Create new session
            session = self.session_factory()
            connection = session.connection()
            
            # Update metrics
            self.metrics.active_connections += 1
            self.metrics.total_queries += 1
            
            response_time = (time.time() - start_time) * 1000
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time + response_time) / 2
            )
            
            # Cache connection info
            if self.redis_client and not read_only:
                cache_data = {
                    'connection_time': datetime.now().isoformat(),
                    'response_time': response_time
                }
                self.redis_client.setex(
                    cache_key,
                    json.dumps(cache_data),
                    exptime=300  # 5 minutes
                )
            
            self.logger.debug(f"🔌 New connection established ({response_time:.2f}ms)")
            return session
            
        except Exception as e:
            self.metrics.errors_count += 1
            self.logger.error(f"🚨 Connection failed: {e}")
            raise
            
    def release_connection(self, session):
        """Release connection back to pool"""
        try:
            connection_time = time.time() - getattr(session, '_start_time', time.time())
            
            session.close()
            
            # Update metrics
            self.metrics.active_connections -= 1
            self.metrics.idle_connections += 1
            
            self.logger.debug(f"🔓 Connection released ({connection_time:.2f}ms)")
            
        except Exception as e:
            self.metrics.errors_count += 1
            self.logger.error(f"🚨 Connection release failed: {e}")
            
    def execute_query(self, session, query: str, params: Dict = None) -> Any:
        """Execute query with performance tracking"""
        start_time = time.time()
        
        try:
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))
                
            # Update metrics
            self.metrics.total_queries += 1
            response_time = (time.time() - start_time) * 1000
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time + response_time) / 2
            )
            
            session.commit()
            
            self.logger.debug(f"📊 Query executed ({response_time:.2f}ms): {query[:100]}...")
            return result
            
        except Exception as e:
            self.metrics.errors_count += 1
            self.logger.error(f"🚨 Query failed: {e}")
            session.rollback()
            raise
            
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics"""
        pool_status = self.engine.pool.status()
        
        return {
            'pool_config': {
                'min_connections': self.config.min_connections,
                'max_connections': self.config.max_connections,
                'current_size': pool_status['size'],
                'checked_in': pool_status['checked_in'],
                'checked_out': pool_status['checked_out']
            },
            'metrics': {
                'active_connections': self.metrics.active_connections,
                'idle_connections': self.metrics.idle_connections,
                'total_queries': self.metrics.total_queries,
                'avg_response_time': round(self.metrics.avg_response_time, 2),
                'errors_count': self.metrics.errors_count,
                'uptime_seconds': (datetime.now() - self.metrics.last_reset).total_seconds()
            },
            'redis_connected': self.redis_client is not None,
            'cache_hits': self._get_cache_hits(),
            'timestamp': datetime.now().isoformat()
        }
        
    def _get_cache_hits(self) -> int:
        """Get cache hit count from Redis"""
        try:
            if self.redis_client:
                hits = self.redis_client.get('cache_hits_counter') or 0
                return int(hits)
        except:
            return 0
            
    def increment_cache_hits(self):
        """Increment cache hit counter"""
        if self.redis_client:
            self.redis_client.incr('cache_hits_counter')
            self.redis_client.expire('cache_hits_counter', 3600)  # 1 hour
            
    def start_monitoring(self):
        """Start performance monitoring thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("📊 Database pool monitoring started")
        
    def stop_monitoring(self):
        """Stop performance monitoring thread"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("📊 Database pool monitoring stopped")
        
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Get pool status
                status = self.get_pool_status()
                
                # Log metrics every 30 seconds
                if self.redis_client:
                    self.redis_client.lpush('pool_metrics', json.dumps(status))
                    self.redis_client.ltrim('pool_metrics', 0, 99)  # Keep last 100 entries
                    
                # Check for performance issues
                if status['metrics']['avg_response_time'] > 1000:  # 1 second
                    self.logger.warning(f"⚠️ Slow query detected: {status['metrics']['avg_response_time']:.2f}ms")
                    
                if status['metrics']['errors_count'] > 0:
                    error_rate = status['metrics']['errors_count'] / status['metrics']['total_queries']
                    if error_rate > 0.05:  # 5% error rate
                        self.logger.error(f"🚨 High error rate: {error_rate:.2%}")
                        
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"🚨 Monitoring loop error: {e}")
                time.sleep(30)
                
    def optimize_pool(self):
        """Optimize pool performance"""
        try:
            # Reset metrics
            self.metrics = ConnectionMetrics()
            self.metrics.last_reset = datetime.now()
            
            # Clear old cache entries
            if self.redis_client:
                self.redis_client.flushdb()
                
            # Recycle connections
            self.engine.dispose()
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.config.max_connections,
                max_overflow=self.config.max_connections,
                pool_pre_ping=self.config.pool_pre_ping,
                pool_recycle=self.config.pool_recycle,
                echo=False
            )
            
            self.session_factory = sessionmaker(bind=self.engine)
            
            self.logger.info("🔧 Database pool optimized")
            
        except Exception as e:
            self.logger.error(f"🚨 Pool optimization failed: {e}")

# Global database pool manager
db_pool_manager = None

def get_db_pool_manager(database_url: str) -> DatabasePoolManager:
    """Get or create database pool manager instance"""
    global db_pool_manager
    if db_pool_manager is None:
        db_pool_manager = DatabasePoolManager(database_url)
    return db_pool_manager

if __name__ == "__main__":
    print("🗄️ ASIMNEXUS Database Pool Manager Starting...")
    
    # Example usage
    from os import getenv
    
    db_url = getenv('DATABASE_URL', 'sqlite:///asimnexus.db')
    manager = get_db_pool_manager(db_url)
    
    print("📊 Pool Status:", manager.get_pool_status())
