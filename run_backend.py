#!/usr/bin/env python3
"""Запуск FastAPI backend."""

import sys
from pathlib import Path

# Добавляем src в path для импорта copilot
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn

from copilot.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "copilot.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
