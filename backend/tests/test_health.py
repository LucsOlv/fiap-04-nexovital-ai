"""Testes do endpoint de health."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "integrations" in data
    assert "azure_speech" in data["integrations"]
    assert "azure_language" in data["integrations"]
    assert "openrouter" in data["integrations"]
