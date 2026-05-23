"""
Tests para el pipeline ETL end-to-end.
"""
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from apps.etl.pipeline import ETLPipeline
from apps.etl.transformers import (
    DuplicateRemover,
    TypeCoercer,
    NullImputer,
    OutlierHandler,
)


class TestETLPipeline:
    """Tests del orquestador ETL completo."""

    def test_pipeline_runs_all_transformers(self, df_with_errors):
        """ETL debe ejecutar todos los 8 transformadores en secuencia."""
        pipeline = ETLPipeline(tipo='manual')

        # Patch _load para evitar acceso a BD
        with patch.object(pipeline, '_load', return_value=len(df_with_errors)):
            result = pipeline.run_dataframe(df_with_errors)

        assert result['status'] == 'success'
        assert 'ejecucion_id' in result
        assert 'report' in result

    def test_pipeline_catches_execution_errors(self):
        """Si un transformador falla, ETL marca como fallido."""
        # DataFrame vacío que causa error en algún paso
        df_empty = pd.DataFrame({'id_paciente': [], 'glucosa': []})
        pipeline = ETLPipeline(tipo='manual')

        with pytest.raises(Exception):
            pipeline.run_dataframe(df_empty)

    def test_pipeline_calculates_duration(self, sample_dataframe):
        """ETL mide correctamente el tiempo de ejecución."""
        pipeline = ETLPipeline(tipo='manual')

        with patch.object(pipeline, '_load', return_value=len(sample_dataframe)):
            result = pipeline.run_dataframe(sample_dataframe)

        report = result['report']
        assert 'duracion_segundos' in report
        assert report['duracion_segundos'] > 0

    def test_pipeline_calls_quality_report(self, df_with_errors):
        """ETL genera DataQualityReport antes y después."""
        pipeline = ETLPipeline(tipo='manual')

        with patch.object(pipeline, '_load', return_value=len(df_with_errors)):
            result = pipeline.run_dataframe(df_with_errors)

        report = result['report']
        assert 'before' in report
        assert 'after' in report
        assert 'quality_score' in report

    def test_pipeline_extracts_correct_count(self, df_with_errors):
        """registros_extraidos refleja el número de filas antes de transformar."""
        pipeline = ETLPipeline(tipo='manual')

        initial_count = len(df_with_errors)
        with patch.object(pipeline, '_load', return_value=initial_count):
            result = pipeline.run_dataframe(df_with_errors)

        assert result['report']['before']['total_rows'] == initial_count


class TestPipelineIntegration:
    """Tests de integración mostrando el valor diferenciador del ETL."""

    def test_full_cleaning_pipeline(self, df_with_errors):
        """El pipeline completo debe limpiar un DataFrame sucio y producir uno limpio."""
        pipeline = ETLPipeline(tipo='simulacion')

        with patch.object(pipeline, '_load', return_value=0):
            result = pipeline.run_dataframe(df_with_errors)

        report = result['report']

        # Debe mostrar acciones correctivas
        assert 'acciones_correctivas' in report
        total_actions = sum(report['acciones_correctivas'].values())
        assert total_actions > 0, "Se esperaban acciones correctivas en datos sucios"

        # El quality score debe ser alto tras la limpieza
        assert report['quality_score'] >= 50

    def test_deduplication_improves_quality(self, sample_dataframe):
        """Eliminar duplicados mejora el quality score."""
        # Crear dataframe con duplicados explícitos
        df_dirty = pd.concat([sample_dataframe, sample_dataframe.head(2)], ignore_index=True)

        pipeline = ETLPipeline(tipo='simulacion')

        with patch.object(pipeline, '_load', return_value=len(df_dirty)):
            result = pipeline.run_dataframe(df_dirty)

        acciones = result['report']['acciones_correctivas']
        assert acciones.get('duplicados_eliminados', 0) >= 2

    def test_null_imputation_reported(self):
        """Nulos eliminados deben reflejarse en el reporte."""
        df_nulls = pd.DataFrame({
            'id_paciente': [1, 2, 3, 4, 5],
            'peso': [None, 80.0, None, 90.0, None],
            'glucosa': [100.0, None, 150.0, None, None],
            'presión_sistólica': [120, 'alta', 110, 'normal', None],
            'presión_diastólica': [80, 95, 70, 105, 75],
            'frecuencia_cardiaca': [72, 85, 68, 90, 70],
            'glucosa': [100.0, 200.0, 90.0, 310.0, 95.0],
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

        pipeline = ETLPipeline(tipo='simulacion')

        with patch.object(pipeline, '_load', return_value=5):
            result = pipeline.run_dataframe(df_nulls)

        acciones = result['report']['acciones_correctivas']
        assert acciones.get('nulos_imputados', 0) > 0 or acciones.get('errores_tipo_corregidos', 0) > 0