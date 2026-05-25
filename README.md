# HealthShield AI

Plataforma Fullstack Django para ETL clínico, Machine Learning y dashboard analítico.

## 📌 Qué hay en este repositorio

- `backend/`: aplicación Django con APIs REST, ETL, ML y autorizaciones JWT.
- `frontend/`: plantillas y recursos estáticos del dashboard.
- `docker/`: Dockerfile, Nginx y scripts de despliegue.
- `docs/`: documentación técnica profesional.
- `scripts/`: automatización local para ETL, ML y pruebas.
- `tests/`: pruebas unitarias e integración independientes del código fuente.

## 🚀 Inicio rápido

### Opción A: Entorno local

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
copy .env.example .env
cd backend
python manage.py migrate
python manage.py runserver
```

### Opción B: Docker

```powershell
docker-compose up --build
```

## 🧩 Comandos útiles

```powershell
make install     # instala dependencias
make run         # levanta el servidor Django local
make test        # ejecuta pytest
python run_tests.py # ejecuta pytest usando el runner de proyecto
make etl         # ejecuta ETL con el comando Django
make docker-up   # levanta stack Docker (pendiente)
make clean       # limpia caches temporales
```

## 📚 Documentación técnica

- `docs/overview.md`: visión general del proyecto y arquitectura.
- `docs/api.md`: referencia de la API REST.
- `docs/architecture.md`: diseño del sistema.
- `docs/erd.sql`: modelo relacional.
- `docs/roadmap.md`: tareas y mejoras planificadas.

## 🧠 Buenas prácticas

- Mantén `backend/` como el único código fuente Django.
- Usa `tests/` para pruebas independientes.
- No subas entornos virtuales ni artefactos de build.
- Usa `scripts/` para automatizar flujos repetibles.
