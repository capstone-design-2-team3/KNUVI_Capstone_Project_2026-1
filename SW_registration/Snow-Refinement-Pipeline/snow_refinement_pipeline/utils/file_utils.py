from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Iterable, List, Sequence

SUPPORTED_IMAGE_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
)


def natural_key(path: Path | str):
    name = Path(path).name
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", name)
    ]


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_images(
    directory: Path | str,
    extensions: Sequence[str] = SUPPORTED_IMAGE_EXTENSIONS,
    recursive: bool = False,
) -> List[Path]:
    directory = Path(directory)

    if not directory.exists():
        return []

    exts = {ext.lower() for ext in extensions}
    iterator: Iterable[Path] = directory.rglob("*") if recursive else directory.iterdir()

    files = [
        p for p in iterator
        if p.is_file() and p.suffix.lower() in exts
    ]

    return sorted(files, key=natural_key)


def copy_file(src: Path | str, dst: Path | str, overwrite: bool = False) -> Path:
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file does not exist: {src}")

    if dst.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {dst}")

    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    return dst


def infer_scene_name(input_dir: Path | str) -> str:
    p = Path(input_dir)
    return p.parent.name if p.name == "input" else p.name
