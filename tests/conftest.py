"""Фикстуры и моки для тестов."""

import io
import os
import sys
from pathlib import Path

import pytest

# Устанавливаем env до импорта copilot (get_settings кэшируется)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-for-pytest")

# Добавляем src в path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def make_test_wav(seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Создаёт минимальный WAV с тишиной для тестов."""
    import struct

    n_samples = int(sample_rate * seconds)
    n_bytes = n_samples * 2
    wav = io.BytesIO()
    wav.write(b"RIFF")
    wav.write(struct.pack("<I", 36 + n_bytes))
    wav.write(b"WAVE")
    wav.write(b"fmt ")
    wav.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    wav.write(b"data")
    wav.write(struct.pack("<I", n_bytes))
    wav.write(b"\x00" * n_bytes)
    return wav.getvalue()


@pytest.fixture
def test_wav() -> bytes:
    """Минимальный WAV-файл (1 сек тишины)."""
    return make_test_wav(1.0)


@pytest.fixture
def large_wav() -> bytes:
    """WAV > 25 MB для теста лимита (25 MB = 25*1024*1024 bytes)."""
    return make_test_wav(seconds=821)  # 16kHz*2*821 > 25 MB


@pytest.fixture
def client():
    """FastAPI TestClient с очищенным кэшем настроек."""
    from copilot.config import get_settings

    get_settings.cache_clear()
    try:
        from fastapi.testclient import TestClient

        from copilot.main import app

        with TestClient(app) as c:
            yield c
    finally:
        get_settings.cache_clear()
