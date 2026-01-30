"""Схемы для эндпоинтов транскрибации и ответов."""

from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    """Ответ транскрибации."""

    text: str = Field(..., description="Транскрибированный текст")


class AnswerRequest(BaseModel):
    """Запрос на ответ LLM."""

    question: str = Field(..., min_length=1, description="Вопрос собеседника")


class AnswerResponse(BaseModel):
    """Ответ LLM на вопрос."""

    question: str = Field(..., description="Вопрос собеседника")
    answer: str = Field(..., description="Ответ LLM")


class ProcessTiming(BaseModel):
    """Метрики времени обработки в миллисекундах."""

    transcribe_ms: int = Field(..., description="Время транскрибации")
    llm_ms: int = Field(..., description="Время вызова LLM")
    total_ms: int = Field(..., description="Общее время")


class ProcessResponse(BaseModel):
    """Результат полной обработки: транскрибация + ответ."""

    transcript: str = Field(..., description="Транскрибированный текст")
    question: str | None = Field(None, description="Выделенный вопрос или None")
    answer: str | None = Field(None, description="Ответ LLM или None, если не вопрос")
    timing: ProcessTiming | None = Field(None, description="Метрики времени")
