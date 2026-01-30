"""Сервисы для транскрибации и LLM."""

from copilot.services.llm_service import llm_service
from copilot.services.transcription_service import transcription_service

__all__ = [
    "llm_service",
    "transcription_service",
]
