# Copilot — помощник на созвонах

Приложение для помощи во время созвонов: захват системного звука, транскрибация речи собеседника, ответы LLM на вопросы.

## Требования

- macOS (для захвата системного звука через BlackHole)
- Python 3.12+
- [BlackHole](https://existential.audio/blackhole/) — виртуальный аудио-драйвер
- OpenAI API key

## Установка

### 1. Системные зависимости

```bash
brew install blackhole-2ch portaudio
```

Создайте Multi-Output Device в **Audio MIDI Setup**:
- Откройте «Audio MIDI Setup» → «Audio Devices»
- «+» → «Create Multi-Output Device»
- Включите «Built-in Output» и «BlackHole 2ch»
- В системных настройках звука выберите этот Multi-Output Device

### 2. Зависимости

```bash
pipenv install
```

### 3. Конфигурация

```bash
cp .env.example .env
# Отредактируйте .env и укажите OPENAI_API_KEY
```

## Запуск

### Терминал 1 — Backend

```bash
pipenv run python run_backend.py
```

Или:

```bash
pipenv run uvicorn copilot.main:app --reload --host 127.0.0.1 --port 8000
```

### Терминал 2 — Desktop-клиент

```bash
pipenv run python run_desktop.py
```

## Использование

1. Запустите backend и desktop-клиент
2. Начните созвон (Zoom, Meet и т.п.)
3. Когда собеседник задал вопрос — нажмите «Обработать последние 30 сек»
4. Вопрос и ответ LLM появятся в интерфейсе

## API

- `POST /api/v1/transcribe` — транскрибация аудио (Whisper)
- `POST /api/v1/answer` — ответ на вопрос (GPT)
- `POST /api/v1/process` — транскрибация + определение вопроса + ответ (всё в одном)

## Структура проекта

```
src/copilot/     — FastAPI backend
app/             — Desktop-клиент (PyQt6 + PyAudio)
```
