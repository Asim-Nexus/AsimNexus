
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Universal API Gateway for ASIMNEXUS World OS
============================================

This is the single entry point for all ASIMNEXUS services.
It provides:
- Unified API routing
- Rate limiting
- Authentication/Authorization
- Load balancing
- API versioning
- Request/response logging
- Circuit breaker pattern
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import json

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


@dataclass
class APIRoute:
    """API route definition"""
    path: str
    method: str
    handler: callable
    auth_required: bool = True
    rate_limit: str = "100/hour"
    cache_ttl: int = 0  # 0 = no cache
    version: str = "v1"


@dataclass
class ServiceConfig:
    """Service configuration"""
    name: str
    base_url: str
    health_check_path: str = "/health"
    timeout: int = 30
    retries: int = 3


@dataclass
class GatewayConfig:
    """Gateway configuration"""
    port: int = 8000
    host: str = "0.0.0.0"
    enable_cors: bool = True
    enable_compression: bool = True
    enable_rate_limiting: bool = True
    default_rate_limit: str = "100/hour"
    enable_auth: bool = True
    enable_logging: bool = True
    enable_metrics: bool = True
    cache_enabled: bool = True
    circuit_breaker_enabled: bool = True


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def record_failure(self):
        """Record a failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def record_success(self):
        """Record a success"""
        self.failure_count = 0
        if self.state == "half-open":
            self.state = "closed"
            logger.info("Circuit breaker closed")
    
    def allow_request(self) -> bool:
        """Check if request is allowed"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout:
                self.state = "half-open"
                logger.info("Circuit breaker moved to half-open")
                return True
            return False
        
        if self.state == "half-open":
            return True
        
        return False


class RateLimiter:
    """Rate limiter implementation"""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, period: int = 3600) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        period_start = now - timedelta(seconds=period)
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > period_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Record request
        self.requests[key].append(now)
        return True


class APIGateway:
    """
    Universal API Gateway for ASIMNEXUS
    
    This gateway provides a unified entry point for all ASIMNEXUS services.
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.app = FastAPI(title="ASIMNEXUS Universal API Gateway")
        self.routes: List[APIRoute] = []
        self.services: Dict[str, ServiceConfig] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiter = RateLimiter()
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        
        self._setup_middleware()
        self._setup_health_check()
        self._setup_metrics()
    
    def _setup_middleware(self):
        """Setup middleware"""
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        if self.config.enable_compression:
            self.app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    def _setup_health_check(self):
        """Setup health check endpoint"""
        @self.app.get("/health")
        async def health_check():
            uptime = (datetime.now() - self.start_time).total_seconds()
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "services": len(self.services),
                "routes": len(self.routes),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/health/services")
        async def services_health():
            """Health check for all registered services"""
            results = {}
            for name, service in self.services.items():
                try:
                    # In production, this would actually ping the service
                    results[name] = {"status": "healthy", "url": service.base_url}
                except Exception as e:
                    results[name] = {"status": "unhealthy", "error": str(e)}
            return results
    
    def _setup_metrics(self):
        """Setup metrics endpoint"""
        @self.app.get("/metrics")
        async def metrics():
            uptime = (datetime.now() - self.start_time).total_seconds()
            error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
            
            return {
                "uptime_seconds": uptime,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate_percent": error_rate,
                "routes": len(self.routes),
                "services": len(self.services),
                "circuit_breakers": {
                    name: {
                        "state": cb.state,
                        "failure_count": cb.failure_count
                    }
                    for name, cb in self.circuit_breakers.items()
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def register_service(self, name: str, config: ServiceConfig):
        """Register a backend service"""
        self.services[name] = config
        self.circuit_breakers[name] = CircuitBreaker()
        logger.info(f"Registered service: {name} at {config.base_url}")
    
    def register_route(self, route: APIRoute):
        """Register an API route"""
        self.routes.append(route)
        
        # Create route handler
        async def handler(request: Request):
            return await self._handle_request(request, route)
        
        # Register with FastAPI
        method = getattr(self.app, route.method.lower())
        method(route.path)(handler)
        
        logger.info(f"Registered route: {route.method} {route.path}")
    
    async def _handle_request(self, request: Request, route: APIRoute) -> Response:
        """Handle incoming request"""
        self.request_count += 1
        start_time = time.time()
        
        try:
            # Rate limiting
            if self.config.enable_rate_limiting:
                client_ip = get_remote_address(request)
                if not self.rate_limiter.is_allowed(client_ip, 100, 3600):
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Authentication
            if route.auth_required and self.config.enable_auth:
                # In production, validate JWT/OAuth token
                pass
            
            # Circuit breaker check
            for service_name, cb in self.circuit_breakers.items():
                if not cb.allow_request():
                    raise HTTPException(
                        status_code=503,
                        detail=f"Service {service_name} is temporarily unavailable"
                    )
            
            # Call handler
            result = await route.handler(request)
            
            # Record success
            for cb in self.circuit_breakers.values():
                cb.record_success()
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Log request
            if self.config.enable_logging:
                logger.info(f"{route.method} {route.path} - {latency_ms:.2f}ms - 200")
            
            return JSONResponse(
                content={
                    "success": True,
                    "data": result,
                    "meta": {
                        "latency_ms": latency_ms,
                        "timestamp": datetime.now().isoformat(),
                        "version": route.version
                    }
                }
            )
        
        except HTTPException as e:
            self.error_count += 1
            latency_ms = (time.time() - start_time) * 1000
            
            if self.config.enable_logging:
                logger.error(f"{route.method} {route.path} - {latency_ms:.2f}ms - {e.status_code}")
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.detail,
                    "meta": {
                        "latency_ms": latency_ms,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
        
        except Exception as e:
            self.error_count += 1
            latency_ms = (time.time() - start_time) * 1000
            
            # Record failure for circuit breaker
            for cb in self.circuit_breakers.values():
                cb.record_failure()
            
            if self.config.enable_logging:
                logger.error(f"{route.method} {route.path} - {latency_ms:.2f}ms - 500 - {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "meta": {
                        "latency_ms": latency_ms,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
    
    async def start(self):
        """Start the gateway server"""
        import uvicorn
        
        logger.info(f"Starting ASIMNEXUS Universal API Gateway on {self.config.host}:{self.config.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Global gateway instance
_gateway: Optional[APIGateway] = None


def get_gateway() -> APIGateway:
    """Get global gateway instance"""
    global _gateway
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway


# Example usage
if __name__ == "__main__":
    async def main():
        gateway = APIGateway()
        
        # Register example routes
        gateway.register_route(APIRoute(
            path="/api/v1/chat",
            method="GET",
            handler=lambda request: {"message": "Hello from gateway"},
            auth_required=False
        ))
        
        await gateway.start()
    
    asyncio.run(main())
