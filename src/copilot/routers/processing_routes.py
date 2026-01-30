"""Роуты для транскрибации и ответов на вопросы."""

import io
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from copilot.schemas import AnswerRequest, AnswerResponse, ProcessResponse, TranscribeResponse
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
    try:
        transcript = await transcription_service.transcribe(content)
        if not transcript.strip():
            return ProcessResponse(transcript="", question=None, answer=None)
        is_q = await llm_service.is_question(transcript)
        if not is_q:
            return ProcessResponse(transcript=transcript, question=None, answer=None)
        answer = await llm_service.answer_question(transcript)
        return ProcessResponse(
            transcript=transcript,
            question=transcript,
            answer=answer,
        )
    except Exception as e:
        logger.exception("Process failed")
        raise HTTPException(status_code=502, detail="Processing failed") from e
