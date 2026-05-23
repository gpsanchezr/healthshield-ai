# 📊 HealthShield AI - Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                │
│  ┌──────────────┬──────────────┬──────────────┬──────────────────┐      │
│  │  Dashboard   │  Pacientes   │ ML Monitor   │  Reportes      │      │
│  │  Bootstrap5  │  CRUD UI     │  XAI Viz     │ PDF/Excel      │      │
│  │  Chart.js    │ Real-time    │ Feature      │ Export         │      │
│  └──────────────┴──────────────┴──────────────┴──────────────────┘      │
│                    ↑                                                    │
│              REST APIs (Django)                                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Django Backend                               │   │
│  │  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │   │
│  │  │  Auth Module │  ETL Engine  │  ML Module   │ Analytics    │ │   │
│  │  │ JWT Auth     │ Transform    │ Trainer      │ KPIs         │ │   │
│  │  │ Roles/Perms  │ Quality      │ Predictor    │ Alerts       │ │   │
│  │  │              │ Report       │ XAI          │ Segmentación │ │   │
│  │  └──────────────┴──────────────┴──────────────┴──────────────┘ │   │
│  │                                                                 │   │
│  │  REST Framework | drf-spectacular (Swagger) | DRF Routers     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          ↑                                             │
│                   PostgreSQL / MySQL                                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       DATA & PROCESSING LAYER                          │
│  ┌──────────────┬──────────────┬──────────────┬──────────────────┐    │
│  │  Extractors  │ Transformers │   Loaders    │   Quality        │    │
│  │ CSV/Excel    │ Cleaners     │ Database     │   Reporter       │    │
│  │              │ Normalizers  │ Bulk Ops     │   Auditor        │    │
│  │              │ Validators   │              │                  │    │
│  └──────────────┴──────────────┴──────────────┴──────────────────┘    │
│                                                                         │
│  Pandas | NumPy | Scikit-Learn | Random Forest | Feature Importance   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                               │
│  Docker | Docker-Compose | PostgreSQL 16 | Redis (optional) | Celery │
└─────────────────────────────────────────────────────────────────────────┘
```

## Module Architecture

### 1. **Authentication Module** (`apps.authentication`)
- **Purpose**: User management, JWT authentication, role-based access control
- **Components**:
  - `models.UsuarioClinico` - Custom user model with role field
  - `permissions.py` - Role-based permission classes (EsAdministrador, EsMedico, EsAnalista)
  - `views.LoginView, RegisterView, RefreshView` - JWT endpoints
  - `serializers.py` - User serialization with validation

### 2. **ETL Module** (`apps.etl`)
- **Purpose**: Extract, Transform, Load clinical data with quality assurance
- **Key Files**:
  - `pipeline.py` - Orchestrator (Extract → Transform → Load → Quality Report)
  - `extractors.py` - CSVExtractor, ExcelExtractor
  - `transformers.py` - 8 transformers in sequence:
    1. DuplicateRemover - Eliminates duplicate patient records
    2. TypeCoercer - Converts edad, presion to correct types
    3. NullImputer - Handles missing values (media/moda)
    4. OutlierHandler - Removes physiologically impossible values
    5. DiagnosisNormalizer - Fixes diagnosis spelling
    6. SexNormalizer - Standardizes gender values
    7. IMCCalculator - peso / altura²
    8. RiskClassifier - Assigns risk level (Bajo/Medio/Alto/Crítico)
  - `loaders.py` - DatabaseLoader with atomic transactions
  - `quality.py` - DataQualityReport (0-100 score)
  - `simulation.py` - DataSimulator for live injection testing

### 3. **Machine Learning Module** (`apps.ml`)
- **Purpose**: Train models, make predictions, explain decisions
- **Key Files**:
  - `trainer.py` - ModelTrainer (Random Forest, Logistic Regression, Decision Tree)
  - `predictor.py` - Predictor with feature importance (XAI)
  - `models.py` - ModeloML, Prediccion storage
  - **Workflow**:
    ```
    Training Data (RegistroClinico) 
      ↓
    Preprocessing (StandardScaler)
      ↓
    Train-Test Split (80-20)
      ↓
    Model.fit()
      ↓
    Evaluate (Accuracy, Precision, Recall, F1, ROC-AUC)
      ↓
    Save Model (joblib)
      ↓
    Dashboard Display
    ```

### 4. **Analytics Module** (`apps.analytics`)
- **Purpose**: Clinical metrics, KPIs, alert generation
- **Metrics**:
  - Descriptive stats (mean, median, std dev)
  - Medical KPIs (critical patients, hypertensive, diabetic, smokers)
  - Risk distribution
  - Age-group segmentation
- **Alerts**: Auto-generated for systolic > 180, glucose > 300, saturation < 85%

### 5. **Dashboard Module** (`apps.dashboard`)
- **Purpose**: Real-time clinical visualization
- **Endpoints**:
  - `/api/dashboard/` - Returns JSON for 6 Chart.js graphs
  - `/dashboard/` - Renders HTML template
- **Visualizations**:
  - KPI Summary (4 metric cards)
  - IMC by Age Group (Bar chart)
  - Glucose vs Systolic Pressure (Scatter)
  - Risk Distribution (Pie chart)
  - ETL Trend (Line chart)
  - Alerts by Urgency (Bar chart)

### 6. **Reports Module** (`apps.reports`)
- **Purpose**: Export clinical data as PDF/Excel/CSV
- **Features**:
  - Dynamic report generation
  - Data Quality Report (post-ETL)
  - ML Metrics Report
  - Patient Risk Report with recommendations

## Data Flow: End-to-End

```
Raw Excel (1800 records with errors)
    ↓
[EXTRACT] - ExcelExtractor reads file
    ↓
DataFrame with 1800 rows
    ↓
[TRANSFORM] - 8 Transformers in pipeline
  - Remove 50 duplicates
  - Fix 6 gender variants (M/F/Masculino/Femenino/m/f)
  - Fix 4 diagnosis spellings
  - Handle 202 null values
  - Coerce 30 string ages to integers
  - Catch 15 physiologic outliers
  - Calculate IMC
  - Classify risk (Bajo/Medio/Alto/Crítico)
    ↓
~1750 clean records
    ↓
[LOAD] - DatabaseLoader.load()
  - Create/update Paciente records
  - Insert RegistroClinico records
  - Log all operations
    ↓
Pacientes (1200 unique) + RegistroClinico (1750 records) in DB
    ↓
[QUALITY REPORT] - Metrics:
  - Input: 1800, Output: 1750, Rejected: 50
  - Duplicates removed: 50
  - Nulls imputed: 202
  - Quality score: 97.2%
    ↓
[ML TRAINING] - Random Forest on 1750 records
  - Features: IMC, age, glucose, etc.
  - Train: 1400 (80%), Test: 350 (20%)
  - Accuracy: 0.94
  - Store model + metrics in BD
    ↓
[PREDICTIONS] - For new/existing patients
  - Input: Patient vitals
  - Output: Risk level (Bajo/Medio/Alto/Crítico) + probability + key factors
    ↓
[DASHBOARD] - Real-time visualization
  - KPIs, graphs, alerts
  - Export reports (PDF/Excel)
```

## Security Model

```
Request
  ↓
JWT Token Validation (middleware)
  ↓
User extracted from token
  ↓
Check user.rol against endpoint permission_classes:
  - EsAdministrador: All endpoints
  - EsMedico: Clinical viewing (pacientes, registros, predicciones, alertas)
  - EsAnalista: ETL, analytics, reports
  ↓
If authorized: Execute view
If not: HTTP 403 Forbidden
```

## Performance Considerations

- **Database**: PostgreSQL with strategic indexes on:
  - `registros_clinicos(paciente_id, fecha_consulta DESC)`
  - `alertas(paciente_id, fecha_alerta DESC)`
  - `predicciones(modelo_id, fecha DESC)`
- **Caching**: Use Django ORM select_related for FK traversal
- **Async**: Celery + Redis for long-running ETL/ML jobs (optional)
- **Pagination**: 50 records default in ListViewSets
