"""AsimNexus monitoring module."""

# Re-export from root-level module: monitoring_middleware.py
from core.monitoring_middleware import (
    PrometheusMonitoringMiddleware,
    get_monitoring,
)



# Re-export from root-level module: prometheus_metrics.py
from core.prometheus_metrics import (
    generate_metrics,
    get_metrics_dict,
    record_auth_event,
    record_federation_event,
    record_http_request,
    set_dreaming_metrics,
    set_evolution_metrics,
    set_mesh_metrics,
    set_self_awareness_metrics,
)



# Re-export from root-level module: structured_logger.py
from core.structured_logger import (
    StructuredFormatter,
    StructuredLogger,
    generate_correlation_id,
    get_correlation_id,
    get_logger,
    reset_loggers,
    set_correlation_id,
    with_correlation_id,
)



# Re-export from root-level module: telemetry_schema.py
from core.telemetry_schema import (
    VALID_ACTIONS,
    VALID_COMPONENTS,
    VALID_MODES,
    VALID_POSTURES,
    VALID_PRIVACY_LEVELS,
    VALID_SEVERITIES,
    VALID_STATUSES,
    event_to_json,
    normalize_event,
    validate_event,
)
