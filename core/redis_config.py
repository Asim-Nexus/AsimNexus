"""
AsimNexus Redis Integration Guide
=================================

Redis को ६ तह AsimNexus मा:
1. Cache Layer - API Responses, LLM Outputs
2. Session Layer - User Sessions, Agent States  
3. Queue Layer - Background Jobs, Async Tasks
4. Pub/Sub Layer - Real-time Updates
5. Rate Limiter - API Limits, DDoS Protection
6. Persistence Layer - Redis Snapshots

Usage Examples:
- cache_get/set: Cache API responses
- session_create/get: User authentication
- queue_push/pop: Background job processing
- publish/subscribe: Real-time notifications
- rate_check: API rate limiting
"""

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "max_connections": 50
}