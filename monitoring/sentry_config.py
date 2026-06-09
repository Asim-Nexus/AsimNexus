"""
ASIMNEXUS Sentry / APM Integration
===================================
Centralized Sentry SDK initialization for performance monitoring
and error tracking across all ASIMNEXUS components.

Usage:
    from monitoring.sentry_config import init_sentry, AsimSentryMiddleware

    init_sentry()
    app.add_middleware(AsimSentryMiddleware)

Environment Variables:
    SENTRY_DSN              — Sentry DSN string (required for Sentry to work)
    ASIM_SENTRY_ENABLED     — Set to "true" to enable (default: true if DSN present)
    ASIM_SENTRY_ENVIRONMENT — Environment label: production, staging, dev (default: production)
    ASIM_SENTRY_TRACES_RATE — Sampling rate for traces, 0.0–1.0 (default: 0.2)
    ASIM_SENTRY_PROFILES_RATE — Sampling rate for profiling, 0.0–1.0 (default: 0.1)
"""

import os
import logging

logger = logging.getLogger("AsimNexus.Sentry")

# Sentinel singleton — prevents double-init if create_app is called repeatedly
_sentry_initialized = False


def init_sentry(
    dsn: str | None = None,
    environment: str | None = None,
    traces_sample_rate: float | None = None,
    profiles_sample_rate: float | None = None,
) -> bool:
    """
    Initialize the Sentry SDK for error tracking & APM.

    Returns True if Sentry was initialized successfully, False otherwise.

    Parameters
    ----------
    dsn : str, optional
        Sentry DSN. Falls back to ``SENTRY_DSN`` env var.
    environment : str, optional
        Deployment environment. Falls back to ``ASIM_SENTRY_ENVIRONMENT`` or
        ``ASIM_ENV`` or ``"production"``.
    traces_sample_rate : float, optional
        Performance tracing sample rate (0.0–1.0).
    profiles_sample_rate : float, optional
        Profiling sample rate (0.0–1.0).
    """
    global _sentry_initialized

    if _sentry_initialized:
        logger.debug("Sentry already initialized — skipping")
        return True

    dsn = dsn or os.environ.get("SENTRY_DSN")
    if not dsn:
        logger.info("SENTRY_DSN not set — Sentry/APM disabled")
        return False

    enabled = os.environ.get("ASIM_SENTRY_ENABLED", "true").lower()
    if enabled not in ("true", "1", "yes"):
        logger.info("ASIM_SENTRY_ENABLED=false — Sentry/APM disabled")
        return False

    environment = (
        environment
        or os.environ.get("ASIM_SENTRY_ENVIRONMENT")
        or os.environ.get("ASIM_ENV", "production")
    )
    traces_sample_rate = traces_sample_rate or float(
        os.environ.get("ASIM_SENTRY_TRACES_RATE", "0.2")
    )
    profiles_sample_rate = profiles_sample_rate or float(
        os.environ.get("ASIM_SENTRY_PROFILES_RATE", "0.1")
    )

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
    except ImportError:
        logger.warning("sentry-sdk package not installed — Sentry/APM disabled")
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            enable_tracing=True,
            attach_stacktrace=True,
            send_default_pii=False,
            max_request_body_size="never",
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
                AsyncioIntegration(),
            ],
            before_send=_before_send,
        )
        _sentry_initialized = True
        logger.info(
            "Sentry initialized — environment=%s traces_rate=%.2f profiles_rate=%.2f",
            environment,
            traces_sample_rate,
            profiles_sample_rate,
        )
        return True
    except Exception as exc:
        logger.warning("Sentry init failed: %s", exc)
        return False


def _before_send(event: dict, hint: dict) -> dict | None:
    """
    Pre-process / filter Sentry events before they are sent.

    - Drops events containing known non-actionable errors.
    - Anonymises any sensitive keys in the extra data.
    """
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type = exc_info[0].__name__ if exc_info[0] else ""
        exc_msg = str(exc_info[1]) if exc_info[1] else ""

        # Drop common non-actionable noise
        noisy = ("ConnectionResetError", "BrokenPipeError", "CancelledError")
        if exc_type in noisy:
            return None

        # Ignore health-check 404s
        if "GET /health" in exc_msg or "GET /healthz" in exc_msg:
            return None

    # Sanitise sensitive tags / extra
    if "extra" in event and isinstance(event["extra"], dict):
        sensitive_keys = {"password", "secret", "token", "api_key", "authorization"}
        event["extra"] = {
            k: ("[redacted]" if k.lower() in sensitive_keys else v)
            for k, v in event["extra"].items()
        }

    return event


class AsimSentryMiddleware:
    """
    FastAPI middleware that attaches ASIMNEXUS-specific Sentry tags
    (release channel, sector mode, node ID) to each request scope.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        import sentry_sdk

        with sentry_sdk.configure_scope() as s:
            s.set_tag("asim.release", os.environ.get("ASIM_RELEASE_CHANNEL", "stable"))
            s.set_tag("asim.sector_mode", os.environ.get("ASIM_SECTOR_MODE", "monolithic"))
            s.set_tag("asim.node_id", os.environ.get("ASIM_NODE_ID", "unknown"))
            s.set_tag("asim.version", os.environ.get("ASIM_VERSION", "2.0.0"))
        await self.app(scope, receive, send)
