"""Health check da API (spec §11)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "integrations": {
            "azure_speech": settings.speech_configured,
            "azure_language": settings.language_configured,
            "openrouter": settings.openrouter_configured,
        },
    }
