# Makefile - HealthShield AI

PY=python
BACKEND_DIR=backend

.PHONY: help install run test etl docker-up docker-down clean

help:
	@echo "HealthShield AI - Comandos disponibles"
	@echo "  install      Instala dependencias del backend"
	@echo "  run          Levanta Django en modo desarrollo"
	@echo "  test         Ejecuta pytest en backend"
	@echo "  etl          Ejecuta el comando ETL definido en Django"
	@echo "  docker-up    Arranca el stack Docker completo"
	@echo "  docker-down  Detiene el stack Docker"
	@echo "  clean        Limpia caches temporales"

install:
	cd $(BACKEND_DIR) && $(PY) -m pip install -r requirements.txt
	@echo "OK: dependencias instaladas"

run:
	cd $(BACKEND_DIR) && $(PY) manage.py runserver

test:
	cd $(BACKEND_DIR) && $(PY) -m pytest -q

etl:
	cd $(BACKEND_DIR) && $(PY) manage.py run_etl

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

clean:
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist tests\__pycache__ rmdir /s /q tests\__pycache__
	@echo "OK: caches limpiados"
