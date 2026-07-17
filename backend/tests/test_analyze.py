"""Teste de integração local do endpoint principal, sem substituir analisadores."""

import json
from pathlib import Path

from app.core.config import settings
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_analyze_processes_real_csv_and_medications() -> None:
    patient = {
        "id": "patient-altered",
        "name": "Carlos Mendes",
        "age": 58,
        "sex": "M",
        "summary": "Paciente fictício com piora respiratória.",
        "notes": "Caso sintético de teste.",
        "previous_medications": [
            {"name": "Enalapril", "dose": "10mg", "frequency": "12/12h"},
        ],
        "has_history": True,
    }
    medications = [
        {"name": "Enalapril", "dose": "20mg", "frequency": "12/12h"},
    ]
    csv_path = REPO_ROOT / "demo-data" / "patient-altered" / "vitals.csv"

    original_key = settings.openrouter_api_key
    settings.openrouter_api_key = ""
    try:
        with csv_path.open("rb") as csv_file:
            response = client.post(
                "/api/analyze",
                data={
                    "patient": json.dumps(patient),
                    "medications": json.dumps(medications),
                },
                files={"vitals_csv": ("vitals.csv", csv_file, "text/csv")},
            )
    finally:
        settings.openrouter_api_key = original_key

    assert response.status_code == 200
    result = response.json()
    assert result["available_modalities"] == ["vitals", "medications"]
    assert set(result["missing_modalities"]) == {"video", "audio", "text"}
    assert result["vitals"]["status"] == "ok"
    assert result["vitals"]["findings"]
    assert result["medications"]["status"] == "ok"
    assert result["medications"]["findings"][0]["type"] == "modified"
    assert 0 <= result["score"] <= 100
    assert result["score"] < 100
    assert result["risk_level"] in {"NORMAL", "ATENÇÃO", "ALERTA"}
    assert result["ai_report"]["summary"] == "Relatório IA não disponível para esta análise."
    assert "NÃO constitui diagnóstico médico" in result["disclaimer"]
