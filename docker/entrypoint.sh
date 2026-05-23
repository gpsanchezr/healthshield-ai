#!/bin/bash
set -e

echo "⏳ Aplicando migraciones..."
python backend/manage.py migrate --noinput

echo "📦 Recolectando archivos estáticos..."
python backend/manage.py collectstatic --noinput

echo "👤 Creando superusuario si no existe..."
python backend/manage.py createsuperuser_if_not_exists \
    --user admin --email admin@healthshield.ai --password admin123 || true

echo "🚀 Iniciando servidor..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2