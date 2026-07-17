"""Cliente OpenRouter para geração de resumo clínico estruturado."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, cast

import httpx

from app.core.config import settings
from app.state import AnalyzerResult

logger = logging.getLogger("nexovital.services.openrouter")

SYSTEM_PROMPT = """Você é um assistente de análise clínica acadêmica para o sistema NexoVital AI.

Você recebe resultados estruturados de uma análise multimodal de um paciente:
- vídeo (sinais de dor/desconforto detectados por pose estimation)
- áudio (transcrição, métricas acústicas, termos críticos na fala)
- texto clínico (sintomas relatados, evolução)
- sinais vitais (CSV com anomalias detectadas)
- medicamentos (alterações em relação ao histórico)

REGRAS:
1. NÃO faça diagnóstico. Isto é um DEMONSTRATIVO ACADÊMICO.
2. Inclua SEMPRE o aviso: "Este relatório é demonstrativo e não constitui diagnóstico médico."
3. Se houver DOR relatada + MEDICAMENTO para dor (ex: Dipirona, Paracetamol, Ibuprofeno), comente sobre a duração do uso e sugira reavaliação médica — NÃO recomende medicamentos específicos, mas alerte que uso prolongado de analgésico sem investigação da causa pode mascarar agravamento.
4. Cruze SINTOMAS do texto/áudio com ALTERAÇÕES DE MEDICAMENTOS: se paciente relata sintoma X e houve mudança de medicamento, comente se a mudança parece relacionada ao quadro.
5. Se SINAIS VITAIS mostram anomalia + VÍDEO mostra sinais de dor, correlacione (ex: taquicardia + postura antálgica = possível dor aguda).
6. Se paciente SEM HISTÓRICO, alerte que a ausência de baseline reduz a confiança da comparação.
7. Se MODALIDADE AUSENTE, mencione que a análise fica incompleta sem ela.
8. Liste de 2 a 5 PONTOS QUE EXIGEM REVISÃO MÉDICA baseados nos achados combinados.
9. Liste as LIMITAÇÕES reais da análise (dados faltantes, baixa confiança, ausência de baseline).
10. Gere CORRELAÇÕES entre modalidades quando houver convergência (ex: áudio com termos de dor + vídeo com postura antálgica + sinais vitais alterados).
11. Liste 5 POSSÍVEIS CAUSAS baseadas na combinação dos achados. Seja específico: cite condições clínicas plausíveis (não genéricas como "dor"). Ex: "Exacerbação de DPOC", "Crise de ansiedade", "Cefaleia tensional", "Dor musculoesquelética por má postura". Inclua nível de urgência para cada uma.
12. Liste 5 POSSÍVEIS TRATAMENTOS/ENCAMINHAMENTOS baseados nas causas. Seja específico: cite classes terapêuticas, exames complementares ou encaminhamentos. Ex: "RX de tórax para descartar pneumonia", "Avaliação com neurologista", "Fisioterapia respiratória", "Reavaliação da prescrição de anti-hipertensivo". Não recomende doses.

Responda APENAS com JSON:
{
  "summary": "resumo clínico contextualizado (2-4 parágrafos, em português)",
  "correlations": [
    {"description": "...", "modalities": ["video", "vitals"]}
  ],
  "review_points": ["ponto 1", "ponto 2"],
  "limitations": ["limitação 1", "limitação 2"],
  "possible_causes": [
    {"condition": "Nome da condição", "rationale": "Por que esta condição se encaixa nos achados", "urgency": "baixa|média|alta"},
    ...
  ],
  "possible_treatments": [
    {"intervention": "Tratamento ou encaminhamento", "rationale": "Por que isso é indicado", "type": "exame|medicamentoso|encaminhamento|terapia|monitoramento"},
    ...
  ]
}"""


def generate_report(
    video_result: AnalyzerResult | None,
    audio_result: AnalyzerResult | None,
    text_result: AnalyzerResult | None,
    vitals_result: AnalyzerResult | None,
    medication_result: AnalyzerResult | None,
    risk_level: str,
    deterministic_score: int,
    fusion_correlations: list[dict[str, Any]],
    fusion_limitations: list[str],
    patient: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Gera relatório estruturado via OpenRouter."""
    if not settings.openrouter_configured:
        logger.warning("OpenRouter não configurado — relatório IA indisponível.")
        return None

    context = _build_context(
        video_result,
        audio_result,
        text_result,
        vitals_result,
        medication_result,
        risk_level,
        deterministic_score,
        fusion_correlations,
        fusion_limitations,
        patient,
    )

    for attempt in range(settings.openrouter_max_retries):
        try:
            response = _call_openrouter(SYSTEM_PROMPT, context)
            # Strip markdown code fences if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            parsed = cast(dict[str, Any], json.loads(cleaned))
            _validate_report_schema(parsed)
            return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("OpenRouter attempt %d failed: %s", attempt + 1, exc)
            if attempt < settings.openrouter_max_retries - 1:
                time.sleep(2**attempt)
        except Exception as exc:
            logger.error("OpenRouter unexpected error: %s", exc)
            return None

    logger.error("OpenRouter exhausted retries — sem relatório IA.")
    return None


def _build_context(
    video: AnalyzerResult | None,
    audio: AnalyzerResult | None,
    text: AnalyzerResult | None,
    vitals: AnalyzerResult | None,
    meds: AnalyzerResult | None,
    risk_level: str,
    score: int,
    correlations: list[dict[str, Any]],
    limitations: list[str],
    patient: dict[str, Any] | None = None,
) -> str:
    parts: list[str] = [
        f"NÍVEL DE RISCO (determinístico): {risk_level}",
        f"SCORE: {score}/100",
    ]

    # Dados do paciente
    if patient:
        parts.append(
            f"\nPACIENTE: {patient.get('name', '?')}, "
            f"{patient.get('age', '?')} anos, sexo {patient.get('sex', '?')}"
        )
        summary = patient.get("summary", "")
        if summary:
            parts.append(f"RESUMO CLÍNICO DO PACIENTE: {summary}")
        notes = patient.get("notes", "")
        if notes:
            parts.append(f"OBSERVAÇÕES: {notes}")
        prev_meds = patient.get("previous_medications", [])
        if prev_meds:
            meds_str = ", ".join(
                f"{m.get('name', '')} {m.get('dose', '')} {m.get('frequency', '')}"
                for m in prev_meds
            )
            parts.append(f"MEDICAMENTOS ANTERIORES: {meds_str}")

    if correlations:
        parts.append(
            "CORRELAÇÕES DETECTADAS: " + "; ".join(c.get("description", "") for c in correlations)
        )
    if limitations:
        parts.append("LIMITAÇÕES DO SISTEMA: " + "; ".join(limitations))

    for name, result in [
        ("VÍDEO (sinais de dor/desconforto)", video),
        ("ÁUDIO (transcrição e métricas)", audio),
        ("TEXTO CLÍNICO", text),
        ("SINAIS VITAIS", vitals),
        ("MEDICAMENTOS (alterações)", meds),
    ]:
        if result is None:
            parts.append(f"{name}: não disponível")
            continue
        parts.append(f"\n{name}:")
        parts.append(
            f"  Severidade: {result.get('severity', '?')}, Score: {result.get('score', '?')}"
        )
        for finding in result.get("findings", []):
            parts.append(f"  - {finding.get('detail', finding.get('description', str(finding)))}")
        for ev in result.get("evidence", []):
            if isinstance(ev, dict):
                for k, v in ev.items():
                    if k not in ("current_medications", "previous_medications"):
                        parts.append(f"  [{k}]: {v}")

    return "\n".join(parts)


def _call_openrouter(system: str, user: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    response = httpx.post(
        f"{settings.openrouter_base_url}/chat/completions",
        json=body,
        headers=headers,
        timeout=settings.openrouter_timeout,
    )
    response.raise_for_status()
    data = response.json()
    return cast(str, data["choices"][0]["message"]["content"])


def _validate_report_schema(report: dict[str, Any]) -> None:
    required = {
        "summary",
        "correlations",
        "review_points",
        "limitations",
        "possible_causes",
        "possible_treatments",
    }
    missing = required - set(report.keys())
    if missing:
        raise ValueError(f"Schema inválido — campos ausentes: {missing}")
    if not isinstance(report["summary"], str) or len(report["summary"]) < 20:
        raise ValueError("Resumo muito curto ou inválido.")
    if not isinstance(report["possible_causes"], list) or len(report["possible_causes"]) < 3:
        raise ValueError("possible_causes deve ter ao menos 3 causas.")
    if (
        not isinstance(report["possible_treatments"], list)
        or len(report["possible_treatments"]) < 3
    ):
        raise ValueError("possible_treatments deve ter ao menos 3 tratamentos.")
