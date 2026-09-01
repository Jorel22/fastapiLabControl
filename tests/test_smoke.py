"""Pruebas de humo: la app arranca y responde."""


def test_health_ok(client):
    """DoD: /api/health responde 200 con estado ok."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_index_ok(client):
    """La página de inicio de la API responde correctamente."""
    resp = client.get("/api/")
    assert resp.status_code == 200
    assert resp.json()["app"] == "LabControl Mecánica ESPOCH API"


def test_docs_ok(client):
    """Swagger UI /docs responde 200 y contiene la interfaz Swagger."""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "swagger-ui" in resp.text.lower()


def test_redoc_ok(client):
    """ReDoc /redoc responde 200 y contiene la interfaz ReDoc."""
    resp = client.get("/redoc")
    assert resp.status_code == 200
    assert "redoc" in resp.text.lower()


def test_openapi_ok(client):
    """OpenAPI JSON responde 200 con el esquema de la API."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["info"]["title"] == "LabControl Mecánica ESPOCH API"
    assert "/api/bienes" in data["paths"]
