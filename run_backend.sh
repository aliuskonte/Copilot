#!/bin/bash
# Запуск только backend. Освобождает порт перед стартом.

set -e
cd "$(dirname "$0")"

PORT=8000
if [ -f .env ]; then
  val=$(grep -E "^API_PORT=" .env 2>/dev/null | cut -d= -f2)
  [ -n "$val" ] && PORT="$val"
fi

lsof -ti:$PORT | xargs kill 2>/dev/null || true
sleep 1

pipenv run python run_backend.py
