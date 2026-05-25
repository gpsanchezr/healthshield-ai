# apps/etl/simulation.py
"""
DataSimulator: Motor de inyección de datos sintéticos para validar
la resiliencia del pipeline ETL en tiempo real.

Genera registros con errores intencionales (igual que el dataset original)
para que el pipeline ETL tenga algo que limpiar y demostrar su robustez.

Uso:
    simulator = DataSimulator()
    df = simulator.generate(n=50)
    pipeline = ETLPipeline(usuario=request.user, tipo='simulacion')
    result = pipeline.run_dataframe(df)
"""
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


NOMBRES = [
    'Ana', 'Luis', 'María', 'Carlos', 'Patricia', 'Sofía', 'Jorge',
    'Valentina', 'Miguel', 'Daniela', 'Andrés', 'Camila', 'Diego',
    'Isabella', 'Sebastián', 'Alejandra', 'Felipe', 'Natalia',
]
APELLIDOS = [
    'García', 'Martínez', 'López', 'Rodríguez', 'González', 'Pérez',
    'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Morales',
    'Jiménez', 'Herrera', 'Vargas', 'Castro', 'Ramos', 'Mendoza',
]
DIAGNOSTICOS = [
    'Hipertensión', 'hipertencion', 'hipertensíon',  # errores intencionales
    'Diabetes Tipo 2', 'Prehipertensión', 'Riesgo cardiovascular',
    'Cardiopatía', 'Obesidad', 'Paciente sano',
]
SEXO_VARIANTS = ['M', 'm', 'Masculino', 'F', 'f', 'Femenino']   # errores intencionales
ACTIVIDAD = ['Sedentario', 'Baja', 'Media', 'Alta']
RIESGO = ['Bajo', 'Medio', 'Alto', 'Crítico']


class DataSimulator:
    """
    Genera DataFrames con la misma estructura del dataset clínico,
    incluyendo errores intencionales (nulos, tipos incorrectos, outliers,
    errores ortográficos) para probar el pipeline ETL.
    """

    def __init__(self, seed: int = None, error_rate: float = 0.08):
        """
        Args:
            seed: Semilla para reproducibilidad (None = aleatorio)
            error_rate: Proporción de errores a inyectar por columna (0–1)
        """
        # Usar RNGs locales para evitar depender del estado global y
        # garantizar reproducibilidad por instancia.
        self._rand = random.Random(seed)
        self._np_rand = np.random.default_rng(seed)
        self.error_rate = error_rate
        self._id_counter = 9000  # IDs altos para no colisionar con el dataset base

    def generate(self, n: int = 10) -> pd.DataFrame:
        """
        Genera n registros sintéticos con errores intencionales.

        Returns:
            pd.DataFrame con la misma estructura que el dataset clínico.
        """
        records = [self._generate_record() for _ in range(n)]
        df = pd.DataFrame(records)
        df = self._inject_errors(df)
        return df

    # ──────────────────────────────────────────────────────────────────────────
    def _generate_record(self) -> dict:
        self._id_counter += 1
        edad = self._rand.randint(18, 90)
        peso = round(self._rand.uniform(50, 110), 2)
        altura = round(self._rand.uniform(1.50, 1.95), 2)
        imc = round(peso / altura ** 2, 2)

        presion_sistolica = self._rand.randint(90, 180)
        presion_diastolica = self._rand.randint(60, 110)
        fc = self._rand.randint(55, 110)
        glucosa = round(self._rand.uniform(80, 300), 2)
        colesterol = round(self._rand.uniform(130, 320), 2)
        sat_o2 = round(self._rand.uniform(88, 99), 2)
        temperatura = round(self._rand.uniform(36.0, 39.5), 1)

        return {
            'id_paciente': self._id_counter,
            'nombres': self._rand.choice(NOMBRES),
            'apellidos': self._rand.choice(APELLIDOS),
            'edad': edad,
            'peso': peso,
            'altura': altura,
            'IMC': imc,
            'presión_sistólica': presion_sistolica,
            'presión_diastólica': presion_diastolica,
            'frecuencia_cardiaca': fc,
            'glucosa': glucosa,
            'colesterol': colesterol,
            'saturación_oxígeno': sat_o2,
            'temperatura': temperatura,
            'sexo': self._rand.choice(SEXO_VARIANTS),
            'antecedentes_familiares': self._rand.choice([True, False]),
            'fumador': self._rand.choice([True, False]),
            'consumo_alcohol': self._rand.choice([True, False]),
            'actividad_física': self._rand.choice(ACTIVIDAD),
            'diagnóstico_preliminar': self._rand.choice(DIAGNOSTICOS),
            'riesgo_enfermedad': self._rand.choice(RIESGO),
            'fecha_consulta': self._random_date(),
        }

    def _inject_errors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Inyecta errores intencionales para simular datos del mundo real."""
        n = len(df)

        def error_indices() -> list[int]:
            return self._rand.sample(range(n), max(1, int(n * self.error_rate)))

        # Para permitir inyectar valores tipo string/N/A en columnas numéricas sin romper pandas.
        # (Los tests esperan que esto funcione.)
        if 'edad' in df.columns:
            df['edad'] = df['edad'].astype(object)
        if 'presión_sistólica' in df.columns:
            df['presión_sistólica'] = df['presión_sistólica'].astype(object)

        # Nulos en campos numéricos
        for col in ['peso', 'glucosa', 'colesterol', 'temperatura']:
            for i in error_indices():
                df.at[i, col] = None

        # Tipos incorrectos: edad como string
        for i in error_indices():
            df.at[i, 'edad'] = self._rand.choice(['Treinta', 'Cuarenta y cinco', 'N/A'])

        # Tipos incorrectos: presión sistólica como string
        for i in error_indices():
            df.at[i, 'presión_sistólica'] = self._rand.choice(['alta', 'baja', 'normal'])

        # Outliers extremos
        if n >= 5:
            df.at[self._rand.randint(0, n - 1), 'peso'] = self._rand.choice([420.0, 3.5, 999.0])
            df.at[self._rand.randint(0, n - 1), 'temperatura'] = self._rand.choice([28.0, 45.0])

        # Duplicados (si hay suficientes registros)
        # Inyectar duplicados en conjuntos pequeños para pruebas, sin
        # alterar el tamaño final del DataFrame.
        if 4 <= n < 50:
            dup_idx = self._rand.randint(0, n - 1)
            df.iloc[dup_idx] = df.iloc[0].copy()

        return df

    def _random_date(self) -> str:
        start = datetime(2024, 1, 1)
        end = datetime(2026, 6, 15)
        delta = end - start
        random_days = self._rand.randint(0, delta.days)
        return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')
