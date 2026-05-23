"""
Tests para el DataSimulator — generación de datos sintéticos.
"""
import pandas as pd
import pytest

from apps.etl.simulation import DataSimulator


class TestDataSimulator:
    def test_generates_requested_count(self):
        sim = DataSimulator(seed=42)
        df = sim.generate(n=50)

        assert len(df) == 50

    def test_generates_required_columns(self):
        sim = DataSimulator(seed=42)
        df = sim.generate(n=10)

        required_cols = [
            'id_paciente', 'nombres', 'apellidos', 'edad', 'sexo',
            'peso', 'altura', 'IMC',
            'presión_sistólica', 'presión_diastólica',
            'frecuencia_cardiaca', 'colesterol', 'saturación_oxígeno',
            'temperatura', 'antecedentes_familiares', 'fumador',
            'consumo_alcohol', 'actividad_física',
            'diagnóstico_preliminar', 'riesgo_enfermedad', 'fecha_consulta',
        ]
        for col in required_cols:
            assert col in df.columns, f"Falta columna: {col}"

    def test_ids_are_unique(self):
        sim = DataSimulator(seed=42)
        df = sim.generate(n=100)

        assert df['id_paciente'].nunique() == len(df)

    def test_injects_nulls(self):
        """El simulador debe generar registros con valores nulos (error_rate)."""
        sim = DataSimulator(seed=42, error_rate=0.1)
        df = sim.generate(n=50)

        null_cols = ['peso', 'glucosa', 'colesterol', 'temperatura']
        total_nulls = sum(df[col].isna().sum() for col in null_cols if col in df.columns)

        assert total_nulls > 0, "Se esperaba inyectar valores nulos"

    def test_injects_duplicate_rows(self):
        """Debe generar al menos un registro duplicado (para probar DuplicateRemover)."""
        sim = DataSimulator(seed=42, error_rate=0.08)
        df = sim.generate(n=20)

        assert df.duplicated(subset=['id_paciente']).any(), "Se esperaban duplicados"

    def test_injects_outlier_extremes(self):
        """Debe generar outliers extremos (peso > 300 o temperatura < 34)."""
        sim = DataSimulator(seed=42, error_rate=0.08)
        df = sim.generate(n=20)

        has_outlier_peso = (df['peso'] > 300).any() if 'peso' in df.columns else False
        has_outlier_temp = ((df['temperatura'] < 34) | (df['temperatura'] > 42)).any() if 'temperatura' in df.columns else False

        assert has_outlier_peso or has_outlier_temp, "Se esperaban outliers extremos"

    def test_injects_type_errors(self):
        """Debe generar edades y presiones como strings incorrectos."""
        sim = DataSimulator(seed=42, error_rate=0.08)
        df = sim.generate(n=50)

        # Algun valor de edad debe ser string no convertible
        non_numeric_ages = df['edad'].apply(lambda x: not isinstance(x, (int, float)) or (isinstance(x, float) and x != x))
        assert non_numeric_ages.any(), "Se esperaban errores de tipo en edad"

    def test_seeded_generator_is_reproducible(self):
        sim1 = DataSimulator(seed=123)
        sim2 = DataSimulator(seed=123)

        df1 = sim1.generate(n=20)
        df2 = sim2.generate(n=20)

        pd.testing.assert_frame_equal(df1, df2)

    def test_date_format_is_valid(self):
        sim = DataSimulator(seed=42)
        df = sim.generate(n=10)

        from datetime import datetime
        for date_str in df['fecha_consulta']:
            try:
                datetime.strptime(str(date_str), '%Y-%m-%d')
            except ValueError:
                pytest.fail(f"Fecha inválida: {date_str}")