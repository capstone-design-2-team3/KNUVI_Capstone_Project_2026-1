from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_utils import (
    SUPPORTED_IMAGE_EXTENSIONS,
    copy_file,
    ensure_dir,
    infer_scene_name,
    list_images,
)
from utils.image_utils import is_readable_image
from utils.manifest_utils import now_iso, save_json


def collect_outputs(
    input_dir: Path | str,
    raw_output_dir: Path | str,
    output_dir: Path | str,
    overwrite: bool = False,
    strict_count: bool = True,
    recursive_raw_search: bool = True,
) -> dict:
    input_dir = Path(input_dir)
    raw_output_dir = Path(raw_output_dir)
    output_dir = Path(output_dir)

    result = {
        "software": "Snow Image Refinement Pipeline for 3DGS Reconstruction",
        "step": "collect_outputs",
        "scene": infer_scene_name(input_dir),
        "input_condition": "snow",
        "output_condition": "de_snow",
        "input_dir": str(input_dir),
        "raw_output_dir": str(raw_output_dir),
        "output_dir": str(output_dir),
        "num_input_images": 0,
        "num_raw_output_images": 0,
        "num_collected_images": 0,
        "copied_files": [],
        "warnings": [],
        "errors": [],
        "started_at": now_iso(),
        "finished_at": None,
        "status": "fail",
    }

    if not input_dir.exists():
        result["errors"].append("Input directory does not exist.")
        result["finished_at"] = now_iso()
        return result

    if not raw_output_dir.exists():
        result["errors"].append("Raw output directory does not exist.")
        result["finished_at"] = now_iso()
        return result

    input_images = list_images(input_dir, SUPPORTED_IMAGE_EXTENSIONS, recursive=False)
    raw_images = list_images(
        raw_output_dir,
        SUPPORTED_IMAGE_EXTENSIONS,
        recursive=recursive_raw_search,
    )

    result["num_input_images"] = len(input_images)
    result["num_raw_output_images"] = len(raw_images)

    if len(input_images) == 0:
        result["errors"].append("No input images found.")
        result["finished_at"] = now_iso()
        return result

    if len(raw_images) == 0:
        result["errors"].append("No raw output images found.")
        result["finished_at"] = now_iso()
        return result

    unreadable_outputs = [p.name for p in raw_images if not is_readable_image(p)]
    if unreadable_outputs:
        result["errors"].append(
            f"Unreadable raw output image files: {unreadable_outputs[:10]}"
        )
        result["finished_at"] = now_iso()
        return result

    if len(input_images) != len(raw_images):
        msg = (
            f"Input/output image count mismatch: "
            f"input={len(input_images)}, raw_output={len(raw_images)}"
        )
        if strict_count:
            result["errors"].append(msg)
            result["finished_at"] = now_iso()
            return result
        result["warnings"].append(msg)

    ensure_dir(output_dir)

    pair_count = min(len(input_images), len(raw_images))
    for input_image, raw_image in zip(input_images[:pair_count], raw_images[:pair_count]):
        target_path = output_dir / input_image.name
        copy_file(raw_image, target_path, overwrite=overwrite)
        result["copied_files"].append(
            {
                "source_raw_output": str(raw_image),
                "target_de_snow": str(target_path),
                "matched_input_name": input_image.name,
            }
        )

    collected_images = list_images(output_dir, SUPPORTED_IMAGE_EXTENSIONS, recursive=False)
    result["num_collected_images"] = len(collected_images)

    if result["num_collected_images"] != len(input_images):
        result["warnings"].append(
            f"Final collected image count differs from input count: "
            f"input={len(input_images)}, collected={result['num_collected_images']}"
        )

    result["finished_at"] = now_iso()
    result["status"] = "success" if not result["errors"] else "fail"
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Collect MWFormer raw outputs into LongSplat/3DGS input folder."
    )
    parser.add_argument("--input_dir", required=True, help="Original snow input folder.")
    parser.add_argument("--raw_output_dir", required=True, help="MWFormer raw output folder.")
    parser.add_argument("--output_dir", required=True, help="Final de_snow input folder.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--allow_count_mismatch",
        action="store_true",
        help="Allow copying min(input_count, output_count) images even when counts mismatch.",
    )
    parser.add_argument(
        "--no_recursive_raw_search",
        action="store_true",
        help="Search raw_output_dir only at the top level.",
    )
    parser.add_argument(
        "--manifest_path",
        default=None,
        help="Optional path to save collection result JSON.",
    )
    args = parser.parse_args()

    result = collect_outputs(
        input_dir=args.input_dir,
        raw_output_dir=args.raw_output_dir,
        output_dir=args.output_dir,
        overwrite=args.overwrite,
        strict_count=not args.allow_count_mismatch,
        recursive_raw_search=not args.no_recursive_raw_search,
    )

    if args.manifest_path:
        save_json(result, args.manifest_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
