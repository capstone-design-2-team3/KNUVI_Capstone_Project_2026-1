"""
표 3: 저조도 이미지 개선 기법 적용 전후 이미지 품질 및 탐지 성능 비교.

행:
  - 평균 밝기 (luminance)              ↑
  - 픽셀 강도 표준편차 (rms_contrast)  ↑
  - 노출 부족 픽셀 비율 (underexp_ratio) ↓
  - MoME mAP                            ↑
  - DeepInteraction mAP                 ↑
  - BEVFusion mAP                       ↑

열: Original / CLAHE / EnlightenGAN / Zero-DCE

이미지 품질은 야간 val 샘플(CAM_FRONT)의 4 조건 이미지에서 image_quality 평균.
mAP는 analyze_ap_difficulty.py가 생성한 ap_matrix.npy의 sample 축 평균.

요구 사전 파일:
  - ap_matrix.npy  ← analyze_ap_difficulty.py 먼저 실행
  - GT pkl (nuscenes_infos_val_night.pkl)
  - 4 조건 이미지 폴더
"""
import os
import csv
from pathlib import Path

import numpy as np
import pickle

from feature_utils import image_quality

BASE = Path('/home/knuvi/Undergraduate/kyungjin')
GT_PKL   = BASE / 'model/MoME/data/nuscenes/nuscenes_infos_val_night.pkl'
IMG_BASE = BASE / 'model/MoME'

COND_DIRS = {
    'Original':     None,  # gt_info['cams']['CAM_FRONT']['data_path'] 사용
    'CLAHE':        BASE / 'dataset/LLIE_images_CLAHE',
    'EnlightenGAN': BASE / 'dataset/LLIE_images_EnlightenGAN',
    'Zero-DCE':     BASE / 'dataset/LLIE_images_ZeroDCE',
}
COND_NAMES = list(COND_DIRS)

AP_NPY = BASE / 'analysis/outputs/ap_difficulty/ap_matrix.npy'
MODEL_NAMES = ['MoME', 'DeepInteraction', 'BEVFusion']

OUT_CSV = BASE / 'analysis/outputs/table3_llie_quality_and_map.csv'

IMG_METRICS = [
    ('luminance',      '평균 밝기 ↑'),
    ('rms_contrast',   '픽셀 강도 표준편차 ↑'),
    ('underexp_ratio', '노출 부족 픽셀 비율 ↓'),
]


def find_llie_image(cond_dir: Path, orig_basename: str) -> Path:
    """Original 파일명(확장자 제외)을 포함하는 LLIE 변환 이미지 경로 반환."""
    key = os.path.splitext(orig_basename)[0]
    for f in os.listdir(cond_dir):
        if key in f:
            return cond_dir / f
    return None


print("Loading GT pkl...")
with open(GT_PKL, 'rb') as f:
    gt_infos = pickle.load(f)['infos']
N = len(gt_infos)
print(f"  {N} samples")

print("\nComputing image quality across 4 LLIE conditions...")
img_metrics_collected = {cond: {k: [] for k, _ in IMG_METRICS} for cond in COND_NAMES}

for i, gt_info in enumerate(gt_infos):
    if i % 100 == 0:
        print(f"  [{i}/{N}]")
    orig_path = IMG_BASE / gt_info['cams']['CAM_FRONT']['data_path']
    orig_basename = os.path.basename(str(orig_path))

    for cond in COND_NAMES:
        if cond == 'Original':
            img_path = orig_path
        else:
            img_path = find_llie_image(COND_DIRS[cond], orig_basename)
            if img_path is None:
                continue
        iq = image_quality(img_path)
        for key, _ in IMG_METRICS:
            img_metrics_collected[cond][key].append(iq[key])

print("\nLoading ap_matrix.npy ...")
ap_matrix = np.load(AP_NPY)
assert ap_matrix.shape[1:] == (3, 4), f"unexpected shape {ap_matrix.shape}"

rows = []
for key, label in IMG_METRICS:
    vals = []
    for cond in COND_NAMES:
        arr = np.array(img_metrics_collected[cond][key], dtype=float)
        arr = arr[~np.isnan(arr)]
        vals.append(float(arr.mean()) if len(arr) else np.nan)
    rows.append((label, vals))

for mi, model in enumerate(MODEL_NAMES):
    vals = [float(np.nanmean(ap_matrix[:, mi, ci])) for ci in range(4)]
    rows.append((f"{model} mAP ↑", vals))

print("\n" + "=" * 100)
print(" 표 3: 저조도 이미지 개선 기법 적용 전후 이미지 품질 및 탐지 성능 비교")
print("=" * 100)
print(f"{'Metric':<28}" + "".join(f"{c:>16}" for c in COND_NAMES))
print("-" * 100)
for label, vals in rows:
    print(f"{label:<28}" + "".join(f"{v:>16.4f}" for v in vals))

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Metric'] + COND_NAMES)
    for label, vals in rows:
        writer.writerow([label] + [f'{v:.4f}' for v in vals])
print(f"\nCSV saved: {OUT_CSV}")
