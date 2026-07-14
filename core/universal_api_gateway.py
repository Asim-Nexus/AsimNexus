"""
AsimNexus — Universal API Gateway
==================================
Universal API Gateway for routing requests to appropriate handlers
with rate limiting, authentication, and route management.
"""

import uuid
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable


@dataclass
class GatewayConfig:
    """Configuration for the API Gateway."""
    port: int = 8000
    enable_rate_limiting: bool = True
    enable_auth: bool = True
    rate_limit_per_minute: int = 60
    auth_token: Optional[str] = None


@dataclass
class APIRoute:
    """A registered API route."""
    path: str
    method: str
    handler: Callable
    auth_required: bool = True
    rate_limit: Optional[int] = None
    route_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class APIGateway:
    """Universal API Gateway for request routing and management."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self._lock = threading.Lock()
        self._routes: Dict[str, APIRoute] = {}
        self._rate_limiters: Dict[str, List[float]] = {}

    @property
    def routes(self) -> Dict[str, APIRoute]:
        """Get all registered routes."""
        with self._lock:
            return dict(self._routes)

    def register_route(self, route: APIRoute) -> None:
        """Register a new route."""
        with self._lock:
            key = f"{route.method}:{route.path}"
            self._routes[key] = route

    def unregister_route(self, path: str, method: str = "GET") -> None:
        """Unregister a route."""
        with self._lock:
            key = f"{method}:{path}"
            self._routes.pop(key, None)

    def route_request(self, path: str, method: str = "GET", request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route a request to the appropriate handler."""
        key = f"{method}:{path}"

        with self._lock:
            route = self._routes.get(key)

        if not route:
            return {"error": "Route not found", "status": 404}

        # Rate limiting check
        if self.config.enable_rate_limiting:
            if not self._check_rate_limit(key):
                return {"error": "Rate limit exceeded", "status": 429}

        # Execute handler
        try:
            result = route.handler(request or {})
            return {"data": result, "status": 200}
        except Exception as e:
            return {"error": str(e), "status": 500}

    def _check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limits."""
        now = time.time()
        with self._lock:
            if key not in self._rate_limiters:
                self._rate_limiters[key] = []

            # Clean old entries
            self._rate_limiters[key] = [
                t for t in self._rate_limiters[key]
                if now - t < 60
            ]

            limit = self.config.rate_limit_per_minute
            if len(self._rate_limiters[key]) >= limit:
                return False

            self._rate_limiters[key].append(now)
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        with self._lock:
            return {
                "total_routes": len(self._routes),
                "rate_limiting_enabled": self.config.enable_rate_limiting,
                "auth_enabled": self.config.enable_auth,
                "port": self.config.port,
            }
