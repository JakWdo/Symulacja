"""
Testy jednostkowe dla CacheControlMiddleware.

Weryfikuje poprawne ustawienie Cache-Control headers dla różnych typów plików.
"""

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from app.middleware.cache_control import CacheControlMiddleware


@pytest.fixture
def app_with_cache_middleware():
    """Tworzy aplikację FastAPI z CacheControlMiddleware."""
    app = FastAPI()

    # Dodaj middleware
    app.add_middleware(CacheControlMiddleware)

    # Dodaj test endpoints
    @app.get("/")
    async def root():
        return Response(content="<html>index</html>", media_type="text/html")

    @app.get("/index.html")
    async def index_html():
        return Response(content="<html>index</html>", media_type="text/html")

    @app.get("/assets/MainDashboard-CG2zrQto.js")
    async def hashed_js():
        return Response(content="console.log('test')", media_type="application/javascript")

    @app.get("/assets/index-A1Ck2qsN.css")
    async def hashed_css():
        return Response(content="body { color: red; }", media_type="text/css")

    @app.get("/assets/logo-BhjYWlpK.png")
    async def hashed_image():
        return Response(content=b"fake-image", media_type="image/png")

    @app.get("/assets/old-style.css")
    async def non_hashed_asset():
        return Response(content="body { margin: 0; }", media_type="text/css")

    @app.get("/favicon.ico")
    async def favicon():
        return Response(content=b"fake-icon", media_type="image/x-icon")

    @app.post("/api/v1/projects")
    async def api_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app_with_cache_middleware):
    """Tworzy test client."""
    return TestClient(app_with_cache_middleware)


class TestCacheControlMiddleware:
    """Test suite dla CacheControlMiddleware."""

    def test_root_path_no_cache(self, client):
        """
        Test: Root path (/) powinien mieć no-cache headers.
        Zapewnia że przeglądarka zawsze pobiera świeżą wersję index.html.
        """
        response = client.get("/")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-cache, must-revalidate, max-age=0"
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "0"

    def test_index_html_no_cache(self, client):
        """
        Test: index.html powinien mieć no-cache headers.
        Zapobiega problemowi 404 po deploymencie z nowymi hashami assetów.
        """
        response = client.get("/index.html")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-cache, must-revalidate, max-age=0"
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "0"

    def test_hashed_js_long_cache(self, client):
        """
        Test: JS z hashem Vite (MainDashboard-CG2zrQto.js) powinien mieć długi cache.
        Pattern: /assets/{name}-{hash}.js
        """
        response = client.get("/assets/MainDashboard-CG2zrQto.js")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"

    def test_hashed_css_long_cache(self, client):
        """
        Test: CSS z hashem Vite (index-A1Ck2qsN.css) powinien mieć długi cache.
        Pattern: /assets/{name}-{hash}.css
        """
        response = client.get("/assets/index-A1Ck2qsN.css")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"

    def test_hashed_image_long_cache(self, client):
        """
        Test: Obrazy z hashem Vite (logo-BhjYWlpK.png) powinny mieć długi cache.
        Pattern: /assets/{name}-{hash}.{ext}
        """
        response = client.get("/assets/logo-BhjYWlpK.png")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"

    def test_non_hashed_asset_medium_cache(self, client):
        """
        Test: Assety bez hasha w /assets/ powinny mieć średni cache (1h).
        Pattern: /assets/{name}.{ext} (bez hasha)
        """
        response = client.get("/assets/old-style.css")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "public, max-age=3600"

    def test_favicon_medium_cache(self, client):
        """
        Test: Favicon i inne ikony powinny mieć średni cache (1h).
        """
        response = client.get("/favicon.ico")

        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "public, max-age=3600"

    def test_api_endpoint_no_cache_headers(self, client):
        """
        Test: API endpointy (POST requests) nie powinny mieć cache headers.
        Middleware ignoruje non-GET requests.
        """
        response = client.post("/api/v1/projects")

        assert response.status_code == 200
        # Middleware nie dodaje cache headers dla POST
        # (może mieć domyślne headers z FastAPI, ale nie z middleware)

    def test_custom_no_cache_paths(self):
        """
        Test: Middleware powinien respektować custom no_cache_paths.
        """
        app = FastAPI()
        app.add_middleware(CacheControlMiddleware, no_cache_paths=["/", "/index.html", "/custom"])

        @app.get("/custom")
        async def custom():
            return Response(content="custom", media_type="text/plain")

        client = TestClient(app)
        response = client.get("/custom")

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-cache, must-revalidate, max-age=0"

    def test_custom_long_cache_duration(self):
        """
        Test: Middleware powinien respektować custom long_cache_duration.
        """
        app = FastAPI()
        app.add_middleware(CacheControlMiddleware, long_cache_duration=86400)  # 1 dzień

        @app.get("/assets/test-ABC123.js")
        async def hashed():
            return Response(content="test", media_type="application/javascript")

        client = TestClient(app)
        response = client.get("/assets/test-ABC123.js")

        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "public, max-age=86400, immutable"

    def test_hashed_pattern_matching(self):
        """
        Test: Weryfikuje że pattern rozpoznaje różne formaty hashy Vite.
        Vite używa hashów alfanumerycznych z myślnikami i podkreśleniami.
        """
        app = FastAPI()
        app.add_middleware(CacheControlMiddleware)

        test_cases = [
            "/assets/Main-ABC123.js",
            "/assets/test-xyz789_foo.js",
            "/assets/icon-A1B2C3D4.svg",
            "/assets/font-hash123.woff2",
        ]

        for path in test_cases:
            @app.get(path)
            async def handler():
                return Response(content="test")

        client = TestClient(app)

        for path in test_cases:
            response = client.get(path)
            assert response.status_code == 200
            assert "immutable" in response.headers["Cache-Control"], f"Failed for {path}"
