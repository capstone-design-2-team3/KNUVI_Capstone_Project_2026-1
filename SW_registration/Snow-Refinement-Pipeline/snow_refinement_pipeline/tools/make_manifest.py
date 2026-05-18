from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_utils import infer_scene_name, list_images
from utils.manifest_utils import now_iso, save_json


def make_manifest(
    input_dir: Path | str,
    output_dir: Path | str,
    manifest_path: Path | str,
    model_name: str = "MWFormer",
    weight_path: Path | str | None = None,
    status: str = "success",
) -> dict:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    manifest = {
        "software": "Snow Image Refinement Pipeline for 3DGS Reconstruction",
        "scene": infer_scene_name(input_dir),
        "input_condition": "snow",
        "output_condition": "de_snow",
        "external_model": model_name,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "weight_path": str(weight_path) if weight_path else None,
        "num_input_images": len(list_images(input_dir)),
        "num_output_images": len(list_images(output_dir)),
        "created_at": now_iso(),
        "status": status,
    }

    save_json(manifest, manifest_path)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Create refinement manifest JSON.")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--manifest_path", required=True)
    parser.add_argument("--model_name", default="MWFormer")
    parser.add_argument("--weight_path", default=None)
    parser.add_argument("--status", default="success")
    args = parser.parse_args()

    manifest = make_manifest(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        manifest_path=args.manifest_path,
        model_name=args.model_name,
        weight_path=args.weight_path,
        status=args.status,
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
