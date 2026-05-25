import time
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from .transformers import (
    DuplicateRemover,
    TypeCoercer,
    NullImputer,
    OutlierHandler,
    DiagnosisNormalizer,
    SexNormalizer,
    IMCCalculator,
    RiskClassifier,
)
from .quality import DataQualityReport
from .extractors import CSVExtractor, ExcelExtractor
from .loaders import DatabaseLoader
from .models import EjecucionETL, LogETL

logger = logging.getLogger('etl')


class ETLPipeline:
    """Orquestador Extract → Transform → Load con reporte de calidad."""

    TRANSFORMERS = [
        DuplicateRemover,
        TypeCoercer,
        NullImputer,
        OutlierHandler,
        DiagnosisNormalizer,
        SexNormalizer,
        IMCCalculator,
        RiskClassifier,
    ]

    def __init__(self, usuario=None, tipo: str = 'manual'):
        self.usuario = usuario
        self.tipo = tipo
        self.ejecucion: Optional[EjecucionETL] = None
        self.quality_report = DataQualityReport()
        self.start_time = None

    def run(self, source_path: str) -> dict:
        self.start_time = time.time()
        self.ejecucion = EjecucionETL.objects.create(
            usuario=self.usuario,
            archivo_fuente=source_path,
            tipo=self.tipo,
            estado='en_proceso',
        )

        try:
            logger.info(f"[ETL] EXTRACT: leyendo {source_path}")
            df_raw = self._extract(source_path)
            self.ejecucion.registros_extraidos = len(df_raw)
            self.quality_report.snapshot_before(df_raw)

            logger.info(f"[ETL] TRANSFORM: {len(self.TRANSFORMERS)} transformadores")
            df_clean = self._transform(df_raw)

            logger.info(f"[ETL] LOAD: insertando {len(df_clean)} registros")
            loaded_count = self._load(df_clean)

            duration = time.time() - self.start_time
            report = self.quality_report.generate(df_raw, df_clean, duration)

            self.ejecucion.fecha_fin = datetime.now()
            self.ejecucion.duracion_segundos = round(duration, 3)
            self.ejecucion.registros_procesados = loaded_count
            self.ejecucion.registros_rechazados = len(df_raw) - len(df_clean)
            self.ejecucion.reporte_calidad = report
            # mantener campos contadores (si existen en report)
            self.ejecucion.duplicados_eliminados = int(report['acciones_correctivas'].get('duplicados_eliminados', 0))
            self.ejecucion.nulos_imputados = int(report['acciones_correctivas'].get('nulos_imputados', 0))
            self.ejecucion.estado = 'completado'
            self.ejecucion.save()

            logger.info(f"[ETL] COMPLETADO en {duration:.2f}s — {loaded_count} registros cargados")
            return {'status': 'success', 'ejecucion_id': self.ejecucion.id, 'report': report}

        except Exception as exc:
            if self.ejecucion:
                self.ejecucion.estado = 'fallido'
                self.ejecucion.save(update_fields=['estado'])
            logger.error(f"[ETL] FALLIDO: {exc}", exc_info=True)
            raise

    def run_dataframe(self, df: pd.DataFrame) -> dict:
        """Ruta alternativa para ETL sobre un DataFrame (simulaciones/tests).

        En esta ruta NO persistimos EjecucionETL, por lo que evitamos acceder a self.ejecucion.
        """
        self.start_time = time.time()
        self.ejecucion = None

        try:
            df_raw = df.copy()
            # En tests solo necesitamos el reporte; no persisitimos EjecucionETL.
            self.quality_report.snapshot_before(df_raw)


            df_clean = self._transform(df_raw)
            loaded_count = self._load(df_clean)

            duration = time.time() - self.start_time
            report = self.quality_report.generate(df_raw, df_clean, duration)

            # No se persiste la ejecución cuando se trabaja con DataFrames
            return {'status': 'success', 'ejecucion_id': None, 'report': report}
        except Exception:
            # En caso de error no intentamos persistir estado de ejecución
            raise

    def _extract(self, source_path: str) -> pd.DataFrame:
        if source_path.endswith('.xlsx') or source_path.endswith('.xls'):
            return ExcelExtractor().extract(source_path)
        return CSVExtractor().extract(source_path)

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        for TransformerClass in self.TRANSFORMERS:
            transformer = TransformerClass(ejecucion=self.ejecucion, quality_report=self.quality_report)
            df = transformer.transform(df)
            logger.info(f"  ✔ {TransformerClass.__name__}: {len(df)} registros restantes")
        return df

    def _load(self, df: pd.DataFrame) -> int:
        loader = DatabaseLoader(ejecucion=self.ejecucion)
        return loader.load(df)

