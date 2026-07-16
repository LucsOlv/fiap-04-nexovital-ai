"""Dependências mínimas para o MVP — sem DB, fila ou worker."""

from __future__ import annotations

import logging

from app.core.config import settings


def get_logger(name: str = "nexovital") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level.upper())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
    return logger
