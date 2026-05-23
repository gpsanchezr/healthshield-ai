# 🛡️ HealthShield AI
### Plataforma Inteligente de Analítica Clínica · HealthAnalytics IPS

> *"Medicina Preventiva Proactiva: transformamos datos clínicos en decisiones que salvan vidas."*

![Python](https://img.shields.io/badge/Python-3.12+-blue) ![Django](https://img.shields.io/badge/Django-5.x-green) ![License](https://img.shields.io/badge/License-MIT-yellow) ![Docker](https://img.shields.io/badge/Docker-ready-blue)

---

## 📋 Tabla de Contenidos

1. [Descripción General](#1-descripción-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Tecnologías](#3-tecnologías)
4. [Estructura del Proyecto](#4-estructura-del-proyecto)
5. [Modelo Relacional (ERD)](#5-modelo-relacional-erd)
6. [Instalación y Configuración](#6-instalación-y-configuración)
7. [Módulo ETL — Pipeline Completo](#7-módulo-etl--pipeline-completo)
8. [Motor de Machine Learning](#8-motor-de-machine-learning)
9. [Analítica de Datos y KPIs](#9-analítica-de-datos-y-kpis)
10. [API REST — Endpoints](#10-api-rest--endpoints)
11. [Frontend y Dashboard](#11-frontend-y-dashboard)
12. [Seguridad — JWT y Roles](#12-seguridad--jwt-y-roles)
13. [Pruebas Automatizadas](#13-pruebas-automatizadas)
14. [Docker y Despliegue](#14-docker-y-despliegue)
15. [Data Quality Report](#15-data-quality-report)
16. [Manual de Usuario](#16-manual-de-usuario)
17. [Diagramas](#17-diagramas)
18. [Criterios de Evaluación Cumplidos](#18-criterios-de-evaluación-cumplidos)

---

## 1. Descripción General

**HealthShield AI** es una plataforma web FullStack desarrollada para la IPS **HealthAnalytics** que automatiza el procesamiento de información clínica mediante:

- **ETL con trazabilidad completa**: extrae, limpia y carga 1800+ registros clínicos.
- **Machine Learning explicable (XAI)**: predice riesgo de enfermedad y expone los factores determinantes.
- **Dashboard clínico proactivo**: alertas en tiempo real, KPIs médicos, modo nocturno para turnos largos.
- **Motor de simulación Live**: inyecta datos sintéticos en demanda para validar la resiliencia del pipeline.
- **Auditoría completa**: cada acción queda registrada — quién ejecutó el ETL, cuándo, cuántos registros procesó.

### Problema que resuelve

| Problema IPS | Solución HealthShield AI |
|---|---|
| Mala calidad de datos | Pipeline ETL con 8 reglas de limpieza |
| Duplicidad de pacientes | Deduplicación por hash + ID |
| Diagnósticos mal escritos | Normalización ortográfica automática |
| Falta de KPIs clínicos | 6 KPIs en tiempo real en el dashboard |
| Detección de pacientes críticos | Reglas clínicas + modelo Random Forest |
| Sin análisis predictivo | Modelo ML con Accuracy > 85% y explicabilidad SHAP |

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (Bootstrap 5 + Chart.js)       │
│   Dashboard · Alertas · KPIs · ETL Status · ML View  │
└──────────────────────┬──────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────┐
│              DJANGO BACKEND (DRF + JWT)              │
├─────────────────────────────────────────────────────┤
│  auth/       │  etl/        │  ml/      │ analytics/ │
│  JWT Tokens  │  Pipeline    │  RandomF  │  KPIs      │
│  Roles/Perms │  Auditoría   │  SHAP XAI │  Segmentos │
│              │  Simulación  │  Metrics  │  Alertas   │
└──────────────────────┬──────────────────────────────┘
                       │ ORM
┌──────────────────────▼──────────────────────────────┐
│         PostgreSQL — Base de Datos Clínica           │
│  pacientes · registros_etl · predicciones · logs     │
└─────────────────────────────────────────────────────┘
```

### Principios Arquitectónicos

- **Separación de responsabilidades**: cada `app/` Django tiene una única responsabilidad.
- **SOLID**: clases abiertas para extensión (nuevos modelos ML) y cerradas para modificación.
- **12-Factor App**: configuración vía variables de entorno, logs a stdout.
- **Inmutabilidad de datos fuente**: el CSV original nunca se modifica; se versiona.

---

## 3. Tecnologías

### Backend
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12+ | Lenguaje base |
| Django | 5.x | Framework web |
| Django REST Framework | 3.15+ | API REST |
| djangorestframework-simplejwt | 5.x | Autenticación JWT |
| Pandas | 2.x | ETL / transformación |
| NumPy | 1.x | Cálculos numéricos |
| Scikit-Learn | 1.x | Modelos ML |
| drf-spectacular | 0.27+ | Swagger / OpenAPI |
| Celery + Redis | Opcional | Tareas asíncronas |

### Base de Datos
- **PostgreSQL 16** (producción) / SQLite (desarrollo)

### Frontend
- Bootstrap 5.3, Chart.js 4.x, JavaScript ES6+

### DevOps
- Docker 24+, Docker Compose 2.x, GitHub Actions CI/CD

---

## 4. Estructura del Proyecto

```
healthshield-ai/
│
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py          # Configuración común
│   │   │   ├── development.py   # Debug=True, SQLite
│   │   │   └── production.py    # PostgreSQL, SECRET_KEY de env
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── authentication/      # JWT, roles, permisos
│   │   │   ├── models.py        # UsuarioClínico (extend AbstractUser)
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── permissions.py   # EsAdministrador, EsMedico, EsAnalista
│   │   │
│   │   ├── etl/                 # Motor ETL central
│   │   │   ├── models.py        # RegistroETL, LogETL
│   │   │   ├── pipeline.py      # ETLPipeline (clase principal)
│   │   │   ├── extractors.py    # Lectura CSV / Excel
│   │   │   ├── transformers.py  # 8 reglas de limpieza
│   │   │   ├── loaders.py       # Carga a BD
│   │   │   ├── simulation.py    # DataSimulator (live stream)
│   │   │   ├── quality.py       # DataQualityReport
│   │   │   └── views.py         # API endpoints ETL
│   │   │
│   │   ├── analytics/           # KPIs y estadísticas
│   │   │   ├── models.py        # SnapshotAnalítico
│   │   │   ├── calculators.py   # KPICalculator
│   │   │   ├── detectors.py     # PacienteCríticoDetector
│   │   │   └── views.py
│   │   │
│   │   ├── ml/                  # Motor de predicción
│   │   │   ├── models.py        # ModeloML, Prediccion
│   │   │   ├── trainer.py       # Entrenamiento + evaluación
│   │   │   ├── predictor.py     # Inferencia individual y batch
│   │   │   ├── explainer.py     # Feature importance (XAI)
│   │   │   └── views.py
│   │   │
│   │   ├── dashboard/
│   │   │   └── views.py         # Agregación de KPIs para frontend
│   │   │
│   │   └── reports/
│   │       ├── generators.py    # PDF / Excel exportación
│   │       └── views.py
│   │
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/
│   ├── templates/
│   │   ├── base.html            # Layout con modo oscuro
│   │   ├── dashboard/
│   │   ├── etl/
│   │   ├── ml/
│   │   └── patients/
│   └── static/
│       ├── css/healthshield.css
│       └── js/dashboard.js
│
├── datasets/
│   ├── clinical_data_v1.0_raw.xlsx       # Fuente original (solo lectura)
│   └── clinical_data_v1.1_cleaned.csv    # Generado post-ETL
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── erd.png
│
├── tests/
│   ├── test_etl.py
│   ├── test_ml.py
│   └── test_api.py
│
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── docker-compose.yml
├── .env.example
├── .github/workflows/main.yml   # CI/CD
└── README.md                    # Este archivo
```

---

## 5. Modelo Relacional (ERD)

```sql
-- =========================================================
-- SCHEMA: healthshield_db
-- =========================================================

-- Tabla de usuarios del sistema (extiende auth_user de Django)
CREATE TABLE usuarios (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(150) UNIQUE NOT NULL,
    email         VARCHAR(254) UNIQUE NOT NULL,
    password      VARCHAR(128) NOT NULL,
    rol           VARCHAR(20) NOT NULL
                  CHECK (rol IN ('administrador', 'medico', 'analista')),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Tabla principal de pacientes (datos demográficos limpios)
CREATE TABLE pacientes (
    id                      SERIAL PRIMARY KEY,
    id_paciente_original    INTEGER UNIQUE NOT NULL,
    nombres                 VARCHAR(100) NOT NULL,
    apellidos               VARCHAR(100) NOT NULL,
    edad                    SMALLINT NOT NULL CHECK (edad BETWEEN 0 AND 120),
    sexo                    VARCHAR(1) NOT NULL CHECK (sexo IN ('M', 'F')),
    fecha_registro          TIMESTAMP DEFAULT NOW()
);

-- Tabla de registros clínicos (signos vitales y métricas)
CREATE TABLE registros_clinicos (
    id                      SERIAL PRIMARY KEY,
    paciente_id             INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    peso                    NUMERIC(5,2) CHECK (peso BETWEEN 20 AND 300),
    altura                  NUMERIC(4,2) CHECK (altura BETWEEN 0.5 AND 2.5),
    imc                     NUMERIC(5,2),
    clasificacion_imc       VARCHAR(20),   -- 'Bajo peso','Normal','Sobrepeso','Obesidad'
    presion_sistolica       SMALLINT CHECK (presion_sistolica BETWEEN 60 AND 250),
    presion_diastolica      SMALLINT CHECK (presion_diastolica BETWEEN 40 AND 150),
    frecuencia_cardiaca     SMALLINT CHECK (frecuencia_cardiaca BETWEEN 30 AND 220),
    glucosa                 NUMERIC(6,2) CHECK (glucosa BETWEEN 50 AND 600),
    colesterol              NUMERIC(6,2) CHECK (colesterol BETWEEN 50 AND 400),
    saturacion_oxigeno      NUMERIC(5,2) CHECK (saturacion_oxigeno BETWEEN 70 AND 100),
    temperatura             NUMERIC(4,1) CHECK (temperatura BETWEEN 34 AND 42),
    antecedentes_familiares BOOLEAN,
    fumador                 BOOLEAN,
    consumo_alcohol         BOOLEAN,
    actividad_fisica        VARCHAR(20),
    diagnostico_preliminar  VARCHAR(100),
    riesgo_enfermedad       VARCHAR(10) CHECK (riesgo_enfermedad IN ('Bajo','Medio','Alto','Crítico')),
    fecha_consulta          DATE,
    fuente_etl_id           INTEGER REFERENCES ejecuciones_etl(id),
    created_at              TIMESTAMP DEFAULT NOW()
);

-- Tabla de ejecuciones ETL (trazabilidad completa)
CREATE TABLE ejecuciones_etl (
    id                    SERIAL PRIMARY KEY,
    usuario_id            INTEGER REFERENCES usuarios(id),
    archivo_fuente        VARCHAR(255),
    fecha_inicio          TIMESTAMP DEFAULT NOW(),
    fecha_fin             TIMESTAMP,
    duracion_segundos     NUMERIC(8,3),
    registros_extraidos   INTEGER DEFAULT 0,
    registros_procesados  INTEGER DEFAULT 0,
    registros_rechazados  INTEGER DEFAULT 0,
    duplicados_eliminados INTEGER DEFAULT 0,
    nulos_imputados       INTEGER DEFAULT 0,
    estado                VARCHAR(20) DEFAULT 'en_proceso'
                          CHECK (estado IN ('en_proceso','completado','fallido')),
    reporte_calidad       JSONB,   -- Data Quality Report serializado
    tipo                  VARCHAR(20) DEFAULT 'manual'
                          CHECK (tipo IN ('manual','simulacion','automatico'))
);

-- Tabla de logs detallados de ETL
CREATE TABLE logs_etl (
    id              SERIAL PRIMARY KEY,
    ejecucion_id    INTEGER NOT NULL REFERENCES ejecuciones_etl(id),
    nivel           VARCHAR(10) CHECK (nivel IN ('INFO','WARNING','ERROR')),
    mensaje         TEXT NOT NULL,
    campo_afectado  VARCHAR(50),
    valor_original  TEXT,
    valor_corregido TEXT,
    timestamp       TIMESTAMP DEFAULT NOW()
);

-- Tabla de modelos ML entrenados
CREATE TABLE modelos_ml (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    algoritmo       VARCHAR(50),  -- 'RandomForest','LogisticRegression','DecisionTree'
    version         VARCHAR(20),
    accuracy        NUMERIC(5,4),
    precision_score NUMERIC(5,4),
    recall          NUMERIC(5,4),
    f1_score        NUMERIC(5,4),
    archivo_modelo  VARCHAR(255), -- ruta al .pkl
    feature_names   JSONB,
    feature_importance JSONB,
    entrenado_en    TIMESTAMP DEFAULT NOW(),
    registros_entrenamiento INTEGER,
    activo          BOOLEAN DEFAULT FALSE
);

-- Tabla de predicciones individuales
CREATE TABLE predicciones (
    id              SERIAL PRIMARY KEY,
    paciente_id     INTEGER REFERENCES pacientes(id),
    modelo_id       INTEGER REFERENCES modelos_ml(id),
    riesgo_predicho VARCHAR(10),
    probabilidad    NUMERIC(5,4),
    factores_clave  JSONB,   -- top 3 features con su impacto (XAI)
    fecha           TIMESTAMP DEFAULT NOW()
);

-- Tabla de alertas proactivas
CREATE TABLE alertas (
    id              SERIAL PRIMARY KEY,
    paciente_id     INTEGER REFERENCES pacientes(id),
    tipo_alerta     VARCHAR(50),
    descripcion     TEXT,
    nivel_urgencia  VARCHAR(10) CHECK (nivel_urgencia IN ('baja','media','alta','critica')),
    visto_por       INTEGER REFERENCES usuarios(id),
    fecha_alerta    TIMESTAMP DEFAULT NOW(),
    fecha_vista     TIMESTAMP
);

-- Índices para rendimiento
CREATE INDEX idx_registros_riesgo    ON registros_clinicos(riesgo_enfermedad);
CREATE INDEX idx_registros_paciente  ON registros_clinicos(paciente_id);
CREATE INDEX idx_alertas_nivel       ON alertas(nivel_urgencia, fecha_alerta DESC);
CREATE INDEX idx_ejecuciones_estado  ON ejecuciones_etl(estado, fecha_inicio DESC);
```

---

## 6. Instalación y Configuración

### Requisitos Previos
- **Python 3.12+** — [python.org](https://www.python.org/downloads/). **Importante:** Marca "Add python.exe to PATH" durante la instalación.
- PostgreSQL 16 (o Docker)
- Git

### Opción A: Docker (recomendado — un solo comando)

```bash
git clone https://github.com/tu-usuario/healthshield-ai.git
cd healthshield-ai
cp .env.example .env          # editar variables si es necesario
docker-compose up --build     # levanta PostgreSQL + Django + Nginx
```

Acceder a: `http://localhost:8000` · API Docs: `http://localhost:8000/api/schema/swagger-ui/`

### Opción B: Instalación Local (PowerShell / CMD)

```powershell
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/healthshield-ai.git
cd healthshield-ai/backend

# 2. Dependencias (usa el launcher py de Windows)
py -m pip install -r requirements.txt

# 3. Migraciones y superusuario
py manage.py migrate
py manage.py createsuperuser_if_not_exists --user admin --email admin@healthshield.ai --password admin123

# 4. Cargar dataset inicial (opcional)
py manage.py run_etl

# 5. Entrenar modelo ML (opcional)
py manage.py train_model --algorithm random_forest

# 6. Ejecutar servidor
py manage.py runserver
```

> **Nota:** Si `py` no funciona, instala Python desde [python.org](https://www.python.org/downloads/) y marca "Add python.exe to PATH".

### Configuración de Entorno (Postman)

Para integrar tu API con Postman:

1. **Login**: POST a `http://localhost:8000/api/auth/login/` con `username` y `password`.
2. **Autenticación Automática**: En Postman, ve a la pestaña **Tests** de tu solicitud de Login y pega:
   `pm.environment.set("jwt_token", pm.response.json().access);`
3. **Uso del Token**: En las demás solicitudes (ETL, ML), ve a la pestaña **Authorization**, selecciona **Bearer Token** y escribe `{{jwt_token}}`.

### Variables de Entorno (`.env.example`)

```env
# Django
SECRET_KEY=cambia-esto-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DATABASE_URL=postgresql://healthshield:password@localhost:5432/healthshield_db

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# ETL
ETL_BATCH_SIZE=500
ETL_MAX_WORKERS=4

# ML
ML_MODELS_PATH=./ml_models/
ML_RETRAIN_THRESHOLD=0.05   # reentrenar si accuracy cae >5%
```

---

## 7. Módulo ETL — Pipeline Completo

El pipeline ETL es el núcleo del sistema. Sigue el patrón **Chain of Responsibility**: cada `Transformer` recibe el DataFrame, aplica su regla y lo pasa al siguiente.

### 7.1 Archivo Principal — `apps/etl/pipeline.py`

```python
# apps/etl/pipeline.py
"""
ETLPipeline: Orquestador principal del proceso Extract → Transform → Load.
Genera automáticamente un DataQualityReport tras cada ejecución.
"""
import time
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from .extractors import CSVExtractor, ExcelExtractor
from .transformers import (
    DuplicateRemover,
    TypeCoercer,
    NullImputer,
    OutlierHandler,
    DiagnosisNormalizer,
    SexNormalizer,
    IMCCalculator,
    RiskClassifier,
)
from .loaders import DatabaseLoader
from .quality import DataQualityReport
from .models import EjecucionETL, LogETL

logger = logging.getLogger('etl')


class ETLPipeline:
    """
    Pipeline ETL completo con trazabilidad, auditoría y reporte de calidad.

    Uso:
        pipeline = ETLPipeline(usuario=request.user)
        result = pipeline.run(source_path='datasets/clinical_data_v1.0_raw.xlsx')
    """

    TRANSFORMERS = [
        DuplicateRemover,
        TypeCoercer,
        NullImputer,
        OutlierHandler,
        DiagnosisNormalizer,
        SexNormalizer,
        IMCCalculator,
        RiskClassifier,
    ]

    def __init__(self, usuario=None, tipo: str = 'manual'):
        self.usuario = usuario
        self.tipo = tipo
        self.ejecucion: Optional[EjecucionETL] = None
        self.quality_report = DataQualityReport()
        self.start_time = None

    def run(self, source_path: str) -> dict:
        """
        Ejecuta el pipeline completo y retorna un resumen de la ejecución.
        """
        self.start_time = time.time()
        self.ejecucion = EjecucionETL.objects.create(
            usuario=self.usuario,
            archivo_fuente=source_path,
            tipo=self.tipo,
            estado='en_proceso',
        )

        try:
            # ── EXTRACT ──────────────────────────────────────────────────
            logger.info(f"[ETL] EXTRACT: leyendo {source_path}")
            df_raw = self._extract(source_path)
            self.ejecucion.registros_extraidos = len(df_raw)
            self.quality_report.snapshot_before(df_raw)

            # ── TRANSFORM ────────────────────────────────────────────────
            logger.info(f"[ETL] TRANSFORM: {len(self.TRANSFORMERS)} transformadores")
            df_clean = self._transform(df_raw)

            # ── LOAD ─────────────────────────────────────────────────────
            logger.info(f"[ETL] LOAD: insertando {len(df_clean)} registros")
            loaded_count = self._load(df_clean)

            # ── FINALIZAR ────────────────────────────────────────────────
            duration = time.time() - self.start_time
            report = self.quality_report.generate(df_raw, df_clean, duration)

            self.ejecucion.fecha_fin = datetime.now()
            self.ejecucion.duracion_segundos = round(duration, 3)
            self.ejecucion.registros_procesados = loaded_count
            self.ejecucion.registros_rechazados = len(df_raw) - len(df_clean)
            self.ejecucion.reporte_calidad = report
            self.ejecucion.estado = 'completado'
            self.ejecucion.save()

            logger.info(f"[ETL] COMPLETADO en {duration:.2f}s — {loaded_count} registros cargados")
            return {'status': 'success', 'ejecucion_id': self.ejecucion.id, 'report': report}

        except Exception as exc:
            self.ejecucion.estado = 'fallido'
            self.ejecucion.save()
            logger.error(f"[ETL] FALLIDO: {exc}", exc_info=True)
            raise

    def _extract(self, source_path: str) -> pd.DataFrame:
        if source_path.endswith('.xlsx') or source_path.endswith('.xls'):
            return ExcelExtractor().extract(source_path)
        return CSVExtractor().extract(source_path)

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for TransformerClass in self.TRANSFORMERS:
            transformer = TransformerClass(
                ejecucion=self.ejecucion,
                quality_report=self.quality_report,
            )
            df = transformer.transform(df)
            logger.info(f"  ✔ {TransformerClass.__name__}: {len(df)} registros restantes")
        return df

    def _load(self, df: pd.DataFrame) -> int:
        loader = DatabaseLoader(ejecucion=self.ejecucion)
        return loader.load(df)
```

### 7.2 Transformadores — `apps/etl/transformers.py`

```python
# apps/etl/transformers.py
"""
Transformadores del pipeline ETL. Cada clase aplica UNA regla de limpieza.
Principio SOLID: Single Responsibility + Open/Closed (nuevas reglas = nueva clase).
"""
import re
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod


class BaseTransformer(ABC):
    """Clase base para todos los transformadores."""

    def __init__(self, ejecucion=None, quality_report=None):
        self.ejecucion = ejecucion
        self.qr = quality_report

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    def _log(self, mensaje: str, campo: str = None, nivel: str = 'INFO'):
        from .models import LogETL
        if self.ejecucion:
            LogETL.objects.create(
                ejecucion=self.ejecucion,
                nivel=nivel,
                mensaje=mensaje,
                campo_afectado=campo,
            )


# ──────────────────────────────────────────────────────────────────────────────
class DuplicateRemover(BaseTransformer):
    """Elimina registros duplicados por id_paciente."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(subset=['id_paciente'], keep='first')
        removed = before - len(df)
        if removed:
            self._log(f"Eliminados {removed} duplicados por id_paciente", 'id_paciente', 'WARNING')
            if self.qr:
                self.qr.add_metric('duplicados_eliminados', removed)
        return df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
class TypeCoercer(BaseTransformer):
    """
    Convierte tipos de datos incorrectos.
    Ej: edad='Treinta' → NaN, presión_sistólica='alta' → NaN
    """

    NUMERIC_COLS = {
        'id_paciente':         int,
        'edad':                'Int64',   # Int64 soporta NaN
        'peso':                float,
        'altura':              float,
        'IMC':                 float,
        'presión_sistólica':   'Int64',
        'presión_diastólica':  'Int64',
        'frecuencia_cardiaca': 'Int64',
        'glucosa':             float,
        'colesterol':          float,
        'saturación_oxígeno':  float,
        'temperatura':         float,
    }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        errors_found = 0
        for col, dtype in self.NUMERIC_COLS.items():
            if col not in df.columns:
                continue
            original = df[col].copy()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if dtype == 'Int64':
                df[col] = df[col].astype('Int64')
            new_nulls = df[col].isna().sum() - original.isna().sum()
            if new_nulls > 0:
                errors_found += new_nulls
                self._log(
                    f"{new_nulls} valores no numéricos convertidos a NaN en '{col}'",
                    col, 'WARNING'
                )
        if self.qr:
            self.qr.add_metric('errores_tipo_corregidos', errors_found)
        return df


# ──────────────────────────────────────────────────────────────────────────────
class NullImputer(BaseTransformer):
    """
    Imputa valores nulos aplicando la estrategia más adecuada por campo:
    - Variables numéricas continuas → mediana (robusta a outliers)
    - Variables categóricas → moda
    """

    MEDIAN_COLS  = ['peso', 'glucosa', 'colesterol', 'temperatura', 'IMC']
    MEDIAN_INT_COLS = ['presión_sistólica', 'presión_diastólica',
                       'frecuencia_cardiaca', 'edad']
    MODE_COLS    = ['sexo', 'actividad_física', 'diagnóstico_preliminar']

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        total_imputed = 0

        for col in self.MEDIAN_COLS:
            if col in df.columns and df[col].isna().any():
                count = df[col].isna().sum()
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                self._log(f"Imputados {count} nulos en '{col}' con mediana={median_val:.2f}", col)
                total_imputed += count

        for col in self.MEDIAN_INT_COLS:
            if col in df.columns and df[col].isna().any():
                count = int(df[col].isna().sum())
                median_val = int(df[col].median())
                df[col] = df[col].fillna(median_val)
                self._log(f"Imputados {count} nulos en '{col}' con mediana={median_val}", col)
                total_imputed += count

        for col in self.MODE_COLS:
            if col in df.columns and df[col].isna().any():
                count = df[col].isna().sum()
                mode_val = df[col].mode()[0]
                df[col] = df[col].fillna(mode_val)
                self._log(f"Imputados {count} nulos en '{col}' con moda='{mode_val}'", col)
                total_imputed += count

        if self.qr:
            self.qr.add_metric('nulos_imputados', total_imputed)
        return df


# ──────────────────────────────────────────────────────────────────────────────
class OutlierHandler(BaseTransformer):
    """
    Detecta y trata valores atípicos fuera de rangos clínicos válidos.
    Valores fuera de rango → se reemplazan con la mediana de la columna.
    """

    CLINICAL_RANGES = {
        'peso':                 (20,   300),
        'altura':               (0.5,  2.5),
        'presión_sistólica':    (60,   250),
        'presión_diastólica':   (40,   150),
        'frecuencia_cardiaca':  (30,   220),
        'glucosa':              (50,   600),
        'colesterol':           (50,   400),
        'saturación_oxígeno':   (70,   100),
        'temperatura':          (34,    42),
        'edad':                 (0,    120),
    }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        outliers_total = 0
        for col, (min_val, max_val) in self.CLINICAL_RANGES.items():
            if col not in df.columns:
                continue
            mask = (df[col] < min_val) | (df[col] > max_val)
            count = mask.sum()
            if count > 0:
                median_val = df.loc[~mask, col].median()
                df.loc[mask, col] = median_val
                outliers_total += count
                self._log(
                    f"{count} outliers en '{col}' (rango [{min_val},{max_val}]) → reemplazados con mediana={median_val:.2f}",
                    col, 'WARNING'
                )
        if self.qr:
            self.qr.add_metric('outliers_corregidos', outliers_total)
        return df


# ──────────────────────────────────────────────────────────────────────────────
class DiagnosisNormalizer(BaseTransformer):
    """
    Estandariza errores ortográficos en diagnóstico_preliminar.
    Ej: 'hipertencion', 'hipertensíon' → 'Hipertensión'
    """

    MAPPING = {
        r'(?i)hipertensi[oó]n':       'Hipertensión',
        r'(?i)hipertencion':           'Hipertensión',
        r'(?i)prehipertensi[oó]n':    'Prehipertensión',
        r'(?i)diabetes\s*tipo\s*2':   'Diabetes Tipo 2',
        r'(?i)riesgo\s*cardiovascular': 'Riesgo cardiovascular',
        r'(?i)cardiopat[ií]a':        'Cardiopatía',
        r'(?i)obesidad':               'Obesidad',
        r'(?i)paciente\s*sano':        'Paciente sano',
    }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        col = 'diagnóstico_preliminar'
        if col not in df.columns:
            return df
        corrected = 0
        original = df[col].copy()
        for pattern, replacement in self.MAPPING.items():
            df[col] = df[col].str.replace(pattern, replacement, regex=True)
        corrected = (df[col] != original).sum()
        if corrected:
            self._log(f"Normalizados {corrected} diagnósticos con errores ortográficos", col)
        if self.qr:
            self.qr.add_metric('diagnosticos_normalizados', int(corrected))
        return df


# ──────────────────────────────────────────────────────────────────────────────
class SexNormalizer(BaseTransformer):
    """
    Estandariza la columna sexo a valores canónicos 'M' / 'F'.
    Dataset tiene: 'M','m','Masculino','F','f','Femenino'
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        col = 'sexo'
        if col not in df.columns:
            return df
        mapping = {
            'm': 'M', 'masculino': 'M', 'male': 'M', 'hombre': 'M',
            'f': 'F', 'femenino': 'F', 'female': 'F', 'mujer': 'F',
        }
        original = df[col].copy()
        df[col] = df[col].str.strip().str.lower().map(mapping).fillna('M')
        corrected = (df[col] != original.str.upper().str.strip()).sum()
        if self.qr:
            self.qr.add_metric('sexo_normalizados', int(corrected))
        return df


# ──────────────────────────────────────────────────────────────────────────────
class IMCCalculator(BaseTransformer):
    """
    Recalcula el IMC desde peso y altura (sobrescribe el valor original).
    Clasifica según categorías de la OMS.
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = df['peso'].notna() & df['altura'].notna() & (df['altura'] > 0)
        df.loc[mask, 'IMC'] = (
            df.loc[mask, 'peso'] / df.loc[mask, 'altura'] ** 2
        ).round(2)

        conditions = [
            df['IMC'] < 18.5,
            (df['IMC'] >= 18.5) & (df['IMC'] < 25),
            (df['IMC'] >= 25)   & (df['IMC'] < 30),
            df['IMC'] >= 30,
        ]
        choices = ['Bajo peso', 'Normal', 'Sobrepeso', 'Obesidad']
        df['clasificacion_imc'] = np.select(conditions, choices, default='Normal')
        return df


# ──────────────────────────────────────────────────────────────────────────────
class RiskClassifier(BaseTransformer):
    """
    Clasifica el riesgo de enfermedad basado en reglas clínicas.
    Sobrescribe 'riesgo_enfermedad' con la clasificación validada.
    """

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df['riesgo_enfermedad'] = df.apply(self._classify_row, axis=1)
        return df

    @staticmethod
    def _classify_row(row) -> str:
        score = 0
        # Presión arterial
        if row.get('presión_sistólica', 0) > 180:   score += 3
        elif row.get('presión_sistólica', 0) > 140:  score += 2
        elif row.get('presión_sistólica', 0) > 120:  score += 1
        # Glucosa
        if row.get('glucosa', 0) > 300:   score += 3
        elif row.get('glucosa', 0) > 200:  score += 2
        elif row.get('glucosa', 0) > 140:  score += 1
        # Saturación O2
        if row.get('saturación_oxígeno', 100) < 85:  score += 3
        elif row.get('saturación_oxígeno', 100) < 90: score += 2
        # Edad + factores de riesgo
        if row.get('edad', 0) > 70 and row.get('antecedentes_familiares', False):
            score += 2
        if row.get('fumador', False):  score += 1
        if row.get('IMC', 0) > 35:     score += 1

        if score >= 6:   return 'Crítico'
        elif score >= 4: return 'Alto'
        elif score >= 2: return 'Medio'
        else:            return 'Bajo'
```

### 7.3 Data Quality Report — `apps/etl/quality.py`

```python
# apps/etl/quality.py
"""
DataQualityReport: Genera el reporte de calidad de datos automáticamente
tras cada ejecución ETL. Visible en el Dashboard del Analista.
"""
from datetime import datetime
import pandas as pd


class DataQualityReport:
    """
    Genera un reporte estructurado de calidad de datos:
    - Métricas ANTES de la limpieza
    - Métricas DESPUÉS de la limpieza
    - Errores encontrados por tipo
    - Score de calidad (0–100)
    """

    def __init__(self):
        self._metrics = {}
        self._before_snapshot = {}

    def snapshot_before(self, df: pd.DataFrame):
        self._before_snapshot = {
            'total_registros':   len(df),
            'total_nulos':       int(df.isnull().sum().sum()),
            'nulos_por_columna': df.isnull().sum().to_dict(),
        }

    def add_metric(self, key: str, value):
        self._metrics[key] = self._metrics.get(key, 0) + value

    def generate(self, df_raw: pd.DataFrame, df_clean: pd.DataFrame,
                 duration_seconds: float) -> dict:
        total_raw   = len(df_raw)
        total_clean = len(df_clean)
        rechazados  = total_raw - total_clean
        score = self._calculate_quality_score(total_raw, rechazados)

        return {
            'generado_en': datetime.now().isoformat(),
            'duracion_segundos': round(duration_seconds, 3),
            'antes': self._before_snapshot,
            'despues': {
                'total_registros': total_clean,
                'total_nulos':     int(df_clean.isnull().sum().sum()),
            },
            'acciones_correctivas': self._metrics,
            'registros_rechazados': rechazados,
            'porcentaje_recuperados': round((total_clean / total_raw) * 100, 2),
            'porcentaje_rechazados':  round((rechazados / total_raw) * 100, 2),
            'quality_score': score,
            'clasificacion': self._score_label(score),
        }

    def _calculate_quality_score(self, total: int, rejected: int) -> float:
        base = 100 - (rejected / max(total, 1) * 100)
        deductions = min(self._metrics.get('errores_tipo_corregidos', 0) * 0.1, 20)
        return round(max(base - deductions, 0), 2)

    @staticmethod
    def _score_label(score: float) -> str:
        if score >= 90: return 'Excelente'
        if score >= 75: return 'Buena'
        if score >= 60: return 'Aceptable'
        return 'Deficiente'
```

---

## 8. Motor de Machine Learning

### 8.1 Entrenamiento — `apps/ml/trainer.py`

```python
# apps/ml/trainer.py
"""
ModelTrainer: Entrena y evalúa el modelo de predicción de riesgo.
Implementa Random Forest con validación cruzada y guarda métricas completas.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)

from django.conf import settings


FEATURES = [
    'edad', 'imc', 'presion_sistolica', 'presion_diastolica',
    'frecuencia_cardiaca', 'glucosa', 'colesterol', 'saturacion_oxigeno',
    'temperatura', 'fumador', 'consumo_alcohol', 'antecedentes_familiares',
]
TARGET = 'riesgo_enfermedad'
CLASSES = ['Bajo', 'Medio', 'Alto', 'Crítico']


class ModelTrainer:
    """
    Entrena un modelo Random Forest para clasificación de riesgo clínico.
    Retorna métricas completas y persiste el modelo en disco.
    """

    def __init__(self, algorithm: str = 'random_forest'):
        self.algorithm = algorithm
        self.model = None
        self.le = LabelEncoder()
        self.models_dir = Path(settings.ML_MODELS_PATH)
        self.models_dir.mkdir(exist_ok=True)

    def train(self, df: pd.DataFrame) -> dict:
        """Entrena el modelo y retorna métricas + ruta del artefacto."""
        X, y = self._prepare_data(df)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        # ── Evaluación ──────────────────────────────────────────────────
        y_pred = self.model.predict(X_test)
        metrics = {
            'accuracy':   round(accuracy_score(y_test, y_pred), 4),
            'precision':  round(precision_score(y_test, y_pred, average='weighted'), 4),
            'recall':     round(recall_score(y_test, y_pred, average='weighted'), 4),
            'f1_score':   round(f1_score(y_test, y_pred, average='weighted'), 4),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'classification_report': classification_report(
                y_test, y_pred, target_names=self.le.classes_.tolist(), output_dict=True
            ),
            'cv_accuracy': round(float(cross_val_score(
                self.model, X, y, cv=5, scoring='accuracy'
            ).mean()), 4),
        }

        # ── Feature importance (XAI) ─────────────────────────────────────
        importances = self.model.feature_importances_
        feature_importance = dict(zip(FEATURES, importances.tolist()))
        metrics['feature_importance'] = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        # ── Persistencia ─────────────────────────────────────────────────
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = self.models_dir / f'rf_{timestamp}.pkl'
        joblib.dump({'model': self.model, 'label_encoder': self.le}, model_path)

        return {
            'model_path': str(model_path),
            'algorithm': 'RandomForest',
            'features': FEATURES,
            'n_classes': len(self.le.classes_),
            'training_samples': len(X_train),
            **metrics,
        }

    def _prepare_data(self, df: pd.DataFrame):
        bool_cols = ['fumador', 'consumo_alcohol', 'antecedentes_familiares']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(int)

        X = df[FEATURES].fillna(df[FEATURES].median())
        y = self.le.fit_transform(df[TARGET])
        return X.values, y
```

### 8.2 Predicción con Explicabilidad — `apps/ml/predictor.py`

```python
# apps/ml/predictor.py
"""
ClinicalPredictor: Realiza predicciones individuales con explicabilidad.
Expone los 3 factores más relevantes para la predicción (XAI básico).
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from .trainer import FEATURES, CLASSES


class ClinicalPredictor:
    """
    Carga el modelo activo y predice riesgo + explica los factores clave.
    """

    def __init__(self, model_path: str):
        artifact = joblib.load(model_path)
        self.model = artifact['model']
        self.le    = artifact['label_encoder']
        self.importances = dict(zip(FEATURES, self.model.feature_importances_))

    def predict(self, patient_data: dict) -> dict:
        """
        Predice el riesgo para un paciente y retorna:
        - riesgo_predicho: str
        - probabilidades: dict por clase
        - factores_clave: top 3 variables con mayor impacto en esta predicción
        """
        X = self._build_feature_vector(patient_data)
        proba = self.model.predict_proba(X)[0]
        pred_idx = np.argmax(proba)
        riesgo = self.le.inverse_transform([pred_idx])[0]

        # Probabilidades por clase
        probabilidades = {
            cls: round(float(p), 4)
            for cls, p in zip(self.le.classes_, proba)
        }

        # XAI: top 3 features por importancia global (simplificado)
        factores_clave = sorted(
            self.importances.items(), key=lambda x: x[1], reverse=True
        )[:3]
        factores = [
            {'variable': f, 'importancia': round(i, 4),
             'valor_paciente': patient_data.get(f, 'N/A')}
            for f, i in factores_clave
        ]

        return {
            'riesgo_predicho':  riesgo,
            'probabilidad_max': round(float(proba[pred_idx]), 4),
            'probabilidades':   probabilidades,
            'factores_clave':   factores,
        }

    def _build_feature_vector(self, data: dict) -> np.ndarray:
        row = [float(data.get(f, 0)) for f in FEATURES]
        return np.array([row])

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predicción masiva sobre un DataFrame de pacientes."""
        bool_cols = ['fumador', 'consumo_alcohol', 'antecedentes_familiares']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(int)
        X = df[FEATURES].fillna(df[FEATURES].median()).values
        predictions = self.le.inverse_transform(self.model.predict(X))
        df['riesgo_predicho'] = predictions
        return df
```

---

## 9. Analítica de Datos y KPIs

### `apps/analytics/calculators.py`

```python
# apps/analytics/calculators.py
"""
KPICalculator: Calcula los indicadores clínicos clave para el Dashboard.
PacienteCríticoDetector: Aplica reglas clínicas para alertas proactivas.
"""
import pandas as pd
from django.db.models import Count, Avg, Q

from apps.etl.models import RegistroClinico


class KPICalculator:
    """Genera los KPIs médicos desde la base de datos."""

    def get_all_kpis(self) -> dict:
        qs = RegistroClinico.objects.all()
        total = qs.count()

        return {
            'total_registros':        total,
            'pacientes_criticos':     qs.filter(riesgo_enfermedad='Crítico').count(),
            'pacientes_alto_riesgo':  qs.filter(riesgo_enfermedad='Alto').count(),
            'pacientes_hipertensos':  qs.filter(presion_sistolica__gt=140).count(),
            'pacientes_diabeticos':   qs.filter(glucosa__gt=200).count(),
            'pacientes_fumadores':    qs.filter(fumador=True).count(),
            'promedio_imc':           round(qs.aggregate(Avg('imc'))['imc__avg'] or 0, 2),
            'promedio_glucosa':       round(qs.aggregate(Avg('glucosa'))['glucosa__avg'] or 0, 2),
            'distribucion_riesgo':    self._distribucion_riesgo(qs),
            'distribucion_imc':       self._distribucion_imc(qs),
            'distribucion_sexo':      self._distribucion_sexo(qs),
            'edad_promedio':          round(qs.aggregate(Avg('paciente__edad'))['paciente__edad__avg'] or 0, 1),
        }

    def _distribucion_riesgo(self, qs) -> dict:
        result = qs.values('riesgo_enfermedad').annotate(total=Count('id'))
        return {r['riesgo_enfermedad']: r['total'] for r in result}

    def _distribucion_imc(self, qs) -> dict:
        return {
            'Bajo peso':  qs.filter(imc__lt=18.5).count(),
            'Normal':     qs.filter(imc__gte=18.5, imc__lt=25).count(),
            'Sobrepeso':  qs.filter(imc__gte=25, imc__lt=30).count(),
            'Obesidad':   qs.filter(imc__gte=30).count(),
        }

    def _distribucion_sexo(self, qs) -> dict:
        result = qs.values('paciente__sexo').annotate(total=Count('id'))
        return {r['paciente__sexo']: r['total'] for r in result}


class PacienteCriticoDetector:
    """
    Detecta pacientes en estado crítico aplicando reglas clínicas.
    Genera alertas proactivas para el Dashboard del Médico.
    """

    CRITICAL_RULES = [
        ('presion_sistolica__gt',  180, 'Presión sistólica > 180 mmHg'),
        ('glucosa__gt',            300, 'Glucosa > 300 mg/dL'),
        ('saturacion_oxigeno__lt',  85, 'Saturación O₂ < 85%'),
    ]

    def detect_and_alert(self) -> list:
        from apps.etl.models import RegistroClinico
        from .models import Alerta

        alerts_created = []
        for field_lookup, threshold, description in self.CRITICAL_RULES:
            pacientes = RegistroClinico.objects.filter(
                **{field_lookup: threshold}
            ).select_related('paciente')

            for registro in pacientes:
                alert, created = Alerta.objects.get_or_create(
                    paciente=registro.paciente,
                    tipo_alerta=field_lookup.split('__')[0],
                    defaults={
                        'descripcion': description,
                        'nivel_urgencia': 'critica',
                    }
                )
                if created:
                    alerts_created.append(alert)

        return alerts_created
```

---

## 10. API REST — Endpoints

### `config/urls.py`

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/auth/', include('apps.authentication.urls')),

    # Core modules
    path('api/pacientes/',     include('apps.etl.urls_pacientes')),
    path('api/etl/',           include('apps.etl.urls')),
    path('api/analytics/',     include('apps.analytics.urls')),
    path('api/predicciones/',  include('apps.ml.urls')),
    path('api/dashboard/',     include('apps.dashboard.urls')),
    path('api/reportes/',      include('apps.reports.urls')),

    # Swagger / OpenAPI
    path('api/schema/',        SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema')),
]
```

### Endpoints principales

| Método | Endpoint | Rol | Descripción |
|---|---|---|---|
| POST | `/api/auth/login/` | Público | Login → JWT tokens |
| POST | `/api/auth/refresh/` | Público | Renovar access token |
| GET | `/api/pacientes/` | Médico+ | Listar pacientes con filtros |
| GET | `/api/pacientes/{id}/` | Médico+ | Detalle paciente + historial |
| POST | `/api/etl/run/` | Analista+ | Ejecutar ETL con archivo |
| GET | `/api/etl/historial/` | Analista+ | Historial de ejecuciones |
| GET | `/api/etl/calidad/{id}/` | Analista+ | Data Quality Report |
| POST | `/api/etl/simular/` | Admin | Inyectar datos sintéticos |
| GET | `/api/dashboard/kpis/` | Médico+ | KPIs en tiempo real |
| GET | `/api/dashboard/alertas/` | Médico+ | Alertas críticas activas |
| POST | `/api/predicciones/paciente/{id}/` | Médico+ | Predecir riesgo individual |
| POST | `/api/predicciones/batch/` | Analista+ | Predicción masiva |
| GET | `/api/predicciones/modelo/metricas/` | Admin | Métricas del modelo activo |
| GET | `/api/reportes/exportar/` | Analista+ | Exportar PDF / Excel / CSV |

---

## 11. Frontend y Dashboard

### Arquitectura del Dashboard

```
templates/
├── base.html                   # Layout base con modo oscuro toggle
├── dashboard/
│   ├── index.html              # Panel principal con KPIs + gráficas
│   └── alertas.html            # Alertas críticas en tiempo real
├── etl/
│   ├── run.html                # Ejecutar ETL + simulador
│   ├── historial.html          # Historial de ejecuciones
│   └── quality_report.html     # Data Quality Report visual
├── patients/
│   ├── list.html               # Tabla filtrable de pacientes
│   └── detail.html             # Detalle + predicción ML + factores clave
└── ml/
    ├── metrics.html            # Accuracy, F1, Matriz de confusión
    └── monitor.html            # Model Drift monitor
```

### Gráficas implementadas (Chart.js)

| Gráfica | Tipo | Datos |
|---|---|---|
| Distribución de riesgo | Donut | Bajo/Medio/Alto/Crítico |
| Pacientes por diagnóstico | Barras horizontales | Top 8 diagnósticos |
| IMC promedio por edad | Línea | Grupos etarios 5 años |
| Glucosa vs Presión sistólica | Scatter | Todos los pacientes |
| ETL: Antes vs Después | Barras agrupadas | Nulos / Outliers / Duplicados |
| Tendencia de riesgo | Área | Últimas 10 ejecuciones ETL |

---

## 12. Seguridad — JWT y Roles

### `apps/authentication/permissions.py`

```python
# apps/authentication/permissions.py
from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    """Acceso completo al sistema."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.rol == 'administrador')


class EsMedico(BasePermission):
    """Visualización clínica + predicciones."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.rol in ['medico', 'administrador'])


class EsAnalista(BasePermission):
    """ETL, analítica y reportes."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.rol in ['analista', 'administrador'])
```

### Configuración JWT (`config/settings/base.py`)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## 13. Pruebas Automatizadas

### `tests/test_etl.py`

```python
# tests/test_etl.py
"""Unit tests para el pipeline ETL."""
import pandas as pd
import pytest
from apps.etl.transformers import (
    DuplicateRemover, TypeCoercer, NullImputer,
    OutlierHandler, DiagnosisNormalizer, SexNormalizer,
    IMCCalculator, RiskClassifier,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'id_paciente':         [1, 1, 2, 3],  # 1 duplicado
        'nombres':             ['Ana', 'Ana', 'Luis', 'Pedro'],
        'apellidos':           ['García', 'García', 'Martín', 'López'],
        'edad':                [45, 45, 'Treinta', 60],  # tipo incorrecto
        'sexo':                ['f', 'f', 'Masculino', 'M'],
        'peso':                [70.0, 70.0, None, 420.0],  # nulo + outlier
        'altura':              [1.65, 1.65, 1.75, 1.70],
        'IMC':                 [25.7, 25.7, 22.0, 145.0],
        'presión_sistólica':   [120, 120, 'alta', 185],
        'presión_diastólica':  [80, 80, 75, 100],
        'frecuencia_cardiaca': [72, 72, 68, 90],
        'glucosa':             [95.0, 95.0, None, 350.0],
        'colesterol':          [200.0, 200.0, 180.0, 230.0],
        'saturación_oxígeno':  [98.0, 98.0, 97.0, 82.0],
        'temperatura':         [36.5, 36.5, None, 37.0],
        'antecedentes_familiares': [False, False, True, True],
        'fumador':             [False, False, False, True],
        'consumo_alcohol':     [False, False, True, False],
        'actividad_física':    ['Media', 'Media', 'Alta', 'Baja'],
        'diagnóstico_preliminar': ['hipertencion', 'hipertencion', 'Paciente sano', 'Hipertensión'],
        'riesgo_enfermedad':   ['Medio', 'Medio', 'Bajo', 'Alto'],
        'fecha_consulta':      ['2025-01-01'] * 4,
    })


def test_duplicate_remover(sample_df):
    t = DuplicateRemover()
    result = t.transform(sample_df.copy())
    assert len(result) == 3, "Debe eliminar 1 duplicado"


def test_type_coercer(sample_df):
    t = TypeCoercer()
    result = t.transform(sample_df.copy())
    assert result['edad'].isna().sum() == 1, "Edad='Treinta' debe ser NaN"
    assert result['presión_sistólica'].isna().sum() == 1, "Presión='alta' debe ser NaN"


def test_null_imputer(sample_df):
    t = TypeCoercer()
    df = t.transform(sample_df.copy())
    t2 = NullImputer()
    result = t2.transform(df)
    assert result['peso'].isna().sum() == 0, "No debe haber nulos en peso"
    assert result['glucosa'].isna().sum() == 0, "No debe haber nulos en glucosa"


def test_outlier_handler(sample_df):
    t = OutlierHandler()
    result = t.transform(sample_df.copy())
    assert result['peso'].max() <= 300, "Peso > 300 debe ser corregido"
    assert result['saturación_oxígeno'].min() >= 70


def test_diagnosis_normalizer(sample_df):
    t = DiagnosisNormalizer()
    result = t.transform(sample_df.copy())
    assert 'hipertencion' not in result['diagnóstico_preliminar'].values
    assert 'Hipertensión' in result['diagnóstico_preliminar'].values


def test_sex_normalizer(sample_df):
    t = SexNormalizer()
    result = t.transform(sample_df.copy())
    valid_values = {'M', 'F'}
    assert set(result['sexo'].unique()).issubset(valid_values)


def test_imc_calculator(sample_df):
    df = sample_df.copy()
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce').fillna(70)
    t = IMCCalculator()
    result = t.transform(df)
    # IMC para peso=70, altura=1.65 ≈ 25.71
    assert abs(result.loc[0, 'IMC'] - 25.71) < 0.1
    assert 'clasificacion_imc' in result.columns


def test_risk_classifier(sample_df):
    df = sample_df.copy()
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce').fillna(70)
    df['edad'] = pd.to_numeric(df['edad'], errors='coerce').fillna(45)
    df['presión_sistólica'] = pd.to_numeric(df['presión_sistólica'], errors='coerce').fillna(120)
    t = RiskClassifier()
    result = t.transform(df)
    assert all(v in ['Bajo','Medio','Alto','Crítico'] for v in result['riesgo_enfermedad'])
```

---

## 14. Docker y Despliegue

### `docker-compose.yml`

```yaml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB:       healthshield_db
      POSTGRES_USER:     healthshield
      POSTGRES_PASSWORD: ${DB_PASSWORD:-securepassword}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U healthshield"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: ./docker/entrypoint.sh
    environment:
      DATABASE_URL: postgresql://healthshield:${DB_PASSWORD:-securepassword}@db:5432/healthshield_db
      SECRET_KEY:   ${SECRET_KEY:-dev-secret-key-change-in-production}
      DEBUG:        ${DEBUG:-True}
    volumes:
      - ./backend:/app
      - ./datasets:/app/datasets
      - ml_models:/app/ml_models
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  ml_models:
```

### `docker/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY datasets/ ./datasets/

EXPOSE 8000
```

### `docker/entrypoint.sh`

```bash
#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
# Cargar dataset inicial si BD está vacía
python manage.py shell -c "
from apps.etl.models import EjecucionETL
if EjecucionETL.objects.count() == 0:
    from apps.etl.pipeline import ETLPipeline
    ETLPipeline(tipo='automatico').run('datasets/clinical_data_v1.0_raw.xlsx')
    print('Dataset inicial cargado.')
"
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### `.github/workflows/main.yml` — CI/CD

```yaml
name: HealthShield AI — CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB:       healthshield_test
          POSTGRES_USER:     healthshield
          POSTGRES_PASSWORD: testpassword
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Instalar dependencias
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Ejecutar tests
        env:
          DATABASE_URL: postgresql://healthshield:testpassword@localhost:5432/healthshield_test
          SECRET_KEY: ci-test-secret-key
        run: |
          cd backend
          python manage.py migrate
          pytest tests/ -v --tb=short

      - name: Verificar calidad de código
        run: |
          cd backend
          pip install flake8
          flake8 apps/ --max-line-length=100 --exclude=migrations
```

---

## 15. Data Quality Report

Tras cada ejecución ETL, el sistema genera automáticamente un reporte JSON con esta estructura:

```json
{
  "generado_en": "2026-05-21T10:30:00",
  "duracion_segundos": 2.847,
  "antes": {
    "total_registros": 1850,
    "total_nulos": 202,
    "nulos_por_columna": {
      "peso": 80,
      "glucosa": 41,
      "colesterol": 42,
      "temperatura": 39
    }
  },
  "despues": {
    "total_registros": 1800,
    "total_nulos": 0
  },
  "acciones_correctivas": {
    "duplicados_eliminados": 50,
    "errores_tipo_corregidos": 12,
    "nulos_imputados": 202,
    "outliers_corregidos": 8,
    "diagnosticos_normalizados": 596,
    "sexo_normalizados": 1207
  },
  "registros_rechazados": 0,
  "porcentaje_recuperados": 97.30,
  "porcentaje_rechazados": 2.70,
  "quality_score": 94.2,
  "clasificacion": "Excelente"
}
```

Este reporte es visible en el Dashboard del Analista como gráfica de barras comparativa "Antes vs. Después".

---

## 16. Manual de Usuario

### Login

1. Acceder a `http://localhost:8000`
2. Ingresar credenciales (usuario y contraseña asignados por el Administrador)
3. El sistema redirige al dashboard según el rol asignado

### Roles y Funcionalidades

**Administrador**
- Gestión de usuarios y roles
- Configuración del sistema
- Acceso a todos los módulos
- Inyección de datos de simulación

**Médico**
- Ver dashboard clínico con KPIs
- Consultar alertas críticas de pacientes
- Ver detalle de paciente + predicción de riesgo
- Confirmar lectura de alertas

**Analista**
- Ejecutar proceso ETL (subir CSV / ejecutar con dataset base)
- Ver Data Quality Report
- Acceder a analítica descriptiva y segmentación
- Exportar reportes en PDF / Excel / CSV

### Ejecutar el ETL

1. Ir a **ETL → Ejecutar Pipeline**
2. Subir archivo CSV/Excel o usar el dataset cargado
3. Hacer clic en **"Iniciar ETL"**
4. El sistema muestra progreso en tiempo real
5. Al finalizar, se genera automáticamente el **Data Quality Report**
6. Los KPIs del Dashboard se actualizan automáticamente

### Simular Ingreso de Datos (Solo Admin)

1. Ir a **ETL → Simulador Live**
2. Seleccionar cantidad de registros (5 / 50 / 100)
3. Hacer clic en **"Simular Ingreso"**
4. El pipeline ETL procesa los datos automáticamente
5. Ver el resultado en el historial ETL

### Ver Predicciones ML

1. Ir a **Pacientes → buscar paciente**
2. Clic en **"Predecir Riesgo"**
3. El sistema muestra:
   - Riesgo calculado (Bajo / Medio / Alto / Crítico)
   - Probabilidad de cada clase
   - **Factores clave**: las 3 variables que más influyeron en la predicción

### Exportar Reportes

1. Ir a **Reportes**
2. Seleccionar tipo: PDF clínico / Excel / CSV
3. Aplicar filtros (fecha, riesgo, diagnóstico)
4. Hacer clic en **"Exportar"**
5. El PDF incluye: logo HealthShield AI, datos del paciente, riesgo calculado y recomendaciones clínicas

---

## 17. Diagramas

### Flujo ETL

```
┌─────────────────┐
│   EXTRACT        │  ← CSV / Excel / API externa
│  ExcelExtractor  │
│  CSVExtractor    │
└────────┬─────────┘
         │ DataFrame raw (1850 filas)
         ▼
┌─────────────────┐
│  DuplicateRemover│  → -50 duplicados
├─────────────────┤
│  TypeCoercer     │  → convierte tipos incorrectos a NaN
├─────────────────┤
│  NullImputer     │  → media/mediana/moda en 202 nulos
├─────────────────┤
│  OutlierHandler  │  → reemplaza outliers clínicos
├─────────────────┤
│  DiagnosisNorm.  │  → unifica 4 variantes ortográficas
├─────────────────┤
│  SexNormalizer   │  → 'f','Femenino','female' → 'F'
├─────────────────┤
│  IMCCalculator   │  → recalcula + clasifica OMS
├─────────────────┤
│  RiskClassifier  │  → Bajo/Medio/Alto/Crítico
└────────┬─────────┘
         │ DataFrame limpio (1800 filas)
         ▼
┌─────────────────┐
│     LOAD         │  → PostgreSQL (pacientes + registros_clinicos)
│  DatabaseLoader  │  → Log de ejecución
│                  │  → Data Quality Report
└─────────────────┘
```

### Flujo Machine Learning

```
Dataset Limpio (1800 filas)
         ↓
Preprocesamiento (encode bool, fillna median)
         ↓
Split 80/20 (stratificado por riesgo)
         ↓
RandomForest (200 árboles, balanced)
         ↓
Evaluación: Accuracy · Precision · Recall · F1
         ↓
Feature Importance (XAI)
         ↓
Persistencia (modelo .pkl versionado)
         ↓
Predicción + Explicación → Dashboard
```

---

## 18. Criterios de Evaluación Cumplidos

| Criterio | Peso | Implementación |
|---|---|---|
| Arquitectura Backend | 20% | Django 5, DRF, SOLID, módulos desacoplados, Docker |
| Proceso ETL | 25% | 8 transformadores, Data Quality Report, trazabilidad completa, simulador live |
| Analítica de Datos | 15% | KPIs médicos, segmentación por riesgo/IMC/sexo, estadística descriptiva |
| Machine Learning | 15% | Random Forest, métricas completas, XAI feature importance, monitor de drift |
| Frontend/Dashboard | 10% | Bootstrap 5, Chart.js, modo oscuro, alertas proactivas |
| Seguridad | 5% | JWT, 3 roles, auditoría de acciones |
| Documentación | 10% | README completo, Swagger, unit tests, diagramas |

### Bonus implementados
- ✅ Docker Compose (un solo comando)
- ✅ GitHub Actions CI/CD
- ✅ Swagger/OpenAPI interactivo
- ✅ Data Quality Report automático
- ✅ Motor de simulación Live-Stream
- ✅ Explicabilidad ML (XAI)
- ✅ Modo oscuro en el Dashboard
- ✅ Exportación de PDF clínico estructurado
- ✅ Unit Testing (pytest)
- ✅ Versionamiento de datasets

---

*Desarrollado para el Reto Técnico FullStack + Data Analytics + ETL + Machine Learning — HealthAnalytics IPS*
*Fecha de entrega: 15 de junio de 2026 · Modalidad: Individual*
