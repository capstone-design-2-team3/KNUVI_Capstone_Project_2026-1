from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS = {
    "snow_root": "data/snow",
    "output_root": "data/de_snow",
    "raw_output_root": "outputs/mwformer_raw",
    "mwformer_repo": "",
    "backbone_path": "",
    "style_filter_path": "",
    "device": "auto",
    "batch_size": 1,
    "num_workers": 0,
    "max_side": 1024,
    "size_multiple": 16,
}


def load_settings(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
    except Exception:
        return DEFAULT_SETTINGS.copy()

    settings = DEFAULT_SETTINGS.copy()
    settings.update(loaded)
    return settings


def save_settings(path: str | Path, settings: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
