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

### Вариант 1: Единый скрипт (рекомендуется)

Освобождает порт, запускает backend и desktop. Не возникает ошибка «Address already in use»:

```bash
./run.sh
```

### Вариант 2: Два терминала

**Терминал 1 — Backend:**
```bash
./run_backend.sh
# или: pipenv run python run_backend.py
```

**Терминал 2 — Desktop:**
```bash
pipenv run python run_desktop.py
```

`run_backend.sh` освобождает порт перед стартом.

## Использование

1. Запустите backend и desktop-клиент
2. Начните созвон (Zoom, Meet и т.п.)
3. Когда собеседник задал вопрос — нажмите «Обработать последние 15 сек» или включите «Авто»
4. Вопрос и ответ LLM появятся в интерфейсе

**Авто:** включите чекбокс «Авто: проверять каждые 3 сек» — приложение будет автоматически обрабатывать последний сегмент речи (VAD) и отправлять на API. Минимум 8 сек между запросами.

## API

- `POST /api/v1/transcribe` — транскрибация аудио (Whisper)
- `POST /api/v1/answer` — ответ на вопрос (GPT)
- `POST /api/v1/process` — транскрибация + определение вопроса + ответ (всё в одном). Возвращает `timing`: `transcribe_ms`, `llm_ms`, `total_ms`

## Бенчмарк скорости

```bash
# Backend должен быть запущен
pipenv run python tools/benchmark_process.py -s 5 -n 3
# -s 5: 5 сек аудио
# -n 3: 3 запуска
```

## Структура проекта

```
src/copilot/     — FastAPI backend
app/             — Desktop-клиент (PyQt6 + PyAudio)
```
