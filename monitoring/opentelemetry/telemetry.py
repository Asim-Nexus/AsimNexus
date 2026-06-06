
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Observability & Telemetry
===================================
OpenTelemetry integration for metrics, traces, and logs
Includes: Prometheus metrics, distributed tracing, structured logging
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os

logger = logging.getLogger("Telemetry")


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TraceStatus(Enum):
    """Trace statuses"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Metric:
    """Metric data point"""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Trace:
    """Distributed trace"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    status: TraceStatus
    start_time: datetime
    end_time: Optional[datetime]
    attributes: Dict[str, Any]
    events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LogEntry:
    """Structured log entry"""
    log_id: str
    level: str
    message: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None


class TelemetrySystem:
    """OpenTelemetry-based observability system"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}
        self.traces: Dict[str, Trace] = {}
        self.logs: List[LogEntry] = []
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize telemetry system"""
        logger.info("📊 Initializing Observability & Telemetry...")
        logger.info("📈 Setting up Prometheus metrics")
        logger.info("🔍 Setting up distributed tracing")
        logger.info("📝 Setting up structured logging")
        logger.info("✅ Observability & Telemetry initialized")
    
    def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """Record a metric"""
        metric = Metric(
            metric_id=f"metric_{uuid.uuid4().hex[:8]}",
            name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric)
        
        logger.debug(f"Recorded metric: {name} = {value}")
        return metric
    
    def start_trace(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Trace:
        """Start a new trace"""
        trace = Trace(
            trace_id=f"trace_{uuid.uuid4().hex[:16]}",
            span_id=f"span_{uuid.uuid4().hex[:8]}",
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            status=TraceStatus.STARTED,
            start_time=datetime.utcnow(),
            end_time=None,
            attributes=attributes or {}
        )
        
        self.traces[trace.trace_id] = trace
        logger.debug(f"Started trace: {operation_name}")
        return trace
    
    def end_trace(self, trace_id: str, status: TraceStatus = TraceStatus.COMPLETED) -> bool:
        """End a trace"""
        if trace_id not in self.traces:
            return False
        
        trace = self.traces[trace_id]
        trace.end_time = datetime.utcnow()
        trace.status = status
        
        logger.debug(f"Ended trace: {trace_id}")
        return True
    
    def add_trace_event(self, trace_id: str, event_name: str, attributes: Dict[str, Any]) -> bool:
        """Add event to trace"""
        if trace_id not in self.traces:
            return False
        
        event = {
            "name": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes
        }
        
        self.traces[trace_id].events.append(event)
        return True
    
    def log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> LogEntry:
        """Record structured log"""
        log_entry = LogEntry(
            log_id=f"log_{uuid.uuid4().hex[:8]}",
            level=level,
            message=message,
            context=context or {},
            trace_id=trace_id
        )
        
        self.logs.append(log_entry)
        
        # Also log to standard logger
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "INFO":
            logger.info(message)
        elif level == "DEBUG":
            logger.debug(message)
        
        return log_entry
    
    def get_metrics(self, metric_name: Optional[str] = None) -> Dict[str, List[Metric]]:
        """Get metrics"""
        if metric_name:
            return {metric_name: self.metrics.get(metric_name, [])}
        return self.metrics
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get metric summary statistics"""
        if metric_name not in self.metrics:
            return {"error": "Metric not found"}
        
        values = [m.value for m in self.metrics[metric_name]]
        
        return {
            "name": metric_name,
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0
        }
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID"""
        return self.traces.get(trace_id)
    
    def get_logs(
        self,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Get logs with optional filtering"""
        logs = self.logs
        
        if level:
            logs = [l for l in logs if l.level == level]
        
        return logs[-limit:]
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        for metric_name, metrics in self.metrics.items():
            if not metrics:
                continue
            
            latest = metrics[-1]
            metric_type = latest.metric_type.value.upper()
            
            lines.append(f"# TYPE {metric_name} {metric_type}")
            
            # Add labels
            labels_str = ",".join([f'{k}="{v}"' for k, v in latest.labels.items()])
            if labels_str:
                lines.append(f"{metric_name}{{{labels_str}}} {latest.value}")
            else:
                lines.append(f"{metric_name} {latest.value}")
        
        return "\n".join(lines)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get telemetry system statistics"""
        metric_counts = {}
        for name, metrics in self.metrics.items():
            metric_counts[name] = len(metrics)
        
        trace_status_counts = {}
        for trace in self.traces.values():
            trace_status_counts[trace.status.value] = trace_status_counts.get(trace.status.value, 0) + 1
        
        log_level_counts = {}
        for log in self.logs:
            log_level_counts[log.level] = log_level_counts.get(log.level, 0) + 1
        
        return {
            "total_metrics": sum(len(m) for m in self.metrics.values()),
            "unique_metrics": len(self.metrics),
            "metric_counts": metric_counts,
            "total_traces": len(self.traces),
            "trace_status_distribution": trace_status_counts,
            "total_logs": len(self.logs),
            "log_level_distribution": log_level_counts
        }


# Global instance
_telemetry: Optional[TelemetrySystem] = None


def get_telemetry() -> TelemetrySystem:
    """Get singleton instance"""
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetrySystem()
    return _telemetry
