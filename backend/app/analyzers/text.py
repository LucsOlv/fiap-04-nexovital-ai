"""Analisador de texto clínico — Azure AI Language + termos críticos (spec §9.3)."""

from __future__ import annotations

import logging
from typing import Any

from app.analyzers.critical_terms import CRITICAL_TERMS_LOWER
from app.state import AnalyzerResult

logger = logging.getLogger("nexovital.analyzers.text")


def analyze_text(
    text: str | None,
    azure_language_key: str = "",
    azure_language_endpoint: str = "",
) -> AnalyzerResult:
    if not text or not text.strip():
        return AnalyzerResult(
            status="missing",
            severity="NORMAL",
            score=0,
            findings=[],
            evidence=[],
            limitations=["Texto clínico não informado."],
        )

    text_lower = text.lower()
    findings: list[dict[str, Any]] = []
    limitations: list[str] = []
    score = 0

    # 1. Termos críticos (regras locais, sempre disponíveis)
    found_terms: list[dict[str, Any]] = []
    for term, severity in CRITICAL_TERMS_LOWER.items():
        if term in text_lower:
            found_terms.append({"term": term, "severity": severity})
            if severity == "ALERTA":
                score += 20
            else:
                score += 10

    for ft in found_terms:
        findings.append(
            {
                "type": "critical_term",
                "term": ft["term"],
                "severity": ft["severity"],
                "detail": f"Termo crítico detectado: '{ft['term']}'.",
            }
        )

    # 2. Azure AI Language (se configurado)
    sentiment = "neutral"
    key_phrases: list[str] = []

    if azure_language_key and azure_language_endpoint:
        try:
            azure_result = _call_azure_language(text, azure_language_key, azure_language_endpoint)
            sentiment = azure_result.get("sentiment", "neutral")
            key_phrases = azure_result.get("key_phrases", [])
            if sentiment == "negative":
                score += 15
                findings.append(
                    {
                        "type": "sentiment",
                        "value": sentiment,
                        "detail": "Sentimento negativo detectado no texto clínico.",
                    }
                )
            elif sentiment == "positive":
                findings.append(
                    {
                        "type": "sentiment",
                        "value": sentiment,
                        "detail": "Sentimento positivo detectado.",
                    }
                )
            for phrase in key_phrases:
                findings.append(
                    {
                        "type": "key_phrase",
                        "value": phrase,
                        "detail": f"Termo-chave: '{phrase}'.",
                    }
                )
        except Exception as exc:
            logger.warning("Azure Language failed: %s", exc)
            limitations.append(f"Azure AI Language indisponível: {exc}")
    else:
        limitations.append(
            "Azure AI Language não configurado — apenas termos críticos locais analisados."
        )

    severity = "NORMAL"
    if score >= 40:
        severity = "ALERTA"
    elif score >= 20:
        severity = "ATENÇÃO"

    return AnalyzerResult(
        status="ok" if not limitations or "não configurado" not in str(limitations) else "ok",
        severity=severity,
        score=min(100, score),
        findings=findings,
        evidence=[
            {
                "text_length": len(text),
                "sentiment": sentiment,
                "key_phrases": key_phrases,
                "critical_terms_found": len(found_terms),
            }
        ],
        limitations=limitations,
    )


def _call_azure_language(text: str, key: str, endpoint: str) -> dict[str, Any]:
    """Chama Azure AI Language para sentimento e frases-chave."""
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential

    if not endpoint.endswith("/"):
        endpoint += "/"

    client = TextAnalyticsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    result: dict[str, Any] = {"sentiment": "neutral", "key_phrases": []}

    # Sentimento
    sentiment_response = client.analyze_sentiment(documents=[text])[0]
    if not sentiment_response.is_error:
        result["sentiment"] = sentiment_response.sentiment

    # Frases-chave
    phrases_response = client.extract_key_phrases(documents=[text])[0]
    if not phrases_response.is_error:
        result["key_phrases"] = phrases_response.key_phrases

    return result
