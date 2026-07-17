"""Fixtures dos 3 pacientes de demonstração (spec §5)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

PATIENTS = [
    {
        "id": "patient-altered",
        "name": "Carlos Mendes",
        "age": 58,
        "sex": "M",
        "summary": "Paciente com histórico de DPOC, apresentando piora respiratória recente. "
        "Relata cansaço e falta de ar nos últimos 3 dias. SpO2 em queda e frequência "
        "respiratória aumentada.",
        "notes": "Ex-tabagista (cessou há 5 anos). Internação prévia por exacerbação de DPOC "
        "há 3 meses. Medicamento para hipertensão alterado recentemente.",
        "previous_medications": [
            {"name": "Enalapril", "dose": "10mg", "frequency": "12/12h"},
            {"name": "Salbutamol", "dose": "100mcg", "frequency": "6/6h"},
            {"name": "Ipratrópio", "dose": "20mcg", "frequency": "6/6h"},
        ],
        "has_history": True,
    },
    {
        "id": "patient-healthy",
        "name": "Ana Beatriz Silva",
        "age": 34,
        "sex": "F",
        "summary": "Paciente em acompanhamento de rotina pós-cirúrgico. Sem queixas. "
        "Sinais vitais dentro da normalidade. Boa evolução.",
        "notes": "Apendicectomia há 30 dias. Sem intercorrências. Retorno para liberação "
        "de atividades físicas.",
        "previous_medications": [
            {"name": "Dipirona", "dose": "500mg", "frequency": "6/6h (se dor)"},
        ],
        "has_history": True,
    },
    {
        "id": "patient-neuro-no-history",
        "name": "Rafael Oliveira",
        "age": 42,
        "sex": "M",
        "summary": "Paciente com quadro neurológico em investigação. Primeira consulta "
        "nesta unidade. Sem exames ou registros anteriores no sistema.",
        "notes": "Encaminhado por neurologista externo. Relata episódios de fraqueza "
        "e dormência em membros inferiores. Sem diagnóstico fechado. "
        "Nenhum exame prévio disponível no sistema.",
        "previous_medications": [],
        "has_history": False,
    },
]

router = APIRouter(tags=["patients"])


@router.get("/api/demo-patients")
def get_demo_patients() -> list[dict[str, Any]]:
    return PATIENTS
