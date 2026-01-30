"""Клиент для Copilot API."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def get_base_url() -> str:
    host = os.getenv("API_HOST", "127.0.0.1")
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"


async def process_audio(audio_wav: bytes) -> dict:
    """Отправляет аудио на /api/v1/process и возвращает результат."""
    base = get_base_url()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base}/api/v1/process",
            files={"audio": ("audio.wav", audio_wav, "audio/wav")},
        )
        response.raise_for_status()
        return response.json()


def process_audio_sync(audio_wav: bytes) -> dict:
    """Синхронная обёртка для process_audio."""
    import asyncio
    return asyncio.run(process_audio(audio_wav))
