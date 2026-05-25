import pandas as pd
from pathlib import Path
from typing import Set


class CSVExtractor:
    """Extrae datos desde CSV con validación de 22 columnas clínicas requeridas."""
    
    REQUIRED_COLUMNS: Set[str] = {
        'id_paciente', 'nombres', 'apellidos', 'edad', 'sexo', 'peso',
        'altura', 'imc', 'presion_sistolica', 'presion_diastolica',
        'frecuencia_cardiaca', 'glucosa', 'colesterol', 'saturacion_oxigeno',
        'temperatura', 'antecedentes_familiares', 'fumador', 'consumo_alcohol',
        'actividad_fisica', 'diagnostico_preliminar', 'riesgo_enfermedad', 'fecha_consulta',
    }

    def extract(self, path: str) -> pd.DataFrame:
        """Extrae CSV y valida todas las 22 columnas requeridas."""
        path_obj: Path = Path(path)
        if not path_obj.exists() or not path_obj.is_file():
            raise FileNotFoundError(f"El archivo no existe: {path}")

        try:
            df: pd.DataFrame = pd.read_csv(path)
        except Exception as exc:
            raise ValueError(f"Error leyendo CSV: {exc}") from exc

        self._validate_columns(df)
        return df

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Valida que todas las 22 columnas requeridas estén presentes."""
        missing: list = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(
                f"CSV inválido: faltan columnas requeridas ({len(missing)}/22): {', '.join(sorted(missing))}"
            )


class ExcelExtractor:
    """Extrae datos desde Excel con validación de 22 columnas clínicas requeridas."""
    
    REQUIRED_COLUMNS: Set[str] = CSVExtractor.REQUIRED_COLUMNS

    def extract(self, path: str) -> pd.DataFrame:
        """Extrae primera hoja de Excel y valida todas las 22 columnas requeridas."""
        try:
            df: pd.DataFrame = pd.read_excel(path)
        except Exception as exc:
            raise ValueError(f"Error leyendo Excel: {exc}") from exc

        self._validate_columns(df)
        return df

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Valida que todas las 22 columnas requeridas estén presentes."""
        missing: list = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(
                f"Excel inválido: faltan columnas requeridas ({len(missing)}/22): {', '.join(sorted(missing))}"
            )

