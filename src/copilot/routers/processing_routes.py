"""Роуты для транскрибации и ответов на вопросы."""

import io
import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from copilot.schemas import (
    AnswerRequest,
    AnswerResponse,
    ProcessResponse,
    ProcessTiming,
    ProcessTranscriptRequest,
    ProcessTranscriptResponse,
    TranscribeResponse,
)
from copilot.services import llm_service, transcription_service

router = APIRouter(prefix="/api/v1", tags=["processing"])
logger = logging.getLogger(__name__)

MAX_AUDIO_SIZE_MB = 25
MAX_AUDIO_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(audio: UploadFile = File(...)) -> TranscribeResponse:
    """Транскрибирует аудиофайл через Whisper API."""
    content = await audio.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Max {MAX_AUDIO_SIZE_MB} MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    try:
        text = await transcription_service.transcribe(content)
        return TranscribeResponse(text=text)
    except Exception as e:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=502, detail="Transcription failed") from e


@router.post("/process-transcript", response_model=ProcessTranscriptResponse)
async def process_transcript(request: ProcessTranscriptRequest) -> ProcessTranscriptResponse:
    """Обрабатывает транскрипт: определяет вопрос, отвечает. Без транскрибации."""
    if not request.transcript.strip():
        return ProcessTranscriptResponse(question=None, answer=None, llm_ms=0)
    t0 = time.perf_counter()
    try:
        is_q, answer = await llm_service.process_question_or_answer(request.transcript)
        llm_ms = int((time.perf_counter() - t0) * 1000)
        if not is_q:
            return ProcessTranscriptResponse(question=None, answer=None, llm_ms=llm_ms)
        return ProcessTranscriptResponse(
            question=request.transcript,
            answer=answer or "",
            llm_ms=llm_ms,
        )
    except Exception as e:
        logger.exception("Process transcript failed")
        raise HTTPException(status_code=502, detail="Processing failed") from e


@router.post("/answer", response_model=AnswerResponse)
async def answer_question(request: AnswerRequest) -> AnswerResponse:
    """Отвечает на вопрос собеседника через LLM."""
    try:
        answer = await llm_service.answer_question(request.question)
        return AnswerResponse(question=request.question, answer=answer)
    except Exception as e:
        logger.exception("LLM answer failed")
        raise HTTPException(status_code=502, detail="LLM answer failed") from e


@router.post("/process", response_model=ProcessResponse)
async def process_audio(audio: UploadFile = File(...)) -> ProcessResponse:
    """Транскрибирует аудио, определяет вопрос, отвечает. Всё в одном запросе."""
    content = await audio.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Max {MAX_AUDIO_SIZE_MB} MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    t0 = time.perf_counter()
    try:
        t1 = time.perf_counter()
        transcript = await transcription_service.transcribe(content)
        transcribe_ms = int((time.perf_counter() - t1) * 1000)
        if not transcript.strip():
            total_ms = int((time.perf_counter() - t0) * 1000)
            return ProcessResponse(
                transcript="",
                question=None,
                answer=None,
                timing=ProcessTiming(transcribe_ms=transcribe_ms, llm_ms=0, total_ms=total_ms),
            )
        t2 = time.perf_counter()
        is_q, answer = await llm_service.process_question_or_answer(transcript)
        llm_ms = int((time.perf_counter() - t2) * 1000)
        total_ms = int((time.perf_counter() - t0) * 1000)
        if not is_q:
            return ProcessResponse(
                transcript=transcript,
                question=None,
                answer=None,
                timing=ProcessTiming(transcribe_ms=transcribe_ms, llm_ms=llm_ms, total_ms=total_ms),
            )
        return ProcessResponse(
            transcript=transcript,
            question=transcript,
            answer=answer or "",
            timing=ProcessTiming(transcribe_ms=transcribe_ms, llm_ms=llm_ms, total_ms=total_ms),
        )
    except Exception as e:
        logger.exception("Process failed")
        raise HTTPException(status_code=502, detail="Processing failed") from e
