#!/usr/bin/env python
"""Convenience entry point that forwards commands to Django's manage.py."""

from pathlib import Path
import subprocess
import sys


def main() -> None:
    project_dir = Path(__file__).resolve().parent / "simulador_operacional"
    manage_py = project_dir / "manage.py"
    cmd = [sys.executable, str(manage_py), *sys.argv[1:]]
    subprocess.run(cmd, check=True, cwd=project_dir)


if __name__ == "__main__":
    main()
