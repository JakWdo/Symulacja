"""
Security Headers Middleware

Middleware dodający security headers do wszystkich responses zgodnie z OWASP recommendations:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains (tylko HTTPS)
- Content-Security-Policy: restrykcyjna polityka
- Referrer-Policy: strict-origin-when-cross-origin

Używa Starlette BaseHTTPMiddleware dla compatibility z FastAPI.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from collections.abc import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware dodający security headers do każdego response

    Headers chronią przed:
    - XSS attacks (X-XSS-Protection, Content-Security-Policy)
    - Clickjacking (X-Frame-Options)
    - MIME type sniffing (X-Content-Type-Options)
    - Man-in-the-middle (Strict-Transport-Security dla HTTPS)
    - Information leakage (Referrer-Policy)

    Usage:
        app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.enable_hsts = kwargs.get('enable_hsts', False)  # Włącz tylko na HTTPS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dodaje security headers do response"""
        response = await call_next(request)

        # X-Content-Type-Options: Zapobiega MIME type sniffing
        # Browser nie będzie próbował "zgadywać" typu zawartości
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Zapobiega clickjacking attacks
        # DENY = strona nie może być wyświetlona w iframe/frame
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: Włącza built-in XSS filter w starszych browserach
        # mode=block = blokuje całą stronę jeśli wykryto XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Kontroluje ile informacji jest wysyłane w Referer header
        # strict-origin-when-cross-origin = wysyłaj pełny URL tylko dla same-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Kontroluje dostęp do browser features (dawniej Feature-Policy)
        # Wyłączamy potencjalnie niebezpieczne features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=()"
        )

        # Content-Security-Policy: Restrykcyjna polityka zasobów
        # default-src 'self' = domyślnie tylko same-origin
        # script-src - pozwól inline scripts (potrzebne dla Swagger UI)
        # style-src - pozwól inline styles (potrzebne dla Swagger UI)
        # img-src - pozwól data: URIs (dla base64 images) i same-origin
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # unsafe-eval needed for Swagger
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",  # Równoważne X-Frame-Options: DENY
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Strict-Transport-Security: Wymusza HTTPS (tylko jeśli włączone i request przez HTTPS)
        # max-age=31536000 = 1 rok
        # includeSubDomains = dotyczy też wszystkich subdomen
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
