FROM python:3.12-slim

WORKDIR /app

# ── Dependencias del sistema ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ─────────────────────────────────────────────────────────────────
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt gunicorn

# ── Archivos del proyecto ───────────────────────────────────────────────────────
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY datasets/ /app/datasets/
COPY .env.example /app/.env

# ── Directorios runtime ─────────────────────────────────────────────────────────
RUN mkdir -p /app/ml_models /app/media /app/staticfiles

# ── Usuario sin privilegios ────────────────────────────────────────────────────
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000