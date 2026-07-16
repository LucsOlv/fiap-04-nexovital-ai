"""App factory do NexoVital AI MVP — sem auth, sem DB, sem worker."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analyze import router as analyze_router
from app.api.demo_patients import router as patients_router
from app.api.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="NexoVital AI API",
        version="0.2.0",
        description="MVP acadêmico — análise multimodal síncrona.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "detail": "Erro interno inesperado."},
        )

    app.include_router(health_router)
    app.include_router(patients_router)
    app.include_router(analyze_router)
    return app


app = create_app()
