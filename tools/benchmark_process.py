#!/usr/bin/env python3
"""Бенчмарк скорости обработки /api/v1/process."""

import io
import os
import struct
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


def make_wav(seconds: float = 5.0, sample_rate: int = 16000) -> bytes:
    """Создаёт WAV с тишиной заданной длительности."""
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


def get_base_url() -> str:
    host = os.getenv("API_HOST", "127.0.0.1")
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"


def run_benchmark(seconds: float = 5.0, runs: int = 3) -> None:
    """Запускает бенчмарк: отправляет WAV на /process, измеряет время."""
    base = get_base_url()
    wav = make_wav(seconds)
    print(f"Бенчмарк /api/v1/process")
    print(f"  Аудио: {seconds} сек (~{len(wav) / 1024:.1f} KB)")
    print(f"  Запусков: {runs}")
    print(f"  Backend: {base}")
    print()

    times: list[float] = []
    timings: list[dict] = []

    for i in range(runs):
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{base}/api/v1/process",
                    files={"audio": ("audio.wav", wav, "audio/wav")},
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            print(f"  Запуск {i + 1}: ОШИБКА — {e}")
            continue
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        timing = data.get("timing", {})
        timings.append(timing)
        total_ms = timing.get("total_ms", int(elapsed * 1000))
        transcribe_ms = timing.get("transcribe_ms", 0)
        llm_ms = timing.get("llm_ms", 0)
        print(f"  Запуск {i + 1}: {elapsed:.2f} сек (transcribe: {transcribe_ms} мс, llm: {llm_ms} мс)")

    if not times:
        print("Нет успешных запусков.")
        sys.exit(1)

    avg = sum(times) / len(times)
    print()
    print(f"Среднее: {avg:.2f} сек ({int(avg * 1000)} мс)")
    if timings:
        avg_transcribe = sum(t.get("transcribe_ms", 0) for t in timings) / len(timings)
        avg_llm = sum(t.get("llm_ms", 0) for t in timings) / len(timings)
        print(f"  transcribe: ~{int(avg_transcribe)} мс")
        print(f"  llm: ~{int(avg_llm)} мс")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Бенчмарк скорости /api/v1/process")
    parser.add_argument(
        "-s", "--seconds",
        type=float,
        default=5.0,
        help="Длительность тестового аудио в секундах (default: 5)",
    )
    parser.add_argument(
        "-n", "--runs",
        type=int,
        default=3,
        help="Количество запусков (default: 3)",
    )
    args = parser.parse_args()

    run_benchmark(seconds=args.seconds, runs=args.runs)


if __name__ == "__main__":
    main()
