#!/usr/bin/env bash
# Entrypoint backend: jalankan migrasi DB lalu start server.
set -euo pipefail

echo "[entrypoint] Menjalankan migrasi Alembic..."
alembic upgrade head

echo "[entrypoint] Memulai uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}"
