"""Тесты audio_recorder."""

import io
from unittest.mock import MagicMock, patch

import pytest

from app.audio_recorder import (
    SAMPLE_RATE,
    AudioRecorder,
    bytes_to_wav,
    find_blackhole_device,
)


class TestBytesToWav:
    def test_valid_wav_structure(self) -> None:
        raw = b"\x00\x00" * (SAMPLE_RATE // 2)  # 0.5 sec
        wav = bytes_to_wav(raw)
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"
        assert wav[12:16] == b"fmt "
        assert wav[36:40] == b"data"
        assert len(wav) == 44 + len(raw)  # 44 = RIFF header + fmt + data header

    def test_empty_input(self) -> None:
        raw = b""
        wav = bytes_to_wav(raw)
        assert wav[:4] == b"RIFF"
        assert len(wav) == 44  # minimal WAV header

    def test_custom_sample_rate(self) -> None:
        raw = b"\x00\x00" * 8000
        wav = bytes_to_wav(raw, sample_rate=8000)
        assert wav[:4] == b"RIFF"


class TestFindBlackholeDevice:
    def test_blackhole_found(self) -> None:
        mock_p = MagicMock()
        mock_p.get_device_count.return_value = 3
        mock_p.get_device_info_by_index.side_effect = [
            {"name": "Built-in Microphone", "maxInputChannels": 1},
            {"name": "BlackHole 2ch", "maxInputChannels": 2},
            {"name": "Other", "maxInputChannels": 1},
        ]
        idx = find_blackhole_device(mock_p)
        assert idx == 1

    def test_blackhole_not_found(self) -> None:
        mock_p = MagicMock()
        mock_p.get_device_count.return_value = 2
        mock_p.get_device_info_by_index.side_effect = [
            {"name": "Built-in Microphone", "maxInputChannels": 1},
            {"name": "Other", "maxInputChannels": 1},
        ]
        idx = find_blackhole_device(mock_p)
        assert idx is None

    def test_blackhole_no_input_channels(self) -> None:
        mock_p = MagicMock()
        mock_p.get_device_count.return_value = 1
        mock_p.get_device_info_by_index.return_value = {
            "name": "BlackHole 2ch",
            "maxInputChannels": 0,
        }
        idx = find_blackhole_device(mock_p)
        assert idx is None


class TestAudioRecorder:
    def test_get_buffer_as_wav_empty_returns_none(self) -> None:
        recorder = AudioRecorder()
        recorder._buffer.clear()
        assert recorder.get_buffer_as_wav() is None
        recorder.close()

    def test_get_buffer_as_wav_short_buffer_returns_none(self) -> None:
        recorder = AudioRecorder()
        recorder._buffer.append(b"\x00\x00" * 100)  # < 1 sec
        assert recorder.get_buffer_as_wav() is None
        recorder.close()

    def test_get_buffer_as_wav_sufficient_data_returns_wav(self) -> None:
        recorder = AudioRecorder()
        chunk = b"\x00\x00" * 512
        for _ in range(32):  # ~1 sec at 16kHz
            recorder._buffer.append(chunk)
        wav = recorder.get_buffer_as_wav()
        assert wav is not None
        assert wav[:4] == b"RIFF"
        recorder.close()
