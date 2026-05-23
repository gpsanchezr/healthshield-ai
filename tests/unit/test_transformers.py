"""
Tests para los transformadores del pipeline ETL.
Cada transformador aplica una regla de limpieza específica.
"""
import numpy as np
import pandas as pd
import pytest

from apps.etl.transformers import (
    DuplicateRemover,
    TypeCoercer,
    NullImputer,
    OutlierHandler,
    DiagnosisNormalizer,
    SexNormalizer,
    IMCCalculator,
    RiskClassifier,
)
from apps.etl.quality import DataQualityReport


class MockEjecucion:
    """Mock mínimo de EjecucionETL para tests."""
    def __init__(self):
        self.id = 1


class TestDuplicateRemover:
    def test_removes_duplicates_by_id_paciente(self):
        df = pd.DataFrame({
            'id_paciente': [1, 2, 1, 3, 2],
            'nombre': ['Ana', 'Luis', 'Ana', 'María', 'Luis'],
            'glucosa': [100.0, 200.0, 100.0, 150.0, 200.0],
        })
        qr = DataQualityReport()
        transformer = DuplicateRemover(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert len(result) == 3
        ids = result['id_paciente'].tolist()
        assert ids == [1, 2, 3]
        assert qr.metrics.get('duplicados_eliminados', 0) == 2

    def test_no_duplicates_unchanged(self):
        df = pd.DataFrame({
            'id_paciente': [1, 2, 3],
            'glucosa': [100.0, 200.0, 150.0],
        })
        qr = DataQualityReport()
        transformer = DuplicateRemover(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert len(result) == 3
        assert qr.metrics.get('duplicados_eliminados', 0) == 0


class TestTypeCoercer:
    def test_converts_valid_numeric_columns(self):
        df = pd.DataFrame({
            'edad': [25, 30, 45],
            'presion_sistolica': [120, 110, 140],
            'glucosa': [100.0, 90.5, 120.0],
        })
        qr = DataQualityReport()
        transformer = TypeCoercer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['edad'].dtype in [int, 'int64', 'Int64']
        assert result['presion_sistolica'].dtype in [int, 'int64', 'Int64']
        assert result['glucosa'].dtype == float

    def test_converts_invalid_strings_to_nan(self):
        df = pd.DataFrame({
            'edad': [25, 'Treinta', 45, 'N/A'],
            'presion_sistolica': [120, 'alta', 'normal', 110],
        })
        qr = DataQualityReport()
        transformer = TypeCoercer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['edad'].isna().sum() == 2
        assert result['presion_sistolica'].isna().sum() == 2
        assert qr.metrics.get('errores_tipo_corregidos', 0) == 4

    def test_ignores_missing_columns(self):
        df = pd.DataFrame({'glucosa': [100.0, 200.0]})
        qr = DataQualityReport()
        transformer = TypeCoercer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert len(result) == 2
        assert qr.metrics.get('errores_tipo_corregidos', 0) == 0


class TestNullImputer:
    def test_imputes_numeric_medians(self):
        df = pd.DataFrame({
            'peso': [65.0, None, 55.0],
            'glucosa': [None, 200.0, 150.0],
            'presion_sistolica': [120, 110, None],
        })
        qr = DataQualityReport()
        transformer = NullImputer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['peso'].isna().sum() == 0
        assert result['glucosa'].isna().sum() == 0
        assert result['presion_sistolica'].isna().sum() == 0
        assert qr.metrics.get('nulos_imputados', 0) == 3

    def test_imputes_categorical_modes(self):
        df = pd.DataFrame({
            'sexo': ['M', None, 'F', None],
            'diagnostico_preliminar': [None, 'Hipertensión', 'Diabetes Tipo 2', None],
        })
        qr = DataQualityReport()
        transformer = NullImputer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['sexo'].isna().sum() == 0
        assert result['diagnostico_preliminar'].isna().sum() == 0


class TestOutlierHandler:
    def test_winsorizes_out_of_range_values(self):
        df = pd.DataFrame({
            'peso': [65.0, 450.0, 55.0],         # 450 is outlier (>300)
            'presion_sistolica': [120, 300, 110], # 300 is outlier (>250)
            'temperatura': [36.5, 28.0, 36.8],    # 28 is outlier (<34)
            'glucosa': [100.0, 200.0, 150.0],
        })
        qr = DataQualityReport()
        transformer = OutlierHandler(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['peso'].max() <= 300
        assert result['presion_sistolica'].max() <= 250
        assert result['temperatura'].min() >= 34
        assert qr.metrics.get('outliers_corregidos', 0) == 3

    def test_leaves_normal_values_unchanged(self):
        df = pd.DataFrame({
            'peso': [65.0, 80.0, 55.0],
            'presion_sistolica': [120, 130, 110],
            'glucosa': [100.0, 200.0, 150.0],
        })
        qr = DataQualityReport()
        transformer = OutlierHandler(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert qr.metrics.get('outliers_corregidos', 0) == 0


class TestDiagnosisNormalizer:
    def test_normalizes_hypertension_variants(self):
        df = pd.DataFrame({
            'diagnóstico_preliminar': ['hipertencion', 'HIPERTENSIÓN', 'Hipertension', 'Hipertensión'],
        })
        qr = DataQualityReport()
        transformer = DiagnosisNormalizer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert all(result['diagnóstico_preliminar'] == 'Hipertensión')
        assert qr.metrics.get('diagnosticos_normalizados', 0) == 3

    def test_normalizes_diabetes_type2(self):
        df = pd.DataFrame({
            'diagnóstico_preliminar': ['Diabetes tipo 2', 'diabetes tipo 2', 'Diabetes Tipo 2'],
        })
        qr = DataQualityReport()
        transformer = DiagnosisNormalizer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert all(result['diagnóstico_preliminar'] == 'Diabetes Tipo 2')


class TestSexNormalizer:
    def test_normalizes_sex_values(self):
        df = pd.DataFrame({
            'sexo': ['m', 'M', 'masculino', 'F', 'f', 'femenino', 'mujer'],
        })
        qr = DataQualityReport()
        transformer = SexNormalizer(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['sexo'].tolist() == ['M', 'M', 'M', 'F', 'F', 'F', 'F']


class TestIMCCalculator:
    def test_calculates_imc_from_peso_altura(self):
        df = pd.DataFrame({
            'peso': [65.0, 80.0],
            'altura': [1.65, 1.75],
        })
        qr = DataQualityReport()
        transformer = IMCCalculator(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        expected_imc = [round(65.0 / (1.65 ** 2), 2), round(80.0 / (1.75 ** 2), 2)]
        assert result['IMC'].iloc[0] == expected_imc[0]
        assert result['IMC'].iloc[1] == expected_imc[1]

    def test_assigns_imc_classification(self):
        df = pd.DataFrame({
            'peso': [45.0, 70.0, 90.0, 110.0],
            'altura': [1.65, 1.65, 1.65, 1.65],
        })
        qr = DataQualityReport()
        transformer = IMCCalculator(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert 'Bajo peso' in result['clasificacion_imc'].values
        assert 'Normal' in result['clasificacion_imc'].values
        assert 'Sobrepeso' in result['clasificacion_imc'].values
        assert 'Obesidad' in result['clasificacion_imc'].values


class TestRiskClassifier:
    def test_classifies_critical_high_risk(self):
        df = pd.DataFrame({
            'presión_sistólica': [190],
            'presión_diastólica': [100],
            'glucosa': [350],
            'saturación_oxígeno': [80],
            'IMC': 30,
            'fumador': True,
            'antecedentes_familiares': True,
            'edad': 75,
        })
        qr = DataQualityReport()
        transformer = RiskClassifier(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['riesgo_enfermedad'].iloc[0] == 'Crítico'

    def test_classifies_low_risk(self):
        df = pd.DataFrame({
            'presión_sistólica': [110],
            'presión_diastólica': [70],
            'glucosa': [100],
            'saturación_oxígeno': [98],
            'IMC': 22,
            'fumador': False,
            'antecedentes_familiares': False,
            'edad': 30,
        })
        qr = DataQualityReport()
        transformer = RiskClassifier(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['riesgo_enfermedad'].iloc[0] == 'Bajo'

    def test_classifies_medium_risk(self):
        df = pd.DataFrame({
            'presión_sistólica': [130],
            'presión_diastólica': [85],
            'glucosa': [160],
            'saturación_oxígeno': [96],
            'IMC': 27,
            'fumador': False,
            'antecedentes_familiares': False,
            'edad': 45,
        })
        qr = DataQualityReport()
        transformer = RiskClassifier(ejecucion=MockEjecucion(), quality_report=qr)
        result = transformer.transform(df)

        assert result['riesgo_enfermedad'].iloc[0] == 'Medio'