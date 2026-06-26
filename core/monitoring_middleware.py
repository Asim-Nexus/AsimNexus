"""AsimNexus Prometheus Monitoring Middleware"""
import time
import logging
from collections import defaultdict
from typing import Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("AsimNexus.Monitoring")

monitoring_instance: "PrometheusMonitoringMiddleware" = None


class PrometheusMonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.metrics: Dict[str, Any] = {
            "request_count": defaultdict(int),
            "request_latency": defaultdict(list),
            "error_count": defaultdict(int),
            "active_users": set(),
        }

    async def dispatch(self, request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method

        response = await call_next(request)

        latency = time.time() - start_time
        key = f"{method}:{path}"

        self.metrics["request_count"][key] += 1
        self.metrics["request_latency"][key].append(latency)

        if response.status_code >= 400:
            self.metrics["error_count"][key] += 1

        return response

    def get_metrics(self) -> Dict[str, Any]:
        result = {
            "request_count": dict(self.metrics["request_count"]),
            "error_count": dict(self.metrics["error_count"]),
            "latency_avg": {},
            "active_users": len(self.metrics["active_users"]),
        }
        for key, latencies in self.metrics["request_latency"].items():
            if latencies:
                result["latency_avg"][key] = sum(latencies) / len(latencies)
        return result


def get_monitoring() -> PrometheusMonitoringMiddleware:
    """Get the singleton monitoring middleware instance."""
    return monitoring_instance


async def set_monitoring(instance: PrometheusMonitoringMiddleware):
    """Set the singleton monitoring middleware instance."""
    global monitoring_instance
    monitoring_instance = instance