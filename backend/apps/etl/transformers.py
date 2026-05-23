import re
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class BaseTransformer(ABC):
    def __init__(self, ejecucion=None, quality_report=None):
        self.ejecucion = ejecucion
        self.qr = quality_report

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def _log(self, mensaje: str, campo: str = None, nivel: str = 'INFO'):
        """Registra auditoría si existe EjecucionETL real.

        En tests se usa un MockEjecucion que no es instancia de EjecucionETL,
        por lo que aquí degradamos a no-op.
        """
        if not self.ejecucion:
            return

        try:
            from .models import EjecucionETL, LogETL

            if not isinstance(self.ejecucion, EjecucionETL):
                return

            LogETL.objects.create(
                ejecucion=self.ejecucion,
                nivel=nivel,
                mensaje=mensaje,
                campo_afectado=campo,
            )
        except Exception:
            return




class DuplicateRemover(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(subset=['id_paciente'], keep='first')
        removed = before - len(df)
        if removed and self.qr:
            self.qr.add_metric('duplicados_eliminados', removed)
            self._log(f"Eliminados {removed} duplicados por id_paciente", 'id_paciente', 'WARNING')
        return df.reset_index(drop=True)


class TypeCoercer(BaseTransformer):
    NUMERIC_COLS = {
        'id_paciente': int,
        'edad': 'Int64',
        'peso': float,
        'altura': float,
        'IMC': float,
        # Compatibilidad con tests: usan presion_sistolica/presion_diastolica sin tilde
        'presion_sistolica': 'Int64',
        'presion_diastolica': 'Int64',
        # Alias con tilde (por si vienen del dataset)
        'presión_sistólica': 'Int64',
        'presión_diastólica': 'Int64',
        'frecuencia_cardiaca': 'Int64',
        'glucosa': float,
        'colesterol': float,
        'saturación_oxígeno': float,
        'saturacion_oxigeno': float,
        'temperatura': float,
    }


    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        errors_found = 0
        for col, dtype in self.NUMERIC_COLS.items():
            if col not in df.columns:
                continue
            original_na = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if dtype == 'Int64':
                df[col] = df[col].astype('Int64')
            new_na = int(df[col].isna().sum() - original_na)
            if new_na > 0:
                errors_found += new_na
                self._log(f"{new_na} valores no numéricos convertidos a NaN en '{col}'", col, 'WARNING')

        if self.qr:
            self.qr.add_metric('errores_tipo_corregidos', errors_found)
        return df


class NullImputer(BaseTransformer):
    MEDIAN_COLS = ['peso', 'glucosa', 'colesterol', 'temperatura', 'IMC']
    MEDIAN_INT_COLS = ['presion_sistolica', 'presion_diastolica', 'presión_sistólica', 'presión_diastólica', 'frecuencia_cardiaca', 'edad']

    MODE_COLS = ['sexo', 'actividad_física', 'diagnostico_preliminar', 'diagnóstico_preliminar']


    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        total_imputed = 0

        for col in self.MEDIAN_COLS:
            if col in df.columns and df[col].isna().any():
                count = int(df[col].isna().sum())
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                total_imputed += count
                self._log(f"Imputados {count} nulos en '{col}' con mediana={median_val:.2f}", col)

        for col in self.MEDIAN_INT_COLS:
            if col in df.columns and df[col].isna().any():
                count = int(df[col].isna().sum())
                median_val = int(df[col].median())
                df[col] = df[col].fillna(median_val)
                total_imputed += count
                self._log(f"Imputados {count} nulos en '{col}' con mediana={median_val}", col)

        for col in self.MODE_COLS:
            if col in df.columns and df[col].isna().any():
                count = int(df[col].isna().sum())
                mode_val = df[col].mode()[0]
                df[col] = df[col].fillna(mode_val)
                total_imputed += count
                self._log(f"Imputados {count} nulos en '{col}' con moda='{mode_val}'", col)

        if self.qr:
            self.qr.add_metric('nulos_imputados', total_imputed)
        return df


class OutlierHandler(BaseTransformer):
    CLINICAL_RANGES = {
        'peso': (20, 300),
        'altura': (0.5, 2.5),
        # Tests usan sin tilde
        'presion_sistolica': (60, 250),
        'presion_diastolica': (40, 150),
        # Alias con tilde
        'presión_sistólica': (60, 250),
        'presión_diastólica': (40, 150),
        'frecuencia_cardiaca': (30, 220),
        'glucosa': (50, 600),
        'colesterol': (50, 400),
        'saturacion_oxigeno': (70, 100),
        'saturación_oxígeno': (70, 100),
        'temperatura': (34, 42),
        'edad': (0, 120),
    }


    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        outliers_total = 0
        for col, (min_val, max_val) in self.CLINICAL_RANGES.items():
            if col not in df.columns:
                continue
            mask = (df[col] < min_val) | (df[col] > max_val)
            count = int(mask.sum())
            if count > 0:
                median_val = df.loc[~mask, col].median()
                df.loc[mask, col] = median_val
                outliers_total += count
                self._log(
                    f"{count} outliers en '{col}' (rango [{min_val},{max_val}]) → reemplazados con mediana={median_val:.2f}",
                    col,
                    'WARNING',
                )
        if self.qr:
            self.qr.add_metric('outliers_corregidos', outliers_total)
        return df


class DiagnosisNormalizer(BaseTransformer):
    col = 'diagnóstico_preliminar'
    MAPPING = {
        r'(?i)hipertensi[oó]n': 'Hipertensión',
        r'(?i)hipertencion': 'Hipertensión',
        r'(?i)prehipertensi[oó]n': 'Prehipertensión',
        r'(?i)diabetes\s*tipo\s*2': 'Diabetes Tipo 2',
        r'(?i)riesgo\s*cardiovascular': 'Riesgo cardiovascular',
        r'(?i)cardiopat[ií]a': 'Cardiopatía',
        r'(?i)obesidad': 'Obesidad',
        r'(?i)paciente\s*sano': 'Paciente sano',
    }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.col not in df.columns:
            return df
        original = df[self.col].copy()
        for pattern, repl in self.MAPPING.items():
            df[self.col] = df[self.col].astype(str).str.replace(pattern, repl, regex=True)
        corrected = int((df[self.col] != original).sum())
        if corrected:
            self._log(f"Normalizados {corrected} diagnósticos con errores ortográficos", self.col)
            if self.qr:
                self.qr.add_metric('diagnosticos_normalizados', corrected)
        return df


class SexNormalizer(BaseTransformer):
    col = 'sexo'

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.col not in df.columns:
            return df
        mapping = {
            'm': 'M', 'masculino': 'M', 'hombre': 'M',
            'f': 'F', 'femenino': 'F', 'mujer': 'F',
        }
        original = df[self.col].copy()
        df[self.col] = df[self.col].astype(str).str.strip().str.lower().map(mapping).fillna('M')
        corrected = int((df[self.col] != original).sum())
        if self.qr:
            self.qr.add_metric('sexo_normalizados', corrected)
        return df


class IMCCalculator(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = df['peso'].notna() & df['altura'].notna() & (df['altura'] > 0)
        df.loc[mask, 'IMC'] = (df.loc[mask, 'peso'] / (df.loc[mask, 'altura'] ** 2)).round(2)

        conditions = [
            df['IMC'] < 18.5,
            (df['IMC'] >= 18.5) & (df['IMC'] < 25),
            (df['IMC'] >= 25) & (df['IMC'] < 30),
            df['IMC'] >= 30,
        ]
        # Tests esperan exactamente las etiquetas: 'Bajo peso', 'Normal', etc.
        choices = ['Bajo peso', 'Normal', 'Sobrepeso', 'Obesidad']
        df['clasificacion_imc'] = np.select(conditions, choices, default='Normal')

        # Asegurar que exista 'Normal' para IMC en [18.5, 25)
        # (si algún dtype raro impide que se cumpla la condición)
        normal_mask = (df['IMC'] >= 18.5) & (df['IMC'] < 25)
        df.loc[normal_mask, 'clasificacion_imc'] = 'Normal'


        return df


class RiskClassifier(BaseTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df['riesgo_enfermedad'] = df.apply(self._classify_row, axis=1)
        return df

    @staticmethod
    def _classify_row(row) -> str:
        score = 0

        ps = row.get('presión_sistólica', 0) or 0
        pd_ = row.get('presión_diastólica', 0) or 0

        if ps > 180:
            score += 3
        elif ps > 140:
            score += 2
        elif ps > 120:
            score += 1

        glu = row.get('glucosa', 0) or 0
        if glu > 300:
            score += 3
        elif glu > 200:
            score += 2
        elif glu > 140:
            score += 1

        sat = row.get('saturación_oxígeno', 100) or 100
        if sat < 85:
            score += 3
        elif sat < 90:
            score += 2

        edad = row.get('edad', 0) or 0
        if edad > 70 and bool(row.get('antecedentes_familiares', False)):
            score += 2
        if bool(row.get('fumador', False)):
            score += 1
        if (row.get('IMC', 0) or 0) > 35:
            score += 1

        if score >= 6:
            return 'Crítico'
        if score >= 4:
            return 'Alto'
        if score >= 2:
            return 'Medio'
        return 'Bajo'


# ─────────────────────────────────────────────────────────────────────────────
# Función de alto nivel: limpia archivo Excel clínico completo
# Uso directo:  python -c "from apps.etl.transformers import limpiar_excel_clinico; limpiar_excel_clinico('datos/raw.xlsx', 'datos/limpio.xlsx')"
# Integrado a ETLPipeline: pipeline.run_file('datos/raw.xlsx')
# ─────────────────────────────────────────────────────────────────────────────


def limpiar_excel_clinico(ruta_entrada: str, ruta_salida: str | None = None) -> pd.DataFrame:
    """
    Limpia un archivo Excel de datos clínicos de HealthAnalytics IPS.

    Pipeline aplicado (en orden):
      1. DuplicateRemover  → elimina registros duplicados por id_paciente
      2. TypeCoercer      → convierte columnas numéricas, valores no numéricos → NaN
      3. NullImputer      → imputa NaN con mediana (signos vitales) o moda (categóricas)
      4. OutlierHandler   → recorta valores fuera de rangos clínicos a la mediana
      5. DiagnosisNormalizer → corrige spelling de diagnósticos manuscritos
      6. IMCCalculator    → calcula IMC y clasificación ponderal
      7. RiskClassifier   → asigna riesgo_enfermedad (Bajo/Medio/Alto/Crítico)

    Args:
        ruta_entrada:  Ruta al archivo .xlsx/.xls bruto.
        ruta_salida:   Si se proporciona, guarda el DataFrame limpio en esa ruta.

    Returns:
        DataFrame limpio, listo para cargar a la BD o entrenar ML.
    """
    import logging
    from apps.etl.quality import DataQualityReport
    from apps.etl.pipeline import ETLPipeline

    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando limpieza de: {ruta_entrada}")

    # ── Carga desde archivo Excel ─────────────────────────────────
    df = ETLPipeline._extract_from_file(ruta_entrada)
    initial_rows = len(df)
    logger.info(f"Registros cargados: {initial_rows}")

    # ── Snapshot antes ────────────────────────────────────────────
    qr = DataQualityReport()
    qr.snapshot_before(df)

    # ── Pipeline de limpieza ──────────────────────────────────────
    pipeline = ETLPipeline(tipo='manual')

    transformers = [
        DuplicateRemover(ejecucion=None, quality_report=qr),
        TypeCoercer(ejecucion=None, quality_report=qr),
        NullImputer(ejecucion=None, quality_report=qr),
        OutlierHandler(ejecucion=None, quality_report=qr),
        DiagnosisNormalizer(ejecucion=None, quality_report=qr),
        IMCCalculator(ejecucion=None, quality_report=qr),
        RiskClassifier(ejecucion=None, quality_report=qr),
    ]

    for t in transformers:
        df = t.transform(df)

    # ── Generar DataQualityReport ─────────────────────────────────
    report = qr.generate(df_before=df, df_after=df, duration=0.0)

    logger.info(f"Reporte de calidad: score={report['quality_score']}")
    logger.info(f"Acciones correctivas: {report['acciones_correctivas']}")

    # ── Guardar salida si se pidió ────────────────────────────────
    if ruta_salida:
        df.to_excel(ruta_salida, index=False, engine='openpyxl')
        logger.info(f"Archivo limpio guardado en: {ruta_salida}")

    return df

