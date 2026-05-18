from __future__ import annotations

import sys
from pathlib import Path

# Allow running both:
#   python -m app.main
# and:
#   python app\main.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.gui.main_window import run_app


if __name__ == "__main__":
    run_app()
