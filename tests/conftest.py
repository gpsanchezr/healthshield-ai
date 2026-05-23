"""
Pytest configuration and fixtures para HealthShield AI.
"""
import os
import sys
from pathlib import Path

import django
import pytest

# Agregar backend al path
BACKEND_DIR = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

pytestmark = pytest.mark.django_db


def pytest_configure():
    """Configura Django antes de ejecutar tests."""
    django.setup()


@pytest.fixture
def sample_dataframe():
    """DataFrame de prueba con estructura clínica."""
    import pandas as pd
    import numpy as np

    return pd.DataFrame({
        'id_paciente': [1, 2, 3, 4, 5],
        'nombres': ['Ana', 'Luis', 'María', 'Carlos', 'Sofía'],
        'apellidos': ['García', 'Martínez', 'López', 'Rodríguez', 'Pérez'],
        'edad': [25, 45, 35, 60, 28],
        'sexo': ['F', 'M', 'F', 'M', 'F'],
        'peso': [65.0, 80.5, 55.0, 90.0, 60.0],
        'altura': [1.65, 1.75, 1.60, 1.80, 1.62],
        'IMC': [23.88, 26.29, 21.48, 27.77, 22.86],
        'presión_sistólica': [120, 150, 110, 170, 115],
        'presión_diastólica': [80, 95, 70, 105, 75],
        'frecuencia_cardiaca': [72, 85, 68, 90, 70],
        'glucosa': [100.0, 250.0, 90.0, 310.0, 95.0],
        'colesterol': [190.0, 240.0, 180.0, 300.0, 170.0],
        'saturación_oxígeno': [98.0, 95.0, 99.0, 82.0, 97.0],
        'temperatura': [36.5, 37.2, 36.8, 38.5, 36.6],
        'antecedentes_familiares': [False, True, False, True, False],
        'fumador': [False, True, False, True, False],
        'consumo_alcohol': [True, False, True, False, False],
        'diagnóstico_preliminar': ['Paciente sano', 'Hipertensión', 'Obesidad', 'Diabetes Tipo 2', 'Paciente sano'],
        'riesgo_enfermedad': ['Bajo', 'Alto', 'Medio', 'Crítico', 'Bajo'],
        'fecha_consulta': ['2026-01-15', '2026-02-20', '2026-03-10', '2026-04-05', '2026-05-01'],
    })


@pytest.fixture
def df_with_errors(sample_dataframe):
    """DataFrame con errores intencionales para probar transformadores."""
    import pandas as pd
    import numpy as np

    df = sample_dataframe.copy()
    # Inject errors
    df.at[0, 'peso'] = None                          # nulo
    df.at[1, 'edad'] = 'Treinta'                     # tipo incorrecto
    df.at[2, 'presión_sistólica'] = 'alta'           # tipo incorrecto
    df.loc[4] = df.loc[3].copy()                     # duplicado
    df.at[3, 'peso'] = 450.0                         # outlier extremo
    df.at[1, 'diagnóstico_preliminar'] = 'hipertencion'  # error ortográfico
    return df


@pytest.fixture
def df_minimal():
    """DataFrame mínimo con columnas requeridas para entrenamiento ML."""
    import pandas as pd

    return pd.DataFrame({
        'imc': [23.5, 28.1, 19.2, 31.0, 24.8],
        'presion_sistolica': [115, 155, 108, 185, 118],
        'presion_diastolica': [75, 98, 68, 110, 78],
        'frecuencia_cardiaca': [70, 88, 65, 95, 72],
        'glucosa': [95.0, 260.0, 88.0, 320.0, 92.0],
        'colesterol': [185.0, 250.0, 175.0, 310.0, 180.0],
        'saturacion_oxigeno': [98.0, 94.0, 99.0, 80.0, 97.0],
        'temperatura': [36.5, 37.8, 36.3, 38.9, 36.7],
        'fumador': [0, 1, 0, 1, 0],
        'consumo_alcohol': [0, 1, 0, 0, 1],
        'antecedentes_familiares': [0, 1, 0, 1, 0],
        'edad': [30, 55, 25, 65, 35],
        'riesgo_enfermedad': ['Bajo', 'Alto', 'Bajo', 'Crítico', 'Medio'],
    })