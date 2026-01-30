#!/bin/bash
# Запуск только backend. Освобождает порт перед стартом.

set -e
cd "$(dirname "$0")"

PORT=8000
if [ -f .env ]; then
  val=$(grep -E "^API_PORT=" .env 2>/dev/null | cut -d= -f2)
  [ -n "$val" ] && PORT="$val"
fi

for _ in 1 2 3; do
  pids=$(lsof -nti:$PORT 2>/dev/null) || true
  [ -z "$pids" ] && break
  echo "$pids" | xargs kill -9 2>/dev/null || true
  sleep 2
done

pipenv run python run_backend.py
