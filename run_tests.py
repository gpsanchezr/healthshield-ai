"""Run the backend test suite for HealthShield AI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    backend_dir = repo_root / "backend"

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    env.setdefault("PYTHONPATH", str(backend_dir))

    cmd = [sys.executable, "-m", "pytest", "-q"] + sys.argv[1:]
    return subprocess.call(cmd, cwd=str(repo_root), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
