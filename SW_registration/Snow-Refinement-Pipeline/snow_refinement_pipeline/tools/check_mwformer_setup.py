from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_utils import list_images
from utils.manifest_utils import now_iso


def check_mwformer_setup(
    input_dir: Path | str,
    mwformer_repo: Path | str,
    backbone_path: Path | str,
    style_filter_path: Path | str,
) -> dict:
    input_dir = Path(input_dir)
    mwformer_repo = Path(mwformer_repo)
    backbone_path = Path(backbone_path)
    style_filter_path = Path(style_filter_path)

    result = {
        "software": "Snow Image Refinement Pipeline for 3DGS Reconstruction",
        "step": "check_mwformer_setup",
        "checked_at": now_iso(),
        "input_dir": str(input_dir),
        "mwformer_repo": str(mwformer_repo),
        "backbone_path": str(backbone_path),
        "style_filter_path": str(style_filter_path),
        "checks": {},
        "errors": [],
        "warnings": [],
        "status": "fail",
    }

    result["checks"]["input_dir_exists"] = input_dir.exists() and input_dir.is_dir()
    result["checks"]["num_input_images"] = len(list_images(input_dir))

    result["checks"]["mwformer_repo_exists"] = mwformer_repo.exists() and mwformer_repo.is_dir()
    result["checks"]["backbone_exists"] = backbone_path.exists() and backbone_path.is_file()
    result["checks"]["style_filter_exists"] = style_filter_path.exists() and style_filter_path.is_file()

    required_repo_files = [
        mwformer_repo / "model" / "EncDec.py",
        mwformer_repo / "model" / "style_filter64.py",
    ]
    result["checks"]["required_repo_files"] = {
        str(p): p.exists() for p in required_repo_files
    }

    if not result["checks"]["input_dir_exists"]:
        result["errors"].append("Input directory does not exist.")

    if result["checks"]["num_input_images"] == 0:
        result["errors"].append("No input images found.")

    if not result["checks"]["mwformer_repo_exists"]:
        result["errors"].append("MWFormer repository directory does not exist.")

    missing_repo_files = [
        str(p) for p in required_repo_files if not p.exists()
    ]
    if missing_repo_files:
        result["errors"].append(f"Missing MWFormer repo files: {missing_repo_files}")

    if not result["checks"]["backbone_exists"]:
        result["errors"].append("Backbone weight file does not exist.")

    if not result["checks"]["style_filter_exists"]:
        result["errors"].append("Style filter weight file does not exist.")

    try:
        import torch
        result["checks"]["torch_import"] = True
        result["checks"]["torch_version"] = torch.__version__
        result["checks"]["cuda_available"] = torch.cuda.is_available()
        result["checks"]["cuda_device_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            result["checks"]["cuda_device_name"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        result["checks"]["torch_import"] = False
        result["errors"].append(f"Failed to import torch: {exc}")

    try:
        import torchvision
        result["checks"]["torchvision_import"] = True
        result["checks"]["torchvision_version"] = torchvision.__version__
    except Exception as exc:
        result["checks"]["torchvision_import"] = False
        result["errors"].append(f"Failed to import torchvision: {exc}")

    try:
        import timm
        result["checks"]["timm_import"] = True
        result["checks"]["timm_version"] = getattr(timm, "__version__", "unknown")
    except Exception as exc:
        result["checks"]["timm_import"] = False
        result["warnings"].append(f"Failed to import timm: {exc}")

    if result["checks"]["mwformer_repo_exists"]:
        sys.path.insert(0, str(mwformer_repo))
        try:
            from model.EncDec import Network_top
            from model.style_filter64 import StyleFilter_Top
            result["checks"]["mwformer_module_import"] = True
            result["checks"]["mwformer_classes"] = [
                Network_top.__name__,
                StyleFilter_Top.__name__,
            ]
        except Exception as exc:
            result["checks"]["mwformer_module_import"] = False
            result["errors"].append(f"Failed to import MWFormer modules: {exc}")

    result["status"] = "success" if not result["errors"] else "fail"
    return result


def main():
    parser = argparse.ArgumentParser(description="Check MWFormer setup before inference.")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--mwformer_repo", required=True)
    parser.add_argument("--backbone_path", required=True)
    parser.add_argument("--style_filter_path", required=True)
    args = parser.parse_args()

    result = check_mwformer_setup(
        input_dir=args.input_dir,
        mwformer_repo=args.mwformer_repo,
        backbone_path=args.backbone_path,
        style_filter_path=args.style_filter_path,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
