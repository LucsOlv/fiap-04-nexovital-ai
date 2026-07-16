"""Grafo LangGraph — pipeline de análise multimodal (spec §8)."""

from __future__ import annotations

import logging

from langgraph.graph import StateGraph, END

from app.analyzers.audio import analyze_audio
from app.analyzers.fusion import fuse_evidence
from app.analyzers.medications import analyze_medications
from app.analyzers.text import analyze_text
from app.analyzers.video import analyze_video
from app.analyzers.vitals import analyze_vitals
from app.core.config import settings
from app.services.openrouter_client import generate_report
from app.state import AnalysisState

logger = logging.getLogger("nexovital.graph")


def _validate_input(state: AnalysisState) -> AnalysisState:
    modalities: list[str] = []
    if state.get("video_bytes"):
        modalities.append("video")
    if state.get("audio_bytes"):
        modalities.append("audio")
    if state.get("clinical_text"):
        modalities.append("text")
    if state.get("vitals_csv_bytes"):
        modalities.append("vitals")
    if state.get("current_medications"):
        modalities.append("medications")

    state["available_modalities"] = modalities
    return state


def _prepare_context(state: AnalysisState) -> AnalysisState:
    state["limitations"] = state.get("limitations", [])
    patient = state.get("patient", {})
    if not patient.get("has_history", True):
        state["limitations"].append("Paciente sem histórico clínico prévio — análise parcial.")
    return state


def _analyze_modalities(state: AnalysisState) -> AnalysisState:
    modalities = state.get("available_modalities", [])

    if "video" in modalities:
        state["video_result"] = analyze_video(state.get("video_bytes"))
    else:
        state["video_result"] = {"status": "missing", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": ["Vídeo não enviado."]}

    if "audio" in modalities:
        state["audio_result"] = analyze_audio(
            state.get("audio_bytes"),
            azure_speech_key=settings.azure_speech_key,
            azure_speech_region=settings.azure_speech_region,
            azure_language_key=settings.azure_language_key,
            azure_language_endpoint=settings.azure_language_endpoint,
        )
    else:
        state["audio_result"] = {"status": "missing", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": ["Áudio não enviado."]}

    if "text" in modalities:
        state["text_result"] = analyze_text(
            state.get("clinical_text"),
            azure_language_key=settings.azure_language_key,
            azure_language_endpoint=settings.azure_language_endpoint,
        )
    else:
        state["text_result"] = {"status": "missing", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": ["Texto clínico não enviado."]}

    if "vitals" in modalities:
        state["vitals_result"] = analyze_vitals(
            state.get("vitals_csv_bytes") or b"",
            max_rows=settings.csv_max_rows,
        )
    else:
        state["vitals_result"] = {"status": "missing", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": ["CSV de sinais vitais não enviado."]}

    if "medications" in modalities:
        patient = state.get("patient", {})
        previous = patient.get("previous_medications")
        state["medication_result"] = analyze_medications(
            state.get("current_medications"),
            previous,
        )
    else:
        state["medication_result"] = {"status": "missing", "severity": "NORMAL", "score": 0, "findings": [], "evidence": [], "limitations": ["Medicamentos não informados."]}

    return state


def _fuse_evidence(state: AnalysisState) -> AnalysisState:
    patient = state.get("patient", {})
    score, level, correlations, limits = fuse_evidence(
        video=state.get("video_result"),
        audio=state.get("audio_result"),
        text=state.get("text_result"),
        vitals=state.get("vitals_result"),
        medications=state.get("medication_result"),
        has_history=patient.get("has_history", True),
    )

    state["deterministic_score"] = score
    state["risk_level"] = level
    state["correlations"] = correlations
    state["limitations"] = state.get("limitations", []) + limits
    return state


def _generate_summary(state: AnalysisState) -> AnalysisState:
    report = generate_report(
        video_result=state.get("video_result"),
        audio_result=state.get("audio_result"),
        text_result=state.get("text_result"),
        vitals_result=state.get("vitals_result"),
        medication_result=state.get("medication_result"),
        risk_level=state.get("risk_level", "NORMAL"),
        deterministic_score=state.get("deterministic_score", 0),
        fusion_correlations=state.get("correlations", []),
        fusion_limitations=state.get("limitations", []),
        patient=state.get("patient"),
    )
    if report:
        state["final_report"] = report
    else:
        state["openrouter_error"] = "OpenRouter não configurado ou falhou."
        state["limitations"].append("Resumo IA não disponível — verifique OpenRouter.")
    return state


def _validate_and_return(state: AnalysisState) -> AnalysisState:
    missing_report = state.get("openrouter_error", "")
    if missing_report:
        state["final_report"] = {
            "summary": "Relatório IA não disponível para esta análise.",
            "correlations": state.get("correlations", []),
            "review_points": ["Revisão médica recomendada (relatório IA indisponível)."],
            "limitations": state.get("limitations", []),
        }
    return state


def build_graph() -> StateGraph:
    workflow = StateGraph(AnalysisState)

    workflow.add_node("validate_input", _validate_input)
    workflow.add_node("prepare_context", _prepare_context)
    workflow.add_node("analyze_modalities", _analyze_modalities)
    workflow.add_node("fuse_evidence", _fuse_evidence)
    workflow.add_node("generate_summary", _generate_summary)
    workflow.add_node("validate_and_return", _validate_and_return)

    workflow.set_entry_point("validate_input")
    workflow.add_edge("validate_input", "prepare_context")
    workflow.add_edge("prepare_context", "analyze_modalities")
    workflow.add_edge("analyze_modalities", "fuse_evidence")
    workflow.add_edge("fuse_evidence", "generate_summary")
    workflow.add_edge("generate_summary", "validate_and_return")
    workflow.add_edge("validate_and_return", END)

    return workflow.compile()
