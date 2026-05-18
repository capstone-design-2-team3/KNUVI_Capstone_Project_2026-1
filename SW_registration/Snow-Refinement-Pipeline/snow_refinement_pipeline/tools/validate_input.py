from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_utils import list_images, SUPPORTED_IMAGE_EXTENSIONS
from utils.image_utils import get_image_size, is_readable_image


def validate_input_dir(input_dir: Path | str, min_images: int = 1, strict_numeric: bool = False) -> dict:
    input_dir = Path(input_dir)

    result = {
        "input_dir": str(input_dir),
        "exists": input_dir.exists(),
        "is_dir": input_dir.is_dir(),
        "num_images": 0,
        "image_files": [],
        "first_image_size": None,
        "warnings": [],
        "errors": [],
        "status": "fail",
    }

    if not input_dir.exists():
        result["errors"].append("Input directory does not exist.")
        return result

    if not input_dir.is_dir():
        result["errors"].append("Input path is not a directory.")
        return result

    images = list_images(input_dir, SUPPORTED_IMAGE_EXTENSIONS, recursive=False)

    result["num_images"] = len(images)
    result["image_files"] = [p.name for p in images]

    if len(images) < min_images:
        result["errors"].append(
            f"Not enough images. Required >= {min_images}, found {len(images)}."
        )
        return result

    unreadable = [p.name for p in images if not is_readable_image(p)]
    if unreadable:
        result["errors"].append(f"Unreadable image files: {unreadable[:10]}")
        return result

    result["first_image_size"] = get_image_size(images[0])

    stems = [p.stem for p in images]

    non_numeric = [s for s in stems if not re.fullmatch(r"\d+", s)]
    if non_numeric:
        msg = f"Non-numeric filenames exist: {non_numeric[:10]}"
        if strict_numeric:
            result["errors"].append(msg)
            return result
        result["warnings"].append(msg)

    numeric_stems = [int(s) for s in stems if re.fullmatch(r"\d+", s)]
    if numeric_stems:
        missing = sorted(
            set(range(min(numeric_stems), max(numeric_stems) + 1)) - set(numeric_stems)
        )
        if missing:
            result["warnings"].append(f"Numeric filename gaps exist: {missing[:20]}")

    result["status"] = "success" if not result["errors"] else "fail"
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate snow image input folder.")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--min_images", type=int, default=1)
    parser.add_argument("--strict_numeric", action="store_true")
    args = parser.parse_args()

    result = validate_input_dir(args.input_dir, args.min_images, args.strict_numeric)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    raise SystemExit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()