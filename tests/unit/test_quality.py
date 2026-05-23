"""
Tests para el módulo de calidad de datos (DataQualityReport).
El report genera métricas antes/después de la transformación ETL.
"""
import pandas as pd
import pytest

from apps.etl.quality import DataQualityReport


class TestDataQualityReport:
    def test_snapshot_before_captures_null_counts(self):
        df = pd.DataFrame({
            'glucosa': [100.0, None, 150.0],
            'peso': [65.0, 80.0, None],
        })
        qr = DataQualityReport()
        qr.snapshot_before(df)

        assert qr.before_stats['nulos']['glucosa'] == 1
        assert qr.before_stats['nulos']['peso'] == 1
        assert qr.before_stats['total_rows'] == 3

    def test_snapshot_before_captures_unique_counts(self):
        df = pd.DataFrame({
            'id_paciente': [1, 2, 1, 3, 1],
            'glucosa': [100.0, 200.0, 150.0, 180.0, 120.0],
        })
        qr = DataQualityReport()
        qr.snapshot_before(df)

        assert qr.before_stats['duplicados']['id_paciente'] == 2  # 2 duplicate entries

    def test_generate_returns_complete_report(self):
        df_before = pd.DataFrame({
            'glucosa': [100.0, None, 150.0],
            'peso': [65.0, 80.0, None],
        })
        df_after = pd.DataFrame({
            'glucosa': [100.0, 125.0, 150.0],  # nulos imputados
            'peso': [65.0, 80.0, 72.5],         # nulos imputados
        })

        qr = DataQualityReport()
        qr.snapshot_before(df_before)
        qr.add_metric('nulos_imputados', 3)
        qr.add_metric('duplicados_eliminados', 0)
        qr.add_metric('errores_tipo_corregidos', 0)
        qr.add_metric('outliers_corregidos', 0)
        qr.add_metric('diagnosticos_normalizados', 0)

        report = qr.generate(df_before, df_after, duration=1.5)

        assert 'quality_score' in report
        assert 'before' in report
        assert 'after' in report
        assert 'metricas_resumen' in report
        assert 'acciones_correctivas' in report
        assert 'file_quality_score' in report

        assert report['before']['total_rows'] == 3
        assert report['after']['total_rows'] == 3
        assert report['acciones_correctivas']['nulos_imputados'] == 3

    def test_quality_score_reflects_data_quality(self):
        df_before = pd.DataFrame({
            'glucosa': [None, None, None, None, None],  # 100% nulos
            'peso': [None, None, None, None, None],
        })
        df_after = pd.DataFrame({
            'glucosa': [100.0, 100.0, 100.0, 100.0, 100.0],
            'peso': [70.0, 70.0, 70.0, 70.0, 70.0],
        })

        qr = DataQualityReport()
        qr.snapshot_before(df_before)
        qr.add_metric('nulos_imputados', 10)
        qr.add_metric('duplicados_eliminados', 0)
        qr.add_metric('errores_tipo_corregidos', 0)
        qr.add_metric('outliers_corregidos', 0)
        qr.add_metric('diagnosticos_normalizados', 0)

        report = qr.generate(df_before, df_after, duration=0.1)

        # Score debería ser alto porque los datos fueron limpiados
        assert report['quality_score'] > 80
        assert report['file_quality_score'] > 80

    def test_zero_nulos_before_yields_full_score(self):
        df_before = pd.DataFrame({
            'glucosa': [100.0, 150.0, 120.0],
            'peso': [65.0, 80.0, 55.0],
        })
        df_after = df_before.copy()

        qr = DataQualityReport()
        qr.snapshot_before(df_before)
        qr.add_metric('nulos_imputados', 0)
        qr.add_metric('duplicados_eliminados', 0)
        qr.add_metric('errores_tipo_corregidos', 0)
        qr.add_metric('outliers_corregidos', 0)
        qr.add_metric('diagnosticos_normalizados', 0)

        report = qr.generate(df_before, df_after, duration=0.05)

        assert report['quality_score'] == 100

    def test_add_metric_accumulates(self):
        qr = DataQualityReport()
        qr.add_metric('nulos_imputados', 3)
        qr.add_metric('nulos_imputados', 2)

        assert qr.metrics['nulos_imputados'] == 5