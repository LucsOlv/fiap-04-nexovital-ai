"""Configuração da API carregada de variáveis de ambiente (MVP)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    app_env: str = "local"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    # Azure Speech to Text (F0)
    azure_speech_key: str = ""
    azure_speech_region: str = ""

    # Azure AI Language (F0)
    azure_language_key: str = ""
    azure_language_endpoint: str = ""

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-flash-1.5"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout: float = 60.0
    openrouter_max_retries: int = 3

    # Alert webhook
    webhook_alert_url: str = ""

    @property
    def webhook_configured(self) -> bool:
        return bool(self.webhook_alert_url)

    # Media limits
    video_max_bytes: int = 25 * 1024 * 1024
    video_max_duration_seconds: float = 30.0
    audio_max_bytes: int = 10 * 1024 * 1024
    audio_max_duration_seconds: float = 120.0
    csv_max_bytes: int = 1 * 1024 * 1024
    csv_max_rows: int = 500

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def speech_configured(self) -> bool:
        return bool(self.azure_speech_key and self.azure_speech_region)

    @property
    def language_configured(self) -> bool:
        return bool(self.azure_language_key and self.azure_language_endpoint)

    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key)


settings = Settings()
