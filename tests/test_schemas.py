"""Тесты Pydantic-схем."""

import pytest
from pydantic import ValidationError

from copilot.schemas import (
    AnswerRequest,
    AnswerResponse,
    ProcessResponse,
    TranscribeResponse,
)


class TestAnswerRequest:
    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError):
            AnswerRequest(question="")

    def test_single_char_valid(self) -> None:
        req = AnswerRequest(question="?")
        assert req.question == "?"

    def test_valid_question(self) -> None:
        req = AnswerRequest(question="Какой сегодня день?")
        assert req.question == "Какой сегодня день?"


class TestTranscribeResponse:
    def test_serialization(self) -> None:
        resp = TranscribeResponse(text="Привет мир")
        assert resp.text == "Привет мир"
        assert resp.model_dump() == {"text": "Привет мир"}


class TestAnswerResponse:
    def test_serialization(self) -> None:
        resp = AnswerResponse(question="Что?", answer="Ответ")
        assert resp.question == "Что?"
        assert resp.answer == "Ответ"
        assert resp.model_dump() == {"question": "Что?", "answer": "Ответ"}


class TestProcessResponse:
    def test_with_question_and_answer(self) -> None:
        resp = ProcessResponse(
            transcript="Какой день?",
            question="Какой день?",
            answer="Понедельник",
        )
        assert resp.transcript == "Какой день?"
        assert resp.question == "Какой день?"
        assert resp.answer == "Понедельник"

    def test_without_question(self) -> None:
        resp = ProcessResponse(transcript="Просто текст", question=None, answer=None)
        assert resp.transcript == "Просто текст"
        assert resp.question is None
        assert resp.answer is None
