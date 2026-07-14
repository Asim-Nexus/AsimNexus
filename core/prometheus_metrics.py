"""
AsimNexus Prometheus Metrics Exporter
======================================
Exposes Prometheus-compatible metrics in text format for scraping by Prometheus.

Provides:
  - HTTP request counters (total, by status, by method, by path)
  - HTTP request latency histogram
  - Self-awareness metrics (modules, routes, issues, build actions)
  - Mesh network metrics (peers, sync messages)
  - Evolution engine metrics (suggestions, approvals, applications)
  - Dreaming engine metrics (cycles, lessons)
  - Auth metrics (logins, failed logins)
  - Federation metrics (sync messages, handshakes)
  - System metrics (memory, CPU, uptime)
"""

import os
import time
import json
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone


# ── Thread-safe metric store ──────────────────────────────────

_lock = threading.Lock()

# Counters
_http_requests_total: Dict[str, int] = defaultdict(int)  # key: "method:path:status"
_http_request_duration_buckets: Dict[str, List[float]] = defaultdict(list)  # key: "method:path"
_http_duration_bucket_edges = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

# Self-awareness
_self_awareness_modules_total = 0
_self_awareness_routes_total = 0
_self_awareness_issues_total = 0
_self_awareness_open_issues_total = 0
_self_awareness_build_actions_total = 0
_self_awareness_last_scan_timestamp = 0.0

# Mesh
_mesh_connected_peers = 0
_mesh_sync_messages_total = 0

# Evolution
_evolution_suggestions_total = 0
_evolution_suggestions_approved_total = 0
_evolution_suggestions_applied_total = 0

# Dreaming
_dreaming_cycles_total = 0
_dreaming_lessons_extracted_total = 0

# Auth
_auth_logins_total = 0
_auth_failed_logins_total = 0

# Federation
_federation_sync_messages_total = 0
_federation_handshakes_total = 0

# System
_start_time = time.time()


# ── Public API ────────────────────────────────────────────────

def record_http_request(method: str, path: str, status_code: int, duration: float) -> None:
    """Record an HTTP request with its duration."""
    with _lock:
        key = f"{method}:{path}:{status_code}"
        _http_requests_total[key] += 1
        bucket_key = f"{method}:{path}"
        _http_request_duration_buckets[bucket_key].append(duration)


def set_self_awareness_metrics(
    modules: int = 0,
    routes: int = 0,
    issues_total: int = 0,
    issues_open: int = 0,
    build_actions: int = 0,
) -> None:
    """Update self-awareness metrics."""
    global _self_awareness_modules_total, _self_awareness_routes_total
    global _self_awareness_issues_total, _self_awareness_open_issues_total
    global _self_awareness_build_actions_total, _self_awareness_last_scan_timestamp
    with _lock:
        _self_awareness_modules_total = modules
        _self_awareness_routes_total = routes
        _self_awareness_issues_total = issues_total
        _self_awareness_open_issues_total = issues_open
        _self_awareness_build_actions_total = build_actions
        _self_awareness_last_scan_timestamp = time.time()


def set_mesh_metrics(peers: int = 0, sync_messages: int = 0) -> None:
    """Update mesh network metrics."""
    global _mesh_connected_peers, _mesh_sync_messages_total
    with _lock:
        _mesh_connected_peers = peers
        _mesh_sync_messages_total = sync_messages


def set_evolution_metrics(total: int = 0, approved: int = 0, applied: int = 0) -> None:
    """Update evolution engine metrics."""
    global _evolution_suggestions_total, _evolution_suggestions_approved_total
    global _evolution_suggestions_applied_total
    with _lock:
        _evolution_suggestions_total = total
        _evolution_suggestions_approved_total = approved
        _evolution_suggestions_applied_total = applied


def set_dreaming_metrics(cycles: int = 0, lessons: int = 0) -> None:
    """Update dreaming engine metrics."""
    global _dreaming_cycles_total, _dreaming_lessons_extracted_total
    with _lock:
        _dreaming_cycles_total = cycles
        _dreaming_lessons_extracted_total = lessons


def record_auth_event(success: bool) -> None:
    """Record an authentication event."""
    with _lock:
        if success:
            global _auth_logins_total
            _auth_logins_total += 1
        else:
            global _auth_failed_logins_total
            _auth_failed_logins_total += 1


def record_federation_event(sync: bool = False, handshake: bool = False) -> None:
    """Record a federation protocol event."""
    with _lock:
        if sync:
            global _federation_sync_messages_total
            _federation_sync_messages_total += 1
        if handshake:
            global _federation_handshakes_total
            _federation_handshakes_total += 1


# ── Metrics Generation ────────────────────────────────────────

def _format_metric_line(name: str, value: float, labels: Optional[Dict[str, str]] = None,
                        help_text: Optional[str] = None, metric_type: Optional[str] = None) -> str:
    """Format a single metric line in Prometheus text format."""
    lines = []
    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    if metric_type:
        lines.append(f"# TYPE {name} {metric_type}")
    if labels:
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        lines.append(f'{name}{{{label_str}}} {value}')
    else:
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"


def generate_metrics() -> str:
    """Generate the full Prometheus metrics output."""
    with _lock:
        lines = []

        # ── HTTP Metrics ──────────────────────────────────────
        lines.append("# ── HTTP Metrics ──────────────────────────────\n")
        for key, count in sorted(_http_requests_total.items()):
            method, path, status = key.split(":", 2)
            lines.append(
                _format_metric_line(
                    "http_requests_total", float(count),
                    {"method": method, "path": path, "status": status},
                    "Total HTTP requests by method, path, and status", "counter",
                )
            )

        # Duration histogram
        for bucket_key, durations in _http_request_duration_buckets.items():
            method, path = bucket_key.split(":", 1)
            for edge in _http_duration_bucket_edges:
                count = sum(1 for d in durations if d <= edge)
                lines.append(
                    _format_metric_line(
                        "http_request_duration_seconds_bucket", float(count),
                        {"method": method, "path": path, "le": str(edge)},
                        "", "histogram",
                    )
                )
            # +Inf bucket
            lines.append(
                _format_metric_line(
                    "http_request_duration_seconds_bucket", float(len(durations)),
                    {"method": method, "path": path, "le": "+Inf"},
                    "", "histogram",
                )
            )
            # Count and sum
            lines.append(
                _format_metric_line(
                    "http_request_duration_seconds_count", float(len(durations)),
                    {"method": method, "path": path}, "", "histogram",
                )
            )
            lines.append(
                _format_metric_line(
                    "http_request_duration_seconds_sum", sum(durations),
                    {"method": method, "path": path}, "", "histogram",
                )
            )

        # ── Self-Awareness Metrics ────────────────────────────
        lines.append("\n# ── Self-Awareness Metrics ───────────────────────\n")
        lines.append(_format_metric_line(
            "self_awareness_modules_total", float(_self_awareness_modules_total),
            help_text="Total number of known modules", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "self_awareness_routes_total", float(_self_awareness_routes_total),
            help_text="Total number of registered routes", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "self_awareness_issues_total", float(_self_awareness_issues_total),
            help_text="Total number of issues", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "self_awareness_open_issues_total", float(_self_awareness_open_issues_total),
            help_text="Number of open issues", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "self_awareness_build_actions_total", float(_self_awareness_build_actions_total),
            help_text="Total number of build actions performed", metric_type="counter",
        ))
        lines.append(_format_metric_line(
            "self_awareness_last_scan_timestamp_seconds", _self_awareness_last_scan_timestamp,
            help_text="Timestamp of the last codebase scan", metric_type="gauge",
        ))

        # ── Mesh Metrics ──────────────────────────────────────
        lines.append("\n# ── Mesh Network Metrics ─────────────────────────\n")
        lines.append(_format_metric_line(
            "mesh_connected_peers", float(_mesh_connected_peers),
            help_text="Number of connected mesh peers", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "mesh_sync_messages_total", float(_mesh_sync_messages_total),
            help_text="Total number of mesh sync messages", metric_type="counter",
        ))

        # ── Evolution Metrics ─────────────────────────────────
        lines.append("\n# ── Evolution Engine Metrics ─────────────────────\n")
        lines.append(_format_metric_line(
            "evolution_suggestions_total", float(_evolution_suggestions_total),
            help_text="Total number of evolution suggestions", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "evolution_suggestions_approved_total", float(_evolution_suggestions_approved_total),
            help_text="Total number of approved suggestions", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "evolution_suggestions_applied_total", float(_evolution_suggestions_applied_total),
            help_text="Total number of applied suggestions", metric_type="gauge",
        ))

        # ── Dreaming Metrics ──────────────────────────────────
        lines.append("\n# ── Dreaming Engine Metrics ──────────────────────\n")
        lines.append(_format_metric_line(
            "dreaming_cycles_total", float(_dreaming_cycles_total),
            help_text="Total number of dreaming cycles", metric_type="counter",
        ))
        lines.append(_format_metric_line(
            "dreaming_lessons_extracted_total", float(_dreaming_lessons_extracted_total),
            help_text="Total number of lessons extracted", metric_type="counter",
        ))

        # ── Auth Metrics ──────────────────────────────────────
        lines.append("\n# ── Authentication Metrics ───────────────────────\n")
        lines.append(_format_metric_line(
            "auth_logins_total", float(_auth_logins_total),
            help_text="Total number of successful logins", metric_type="counter",
        ))
        lines.append(_format_metric_line(
            "auth_failed_logins_total", float(_auth_failed_logins_total),
            help_text="Total number of failed login attempts", metric_type="counter",
        ))

        # ── Federation Metrics ────────────────────────────────
        lines.append("\n# ── Federation Metrics ───────────────────────────\n")
        lines.append(_format_metric_line(
            "federation_sync_messages_total", float(_federation_sync_messages_total),
            help_text="Total number of federation sync messages", metric_type="counter",
        ))
        lines.append(_format_metric_line(
            "federation_handshakes_total", float(_federation_handshakes_total),
            help_text="Total number of federation handshakes", metric_type="counter",
        ))

        # ── System Metrics ────────────────────────────────────
        lines.append("\n# ── System Metrics ───────────────────────────────\n")
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        lines.append(_format_metric_line(
            "process_resident_memory_bytes", float(mem_info.rss),
            help_text="Resident memory size in bytes", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "process_virtual_memory_bytes", float(mem_info.vms),
            help_text="Virtual memory size in bytes", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "process_cpu_percent", process.cpu_percent(interval=0),
            help_text="CPU usage percentage", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "process_open_fds", float(process.num_fds()),
            help_text="Number of open file descriptors", metric_type="gauge",
        ))
        uptime_seconds = time.time() - _start_time
        lines.append(_format_metric_line(
            "process_uptime_seconds", uptime_seconds,
            help_text="Process uptime in seconds", metric_type="gauge",
        ))
        lines.append(_format_metric_line(
            "process_start_time_seconds", _start_time,
            help_text="Process start time in Unix seconds", metric_type="gauge",
        ))

        return "".join(lines)


def get_metrics_dict() -> Dict[str, Any]:
    """Get metrics as a JSON-serializable dict (for backward compatibility)."""
    with _lock:
        return {
            "http_requests_total": dict(_http_requests_total),
            "self_awareness": {
                "modules": _self_awareness_modules_total,
                "routes": _self_awareness_routes_total,
                "issues_total": _self_awareness_issues_total,
                "issues_open": _self_awareness_open_issues_total,
                "build_actions": _self_awareness_build_actions_total,
                "last_scan": _self_awareness_last_scan_timestamp,
            },
            "mesh": {
                "connected_peers": _mesh_connected_peers,
                "sync_messages": _mesh_sync_messages_total,
            },
            "evolution": {
                "suggestions_total": _evolution_suggestions_total,
                "suggestions_approved": _evolution_suggestions_approved_total,
                "suggestions_applied": _evolution_suggestions_applied_total,
            },
            "dreaming": {
                "cycles": _dreaming_cycles_total,
                "lessons": _dreaming_lessons_extracted_total,
            },
            "auth": {
                "logins": _auth_logins_total,
                "failed_logins": _auth_failed_logins_total,
            },
            "federation": {
                "sync_messages": _federation_sync_messages_total,
                "handshakes": _federation_handshakes_total,
            },
            "uptime_seconds": time.time() - _start_time,
        }
