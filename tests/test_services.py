"""Тесты сервисов транскрибации и LLM."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from copilot.services import llm_service, transcription_service


class TestTranscriptionService:
    @pytest.mark.asyncio
    async def test_transcribe_returns_text(self, test_wav) -> None:
        with patch.object(
            transcription_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.text = "Транскрибированный текст"
            mock_create.return_value = mock_response

            result = await transcription_service.transcribe(test_wav)
            assert result == "Транскрибированный текст"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_accepts_bytes_io(self) -> None:
        with patch.object(
            transcription_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.text = "OK"
            mock_create.return_value = mock_response

            audio = io.BytesIO(b"\x00\x00" * 8000)
            result = await transcription_service.transcribe(audio)
            assert result == "OK"


class TestLLMService:
    @pytest.mark.asyncio
    async def test_answer_question_returns_answer(self) -> None:
        with patch.object(
            llm_service._client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="Понедельник"))
            ]
            mock_create.return_value = mock_response

            result = await llm_service.answer_question("Какой день?")
            assert result == "Понедельник"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_question_returns_true(self) -> None:
        with patch.object(
            llm_service._client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="да"))
            ]
            mock_create.return_value = mock_response

            result = await llm_service.is_question("Какой день?")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_question_returns_false(self) -> None:
        with patch.object(
            llm_service._client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="нет"))
            ]
            mock_create.return_value = mock_response

            result = await llm_service.is_question("Просто утверждение")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_question_empty_returns_false(self) -> None:
        result = await llm_service.is_question("")
        assert result is False

    @pytest.mark.asyncio
    async def test_process_question_or_answer_question(self) -> None:
        with patch.object(
            llm_service._client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="Понедельник"))
            ]
            mock_create.return_value = mock_response

            is_q, answer = await llm_service.process_question_or_answer("Какой день?")
            assert is_q is True
            assert answer == "Понедельник"

    @pytest.mark.asyncio
    async def test_process_question_or_answer_not_question(self) -> None:
        with patch.object(
            llm_service._client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="NOT_A_QUESTION"))
            ]
            mock_create.return_value = mock_response

            is_q, answer = await llm_service.process_question_or_answer("Просто текст")
            assert is_q is False
            assert answer is None

    @pytest.mark.asyncio
    async def test_process_question_or_answer_empty_returns_false(self) -> None:
        is_q, answer = await llm_service.process_question_or_answer("")
        assert is_q is False
        assert answer is None
