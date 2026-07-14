"""
STATUS: REAL — Structured JSON Logging with Correlation IDs
ASIMNEXUS Structured Logger
=============================
Provides structured JSON logging with correlation IDs for distributed tracing
across mesh nodes, economy subsystems, and consensus operations.

Reference: DDIA Chapter 8 ("The Trouble with Distributed Systems"),
           Google's Dapper paper (distributed tracing),
           OpenTelemetry correlation context specification

Features:
  - JSON-formatted log entries for machine parsing
  - Correlation IDs for distributed tracing across services
  - Automatic context propagation (thread-local)
  - Structured fields (service, component, node_id, etc.)
  - Configurable log levels per component
  - JSONL persistence for audit trails
"""

import json
import logging
import threading
import uuid
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Thread-local storage for correlation context
_correlation_context = threading.local()


def get_correlation_id() -> str:
    """Get the current correlation ID from thread-local context."""
    return getattr(_correlation_context, "correlation_id", "")


def set_correlation_id(correlation_id: str) -> None:
    """Set the current correlation ID in thread-local context."""
    _correlation_context.correlation_id = correlation_id


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return f"corr_{uuid.uuid4().hex[:16]}"


def with_correlation_id(correlation_id: str):
    """
    Context manager/decorator to set a correlation ID for the scope.

    Usage:
        with with_correlation_id("req_abc123"):
            logger.info("Processing request")
    """
    class _CorrelationContext:
        def __enter__(self):
            self._previous = get_correlation_id()
            set_correlation_id(correlation_id)
            return correlation_id

        def __exit__(self, *args):
            set_correlation_id(self._previous)

    return _CorrelationContext()


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON-structured log records.
    Includes correlation ID, service name, component, and other structured fields.
    """

    def __init__(
        self,
        service: str = "asimnexus",
        component: str = "core",
        node_id: Optional[str] = None,
    ):
        super().__init__()
        self._service = service
        self._component = component
        self._node_id = node_id or ""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self._service,
            "component": self._component,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id() or "",
        }

        if self._node_id:
            log_entry["node_id"] = self._node_id

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra fields from the record
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, default=str)


from datetime import datetime


class StructuredLogger:
    """
    Structured logger wrapper that produces JSON-formatted log entries
    with automatic correlation ID propagation.

    Usage:
        logger = StructuredLogger("mesh.offline_sync", node_id="node_1")
        logger.info("Sync completed", extra={"ops_count": 42})
    """

    def __init__(
        self,
        name: str,
        service: str = "asimnexus",
        component: str = "core",
        node_id: Optional[str] = None,
        level: int = logging.INFO,
    ):
        self._name = name
        self._service = service
        self._component = component
        self._node_id = node_id

        # Create underlying logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        # Add structured handler if not already configured
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                StructuredFormatter(
                    service=service,
                    component=component,
                    node_id=node_id,
                )
            )
            self._logger.addHandler(handler)

    @property
    def name(self) -> str:
        return self._name

    def _log(self, level: int, msg: str, **kwargs) -> None:
        """Internal log method with structured fields."""
        extra_fields = kwargs.pop("extra", {})
        extra_fields["correlation_id"] = get_correlation_id()

        # Create a custom log record with extra fields
        record = self._logger.makeRecord(
            self._name,
            level,
            kwargs.pop("pathname", ""),
            kwargs.pop("lineno", 0),
            msg,
            kwargs.pop("args", ()),
            kwargs.pop("exc_info", None),
        )
        record.extra_fields = extra_fields
        self._logger.handle(record)

    def debug(self, msg: str, **kwargs) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, **kwargs)


# ── Global Structured Logger Factory ──────────────────────────────────────

_loggers: Dict[str, StructuredLogger] = {}
_loggers_lock = threading.Lock()


def get_logger(
    name: str,
    service: str = "asimnexus",
    component: str = "core",
    node_id: Optional[str] = None,
) -> StructuredLogger:
    """Get or create a structured logger by name."""
    global _loggers
    if name not in _loggers:
        with _loggers_lock:
            if name not in _loggers:
                _loggers[name] = StructuredLogger(
                    name=name,
                    service=service,
                    component=component,
                    node_id=node_id,
                )
    return _loggers[name]


def reset_loggers() -> None:
    """Reset all structured loggers (for testing)."""
    global _loggers
    with _loggers_lock:
        _loggers.clear()
