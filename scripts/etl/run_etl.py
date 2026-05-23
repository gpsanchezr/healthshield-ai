"""scripts/etl/run_etl.py

Ejecuta el ETL vía el pipeline del backend.

Uso (ejemplo):
  python scripts/etl/run_etl.py --file datasets/clinical_data_v1.0_raw.xlsx

Si no se indica --file, intenta usar el dataset por defecto del README.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import os


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run ETL (extract -> transform -> load)")
    p.add_argument(
        "--file",
        type=str,
        default="datasets/clinical_data_v1.0_raw.xlsx",
        help="Ruta al archivo fuente (csv/xlsx). Por defecto: datasets/clinical_data_v1.0_raw.xlsx",
    )
    p.add_argument(
        "--tipo",
        type=str,
        default="automatico",
        help="Tipo de ejecución: manual/automatico/simulacion",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    file_path = (repo_root / args.file).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo fuente: {file_path}")

    # Ajusta entorno para que Django pueda inicializarse desde scripts.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    os.environ.setdefault("PYTHONPATH", str(repo_root / "backend"))

    import django

    django.setup()

    from apps.etl.pipeline import ETLPipeline

    pipeline = ETLPipeline(usuario=None, tipo=args.tipo)
    result = pipeline.run(source_path=str(file_path))

    print("ETL finalizado:")
    print(result)


if __name__ == "__main__":
    main()

