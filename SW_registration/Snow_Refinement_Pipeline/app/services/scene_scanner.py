from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


@dataclass
class SceneInfo:
    name: str
    input_dir: Path
    image_count: int


def count_images(input_dir: Path) -> int:
    if not input_dir.exists() or not input_dir.is_dir():
        return 0

    return sum(
        1
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def scan_scenes(snow_root: str | Path) -> list[SceneInfo]:
    # Expected structure:
    # snow_root/grass/input/*.png
    # snow_root/pillar/input/*.png
    # snow_root/road/input/*.png
    snow_root = Path(snow_root)
    scenes: list[SceneInfo] = []

    if not snow_root.exists() or not snow_root.is_dir():
        return scenes

    for scene_dir in sorted([p for p in snow_root.iterdir() if p.is_dir()]):
        input_dir = scene_dir / "input"
        image_count = count_images(input_dir)

        if input_dir.exists() and image_count > 0:
            scenes.append(SceneInfo(scene_dir.name, input_dir, image_count))

    return scenes
