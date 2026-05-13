"""
AP-based difficulty analysis (numerical output only).

ap_matrix.npy 생성 또는 로드 후, 모델별 avg AP의 q25/q75로 Hard/Easy 분류하고
Hard vs Easy 그룹의 씬 통계(obj count, mean dist, lidar pts/obj) 차이를 검정.

ap_matrix.npy shape: (N, 3 models, 4 conditions)
  model:     MoME(0), DeepInteraction(1), BEVFusion(2)
  condition: Original(0), CLAHE(1), EnlightenGAN(2), Zero-DCE(3)
"""
import os
import numpy as np
from scipy.stats import mannwhitneyu

from feature_utils import (
    NUSCENES_CLASSES, compute_per_sample_ap, load_pkl,
)

BASE_DIR = '/home/knuvi/Undergraduate/kyungjin'
GT_PKL   = f'{BASE_DIR}/model/MoME/data/nuscenes/nuscenes_infos_val_night.pkl'
AP_NPY   = f'{BASE_DIR}/analysis/outputs/ap_difficulty/ap_matrix.npy'
OUT_DIR  = f'{BASE_DIR}/analysis/outputs/ap_difficulty'
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NAMES = ['MoME', 'DeepInteraction', 'BEVFusion']
COND_NAMES  = ['Original', 'CLAHE', 'EnlightenGAN', 'Zero-DCE']

PRED_PKLS = [
    [  # MoME
        f'{BASE_DIR}/model/MoME/results/night_results.pkl',
        f'{BASE_DIR}/model/MoME/results/night_clahe_results.pkl',
        f'{BASE_DIR}/model/MoME/results/night_enlighten_results.pkl',
        f'{BASE_DIR}/model/MoME/results/night_zerodce_results.pkl',
    ],
    [  # DeepInteraction
        f'{BASE_DIR}/model/DeepInteraction/results/night_results.pkl',
        f'{BASE_DIR}/model/DeepInteraction/results/night_clahe_results.pkl',
        f'{BASE_DIR}/model/DeepInteraction/results/night_egan_results.pkl',
        f'{BASE_DIR}/model/DeepInteraction/results/night_zerodce_results.pkl',
    ],
    [  # BEVFusion
        f'{BASE_DIR}/model/BEVFusion/results/night_results.pkl',
        f'{BASE_DIR}/model/BEVFusion/results/night_clahe_results.pkl',
        f'{BASE_DIR}/model/BEVFusion/results/night_egan_results.pkl',
        f'{BASE_DIR}/model/BEVFusion/results/night_zerodce_results.pkl',
    ],
]


print("Loading GT pkl...")
gt_infos = load_pkl(GT_PKL)['infos']
N = len(gt_infos)
print(f"  {N} samples")

if os.path.exists(AP_NPY):
    print(f"Loading cached ap_matrix from {AP_NPY}")
    ap_matrix = np.load(AP_NPY)
    print(f"  shape: {ap_matrix.shape}\n")
else:
    print(f"Computing per-sample AP matrix (N={N}, 3 models, 4 conditions)...")
    ap_matrix = np.full((N, 3, 4), np.nan)

    for mi, model in enumerate(MODEL_NAMES):
        for ci, cond in enumerate(COND_NAMES):
            path = PRED_PKLS[mi][ci]
            print(f"  [{model}] [{cond}] loading {os.path.basename(path)}")
            pred_list = load_pkl(path)
            ap_arr = compute_per_sample_ap(gt_infos, pred_list)
            ap_matrix[:, mi, ci] = ap_arr
            print(f"    mean AP = {np.nanmean(ap_arr):.4f}")

    np.save(AP_NPY, ap_matrix)
    print(f"\nSaved: {AP_NPY}\n")


def scene_stats(gt_info):
    gt_boxes  = np.array(gt_info['gt_boxes'])
    gt_names  = np.array(gt_info['gt_names'])
    lidar_pts = np.array(gt_info['num_lidar_pts'])
    valid = np.array([n in NUSCENES_CLASSES for n in gt_names])
    gt_boxes = gt_boxes[valid]; lidar_pts = lidar_pts[valid]
    n = len(gt_boxes)
    if n == 0:
        return 0, np.nan, np.nan
    dists = np.sqrt((gt_boxes[:, :2] ** 2).sum(axis=1))
    return n, float(dists.mean()), float(lidar_pts.mean())

sc_nobj, sc_dist, sc_lidar = [], [], []
for info in gt_infos:
    n, d, l = scene_stats(info)
    sc_nobj.append(n); sc_dist.append(d); sc_lidar.append(l)
sc_nobj  = np.array(sc_nobj,  dtype=float)
sc_dist  = np.array(sc_dist,  dtype=float)
sc_lidar = np.array(sc_lidar, dtype=float)

METRIC_NAMES = ['Obj Count', 'Mean Dist (m)', 'Lidar Pts/Obj']
scene_metrics = {'Obj Count': sc_nobj, 'Mean Dist (m)': sc_dist, 'Lidar Pts/Obj': sc_lidar}

print("\n" + "=" * 80)
print("AP-based Hard/Easy classification")
print("=" * 80)

print(f"\n{'Model':<20} {'Metric':<22} {'Hard mean±std':<26} {'Easy mean±std':<26} {'p'}")
print("-" * 80)

results = []

for mi, model in enumerate(MODEL_NAMES):
    avg_ap = np.nanmean(ap_matrix[:, mi, :], axis=1)
    q25_ap = np.nanpercentile(avg_ap, 25)
    q75_ap = np.nanpercentile(avg_ap, 75)
    hard_mask = avg_ap <= q25_ap
    easy_mask = avg_ap >= q75_ap
    n_hard = int(hard_mask.sum())
    n_easy = int(easy_mask.sum())
    n_middle = N - n_hard - n_easy

    overall_ap_mean = float(np.nanmean(avg_ap))
    hard_ap_mean    = float(np.nanmean(avg_ap[hard_mask]))
    easy_ap_mean    = float(np.nanmean(avg_ap[easy_mask]))

    print(f"\n[{model}]  AP q25={q25_ap:.4f}  q75={q75_ap:.4f}")
    print(f"  Hard  : n={n_hard:>3} ({100*n_hard/N:4.1f}%)  mean AP={hard_ap_mean:.4f}")
    print(f"  Middle: n={n_middle:>3} ({100*n_middle/N:4.1f}%)")
    print(f"  Easy  : n={n_easy:>3} ({100*n_easy/N:4.1f}%)  mean AP={easy_ap_mean:.4f}")
    print(f"  Overall (all {N}):              mean AP={overall_ap_mean:.4f}  "
          f"median={np.nanmedian(avg_ap):.4f}  std={np.nanstd(avg_ap):.4f}")
    print()

    row = {'model': model, 'q25': q25_ap, 'q75': q75_ap,
           'n_hard': n_hard, 'n_easy': n_easy, 'n_middle': n_middle}

    for mname in METRIC_NAMES:
        arr = scene_metrics[mname]
        h = arr[hard_mask]; h = h[~np.isnan(h)]
        e = arr[easy_mask]; e = e[~np.isnan(e)]
        _, p = mannwhitneyu(h, e, alternative='two-sided')
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
        print(f"  {mname:<22} Hard {h.mean():.3f}±{h.std():.3f}    "
              f"Easy {e.mean():.3f}±{e.std():.3f}    p={p:.2e} {sig}")
        row[mname] = {'hard_mean': h.mean(), 'hard_std': h.std(),
                      'easy_mean': e.mean(), 'easy_std': e.std(), 'p': p}
    results.append(row)


ap_means = np.array([
    [np.nanmean(ap_matrix[:, mi, ci]) for ci in range(4)]
    for mi in range(3)
])

print("\n" + "=" * 80)
print("Mean Per-sample AP per Model × Condition")
print("=" * 80)
print(f"  {'Model':<18} " + " ".join(f"{c:>13}" for c in COND_NAMES))
for mi, model in enumerate(MODEL_NAMES):
    print(f"  {model:<18} " + " ".join(f"{ap_means[mi, ci]:>13.4f}" for ci in range(4)))

print("\n" + "=" * 80)
print("FINAL SUMMARY: AP-based Hard/Easy group sizes")
print("=" * 80)
print(f"{'Model':<20} {'Hard n(%)':>12} {'Easy n(%)':>12} {'Middle n(%)':>13}")
print("-" * 60)
for row in results:
    print(f"  {row['model']:<18} "
          f"{row['n_hard']:>4}({100*row['n_hard']/N:4.1f}%) "
          f"{row['n_easy']:>4}({100*row['n_easy']/N:4.1f}%) "
          f"{row['n_middle']:>5}({100*row['n_middle']/N:4.1f}%)")
