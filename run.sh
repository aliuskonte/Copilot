#!/bin/bash
# Единый скрипт запуска Copilot: освобождает порт, запускает backend и desktop.

set -e
cd "$(dirname "$0")"

# Порт из .env или 8000
PORT=8000
if [ -f .env ]; then
  val=$(grep -E "^API_PORT=" .env 2>/dev/null | cut -d= -f2)
  [ -n "$val" ] && PORT="$val"
fi

echo "Copilot: освобождаю порт $PORT..."
lsof -ti:$PORT | xargs kill 2>/dev/null || true
sleep 1

echo "Copilot: запускаю backend..."
pipenv run python run_backend.py &
BACKEND_PID=$!

echo "Copilot: жду готовности API..."
for i in $(seq 1 30); do
  if curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    echo "Copilot: backend готов"
    break
  fi
  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Copilot: backend завершился с ошибкой"
    exit 1
  fi
  sleep 1
done

echo "Copilot: запускаю desktop..."
pipenv run python run_desktop.py
