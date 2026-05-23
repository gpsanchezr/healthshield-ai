from datetime import datetime
import pandas as pd


class DataQualityReport:
    """Reporte de calidad de datos (0–100) basado en recuperaciones y correcciones."""

    def __init__(self):
        self.metrics = {}
        self.before_stats = {}

    def snapshot_before(self, df: pd.DataFrame):
        # Tests esperan una estructura tipo:
        # before_stats = {'nulos': {...}, 'duplicados': {...}, ...}
        nulos = df.isnull().sum().to_dict()
        duplicados = {}
        if 'id_paciente' in df.columns:
            duplicados['id_paciente'] = int(df.duplicated(subset=['id_paciente']).sum())

        self.before_stats = {
            'total_rows': len(df),
            'total_registros': len(df),
            'total_nulos': int(df.isnull().sum().sum()),
            'nulos': {k: int(v) for k, v in nulos.items()},
            'duplicados': duplicados,
        }

    def add_metric(self, key: str, value):
        self.metrics[key] = self.metrics.get(key, 0) + value

    def generate(self, df_before: pd.DataFrame, df_after: pd.DataFrame, duration: float) -> dict:
        total_raw = len(df_before)
        total_clean = len(df_after)
        rechazados = total_raw - total_clean
        score = self._calculate_quality_score(total_raw, rechazados)

        report = {
            'generado_en': datetime.now().isoformat(),
            'duracion_segundos': round(duration, 3),
            'antes': self.before_stats,
            'despues': {
                'total_registros': total_clean,
                'total_nulos': int(df_after.isnull().sum().sum()),
            },
            'acciones_correctivas': self.metrics,
            'registros_rechazados': rechazados,
            'porcentaje_recuperados': round((total_clean / max(total_raw, 1)) * 100, 2),
            'porcentaje_rechazados': round((rechazados / max(total_raw, 1)) * 100, 2),
            'quality_score': score,
            'clasificacion': self._score_label(score),
        }

        # Conserva compatibilidad con nombres de reportes en inglés y español
        report['before'] = report['antes']
        report['after'] = report['despues']
        report['despues']['total_rows'] = report['despues']['total_registros']
        report['metricas_resumen'] = {
            'total_registros_antes': report['antes'].get('total_rows'),
            'total_registros_despues': report['despues'].get('total_registros'),
            'total_nulos_despues': report['despues'].get('total_nulos'),
        }
        report['file_quality_score'] = score

        return report


    def _calculate_quality_score(self, total: int, rejected: int) -> float:
        base = 100 - (rejected / max(total, 1) * 100)
        # Deducción pequeña por correcciones tipo (para reflejar "severidad")
        deductions = min(self.metrics.get('errores_tipo_corregidos', 0) * 0.1, 20)
        return round(max(base - deductions, 0), 2)

    @staticmethod
    def _score_label(score: float) -> str:
        if score >= 90:
            return 'Excelente'
        if score >= 75:
            return 'Buena'
        if score >= 60:
            return 'Aceptable'
        return 'Deficiente'

