# ============================================
# Backend FastAPI — Green Bean Grading (#37)
# ============================================
FROM python:3.11-slim

# Dependensi sistem untuk OpenCV & runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependency Python lebih dulu (manfaatkan layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin kode aplikasi
COPY . .

# Jalankan sebagai user non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck memakai endpoint /health (#8)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# entrypoint.sh menjalankan migrasi Alembic lalu start uvicorn
ENTRYPOINT ["./entrypoint.sh"]
