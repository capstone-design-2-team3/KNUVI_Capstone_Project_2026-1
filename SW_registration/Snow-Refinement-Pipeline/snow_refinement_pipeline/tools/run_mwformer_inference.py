from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.file_utils import SUPPORTED_IMAGE_EXTENSIONS, ensure_dir, list_images
from utils.manifest_utils import now_iso, save_json


def _import_mwformer_modules(mwformer_repo: Path):
    if not mwformer_repo.exists():
        raise FileNotFoundError(f"MWFormer repository does not exist: {mwformer_repo}")

    sys.path.insert(0, str(mwformer_repo))

    try:
        from model.EncDec import Network_top
        from model.style_filter64 import StyleFilter_Top
    except Exception as exc:
        raise ImportError(
            "Failed to import MWFormer modules. "
            "Check whether the original MWFormer repository is placed under "
            f"{mwformer_repo} and whether its dependencies are installed."
        ) from exc

    return Network_top, StyleFilter_Top


def _load_clean_state_dict(model, ckpt_path: Path):
    import torch

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Weight file does not exist: {ckpt_path}")

    ckpt = torch.load(str(ckpt_path), map_location="cpu")

    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        ckpt = ckpt["state_dict"]

    if isinstance(ckpt, dict):
        ckpt = {k.replace("module.", ""): v for k, v in ckpt.items()}

    model.load_state_dict(ckpt, strict=True)
    return model


def _resize_like_mwformer_repo(input_img, max_side: Optional[int] = 1024, size_multiple: int = 16):
    import math
    from PIL import Image

    width, height = input_img.size
    new_w, new_h = width, height

    if max_side is not None:
        if new_h > new_w and new_h > max_side:
            new_w = int(math.ceil(new_w * max_side / new_h))
            new_h = max_side
        elif new_h <= new_w and new_w > max_side:
            new_h = int(math.ceil(new_h * max_side / new_w))
            new_w = max_side

    if size_multiple and size_multiple > 1:
        new_w = int(size_multiple * math.ceil(new_w / size_multiple))
        new_h = int(size_multiple * math.ceil(new_h / size_multiple))

    if (new_w, new_h) != (width, height):
        input_img = input_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return input_img


class MWFormerInputDataset:
    def __init__(
        self,
        input_dir: Path,
        max_side: Optional[int] = 1024,
        size_multiple: int = 16,
    ):
        from torchvision.transforms import Compose, Normalize, ToTensor

        self.input_dir = Path(input_dir)
        self.image_paths = list_images(
            self.input_dir,
            extensions=SUPPORTED_IMAGE_EXTENSIONS,
            recursive=False,
        )
        self.max_side = max_side
        self.size_multiple = size_multiple

        self.transform = Compose([
            ToTensor(),
            Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        from PIL import Image

        img_path = self.image_paths[idx]
        input_img = Image.open(img_path).convert("RGB")
        input_img = _resize_like_mwformer_repo(
            input_img,
            max_side=self.max_side,
            size_multiple=self.size_multiple,
        )
        input_tensor = self.transform(input_img)
        return input_tensor, img_path.name


def run_mwformer_inference(
    input_dir: Path | str,
    raw_output_dir: Path | str,
    mwformer_repo: Path | str,
    backbone_path: Path | str,
    style_filter_path: Path | str,
    device: str = "auto",
    batch_size: int = 1,
    num_workers: int = 0,
    max_side: Optional[int] = 1024,
    size_multiple: int = 16,
    overwrite: bool = True,
) -> dict:
    input_dir = Path(input_dir)
    raw_output_dir = Path(raw_output_dir)
    mwformer_repo = Path(mwformer_repo)
    backbone_path = Path(backbone_path)
    style_filter_path = Path(style_filter_path)

    result = {
        "software": "Snow Image Refinement Pipeline for 3DGS Reconstruction",
        "step": "run_mwformer_inference",
        "external_model": "MWFormer",
        "input_dir": str(input_dir),
        "raw_output_dir": str(raw_output_dir),
        "mwformer_repo": str(mwformer_repo),
        "backbone_path": str(backbone_path),
        "style_filter_path": str(style_filter_path),
        "device": device,
        "batch_size": batch_size,
        "num_workers": num_workers,
        "max_side": max_side,
        "size_multiple": size_multiple,
        "num_input_images": 0,
        "num_output_images": 0,
        "saved_files": [],
        "warnings": [],
        "errors": [],
        "started_at": now_iso(),
        "finished_at": None,
        "status": "fail",
    }

    try:
        import torch
        from torch.utils.data import DataLoader
        from torchvision.utils import save_image
        from tqdm import tqdm

        input_images = list_images(input_dir, SUPPORTED_IMAGE_EXTENSIONS, recursive=False)
        result["num_input_images"] = len(input_images)

        if len(input_images) == 0:
            raise RuntimeError(f"No input images found: {input_dir}")

        if device == "auto":
            device_obj = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device_obj = torch.device(device)

        Network_top, StyleFilter_Top = _import_mwformer_modules(mwformer_repo)

        net = Network_top().to(device_obj)
        style_filter = StyleFilter_Top().to(device_obj)

        net = _load_clean_state_dict(net, backbone_path).to(device_obj)
        style_filter = _load_clean_state_dict(style_filter, style_filter_path).to(device_obj)

        net.eval()
        style_filter.eval()

        dataset = MWFormerInputDataset(
            input_dir=input_dir,
            max_side=max_side,
            size_multiple=size_multiple,
        )
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        )

        ensure_dir(raw_output_dir)

        with torch.no_grad():
            for input_tensor, names in tqdm(loader, desc="MWFormer inference"):
                input_tensor = input_tensor.to(device_obj)
                feature_vec = style_filter(input_tensor)
                pred = net(input_tensor, feature_vec).clamp(0, 1)

                for i, name in enumerate(names):
                    save_path = raw_output_dir / name
                    if save_path.exists() and not overwrite:
                        raise FileExistsError(f"Output already exists: {save_path}")
                    save_image(pred[i], str(save_path))
                    result["saved_files"].append(str(save_path))

        output_images = list_images(raw_output_dir, SUPPORTED_IMAGE_EXTENSIONS, recursive=False)
        result["num_output_images"] = len(output_images)

        if result["num_output_images"] != result["num_input_images"]:
            result["warnings"].append(
                f"Output count differs from input count: "
                f"input={result['num_input_images']}, output={result['num_output_images']}"
            )

        result["status"] = "success"

    except Exception as exc:
        result["errors"].append(str(exc))
        result["status"] = "fail"

    result["finished_at"] = now_iso()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run external MWFormer inference for snow image refinement."
    )
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--raw_output_dir", required=True)
    parser.add_argument("--mwformer_repo", required=True)
    parser.add_argument("--backbone_path", required=True)
    parser.add_argument("--style_filter_path", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--max_side", type=int, default=1024)
    parser.add_argument("--size_multiple", type=int, default=16)
    parser.add_argument("--no_overwrite", action="store_true")
    parser.add_argument("--manifest_path", default=None)
    args = parser.parse_args()

    result = run_mwformer_inference(
        input_dir=args.input_dir,
        raw_output_dir=args.raw_output_dir,
        mwformer_repo=args.mwformer_repo,
        backbone_path=args.backbone_path,
        style_filter_path=args.style_filter_path,
        device=args.device,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        max_side=args.max_side,
        size_multiple=args.size_multiple,
        overwrite=not args.no_overwrite,
    )

    if args.manifest_path:
        save_json(result, args.manifest_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
