"""Testes do endpoint de pacientes demo."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_patients_returns_three_patients():
    response = client.get("/api/demo-patients")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    ids = {p["id"] for p in data}
    assert ids == {"patient-altered", "patient-healthy", "patient-neuro-no-history"}


def test_demo_patients_have_required_fields():
    response = client.get("/api/demo-patients")
    data = response.json()
    for patient in data:
        assert "id" in patient
        assert "name" in patient
        assert "age" in patient
        assert "sex" in patient
        assert patient["sex"] in ("M", "F")
        assert "summary" in patient
        assert "has_history" in patient
        assert isinstance(patient["has_history"], bool)
