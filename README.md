# HealthShield AI

## Visión

Sistema avanzado de gestión y análisis clínico basado en Django, diseñado para el procesamiento y validación de registros de pacientes con un enfoque en integridad de datos.

## Manual de Usuario (Operaciones)

### 1. Acceso al Panel

- Ingresar a la interfaz administrativa en `/admin/`.
- Iniciar sesión con credenciales de administrador para acceder a la gestión centralizada de pacientes y registros clínicos.

### 2. Gestión de Datos (ETL)

- El sistema permite la ingesta de archivos CSV mediante el pipeline ETL integrado.
- Los registros se procesan a través de una tubería de datos que valida, limpia y transforma la información antes de almacenarla.
- El usuario puede cargar archivos CSV con datos clínicos y el sistema aplicará normalización, eliminación de duplicados e imputación de datos faltantes.

### 3. Interpretación de Indicadores

- El sistema visualiza métricas clave como:
  - **IMC** (Índice de Masa Corporal).
  - **Niveles de riesgo** de pacientes.
  - **Saturación de oxígeno**.
- Estas métricas permiten identificar condiciones clínicas relevantes y apoyar la toma de decisiones.

## Guía Técnica para Desarrolladores

### Stack Tecnológico

- **Django 5.0.6**
- **Python**
- **Pipeline ETL integrado** basado en Pandas y módulos personalizados.
- **Django REST Framework** para APIs.
- **drf-spectacular** para documentación OpenAPI.

### Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/gpsanchezr/healthshield-ai.git
   cd healthshield-ai
   ```
2. Crear y activar el entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Configurar variables de entorno y base de datos según el entorno local.
5. Ejecutar migraciones:
   ```bash
   cd backend
   python manage.py migrate
   ```

### Ejecución

- Levantar el servidor Django:
  ```bash
  python backend/manage.py runserver
  ```
- Ejecutar el ETL con un archivo CSV específico:
  ```bash
  python backend/manage.py run_etl --file backend/data/datos.csv
  ```

## Resultados Alcanzados

### Calidad de Datos

- Se alcanzó un **Quality Score de 95.1%**, lo que indica un nivel alto de validación y consistencia en los registros procesados.

### Logros

- Se procesaron **1,800 registros clínicos** exitosamente.
- Se eliminaron duplicados y se imputaron valores nulos.
- Se implementó la normalización de columnas y la transformación de datos mediante módulos especializados.

## Estado del Proyecto

- Backend operativo y validado.
- Proyecto en fase final de preparación para despliegue en Vercel.

## Nota importante

El sistema requiere una estructura de datos específica en el archivo CSV para asegurar la integridad de la base de datos. Los nombres de columna deben coincidir con el esquema esperado por el pipeline ETL y los valores deben estar en formatos compatibles con los modelos de datos clínicos.
