# Тесты

## Запуск

```bash
pipenv run python -m pytest
```

С опциями:
```bash
pipenv run python -m pytest -v           # подробный вывод
pipenv run python -m pytest tests/test_api.py  # только API
pipenv run python -m pytest --tb=long  # полный traceback
```

## Структура

- `conftest.py` — фикстуры (client, test_wav, large_wav), env
- `test_schemas.py` — Pydantic-схемы
- `test_audio_recorder.py` — bytes_to_wav, find_blackhole, AudioRecorder
- `test_api.py` — FastAPI endpoints (health, transcribe, answer, process)
- `test_services.py` — TranscriptionService, LLMService (с моками OpenAI)
- `test_api_client.py` — desktop API client
