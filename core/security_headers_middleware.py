"""AsimNexus Security Headers Middleware — VAPT Compliance & Hardened Security"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("AsimNexus.Security")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects security headers into every HTTP response.

    Complies with OWASP Secure Headers Project recommendations,
    VAPT requirements, and Nepal IT Act 2063 guidelines.
    """

    # ── Hardened security headers ────────────────────────────────
    HEADERS = {
        # Prevent MIME-type sniffing
        "X-Content-Type-Options": "nosniff",

        # Prevent clickjacking
        "X-Frame-Options": "DENY",

        # Enable XSS filter in legacy browsers
        "X-XSS-Protection": "1; mode=block",

        # Enforce HTTPS for 1 year (include subdomains)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

        # Content Security Policy — restrict resources to same origin
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "object-src 'none'"
        ),

        # Referrer policy — minimal leakage
        "Referrer-Policy": "strict-origin-when-cross-origin",

        # Disable caching of sensitive responses
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",

        # Permissions Policy — restrict browser features
        "Permissions-Policy": (
            "camera=(), microphone=(), geolocation=(), "
            "fullscreen=(self), payment=(), usb=(), "
            "magnetometer=(), accelerometer=(), gyroscope=()"
        ),

        # Cross-Origin isolation
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Resource-Policy": "same-origin",
    }

    # ── Paths that should NOT have strict cache headers ──────────
    CACHEABLE_PREFIXES = ("/static/", "/assets/", "/favicon")

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path

        for header, value in self.HEADERS.items():
            # Skip Cache-Control for static assets
            if header in ("Cache-Control", "Pragma", "Expires") and any(
                path.startswith(p) for p in self.CACHEABLE_PREFIXES
            ):
                continue
            response.headers[header] = value

        # Add correlation ID if present in request
        correlation_id = request.headers.get("X-Correlation-ID")
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id

        return response
