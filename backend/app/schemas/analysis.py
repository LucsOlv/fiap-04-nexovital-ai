"""Schemas da análise e relatório (MVP)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzerOutput(BaseModel):
    status: str = "ok"  # "ok" | "failed" | "missing"
    severity: str = "NORMAL"  # "NORMAL" | "ATENÇÃO" | "ALERTA"
    score: int = 0
    findings: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AiReport(BaseModel):
    summary: str
    correlations: list[dict[str, Any]] = Field(default_factory=list)
    review_points: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    possible_causes: list[dict[str, Any]] = Field(default_factory=list)
    possible_treatments: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    risk_level: str  # "NORMAL" | "ATENÇÃO" | "ALERTA"
    score: int  # 0-100
    available_modalities: list[str]
    missing_modalities: list[str]

    video: AnalyzerOutput | None = None
    audio: AnalyzerOutput | None = None
    text: AnalyzerOutput | None = None
    vitals: AnalyzerOutput | None = None
    medications: AnalyzerOutput | None = None

    correlations: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    ai_report: AiReport | None = None

    disclaimer: str = (
        "ATENÇÃO: Este é um resultado DEMONSTRATIVO gerado por um sistema "
        "acadêmico de apoio à análise multimodal. NÃO constitui diagnóstico "
        "médico. Os achados devem ser interpretados por um profissional de "
        "saúde qualificado."
    )
