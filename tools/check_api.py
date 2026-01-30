#!/usr/bin/env python3
"""Проверка доступа к OpenAI API (Whisper и GPT)."""

import asyncio
import io
import struct
import sys
from pathlib import Path

# Добавляем src в path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openai import AsyncOpenAI

from copilot.config import get_settings


def make_silence_wav(seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Создаёт минимальный WAV с тишиной (Whisper примет, вернёт пустую строку)."""
    n_samples = int(sample_rate * seconds)
    n_bytes = n_samples * 2  # 16-bit
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


async def check_gpt(client: AsyncOpenAI, model: str) -> bool:
    """Проверяет доступ к GPT API."""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Скажи только: OK"}],
            max_tokens=10,
        )
        text = (response.choices[0].message.content or "").strip()
        print(f"  GPT ({model}): OK — ответ: {text[:50]!r}")
        return True
    except Exception as e:
        err = str(e)
        if "429" in err or "insufficient_quota" in err:
            print(f"  GPT ({model}): FAIL — превышен лимит (quota). Добавьте billing на platform.openai.com")
        else:
            print(f"  GPT ({model}): FAIL — {e}")
        return False


async def check_whisper(client: AsyncOpenAI, model: str) -> bool:
    """Проверяет доступ к Whisper API."""
    try:
        wav = make_silence_wav(1.0)
        audio = io.BytesIO(wav)
        audio.name = "test.wav"
        response = await client.audio.transcriptions.create(
            model=model,
            file=audio,
        )
        text = (response.text or "").strip()
        display = repr(text) if text else "(пусто, ожидаемо для тишины)"
        print(f"  Whisper ({model}): OK — транскрипт: {display}")
        return True
    except Exception as e:
        err = str(e)
        if "429" in err or "insufficient_quota" in err:
            print(f"  Whisper ({model}): FAIL — превышен лимит (quota). Добавьте billing на platform.openai.com")
        else:
            print(f"  Whisper ({model}): FAIL — {e}")
        return False


async def main() -> None:
    print("Проверка доступа к OpenAI API...")
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    print(f"API key: {settings.openai_api_key[:10]}...{settings.openai_api_key[-4:]}")
    print()
    gpt_ok = await check_gpt(client, settings.openai_llm_model)
    whisper_ok = await check_whisper(client, settings.openai_whisper_model)
    print()
    if gpt_ok and whisper_ok:
        print("Все API доступны.")
        sys.exit(0)
    print("Есть недоступные API. Проверьте billing на https://platform.openai.com/account/billing")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
