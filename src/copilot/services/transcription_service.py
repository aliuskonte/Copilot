"""Сервис транскрибации через OpenAI Whisper API."""

import io
from typing import BinaryIO

from openai import AsyncOpenAI

from copilot.config import get_settings


class TranscriptionService:
    """Транскрибация аудио через Whisper."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_whisper_model

    async def transcribe(self, audio: bytes | BinaryIO) -> str:
        """Транскрибирует аудио и возвращает текст."""
        if isinstance(audio, bytes):
            audio = io.BytesIO(audio)
        audio.name = "audio.wav"
        response = await self._client.audio.transcriptions.create(
            model=self._model,
            file=audio,
        )
        return response.text.strip()


transcription_service = TranscriptionService()
