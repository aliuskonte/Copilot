"""Тесты API-клиента desktop приложения."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetBaseUrl:
    def test_default_from_env(self) -> None:
        with patch.dict(
            "os.environ",
            {"API_HOST": "127.0.0.1", "API_PORT": "8000"},
            clear=False,
        ):
            from importlib import reload
            import app.api_client as api_client

            reload(api_client)
            url = api_client.get_base_url()
            assert url == "http://127.0.0.1:8000"

    def test_custom_host_port(self) -> None:
        with patch.dict(
            "os.environ",
            {"API_HOST": "localhost", "API_PORT": "9000"},
            clear=False,
        ):
            from importlib import reload
            import app.api_client as api_client

            reload(api_client)
            url = api_client.get_base_url()
            assert url == "http://localhost:9000"


class TestProcessAudio:
    @pytest.mark.asyncio
    async def test_process_audio_success(self, test_wav) -> None:
        with patch("app.api_client.httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "transcript": "Текст",
                "question": "Вопрос?",
                "answer": "Ответ",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            from app.api_client import process_audio

            result = await process_audio(test_wav)
            assert result["transcript"] == "Текст"
            assert result["question"] == "Вопрос?"
            assert result["answer"] == "Ответ"
