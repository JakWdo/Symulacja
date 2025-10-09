"""Testy integracyjne dla głównych endpointów FastAPI."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_root_endpoint_returns_basic_info():
    """Endpoint główny powinien zwracać nazwę projektu i status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"]
    assert data["status"] == "operational"


def test_health_endpoint_reports_status():
    """Health check powinien informować o zdrowiu aplikacji."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_global_exception_handler(monkeypatch):
    """Błędy powinny być przechwytywane przez globalny handler."""

    async def boom():  # pragma: no cover - definicja pomocnicza
        raise RuntimeError("boom")

    app.add_api_route("/test-error", boom)

    try:
        response = client.get("/test-error")
        assert response.status_code == 500
        body = response.json()
        assert body["detail"] == "Internal server error"
        assert "error" in body
    finally:
        # Sprzątanie - usuń testową trasę
        app.router.routes = [route for route in app.router.routes if getattr(route, "path", None) != "/test-error"]
