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
import string
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
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
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
        edad = random.randint(18, 90)
        peso = round(random.uniform(50, 110), 2)
        altura = round(random.uniform(1.50, 1.95), 2)
        imc = round(peso / altura ** 2, 2)

        presion_sistolica = random.randint(90, 180)
        presion_diastolica = random.randint(60, 110)
        fc = random.randint(55, 110)
        glucosa = round(random.uniform(80, 300), 2)
        colesterol = round(random.uniform(130, 320), 2)
        sat_o2 = round(random.uniform(88, 99), 2)
        temperatura = round(random.uniform(36.0, 39.5), 1)

        return {
            'id_paciente':             self._id_counter,
            'nombres':                 random.choice(NOMBRES),
            'apellidos':               random.choice(APELLIDOS),
            'edad':                    edad,
            'sexo':                    random.choice(SEXO_VARIANTS),
            'peso':                    peso,
            'altura':                  altura,
            'IMC':                     imc,
            'presión_sistólica':       presion_sistolica,
            'presión_diastólica':      presion_diastolica,
            'frecuencia_cardiaca':     fc,
            'glucosa':                 glucosa,
            'colesterol':              colesterol,
            'saturación_oxígeno':      sat_o2,
            'temperatura':             temperatura,
            'antecedentes_familiares': random.choice([True, False]),
            'fumador':                 random.choice([True, False]),
            'consumo_alcohol':         random.choice([True, False]),
            'actividad_física':        random.choice(ACTIVIDAD),
            'diagnóstico_preliminar':  random.choice(DIAGNOSTICOS),
            'riesgo_enfermedad':       random.choice(RIESGO),
            'fecha_consulta':          self._random_date(),
        }

    def _inject_errors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Inyecta errores intencionales para simular datos del mundo real."""
        n = len(df)
        error_indices = lambda: random.sample(range(n), max(1, int(n * self.error_rate)))

        # Para permitir inyectar valores tipo string/N/A en columnas numéricas sin romper pandas.
        # (Los tests esperan que esto funcione.)
        if 'edad' in df.columns:
            df['edad'] = df['edad'].astype(object)


        # Nulos en campos numéricos
        for col in ['peso', 'glucosa', 'colesterol', 'temperatura']:
            for i in error_indices():
                df.at[i, col] = None

        # Tipos incorrectos: edad como string
        for i in error_indices():
            df.at[i, 'edad'] = random.choice(['Treinta', 'Cuarenta y cinco', 'N/A'])

        # Tipos incorrectos: presión sistólica como string
        for i in error_indices():
            df.at[i, 'presión_sistólica'] = random.choice(['alta', 'baja', 'normal'])

        # Outliers extremos
        if n >= 5:
            df.at[random.randint(0, n - 1), 'peso'] = random.choice([420.0, 3.5, 999.0])
            df.at[random.randint(0, n - 1), 'temperatura'] = random.choice([28.0, 45.0])

        # Duplicados (si hay suficientes registros)
        if n >= 4:
            duplicate_row = df.iloc[0].copy()
            df = pd.concat([df, pd.DataFrame([duplicate_row])], ignore_index=True)

        return df

    @staticmethod
    def _random_date() -> str:
        start = datetime(2024, 1, 1)
        end = datetime(2026, 6, 15)
        delta = end - start
        random_days = random.randint(0, delta.days)
        return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')
