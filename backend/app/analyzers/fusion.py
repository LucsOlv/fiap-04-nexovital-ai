"""Fusão determinística multimodal.

Regras (spec §10):
- Modalidade ausente não recebe score zero — é ignorada.
- Anomalia forte em sinais vitais pode elevar o alerta.
- Evidências concordantes entre 2+ modalidades aumentam o score.
- Ausência de histórico reduz confiança, mas não cria anomalia.
- O cálculo informa quais regras contribuíram.
- OpenRouter não decide o nível de risco — só a fusão.
"""

from __future__ import annotations

from typing import Any

from app.state import AnalyzerResult

# Pesos das modalidades na fusão
WEIGHTS: dict[str, float] = {
    "vitals": 0.30,
    "video": 0.25,
    "audio": 0.20,
    "text": 0.15,
    "medications": 0.10,
}


def fuse_evidence(
    video: AnalyzerResult | None,
    audio: AnalyzerResult | None,
    text: AnalyzerResult | None,
    vitals: AnalyzerResult | None,
    medications: AnalyzerResult | None,
    has_history: bool = True,
) -> tuple[int, str, list[dict[str, Any]], list[str]]:
    """Calcula score determinístico, nível de risco, correlações e limitações."""

    results: dict[str, AnalyzerResult | None] = {
        "vitals": vitals,
        "video": video,
        "audio": audio,
        "text": text,
        "medications": medications,
    }

    rules_applied: list[str] = []
    weighted_sum: float = 0.0
    total_weight: float = 0.0
    present_count = 0
    abnormal_count = 0
    alert_count = 0
    correlations: list[dict[str, Any]] = []
    limitations: list[str] = []

    for modality, result in results.items():
        if result is None or result.get("status") == "missing":
            limitations.append(f"Modalidade '{modality}' ausente.")
            continue

        if result.get("status") == "failed":
            limitations.append(
                f"Modalidade '{modality}' falhou: "
                f"{result.get('limitations', ['erro desconhecido'])[0]}"
            )
            continue

        present_count += 1
        weight = WEIGHTS.get(modality, 0.20)
        total_weight += weight
        score = result.get("score", 0)
        weighted_sum += score * weight

        if result.get("severity") in {"ATENÇÃO", "ALERTA"}:
            abnormal_count += 1
        if result.get("severity") == "ALERTA":
            alert_count += 1
            rules_applied.append(f"Alerta em {modality} (score={score})")

    # Pontuação base: média ponderada dos scores, que já usam escala 0-100.
    if total_weight > 0:
        base_score = int(weighted_sum / total_weight)
    else:
        base_score = 0
        limitations.append("Nenhuma modalidade válida disponível para fusão.")

    # Regra: anomalia forte em sinais vitais eleva alerta
    if vitals and vitals.get("status") == "ok" and vitals.get("severity") == "ALERTA":
        base_score = min(100, base_score + 15)
        rules_applied.append("Anomalia forte em sinais vitais → +15 pontos")

    # Regra: evidências concordantes entre 2+ modalidades
    if alert_count >= 2:
        base_score = min(100, base_score + 10)
        rules_applied.append(
            f"Evidências concordantes ({alert_count} modalidades em ALERTA) → +10 pontos"
        )
        correlations.append(
            {
                "modalities": [
                    m for m, r in results.items() if r and r.get("severity") == "ALERTA"
                ],
                "type": "convergent",
                "description": f"{alert_count} modalidades indicam anormalidade.",
                "strength": min(1.0, alert_count * 0.35),
            }
        )

    # Regra: ausência de histórico reduz confiança
    if not has_history:
        base_score = max(0, base_score - 10)
        limitations.append("Paciente sem histórico prévio — confiança reduzida.")
        rules_applied.append("Sem baseline histórica → -10 pontos, confiança reduzida")

    # Regra: nenhuma severidade anormal → limita ruído residual.
    if abnormal_count == 0 and present_count > 0:
        base_score = min(base_score, 20)
        rules_applied.append("Nenhuma anomalia detectada → score máximo 20")

    # Mapeamento score → nível
    if base_score >= 70:
        risk_level = "ALERTA"
    elif base_score >= 30:
        risk_level = "ATENÇÃO"
    else:
        risk_level = "NORMAL"

    # Correlação de divergência (se misturar NORMAL com ALERTA)
    severities = [r.get("severity") for r in results.values() if r and r.get("status") == "ok"]
    if "ALERTA" in severities and "NORMAL" in severities:
        correlations.append(
            {
                "modalities": [m for m, r in results.items() if r and r.get("status") == "ok"],
                "type": "divergent",
                "description": "Modalidades com severidades divergentes — requer revisão.",
                "strength": 0.5,
            }
        )

    # Garantir score final em 0-100
    final_score = max(0, min(100, base_score))

    return final_score, risk_level, correlations, limitations
