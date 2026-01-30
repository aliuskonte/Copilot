"""Тесты FastAPI endpoints."""

from unittest.mock import AsyncMock, patch

import pytest


class TestHealth:
    def test_health_returns_ok(self, client) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe_success(self, client, test_wav) -> None:
        with patch(
            "copilot.routers.processing_routes.transcription_service"
        ) as mock_svc:
            mock_svc.transcribe = AsyncMock(return_value="Транскрипт")
            response = client.post(
                "/api/v1/transcribe",
                files={"audio": ("audio.wav", test_wav, "audio/wav")},
            )
            assert response.status_code == 200
            assert response.json() == {"text": "Транскрипт"}

    def test_transcribe_empty_file_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/transcribe",
            files={"audio": ("audio.wav", b"", "audio/wav")},
        )
        assert response.status_code == 400
        assert "Empty" in response.json()["detail"]

    def test_transcribe_large_file_returns_413(self, client, large_wav) -> None:
        response = client.post(
            "/api/v1/transcribe",
            files={"audio": ("audio.wav", large_wav, "audio/wav")},
        )
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()


class TestAnswer:
    @pytest.mark.asyncio
    async def test_answer_success(self, client) -> None:
        with patch("copilot.routers.processing_routes.llm_service") as mock_svc:
            mock_svc.answer_question = AsyncMock(return_value="Ответ")
            response = client.post(
                "/api/v1/answer",
                json={"question": "Какой день?"},
            )
            assert response.status_code == 200
            assert response.json() == {
                "question": "Какой день?",
                "answer": "Ответ",
            }

    def test_answer_empty_question_returns_422(self, client) -> None:
        response = client.post(
            "/api/v1/answer",
            json={"question": ""},
        )
        assert response.status_code == 422


class TestProcess:
    @pytest.mark.asyncio
    async def test_process_empty_transcript(
        self, client, test_wav
    ) -> None:
        with patch(
            "copilot.routers.processing_routes.transcription_service"
        ) as mock_trans:
            mock_trans.transcribe = AsyncMock(return_value="")
            response = client.post(
                "/api/v1/process",
                files={"audio": ("audio.wav", test_wav, "audio/wav")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["transcript"] == ""
            assert data["question"] is None
            assert data["answer"] is None
            assert "timing" in data

    @pytest.mark.asyncio
    async def test_process_not_question(
        self, client, test_wav
    ) -> None:
        with patch(
            "copilot.routers.processing_routes.transcription_service"
        ) as mock_trans, patch(
            "copilot.routers.processing_routes.llm_service"
        ) as mock_llm:
            mock_trans.transcribe = AsyncMock(return_value="Просто утверждение")
            mock_llm.process_question_or_answer = AsyncMock(return_value=(False, None))
            response = client.post(
                "/api/v1/process",
                files={"audio": ("audio.wav", test_wav, "audio/wav")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["transcript"] == "Просто утверждение"
            assert data["question"] is None
            assert data["answer"] is None
            assert "timing" in data

    @pytest.mark.asyncio
    async def test_process_question(
        self, client, test_wav
    ) -> None:
        with patch(
            "copilot.routers.processing_routes.transcription_service"
        ) as mock_trans, patch(
            "copilot.routers.processing_routes.llm_service"
        ) as mock_llm:
            mock_trans.transcribe = AsyncMock(return_value="Какой день?")
            mock_llm.process_question_or_answer = AsyncMock(
                return_value=(True, "Понедельник")
            )
            response = client.post(
                "/api/v1/process",
                files={"audio": ("audio.wav", test_wav, "audio/wav")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["transcript"] == "Какой день?"
            assert data["question"] == "Какой день?"
            assert data["answer"] == "Понедельник"
            assert "timing" in data

    def test_process_empty_file_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/process",
            files={"audio": ("audio.wav", b"", "audio/wav")},
        )
        assert response.status_code == 400

    def test_process_large_file_returns_413(self, client, large_wav) -> None:
        response = client.post(
            "/api/v1/process",
            files={"audio": ("audio.wav", large_wav, "audio/wav")},
        )
        assert response.status_code == 413
