from __future__ import annotations

import math
from pathlib import Path
from PIL import Image


def is_readable_image(path: Path | str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def get_image_size(path: Path | str) -> tuple[int, int]:
    with Image.open(path) as img:
        return img.size


def aligned_size(
    width: int,
    height: int,
    max_side: int | None = 1024,
    multiple: int = 16,
) -> tuple[int, int]:
    new_w, new_h = width, height

    if max_side is not None and max(width, height) > max_side:
        scale = max_side / float(max(width, height))
        new_w = int(math.ceil(width * scale))
        new_h = int(math.ceil(height * scale))

    if multiple and multiple > 1:
        new_w = int(multiple * math.ceil(new_w / multiple))
        new_h = int(multiple * math.ceil(new_h / multiple))

    return new_w, new_h