from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.collect_outputs import collect_outputs
from tools.run_mwformer_inference import run_mwformer_inference
from tools.validate_input import validate_input_dir
from utils.file_utils import ensure_dir, infer_scene_name, list_images
from utils.logging_utils import setup_logger
from utils.manifest_utils import now_iso, save_json


def run_refinement_pipeline(
    input_dir: Path | str,
    output_dir: Path | str,
    mwformer_repo: Path | str,
    backbone_path: Path | str,
    style_filter_path: Path | str,
    raw_output_dir: Path | str | None = None,
    manifest_path: Path | str | None = None,
    log_path: Path | str | None = None,
    device: str = "auto",
    batch_size: int = 1,
    num_workers: int = 0,
    max_side: int | None = 1024,
    size_multiple: int = 16,
    overwrite: bool = True,
    skip_mwformer: bool = False,
) -> dict:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    mwformer_repo = Path(mwformer_repo)
    backbone_path = Path(backbone_path)
    style_filter_path = Path(style_filter_path)

    scene = infer_scene_name(input_dir)

    if raw_output_dir is None:
        raw_output_dir = PROJECT_ROOT / "outputs" / "mwformer_raw" / scene
    else:
        raw_output_dir = Path(raw_output_dir)

    if manifest_path is None:
        manifest_path = PROJECT_ROOT / "outputs" / "manifests" / f"{scene}_refinement_manifest.json"
    else:
        manifest_path = Path(manifest_path)

    if log_path is None:
        log_path = PROJECT_ROOT / "outputs" / "logs" / f"{scene}_refinement.log"
    else:
        log_path = Path(log_path)

    logger = setup_logger(log_path)

    final_manifest = {
        "software": "Snow Image Refinement Pipeline for 3DGS Reconstruction",
        "version": "0.3.0",
        "scene": scene,
        "input_condition": "snow",
        "output_condition": "de_snow",
        "external_model": "MWFormer",
        "input_dir": str(input_dir),
        "raw_output_dir": str(raw_output_dir),
        "output_dir": str(output_dir),
        "mwformer_repo": str(mwformer_repo),
        "backbone_path": str(backbone_path),
        "style_filter_path": str(style_filter_path),
        "device": device,
        "batch_size": batch_size,
        "num_workers": num_workers,
        "max_side": max_side,
        "size_multiple": size_multiple,
        "skip_mwformer": skip_mwformer,
        "started_at": now_iso(),
        "finished_at": None,
        "validate_input": None,
        "mwformer_inference": None,
        "collect_outputs": None,
        "num_input_images": 0,
        "num_output_images": 0,
        "status": "fail",
        "errors": [],
        "warnings": [],
    }

    try:
        logger.info("Step 1/3: validating input folder")
        validate_result = validate_input_dir(input_dir=input_dir, min_images=1)
        final_manifest["validate_input"] = validate_result

        if validate_result["status"] != "success":
            raise RuntimeError(f"Input validation failed: {validate_result['errors']}")

        final_manifest["num_input_images"] = validate_result["num_images"]

        if not skip_mwformer:
            logger.info("Step 2/3: running external MWFormer inference")
            inference_result = run_mwformer_inference(
                input_dir=input_dir,
                raw_output_dir=raw_output_dir,
                mwformer_repo=mwformer_repo,
                backbone_path=backbone_path,
                style_filter_path=style_filter_path,
                device=device,
                batch_size=batch_size,
                num_workers=num_workers,
                max_side=max_side,
                size_multiple=size_multiple,
                overwrite=overwrite,
            )
            final_manifest["mwformer_inference"] = inference_result

            if inference_result["status"] != "success":
                raise RuntimeError(
                    f"MWFormer inference failed: {inference_result['errors']}"
                )
        else:
            logger.info("Step 2/3: skipping MWFormer inference; using existing raw outputs")
            final_manifest["mwformer_inference"] = {
                "status": "skipped",
                "reason": "skip_mwformer=True",
                "raw_output_dir": str(raw_output_dir),
            }

        logger.info("Step 3/3: collecting outputs into LongSplat/3DGS input structure")
        collect_result = collect_outputs(
            input_dir=input_dir,
            raw_output_dir=raw_output_dir,
            output_dir=output_dir,
            overwrite=overwrite,
            strict_count=True,
            recursive_raw_search=True,
        )
        final_manifest["collect_outputs"] = collect_result

        if collect_result["status"] != "success":
            raise RuntimeError(f"Output collection failed: {collect_result['errors']}")

        final_manifest["num_output_images"] = len(list_images(output_dir))
        final_manifest["warnings"].extend(validate_result.get("warnings", []))
        final_manifest["warnings"].extend(collect_result.get("warnings", []))

        if final_manifest["num_input_images"] != final_manifest["num_output_images"]:
            raise RuntimeError(
                f"Final count mismatch: input={final_manifest['num_input_images']}, "
                f"output={final_manifest['num_output_images']}"
            )

        final_manifest["status"] = "success"
        logger.info("Refinement pipeline completed successfully")

    except Exception as exc:
        final_manifest["errors"].append(str(exc))
        final_manifest["status"] = "fail"
        logger.error(str(exc))

    final_manifest["finished_at"] = now_iso()
    ensure_dir(Path(manifest_path).parent)
    save_json(final_manifest, manifest_path)
    logger.info(f"Manifest saved: {manifest_path}")

    return final_manifest


def main():
    parser = argparse.ArgumentParser(
        description="Run full snow image refinement pipeline for 3DGS reconstruction."
    )
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--mwformer_repo", required=True)
    parser.add_argument("--backbone_path", required=True)
    parser.add_argument("--style_filter_path", required=True)
    parser.add_argument("--raw_output_dir", default=None)
    parser.add_argument("--manifest_path", default=None)
    parser.add_argument("--log_path", default=None)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--max_side", type=int, default=1024)
    parser.add_argument("--size_multiple", type=int, default=16)
    parser.add_argument("--no_overwrite", action="store_true")
    parser.add_argument(
        "--skip_mwformer",
        action="store_true",
        help="Skip MWFormer execution and only collect existing raw outputs. Useful for testing.",
    )
    args = parser.parse_args()

    result = run_refinement_pipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        mwformer_repo=args.mwformer_repo,
        backbone_path=args.backbone_path,
        style_filter_path=args.style_filter_path,
        raw_output_dir=args.raw_output_dir,
        manifest_path=args.manifest_path,
        log_path=args.log_path,
        device=args.device,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        max_side=args.max_side,
        size_multiple=args.size_multiple,
        overwrite=not args.no_overwrite,
        skip_mwformer=args.skip_mwformer,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
