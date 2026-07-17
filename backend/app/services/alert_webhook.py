"""Serviço de notificação externa via webhook."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("nexovital.services.webhook")

ALERT_WEBHOOK_TIMEOUT = 10.0


async def send_alert_webhook(
    patient_name: str,
    patient_id: str,
    risk_level: str,
    score: int,
    modalities: list[str],
    limitations: list[str],
    summary: str,
) -> bool:
    """Envia notificação de alerta para webhook configurado."""
    if not settings.webhook_configured:
        logger.debug("Webhook não configurado — notificação ignorada.")
        return False

    payload: dict[str, Any] = {
        "event": "alert",
        "system": "NexoVital AI",
        "patient_name": patient_name,
        "patient_id": patient_id,
        "risk_level": risk_level,
        "score": score,
        "available_modalities": modalities,
        "limitations": limitations,
        "summary": summary,
        "disclaimer": (
            "Resultado demonstrativo. "
            "Não constitui diagnóstico médico. "
            "Requer revisão de profissional de saúde."
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=ALERT_WEBHOOK_TIMEOUT) as client:
            resp = await client.post(
                settings.webhook_alert_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.is_success:
                logger.info(
                    "Webhook de alerta enviado: %s → %d",
                    patient_id,
                    resp.status_code,
                )
                return True
            logger.warning(
                "Webhook de alerta falhou: %s → %d %s",
                patient_id,
                resp.status_code,
                resp.text[:200],
            )
            return False
    except Exception:
        logger.exception("Erro ao enviar webhook de alerta para %s", patient_id)
        return False
