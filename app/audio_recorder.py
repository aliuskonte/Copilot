"""Запись аудио с BlackHole (системный звук)."""

import io
import struct
import threading
from collections import deque
from typing import Callable

import pyaudio

SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024
BUFFER_SECONDS = 15


def find_blackhole_device(p: pyaudio.PyAudio) -> int | None:
    """Находит индекс устройства BlackHole в списке входов."""
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        name = info.get("name", "").lower()
        max_input = info.get("maxInputChannels", 0)
        if "blackhole" in name and max_input > 0:
            return i
    return None


def bytes_to_wav(audio_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Конвертирует сырые PCM-байты в WAV."""
    n_frames = len(audio_bytes) // 2
    wav = io.BytesIO()
    wav.write(b"RIFF")
    wav.write(struct.pack("<I", 36 + n_frames * 2))
    wav.write(b"WAVE")
    wav.write(b"fmt ")
    wav.write(struct.pack("<IHHIIHH", 16, 1, CHANNELS, sample_rate, sample_rate * 2, 2, 16))
    wav.write(b"data")
    wav.write(struct.pack("<I", n_frames * 2))
    wav.write(audio_bytes)
    return wav.getvalue()


class AudioRecorder:
    """Записывает аудио с BlackHole в кольцевой буфер."""

    def __init__(self, on_error: Callable[[str], None] | None = None) -> None:
        self._p = pyaudio.PyAudio()
        self._stream: pyaudio.Stream | None = None
        self._device_index: int | None = None
        self._buffer: deque[bytes] = deque(maxlen=BUFFER_SECONDS * SAMPLE_RATE * 2 // CHUNK)
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._on_error = on_error

    def _record_loop(self) -> None:
        while self._running and self._stream:
            try:
                data = self._stream.read(CHUNK, exception_on_overflow=False)
                with self._lock:
                    self._buffer.append(data)
            except Exception as e:
                if self._on_error:
                    self._on_error(str(e))
                break

    def start(self) -> bool:
        """Запускает запись. Возвращает True при успехе."""
        if self._running:
            return True
        self._device_index = find_blackhole_device(self._p)
        if self._device_index is None:
            if self._on_error:
                self._on_error("BlackHole не найден. Установите: brew install blackhole-2ch")
            return False
        try:
            self._stream = self._p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self._device_index,
                frames_per_buffer=CHUNK,
            )
        except Exception as e:
            if self._on_error:
                self._on_error(f"Не удалось открыть BlackHole: {e}")
            return False
        self._running = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Останавливает запись."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def get_buffer_raw(self) -> bytes | None:
        """Возвращает сырые PCM-байты буфера или None, если пуст."""
        with self._lock:
            if not self._buffer:
                return None
            return b"".join(self._buffer)

    def get_buffer_as_wav(self) -> bytes | None:
        """Возвращает содержимое буфера как WAV или None, если буфер пуст."""
        raw = self.get_buffer_raw()
        if not raw or len(raw) < SAMPLE_RATE:  # минимум ~1 сек
            return None
        return bytes_to_wav(raw)

    def close(self) -> None:
        """Освобождает ресурсы."""
        self.stop()
        self._p.terminate()
