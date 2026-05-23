"""scripts/ml/train_model.py

Entrena el modelo ML vía management command.

Uso:
  python scripts/ml/train_model.py --algorithm random_forest
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train ML model")
    p.add_argument(
        "--algorithm",
        type=str,
        default="random_forest",
        help="Algoritmo a entrenar (default: random_forest)",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    os.environ.setdefault("PYTHONPATH", str(repo_root / "backend"))

    import django

    django.setup()

    from django.core.management import call_command

    call_command("train_model", algorithm=args.algorithm)


if __name__ == "__main__":
    main()

