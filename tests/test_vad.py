"""Тесты VAD."""

import pytest

from app.audio_recorder import SAMPLE_RATE, bytes_to_wav
from app.vad import get_last_speech_segment, segment_audio


def make_silence(seconds: float = 1.0, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Создаёт тишину (нули)."""
    n = int(sample_rate * seconds * 2)
    return b"\x00" * n


def make_noise(seconds: float = 1.0, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Создаёт «шум» (ненулевые значения — VAD может считать речью)."""
    n = int(sample_rate * seconds * 2)
    return bytes([(i % 256) for i in range(n)])


class TestSegmentAudio:
    def test_empty_returns_empty(self) -> None:
        result = segment_audio(b"")
        assert result == []

    def test_short_returns_empty(self) -> None:
        result = segment_audio(make_silence(0.5))
        assert result == []

    def test_silence_returns_empty(self) -> None:
        result = segment_audio(make_silence(2.0))
        assert result == []

    def test_noise_may_return_segments(self) -> None:
        audio = make_noise(2.0)
        result = segment_audio(audio)
        assert isinstance(result, list)


class TestGetLastSpeechSegment:
    def test_empty_returns_none(self) -> None:
        result = get_last_speech_segment(b"")
        assert result is None

    def test_silence_returns_none(self) -> None:
        result = get_last_speech_segment(make_silence(2.0))
        assert result is None

    def test_short_returns_none(self) -> None:
        result = get_last_speech_segment(make_silence(0.5), min_speech_sec=1.0)
        assert result is None
