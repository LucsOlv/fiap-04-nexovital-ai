"""Anonimização de dados do paciente antes de envio a serviços externos."""

from __future__ import annotations

from typing import Any

# Campos que contêm PII e devem ser removidos antes de enviar a APIs externas
_PII_FIELDS = {"name", "id", "sex", "age"}


def strip_patient_pii(patient: dict[str, Any] | None) -> dict[str, Any]:
    """Remove campos de identificação pessoal do paciente.

    Retorna uma cópia com apenas os campos não sensíveis (summary, notes,
    previous_medications, has_history). O campo 'id' é substituído por hash
    parcial para manter rastreabilidade sem expor identidade.
    """
    if not patient:
        return {}

    safe: dict[str, Any] = {}
    for key, value in patient.items():
        if key in _PII_FIELDS:
            continue
        safe[key] = value

    # Substitui ID real por referência opaca
    original_id = patient.get("id", "unknown")
    safe["patient_ref"] = f"patient-{hash(original_id) & 0xFFFF:04x}"

    return safe
