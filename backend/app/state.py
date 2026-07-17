"""Estado do grafo LangGraph para análise multimodal."""

from __future__ import annotations

from typing import Any, TypedDict


class AnalyzerResult(TypedDict, total=False):
    status: str  # "ok" | "failed" | "missing"
    severity: str  # "NORMAL" | "ATENÇÃO" | "ALERTA"
    score: int  # 0-100
    findings: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    limitations: list[str]


class AnalysisState(TypedDict, total=False):
    # Entrada
    patient: dict[str, Any]
    video_bytes: bytes | None
    audio_bytes: bytes | None
    clinical_text: str | None
    current_medications: list[dict[str, Any]] | None
    vitals_csv_bytes: bytes | None

    # Modalidades disponíveis (calculado)
    available_modalities: list[str]

    # Resultados por analisador
    video_result: AnalyzerResult | None
    audio_result: AnalyzerResult | None
    text_result: AnalyzerResult | None
    vitals_result: AnalyzerResult | None
    medication_result: AnalyzerResult | None

    # Fusão
    deterministic_score: int
    risk_level: str  # "NORMAL" | "ATENÇÃO" | "ALERTA"
    correlations: list[dict[str, Any]]
    limitations: list[str]

    # Relatório final (OpenRouter)
    final_report: dict[str, Any] | None
    openrouter_error: str | None
