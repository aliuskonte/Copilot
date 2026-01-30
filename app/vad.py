"""Voice Activity Detection — сегментация речи по тишине."""

import webrtcvad

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 20
FRAME_BYTES = int(SAMPLE_RATE * (FRAME_DURATION_MS / 1000) * 2)


def _frame_generator(audio: bytes, sample_rate: int) -> list[bytes]:
    """Разбивает PCM на кадры по 20ms (16-bit mono)."""
    n = int(sample_rate * (FRAME_DURATION_MS / 1000.0) * 2)
    frames = []
    offset = 0
    while offset + n <= len(audio):
        frames.append(audio[offset : offset + n])
        offset += n
    return frames


def segment_audio(
    audio: bytes,
    sample_rate: int = SAMPLE_RATE,
    aggressiveness: int = 2,
    padding_duration_ms: int = 300,
) -> list[bytes]:
    """
    Сегментирует PCM-аудио на сегменты речи.
    Возвращает список сырых PCM-байтов (только речь).
    """
    if sample_rate not in (8000, 16000, 32000):
        raise ValueError("webrtcvad supports 8000, 16000, 32000 Hz only")
    if len(audio) < FRAME_BYTES:
        return []
    vad = webrtcvad.Vad(aggressiveness)
    frames = _frame_generator(audio, sample_rate)
    num_padding = max(1, padding_duration_ms // FRAME_DURATION_MS)
    ring: list[tuple[bytes, bool]] = []
    triggered = False
    voiced_frames: list[bytes] = []
    segments: list[bytes] = []

    for frame in frames:
        is_speech = vad.is_speech(frame, sample_rate)
        if not triggered:
            ring.append((frame, is_speech))
            if len(ring) > num_padding:
                ring.pop(0)
            num_voiced = sum(1 for _, s in ring if s)
            if num_voiced > 0.9 * len(ring):
                triggered = True
                voiced_frames = [f for f, _ in ring]
                ring.clear()
        else:
            voiced_frames.append(frame)
            ring.append((frame, is_speech))
            if len(ring) > num_padding:
                ring.pop(0)
            num_unvoiced = sum(1 for _, s in ring if not s)
            if num_unvoiced > 0.9 * len(ring):
                triggered = False
                segment = b"".join(voiced_frames)
                if len(segment) >= SAMPLE_RATE * 2:  # минимум ~1 сек (16-bit)
                    segments.append(segment)
                voiced_frames = []
                ring.clear()

    if triggered and voiced_frames:
        segment = b"".join(voiced_frames)
        if len(segment) >= SAMPLE_RATE * 2:
            segments.append(segment)

    return segments


def get_last_speech_segment(
    audio: bytes,
    sample_rate: int = SAMPLE_RATE,
    min_speech_sec: float = 1.0,
    **kwargs: int,
) -> bytes | None:
    """
    Возвращает последний сегмент речи из аудио.
    None, если сегментов нет или последний короче min_speech_sec.
    """
    segments = segment_audio(audio, sample_rate, **kwargs)
    if not segments:
        return None
    last = segments[-1]
    min_bytes = int(sample_rate * min_speech_sec * 2)
    if len(last) < min_bytes:
        return None
    return last
