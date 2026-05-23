# 🔌 HealthShield AI - REST API Reference

## Base URL
```
http://localhost:8000/api/
```

## Authentication
All endpoints (except `/auth/login/` and `/auth/refresh/`) require a JWT token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### `POST /auth/login/`
Login and obtain JWT tokens.

**Request:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### `POST /auth/refresh/`
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response:**
```json
{
  "access": "<new_access_token>"
}
```

### `POST /auth/register/` ⚠️ Admin Only
Register a new user (requires Administrador role).

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123",
  "rol": "medico"
}
```

**Response:**
```json
{
  "status": "created"
}
```

---

## 2. ETL Endpoints

### `GET /etl/pacientes/`
List all patients with pagination.

**Query Params:**
- `page` (int): Page number (default: 1)
- `search` (str): Search by name
- `ordering` (str): Order by field (e.g., `-fecha_registro`)

**Response:**
```json
{
  "count": 1250,
  "next": "http://localhost:8000/api/etl/pacientes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "nombres": "Juan",
      "apellidos": "Pérez",
      "edad": 45,
      "sexo": "M",
      "fecha_registro": "2026-05-22T10:30:00Z",
      "total_registros": 3,
      "registros": [
        {
          "id": 1,
          "fecha_consulta": "2026-05-22T10:30:00Z",
          "peso": 78.5,
          "altura": 1.75,
          "imc": 25.6,
          "presion_sistolica": 130,
          "presion_diastolica": 85,
          "glucosa": 110.5,
          "frecuencia_cardiaca": 72,
          "riesgo_enfermedad": "Medio"
        }
      ]
    }
  ]
}
```

### `POST /etl/run/` 🔐 Analista
Execute ETL pipeline manually.

**Request:**
```json
{
  "archivo": "<binary file>"
}
```

**Response:**
```json
{
  "id": 125,
  "estado": "completado",
  "registros_extraidos": 1800,
  "registros_procesados": 1750,
  "registros_rechazados": 50,
  "duplicados_eliminados": 45,
  "nulos_imputados": 202,
  "duracion_segundos": 12.345,
  "calidad_score": 97.22,
  "archivo_fuente": "clinical_data_v1.0.xlsx"
}
```

### `POST /etl/simular/` 🔐 Analista
Simulate data injection (live testing).

**Request:**
```json
{
  "count": 50
}
```

**Response:**
```json
{
  "message": "Simulation completed",
  "registros_generados": 50,
  "registros_procesados": 48,
  "calidad_score": 96.0
}
```

### `GET /etl/historial/`
View ETL execution history.

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 125,
      "fecha_inicio": "2026-05-22T10:30:00Z",
      "fecha_fin": "2026-05-22T10:32:12Z",
      "duracion_segundos": 12.345,
      "registros_procesados": 1750,
      "calidad_score": 97.22,
      "estado": "completado",
      "tipo": "manual"
    }
  ]
}
```

### `GET /etl/calidad/<ejecucion_id>/`
Get detailed quality report for an ETL execution.

**Response:**
```json
{
  "ejecucion_id": 125,
  "quality_score": 97.22,
  "metricas": {
    "total_registros_entrada": 1800,
    "total_registros_salida": 1750,
    "registros_rechazados": 50,
    "duplicados_eliminados": 45,
    "nulos_imputados": 202,
    "outliers_removidos": 15
  },
  "errores": {
    "tipos_incorrectos": 30,
    "valores_fuera_rango": 15,
    "duplicados": 50
  }
}
```

---

## 3. Machine Learning Endpoints

### `GET /ml/modelos/` 
List trained ML models.

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "nombre": "RandomForest_v1.0",
      "algoritmo": "random_forest",
      "version": "1.0",
      "accuracy": 0.9412,
      "precision_score": 0.9356,
      "recall": 0.9284,
      "f1_score": 0.9320,
      "roc_auc": 0.9756,
      "activo": true,
      "entrenado_en": "2026-05-22T10:00:00Z"
    }
  ]
}
```

### `GET /ml/modelos/active/`
Get the currently active model.

**Response:** Same as single model object above.

### `POST /ml/predicciones/`
Make a prediction for a patient.

**Request:**
```json
{
  "paciente_id": 1,
  "modelo_id": 1
}
```

**Response:**
```json
{
  "id": 501,
  "paciente_id": 1,
  "modelo_id": 1,
  "riesgo_predicho": "Medio",
  "probabilidad": 0.67,
  "confianza": 0.89,
  "factores_clave": {
    "IMC": 0.28,
    "Glucosa": 0.24,
    "Presión_Sistólica": 0.18,
    "Edad": 0.15,
    "Frecuencia_Cardíaca": 0.10,
    "Colesterol": 0.05
  },
  "fecha": "2026-05-22T11:00:00Z"
}
```

### `GET /ml/predicciones/?paciente_id=1`
Get prediction history for a patient.

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 501,
      "riesgo_predicho": "Medio",
      "probabilidad": 0.67,
      "fecha": "2026-05-22T11:00:00Z"
    }
  ]
}
```

---

## 4. Analytics Endpoints

### `GET /analytics/alertas/`
Get active clinical alerts.

**Query Params:**
- `nivel_urgencia` (str): Filter by urgency (bajo/medio/alto/crítico)
- `resuelta` (bool): Filter by resolution status

**Response:**
```json
{
  "count": 42,
  "results": [
    {
      "id": 1,
      "paciente": {
        "id": 5,
        "nombres": "María",
        "apellidos": "García"
      },
      "tipo_alerta": "Hipertensión Crítica",
      "nivel_urgencia": "crítico",
      "descripcion": "Presión sistólica > 180",
      "fecha_alerta": "2026-05-22T09:15:00Z",
      "resuelta": false
    }
  ]
}
```

### `PATCH /analytics/alertas/<id>/`
Mark alert as resolved or change status.

**Request:**
```json
{
  "resuelta": true
}
```

---

## 5. Dashboard Endpoints

### `GET /dashboard/`
Get clinical summary data for dashboard visualization.

**Response:**
```json
{
  "kpi_resumen": {
    "pacientes_en_riesgo": 285,
    "promedio_glucosa": 118.5,
    "total_etl_procesado": 1750,
    "alertas_criticas": 23
  },
  "grafica_imc_por_grupo_etario": {
    "labels": ["10-19", "20-29", "30-39", "40-49", "50-59", "60+"],
    "datasets": [
      {
        "label": "IMC Promedio",
        "data": [20.8, 23.2, 24.6, 25.9, 26.7, 27.4]
      }
    ]
  },
  "grafica_glucosa_vs_presion": {
    "labels": ["Paciente 1", "Paciente 2", ...],
    "datasets": [
      {
        "label": "Glucosa (mg/dL)",
        "data": [100, 150, 200, ...]
      },
      {
        "label": "Presión Sistólica (mmHg)",
        "data": [120, 140, 160, ...]
      }
    ]
  }
}
```

---

## 6. Reports Endpoints

### `POST /reports/generate/`
Generate a clinical report.

**Request:**
```json
{
  "type": "clinical_summary",
  "format": "pdf"
}
```

**Response:** Binary PDF file download

**Supported types:**
- `clinical_summary` - Overall clinical snapshot
- `etl_quality` - Data quality metrics
- `ml_metrics` - Model performance report
- `patient_risk` - High-risk patient list

**Supported formats:**
- `pdf` - PDF document
- `excel` - Excel workbook
- `csv` - Comma-separated values

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid input",
  "detail": "Field 'edad' must be an integer between 0 and 120"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Unexpected error processing request"
}
```

---

## Rate Limiting & Pagination

- **Default page size**: 50 records
- **Max page size**: 500 records
- **Rate limit**: 1000 requests/hour per IP

---

## Swagger/OpenAPI

Interactive API documentation available at:
- `http://localhost:8000/api/schema/swagger-ui/`
- `http://localhost:8000/api/schema/redoc/`
