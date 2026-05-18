from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.file_utils import ensure_dir


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def save_json(data: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    ensure_dir(output_path.parent)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path
