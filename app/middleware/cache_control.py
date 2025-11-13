"""
Middleware do zarządzania Cache-Control headers dla statycznych plików.

Rozwiązuje problem browser cache który powoduje 404 dla assetów po deploymencie:
- index.html: no-cache (zawsze świeża wersja)
- Assets z hashami (/assets/*.js, *.css): długi cache (optymalizacja)
"""

import re
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware ustawiający odpowiednie Cache-Control headers dla statycznych plików.

    Strategia cache:
    1. index.html → no-cache, must-revalidate (zawsze pobieraj świeżą wersję)
    2. Assets z hashami (*.js, *.css w /assets/) → długi cache z immutable
    3. Inne statyczne pliki → domyślny cache

    Rozwiązuje problem:
    Vite generuje nowe hashe dla plików przy każdym buildzie (MainDashboard-ABC123.js).
    Bez tej polityki cache, przeglądarka może mieć stary index.html który referencuje
    nieistniejące pliki z poprzedniego deploymentu → 404 errors.
    """

    # Pattern dla assetów z hashami Vite (np. MainDashboard-CG2zrQto.js)
    # Wymaga: /assets/{name}-{hash}.{ext} gdzie hash to min 6 znaków alfanumerycznych
    # Vite używa 8-12 znakowych hashów (base64url), więc min 6 znaków filtruje false positives
    HASHED_ASSET_PATTERN = re.compile(r'^/assets/[^/]+-[a-zA-Z0-9_]{6,}\.(js|css|woff2?|ttf|eot|svg|png|jpg|jpeg|gif|webp)$')

    def __init__(
        self,
        app: ASGIApp,
        no_cache_paths: list[str] | None = None,
        long_cache_duration: int = 31536000,  # 1 rok w sekundach
    ):
        """
        Args:
            app: ASGI application
            no_cache_paths: Lista ścieżek które nigdy nie powinny być cache'owane
                           (domyślnie: ["/", "/index.html"])
            long_cache_duration: Czas cache dla assetów z hashami w sekundach
                                (domyślnie: 31536000 = 1 rok)
        """
        super().__init__(app)
        self.no_cache_paths = no_cache_paths or ["/", "/index.html"]
        self.long_cache_duration = long_cache_duration

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Przetwarza request i dodaje odpowiednie Cache-Control headers do response.
        """
        response = await call_next(request)

        # Tylko dla GET requests (cache nie ma sensu dla POST/PUT/DELETE)
        if request.method != "GET":
            return response

        path = request.url.path

        # 1. No-cache dla index.html (zawsze świeża wersja)
        if path in self.no_cache_paths:
            response.headers["Cache-Control"] = "no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"  # HTTP/1.0 backwards compatibility
            response.headers["Expires"] = "0"

        # 2. Długi cache z immutable dla assetów z hashami Vite
        elif self.HASHED_ASSET_PATTERN.match(path):
            response.headers["Cache-Control"] = (
                f"public, max-age={self.long_cache_duration}, immutable"
            )

        # 3. Średni cache dla innych statycznych plików (np. favicon.ico)
        elif path.startswith("/assets/") or any(
            path.endswith(ext) for ext in [".ico", ".png", ".jpg", ".svg", ".webp"]
        ):
            response.headers["Cache-Control"] = "public, max-age=3600"  # 1 godzina

        return response
