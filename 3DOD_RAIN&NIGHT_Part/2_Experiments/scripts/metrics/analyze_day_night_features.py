"""
주간 vs 야간 특성 비교

그룹:
  Night           : 야간 602 샘플
  Day (all)       : 전체 val(6019) 중 야간 제외 (5417 샘플)
  Day (scene-matched) : 야간과 동일한 15개 씬에 속하는 주간 샘플

지표:
  이미지 품질 : luminance, rms_contrast, entropy, underexp_ratio, laplacian_var, noise_est, illum_uniformity
  씬 특징    : total_lidar_pts, mean_dist, mean_pts_per_obj, small_obj_ratio, gt_obj_count
"""
import json, pickle, numpy as np
from pathlib import Path
from scipy.stats import kruskal

from feature_utils import image_quality, lidar_quality, IMG_KEYS, SCN_KEYS

BASE      = Path('/home/knuvi/Undergraduate/kyungjin')
NIGHT_PKL = BASE / 'model/MoME/data/nuscenes/nuscenes_infos_val_night.pkl'
VAL_PKL   = BASE / 'model/MoME/data/nuscenes/nuscenes_infos_val.pkl'
IMG_BASE  = BASE / 'model/MoME'
META_DIR  = BASE / 'model/MoME/data/nuscenes/v1.0-trainval'
OUT_CSV   = BASE / 'analysis/outputs/day_night_features.csv'


def compute_features(infos, label):
    feats = []
    for i, gt_info in enumerate(infos):
        if i % 200 == 0:
            print(f"  {label} [{i}/{len(infos)}]")
        img_path = IMG_BASE / gt_info['cams']['CAM_FRONT']['data_path']
        iq = image_quality(img_path)
        lq = lidar_quality(gt_info)
        feats.append([iq[k] for k in IMG_KEYS] + [lq[k] for k in SCN_KEYS])
    return np.array(feats, dtype=float)


def main():
    # ── 샘플 분류 ────────────────────────────────────────────────────────
    print("Loading pkls...")
    with open(NIGHT_PKL, 'rb') as f:
        night_infos = pickle.load(f)['infos']
    with open(VAL_PKL, 'rb') as f:
        val_infos = pickle.load(f)['infos']

    night_tokens = {s['token'] for s in night_infos}

    # sample_token → scene_token
    samples_json = json.load(open(META_DIR / 'sample.json'))
    tok2scene = {s['token']: s['scene_token'] for s in samples_json}
    night_scenes = {tok2scene[t] for t in night_tokens if t in tok2scene}
    print(f"Night scenes: {len(night_scenes)}")

    day_all = [s for s in val_infos if s['token'] not in night_tokens]
    # nuScenes night scenes have no daytime counterpart in val split (overlap=0).
    # Use size-matched random sample (same N as night) for fair comparison.
    rng = np.random.default_rng(42)
    day_matched = [day_all[i] for i in rng.choice(len(day_all), size=len(night_infos), replace=False)]
    print(f"Night: {len(night_infos)}, Day(all): {len(day_all)}, Day(size-matched, n={len(day_matched)})")

    # ── 특성 계산 ─────────────────────────────────────────────────────
    print("\nComputing Night features...")
    night_data = compute_features(night_infos, 'Night')
    print("Computing Day(all) features...")
    day_all_data = compute_features(day_all, 'Day(all)')
    print("Computing Day(size-matched) features...")
    day_match_data = compute_features(day_matched, 'Day(matched)')

    # ── 출력 ──────────────────────────────────────────────────────────
    all_keys  = IMG_KEYS + SCN_KEYS
    sections  = (['[이미지 품질]'] + IMG_KEYS + ['[씬 특징]'] + SCN_KEYS)

    print(f"\n{'Metric':<22} {'Night':>16} {'Day(all)':>16} {'Day(size-match)':>16} {'p(Kruskal)':>12} {'sig':>4}")
    print('=' * 92)

    import csv
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    csv_rows = []

    feat_idx = 0
    for label in sections:
        if label.startswith('['):
            print(f"\n{label}")
            continue
        n  = night_data[:, feat_idx];  n  = n[~np.isnan(n)]
        da = day_all_data[:, feat_idx]; da = da[~np.isnan(da)]
        dm = day_match_data[:, feat_idx]; dm = dm[~np.isnan(dm)]

        if len(n) >= 2 and len(da) >= 2 and len(dm) >= 2:
            _, p = kruskal(n, da, dm)
            sig  = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
            p_str = f'{p:.2e}'
        else:
            p_str, sig = 'nan', ''

        fmt = lambda arr: f'{arr.mean():.3f}±{arr.std():.3f}'
        print(f"  {label:<20}  {fmt(n):>16}  {fmt(da):>16}  {fmt(dm):>16}  {p_str:>12} {sig:>3}")
        csv_rows.append([label,
                         f'{n.mean():.4f}', f'{n.std():.4f}',
                         f'{da.mean():.4f}', f'{da.std():.4f}',
                         f'{dm.mean():.4f}', f'{dm.std():.4f}',
                         p_str, sig])
        feat_idx += 1

    with open(OUT_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric',
                         'night_mean', 'night_std',
                         'day_all_mean', 'day_all_std',
                         'day_size_matched_mean', 'day_size_matched_std',
                         'p_kruskal', 'sig'])
        writer.writerows(csv_rows)
    print(f"\nCSV saved: {OUT_CSV}")


if __name__ == '__main__':
    main()
