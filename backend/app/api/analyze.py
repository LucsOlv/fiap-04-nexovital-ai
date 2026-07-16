"""Endpoint principal de análise multimodal — POST /api/analyze (spec §11)."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile, status

from app.core.config import settings
from app.graph import build_graph
from app.schemas.analysis import (
    AiReport,
    AnalysisResponse,
    AnalyzerOutput,
)
from app.state import AnalysisState

logger = logging.getLogger("nexovital.api.analyze")

router = APIRouter(tags=["analysis"])

# Singleton — compilado uma vez e reusado
_graph = build_graph()


@router.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    # Patient snapshot (JSON string)
    patient: Annotated[str, Form(description="Snapshot JSON do paciente")] = "",
    # Optional files
    video: UploadFile | None = None,
    audio: UploadFile | None = None,
    vitals_csv: UploadFile | None = None,
    # Text fields
    clinical_text: Annotated[str, Form(description="Texto clínico livre")] = "",
    # Medications (JSON string)
    medications: Annotated[str, Form(description="JSON da lista de medicamentos atuais")] = "",
) -> AnalysisResponse:
    """Executa pipeline multimodal completa e retorna relatório."""

    # ── Validar entrada ──
    try:
        patient_data = json.loads(patient) if patient else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JSON do paciente inválido.",
        )

    try:
        current_meds = json.loads(medications) if medications else None
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JSON de medicamentos inválido.",
        )

    # ── Ler arquivos em memória ──
    video_bytes: bytes | None = None
    audio_bytes: bytes | None = None
    csv_bytes: bytes | None = None

    if video:
        video_bytes = await _read_and_validate(
            video, settings.video_max_bytes, ["video/mp4", "video/webm", "video/quicktime"]
        )
    if audio:
        audio_bytes = await _read_and_validate(
            audio, settings.audio_max_bytes,
            ["audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/x-m4a",
             "audio/ogg", "audio/mp3"],
        )
    if vitals_csv:
        csv_bytes = await _read_and_validate(
            vitals_csv, settings.csv_max_bytes, ["text/csv", "application/csv"]
        )

    # ── Construir estado ──
    state: AnalysisState = {
        "patient": patient_data,
        "video_bytes": video_bytes,
        "audio_bytes": audio_bytes,
        "clinical_text": clinical_text.strip() if clinical_text else None,
        "current_medications": current_meds,
        "vitals_csv_bytes": csv_bytes,
    }

    # ── Executar grafo (síncrono — ainvoke aguarda término) ──
    try:
        result = await _graph.ainvoke(state)  # type: ignore[arg-type]
    except Exception as exc:
        logger.exception("Pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na pipeline de análise: {exc}",
        )

    # ── Montar resposta ──
    avail = result.get("available_modalities", [])
    all_mods = ["video", "audio", "text", "vitals", "medications"]
    missing = [m for m in all_mods if m not in avail]

    return AnalysisResponse(
        risk_level=result.get("risk_level", "NORMAL"),
        score=result.get("deterministic_score", 0),
        available_modalities=avail,
        missing_modalities=missing,
        video=_to_analyzer_output(result.get("video_result")),
        audio=_to_analyzer_output(result.get("audio_result")),
        text=_to_analyzer_output(result.get("text_result")),
        vitals=_to_analyzer_output(result.get("vitals_result")),
        medications=_to_analyzer_output(result.get("medication_result")),
        correlations=result.get("correlations", []),
        limitations=result.get("limitations", []),
        ai_report=_to_ai_report(result.get("final_report")),
    )


async def _read_and_validate(
    upload: UploadFile, max_bytes: int, allowed_types: list[str],
) -> bytes:
    data = await upload.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o tamanho máximo de {max_bytes // (1024*1024)} MB.",
        )
    content_type = upload.content_type or ""
    if content_type:
        normalized_ct = content_type.split(";")[0].strip().lower()
        if normalized_ct not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Tipo de arquivo não permitido: {content_type}",
            )
    if len(data) == 0:
        return None
    return data


def _to_analyzer_output(data: dict | None) -> AnalyzerOutput | None:
    if data is None:
        return None
    return AnalyzerOutput(
        status=data.get("status", "ok"),
        severity=data.get("severity", "NORMAL"),
        score=data.get("score", 0),
        findings=data.get("findings", []),
        evidence=data.get("evidence", []) if isinstance(data.get("evidence"), list) else [data.get("evidence", {})],
        limitations=data.get("limitations", []),
    )


def _to_ai_report(data: dict | None) -> AiReport | None:
    if data is None:
        return None
    return AiReport(
        summary=data.get("summary", ""),
        correlations=data.get("correlations", []),
        review_points=data.get("review_points", []),
        limitations=data.get("limitations", []),
        possible_causes=data.get("possible_causes", []),
        possible_treatments=data.get("possible_treatments", []),
    )
