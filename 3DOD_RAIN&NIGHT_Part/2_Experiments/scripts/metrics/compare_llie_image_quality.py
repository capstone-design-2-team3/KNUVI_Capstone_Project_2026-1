"""
LLIE 4 conditions × image quality metrics (numerical output).

Compares Original / CLAHE / EnlightenGAN / Zero-DCE images on:
  - 7 image_quality metrics from feature_utils (luminance, rms_contrast, entropy,
    underexp_ratio, laplacian_var, noise_est, illum_uniformity)
  - BRISQUE score (외부 IQA; libsvm 환경 의존 — 실패 시 NaN)

Output: CSV with mean / std per condition.
"""
import os
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from brisque import BRISQUE

from feature_utils import image_quality, IMG_KEYS

BASE = Path('/home/knuvi/Undergraduate/kyungjin')
DIRS = {
    'Original':     BASE / 'LLIE_module/Zero-DCE/Zero-DCE++/data/test_data/night',
    'CLAHE':        BASE / 'dataset/LLIE_images_CLAHE',
    'EnlightenGAN': BASE / 'dataset/LLIE_images_EnlightenGAN',
    'Zero-DCE':     BASE / 'dataset/LLIE_images_ZeroDCE',
}
OUT_CSV = BASE / 'analysis/outputs/llie_image_quality.csv'

brisq_obj = BRISQUE(url=False)
_brisque_error_printed = False


def calc_brisque(img_path: Path) -> float:
    global _brisque_error_printed
    try:
        img = cv2.imread(str(img_path))
        return brisq_obj.score(img)
    except Exception as e:
        if not _brisque_error_printed:
            print(f"\n⚠️ [BRISQUE 실패] {e}")
            print("리눅스 환경 libsvm 충돌 가능성. 해당 지표는 NaN 처리합니다.\n")
            _brisque_error_printed = True
        return np.nan


def build_lookup(directory: Path) -> dict:
    """Map {original_basename_no_ext: full_path} for LLIE folders that prefix outputs."""
    result = {}
    for f in os.listdir(directory):
        name_no_ext = os.path.splitext(f)[0]
        key = name_no_ext.split('__', 1)[-1] if '__' in name_no_ext else name_no_ext
        result[key] = directory / f
    return result


orig_files = sorted([
    f for f in os.listdir(DIRS['Original'])
    if f.endswith(('.jpg', '.png')) and 'CAM_FRONT' in f and 'LEFT' not in f and 'RIGHT' not in f
])
print(f"총 {len(orig_files)}장 평가 시작 (BRISQUE 연산으로 시간이 다소 소요됩니다)...")

lookups = {cond: build_lookup(d) for cond, d in DIRS.items() if cond != 'Original'}


def find_path(cond: str, base_name: str) -> Path:
    if cond == 'Original':
        return DIRS['Original'] / base_name
    key = os.path.splitext(base_name)[0]
    return lookups[cond].get(key)


records = []
for i, base_name in enumerate(orig_files):
    for cond in DIRS:
        p = find_path(cond, base_name)
        if p is None or not p.exists():
            continue
        iq = image_quality(p)
        rec = {'Filename': base_name, 'Condition': cond}
        rec.update(iq)
        rec['BRISQUE'] = calc_brisque(p)
        records.append(rec)

    if (i + 1) % 50 == 0:
        print(f"  진행 중... {i + 1} / {len(orig_files)}")

df = pd.DataFrame(records)

cols = IMG_KEYS + ['BRISQUE']
table = df.groupby('Condition')[cols].agg(['mean', 'std'])

print("\n" + "=" * 100)
print(" LLIE Conditions × Image Quality Metrics (mean / std)")
print("=" * 100)
print(table.to_string())

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
table.to_csv(OUT_CSV)
print(f"\nCSV saved: {OUT_CSV}")
