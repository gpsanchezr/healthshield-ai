"""scripts/test/run_pytest.py

Wrapper para ejecutar pytest de backend con configuración consistente.

Uso:
  python scripts/test/run_pytest.py

Nota:
  Este wrapper asume que el entorno ya tiene dependencias instaladas.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"

    env = os.environ.copy()
    # Asegura que Django settings se inicialicen si algún test las necesita.
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    env.setdefault("PYTHONPATH", str(backend_dir))

    cmd = [sys.executable, "-m", "pytest", "-q"]
    subprocess.check_call(cmd, cwd=str(backend_dir), env=env)


if __name__ == "__main__":
    main()

